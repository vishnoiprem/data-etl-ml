---
l_id: L130
title: Secure vs. normal view
duration: "4:30"
prereqs: ["L129"]
---

# L130 — Secure vs. normal view

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 18 — Data Sharing
> **Duration:** 4:30

## Prereqs

L129 — Sharing database & schema.

## Key terms

- **Normal view** — a saved `SELECT` query. Snowflake may
  optimize it by inlining the definition at query time, exposing
  the underlying columns and filters to the consumer.
- **Secure view** — a view whose definition is hidden from the
  consumer. Snowflake does not inline the definition; the consumer
  can only see the columns the view explicitly exposes.
- **Sharing rule** — only **secure views** can be shared.

## Lecture

Welcome back. Today we cover the single most common producer-side
gotcha in data sharing: **the view you're sharing must be a secure
view**. Snowflake silently refuses to put a normal view into a
share. By the end of this lecture you'll know why, and how to
create a secure view.

### Why the distinction exists

Consider this normal view:

```sql
CREATE VIEW customer_summary AS
  SELECT region, SUM(amount) AS total
  FROM   orders
  GROUP BY region;
```

A consumer who runs `SELECT * FROM customer_summary` should see
`(region, total)`. But if Snowflake optimizes by inlining the view,
the consumer's query planner could see the underlying `orders`
table — including columns the producer never intended to share
(customer name, address, payment method).

A **secure view** prevents that. Snowflake treats the definition as
opaque: the consumer cannot see the underlying tables, cannot see
columns the view doesn't expose, and cannot infer predicates that
would let them reconstruct hidden data.

### The syntax

```sql
CREATE SECURE VIEW customer_summary AS
  SELECT region, SUM(amount) AS total
  FROM   orders
  GROUP BY region;
```

The keyword `SECURE` is the only change. Everything else is the same
`SELECT` you already know.

### Sharing a secure view

```sql
GRANT SELECT ON VIEW customer_summary TO SHARE finance_share;
```

Note: you grant on `VIEW`, not `TABLE`. The rest of the share
recipe is identical to L129.

### Limitations of secure views

- **No `SELECT *` is allowed** in the view body if the producer
  wants to control which columns are exposed. Be explicit.
- **Some optimizations are off.** Snowflake won't rewrite a secure
  view against the underlying tables, so query performance can be
  worse than a normal view in some cases.
- **Cannot use `WITH ROW ACCESS POLICY` to filter rows based on the
  consumer.** Row filtering belongs in the view's `WHERE` clause.

### When you must use a secure view

- any view you want to share
- any view that exposes a *predicate* you don't want the consumer
  to learn (e.g. "WHERE region = 'EU'")
- any view that joins multiple tables where some of the joined
  columns should not be exposed

### When a normal view is fine

- internal views that no one outside your org queries
- performance-sensitive views where you need Snowflake's view
  optimization
- views you want the optimizer to rewrite against underlying tables

## Hands-on

```sql
USE SCHEMA FIN_DEMO.PUBLIC;

-- 1. Create the underlying table
CREATE OR REPLACE TABLE ORDERS (
  id        NUMBER,
  customer  VARCHAR,
  region    VARCHAR,
  amount    NUMBER
);

INSERT INTO ORDERS VALUES
  (1, 'alice', 'EU', 100),
  (2, 'bob',   'NA', 250),
  (3, 'eve',   'EU', 175);

-- 2. A normal view (NOT shareable)
CREATE OR REPLACE VIEW region_total AS
  SELECT region, SUM(amount) AS total
  FROM   ORDERS
  GROUP BY region;

-- 3. A secure view (shareable)
CREATE OR REPLACE SECURE VIEW region_total_secure AS
  SELECT region, SUM(amount) AS total
  FROM   ORDERS
  GROUP BY region;

-- Both look the same to the user:
SELECT * FROM region_total;
SELECT * FROM region_total_secure;
-- Yet only the secure one is eligible for sharing.
```

## Key takeaways

- Only **secure views** can be shared.
- A secure view's definition is opaque to the consumer — they cannot
  see underlying tables or filters.
- The syntax is `CREATE SECURE VIEW ...`; everything else is the
  same.
- Performance can be slightly worse than a normal view; the
  trade-off is intentional.

## What's next

L131 puts secure views to work in a full sharing scenario —
end-to-end, producer-side to consumer-side.