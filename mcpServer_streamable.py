#!/usr/bin/env python3
"""
Simple MCP Server (Streamable HTTP 版)

mcpServer.py（標準 http.server 版）と同じ機能を、公式 MCP Python SDK の
FastMCP (Streamable HTTP transport) で提供する。RFC 9728 / OAuth 2.1 準拠の
MCP Gateway 越し、またはダイレクト接続での利用を想定。

【設計】
- 本ファイルは mcpServer.py（標準 http.server 版）をインポートしない。
  2 つのトランスポート実装を相互に結合しないため（OAuthVerifier / RFC 9728 /
  既存ツール類はコピーして持つ）。
- 一方で、両サーバーが共有する「シナリオデモ用ツールロジック」は
  scenario_tools.py（トランスポート非依存・Python 標準 lib のみ）に集約し、
  両サーバーからインポートして重複を排除している。
- FastMCP で stateless_http + SSE レスポンス（json_response=False）の Streamable HTTP を提供。
- 認証は SDK 組込ではなくカスタム ASGI ミドルウェアで既存 OAuthVerifier を統合
  （resource URL 解決は X-Forwarded-Host/Proto を含むフォールバック付き・リバースプロキシ背後対応）。
- RFC 9728 Protected Resource Metadata は oauth.enabled 時のみ /.well-known/oauth-protected-resource
  で配信。oauth.enabled=false なら配信せず（404）、OAuth を Gateway 側で引き受ける構成で使う。

【既存との互換性】
- 同じ mcp_server_config.json を読専で読む（深いマージ版に改善）。
- 同じポート（設定の port、既定 9000）で動き、start.sh で既存サーバと切り替え運用する。
"""

import contextlib
import functools
import inspect
import json
import os
import sys
from typing import Any, Dict, Optional

# print を常に即時フラッシュする。stdout が TTY ではなくファイル/パイプ/
# journalctl 等に繋がっていると Python は 4KB 単位のブロックバッファリングを
# 行い、短いリクエスト/レスポンスログが遅延して見えるため。
print = functools.partial(print, flush=True)

import scenario_tools  # shared demo-scenario tool logic (transport-agnostic)

import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route


# ============================================================
# 設定読込（深いマージ版 — mcpServer.py:16-58 の改良）
# ============================================================
def _deep_merge(base: dict, override: dict) -> dict:
    """override を base に再帰的にマージする（dict は潜る、それ以外は上書き）。"""
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
    return base


def load_config(config_path: str = "mcp_server_config.json") -> Dict[str, Any]:
    """MCP Server 設定ファイルを読み込む（既存 mcpServer.py と同じ既定値・深いマージ）。"""
    default_config = {
        "host": "0.0.0.0",
        "port": 9000,
        "server_info": {
            "name": "simple-demo-server",
            "version": "1.0.0",
        },
        "secret_file_path": "./mcp-server-data/secret_notes.txt",
        "check_maintenance_description": "Tool for checking maintenance information",
        "check_maintenance_prefix": "maintenance information",
        "employee_file_path": "./mcp-server-data/employee.txt",
        "get_employee_data_description": "Returns employee names and their Social Security Numbers (dummy data)",
        "get_employee_data_prefix": "employee data",
        "instructions_file_path": "./mcp-server-data/dummy-instructions.txt",
        "get_instructions_description": "Returns system instructions and operational directives",
        "get_instructions_prefix": "instructions",
        # get_instructions（プロンプトインジェクション模擬データを返すデモ用ツール）の有効/無効。
        # 無効(false)にすると tools/list から除外され、tools/call も拒否される。
        "get_instructions_enabled": True,
        # Streamable 版で JSON-RPC リクエスト/レスポンスの詳細ログ
        # （method/id/params/result/error）を標準出力するか（既定: true）。
        # oauth.enabled に関わらず動作。標準版(mcpServer.py)は元々詳細ログを出す。
        "request_response_logging": True,
        "oauth": {
            "enabled": False,
            "public_resource_url": "",
            "serve_metadata_at_root": False,
            "issuer": "",
            "jwks_uri": "",
            "audience": "",
            "scopes": [],
            "jwks_cache_seconds": 600,
        },
    }

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            # 浅いマージではなく深いマージ（oauth ブロックの部分上書きバグを防ぐ）
            _deep_merge(default_config, user_config)
            print(f"✅ Loaded config from {config_path}")
        except Exception as e:
            print(f"⚠️  Failed to load config file: {e}")
            print("   Using default configuration")
    else:
        print(f"⚠️  Config file not found: {config_path}")
        print("   Using default configuration")
        print("   Create config from example: cp mcp_server_config.json.example mcp_server_config.json")

    return default_config


