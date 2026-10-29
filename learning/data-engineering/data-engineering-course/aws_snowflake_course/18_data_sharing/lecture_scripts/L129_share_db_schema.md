---
l_id: L129
title: Sharing database & schema
duration: "5:00"
prereqs: ["L128"]
---

# L129 — Sharing database & schema

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 18 — Data Sharing
> **Duration:** 5:00

## Prereqs

L128 — Set up users for share. The consumer-side grant chain
should be second nature.

## Key terms

- **Bulk grant** — `GRANT SELECT ON ALL TABLES IN SCHEMA` is the
  shorthand for granting every current table at once.
- **`SHOW GRANTS TO SHARE`** — the canonical audit command.
- **Outbound share** — the share object created by the producer
  account.

## Lecture

Welcome back. Today we walk the most common producer-side flow in
production: **share an entire schema** with one or more consumer
accounts. This is the pattern you will use over and over for B2B
data distribution.

### The full recipe

```sql
-- Producer side
USE ROLE ACCOUNTADMIN;

-- 1. Create the share
CREATE SHARE finance_share;

-- 2. Grant the database and one schema
GRANT USAGE ON DATABASE FINANCE        TO SHARE finance_share;
GRANT USAGE ON SCHEMA   FINANCE.RAW    TO SHARE finance_share;

-- 3. Grant every table in the schema (and future ones)
GRANT SELECT ON ALL TABLES IN SCHEMA FINANCE.RAW TO SHARE finance_share;
GRANT SELECT ON FUTURE TABLES IN SCHEMA FINANCE.RAW TO SHARE finance_share;

-- 4. Publish to consumers
ALTER SHARE finance_share ADD ACCOUNTS = (
  abc12345.us-east-1,
  xy98765.us-east-1
);
```

Three SQL blocks. After this:

- Every current table in `finance.raw` is shared.
- Every *future* table in `finance.raw` will be shared automatically
  the moment the producer creates it.
- Both consumer accounts can mount the share as a database and read
  all tables in it.

### Choosing what to share

In production, you almost never share the *whole* database — you
share specific schemas. The common patterns:

| Schema name | What's inside | Share to |
|---|---|---|
| `raw` | clean, validated raw data | internal consumers |
| `mart` | conformed dimensions and facts | partner consumers |
| `pii` | regulated data | no one (kept private) |

Sharing the wrong schema is the most common producer-side mistake.
The audit command is `SHOW GRANTS TO SHARE finance_share;` — keep
that handy.

### Removing tables from a share

If you've shared a table by mistake or want to restrict access:

```sql
REVOKE SELECT ON TABLE FINANCE.RAW.SECRET FROM SHARE finance_share;
```

A `REVOKE` on a shared object takes effect immediately. The next
query from any consumer against `SECRET` will fail.

### Auditing

```sql
-- What's in a share?
SHOW GRANTS TO SHARE finance_share;

-- What does this account look like as a consumer?
SHOW SHARES;
-- Filter by `kind = INBOUND` for shares you've mounted.

-- What share members exist?
SHOW GRANTS OF SHARE finance_share;
```

Three commands. Together they cover every "who has access to what"
question you'll be asked in production.

## Hands-on

```sql
-- Producer side
USE ROLE ACCOUNTADMIN;
CREATE DATABASE IF NOT EXISTS FIN_DEMO;
USE SCHEMA FIN_DEMO.PUBLIC;
CREATE TABLE BALANCES (cust VARCHAR, amount NUMBER);
INSERT INTO BALANCES VALUES ('alice', 1000), ('bob', 2500);

CREATE SHARE finance_demo;
GRANT USAGE ON DATABASE FIN_DEMO          TO SHARE finance_demo;
GRANT USAGE ON SCHEMA   FIN_DEMO.PUBLIC   TO SHARE finance_demo;
GRANT SELECT ON ALL TABLES IN SCHEMA FIN_DEMO.PUBLIC TO SHARE finance_demo;
GRANT SELECT ON FUTURE TABLES IN SCHEMA FIN_DEMO.PUBLIC TO SHARE finance_demo;

SHOW GRANTS TO SHARE finance_demo;
```

## Key takeaways

- Share entire schemas, not random selections of tables — easier to
  reason about.
- Always pair `ALL TABLES` with `FUTURE TABLES` so new tables are
  picked up automatically.
- `SHOW GRANTS TO SHARE` is the canonical audit.
- Use `REVOKE SELECT` to take a table back; takes effect immediately.

## What's next

L130 introduces **secure views** — the only kind of view you can
share, and the foundation of row- and column-level security in
Snowflake.