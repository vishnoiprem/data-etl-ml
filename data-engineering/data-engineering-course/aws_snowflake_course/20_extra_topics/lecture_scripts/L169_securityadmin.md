---
l_id: L169
title: SECURITYADMIN + practice
duration: "5:00"
prereqs: ["L168"]
---

# L169 — SECURITYADMIN + practice

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 5. Roles deep-dive
> **Duration:** 5:00

## Prereqs

L168 — ACCOUNTADMIN + practice.

## Key terms

- **RBAC management** — the right role for adding users,
  creating roles, and granting privileges.
- **Inherits ACCOUNTADMIN** — `SECURITYADMIN` is granted to
  `ACCOUNTADMIN`; it inherits all of those privileges, but
  in practice you don't use them.

## Lecture

Welcome back. Today's lecture is `SECURITYADMIN` — the role
that should own RBAC work in any production account.

### What `SECURITYADMIN` can do

- Create and drop users.
- Create and drop custom roles.
- Grant and revoke roles to/from users and other roles.
- Grant and revoke privileges on any object (including
  those it doesn't own).
- Read the access history (`ACCESS_HISTORY` view).

`SECURITYADMIN` is a child of `ACCOUNTADMIN` in the role
hierarchy, so it inherits all of `ACCOUNTADMIN`'s
privileges. In practice, the *intended* use of
`SECURITYADMIN` is the RBAC subset; using it for object
management is poor hygiene.

### The "people team" pattern

In a well-governed account:

- The security / IAM team has `SECURITYADMIN`.
- Data engineers have `SYSADMIN` and their custom roles.
- The two groups are *different* people. Data engineers
  don't grant each other roles.

The reason: separation of duties. The person who creates a
table should not also be the one who grants access to it.
Otherwise you have one role with all the power and no audit
trail.

### Common operations

```sql
USE ROLE SECURITYADMIN;

-- Add a new user
CREATE USER analyst_bob
  PASSWORD = 'Temp_2026!'
  DEFAULT_ROLE = analyst
  MUST_CHANGE_PASSWORD = TRUE;

-- Grant the role
GRANT ROLE analyst TO USER analyst_bob;

-- Add a new custom role
CREATE ROLE data_steward;
GRANT ROLE data_steward TO ROLE sysadmin;

-- Grant a privilege
GRANT USAGE ON DATABASE finance TO ROLE data_steward;
```

### What `SECURITYADMIN` cannot do

- Drop the account.
- Set account-level parameters (e.g. `RESOURCE_MONITOR`).
- Create integrations (storage, notification, API).
- Bypass masking or row-access policies.

Those require `ACCOUNTADMIN`. `SECURITYADMIN` is for *people
and roles*, not for *infrastructure*.

### The audit pattern

```sql
SELECT user_name, role_name, query_text, start_time
FROM   TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE  role_name = 'SECURITYADMIN'
  AND  start_time > DATEADD('day', -7, CURRENT_TIMESTAMP())
ORDER BY start_time DESC;
```

A weekly review of `SECURITYADMIN` activity is a strong
control. Look for: unusual grants, role changes, user
creations outside business hours.

## Hands-on

```sql
USE ROLE SECURITYADMIN;

-- Create a custom role for analysts
CREATE ROLE IF NOT EXISTS analyst;

-- Add a new user
CREATE USER analyst_carol
  PASSWORD = 'Temp_2026!'
  DEFAULT_ROLE = analyst
  MUST_CHANGE_PASSWORD = TRUE;
GRANT ROLE analyst TO USER analyst_carol;

-- Inspect what you've done
SHOW USERS LIKE 'analyst_carol';
SHOW GRANTS TO USER analyst_carol;
```

## Key takeaways

- `SECURITYADMIN` is the role for RBAC: users, roles,
  grants.
- It inherits `ACCOUNTADMIN`, but use it only for the
  RBAC subset.
- The "people team" pattern: data engineers should not
  grant each other roles.
- Audit `SECURITYADMIN` activity weekly.

## What's next

L170 — SYSADMIN + practice. The workhorse role for day-to-day
data engineering.