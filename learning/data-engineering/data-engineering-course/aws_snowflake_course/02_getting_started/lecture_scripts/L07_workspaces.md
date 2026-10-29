---
l_id: L07
title: Understanding Workspaces & Querying Data
duration: "7:00"
prereqs: ["L06"]
downloads: []
---

# L07 — Understanding Workspaces & Querying Data

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 2 — Getting Started
> **Duration:** ~7:00

## Prereqs

L06 — Getting to know the interface. You should be able to log
in and navigate the left sidebar.

## Key terms

- **Workspace** — Snowflake's folder for grouping worksheets
  and dashboards. Each user gets a default personal workspace.
- **Stage** — a location where data files are stored (internal
  or external). We cover stages in detail in section 4.
- **File format** — a named object describing how to parse
  CSV/JSON/Parquet files (delimiter, header, compression, etc.).
- **Result cache** — Snowflake caches the result of every query
  for 24 hours; identical queries within that window return
  instantly without re-running.

## Lecture

In this lecture we look at the workspace model in Snowflake and
write our first real queries against the sample data.

### Worksheet workspaces

Snowsight groups worksheets into **workspaces**. A workspace
is a folder that holds worksheets, dashboards, and shared
content. By default you have:

- **Personal** — your private worksheets. No one else sees them.
- **Shared with you** — worksheets other users have shared.
- **Team workspaces** — pre-created in larger orgs; can be
  granted to specific roles.

> **Tip.** Create one workspace per project — e.g. "Loading
> Pipeline", "Reporting", "Ad-hoc Analysis". Worksheets inside
> a workspace inherit the workspace's role and warehouse
> defaults.

### Switching context (database, schema, warehouse, role)

In a worksheet, set the context you want every query in the
session to use:

```sql
USE ROLE SYSADMIN;
USE WAREHOUSE COMPUTE_WH;
USE DATABASE SNOWFLAKE_SAMPLE_DATA;
USE SCHEMA TPCH_SF1;
```

This is the Snowflake equivalent of `cd`'ing into a directory.
Once you set the context, every subsequent query runs in it
until you change it.

Alternatively, fully qualify object names — this is verbose
but very explicit:

```sql
SELECT COUNT(*)
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.NATION;
```

Most production SQL uses the explicit form because it survives
copy-paste across worksheets with different contexts.

### Querying the sample TPC-H data

TPC-H is the industry-standard decision-support benchmark.
Snowflake provides a 1TB sample dataset in
`SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`. The schema models a wholesale
supplier with tables like:

- `REGION`, `NATION` — geography
- `SUPPLIER`, `CUSTOMER` — business entities
- `PART`, `PARTSUPP` — products
- `ORDERS`, `LINEITEM` — sales

A classic TPC-H query — top customers by order value:

```sql
SELECT C_CUSTKEY,
       C_NAME,
       SUM(O_TOTALPRICE) AS total_spend
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER
JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS
  ON C_CUSTKEY = O_CUSTKEY
WHERE O_ORDERDATE >= '1995-01-01'
GROUP BY C_CUSTKEY, C_NAME
ORDER BY total_spend DESC
LIMIT 10;
```

The first run will take a few seconds (cold cache, query
compilation). The second run will return in milliseconds
because of the **result cache**.

### Result cache in action

Run the same query twice and check **Query History** — the
second run reports a different status: `Result reused from
cache` and 0% of warehouse time billed.

> The result cache is keyed on the **full SQL text** plus
> the user's role. Changing a single space, a comment, or
> the role invalidates the cache for that query.

### Inspecting the query profile

Click any query in Query History → **Query Profile** to see
the execution plan. The query profile is the single most
important debugging tool in Snowflake — it shows:

- How the planner parallelized the query.
- How many micro-partitions each operator scanned.
- Where time was spent (spilling to disk, partition pruning,
  join reordering).
- Bytes scanned per table.

We use the query profile heavily in the performance section.

## Hands-on

```sql
-- Create your own demo database
USE ROLE SYSADMIN;
CREATE DATABASE IF NOT EXISTS DEMO;
USE DATABASE DEMO;
CREATE SCHEMA IF NOT EXISTS ANALYTICS;

-- Create a small table and load data via INSERT
CREATE OR REPLACE TABLE SALES (
  sale_id     NUMBER AUTOINCREMENT,
  sale_date   DATE,
  amount      NUMBER(10,2),
  region      VARCHAR
);

INSERT INTO SALES (sale_date, amount, region) VALUES
  ('2024-01-15', 1200.00, 'NA'),
  ('2024-01-16',  890.50, 'EMEA'),
  ('2024-01-17', 1500.00, 'APAC');

SELECT region, SUM(amount) AS total
FROM SALES
GROUP BY region
ORDER BY total DESC;
```

You should see three rows summing the sales by region.

## Quiz prep

- What does the `USE` statement control? (Session context —
  role, warehouse, database, schema)
- How long does the result cache live? (24 hours)
- What does the **Query Profile** show? (Execution plan,
  bytes scanned, partition pruning, time per operator)

## What's next

Next up is **L08 — Snowflake architecture**, where we cover
the three-layer architecture (storage, compute, cloud
services) that drives every Snowflake decision.