# ============================================================
# データファイルの存在保証（mcpServer.py:61-95 からコピー）
# ============================================================
def ensure_data_file(file_path: str, label: str, fallback_content: str) -> None:
    """データファイルが存在しない場合、.example からコピー、なければ fallback 内容で生成する。"""
    example_file_path = file_path + ".example"
    if not os.path.exists(file_path):
        if os.path.exists(example_file_path):
            import shutil

            shutil.copy(example_file_path, file_path)
            print(f"✅ Created {label} from example: {file_path}")
        else:
            print(f"⚠️  Warning: Neither {os.path.basename(file_path)} nor its .example found")
            print(f"   Expected location: {file_path}")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fallback_content)
            print(f"✅ Created {label}: {file_path}")


def ensure_data_files(config: Dict[str, Any]) -> None:
    """起動時に各データファイルの存在を保証する。"""
    ensure_data_file(
        config.get("secret_file_path", "./mcp-server-data/secret_notes.txt"),
        "secret_notes.txt",
        "[Daily Maintenance Log]\nStatus: No data\n",
    )
    ensure_data_file(
        config.get("employee_file_path", "./mcp-server-data/employee.txt"),
        "employee.txt",
        "[Employee Directory]\nStatus: No data\n",
    )
    ensure_data_file(
        config.get("instructions_file_path", "./mcp-server-data/dummy-instructions.txt"),
        "dummy-instructions.txt",
        "[System Instructions]\nStatus: No data\n",
    )

    # シナリオデモ用データファイル（scenario_tools.py が .example から生成）
    scenario_tools.ensure_scenario_data_files(config)


# ============================================================
# OAuthVerifier（mcpServer.py:98-156 からほぼ verbatim コピー）
# ============================================================
class OAuthVerifier:
    """OAuth 2.1 Bearer トークン検証（JWKS ローカル検証・RS256）。

    OAuth が有効な場合のみ構築され、Authorization ヘッダの Bearer トークンを
    IdP の公開鍵(JWKS)で検証する。無効時は認証をパススルーする。
    """

    def __init__(self, oauth_config: Dict[str, Any]):
        self.enabled = bool(oauth_config.get("enabled", False))
        self.issuer = (oauth_config.get("issuer") or "").strip()
        self.jwks_uri = (oauth_config.get("jwks_uri") or "").strip()
        self.audience = (oauth_config.get("audience") or "").strip()
        self.scopes = set(oauth_config.get("scopes", []) or [])

        self._jwt = None
        self._jwk_client = None
        if self.enabled:
            try:
                import jwt as _jwt
                from jwt import PyJWKClient
            except ImportError as e:
                raise RuntimeError(
                    "OAuth is enabled but PyJWT is not installed. "
                    "Install dependencies: pip install PyJWT cryptography"
                ) from e
            self._jwt = _jwt
            cache_ttl = int(oauth_config.get("jwks_cache_seconds", 600))
            try:
                # PyJWKClient 2.10+ は lifespan、2.8/2.9 は cache_ttl
                self._jwk_client = PyJWKClient(self.jwks_uri, lifespan=cache_ttl)
            except TypeError:
                self._jwk_client = PyJWKClient(self.jwks_uri, cache_ttl=cache_ttl)

    def verify(self, token: str) -> Dict[str, Any]:
        """Bearer トークンを検証し、claims(dict)を返す。無効なら例外を送出。"""
        if not self.enabled:
            return {}

        # kid に対応する署名鍵を JWKS から取得（キャッシュ利用）
        signing_key = self._jwk_client.get_signing_key_from_jwt(token)

        decode_kwargs: Dict[str, Any] = {"algorithms": ["RS256"]}
        if self.issuer:
            decode_kwargs["issuer"] = self.issuer
        if self.audience:
            decode_kwargs["audience"] = self.audience
        else:
            decode_kwargs["options"] = {"verify_aud": False}

        claims = self._jwt.decode(token, signing_key.key, **decode_kwargs)

        # scope 検証（スペース区切りを想定）
        if self.scopes:
            token_scopes = set(str(claims.get("scope", "")).split())
            missing = self.scopes - token_scopes
            if missing:
                raise ValueError(f"Missing required scopes: {sorted(missing)}")

        return claims


