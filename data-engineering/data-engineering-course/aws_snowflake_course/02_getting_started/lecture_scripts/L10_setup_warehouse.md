---
l_id: L10
title: Setting up warehouse
duration: "8:00"
prereqs: ["L09"]
downloads: []
---

# L10 — Setting Up a Warehouse

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 2 — Getting Started
> **Duration:** ~8:00

## Prereqs

L09 — Architecture (deeper). This lecture is the first hands-on
with virtual warehouses.

## Key terms

- **Virtual warehouse** — a cluster of compute resources that
  runs queries. Created with `CREATE WAREHOUSE`.
- **Warehouse size** — X-Small to 6X-Large. Each step doubles
  the per-hour credit cost.
- **Auto-suspend / auto-resume** — controls when a warehouse
  pauses and starts.
- **Resource monitor** — a credit cap. When a warehouse's
  accumulated credit usage hits the cap, the warehouse
  suspends.

## Lecture

In this lecture we create our first virtual warehouses through
the Snowflake UI. The UI-driven workflow is great for one-off
warehouses; L11 covers the SQL equivalent for production
workloads.

### Create a warehouse via the UI

1. Click **Admin** → **Warehouses** in the left sidebar.
2. Click **+ Warehouse**.
3. Fill in:

```text
Name:               ETL_WH
Size:               Medium
Auto-suspend:       5 minutes
Auto-resume:        ✓
Initially suspended: ✓
Scaling policy:     Standard
```

4. Click **Create Warehouse**.

You now have a `MEDIUM` warehouse that bills at 8 credits/hour
while running, 0 when suspended. Auto-suspend kicks in after 5
minutes of no queries.

### Sizing a warehouse — the rules of thumb

| Workload | Size | Why |
|---|---|---|
| Ad-hoc analyst queries | X-Small or Small | 1–2 credits/hour, fast for small scans |
| ETL on small data (<10 GB) | Small or Medium | 2–8 credits/hour |
| ETL on big data (>100 GB) | Large or X-Large | 16+ credits/hour, parallel scan |
| Reporting / dashboard | Small | Steady, predictable |
| ML feature engineering | Large or X-Large | Heavier joins, group-bys |

> **Rule of thumb.** Start Small. If queries are slow or you
> see queueing, double the size. If you're not constrained,
> drop one size.

> **Anti-pattern.** Running everything on a Large or X-Large
> "just in case". You pay for every minute the warehouse is
> running, including idle time.

### Auto-suspend — the most important cost lever

Auto-suspend is **the** most effective cost control in
Snowflake. The default is 60 seconds; many production setups
use 60–300 seconds.

Considerations:

- **60 seconds** — minimal idle waste; warehouse pauses quickly
  after the last query. Cold-start penalty is 1–2 seconds.
- **300 seconds (5 min)** — balances cold-start vs. savings.
  Good default for most workloads.
- **600+ seconds** — only if every second of cold-start
  matters (real-time dashboards, sub-second SLAs).

### Auto-resume — keep it on

Auto-resume is on by default. When a query is submitted to a
suspended warehouse, the warehouse resumes within 1–2 seconds
and the query runs. Disable auto-resume only for warehouses you
want to control manually (e.g. an off-hours batch warehouse).

### Resource monitors

A **resource monitor** caps the credits a warehouse can
consume over a period. We cover them in L23, but you'll
typically:

- Set a monthly cap on the `ETL_WH` warehouse.
- Set a **lower** monthly cap on ad-hoc warehouses.
- Get an email at 75% and 100% of the cap.

### Putting it together — a starter warehouse setup

For a small team just starting with Snowflake, three
warehouses is a good baseline:

| Warehouse | Size | Auto-suspend | Use |
|---|---|---|---|
| `LOADING_WH` | Large | 60s | Bulk data loading (sections 4–10) |
| `TRANSFORM_WH` | Medium | 60s | dbt, ELT transformations |
| `ANALYST_WH` | X-Small | 60s | Ad-hoc queries, BI |

Each is independent. A heavy load job doesn't slow down an
analyst's dashboard.

## Hands-on

Create the three starter warehouses above via the UI. Then
run a query against each:

```sql
USE WAREHOUSE LOADING_WH;
SELECT COUNT(*) FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.LINEITEM;

USE WAREHOUSE TRANSFORM_WH;
SELECT COUNT(*) FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS;

USE WAREHOUSE ANALYST_WH;
SELECT COUNT(*) FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER;
```

## Quiz prep

- What's the default auto-suspend value? (60 seconds)
- What is the per-hour credit cost of a Medium warehouse?
  (4 credits/hour, billed per second)
- What is the recommended starter warehouse setup for a small
  team? (LOADING, TRANSFORM, ANALYST — three separate
  warehouses)

## What's next

Next up is **L11 — Setting up warehouse using SQL**, where we
do the same setup in code so it's reproducible and version-
controlled.
