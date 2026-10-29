---
l_id: L172
title: USERADMIN + practice
duration: "4:30"
prereqs: ["L171"]
---

# L172 — USERADMIN + practice

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 5. Roles deep-dive
> **Duration:** 4:30

## Prereqs

L171 — Custom roles + practice.

## Key terms

- **`USERADMIN`** — manages users and roles (a subset of
  `SECURITYADMIN`).
- **Delegation** — the pattern of giving a helpdesk
  `USERADMIN` instead of `SECURITYADMIN` so they can't
  grant themselves too much power.

## Lecture

Welcome back. Today's lecture is `USERADMIN` — the smallest
of the system-defined roles, but the right one for delegated
user management.

### What `USERADMIN` can do

- Create and drop users.
- Create and drop roles.
- Grant and revoke roles to/from users and other roles.

What it cannot do:

- Grant privileges on database objects (you need
  `SECURITYADMIN` or the object owner for that).
- Create account-level resources.
- Bypass any security policy.

`USERADMIN` is essentially the "create and assign" subset
of `SECURITYADMIN` — it can manage the *people*, but not
the *privileges* those people get on objects.

### When to use `USERADMIN`

The canonical case: a helpdesk that handles "I forgot my
password" and "please add a new user". They need to create
users and assign them to a pre-existing role, but they
should *not* be able to grant privileges on production
databases.

```sql
USE ROLE USERADMIN;

-- Helpdesk: create a new user
CREATE USER analyst_eve
  PASSWORD = 'Temp_2026!'
  DEFAULT_ROLE = analyst
  MUST_CHANGE_PASSWORD = TRUE;

-- Helpdesk: assign to a pre-existing role
GRANT ROLE analyst TO USER analyst_eve;
```

The helpdesk doesn't need `SECURITYADMIN` to do this. They
can do it all with `USERADMIN`.

### When NOT to use `USERADMIN`

If the helpdesk needs to grant a *new* privilege to a role
(e.g. "the analyst team also needs to read the new finance
table"), they need `SECURITYADMIN`. `USERADMIN` is for
people, not privileges.

### The security trade-off

Granting `USERADMIN` is safer than granting
`SECURITYADMIN` because:

- `USERADMIN` cannot grant object-level privileges.
- `USERADMIN` cannot read `ACCESS_HISTORY` (which would
  reveal who accessed what).
- `USERADMIN` cannot change SSO or SCIM configuration.

If the helpdesk account is compromised, the blast radius is
limited to "create and assign users". The compromise can't
escalate to "grant yourself SELECT on production data".

### A typical setup

- 2–3 `ACCOUNTADMIN` users.
- 1–2 `SECURITYADMIN` users (the security team).
- 1–2 `USERADMIN` users (the helpdesk).
- 1 `SYSADMIN` service account (for automation).
- Many custom roles, with the right people in each.

## Hands-on

```sql
USE ROLE USERADMIN;

-- Create a new user (requires USERADMIN or higher)
CREATE USER analyst_frank
  PASSWORD = 'Temp_2026!'
  DEFAULT_ROLE = analyst
  MUST_CHANGE_PASSWORD = TRUE;

GRANT ROLE analyst TO USER analyst_frank;

-- Try to grant a database privilege (should fail)
GRANT USAGE ON DATABASE demo_roles TO ROLE analyst;
-- Insufficient privileges.
```

The last statement will fail with "Insufficient privileges".
That's the right outcome — the `USERADMIN` cannot grant
object privileges.

## Key takeaways

- `USERADMIN` is the people-management subset of
  `SECURITYADMIN`.
- Use it for helpdesk and user-provisioning workflows.
- It cannot grant object privileges — that's the
  safety mechanism.
- Pair with `SECURITYADMIN` for full RBAC control.

## What's next

L173 — PUBLIC role. The default role every user has, and
when to grant on it.