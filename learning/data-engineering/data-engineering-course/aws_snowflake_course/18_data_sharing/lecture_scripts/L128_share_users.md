---
l_id: L128
title: Set up users for share
duration: "5:00"
prereqs: ["L127"]
---

# L128 — Set up users for share

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 18 — Data Sharing
> **Duration:** 5:00

## Prereqs

L127 — Creating a database from share. The mount is live; today we
give humans access.

## Key terms

- **Granted database** — the local database created from a share.
  Looks identical to any other database to users.
- **`GRANT USAGE ON DATABASE`** — required for any user to even
  *see* the mounted database in `SHOW DATABASES`.
- **`GRANT USAGE ON SCHEMA`** — required to see the schemas.
- **`GRANT SELECT ON TABLE`** — required to query individual tables.

## Lecture

Welcome back. After L127, your mounted `partner_sales` database
exists but no user can see it. Snowflake's RBAC is *deny by
default* — the database is invisible until you grant permissions.
Today we walk the full grant chain.

### The consumer-side grant chain

```sql
USE ROLE ACCOUNTADMIN;

-- Step 1: a role (typically SYSADMIN or a custom analyst role)
GRANT USAGE ON DATABASE partner_sales TO ROLE analyst_role;

-- Step 2: schema access
GRANT USAGE ON SCHEMA partner_sales.public TO ROLE analyst_role;

-- Step 3: table-level SELECT
GRANT SELECT ON ALL TABLES IN SCHEMA partner_sales.public
  TO ROLE analyst_role;
```

Three grants, in this exact order. Forgetting step 1 is the most
common reason a new user can't see the database at all — the
`SHOW DATABASES` command returns nothing for them.

### Granting to users

Once the role has the right privileges, assign it to a user:

```sql
-- Create the user (if they don't exist)
CREATE USER analyst_alice
  PASSWORD = 'Temp_2026!'
  LOGIN_NAME = 'alice'
  DEFAULT_ROLE = analyst_role
  MUST_CHANGE_PASSWORD = TRUE;

-- Grant the role to the user
GRANT ROLE analyst_role TO USER analyst_alice;
```

`DEFAULT_ROLE` is the role Snowflake activates when the user
logs in. Without it, the user logs in with the `PUBLIC` role,
which has no grants — and `SELECT` will fail.

### Future grants

If the producer later adds *new* tables to the share, the
`GRANT SELECT ON ALL TABLES` from step 3 above doesn't
automatically apply. You need one more statement:

```sql
GRANT SELECT ON FUTURE TABLES IN SCHEMA partner_sales.public
  TO ROLE analyst_role;
```

`FUTURE` is a Snowflake privilege that auto-applies to any new
table created later. Combine it with a manual grant for the
already-existing tables and the consumer is locked in.

### A full worked example

```sql
USE ROLE ACCOUNTADMIN;

-- 1. Custom role
CREATE ROLE analyst_role;

-- 2. Grants on the shared database
GRANT USAGE ON DATABASE partner_sales         TO ROLE analyst_role;
GRANT USAGE ON SCHEMA   partner_sales.public  TO ROLE analyst_role;
GRANT SELECT ON ALL TABLES IN SCHEMA partner_sales.public
                                                 TO ROLE analyst_role;
GRANT SELECT ON FUTURE TABLES IN SCHEMA partner_sales.public
                                                 TO ROLE analyst_role;

-- 3. User
CREATE USER analyst_alice
  PASSWORD = 'Temp_2026!'
  LOGIN_NAME = 'alice'
  DEFAULT_ROLE = analyst_role
  MUST_CHANGE_PASSWORD = TRUE;
GRANT ROLE analyst_role TO USER analyst_alice;
```

After this, `alice` can log in, see `partner_sales` in
`SHOW DATABASES`, and run `SELECT` queries against the shared
tables — all without ever touching the producer's account.

## Hands-on

If you mounted a share in L127, walk the three-step grant chain
above. If not, you can simulate with a sandbox database:

```sql
CREATE DATABASE sandbox_mounts;
USE SCHEMA sandbox_mounts.PUBLIC;
CREATE TABLE ORDERS (id NUMBER);
INSERT INTO ORDERS VALUES (1);

-- Run the three-step grant chain against SANDBOX_MOUNTS
-- to validate the flow before doing it on a real share.
```

## Key takeaways

- Consumer-side access requires three grants: database, schema,
  table.
- `DEFAULT_ROLE` on the user must be a role with the grants; otherwise
  they log in with `PUBLIC` and see nothing.
- Use `GRANT ... ON FUTURE TABLES ...` to auto-grant new tables the
  producer might add later.

## What's next

L129 walks back to the producer side for an end-to-end example of
sharing an entire **database and schema**.