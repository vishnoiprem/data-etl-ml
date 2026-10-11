---
l_id: L164
title: Alter an existing policy
duration: "4:30"
prereqs: ["L163"]
---

# L164 — Alter an existing policy

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 4. Data Masking
> **Duration:** 4:30

## Prereqs

L163 — Unset & replace policy.

## Key terms

- **`ALTER MASKING POLICY`** — the explicit alter form. Sets
  the body or renames the policy.
- **`SET BODY`** — replace the masking expression in place.
- **`RENAME TO`** — rename a policy object.

## Lecture

Welcome back. Today's lecture is the `ALTER` form in detail.
While `CREATE OR REPLACE` works for most teams, `ALTER` gives
you finer control and is the form that most production code
reviews look for.

### The `ALTER` syntax

```sql
ALTER MASKING POLICY <name> SET BODY -> <expression>;
ALTER MASKING POLICY <name> RENAME TO <new_name>;
ALTER MASKING POLICY <name> SET COMMENT = '<text>';
```

The two operations most teams use: `SET BODY` (update the
expression) and `RENAME TO` (rename after a refactor).

### `SET BODY` in practice

```sql
-- Original
CREATE OR REPLACE MASKING POLICY mask_ssn AS (val STRING)
RETURNS STRING ->
  CASE WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN val
       ELSE '***-**-****' END;

-- Add a new role to the allowed list
ALTER MASKING POLICY mask_ssn SET BODY ->
  CASE WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'COMPLIANCE') THEN val
       ELSE '***-**-****' END;
```

`SET BODY` is atomic. The next query against any column using
`mask_ssn` sees the new body. No rebuild, no downtime.

### `RENAME TO` in practice

Renaming is a metadata operation. It's instant, but columns
that reference the policy by name will pick up the new name
on the next refresh.

```sql
ALTER MASKING POLICY mask_ssn RENAME TO mask_ssn_v2;
```

After this, `SHOW MASKING POLICIES` lists the new name. Any
column that was using `mask_ssn` is now using `mask_ssn_v2`.

### `SET COMMENT` in practice

```sql
ALTER MASKING POLICY mask_ssn SET COMMENT = 'Masks SSN; raw only for ACCOUNTADMIN + COMPLIANCE';
```

Comments are surfaced in Snowsight and `SHOW` output. Use them
to record *why* a policy exists and *who* approved it.

### `ALTER` vs `CREATE OR REPLACE`

| Operation | `ALTER` | `CREATE OR REPLACE` |
|---|---|---|
| Update body | ✓ | ✓ |
| Rename | ✓ | ✗ (must drop & recreate) |
| Atomic | ✓ | ✓ |
| Affects attached columns | Yes, instantly | Yes, instantly |

`ALTER` is preferred when you want to keep the policy name and
update only the body. `CREATE OR REPLACE` is preferred when
you're changing the signature (args, return type).

### A worked example

```sql
-- Start: a working policy
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE MASKING POLICY mask_phone AS (val STRING)
RETURNS STRING ->
  CASE WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN val
       ELSE REGEXP_REPLACE(val, '^(\d{3}).*', '\\1-***-****') END;

-- Audit logs reveal the masking is too tight — Marketing also needs raw
ALTER MASKING POLICY mask_phone SET BODY ->
  CASE WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'MARKETING') THEN val
       ELSE REGEXP_REPLACE(val, '^(\d{3}).*', '\\1-***-****') END;

-- Confirm
SHOW MASKING POLICIES LIKE 'mask_phone';
-- The "comment" field can be updated here too
ALTER MASKING POLICY mask_phone SET COMMENT = 'Raw for ADMIN + MARKETING; partial mask for others';
```

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

ALTER MASKING POLICY mask_ssn SET BODY ->
  CASE WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'COMPLIANCE') THEN val
       ELSE '***-**-****' END;

ALTER MASKING POLICY mask_ssn SET COMMENT = 'SSN mask; raw for ADMIN + COMPLIANCE';
SHOW MASKING POLICIES;
```

## Key takeaways

- `ALTER MASKING POLICY SET BODY` updates the expression
  atomically.
- `RENAME TO` and `SET COMMENT` round out the alter form.
- `ALTER` keeps the policy name; `CREATE OR REPLACE` is for
  signature changes.
- Comments document the *why* of a policy — keep them updated.

## What's next

L165 — Real life examples. End-to-end patterns for PII redaction,
multi-tenant isolation, and audit logging.