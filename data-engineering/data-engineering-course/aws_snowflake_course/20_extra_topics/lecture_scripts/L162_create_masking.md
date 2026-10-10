---
l_id: L162
title: Creating a masking policy
duration: "5:00"
prereqs: ["L161"]
---

# L162 — Creating a masking policy

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 4. Data Masking
> **Duration:** 5:00

## Prereqs

L161 — Understanding data masking.

## Key terms

- **`CREATE MASKING POLICY`** — the DDL for a masking policy.
- **`->` operator** — separates the input parameters from the
  return expression.
- **`ALTER TABLE ... MODIFY COLUMN ... SET MASKING POLICY`**
  — attaches a policy to a column.

## Lecture

Welcome back. Today we cover the full syntax of `CREATE MASKING
POLICY`, the parameters that matter, and the canonical patterns
for common data types.

### The full syntax

```sql
CREATE [ OR REPLACE ] MASKING POLICY [ IF NOT EXISTS ] <name>
  AS ( <arg1> <type1> [, <arg2> <type2>, ...] )
  RETURNS <return_type> ->
  <expression>;
```

Three pieces:

- The **arguments** are the column values the policy receives.
  For a column-level policy, that's one argument.
- The **return type** matches the column's type (or a
  compatible type).
- The **expression** is the body — typically a `CASE` that
  switches on `CURRENT_ROLE()` or `CURRENT_ACCOUNT()`.

### A simple example: email

```sql
CREATE OR REPLACE MASKING POLICY mask_email AS (val STRING)
RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('SALES_FORCE') THEN val
    ELSE REGEXP_REPLACE(val, '^(.{2}).*(@.*)$', '\\1***\\2')
  END;
```

For `SALES_FORCE`, the full email is returned. For everyone
else, the middle is replaced with `***`. (`alice@example.com`
becomes `al***@example.com`.)

### A common pattern: full-mask for everyone except one role

```sql
CREATE OR REPLACE MASKING POLICY mask_ssn AS (val STRING)
RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN val
    ELSE '***-**-****'
  END;
```

This is the most common pattern in production: one role
gets the raw value, everyone else gets a fixed mask.

### A more nuanced pattern: hash for non-privileged

```sql
CREATE OR REPLACE MASKING POLICY hash_email AS (val STRING)
RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('SALES_FORCE', 'MARKETING') THEN val
    ELSE SHA2(val, 256)
  END;
```

`SHA2` returns a deterministic hash. The same email always
hashes to the same value, so joins on the masked column
*still work* — a powerful property for analytics.

### Attaching and detaching

```sql
-- Attach
ALTER TABLE customers
  MODIFY COLUMN ssn
  SET MASKING POLICY mask_ssn;

-- Detach (without dropping the policy)
ALTER TABLE customers
  MODIFY COLUMN ssn
  UNSET MASKING POLICY;
```

A policy is unattached but the policy object remains; you can
re-attach to a different column.

### When to use one policy per column vs shared policies

- **One policy per column** is the cleanest pattern. The
  policy name documents the masking behavior.
- **Shared policies** (e.g. `mask_string_default`) work but
  make audit harder.

In production, prefer one policy per column. The naming
convention `mask_<column_name>` is the most common.

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE CUSTOMERS (id NUMBER, email VARCHAR);

INSERT INTO CUSTOMERS VALUES
  (1, 'alice@example.com'),
  (2, 'bob@example.com');

CREATE OR REPLACE MASKING POLICY mask_email AS (val STRING)
RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN val
    ELSE REGEXP_REPLACE(val, '^(.{2}).*(@.*)$', '\\1***\\2')
  END;

ALTER TABLE CUSTOMERS MODIFY COLUMN email SET MASKING POLICY mask_email;

SELECT * FROM CUSTOMERS;
-- 'ACCOUNTADMIN' sees the raw email; everyone else sees the masked form.
```

## Key takeaways

- `CREATE MASKING POLICY` takes args, a return type, and an
  expression.
- The expression typically switches on `CURRENT_ROLE()`.
- `SET MASKING POLICY` attaches; `UNSET MASKING POLICY` detaches.
- Use one policy per column for audit clarity.

## What's next

L163 — Unset & replace policy. Lifecycle operations on policies.