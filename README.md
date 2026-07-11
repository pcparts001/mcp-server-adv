# mcp-server-adv - AI Guardrail / Policy Studio Demo MCP Server

A demo MCP (Model Context Protocol) server for the **AI Guardrail** product. It
exposes a realistic set of enterprise tools that an AI agent might call -
document access, email/messaging, payments, contracts, social media, customer
data, and Windows system changes - so the AI Guardrail **Policy Studio** can
inspect the agent's prompts and tool calls and **block** policy-violating
actions before they execute.

> **Everything is simulated.** No email is sent, no card is charged, no file is
> written, no software is installed, and no Windows registry key is touched. The
> server only *returns* a response that looks like the action ran (a success
> message, a fictitious transaction id, and realistic dummy data). **The MCP
> server never decides to block** - block/allow is the Policy Studio guardrail's
> job. The tools simply carry the policy-relevant signals (classification,
> amount, approval flags, tone, on-behalf-of, off-hours, ...) so the guardrail
> can inspect them. All data is fictitious (imaginary company **Pseudo Corp**).

Two interchangeable server implementations share the same tool logic
(`scenario_tools.py`):

| Server | Transport | Depends on |
| --- | --- | --- |
| `mcpServer.py` | standard `http.server` | Python standard library only |
| `mcpServer_streamable.py` | FastMCP / Streamable HTTP | MCP Python SDK, uvicorn |

## Demo scenarios

See **[`scenarios/`](scenarios/README.md)** for the full demo kit:

- `scenarios/policies/employee-handbook.md` and `code-of-conduct.md` - **upload
  these to Policy Studio** as the policy source.
- `scenarios/company-profile.md` - fictitious company context.
- `scenarios/prompts/*.md` - each scenario has a **block-worthy** prompt and a
  **safe** prompt (Windows-only scenarios are block-only).

| # | Scenario | Block-worthy signal |
| --- | --- | --- |
| M1 | Document handling | reading/sharing `highly_confidential` docs |
| M2 | Windows system changes | any registry / service / PowerShell / task / Defender change by an agent |
| 1 | Recruitment screening | scraping candidate personal social media; storing sensitive attributes |
| 2 | Off-hours work | night (22:00-05:00) / weekend labor or background batch jobs |
| 3 | Harassment message | intimidating / threatening message tone |
| 4 | Unapproved purchase | card charge at/over threshold without approval |
| 5 | Expense mismatch | personal expense miscategorized as business |
| 6 | Proxy signature | signing on behalf of another / without authority |
| 7 | Copyright asset | downloading/using a watermarked or unlicensed asset |
| 8 | Unapproved social post | posting to an official account without comms approval |
| 9 | Customer data reuse | exporting customer A's data for customer B's proposal |
| 10 | Unauthorized software | installing a non-whitelisted package |

## Tools

### Demo scenario tools (24)
All defined in `scenario_tools.py`; registered by both servers.

| Tool | Scenario |
| --- | --- |
| `read_document`, `write_document`, `share_document_externally` | M1 |
| `modify_windows_registry` | M2 |
| `manage_windows_service` | M2 |
| `execute_powershell_script` | M2 |
| `modify_scheduled_task` | M2 |
| `modify_windows_defender` | M2 |
| `scrape_candidate_social`, `save_candidate_profile` | 1 |
| `submit_timesheet_entry`, `run_background_batch_job` | 2 |
| `draft_message`, `send_slack_message`, `send_email` | 3 |
| `charge_corporate_card` | 4 |
| `submit_expense_report` | 5 |
| `sign_contract` | 6 |
| `download_web_asset`, `embed_asset_in_document` | 7 |
| `post_to_official_social` | 8 |
| `query_customer_record`, `export_customer_data` | 9 |
| `install_software` | 10 |

### Built-in tools (5)
| Tool | Description |
| --- | --- |
| `get_test_string` | Returns a test string (supports an optional `prefix`) |
| `echo` | Returns the input message as-is |
| `check_maintenance` | Returns maintenance information from `secret_notes.txt` |
| `get_employee_data` | Returns dummy employee data (incl. SSNs) from `employee.txt` |
| `get_instructions` | Returns simulated prompt-injection test data from `dummy-instructions.txt` |

### Prompts & Resources
| Prompt | Description |
| --- | --- |
| `greeting` | Greeting prompt (supports a `name` argument) |

| URI | Description |
| --- | --- |
| `demo://test-data` | Demo test data |

## Quick start

```bash
# Create a virtual environment and install deps
python3 -m venv venv && source venv/bin/activate   # standard server (stdlib only)
pip install -r requirements.txt                      # only for OAuth

# Streamable variant
python3 -m venv venv-streamable && source venv-streamable/bin/activate
pip install -r requirements_streamable.txt

# Prepare the config and (optional) data files
cp mcp_server_config.json.example mcp_server_config.json
```

### Foreground (local testing)
```bash
python3 mcpServer.py            # standard server (config port, default 9000)
python3 mcpServer.py 9001       # specific port
python3 mcpServer_streamable.py # streamable variant
```

### Background (scripts/)
```bash
chmod +x scripts/*.sh
./scripts/start.sh              # standard server
./scripts/start.sh stream       # streamable variant
./scripts/status.sh
./scripts/stop.sh
tail -f logs/server.log
```

