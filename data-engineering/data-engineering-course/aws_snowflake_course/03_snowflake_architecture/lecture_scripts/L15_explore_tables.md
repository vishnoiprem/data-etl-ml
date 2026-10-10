---
l_id: L15
title: Exploring tables & databases
duration: "8:00"
prereqs: ["L14"]
downloads: []
---

# L15 — Exploring Tables & Databases

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 3 — Snowflake Architecture
> **Duration:** ~8:00

## Prereqs

L14 — Scaling policy. You should have at least one warehouse
and the `DEMO` database from L12.

## Key terms

- **Database** — a top-level container. In Snowflake a database
  is just a logical grouping of schemas; storage still lives in
  the central S3/ADLS/GCS layer.
- **Schema** — a namespace inside a database. A database must
  contain at least one schema (default: `PUBLIC`).
- **Table** — the actual data, organized as micro-partitions.
- **View** — a saved `SELECT` query. No data is stored; the
  query runs on every access.
- **INFORMATION_SCHEMA** — a per-database schema that exposes
  metadata via standard SQL views (tables, columns, etc.).

## Lecture

In this lecture we explore the table/database/schema hierarchy
in Snowflake, and learn how to inspect objects via
`INFORMATION_SCHEMA` and the `SHOW` commands.

### The hierarchy

```text
Account
└── Database
    └── Schema
        ├── Table
        ├── View
        ├── Stage
        ├── File format
        ├── Sequence
        ├── Pipe
        ├── Task
        └── Stream
```

- An **account** can have many databases.
- A **database** can have many schemas.
- A **schema** can have many tables, views, stages, and other
  objects.

Snowflake accounts have two system databases by default:

- `SNOWFLAKE` — system metadata, account_usage views (only the
  `ACCOUNTADMIN` role can query these by default).
- `SNOWFLAKE_SAMPLE_DATA` — TPC-H, TPC-DS, and weather data
  for learning.

### Creating objects

```sql
USE ROLE SYSADMIN;
USE DATABASE DEMO;
USE SCHEMA ANALYTICS;

-- Schema
CREATE SCHEMA IF NOT EXISTS RAW;

-- Table
CREATE OR REPLACE TABLE RAW.ORDERS (
  order_id    NUMBER        NOT NULL,
  customer_id NUMBER        NOT NULL,
  order_date  DATE,
  amount      NUMBER(10,2),
  status      VARCHAR(20)
);
```

### Inspecting with SHOW

```sql
SHOW DATABABASES;        -- all databases in the account
SHOW SCHEMAS IN DATABASE DEMO;
SHOW TABLES IN SCHEMA DEMO.ANALYTICS;
SHOW COLUMNS IN TABLE DEMO.ANALYTICS.RAW_ORDERS;
```

`SHOW` is the Snowflake-native way to list objects. It returns
rich metadata (created-on, owner, retention time, etc.).

### Inspecting with INFORMATION_SCHEMA

The SQL-standard way:

```sql
SELECT table_schema, table_name, row_count, bytes
FROM DEMO.INFORMATION_SCHEMA.TABLES
WHERE table_schema = 'ANALYTICS';
```

`INFORMATION_SCHEMA` is portable — most queries work the same
in Postgres, SQL Server, BigQuery, etc.

### Views

```sql
CREATE OR REPLACE VIEW HIGH_VALUE_ORDERS AS
  SELECT *
  FROM DEMO.ANALYTICS.RAW_ORDERS
  WHERE amount > 1000;
```

Views are **not materialized** — every access re-runs the
underlying query. For pre-computed views, use a **materialized
view** (covered in section 20).

### Drop / rename

```sql
DROP TABLE DEMO.ANALYTICS.RAW_ORDERS;
DROP VIEW DEMO.ANALYTICS.HIGH_VALUE_ORDERS;

ALTER TABLE DEMO.ANALYTICS.RAW_ORDERS RENAME TO ORDERS_RAW;
```

Snowflake supports the SQL-standard `RENAME TO` syntax, which
is metadata-only (instant) — no data is moved.

## Hands-on

```sql
USE ROLE SYSADMIN;
USE DATABASE DEMO;
USE SCHEMA ANALYTICS;

-- Create a small dataset
CREATE OR REPLACE TABLE REGIONS (
  region_id NUMBER PRIMARY KEY,
  region    VARCHAR(20)
);
INSERT INTO REGIONS VALUES
  (1, 'NA'), (2, 'EMEA'), (3, 'APAC');

-- Inspect
SHOW TABLES IN SCHEMA DEMO.ANALYTICS;
SELECT * FROM REGIONS;
```

## Quiz prep

- What is the difference between a database and a schema?
  (Database = top-level container; schema = namespace inside
  a database)
- What system database has the `ACCOUNT_USAGE` views?
  (`SNOWFLAKE`)
- What is the difference between a view and a materialized
  view? (View = saved SELECT, no data; materialized view =
  pre-computed result)

## What's next

Next up is **L16 — Loading data in Snowflake (intro)**, a
quick orientation lecture before we dive into the loading
methods in section 4.
