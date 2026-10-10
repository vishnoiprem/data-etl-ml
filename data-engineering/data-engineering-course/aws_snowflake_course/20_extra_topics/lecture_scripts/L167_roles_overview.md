---
l_id: L167
title: Roles overview
duration: "4:30"
prereqs: ["L166"]
---

# L167 — Roles overview

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 5. Roles deep-dive
> **Duration:** 4:30

## Prereqs

L166 — Key concepts (RBAC).

## Key terms

- **`ACCOUNTADMIN`** — top of the hierarchy; bypasses all
  security.
- **`SECURITYADMIN`** — manages users, roles, and grants.
- **`USERADMIN`** — manages users (subset of
  `SECURITYADMIN`).
- **`SYSADMIN`** — day-to-day object management.
- **`PUBLIC`** — the role every user has by default; no
  privileges.

## Lecture

Welcome back. Today is a tight tour of the system-defined
roles. By the end of this lecture you should be able to name
what each role does and when to use it.

### The system-defined roles at a glance

| Role | What it can do | When to use it |
|---|---|---|
| `ACCOUNTADMIN` | Everything | Account setup, emergencies |
| `SECURITYADMIN` | Manage users, roles, grants | RBAC work |
| `USERADMIN` | Manage users (subset of `SECURITYADMIN`) | User creation |
| `SYSADMIN` | Create databases, schemas, tables, warehouses | Day-to-day |
| `PUBLIC` | Nothing (by default) | Auto-granted to every user |

### `ACCOUNTADMIN`

The top of the hierarchy. Bypasses every security control —
including masking policies, row-access policies, and
network policies. Snowflake recommends you use it only for
initial account setup and for emergency operations.

In a well-governed account, `ACCOUNTADMIN` is held by 2–3
people, and they use it sparingly. Most day-to-day work
should run as `SYSADMIN` or a custom role.

### `SECURITYADMIN`

Manages users, roles, and grants. The right role for the
"people team" — anyone whose job is to add new users, change
role membership, and audit access.

`SECURITYADMIN` is a child of `ACCOUNTADMIN` in the role
hierarchy, so it inherits `ACCOUNTADMIN`'s privileges. In
practice you don't use those privileges; you use the
RBAC-management ones.

### `USERADMIN`

A subset of `SECURITYADMIN`: user creation and management
only. The right role if you want to delegate "add a new
user" to a helpdesk without giving them full
`SECURITYADMIN` powers.

### `SYSADMIN`

The workhorse role. Creates databases, schemas, tables,
warehouses. The recommended home for ETL jobs, BI tools,
and most application service accounts.

`SYSADMIN` is the parent of every custom role in a typical
production account. Grant `SYSADMIN` to your custom roles
so they inherit the basic privileges.

### `PUBLIC`

Auto-granted to every user; no privileges by default. Use
`PUBLIC` for *very* broadly-shared grants (e.g. a "Welcome"
table that every user should see) — but in practice, almost
nothing should be granted to `PUBLIC`.

### A common production layout

```text
                ACCOUNTADMIN
                      │
                SECURITYADMIN
                 /              \
            USERADMIN         SYSADMIN
                                 │
                          custom roles (analyst, data_eng, ...)
                                 │
                              PUBLIC (everyone)
```

`ACCOUNTADMIN` at the top, custom roles under `SYSADMIN`,
and `PUBLIC` as the broad default.

### The recommended pattern

- `ACCOUNTADMIN` for 2–3 people only.
- `SECURITYADMIN` for the security/rbac team.
- `USERADMIN` for helpdesk / user provisioning.
- `SYSADMIN` for the data team.
- Custom roles under `SYSADMIN` for job functions.
- No grants to `PUBLIC` (except the implicit `USAGE` on
  `PUBLIC` schema in every database).

## Hands-on

```sql
USE ROLE SECURITYADMIN;

-- Inspect the current role hierarchy
SHOW ROLES;
-- Look for: ACCOUNTADMIN, SECURITYADMIN, USERADMIN, SYSADMIN, PUBLIC.

-- Inspect role memberships
SHOW GRANTS TO ROLE sysadmin;
```

## Key takeaways

- `ACCOUNTADMIN` does everything; use sparingly.
- `SECURITYADMIN` and `USERADMIN` manage users and roles.
- `SYSADMIN` is the day-to-day role.
- `PUBLIC` is auto-granted but has no privileges.
- Custom roles go under `SYSADMIN`.

## What's next

L168 — ACCOUNTADMIN + practice. The privileges of the top
role, and the recommended pattern for its use.