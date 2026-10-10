---
l_id: L19
title: Snowflake editions
duration: "7:00"
prereqs: ["L18"]
downloads: []
---

# L19 — Snowflake Editions

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 3 — Snowflake Architecture
> **Duration:** ~7:00

## Prereqs

L18 — Cloud computing. Familiarity with the PaaS model.

## Key terms

- **Standard** — entry-level. Core SQL, virtual warehouses,
  basic security.
- **Enterprise** — adds multi-cluster warehouses, 90-day Time
  Travel, materialized views, column-level security, search
  optimization.
- **Business Critical** — adds HIPAA support, customer-managed
  keys (Tri-Secret Secure), database failover, private
  connectivity.
- **Virtual Private Snowflake (VPS)** — adds a dedicated
  virtual private cloud and customer-managed virtual network.
- **Government / VPS for US Government** — separate offerings
  for FedRAMP and DoD workloads.

## Lecture

Snowflake has five public editions plus a couple of regulated-
industry variants. Each edition unlocks features and security
capabilities; pricing scales accordingly.

### The edition ladder

```text
┌─────────────────────────────────────┐
│  Standard                           │ ← entry-level
├─────────────────────────────────────┤
│  Enterprise                         │ ← most popular
├─────────────────────────────────────┤
│  Business Critical                  │ ← regulated data
├─────────────────────────────────────┤
│  Virtual Private Snowflake (VPS)    │ ← dedicated VPC
└─────────────────────────────────────┘
```

### Standard

The entry tier. Includes:

- Core SQL and DDL
- Virtual warehouses (single-cluster only)
- 1-day Time Travel
- Basic role-based access control
- Federated authentication / SSO
- 24/7 support (Standard tier)

> When to pick Standard. Small teams, simple workloads, no
> compliance requirements. Most production workloads end up on
> Enterprise within 12 months.

### Enterprise

The most popular tier. Standard plus:

- **Multi-cluster warehouses** (concurrent scaling)
- **90-day Time Travel** (vs 1 day)
- **Materialized views**
- **Column-level security**
- **Search optimization service** (point lookups on string
  columns)
- **Snowpipe** (serverless auto-ingest)
- **Always-on encryption** with customer-managed keys
- **Database failover and failback** (DR)

> When to pick Enterprise. The default for most production
> workloads. If you have multiple concurrent users, want
> longer Time Travel, or run dbt/ELT at scale, you need
> Enterprise.

### Business Critical

Enterprise plus:

- **HIPAA / PCI compliance** support
- **Tri-Secret Secure** — three-party key management for
  regulated industries
- **Database failover and failback** with no data loss
- **Private connectivity** (AWS PrivateLink, Azure Private
  Link)
- **Customer-managed encryption keys** (full)

> When to pick Business Critical. Healthcare, financial
> services, and any environment with HIPAA or PCI
> obligations. Also pick it when you need Tri-Secret Secure
> for key control.

### Virtual Private Snowflake (VPS)

Business Critical plus:

- **Dedicated virtual private cloud** — your Snowflake
  account runs in a VPC no other customer shares
- **Customer-managed virtual network** — bring your own
  network topology
- **Custom cloud account** — Snowflake can deploy into a
  cloud account you control

> When to pick VPS. Highly regulated industries (defense,
> banking) where even a multi-tenant PaaS is unacceptable.

### Pricing per credit (rough order of magnitude)

Edition affects **per-credit price**, not consumption.

```text
Standard          $2 / credit
Enterprise        $3 / credit
Business Critical $4 / credit
VPS               contact sales
```

(Credits are charged per warehouse-second; the per-credit price
varies by edition. Storage is priced separately and is the same
across editions.)

### How to pick

Ask three questions:

1. **Do you have regulated data?** (HIPAA, PCI, FedRAMP) →
   Business Critical or higher.
2. **Do you have many concurrent users?** → Enterprise (multi-
   cluster).
3. **Otherwise?** → Standard is fine to start; upgrade to
   Enterprise when you outgrow it.

You can upgrade at any time without re-creating data.

## Hands-on

```sql
-- Check your current edition
SELECT CURRENT_ACCOUNT_NAME(),
       CURRENT_REGION(),
       CURRENT_VERSION();

-- Account edition is visible in the UI under
-- Admin → Accounts. There's no SQL view for it; you
-- need ACCOUNTADMIN to see the billing page.
```

## Quiz prep

- Which edition is required for multi-cluster warehouses?
  (Enterprise)
- Which edition supports HIPAA / Tri-Secret Secure?
  (Business Critical)
- Which edition gives you a dedicated VPC? (VPS)

## What's next

Next up is **L20 — Snowflake pricing**, where we break down
the credit model, storage pricing, and cloud services costs.