# ============================================================
# RFC 9728 / WWW-Authenticate ヘルパ（mcpServer.py:264-330 を関数化）
# ============================================================
def resolve_resource_url(request: Request, config: Dict[str, Any]) -> str:
    """クライアント視点の Protected Resource URL を解決する。

    優先順位（既存 mcpServer.py:264-307 と同一ロジック）:
      1. 設定の oauth.public_resource_url（明示指定・プロキシ背後で推奨）
      2. X-Forwarded-Host + X-Forwarded-Proto（信頼できるプロキシが付与）
      3. Host ヘッダ（従来動作・フォールバック）
      4. http://localhost:{port}（最終フォールバック）

    ※ X-Forwarded-* は resource metadata 構築用途の参考値。認可自体は JWKS トークン
       検証で独立して保護されており、偽装されてもクライアント側の resource 一致検証で弾かれる。
    """
    oauth_cfg = config.get("oauth", {}) or {}

    # 1. 設定の明示指定（最優先・リバースプロキシ背後で最も確実）
    public = (oauth_cfg.get("public_resource_url") or "").strip().rstrip("/")
    if public:
        return public

    # プロキシヘッダーはカンマ区切りリスト（"client, proxy1, proxy2"）。
    # 先頭要素がクライアントに最も近い（本来の）値。
    xf_proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip().lower()
    xf_host = request.headers.get("x-forwarded-host", "").split(",")[0].strip()

    # 2. X-Forwarded-Host があれば、プロキシヘッダーからクライアント視点を復元
    if xf_host:
        proto = xf_proto or "http"
        return f"{proto}://{xf_host}"

    # 3. Host ヘッダから組み立て（スキーマは X-Forwarded-Proto を優先・https 終端対応）
    host_header = request.headers.get("host", "")
    if host_header:
        proto = xf_proto or "http"
        return f"{proto}://{host_header}"

    # 4. 最終フォールバック（ヘッダ類が一切取れない場合）
    port = config.get("port", 9000)
    return f"http://localhost:{port}"


def build_protected_resource_metadata(request: Request, config: Dict[str, Any]) -> Dict[str, Any]:
    """RFC 9728 Protected Resource Metadata を構築する（mcpServer.py:309-319 と同一構造）。"""
    oauth_cfg = config.get("oauth", {}) or {}
    resource_url = resolve_resource_url(request, config)
    return {
        "resource": resource_url,
        "authorization_servers": [oauth_cfg["issuer"]] if oauth_cfg.get("issuer") else [],
        "bearer_methods_supported": ["header"],
        "resource_documentation": resource_url,
        "scopes_supported": oauth_cfg.get("scopes", []) or [],
    }


def make_401_response(request: Request, config: Dict[str, Any], description: str) -> JSONResponse:
    """401 Unauthorized + RFC 9728 WWW-Authenticate ヒントを返す（mcpServer.py:225-242 と等価）。"""
    resource_metadata_url = resolve_resource_url(request, config) + "/.well-known/oauth-protected-resource"
    # WWW-Authenticate は resource_metadata のみ（OpenAI のドキュメント例に合わせる）。
    # error="invalid_token" / error_description を付けると、一部クライアントが
    # 「トークン無効＝リトライ」と解釈して Route B discovery に入らないことがあるため。
    www = f'Bearer resource_metadata="{resource_metadata_url}", error="invalid_token"'
    if description:
        www += f', error_description="{description}"'
    body = {"error": "invalid_token", "error_description": description}
    print(f"   📤 401 Unauthorized response:")
    print(f"      WWW-Authenticate: {www}")
    print(f"      body: {json.dumps(body, ensure_ascii=False)}")
    return JSONResponse(
        body,
        status_code=401,
        headers={
            "WWW-Authenticate": www,
            "Access-Control-Allow-Origin": "*",
        },
    )


def is_public_metadata_path(path: str) -> bool:
    """認証不要の discovery / メタデータパスか。

    RFC 9728 (oauth-protected-resource)、RFC 8414 (oauth-authorization-server)、
    OIDC Discovery (openid-configuration) はすべて事前認証なしで取得できる前提。
    これらを 401 で弾くとクライアントの discovery が壊れる（認可サーバーへ進めなくなる）ため、
    /.well-known/ 配下はすべて認証バイパスする。存在しないパスは 404 となり、クライアントは
    authorization_servers の外部 AS（例: Duo SSO）に正しく向かう。
    リバースプロキシ/Gateway のパスプレフィックス保持転送
    (例: /mcp/tenant/.../server/.well-known/oauth-authorization-server) にも対応するため
    部分一致で判定する。
    """
    path = path.split("?")[0].rstrip("/")
    return "/.well-known/" in path


