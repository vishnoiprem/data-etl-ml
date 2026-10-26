---
l_id: L161
title: Understanding data masking
duration: "4:30"
prereqs: ["L160"]
---

# L161 — Understanding data masking

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 4. Data Masking
> **Duration:** 4:30

## Prereqs

L160 — Limitations + recap.

## Key terms

- **Masking policy** — a Snowflake object that defines a
  function from a value to either the value or a masked
  version, depending on the querying role.
- **Column-level security** — masking is applied at the column
  level. The row is still visible; specific columns are masked.
- **PII** — personally identifiable information. The most
  common use case for masking.

## Lecture

Welcome to the data masking sub-group. A **masking policy** is
a SQL expression that takes a value and returns either the
original value or a masked version, depending on the role of
the user running the query. By the end of this lecture you'll
know when to use one and the high-level pattern.

### The problem

You're a fintech. You have a `customers` table with
`email`, `phone`, and `ssn` columns. Analysts need to query
the table; they need to see the email (to contact customers)
but should *not* see the SSN. The phone is a middle ground —
they need to know it's there but not the digits.

Three solutions:

1. **Don't store the SSN.** Sometimes the right answer; in
   regulated industries, you may be required to.
2. **Restrict table access.** Forces analysts to use a view
   that omits the SSN. Hard to maintain at scale.
3. **Mask the value.** The column exists; the role of the
   querying user decides whether they see the raw value or a
   masked version. This is what masking policies do.

### The masking policy pattern

```sql
CREATE OR REPLACE MASKING POLICY mask_ssn AS (val STRING)
RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('ANALYST_FULL', 'ACCOUNTADMIN')
    THEN val
    ELSE '***-**-****'
  END;
```

A policy is a function. The input is the column value; the
output is what the user sees. The `CASE` expression switches on
the role of the user running the query.

```sql
-- Attach the policy to a column
ALTER TABLE customers MODIFY COLUMN ssn SET MASKING POLICY mask_ssn;
```

After this, every `SELECT ssn FROM customers` returns either the
raw SSN (for `ANALYST_FULL`) or `***-**-****` (for everyone
else).

### The decision rule

| Question | Answer |
|---|---|
| Does the user need the raw value to do their job? | If yes, give them a role that bypasses masking. |
| Is the column only used for joins/lookups? | Mask it; a hash is enough. |
| Is the column a regulatory requirement to mask? | Mask it; the policy is the audit trail. |

### Why not a view?

A view can do column-level filtering, but:

- A view is a *separate object*; consumers can still `SELECT
  ssn` from the underlying table.
- A view doesn't audit "who saw the raw value when". A masking
  policy does (the role check is logged).
- A view is one more thing to maintain. A masking policy is
  attached to the column itself.

### When NOT to use masking

- **The table is already locked down** — a view that omits the
  column works fine.
- **The masking is one-off** — if it's just one column, just
  hash the value at ingest.
- **The role logic is too complex** — if the policy body grows
  past 50 lines, consider a view + custom roles instead.

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE CUSTOMERS (id NUMBER, name VARCHAR, ssn VARCHAR);
INSERT INTO CUSTOMERS VALUES (1, 'alice', '123-45-6789'),
                             (2, 'bob',   '987-65-4321');

CREATE OR REPLACE MASKING POLICY mask_ssn AS (val STRING)
RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('SYSADMIN', 'ACCOUNTADMIN') THEN val
    ELSE '***-**-****'
  END;

ALTER TABLE CUSTOMERS MODIFY COLUMN ssn SET MASKING POLICY mask_ssn;

USE ROLE ANALYST;
SELECT * FROM CUSTOMERS;
-- ssn should be '***-**-****' for both rows.
```

## Key takeaways

- A masking policy is a SQL function attached to a column.
- The output depends on the querying user's role.
- Policies are an audit-friendly way to do column-level
  security.
- For complex logic, fall back to a view.

## What's next

L162 — Creating a masking policy. The full syntax, parameters,
and patterns.