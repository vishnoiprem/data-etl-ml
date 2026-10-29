---
l_id: L115
title: Transient + Temporary tables & schemas
duration: "5:00"
prereqs: ["L114"]
---

# L115 — Transient + Temporary tables & schemas

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 16 — Types of tables
> **Duration:** 5:00

## Prereqs

L114 — Permanent tables & databases. You should be comfortable with
the default, because everything here is a deliberate deviation from it.

## Key terms

- **Transient schema / database** — parent that makes every child
  table transient by default. Saves storage, drops Fail Safe.
- **Session** — in Snowflake, the lifetime of a worksheet, a CLI
  connection, or a connection pool. Temporary tables die with it.
- **`SHOW TABLES`** — the command you'll use to verify the kind of
  a table after creating it.

## Lecture

Welcome back. This is the last lecture of section 16, and it answers
the question every cost-conscious engineer asks after seeing the
storage bill: *do I really need Fail Safe on this?* The answer is
often no — and Snowflake gives you two ways to opt out.

### Transient tables

A transient table behaves like a permanent table in every way
except one: it skips Fail Safe. The trade-off is real but bounded:

```text
                   Time Travel max   Fail Safe   Drop speed
 Permanent              90 d          YES        normal
 Transient               1 d          NO         faster
```

Snowflake's docs allow up to 1 day of Time Travel on transient
tables in Enterprise Edition. In practice most teams set
`DATA_RETENTION_TIME_IN_DAYS = 0` for transient staging tables and
just accept that a bad load means re-running the pipeline.

```sql
CREATE OR REPLACE TRANSIENT TABLE STG_RAW_EVENTS (
  event_id   NUMBER,
  payload    VARIANT,
  loaded_at  TIMESTAMP_NTZ
) DATA_RETENTION_TIME_IN_DAYS = 0;
```

### Transient schemas and databases

If most of your tables in a database are staging, lift the keyword
up to the schema or database level so you don't have to repeat it:

```sql
CREATE TRANSIENT DATABASE STAGING;
USE SCHEMA STAGING.PUBLIC;

CREATE TABLE ORDERS_RAW   (...);  -- transient, inherits from db
CREATE TABLE CUSTOMERS_RAW (...); -- transient, inherits from db
```

The inheritance is one-way and downward: a transient database
makes all its child schemas transient, which makes all their child
tables transient. You can still create a permanent table inside a
transient schema by being explicit.

### Temporary tables

A temporary table is the most extreme option. It is:

- **Session-scoped** — dropped automatically when the session ends.
- **Invisible to other sessions** — only the creating session sees it.
- **No Fail Safe**, max 1 day of Time Travel (often set to 0).

```sql
-- Inside a worksheet
CREATE OR REPLACE TEMPORARY TABLE SCRATCH_JOIN (
  id NUMBER,
  amount NUMBER
);

INSERT INTO SCRATCH_JOIN VALUES (1, 100), (2, 250);

SELECT * FROM SCRATCH_JOIN;
-- Close the worksheet → table is gone, automatically.
```

Temporary tables are a great fit for ad-hoc exploration, ad-hoc
joins in a notebook, and any work that you definitely do not want
to persist to disk.

### The mental model

| If your data is... | Use |
|---|---|
| Critical, replaceable only at high cost | permanent |
| Rebuilt from source on every pipeline run | transient |
| Pure session scratch, one-off joins | temporary |

## Hands-on

```sql
-- Build a transient database
CREATE OR REPLACE TRANSIENT DATABASE DEMO_TRAN;
USE SCHEMA DEMO_TRAN.PUBLIC;

-- Children inherit transient by default
CREATE OR REPLACE TABLE RAW_ORDERS (id NUMBER, amount NUMBER);

-- Verify
SHOW TABLES IN SCHEMA DEMO_TRAN.PUBLIC;
-- "kind" column should read: TRANSIENT

-- Drop and recreate — no Fail Safe, so drops are noticeably quicker
DROP TABLE RAW_ORDERS;
```

## Key takeaways

- Transient tables: same as permanent except **no Fail Safe**, max
  1 day Time Travel. Faster drops.
- Transient schema / database propagates the type to all children.
- Temporary tables are session-scoped and invisible to other
  sessions. Use them for scratch work.
- Picking the right type is mostly a cost decision: cheaper
  recovery means cheaper storage.

## What's next

Section 17 is **Zero-Copy Cloning** — and with the table-type
vocabulary under your belt, you can finally understand *why* a
clone of a permanent table has different storage behavior than a
clone of a transient one.
