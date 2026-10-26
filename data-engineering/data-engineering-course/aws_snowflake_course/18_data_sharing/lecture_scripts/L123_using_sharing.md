---
l_id: L123
title: Using data sharing
duration: "4:30"
prereqs: ["L122"]
---

# L123 — Using data sharing

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 18 — Data Sharing
> **Duration:** 4:30

## Prereqs

L122 — Understanding data sharing. The producer/consumer model
should already make sense.

## Key terms

- **`CREATE SHARE`** — creates an empty share object.
- **`GRANT USAGE ON DATABASE`** — grants a database to a share.
- **`GRANT USAGE ON SCHEMA`** — grants a schema to a share.
- **`GRANT SELECT ON TABLE`** — grants a table to a share.
- **`ALTER SHARE ... ADD ACCOUNTS = ...`** — publishes the share
  to one or more consumer accounts.
- **`<account_locator>`** — the producer's account identifier,
  e.g. `abc12345.us-east-1`.

## Lecture

Welcome back. Today we go end-to-end through the SQL surface of
data sharing. By the end of this lecture you will be able to share
a single table with one consumer account using three statements.

### The full SQL recipe

```sql
-- 1. Create the share (one-time)
CREATE SHARE sales_share;

-- 2. Allow the share to USE a database and schema
GRANT USAGE ON DATABASE sales_db      TO SHARE sales_share;
GRANT USAGE ON SCHEMA   sales_db.raw  TO SHARE sales_share;

-- 3. Expose the table itself
GRANT SELECT ON TABLE   sales_db.raw.orders TO SHARE sales_share;

-- 4. Publish to one or more consumer accounts
ALTER SHARE sales_share ADD ACCOUNTS = abc12345.us-east-1;
```

That's it. The consumer can now mount the share as a database:

```sql
-- Consumer side
CREATE DATABASE consumer_sales FROM SHARE producer_account.sales_share;
```

### What's actually being granted

Each of those four statements is *necessary*. A common beginner
mistake is to skip step 2 (the schema grant). Without
`USAGE ON SCHEMA`, the table grant is invisible to the consumer and
they get a "permission denied" error. The order of grants is also
strict: you can't grant on a table inside a schema you haven't
granted `USAGE` on.

### Sharing multiple objects

Repeat steps 2–3 for every schema and table you want to expose. You
can also grant `SELECT ON ALL TABLES IN SCHEMA` to save keystrokes:

```sql
GRANT SELECT ON ALL TABLES IN SCHEMA sales_db.raw TO SHARE sales_share;
```

This pattern is exactly what you'll use in L132 when sharing data
drawn from multiple databases.

### Account locators

The `abc12345.us-east-1` identifier is the **account locator** —
Snowflake's region-qualified name. You can find yours in the
Snowflake UI under *Account → Account details*, or programmatically:

```sql
SELECT CURRENT_ACCOUNT_NAME(), CURRENT_REGION();
```

When sharing across regions, the consumer's locator must match the
region they want the share to live in. If you share `us-east-1` data
to a `eu-west-1` consumer, Snowflake will silently refuse or warn
about cross-region latency.

### Revoking access

```sql
-- Remove a consumer from a share
ALTER SHARE sales_share REMOVE ACCOUNTS = abc12345.us-east-1;

-- Drop the share entirely
DROP SHARE sales_share;
```

Dropping a share is instantaneous and does not affect any database
the consumer has already mounted; the consumer simply loses access
on their next query.

## Hands-on

```sql
-- Producer side (use a sandbox account)
USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS DEMO_SHARE;
USE SCHEMA DEMO_SHARE.PUBLIC;

CREATE OR REPLACE TABLE ORDERS (id NUMBER, amount NUMBER, region VARCHAR);
INSERT INTO ORDERS VALUES (1, 100, 'NA'), (2, 200, 'EU');

CREATE SHARE demo_share;
GRANT USAGE ON DATABASE DEMO_SHARE      TO SHARE demo_share;
GRANT USAGE ON SCHEMA   DEMO_SHARE.PUBLIC TO SHARE demo_share;
GRANT SELECT ON TABLE   DEMO_SHARE.PUBLIC.ORDERS TO SHARE demo_share;

SHOW SHARES;
-- Confirm "demo_share" appears with no consumers yet.
```

## Key takeaways

- A complete share requires grants on database, schema, and table.
- `ALTER SHARE ... ADD ACCOUNTS = ...` publishes to consumers.
- Use `SELECT ON ALL TABLES IN SCHEMA` to bulk-grant.
- Account locators are `name.region`; you can find them with
  `CURRENT_ACCOUNT_NAME()` and `CURRENT_REGION()`.

## What's next

L124 walks the same flow through the **Snowflake UI** for teams that
prefer clicks over SQL.