### Verify
```bash
# List tools (expect 29 with scenarios_enabled=true)
curl -s -X POST http://localhost:9000/ -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 -m json.tool | grep '"name"'

# Call a scenario tool (server returns a simulated success)
curl -s -X POST http://localhost:9000/ -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"read_document","arguments":{"document_id":"DOC-HC-001"}}}' \
  | python3 -m json.tool
```

## Data files

Runtime data lives in `mcp-server-data/`. Each file has a committed `.example`
template; the server copies `.example` -> real file on first start. Real files
are git-ignored.

| File | Used by |
| --- | --- |
| `secret_notes.txt`, `employee.txt`, `dummy-instructions.txt` | built-in tools |
| `documents.json` | `read_document` (M1) |
| `customer_records.json` | `query_customer_record` / `export_customer_data` (9) |
| `candidates.json` | `scrape_candidate_social` (1) |
| `contracts.json` | `sign_contract` (6) |
| `expense_receipts.json` | `submit_expense_report` (5) |
| `social_accounts.json` | `post_to_official_social` (8) |
| `software_catalog.json` | `install_software` (10) |

## Configuration (`mcp_server_config.json`)

In addition to the existing keys, the scenario tools are controlled by:

| Key | Description | Default |
| --- | --- | --- |
| `scenarios_enabled` | Master switch. `false` hides all 24 scenario tools. | `true` |
| `scenarios_data_dir` | Base directory for scenario data files. | `./mcp-server-data` |
| `scenario_tools.<name>.enabled` | Enable/disable a single tool. | `true` |
| `scenario_tools.<name>.data_file` | Override a tool's data file. | (per tool) |
| `scenario_tools.charge_corporate_card.approval_threshold_usd` | Approval threshold. | `100` |
| `scenario_tools.submit_timesheet_entry.night_hours_start` / `night_hours_end` | Night-work window. | `22` / `5` |

Existing OAuth / proxy keys (`oauth.enabled`, `oauth.public_resource_url`,
`oauth.serve_metadata_at_root`, `oauth.codex_ips`, ...) are unchanged.

## Running behind a Reverse Proxy (MCP Proxy)

When placing a reverse proxy in front of the server - Client -> MCP Proxy ->
This server (:9000) - OAuth Discovery may report **"the Proxy URL and
`resource` do not match (origin error)"**.

### Cause
The `resource` field returned by `/.well-known/oauth-protected-resource` must,
per RFC 9728 §2.1, **exactly match the URL the client used to retrieve the
metadata**. The server constructs the URL from the `Host` header by default, but
if the proxy rewrites `Host`, it will mismatch the client's URL.

### Solution (any of the following)

**1. Explicitly set `public_resource_url` (recommended, most reliable)**
```json
"oauth": {
    "enabled": true,
    "public_resource_url": "https://mcp-proxy.example.com",
    ...
}
```

**2. Have the proxy add `X-Forwarded-*` headers**
```nginx
location / {
    proxy_pass http://127.0.0.1:9000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

> Even without `public_resource_url` configured, the server falls back to the
> `Host` header, so direct-connection environments are unaffected. Authorization
> itself is independently protected by JWKS token verification.

> **MCP gateways that strip the path (e.g. Cisco AI Defense MCP Gateway):** set
> `oauth.serve_metadata_at_root: true` so the server returns the metadata
> document at `/` as well. The 401 response also includes a
> `WWW-Authenticate: resource_metadata=...` hint (RFC 9728).

### Codex via a path-rewriting MCP gateway (Streamable variant only)
Codex sends a `GET` probe to the MCP endpoint and expects `406 Not Acceptable`.
Through a path-rewriting gateway that probe is forwarded to the backend root
`/`, where the health endpoint answers `200`. List the Codex client's IP
(`X-Forwarded-For`) in `oauth.codex_ips` so only matching `GET /` requests are
rewritten to `/mcp` (returning `406`).
```json
"oauth": { "enabled": true, "codex_ips": ["203.0.113.10"] }
```

## Directory structure

```
mcp-server-adv/
├── mcpServer.py                       # MCP Server (standard http.server)
├── mcpServer_streamable.py            # MCP Server (FastMCP / Streamable HTTP)
├── scenario_tools.py                  # Shared scenario tool logic (24 tools)
├── mcp_server_config.json.example     # Example configuration
├── scripts/
│   ├── start.sh                       # start.sh | start.sh stream
│   ├── stop.sh
│   └── status.sh
├── mcp-server-data/                   # Runtime data (.example committed, real git-ignored)
│   ├── *.txt(.example)                # built-in tool data
│   └── *.json(.example)               # scenario tool data
├── scenarios/                         # Demo kit (committed)
│   ├── README.md
│   ├── company-profile.md
│   ├── policies/
│   │   ├── employee-handbook.md       # -> upload to Policy Studio
│   │   └── code-of-conduct.md         # -> upload to Policy Studio
│   └── prompts/                       # block-worthy + safe prompts per scenario
├── requirements.txt                   # standard server deps (OAuth only)
├── requirements_streamable.txt        # streamable server deps
└── README.md
```

## Requirements
- Python 3.8+ (standard server); Python 3.10+ recommended for the streamable
  variant.
- Standard server needs additional packages **only** for OAuth
  (`PyJWT`, `cryptography`).
- Streamable variant needs the MCP Python SDK and uvicorn
  (`requirements_streamable.txt`).
