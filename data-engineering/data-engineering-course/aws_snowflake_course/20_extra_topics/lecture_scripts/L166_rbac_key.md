---
l_id: L166
title: Key concepts (RBAC)
duration: "4:30"
prereqs: ["L165"]
---

# L166 — Key concepts (RBAC)

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 5. Roles deep-dive
> **Duration:** 4:30

## Prereqs

L165 — Real life examples (data masking). You should be
comfortable with `CURRENT_ROLE()` and `GRANT`.

## Key terms

- **RBAC** — role-based access control. Permissions are
  attached to roles; users are made members of roles.
- **Role hierarchy** — a role can be granted to another role,
  forming a tree.
- **System role** — a role Snowflake ships with (e.g.
  `ACCOUNTADMIN`).
- **Custom role** — a role you create.
- **Ownership** — a special privilege; the role that owns an
  object has full control over it.

## Lecture

Welcome to the roles deep-dive sub-group. By the end of these
8 lectures you should be able to design a complete RBAC
hierarchy for a Snowflake account. Today's lecture is the
concepts.

### The RBAC model

Snowflake uses a three-tier RBAC model:

```text
   USER  ── belongs to ──>  ROLE  ── has privilege on ──>  OBJECT
```

- A **user** is a person (or service) that logs in.
- A **role** is a named bundle of privileges.
- An **object** is anything you can grant on: databases,
  schemas, tables, views, warehouses, etc.

Users don't get privileges directly; they get *roles*. A user
who has been granted a role inherits all the privileges of
that role. Roles can also be granted to other roles,
forming a hierarchy.

### The role hierarchy

```text
              SYSADMIN
                 │
       ┌─────────┼─────────┐
       │         │         │
   ANALYST_A  ANALYST_B  DATA_ENG
       │                     │
   ┌───┴───┐             ┌───┴───┐
   │       │             │       │
 JR_AN   JR_ANOTHER   ETL_DEV  REPORTING
```

A role that has been granted to another role *passes down* its
privileges. `ETL_DEV` automatically has everything `DATA_ENG`
has, plus its own additional grants.

### System roles

Snowflake ships with these system-defined roles:

- `ACCOUNTADMIN` — top of the hierarchy. Can do anything.
- `SECURITYADMIN` — manages users and roles.
- `USERADMIN` — manages users (subset of `SECURITYADMIN`).
- `SYSADMIN` — creates databases, schemas, tables. The
  recommended home for day-to-day work.
- `PUBLIC` — automatically granted to every user; has no
  privileges by default.

### Custom roles

In production, you build a tree of *custom* roles on top of
`SYSADMIN`:

```sql
CREATE ROLE analyst;
CREATE ROLE data_engineer;
CREATE ROLE etl_developer;

GRANT ROLE data_engineer TO ROLE sysadmin;
GRANT ROLE etl_developer TO ROLE data_engineer;
GRANT ROLE analyst       TO ROLE sysadmin;
```

The pattern: one role per job function, granted under
`SYSADMIN` so they inherit the basic privileges of a working
account.

### Ownership

`OWNERSHIP` is a special privilege. The role that *owns* an
object can drop it, alter it, or transfer ownership. By
default, the role that created the object owns it. In
production, ownership is typically `SYSADMIN` or a custom
role, not a personal role.

### The principle of least privilege

Always grant the *minimum* role that allows the user to do
their job. A new analyst gets `analyst`, not `SYSADMIN`. A
new data engineer gets `data_engineer`, not `ACCOUNTADMIN`.
Resist the temptation to give everyone `ACCOUNTADMIN` — it
bypasses every audit and security control.

## Hands-on

```sql
USE ROLE SECURITYADMIN;

-- Create a custom role hierarchy
CREATE ROLE analyst;
CREATE ROLE data_engineer;

GRANT ROLE analyst       TO ROLE sysadmin;
GRANT ROLE data_engineer TO ROLE sysadmin;

-- A user
CREATE USER analyst_alice
  PASSWORD = 'Temp_2026!'
  DEFAULT_ROLE = analyst
  MUST_CHANGE_PASSWORD = TRUE;

GRANT ROLE analyst TO USER analyst_alice;
```

## Key takeaways

- RBAC: users → roles → privileges → objects.
- Roles can be granted to other roles; privileges cascade.
- Snowflake ships with `ACCOUNTADMIN`, `SECURITYADMIN`,
  `USERADMIN`, `SYSADMIN`, `PUBLIC`.
- Production roles are *custom*, built under `SYSADMIN`.
- Least privilege: grant the smallest role that does the job.

## What's next

L167 — Roles overview. A closer look at the system-defined
roles and when to use each.