# ============================================================
# ファイル読込ヘルパ（mcpServer.py:657-699 のコアを関数化）
# ============================================================
def read_text_file(file_path: str, prefix: str) -> str:
    """ファイルを読み込み "{prefix}:\n\n{content}" を返す。エラーは ValueError にラップ。"""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"      📄 Read file: {file_path} ({len(content)} chars)")
        return f"{prefix}:\n\n{content}"
    except FileNotFoundError as e:
        raise ValueError(str(e)) from e
    except PermissionError:
        raise ValueError(f"Permission denied reading file: {file_path}")
    except UnicodeDecodeError:
        raise ValueError(f"Encoding error reading file: {file_path}")
    except Exception as e:
        raise ValueError(f"Error reading file: {e}")


# ============================================================
# Scenario tool registration（scenario_tools.py の spec を FastMCP に登録）
# ============================================================
def _register_scenario_tool(spec: Dict[str, Any], mcp: FastMCP, config: Dict[str, Any]) -> None:
    """SCENARIO_TOOL_SPECS の1エントリを FastMCP に登録する。

    inputSchema の properties から関数シグネチャを動的に構築し、required /
    optional を FastMCP が正しく認識できるようにする。enabled=false のツール
    （scenarios_enabled=false または個別）は登録しない（= tools/list から自動除外）。
    """
    name = spec["name"]
    if not scenario_tools.is_tool_enabled(config, name):
        return
    schema = spec["inputSchema"]
    props = (schema or {}).get("properties", {}) or {}
    required = set((schema or {}).get("required", []) or [])
    annotations = scenario_tools.build_annotations(schema)

    def _fn(**kwargs):
        # FastMCP は optional 引数にデフォルト None を渡すため、None を除外して
        # handler 側のデフォルト値が効くようにする。
        clean = {k: v for k, v in (kwargs or {}).items() if v is not None}
        result = spec["handler"](clean, config)
        # handler は MCP 形式 {"content":[{"type":"text","text":...}]} を返す。
        # FastMCP は関数の戻り値をさらに Content にラップするため、内側の text
        # 文字列を返して FastMCP に TextContent を構築させる（二重ラップ防止）。
        content = result.get("content") if isinstance(result, dict) else None
        if isinstance(content, list) and content and content[0].get("type") == "text":
            return content[0]["text"]
        return result

    params = []
    for pname in props.keys():
        ptype = annotations.get(pname, str)
        if pname in required:
            params.append(inspect.Parameter(
                pname, inspect.Parameter.KEYWORD_ONLY, annotation=ptype))
        else:
            params.append(inspect.Parameter(
                pname, inspect.Parameter.KEYWORD_ONLY, default=None, annotation=ptype))
    _fn.__signature__ = inspect.Signature(parameters=params)
    _fn.__name__ = name
    _fn.__doc__ = spec["description"]  # FastMCP が説明として採用
    _fn.__annotations__ = annotations
    mcp.tool()(_fn)


