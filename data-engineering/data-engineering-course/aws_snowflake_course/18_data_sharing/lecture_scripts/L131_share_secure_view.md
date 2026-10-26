---
l_id: L131
title: Sharing a secure view
duration: "5:00"
prereqs: ["L130"]
---

# L131 — Sharing a secure view

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 18 — Data Sharing
> **Duration:** 5:00

## Prereqs

L130 — Secure vs. normal view.

## Key terms

- **Predicate exposure** — when a normal view's `WHERE` clause
  becomes visible to the consumer and lets them infer data they
  shouldn't see.
- **View grant on a share** — the explicit `GRANT SELECT ON VIEW`
  statement required to include a view in a share.

## Lecture

Welcome back. Today we put it all together. We will share a single
secure view from the producer side, then mount it on the consumer
side. By the end of this lecture you should be able to set up the
same pattern for your own data.

### The producer-side recipe

```sql
-- Producer
USE ROLE ACCOUNTADMIN;

-- 1. Create the secure view
USE SCHEMA FIN_DEMO.PUBLIC;

CREATE OR REPLACE SECURE VIEW eu_only AS
  SELECT id, customer, amount
  FROM   ORDERS
  WHERE  region = 'EU';

-- 2. Create the share (if not already)
CREATE SHARE if not exists finance_view_share;

-- 3. Grant database, schema, view
GRANT USAGE ON DATABASE FIN_DEMO          TO SHARE finance_view_share;
GRANT USAGE ON SCHEMA   FIN_DEMO.PUBLIC   TO SHARE finance_view_share;
GRANT SELECT ON VIEW    FIN_DEMO.PUBLIC.EU_ONLY TO SHARE finance_view_share;

-- 4. Publish
ALTER SHARE finance_view_share ADD ACCOUNTS = abc12345.us-east-1;
```

After this, the consumer can mount the share and query the view —
*and they cannot see the underlying ORDERS table*.

### The consumer-side recipe

```sql
-- Consumer
USE ROLE SYSADMIN;

CREATE DATABASE acme_finance
FROM SHARE  PRODUCER_LOCATOR.finance_view_share;

SELECT * FROM acme_finance.public.eu_only;
```

The consumer sees only the three columns the view exposes
(`id, customer, amount`) and only the rows that match the view's
predicate (`region = 'EU'`). They will get errors if they try to
access the underlying `ORDERS` table:

```sql
SELECT * FROM acme_finance.public.orders;  -- ERROR: does not exist or not authorized
```

### Why this is safer than a normal view

Imagine the producer had used a *normal* view instead. Snowflake's
optimizer might inline the view's body, exposing:

- the existence of the `ORDERS` table
- the column names `customer`, `amount`, `region`
- the predicate `region = 'EU'`

With that knowledge, a clever consumer could craft a query that
bypasses the view — for example, by sharing ORDERS metadata through
information schema queries. Secure views prevent all of that by
keeping the definition opaque.

### When to combine secure views with row-access policies

For multi-tenant data, pair a secure view with a row-access policy
(see section 20). The secure view exposes a *stable* schema; the
row-access policy filters at query time based on the consumer's
role or user.

```sql
-- Future L162 syntax, preview here
ALTER VIEW eu_only ADD ROW ACCESS POLICY rap_acme_only;
```

## Hands-on

```sql
-- Producer side, full demo
USE ROLE ACCOUNTADMIN;
USE SCHEMA FIN_DEMO.PUBLIC;

CREATE OR REPLACE SECURE VIEW eu_only AS
  SELECT id, customer, amount FROM ORDERS WHERE region = 'EU';

CREATE SHARE IF NOT EXISTS finance_view_share;
GRANT USAGE ON DATABASE FIN_DEMO          TO SHARE finance_view_share;
GRANT USAGE ON SCHEMA   FIN_DEMO.PUBLIC   TO SHARE finance_view_share;
GRANT SELECT ON VIEW    FIN_DEMO.PUBLIC.EU_ONLY TO SHARE finance_view_share;

SHOW GRANTS TO SHARE finance_view_share;
```

## Key takeaways

- Share secure views with `GRANT SELECT ON VIEW`.
- The consumer sees only the view's exposed columns and rows.
- Combine with row-access policies for multi-tenant isolation.
- Always run `SHOW GRANTS TO SHARE` before publishing to verify.

## What's next

L132 closes section 18 with the **multi-database share** — sharing
data drawn from more than one database in a single share.