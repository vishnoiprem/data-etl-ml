---
l_id: L12
title: Setting up warehouse (recap)
duration: "4:00"
prereqs: ["L11"]
downloads: []
---

# L12 — Setting Up a Warehouse (Recap)

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 2 — Getting Started
> **Duration:** ~4:00

## Prereqs

L10–L11. This is a short recap tying the UI and SQL workflows
together.

## Key terms

- **Idempotent DDL** — DDL that can be run multiple times with
  the same effect. Snowflake's `CREATE ... IF NOT EXISTS` and
  `DROP ... IF EXISTS` make scripts safe to re-run.
- **Bootstrap script** — a SQL file that brings an account
  from empty to a known-good state. Checked into version
  control.

## Lecture

L10 covered the UI workflow; L11 covered the SQL equivalent.
This recap gives you the canonical pattern for production.

### The canonical bootstrap script

```sql
-- bootstrap_warehouses.sql — run once per environment
USE ROLE SYSADMIN;

-- Compute
CREATE WAREHOUSE IF NOT EXISTS LOADING_WH
  WITH WAREHOUSE_SIZE = 'LARGE' AUTO_SUSPEND = 60;
CREATE WAREHOUSE IF NOT EXISTS TRANSFORM_WH
  WITH WAREHOUSE_SIZE = 'MEDIUM' AUTO_SUSPEND = 60;
CREATE WAREHOUSE IF NOT EXISTS ANALYST_WH
  WITH WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60;

-- Storage
CREATE DATABASE IF NOT EXISTS DEMO;
CREATE SCHEMA IF NOT EXISTS DEMO.RAW;
CREATE SCHEMA IF NOT EXISTS DEMO.ANALYTICS;
```

The `IF NOT EXISTS` guards make the script safe to re-run.

### UI vs SQL — when to use which

| Situation | Use |
|---|---|
| Spinning up a one-off warehouse for an experiment | UI |
| Production setup that must be reproducible | SQL |
| Per-environment (dev / stage / prod) parity | SQL |
| Auditing "what does the account have?" | UI (and `SHOW`) |
| Documenting the setup in version control | SQL |

### Sizing recap

The single biggest cost lever is **right-sizing**. The
recommended pattern:

1. Start Small / Medium.
2. Profile with Query History — look for long-running or
   queueing queries.
3. If queries are slow despite partition pruning working,
   scale **up** (larger warehouse).
4. If many users are queued, scale **out** (multi-cluster,
   Enterprise+).
5. Re-evaluate quarterly. Workloads drift.

## Hands-on

Re-run your `bootstrap_warehouses.sql` from L11 and confirm
that all three warehouses are still there (the `IF NOT EXISTS`
guards prevent duplicates).

```sql
SHOW WAREHOUSES;
```

You should see exactly the three warehouses you created —
`LOADING_WH`, `TRANSFORM_WH`, `ANALYST_WH`.

## Quiz prep

- Why is `CREATE ... IF NOT EXISTS` important for
  bootstrapping? (Makes the script idempotent — safe to
  re-run)
- When should you prefer UI over SQL for warehouse setup?
  (One-off, exploratory)
- What is the right-sizing pattern? (Start small, profile,
  scale up or out, re-evaluate quarterly)

## What's next

Next up is **L13 — Manage warehouses**, where we cover the
operational side: resizing, resuming/suspending, and credit
monitoring.