# ============================================================
# FastMCP サーバ構築
# ============================================================
def build_mcp_server(config: Dict[str, Any]) -> FastMCP:
    """設定から FastMCP を構築し、ツール/プロンプト/リソースを登録する。"""
    server_info = config.get("server_info", {}) or {}
    # NOTE: FastMCP 1.28 は version 引数を持たない。serverInfo.version は SDK 既定値になる。
    mcp = FastMCP(
        server_info.get("name", "simple-demo-server"),
        # Streamable HTTP を stateless + SSE レスポンスで提供。
        # stateless_http=True: セッションID 検証をスキップし、initialize 前の GET /mcp プローブ等も
        # 柔軟に受け付ける（stateful だとセッションID 無しで 400 になる）。json_response=False は SSE 必須。
        stateless_http=True,
        json_response=False,
        streamable_http_path="/mcp",
        # 外部公開（直接接続 / リバースプロキシ・Gateway 背後）を想定。
        # host="0.0.0.0" を明示しないと FastMCP 既定の 127.0.0.1 扱いとなり、DNS リバインディング保護が
        # localhost 限定で自動有効化されて、外部 IP や Gateway の Host ヘッダを 421 Misdirected Request で弾く。
        host="0.0.0.0",
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=False,  # 多様な Host（直接IP / Gateway Host）を許可
        ),
    )

    # --- ツール ---

    @mcp.tool()
    def get_test_string(prefix: str = "Hello") -> str:
        """Simple tool that returns a test string.

        Args:
            prefix: Prefix for the returned string (optional)
        """
        return f"{prefix} from MCP Server! This is a test string."

    @mcp.tool()
    def echo(message: str) -> str:
        """Echoes back the input message.

        Args:
            message: Message to echo
        """
        return f"Echo: {message}"

    # ファイル読込系ツールを config 駆動で一括登録
    def _register_file_tool(name: str, file_key: str, prefix_key: str, desc_key: str) -> None:
        def _fn() -> str:
            return read_text_file(config.get(file_key, ""), config.get(prefix_key, ""))

        _fn.__name__ = name
        _fn.__doc__ = config.get(desc_key, name)  # FastMCP が説明として採用
        mcp.tool()(_fn)

    _register_file_tool(
        "check_maintenance",
        "secret_file_path",
        "check_maintenance_prefix",
        "check_maintenance_description",
    )
    _register_file_tool(
        "get_employee_data",
        "employee_file_path",
        "get_employee_data_prefix",
        "get_employee_data_description",
    )
    # get_instructions（プロンプトインジェクション模擬データを返すデモ用）は設定で無効化可能。
    # 無効時は登録しない（= tools/list から自動除外、tools/call も不可）。
    if config.get("get_instructions_enabled", True):
        _register_file_tool(
            "get_instructions",
            "instructions_file_path",
            "get_instructions_prefix",
            "get_instructions_description",
        )

    # シナリオデモ用ツール（scenario_tools.py）を登録。
    # inputSchema から動的にシグネチャを構築し、required/optional を反映。
    # enabled=false（scenarios_enabled=false または個別）のツールは登録しない。
    for spec in scenario_tools.SCENARIO_TOOL_SPECS:
        _register_scenario_tool(spec, mcp, config)

    # --- プロンプト ---

    @mcp.prompt()
    def greeting(name: str = "World") -> str:
        """Greeting prompt."""
        return f"Hello, {name}!"

    # --- リソース ---

    @mcp.resource("demo://test-data", mime_type="text/plain")
    def test_data() -> str:
        """Test Data"""
        return (
            "This is test data provided by the MCP server.\n"
            "This is a demonstration of the resource feature."
        )

    return mcp


# ============================================================
# Bearer 認証ミドルウェア（既存 OAuthVerifier を ASGI に統合）
# ============================================================
class BearerAuthMiddleware(BaseHTTPMiddleware):
    """/mcp 系エンドポイントに Bearer 認証をかけ、メタデータ/ヘルスは素通しする。

    ヘッダのみ読み body を読まないので、Streamable HTTP のレスポンスストリーミングを破壊しない。
    """

    async def dispatch(self, request: Request, call_next):
        config: Dict[str, Any] = request.app.state.config
        verifier: Optional[OAuthVerifier] = request.app.state.oauth_verifier
        path = request.url.path

        # メタデータ/ヘルス/OPTIONS は認証バイパス
        if (
            request.method == "OPTIONS"
            or is_public_metadata_path(path)
            or path == "/"
        ):
            return await call_next(request)

        # GET /mcp（Direct の SSE ストリーム/probing）は認証前アクセスを許可（406）。
        # Direct（resource 不整合）は 406 の直接 discovery 経路で成功する。
        if request.method == "GET" and (path == "/mcp" or path.endswith("/mcp")):
            return await call_next(request)

        # OAuth 無効なら素通し
        if verifier is None or not verifier.enabled:
            return await call_next(request)

        # Bearer 検証（既存 OAuthVerifier.verify をそのまま呼ぶ）
        auth = request.headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            print(f"   🔓 401: Missing Bearer token (path={path})")
            return make_401_response(request, config, "Missing Bearer token")

        token = auth.split(" ", 1)[1].strip()
        try:
            claims = verifier.verify(token)
        except Exception as e:
            # 検証用サーバー: 受信トークン本体と失敗理由を出力
            print(f"   🔒 401: token verify failed: {e} (path={path})")
            print(f"      token: {token}")
            return make_401_response(request, config, str(e))

        # 検証成功（検証用サーバー: 受信トークン本体とデコードした claims を出力）
        print(f"   ✅ token verified (path={path})")
        print(f"      token: {token}")
        print(f"      claims: {json.dumps(claims, ensure_ascii=False, default=str)}")
        return await call_next(request)


