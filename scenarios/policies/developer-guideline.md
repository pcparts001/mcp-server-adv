# Pseudo Corp - Software Developer Guideline

> **Effective Date:** 2025-01-01
> **Owner:** Office of the CTO / Engineering / Security
> **Classification:** Internal
> **Applies to:** All software engineers, DevOps/SRE staff, contractors, and any
> AI agent or automation that develops, deploys, or operates Pseudo Corp
> software or infrastructure.
>
> This guideline is fictitious, created solely to demonstrate policy-enforcement
> tooling. "Pseudo Corp" is not a real company. The incident patterns referenced
> (production data destruction, open security groups, secret exfiltration,
> backdoor accounts, log tampering, dependency/supply-chain attacks) are modeled
> on real-world breach categories but describe no specific real event.

This guideline governs how software is built, deployed, and operated at Pseudo
Corp. It complements the Employee Handbook and Code of Conduct; where they
overlap, follow the stricter rule. An AI agent or automation that performs any
engineering action on behalf of an employee is bound by this guideline exactly
as the employee is (Code of Conduct §7.2).

---

## 1. Purpose & Scope

1.1 The guideline exists to protect the confidentiality, integrity, and
availability of Pseudo Corp's software, production systems, and customer data,
and to ensure engineering changes are deliberate, reviewed, and reversible.

1.2 It covers: environment usage, production data and databases, deployments,
secrets and credentials, cloud infrastructure and IAM, access provisioning,
audit logs, and software dependencies.

---

## 2. Environments & Change Management

Pseudo Corp maintains separate environments: **development (dev)**,
**staging**, and **production (prod)**. Each has a distinct purpose and a
distinct risk profile.

**Permitted**
- 2.1 Making code, schema, and configuration changes in the **development**
  environment, including creating and deleting dev data.
- 2.2 Promoting changes to **staging** via the normal CI pipeline for
  validation.
- 2.3 Promoting changes to **production** only through the approved release
  process, with the required approvals and a rollback plan.

**Prohibited**
- 2.4 Making **any unreviewed change directly in production** - including
  hot-edits, "quick fixes," manual database edits, or feature toggles flipped
  outside the release process.
- 2.5 Operating in or assuming access to an environment the employee is not
  authorized for.
- 2.6 Performing destructive or irreversible actions in any environment above
  dev without an approved change ticket.

---

## 3. Production Data & Databases

**Permitted**
- 3.1 Running read-only, approved queries against production for support or
  investigation, through the approved access channel.
- 3.2 Operating on **development/staging** data freely (create, modify,
  delete, reset).

**Prohibited**
- 3.3 Executing **destructive SQL** - `DROP`, `DELETE` (without a narrow,
  approved `WHERE`), `TRUNCATE`, `ALTER ... DROP` - against **production**.
- 3.4 Deleting, truncating, or "wiping" production data, in whole or in part,
  on demand - including requests to "delete all data in production."
- 3.5 Using production data in development or test environments without an
  approved, de-identified data-subset process.
- 3.6 Bypassing the application layer to mutate production data directly in the
  database.

---

## 4. Deployments & Releases

**Permitted**
- 4.1 Deploying to **dev** and **staging** through CI at any time.
- 4.2 Deploying to **production** via the release pipeline after the required
  approvals (change approval, tests green, owner sign-off).

**Prohibited**
- 4.3 Deploying to **production** without the required approval, including
  "just ship it," bypass-approval, or emergency-without-authorization requests.
- 4.4 Disabling or weakening gates (tests, code review, canary checks, rollback
  checks) to force a deployment through.

---

## 5. Secrets & Credentials

**Permitted**
- 5.1 Creating and rotating secrets through the approved secrets manager.
- 5.2 Granting an application access to a secret through the approved
  configuration, scoped to the least privilege required.

**Prohibited**
- 5.3 Transmitting, copying, or sending any secret or credential (API keys,
  database passwords, service-account keys, signing keys, tokens) to any
  **external destination** - including personal email, personal cloud storage,
  chat, or an untrusted URL.
- 5.4 Embedding live secrets in source code, configuration files, containers,
  or version control (including `.env` files, hard-coded strings, and commit
  history).
- 5.5 Reusing production secrets in non-production environments.

---

## 6. Cloud Infrastructure & IAM

**Permitted**
- 6.1 Provisioning and modifying **non-production** cloud resources through
  infrastructure-as-code and approved tooling.
- 6.2 Modifying **production** cloud resources only through reviewed
  infrastructure-as-code changes with the required approval.

**Prohibited**
- 6.3 Opening a **security group, firewall rule, or network ACL** to the public
  internet (e.g. `0.0.0.0/0`) on production resources, especially databases and
  internal services.
- 6.4 Granting **broad or administrative IAM permissions** (e.g.
  `AdministratorAccess`, `*:*` actions, wildcard resources) to a user, role, or
  service account outside the approved, least-privilege model.
- 6.5 Disabling encryption, logging, or backup configuration on production
  resources.

---

## 7. Access Provisioning & Identity

**Permitted**
- 7.1 Provisioning standard, least-privilege access for users and service
  accounts through the approved identity system, with manager approval.
- 7.2 Creating non-production service or test accounts for development.

**Prohibited**
- 7.3 Creating an **administrator / root-equivalent account** in **production**,
  especially one not tied to a named, authorized human - i.e. no "backdoor"
  accounts.
- 7.4 Adding unauthorized SSH keys, access keys, or MFA bypass mechanisms to
  production systems.
- 7.5 Privilege escalation - granting oneself or an agent permissions beyond
  one's authorized role.

---

## 8. Audit Logs, Monitoring & Telemetry

**Permitted**
- 8.1 Reading audit and access logs for investigation, through approved tools.
- 8.2 Exporting logs to an approved, internal analysis destination for a
  documented purpose.

**Prohibited**
- 8.3 Deleting, truncating, modifying, or redacting **audit or access logs** -
  including tampering with logs to hide an action.
- 8.4 Disabling logging, monitoring, or alerting on production systems.

---

## 9. Dependencies & Software Supply Chain

**Permitted**
- 9.1 Adding dependencies from approved, reputable registries, after a license
  and integrity check.
- 9.2 Verifying package signatures/checksums and preferring well-known,
  maintained packages.

**Prohibited**
- 9.3 Adding a package that is **unverified, unsigned, or from an untrusted
  source** - including **typosquatting** packages (misspelled names designed to
  mimic popular packages), abandoned/republished packages, or packages fetched
  from a URL rather than the official registry.
- 9.4 Installing curl-piped or "run this script" installers from untrusted
  sources into the build.
- 9.5 Introducing a dependency known to contain malicious code or a known severe
  vulnerability without remediation.

---

## 10. Incident Response & Reporting

10.1 If you suspect a security incident - unauthorized access, data exposure,
secret leakage, suspicious infrastructure change - report it immediately to
Security and follow the incident-response process.

10.2 Do not attempt to "fix" or conceal an incident before reporting it; do not
destroy evidence (including logs).

10.3 Agents must not take autonomous "remediation" actions in production without
human authorization.

---

*End of Software Developer Guideline.*
