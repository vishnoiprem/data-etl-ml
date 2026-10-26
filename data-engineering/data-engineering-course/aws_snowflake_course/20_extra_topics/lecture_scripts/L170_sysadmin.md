---
l_id: L170
title: SYSADMIN + practice
duration: "5:00"
prereqs: ["L169"]
---

# L170 — SYSADMIN + practice

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 5. Roles deep-dive
> **Duration:** 5:00

## Prereqs

L169 — SECURITYADMIN + practice.

## Key terms

- **Workhorse role** — `SYSADMIN` is the recommended role for
  day-to-day data engineering.
- **Object management** — creating databases, schemas,
  tables, views, warehouses.
- **Custom role parent** — the recommended parent for every
  custom role.

## Lecture

Welcome back. Today's lecture is `SYSADMIN` — the workhorse
role. By the end, you should know what it can do, why it's
the recommended home for most work, and how to use custom
roles under it.

### What `SYSADMIN` can do

- Create / drop databases, schemas, tables, views.
- Create / drop warehouses.
- Create / drop file formats, stages, sequences, pipes,
  tasks, streams, materialized views.
- Grant privileges on objects it owns.
- Use the warehouses, databases, schemas, tables, and views
  it has access to.

`SYSADMIN` cannot:

- Create / drop users or roles (that's `SECURITYADMIN`).
- Set account-level parameters (that's `ACCOUNTADMIN`).
- Bypass masking or row-access policies (those are
  per-user, not per-role).

### Why `SYSADMIN` is the recommended home

Three reasons:

1. **Sufficient privilege.** It can do everything a data
   engineer or analyst needs day-to-day.
2. **Limited blast radius.** It can't create users or set
   account-level parameters. A misclick won't take down the
   whole account.
3. **Audit-friendly.** All `SYSADMIN` activity shows up in
   `QUERY_HISTORY` with the role name. No "unknown
   superuser" mystery.

### Custom roles under `SYSADMIN`

The recommended pattern is to build custom roles *as
children* of `SYSADMIN`:

```sql
USE ROLE SECURITYADMIN;

CREATE ROLE analyst;
CREATE ROLE data_engineer;

GRANT ROLE analyst       TO ROLE sysadmin;
GRANT ROLE data_engineer TO ROLE sysadmin;
```

Why? Because then `analyst` and `data_engineer` inherit
`SYSADMIN`'s privileges, which include the basic ones every
role needs (`USAGE` on `PUBLIC` schema, `WAREHOUSE_USAGE` if
a default is set, etc.).

### Granting custom privileges to a custom role

```sql
USE ROLE SYSADMIN;

-- Create the database
CREATE DATABASE finance;

-- Grant the analyst role access
GRANT USAGE ON DATABASE finance TO ROLE analyst;
GRANT USAGE ON SCHEMA finance.public TO ROLE analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA finance.public TO ROLE analyst;
```

Note that `SYSADMIN` is the one granting the privilege on
`finance` because `SYSADMIN` owns the database. The
`analyst` role is the recipient.

### When to use `SYSADMIN` directly vs a custom role

- **Service accounts** (ETL tools, BI tools, scheduled
  tasks) often use `SYSADMIN` directly. They need broad
  privileges; a custom role would have to be granted
  everything anyway.
- **Human users** (analysts, data engineers) get custom
  roles, granted under `SYSADMIN`. The custom role has
  the *minimum* privileges for the job.

## Hands-on

```sql
USE ROLE SYSADMIN;

-- Create a database and table
CREATE DATABASE IF NOT EXISTS demo_roles;
USE SCHEMA demo_roles.public;

CREATE OR REPLACE TABLE NUMBERS (n NUMBER);
INSERT INTO NUMBERS SELECT SEQ4() FROM TABLE(GENERATOR(ROWCOUNT => 100));

-- Grant access to the analyst role (created in L169)
GRANT USAGE ON DATABASE demo_roles        TO ROLE analyst;
GRANT USAGE ON SCHEMA   demo_roles.public TO ROLE analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA demo_roles.public TO ROLE analyst;

-- Verify as the analyst
USE ROLE analyst;
SELECT * FROM demo_roles.public.numbers LIMIT 5;
```

## Key takeaways

- `SYSADMIN` is the workhorse role for day-to-day work.
- Custom roles are typically granted *to* `SYSADMIN`, so
  they inherit basic privileges.
- Service accounts often use `SYSADMIN` directly; humans
  use custom roles.
- `SYSADMIN` cannot create users or set account
  parameters.

## What's next

L171 — Custom roles + practice. The full design of a
production RBAC hierarchy.