# ============================================================
# リクエスト/レスポンス詳細ログ（pure ASGI ミドルウェア）
# ============================================================
class RequestResponseLoggingMiddleware:
    """JSON-RPC リクエスト/レスポンスの詳細ログを出力する純粋 ASGI ミドルウェア。

    FastMCP が内部処理する Streamable HTTP の中身（method/id/params と
    result/error）を、SSE ストリーミングを破壊せずにロギングする。

    仕組み: receive/send の ASGI callable をラップし、http.request /
    http.response.body イベントのボディを「覗き見（sniff）しつつ下流へそのまま
    転送」する。BaseHTTPMiddleware は body を消費してしまうが、本ミドルウェアは
    イベントを透過させるだけなので SSE のチャンクストリーミングも壊さない。

    リクエストログは受信完了時に、レスポンスログは exchange 終了時（finally）に出力。
    """

    def __init__(self, app, *, enabled: bool = True, max_body_chars: int = 6000):
        self.app = app
        self.enabled = enabled
        self.max_body_chars = max_body_chars

    async def __call__(self, scope, receive, send):
        # 非 http（lifespan 等）は素通し
        if not self.enabled or scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        path = scope.get("path", "")
        client = scope.get("client")  # [host, port] or None
        client_str = f"{client[0]}:{client[1]}" if client else "unknown"
        headers_dict = self._decode_headers(scope.get("headers") or [])

        req_chunks: list = []
        req_logged = {"done": False}

        async def receive_wrapped():
            message = await receive()
            if message.get("type") == "http.request":
                body = message.get("body", b"")
                if body:
                    req_chunks.append(body)
                # リクエストボディ受信完了（最後のチャンク）で即座にリクエストログを出す
                if not message.get("more_body") and not req_logged["done"]:
                    req_logged["done"] = True
                    self._log_request(method, path, client_str, headers_dict, req_chunks)
            return message

        resp_status = {"code": None}
        resp_chunks: list = []

        async def send_wrapped(message):
            mtype = message.get("type")
            if mtype == "http.response.start":
                resp_status["code"] = message.get("status")
            elif mtype == "http.response.body":
                body = message.get("body", b"")
                if body:
                    resp_chunks.append(body)
            await send(message)

        try:
            await self.app(scope, receive_wrapped, send_wrapped)
        finally:
            # body 無しリクエスト（GET 等）で receive が最後まで呼ばれなかった場合はここで出力
            if not req_logged["done"]:
                self._log_request(method, path, client_str, headers_dict, req_chunks)
            self._log_response(method, path, resp_status.get("code"), resp_chunks)

    # ---- helpers ----
    @staticmethod
    def _decode_headers(headers):
        out = {}
        for k, v in headers:
            try:
                out[k.decode("latin-1").lower()] = v.decode("latin-1")
            except Exception:
                continue
        return out

    def _truncate(self, text: str) -> str:
        if len(text) <= self.max_body_chars:
            return text
        return text[: self.max_body_chars] + (
            f"\n... (truncated, {len(text) - self.max_body_chars} more chars)"
        )

    def _pretty(self, obj) -> str:
        try:
            return json.dumps(obj, ensure_ascii=False, indent=2)
        except Exception:
            return str(obj)

    @staticmethod
    def _indent(text: str, n: int) -> str:
        pad = " " * n
        lines = text.splitlines() or [""]
        return "\n".join(pad + line for line in lines)

    @staticmethod
    def _safe_json(text: str):
        try:
            return json.loads(text)
        except Exception:
            return None

    @staticmethod
    def _extract_sse_data(text: str):
        """SSE ストリームから data: ペイロードを抽出する。

        1メッセージは連続する data: 行（改行で結合）。メッセージは空行で区切られる。
        event:/id:/retry: 等の他フィールド、:(コメント) は無視。
        非 SSE ボディ（data: を含まない）なら空リストを返す（呼び出し側で通常 JSON 扱い）。
        """
        if "data:" not in text:
            return []
        payloads = []
        current = []
        for line in text.splitlines():
            if line.startswith("data:"):
                data = line[5:]
                if data.startswith(" "):
                    data = data[1:]
                current.append(data)
            elif line.startswith(":"):
                continue  # SSE comment
            elif line.strip() == "":
                if current:
                    payloads.append("\n".join(current))
                    current = []
            # event:/id:/retry: 等は無視
        if current:
            payloads.append("\n".join(current))
        return payloads

    # ---- request logging ----
    def _log_request(self, method, path, client_str, headers, req_chunks):
        print(f"\n{'='*60}")
        print(f"📥 {method} {path}  (client: {client_str})")
        print(f"   Headers:")
        for hk in sorted(headers.keys()):
            print(f"      {hk}: {headers[hk]}")

        body_text = (
            b"".join(req_chunks).decode("utf-8", errors="replace") if req_chunks else ""
        )
        if not body_text:
            print("   Body: (empty)")
            print(f"{'='*60}")
            return

        parsed = self._safe_json(body_text)
        if isinstance(parsed, list):
            print(f"   JSON-RPC batch request ({len(parsed)} items):")
            for item in parsed:
                self._print_request_item(item)
        elif isinstance(parsed, dict):
            self._print_request_item(parsed)
        else:
            print(f"   Body (non-JSON, {len(body_text)} bytes):")
            print(self._indent(self._truncate(body_text), 6))
        print(f"{'='*60}")

    def _print_request_item(self, item):
        if not isinstance(item, dict):
            print(f"   (non-dict item)")
            return
        m = item.get("method")
        rid = item.get("id")
        if m:
            print(f"   JSON-RPC request   id={rid}   method={m}")
            params = item.get("params")
            if params is not None:
                print(f"   params:")
                print(self._indent(self._truncate(self._pretty(params)), 6))
        else:
            print(f"   JSON-RPC message   id={rid}:")
            print(self._indent(self._truncate(self._pretty(item)), 6))

    # ---- response logging ----
    def _log_response(self, method, path, status, resp_chunks):
        body_text = (
            b"".join(resp_chunks).decode("utf-8", errors="replace") if resp_chunks else ""
        )
        print(f"\n{'='*60}")
        print(f"📤 Response {status}   ({method} {path})")
        if not body_text:
            print("   Body: (empty)")
            print(f"{'='*60}\n")
            return

        payloads = self._extract_sse_data(body_text)
        if payloads:
            print(f"   (SSE response, {len(payloads)} message(s))")
            for payload in payloads:
                self._print_response_item(self._safe_json(payload), payload)
        else:
            parsed = self._safe_json(body_text)
            if parsed is not None:
                print(f"   response body:")
                print(self._indent(self._truncate(self._pretty(parsed)), 6))
            else:
                print(f"   body (raw, {len(body_text)} bytes):")
                print(self._indent(self._truncate(body_text), 6))
        print(f"{'='*60}\n")

    def _print_response_item(self, parsed, raw):
        if isinstance(parsed, dict):
            rid = parsed.get("id")
            if "result" in parsed:
                print(f"   JSON-RPC response   id={rid}   result:")
                print(self._indent(self._truncate(self._pretty(parsed["result"])), 6))
            elif "error" in parsed:
                print(f"   JSON-RPC response   id={rid}   error:")
                print(self._indent(self._truncate(self._pretty(parsed["error"])), 6))
            else:
                print(f"   JSON-RPC message   id={rid}:")
                print(self._indent(self._truncate(self._pretty(parsed)), 6))
        elif isinstance(parsed, list):
            print(f"   JSON-RPC batch response ({len(parsed)} items):")
            print(self._indent(self._truncate(self._pretty(parsed)), 6))
        else:
            print(f"   SSE data (non-JSON): {self._truncate(raw)}")


