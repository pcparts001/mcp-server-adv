# Pseudo Corp - Company Profile

> **Disclaimer.** "Pseudo Corp" is a fictitious company created solely for
> demonstration purposes. It does not exist. None of the people, customers,
> products, contracts, or financial figures referenced anywhere in this demo
> are real. All names, IDs, email addresses, phone numbers, and values are
> invented.

## Overview

| | |
|---|---|
| **Legal name** | Pseudo Corp. |
| **Domain** | pseudo.example |
| **Industry** | Enterprise software (SaaS) |
| **Founded** | 2014 |
| **Headquarters** | Austin, Texas, USA |
| **Employees** | ~1,400 |
| **FY2025 revenue** | USD 310M |
| **Ticker** | PSDO (fictitious) |

## Products

Pseudo Corp sells a unified software-delivery platform with four products:

1. **Pseudo Build** - CI/CD pipeline automation
2. **Pseudo Plan** - Roadmap and sprint planning
3. **Pseudo Insight** - Analytics and dashboards
4. **Pseudo Guard** - Security and compliance scanning

## Organization (selected roles referenced in the demo)

| Role | Name | Notes |
|---|---|---|
| Chief Executive Officer | John Smith | — |
| Chief Financial Officer | Emily Johnson | Owns highly confidential financial documents |
| Chief Human Resources Officer | Jessica Brown | Owns compensation & HR records |
| VP, Sales | David Jones | Owns the sales pipeline |
| Finance Analyst | Michael Williams | Owns churn/financial analysis |
| General Counsel | (Office of the General Counsel) | Owns contract review authority |
| VP, Communications | (Corporate Communications) | Owns official social-media accounts |
| IT Asset Management | (IT department) | Owns the approved-software whitelist |

## Customers referenced (fictitious)

- **Customer A - "Project Aurora":** Global Retail Holdings (ACC-1001), Apex
  Logistics (ACC-1002), BrightPath Health (ACC-1003).
- **Customer B - "Project Beacon":** Vertex Capital (ACC-2001), Northwind
  Trading (ACC-2002), Summit Foods (ACC-2003).

## Data classification labels

Every internal document, customer record, and data asset carries one of three
labels (defined in the Employee Handbook, Section 5):

- **highly_confidential** - severe harm to Pseudo Corp if disclosed.
- **confidential** - internal business use only.
- **public** - approved for external audiences.

## Purpose of this dataset

This profile exists so the AI Guardrail **Policy Studio** has realistic context.
Upload `policies/employee-handbook.md` and `policies/code-of-conduct.md` into
Policy Studio, then run the example prompts in `prompts/` against an agent that
is wired to the MCP server's tools. The guardrail should *allow* safe prompts
and *block* policy-violating ones.
