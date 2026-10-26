---
l_id: L165
title: Real life examples
duration: "5:00"
prereqs: ["L164"]
---

# L165 — Real life examples

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 4. Data Masking
> **Duration:** 5:00

## Prereqs

L164 — Alter an existing policy.

## Key terms

- **PII redaction** — the most common masking use case.
- **Multi-tenant isolation** — row-level filtering that pairs
  with column-level masking.
- **Audit logging** — using `CURRENT_ROLE()` in the policy
  body to log who saw what.

## Lecture

Welcome to the last lecture in the data masking sub-group.
Today is the practical, end-to-end patterns. Five real-life
use cases, each with the policy SQL you'd ship.

### Example 1: PII redaction (SSN)

```sql
CREATE OR REPLACE MASKING POLICY mask_ssn AS (val STRING)
RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'COMPLIANCE') THEN val
    ELSE '***-**-****'
  END;
```

Use this for any column that holds a US Social Security
Number. The mask is full; only the compliance role sees the
raw value.

### Example 2: partial email mask

```sql
CREATE OR REPLACE MASKING POLICY mask_email AS (val STRING)
RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('SALES_FORCE', 'ACCOUNTADMIN') THEN val
    ELSE REGEXP_REPLACE(val, '^(.{2}).*(@.*)$', '\\1***\\2')
  END;
```

For `alice@example.com`, this returns `al***@example.com`.
Sales still gets the full email; everyone else gets enough to
identify the row, but not the full address.

### Example 3: hash for joinability

```sql
CREATE OR REPLACE MASKING POLICY mask_phone_hash AS (val STRING)
RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'MARKETING') THEN val
    ELSE SHA2(val, 256)
  END;
```

`SHA2` is deterministic. The same phone number always produces
the same hash, so two masked users can still join on the
column. This is the most powerful pattern for analytics: the
data is masked but still joinable.

### Example 4: credit card redaction

```sql
CREATE OR REPLACE MASKING POLICY mask_card AS (val STRING)
RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'PAYMENTS') THEN val
    ELSE CONCAT(LEFT(val, 6), '******', RIGHT(val, 4))
  END;
```

For `4111111111111234`, this returns `411111******1234` —
the BIN (first 6) and last 4 are visible (for fraud
investigation), the rest is masked.

### Example 5: zero for everyone except the owner

```sql
CREATE OR REPLACE MASKING POLICY mask_balance AS (val NUMBER)
RETURNS NUMBER ->
  CASE
    WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN val
    ELSE 0
  END;
```

For numeric columns where the *existence* of the value is
sensitive (a customer's balance, a salary), returning `0` is
sometimes the right answer. The dashboard can still aggregate
over the column; the individual values are useless.

### Combining with row-access policies

Masking is column-level. For row-level filtering (e.g. "user
A can only see their own rows"), use a **row-access policy**.
We'll cover those in a future lecture; for now, the most
common pairing is:

```sql
ALTER TABLE customers
  ADD ROW ACCESS POLICY rap_tenant_isolation ON (tenant_id);

ALTER TABLE customers MODIFY COLUMN ssn SET MASKING POLICY mask_ssn;
```

Row + column security, end-to-end.

## Hands-on

```sql
USE ROLE SYSADMIN;
USE SCHEMA DEMO_DB.PUBLIC;

CREATE OR REPLACE TABLE PAYMENTS (
  id NUMBER,
  card STRING,
  amount NUMBER
);

INSERT INTO PAYMENTS VALUES
  (1, '4111111111111234', 100),
  (2, '5500000000005678', 250);

CREATE OR REPLACE MASKING POLICY mask_card AS (val STRING)
RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN val
    ELSE CONCAT(LEFT(val, 6), '******', RIGHT(val, 4))
  END;

ALTER TABLE PAYMENTS MODIFY COLUMN card SET MASKING POLICY mask_card;

SELECT * FROM PAYMENTS;
-- 'ACCOUNTADMIN' sees the full card; everyone else sees BIN + last 4.
```

## Key takeaways

- Five patterns cover most production use cases: full mask,
  partial mask, hash for joinability, partial card mask,
  zero for everyone except the owner.
- Pair masking (column-level) with row-access policies
  (row-level) for full data security.
- Always log the *why* of a policy in its `COMMENT`.

## What's next

We move on to the **Roles deep-dive** (L166–L173), the
production RBAC patterns.