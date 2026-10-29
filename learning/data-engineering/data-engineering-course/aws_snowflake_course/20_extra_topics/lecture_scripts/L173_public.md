---
l_id: L173
title: PUBLIC role
duration: "4:00"
prereqs: ["L172"]
---

# L173 — PUBLIC role

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 5. Roles deep-dive
> **Duration:** 4:00

## Prereqs

L172 — USERADMIN + practice.

## Key terms

- **`PUBLIC`** — a built-in role that every user has,
  automatically. Has no privileges by default.
- **Implicit grants** — Snowflake auto-grants certain
  privileges to `PUBLIC` (e.g. `USAGE` on the `PUBLIC`
  schema in every database).
- **Revoking from `PUBLIC`** — supported, but use caution.

## Lecture

Welcome to the last lecture in the Roles deep-dive sub-group.
Today: `PUBLIC` — the role every user has, automatically.

### What `PUBLIC` is

`PUBLIC` is a built-in Snowflake role. Every user is
automatically a member of `PUBLIC` — you can't remove them
from it. By default, `PUBLIC` has *no* privileges on
anything.

### The implicit grants

Snowflake auto-grants certain privileges to `PUBLIC` so that
basic operations work out of the box:

- `USAGE` on the `PUBLIC` schema in every database.
- `USAGE` on `WAREHOUSE = PUBLIC` (if a warehouse is named
  `PUBLIC`, which is rare).

These are the only default grants. Everything else — every
table, every view, every stage — is deny by default.

### When to grant to `PUBLIC`

Almost never. The legitimate cases:

- A "Welcome" or "About" table that every user should see.
- A `FILE_FORMAT` that's used by every consumer.
- A `STAGE` for shared data uploads.

In all cases, the access is to a *specific object*, not a
broad class.

### When NOT to grant to `PUBLIC`

- **Sensitive data.** `PUBLIC` includes every user, including
  external readers (if you have any). Don't grant PII to
  `PUBLIC`.
- **Wide classes of objects.** "Grant USAGE on all tables in
  this database to PUBLIC" is the wrong abstraction. Use a
  proper role.
- **Privilege escalation.** `PUBLIC` is a member of every
  user; granting a powerful privilege to `PUBLIC` gives it
  to everyone.

### Revoking from `PUBLIC`

You can revoke implicit grants from `PUBLIC` if you want
a stricter default:

```sql
-- Revoke USAGE on a specific database's PUBLIC schema from PUBLIC
REVOKE USAGE ON SCHEMA my_db.public FROM ROLE PUBLIC;
```

Be careful: revoking from `PUBLIC` affects every user, not
just the ones you intended. In practice, the implicit grants
on `PUBLIC` are usually left alone.

### The decision rule

> If a grant should apply to "every user including
> future users I haven't thought of", put it on `PUBLIC`.
> Otherwise, put it on a custom role.

This is a high bar; `PUBLIC` should be the empty role by
default.

### Inspecting `PUBLIC` grants

```sql
SHOW GRANTS TO ROLE public;
```

The result is the list of implicit grants Snowflake ships
with. Anything else, you or a predecessor granted.

## Hands-on

```sql
-- Inspect PUBLIC's grants
SHOW GRANTS TO ROLE public;

-- Confirm PUBLIC has no privileges on a custom database
USE SCHEMA my_db.public;
SHOW GRANTS TO ROLE public;
-- Should be only the auto-grants: USAGE on the schema itself.
```

## Key takeaways

- `PUBLIC` is a built-in role every user has.
- By default, it has only the implicit `USAGE` on `PUBLIC`
  schema in every database.
- Don't grant PII or broad access to `PUBLIC`.
- Use a custom role for everything else.

## What's next

We move on to **BI Tools** (L174–L181), where we wire
Snowflake up to Power BI, Tableau, and the Snowflake
Marketplace.