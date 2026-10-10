---
l_id: L114
title: Permanent tables & databases
duration: "4:30"
prereqs: ["L113"]
---

# L114 — Permanent tables & databases

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 16 — Types of tables
> **Duration:** 4:30

## Prereqs

L113 — Different table types. This lecture goes deep on the default
type and on the matching **permanent database**, which has the
strongest recovery guarantees in Snowflake.

## Key terms

- **Permanent database** — the default Snowflake database. All
  schemas and tables created inside it inherit the permanent type
  unless explicitly overridden.
- **Inherited type** — child objects (schemas, tables) inherit the
  type of their parent unless you set it otherwise at creation.
- **Data retention period** — the Time Travel window, in days, for
  a permanent table. Default 1, max 90 (Enterprise).
- **`DATA_RETENTION_TIME_IN_DAYS`** — the parameter that controls
  retention at the account, database, schema, or table level.

## Lecture

Welcome back. Today we focus on the workhorse of any Snowflake
account: the **permanent table** and the **permanent database** that
holds it. If you only ever learn one table type, this is the one.

### Permanent databases

When you run `CREATE DATABASE my_db;` you get a permanent database.
A permanent database can hold both permanent and transient schemas,
and within them both permanent and transient tables. The keyword
choice happens at the *child* level — but the parent itself is
permanent, which means dropping or cloning it triggers the full
disaster-recovery story.

```sql
CREATE DATABASE FINANCE;                                -- permanent db
CREATE SCHEMA FINANCE.RAW;                              -- permanent schema (inherits)
CREATE TABLE     FINANCE.RAW.TRANSACTIONS (...);        -- permanent table (inherits)
```

A permanent database also behaves predictably with Time Travel and
`UNDROP` — if a teammate accidentally drops the database, you have
the configured retention period to bring it back. Transient databases
do not give you that.

### Permanent tables

Permanent tables are the default. The full menu of safety features
applies:

- **Time Travel** up to 90 days (Enterprise Edition; 1 day on Standard).
- **Fail Safe** for an additional 7 days after Time Travel expires.
- **UNDROP** within the retention period.
- **Full clone support** including clones of clones.

The cost is storage. Every byte that lives in Time Travel or Fail
Safe is billed, and the longer the retention, the more you pay. A
common production pattern is to leave `DATA_RETENTION_TIME_IN_DAYS`
at 1 for most tables and raise it selectively for critical ones.

### Configuring retention

```sql
-- Account-wide default
ALTER ACCOUNT SET DATA_RETENTION_TIME_IN_DAYS = 1;

-- Override for one critical table
ALTER TABLE FINANCE.RAW.TRANSACTIONS
  SET DATA_RETENTION_TIME_IN_DAYS = 90;
```

Higher-level settings act as ceilings for lower-level settings. If
the account is set to 1, no table can have a higher value. If a
table is set to 90, only that table gets the 90-day window.

### When permanent is the wrong choice

Permanent tables are slightly slower to drop than transient
tables — Snowflake has to track the historical versions for
retention. If you are dropping and recreating a multi-terabyte
staging table every 10 minutes, that overhead adds up. We'll see
exactly when to switch to transient in L115.

## Hands-on

```sql
USE ROLE SYSADMIN;

CREATE DATABASE IF NOT EXISTS DEMO_PERM;
USE SCHEMA DEMO_PERM.PUBLIC;

CREATE OR REPLACE TABLE TRANSACTIONS (
  txn_id     NUMBER,
  customer   VARCHAR,
  amount     NUMBER(10,2),
  created    TIMESTAMP_NTZ
);

-- Raise retention just for this table
ALTER TABLE TRANSACTIONS SET DATA_RETENTION_TIME_IN_DAYS = 14;

SHOW TABLES LIKE 'TRANSACTIONS';
-- Confirm: kind = PERMANENT, retention_time = 14
```

## Key takeaways

- Permanent databases are the default; they enable the full safety
  net for everything inside.
- Permanent tables support Time Travel, Fail Safe, UNDROP, and
  cloning.
- Retention is configurable per account, database, schema, and
  table; the most specific value wins, bounded by the parent.
- The only reason *not* to use permanent is the storage and
  performance cost on heavily-mutated staging data.

## What's next

L115 finishes the trilogy with **transient and temporary** —
the cheap options for tables that don't need the full safety net.