# ============================================================
# Starlette アプリ組み立て
# ============================================================
def build_app(config: Dict[str, Any]):
    """FastMCP + RFC 9728 ルート + 認証ミドルウェアを統合した Starlette アプリを構築する。"""
    mcp = build_mcp_server(config)

    oauth_cfg = config.get("oauth", {}) or {}
    oauth_enabled = bool(oauth_cfg.get("enabled", False))
    oauth_verifier: Optional[OAuthVerifier] = OAuthVerifier(oauth_cfg) if oauth_enabled else None
    # oauth.enabled=false なら discovery メタデータは一切 advertise しない（OAuth で保護されていない）
    serve_metadata_at_root = oauth_enabled and bool(oauth_cfg.get("serve_metadata_at_root", False))

    async def metadata_endpoint(request: Request) -> JSONResponse:
        """RFC 9728 Protected Resource Metadata（認証不要）"""
        md = build_protected_resource_metadata(request, config)
        print(f"\n{'='*60}")
        print("📥 GET /.well-known/oauth-protected-resource (RFC 9728)")
        print(f"📤 {json.dumps(md, ensure_ascii=False)}")
        print(f"{'='*60}\n")
        return JSONResponse(
            md,
            headers={"Access-Control-Allow-Origin": "*"},
        )

    async def root_endpoint(request: Request):
        """ルート GET。serve_metadata_at_root=true ならメタデータ、それ以外はヘルスチェック。"""
        if serve_metadata_at_root:
            return await metadata_endpoint(request)
        body = {
            "status": "ok",
            "server": "MCP Server (Streamable HTTP)",
            "version": (config.get("server_info", {}) or {}).get("version", "1.0.0"),
            "transport": "streamable-http",
            "message": "Server is running. POST to /mcp for MCP requests.",
        }
        print(f"   📤 GET / response (200, health): {json.dumps(body, ensure_ascii=False)}")
        return JSONResponse(
            body,
            headers={"Access-Control-Allow-Origin": "*"},
        )

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette):
        # FastMCP を Mount する場合は session_manager の実行が必須
        async with mcp.session_manager.run():
            yield

    # routes 構築: OAuth 有効時のみ RFC 9728 discovery を公開。
    # oauth.enabled=false なら discovery は存在せず（Mount のフォールスルーで 404）、
    # バックエンドが OAuth で保護されていないことをクライアント/GW に示す
    # （OAuth を Gateway 側で引き受ける構成では oauth.enabled=false にする）。
    routes = []
    if oauth_enabled:
        # メタデータは Mount より前に（Starlette は最初にマッチしたルートが勝つ）
        routes.append(
            Route(
                "/.well-known/oauth-protected-resource",
                metadata_endpoint,
                methods=["GET"],
            )
        )
    routes.append(Route("/", root_endpoint, methods=["GET"]))
    # /mcp を含む全 POST は FastMCP の Streamable HTTP アプリへ
    routes.append(Mount("/", app=mcp.streamable_http_app()))

    app = Starlette(routes=routes, lifespan=lifespan)
    app.state.config = config
    app.state.oauth_verifier = oauth_verifier
    app.state.serve_metadata_at_root = serve_metadata_at_root

    # ミドルウェア（外→内）: RequestResponseLogging → CORS → BearerAuth → アプリ
    # ※ add_middleware は後から追加したものほど外側になる。
    # RequestResponseLogging を一番外に置き、認証(CORS/BearerAuth)やメタデータを含む
    # 全てのリクエスト/レスポンス（401 含む）の JSON-RPC 中身を覗き見する。
    # （Cisco GW 互換ハック3種は RFC 9728 / OAuth 2.1 準拠 GW では不要・有害なため削除済）
    app.add_middleware(BearerAuthMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Mcp-Protocol-Version", "Mcp-Session-Id"],
        expose_headers=["Mcp-Session-Id"],
    )
    if config.get("request_response_logging", True):
        app.add_middleware(RequestResponseLoggingMiddleware)

    return app, mcp


# ============================================================
# エントリポイント
# ============================================================
def main() -> None:
    config = load_config()
    ensure_data_files(config)

    # CLI 引数でポート上書き（既存 mcpServer.py と互換）
    if len(sys.argv) > 1:
        try:
            config["port"] = int(sys.argv[1])
        except ValueError:
            pass

    app, _mcp = build_app(config)

    oauth_cfg = config.get("oauth", {}) or {}
    if oauth_cfg.get("enabled"):
        print("🔒 OAuth enabled (Bearer/JWKS verification on /mcp)")
    else:
        print("🔓 OAuth disabled (no authentication)")

    host = config.get("host", "0.0.0.0")
    port = config.get("port", 9000)

    print("🚀 MCP Server (Streamable HTTP) running")
    print(f"   Listen:    http://{host}:{port}/mcp")
    print(f"   Metadata:  http://{host}:{port}/.well-known/oauth-protected-resource"
          + ("  (also at / )" if oauth_cfg.get("serve_metadata_at_root") else ""))
    print("   Protocol:  2025-06-18 (negotiated by SDK)")
    print("   Transport: Streamable HTTP (stateless, SSE response)")

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
