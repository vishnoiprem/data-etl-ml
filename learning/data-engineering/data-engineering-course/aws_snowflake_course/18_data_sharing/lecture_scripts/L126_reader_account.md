---
l_id: L126
title: Creating a reader account
duration: "5:00"
prereqs: ["L125"]
---

# L126 — Creating a reader account

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 18 — Data Sharing
> **Duration:** 5:00

## Prereqs

L125 — Sharing with non-snowflake users.

## Key terms

- **`CREATE MANAGED ACCOUNT`** — the privileged DDL that creates a
  reader account. Requires `ACCOUNTADMIN`.
- **Reader account locator** — the locator Snowflake assigns to the
  reader account, e.g. `xy98765.us-east-1`.
- **Admin user / password** — the credentials you set when creating
  the account; the consumer uses them to log in.

## Lecture

Welcome back. Today we provision the reader account we discussed in
L125 — a single SQL statement and you're done. The lecture covers
both the SQL and the UI path so you can pick whichever fits your
team.

### The SQL

```sql
USE ROLE ACCOUNTADMIN;

CREATE MANAGED ACCOUNT reader_acme
  ADMIN_NAME = 'admin_acme'
  ADMIN_PASSWORD = 'ChangeMe_2026!'
  TYPE = READER;
```

The required parameters:

- `ADMIN_NAME` — the username of the initial admin user in the
  reader account.
- `ADMIN_PASSWORD` — must meet Snowflake's password complexity
  rules; the consumer will rotate this on first login.
- `TYPE = READER` — required for reader accounts.

Snowflake prints the new locator in the command result:

```text
+-------------------------------+----------+---------+-------------+---------------------+
| reader_account_locator        | name     | url     | created_on  | comment             |
+-------------------------------+----------+---------+-------------+---------------------+
| xy98765.us-east-1             | reader_acme | https://xy98765.us-east-1.snowflakecomputing.com | 2026-10-10 12:34:56 | READER_ACCOUNT |
+-------------------------------+----------+---------+-------------+---------------------+
```

Note that locator — it's what you use as the consumer when
publishing shares (just like any other Snowflake account).

### Sharing with the new reader account

```sql
ALTER SHARE sales_share ADD ACCOUNTS = xy98765.us-east-1;
```

Identical to sharing with a regular consumer. The reader account
will see `sales_share` appear in its *Shares* list the next time
the consumer refreshes.

### Creating the user on the reader account

```sql
-- Switch to the reader account (use the URL printed above).
-- Run as the admin user we just created.
USE ROLE ACCOUNTADMIN;

CREATE USER analyst_acme
  PASSWORD = 'Welcome_2026!'
  LOGIN_NAME = 'analyst_acme'
  DEFAULT_ROLE = 'PUBLIC'
  MUST_CHANGE_PASSWORD = TRUE;
```

`MUST_CHANGE_PASSWORD = TRUE` is the recommended setting; the
consumer will be forced to set their own password on first login.

### Suspending or dropping the reader account

```sql
-- Suspend (cheap): warehouses stop, data still readable
ALTER MANAGED ACCOUNT reader_acme SUSPEND;

-- Drop (irreversible): the entire account is removed
DROP MANAGED ACCOUNT reader_acme;
```

Suspension is the right move when a partner stops consuming; drop
when the relationship ends.

### Common pitfalls

- **Edition.** Your producer account must be on Business Critical
  or higher.
- **Region.** The reader account lives in the producer's region.
  Cross-region shares still work but add latency.
- **Billing.** All reader-account compute is on *your* invoice.

## Hands-on

```sql
-- Pre-flight: confirm edition
USE ROLE ACCOUNTADMIN;
SHOW PARAMETERS LIKE 'ACCOUNT_EDITION';

-- Don't actually run CREATE MANAGED ACCOUNT in this lecture —
-- you'll do it as part of the assignment. Instead, list existing
-- managed accounts (typically empty on a fresh account).
SHOW MANAGED ACCOUNTS;
```

## Key takeaways

- `CREATE MANAGED ACCOUNT ... TYPE = READER` provisions a new
  reader account.
- The new locator is shown in the result — use it as the consumer.
- The producer is billed for all reader-account compute.
- Use `ALTER MANAGED ACCOUNT ... SUSPEND` to pause; `DROP` to
  remove.

## What's next

L127 flips to the **consumer side** — the one-line
`CREATE DATABASE ... FROM SHARE` that mounts the share locally.