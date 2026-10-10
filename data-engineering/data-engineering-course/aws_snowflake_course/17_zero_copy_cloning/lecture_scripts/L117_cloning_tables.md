---
l_id: L117
title: Cloning tables
duration: "5:00"
prereqs: ["L116"]
---

# L117 — Cloning tables

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 17 — Zero-Copy Cloning
> **Duration:** 5:00

## Prereqs

L116 — Understanding Zero-Copy Cloning. The micro-partition model
should already make sense.

## Key terms

- **`CREATE TABLE ... CLONE`** — the DDL keyword that creates a
  zero-copy clone of an existing table.
- **Clone grants** — by default the new table inherits the source
  table's access control. You can re-grant after the fact.
- **Cloning a clone** — fully supported. Clones can be cloned any
  number of times.

## Lecture

Welcome back. Today we make it concrete: one source table, one clone,
one divergence, one observable bill change.

### The basic syntax

```sql
-- Same database / schema
CREATE TABLE orders_clone CLONE orders;

-- Different schema
CREATE TABLE sandbox.orders_clone CLONE prod.public.orders;

-- Different database, different schema
CREATE TABLE sandbox.dba.orders_clone CLONE prod.public.orders;
```

That's it. No `AS SELECT`, no data movement, no waiting. The clone
inherits the table's:

- column definitions and types
- clustering keys
- data (logically — physically shared until divergence)
- masking and row-access policies
- comments

It does **not** inherit:

- the source table's grants, by default
- the source table's outbound shares
- the source table's streams (we'll see those in section 20)

### A complete end-to-end example

```sql
USE ROLE SYSADMIN;

CREATE DATABASE IF NOT EXISTS PROD;
CREATE DATABASE IF NOT EXISTS DEV;

CREATE OR REPLACE TABLE PROD.PUBLIC.ORDERS (
  id        NUMBER,
  amount    NUMBER(10,2),
  customer  VARCHAR,
  created   TIMESTAMP_NTZ
);

INSERT INTO PROD.PUBLIC.ORDERS
  SELECT SEQ4(), UNIFORM(1, 1000, RANDOM()), 'cust_' || SEQ4(), CURRENT_TIMESTAMP()
  FROM TABLE(GENERATOR(ROWCOUNT => 100000));

-- Instant clone for dev
CREATE OR REPLACE TABLE DEV.PUBLIC.ORDERS CLONE PROD.PUBLIC.ORDERS;

-- Both tables now show the same row count
SELECT 'PROD' AS src, COUNT(*) AS rows FROM PROD.PUBLIC.ORDERS
UNION ALL
SELECT 'DEV',  COUNT(*)          FROM DEV.PUBLIC.ORDERS;
```

### Watching divergence

After the clone, run a divergent write in *both* tables and watch
`TABLE_STORAGE_METRICS`:

```sql
INSERT INTO PROD.PUBLIC.ORDERS VALUES (9999999, 1, 'new_prod', CURRENT_TIMESTAMP());
INSERT INTO DEV.PUBLIC.ORDERS  VALUES (8888888, 1, 'new_dev',  CURRENT_TIMESTAMP());

SELECT table_name, active_bytes
FROM   TABLE(INFORMATION_SCHEMA.TABLE_STORAGE_METRICS(
            TABLE_NAME => 'ORDERS', SCHEMA_NAME => 'PUBLIC'));
```

You'll see `active_bytes` start to climb for each table as Snowflake
writes new micro-partitions for the divergent rows.

### Clone of a clone

```sql
CREATE OR REPLACE TABLE DEV.PUBLIC.ORDERS_SCRATCH CLONE DEV.PUBLIC.ORDERS;
-- All three tables share partitions where possible.
```

This is how production teams build "scratch from dev from prod"
chains without doubling storage twice.

## Hands-on

```sql
-- Reset
DROP DATABASE IF EXISTS DEMO_CLONE;
CREATE DATABASE DEMO_CLONE;

USE SCHEMA DEMO_CLONE.PUBLIC;
CREATE TABLE NUMBERS (n NUMBER);
INSERT INTO NUMBERS SELECT SEQ4() FROM TABLE(GENERATOR(ROWCOUNT => 5000));

-- Clone it
CREATE TABLE NUMBERS_BACKUP CLONE NUMBERS;

-- Compare metadata
SELECT table_name, active_bytes
FROM   TABLE(INFORMATION_SCHEMA.TABLE_STORAGE_METRICS(
            TABLE_NAME => 'NUMBERS', SCHEMA_NAME => 'PUBLIC', DB_NAME => 'DEMO_CLONE'));
-- Both tables should report identical (and small) active_bytes.
```

## Key takeaways

- `CREATE TABLE x CLONE y` is the only syntax you need for table clones.
- The clone inherits structure but not grants; re-grant explicitly
  when needed.
- Cloning a clone is supported and cheap.
- Storage divergence is observable through
  `TABLE_STORAGE_METRICS`.

## What's next

L118 lifts the same idea to **schemas and databases** — a one-line
clone that captures an entire logical container.