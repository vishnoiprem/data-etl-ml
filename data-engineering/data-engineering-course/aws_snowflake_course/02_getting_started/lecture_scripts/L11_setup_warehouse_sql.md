---
l_id: L11
title: Setting up warehouse using SQL
duration: "7:00"
prereqs: ["L10"]
downloads: []
---

# L11 — Setting Up a Warehouse Using SQL

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 2 — Getting Started
> **Duration:** ~7:00

## Prereqs

L10 — Setting up warehouse (UI). This lecture does the same
thing in SQL.

## Key terms

- **`CREATE WAREHOUSE`** — DDL to provision a new warehouse.
- **`ALTER WAREHOUSE ... SET`** — modify size, auto-suspend,
  scaling policy, etc.
- **`DROP WAREHOUSE`** — remove a warehouse. Active queries
  fail unless `IF EXISTS` is used with care.
- **`SHOW WAREHOUSES`** — list all warehouses in the account
  (requires `MONITOR` privilege on the warehouse or
  `ACCOUNTADMIN`).

## Lecture

The UI is great for one-offs. For any production setup, you
want your warehouses defined in SQL so they can be checked into
version control and re-run across environments (dev / stage /
prod). This lecture shows the SQL equivalent of L10.

### Create a warehouse

```sql
USE ROLE SYSADMIN;

CREATE WAREHOUSE LOADING_WH
  WITH WAREHOUSE_SIZE       = 'LARGE'
       AUTO_SUSPEND         = 60
       AUTO_RESUME          = TRUE
       INITIALLY_SUSPENDED  = TRUE
       SCALING_POLICY       = 'STANDARD'
       MIN_CLUSTER_COUNT    = 1
       MAX_CLUSTER_COUNT    = 1
       COMMENT              = 'Bulk data loading';
```

Notes on each option:

- `WAREHOUSE_SIZE` — X-Small, Small, Medium, Large, X-Large,
  2X-Large, 3X-Large, 4X-Large. Use single quotes.
- `AUTO_SUSPEND` — in seconds. NULL = never auto-suspend
  (avoid; costs add up fast).
- `AUTO_RESUME` — TRUE by default. Set FALSE for manual-only.
- `INITIALLY_SUSPENDED` — TRUE means the warehouse is created
  in suspended state. Recommended; otherwise you pay for the
  first minute immediately.
- `SCALING_POLICY` — STANDARD (default) or ECONOMY.
- `MIN_CLUSTER_COUNT` / `MAX_CLUSTER_COUNT` — only relevant for
  multi-cluster warehouses (Enterprise+); set to 1 for single-
  cluster.
- `COMMENT` — shows up in `SHOW WAREHOUSES` and the UI.

### Inspect a warehouse

```sql
SHOW WAREHOUSES LIKE 'LOADING_WH';

DESC WAREHOUSE LOADING_WH;
```

`SHOW` returns a row with size, state, current cluster count,
and credit usage. `DESC` returns a row per property (useful
for scripted checks).

### Modify a warehouse

```sql
-- Resize
ALTER WAREHOUSE LOADING_WH SET WAREHOUSE_SIZE = 'XLARGE';

-- Tighten auto-suspend
ALTER WAREHOUSE LOADING_WH SET AUTO_SUSPEND = 30;

-- Resume / suspend manually
ALTER WAREHOUSE LOADING_WH RESUME;
ALTER WAREHOUSE LOADING_WH SUSPEND;

-- Rename (Enterprise+)
ALTER WAREHOUSE LOADING_WH RENAME TO BULK_LOAD_WH;
```

`ALTER WAREHOUSE ... SET` is the right tool for any property
change. Operations are online — current queries are not
interrupted, but a resizing change takes effect on the next
cluster start.

### Drop a warehouse

```sql
DROP WAREHOUSE LOADING_WH;
-- or, safer:
DROP WAREHOUSE IF EXISTS LOADING_WH;
```

If a warehouse is running and has active queries, `DROP`
fails with a clear error. Suspend the warehouse first.

### Putting it in a script

The whole setup is a handful of lines, perfect for a bootstrap
script:

```sql
-- bootstrap_warehouses.sql
USE ROLE SYSADMIN;

CREATE WAREHOUSE IF NOT EXISTS LOADING_WH
  WITH WAREHOUSE_SIZE = 'LARGE', AUTO_SUSPEND = 60;
CREATE WAREHOUSE IF NOT EXISTS TRANSFORM_WH
  WITH WAREHOUSE_SIZE = 'MEDIUM', AUTO_SUSPEND = 60;
CREATE WAREHOUSE IF NOT EXISTS ANALYST_WH
  WITH WAREHOUSE_SIZE = 'XSMALL', AUTO_SUSPEND = 60;
```

Run it from a worksheet, or from a CI/CD pipeline using the
Snowflake CLI or SnowSQL.

## Hands-on

```sql
USE ROLE SYSADMIN;

-- Create the three starter warehouses
CREATE WAREHOUSE IF NOT EXISTS LOADING_WH
  WITH WAREHOUSE_SIZE = 'LARGE', AUTO_SUSPEND = 60;
CREATE WAREHOUSE IF NOT EXISTS TRANSFORM_WH
  WITH WAREHOUSE_SIZE = 'MEDIUM', AUTO_SUSPEND = 60;
CREATE WAREHOUSE IF NOT EXISTS ANALYST_WH
  WITH WAREHOUSE_SIZE = 'XSMALL', AUTO_SUSPEND = 60;

-- Verify
SHOW WAREHOUSES;

-- Drop one to see the error, then recreate
DROP WAREHOUSE IF EXISTS ANALYST_WH;
CREATE WAREHOUSE ANALYST_WH
  WITH WAREHOUSE_SIZE = 'XSMALL', AUTO_SUSPEND = 60;
```

## Quiz prep

- What does `INITIALLY_SUSPENDED = TRUE` do? (Creates the
  warehouse in paused state; no credit burn)
- What command resumes a suspended warehouse? (`ALTER
  WAREHOUSE ... RESUME`)
- What happens if you `DROP` a running warehouse with active
  queries? (The drop fails; suspend first)

## What's next

Next up is **L12 — Setting up warehouse (recap)**, a short
recap lecture tying the UI and SQL workflows together.
