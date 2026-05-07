# Customer Data Warehouse — Access Policy

## Overview

The customer data warehouse (CDW) holds aggregated customer event data,
account metadata, and ML feature stores used by Marketing, Product, and
Data Science teams. Because it contains personal data, access is tightly
controlled through a tiered model.

## Access tiers

The data warehouse defines four access tiers. Each tier corresponds to a
distinct IAM role and to a column-level mask configuration in the warehouse.

| Tier | Name | Who | What they see |
|---|---|---|---|
| 1 | Aggregate | Anyone with a business need (default for new analysts) | Aggregated counts only; no row-level data; no PII |
| 2 | Pseudonymous | Approved analysts | Row-level data with hashed user IDs; no direct identifiers |
| 3 | Identified | Approved data scientists working on production models | Row-level data with un-hashed user IDs; no contact PII |
| 4 | Full PII | Privacy / compliance / fraud team only | All columns including email, phone, address |

Tiers 3 and 4 require explicit approval from the Data Governance Council
and the Chief Privacy Officer. Tier 4 requires re-attestation every 90 days.

## Requesting access

1. Submit an access request in AccessHub specifying the tier and the
   business justification.
2. Your manager approves Tier 1 and 2 directly. Tiers 3 and 4 route to the
   Data Governance Council.
3. Once granted, access is provisioned to your federated IAM role; you log
   in via SSO. There are no static credentials.

## Audit and retention

- All queries against the warehouse are logged to a separate audit account.
- Logs include the user, role, query text, rows returned, and timestamp.
- Logs are retained for 7 years (5 years cold + 2 years archive).
- Quarterly access reviews are performed by the Data Governance Council.

## Acceptable use

- Do not export Tier 3 or 4 data to local laptops or unmanaged tools.
- Use approved BI tools (Hex, Mode) which inherit your tier.
- Sharing query results outside AcmeCorp requires Privacy review.

## Violations

Unauthorized access or use of customer data is a Code of Conduct violation
and may result in disciplinary action up to termination, plus regulatory
reporting in jurisdictions where required.
