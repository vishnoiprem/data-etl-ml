---
l_id: L163
title: Unset & replace policy
duration: "4:30"
prereqs: ["L162"]
---

# L163 — Unset & replace policy

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 4. Data Masking
> **Duration:** 4:30

## Prereqs

L162 — Creating a masking policy.

## Key terms

- **`UNSET MASKING POLICY`** — detach a policy from a column
  without dropping the policy object.
- **`REPLACE`** — overwrite a policy's body with a new
  expression. The replacement is atomic.
- **Atomic replacement** — Snowflake guarantees that `CREATE
  OR REPLACE MASKING POLICY` is a single transaction. No
  partial state where the old and new bodies are both in
  effect.

## Lecture

Welcome back. Today's lecture is the lifecycle: how to unset
a policy from a column, how to replace a policy's body
in-place, and how to drop a policy entirely. The two gotchas
are "the policy is still attached" (when dropping) and
"the column type changed" (when replacing).

### Unset

```sql
-- Detach a policy from a column
ALTER TABLE customers MODIFY COLUMN ssn UNSET MASKING POLICY;
```

After this, the column is unmasked. The policy object still
exists and can be re-attached.

### Replace

```sql
-- Overwrite a policy's body
CREATE OR REPLACE MASKING POLICY mask_ssn AS (val STRING)
RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN val
    ELSE '***-**-****'
  END;
```

The `OR REPLACE` makes this atomic. Every column that uses
this policy sees the new body instantly, on their next query.

You can also use `ALTER MASKING POLICY`:

```sql
ALTER MASKING POLICY mask_ssn SET BODY ->
  CASE
    WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN val
    ELSE 'REDACTED'
  END;
```

The two forms are equivalent; `ALTER` is preferred when the
policy is in use by many columns because it's more explicit.

### Drop

```sql
-- Drop a policy entirely
DROP MASKING POLICY mask_ssn;
```

You can't drop a policy that's still attached. Snowflake
returns an error like "policy is in use by N columns". You
must first `UNSET` it from every column, then drop.

```sql
-- The standard drop sequence
ALTER TABLE customers MODIFY COLUMN ssn UNSET MASKING POLICY;
ALTER TABLE orders   MODIFY COLUMN ssn UNSET MASKING POLICY;
DROP MASKING POLICY mask_ssn;
```

Or, more easily, drop the table:

```sql
DROP TABLE customers;  -- any policy attached to its columns is automatically unset
DROP MASKING POLICY mask_ssn;
```

### Type changes

If you change a column's data type, the policy's argument
type may no longer match. The most common case: the column
was `STRING` and is now `VARCHAR`. Same data type, no
problem. If the column changes from `STRING` to `NUMBER`, the
policy must be re-written.

```sql
-- Column type change
ALTER TABLE customers MODIFY COLUMN ssn SET DATA TYPE NUMBER(9,2);

-- Policy no longer compatible; replace
CREATE OR REPLACE MASKING POLICY mask_ssn AS (val NUMBER)
RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN TO_VARCHAR(val)
    ELSE '***'
  END;
```

### The safe-replace pattern

When replacing a policy that's in use, follow this order:

1. `CREATE OR REPLACE` (atomic swap).
2. Verify the new behavior with a `SELECT` from a non-privileged
   role.
3. If wrong, `CREATE OR REPLACE` again with the old body.

There's no "rollback to a previous version" — keep your policy
DDL in source control so you can re-run any prior version.

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

-- Unset
ALTER TABLE CUSTOMERS MODIFY COLUMN email UNSET MASKING POLICY;

-- Re-attach with a different policy
CREATE OR REPLACE MASKING POLICY mask_email_v2 AS (val STRING)
RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SALES') THEN val
    ELSE '***'
  END;

ALTER TABLE CUSTOMERS MODIFY COLUMN email SET MASKING POLICY mask_email_v2;

-- Drop
ALTER TABLE CUSTOMERS MODIFY COLUMN email UNSET MASKING POLICY;
DROP MASKING POLICY mask_email_v2;
```

## Key takeaways

- `UNSET MASKING POLICY` detaches without dropping the policy.
- `CREATE OR REPLACE` (or `ALTER MASKING POLICY SET BODY`) is
  atomic.
- `DROP` requires the policy to be unset everywhere first.
- Keep policy DDL in source control for safe rollback.

## What's next

L164 — Alter an existing policy. The `ALTER` form in detail.