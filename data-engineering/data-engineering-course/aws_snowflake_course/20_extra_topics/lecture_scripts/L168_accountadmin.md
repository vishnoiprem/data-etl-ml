---
l_id: L168
title: ACCOUNTADMIN + practice
duration: "5:00"
prereqs: ["L167"]
---

# L168 — ACCOUNTADMIN + practice

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 5. Roles deep-dive
> **Duration:** 5:00

## Prereqs

L167 — Roles overview.

## Key terms

- **Superuser** — `ACCOUNTADMIN` is the only role that is a
  superuser. It bypasses all access controls.
- **Account-level operations** — operations that affect the
  whole account (e.g. resource monitors, network policies)
  require `ACCOUNTADMIN`.
- **Initial setup** — `ACCOUNTADMIN` is required for the
  first steps of any new account: creating the first user,
  setting up SSO, etc.

## Lecture

Welcome back. Today's lecture is the top role in detail:
`ACCOUNTADMIN`. By the end, you should know exactly what it
can do, why it's powerful, and how to use it safely.

### What `ACCOUNTADMIN` can do

Everything. Specifically:

- Create / drop users and roles.
- Grant any privilege to any role.
- Drop any object in the account.
- Bypass masking policies and row-access policies.
- Create / drop account-level resources: resource monitors,
  network policies, integrations.
- Set account-level parameters (`ALTER ACCOUNT SET ...`).
- Drop the entire account.

It also receives all of the privileges of `SECURITYADMIN` and
`SYSADMIN` automatically (because the role hierarchy
inherits).

### When you must use `ACCOUNTADMIN`

A short list of operations that only `ACCOUNTADMIN` can do:

- Creating the very first user in a new account.
- Setting up SSO, SCIM, or federated authentication.
- Creating a resource monitor.
- Creating a network policy.
- Creating a storage integration.
- Bypassing a row-access policy to debug.
- Dropping the entire account.

For everything else — creating databases, tables, views,
grants — `SYSADMIN` is the right role.

### The recommended pattern

1. **Two or three `ACCOUNTADMIN` users.** The account
   owner, a backup, and (optionally) a service account for
   emergency operations.
2. **MFA on every `ACCOUNTADMIN` user.** Always. No
   exceptions.
3. **Use `ACCOUNTADMIN` only for the operations that
   require it.** For everything else, drop to `SYSADMIN` or
   a custom role first.
4. **Audit `ACCOUNTADMIN` usage.** `LOGIN_HISTORY` and
   `QUERY_HISTORY` both filter on role; a weekly review of
   `ACCOUNTADMIN` activity is a strong security control.

### The `ALTER ACCOUNT` operations

`ACCOUNTADMIN` is the only role that can run most
`ALTER ACCOUNT` commands:

```sql
-- These require ACCOUNTADMIN
ALTER ACCOUNT SET RESOURCE_MONITOR = monthly_credit_cap;
ALTER ACCOUNT SET NETWORK_POLICY = corp_policy;
ALTER ACCOUNT SET PARAMETERLESS_AUTOCOMMIT = FALSE;
```

`SYSADMIN` cannot run them. A common newbie error is
switching to `SYSADMIN` and then trying to change an
account-level setting — the error message is
"Insufficient privileges".

### The "elevate, do work, drop" pattern

```sql
-- Step 1: elevate
USE ROLE ACCOUNTADMIN;

-- Step 2: do the one operation that needs it
ALTER ACCOUNT SET RESOURCE_MONITOR = monthly_credit_cap;

-- Step 3: drop back to a lower role
USE ROLE SYSADMIN;

-- ... continue with the rest of the work
```

Most production code elevates to `ACCOUNTADMIN` only for
the duration of a single statement, then drops back.

## Hands-on

```sql
-- Inspect your current role
SELECT CURRENT_ROLE();

-- If you're not ACCOUNTADMIN, switch (only if you have the grant)
USE ROLE ACCOUNTADMIN;

-- Audit
SELECT user_name, role_name, event_timestamp
FROM   TABLE(INFORMATION_SCHEMA.LOGIN_HISTORY())
WHERE  role_name = 'ACCOUNTADMIN'
ORDER BY event_timestamp DESC
LIMIT 20;
```

## Key takeaways

- `ACCOUNTADMIN` is the only superuser; bypasses all security.
- Use it for account-level operations and initial setup only.
- 2–3 `ACCOUNTADMIN` users, all with MFA, audited weekly.
- The elevate-do-drop pattern keeps usage scoped.

## What's next

L169 — SECURITYADMIN + practice. The role for RBAC management.