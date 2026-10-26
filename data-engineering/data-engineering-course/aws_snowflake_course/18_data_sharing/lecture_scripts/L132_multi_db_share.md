---
l_id: L132
title: Share data from multiple databases
duration: "4:30"
prereqs: ["L131"]
---

# L132 — Share data from multiple databases

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 18 — Data Sharing
> **Duration:** 4:30

## Prereqs

L131 — Sharing a secure view.

## Key terms

- **Multi-database share** — a single share object that includes
  objects from more than one database.
- **Cross-database join** — a query that joins tables across two
  shared databases; works on the consumer side because both
  databases come from the same producer.

## Lecture

Welcome back. Section 18 closes with the most common production
pattern: a single share that exposes data drawn from *several*
producer databases. The mechanics are exactly the same — you just
repeat the grants. The interesting part is what happens on the
consumer side, where everything appears as one logical database.

### Why you'd share from multiple databases

Real data estates split facts and dimensions into different
databases for operational reasons (separate lifecycles, separate
owners, separate retention policies). But the *consumer* wants to
query them together. Sharing solves this:

```text
producer_account
├── catalog_db          (product catalog)
│   └── public.products
├── orders_db           (transactional orders)
│   └── public.orders
└── customers_db        (customer master)
    └── public.customers
```

A single share can expose tables from all three. The consumer
mounts them under one local database (`PRODUCER`) and runs joins
across them.

### The producer recipe

```sql
USE ROLE ACCOUNTADMIN;

CREATE SHARE catalog_orders_share;

-- catalog_db.products
GRANT USAGE ON DATABASE catalog_db TO SHARE catalog_orders_share;
GRANT USAGE ON SCHEMA   catalog_db.public TO SHARE catalog_orders_share;
GRANT SELECT ON TABLE   catalog_db.public.products TO SHARE catalog_orders_share;

-- orders_db.orders
GRANT USAGE ON DATABASE orders_db   TO SHARE catalog_orders_share;
GRANT USAGE ON SCHEMA   orders_db.public TO SHARE catalog_orders_share;
GRANT SELECT ON TABLE   orders_db.public.orders TO SHARE catalog_orders_share;

-- customers_db.customers
GRANT USAGE ON DATABASE customers_db TO SHARE catalog_orders_share;
GRANT USAGE ON SCHEMA   customers_db.public TO SHARE catalog_orders_share;
GRANT SELECT ON TABLE   customers_db.public.customers TO SHARE catalog_orders_share;

ALTER SHARE catalog_orders_share ADD ACCOUNTS = abc12345.us-east-1;
```

After this, the consumer mounts the share and sees:

```text
consumer_account
└── acm_partitions                                 (mounted)
        ├── public.products        (from catalog_db)
        ├── public.orders          (from orders_db)
        └── public.customers       (from customers_db)
```

All three tables appear in the *same* `public` schema on the
consumer side, even though they came from three different databases.

### Cross-database joins on the consumer side

```sql
-- On the consumer account
SELECT o.order_id,
       c.customer_name,
       p.product_name,
       o.amount
FROM   acm_partitions.public.orders    o
JOIN   acm_partitions.public.customers c ON c.id = o.customer_id
JOIN   acm_partitions.public.products  p ON p.id = o.product_id;
```

This works because everything in `acm_partitions` came from one
producer account. There's no concept of "the orders are from one
account, the customers from another" — the share merges them at
mount time.

### Real-world limits

- All grants must succeed for the share to be valid. If even one
  table is missing its `USAGE ON SCHEMA`, the share is broken
  silently.
- A single share can grant access to **objects in any database in
  the same account** — but **not** to objects in other producer
  accounts. Cross-account combines require *outbound* + *inbound*
  shares chained manually.
- Snowflake has a hard limit on the number of grants per share
  (~thousand-scale). For very large shares, consider splitting
  by consumer.

## Hands-on

```sql
USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS DB_A;
CREATE DATABASE IF NOT EXISTS DB_B;
USE SCHEMA DB_A.PUBLIC;
CREATE TABLE T1 (n NUMBER); INSERT INTO T1 VALUES (1), (2);
USE SCHEMA DB_B.PUBLIC;
CREATE TABLE T2 (n VARCHAR); INSERT INTO T2 VALUES ('a'), ('b');

CREATE SHARE multi_db_share;
GRANT USAGE ON DATABASE DB_A TO SHARE multi_db_share;
GRANT USAGE ON SCHEMA   DB_A.PUBLIC TO SHARE multi_db_share;
GRANT SELECT ON TABLE   DB_A.PUBLIC.T1 TO SHARE multi_db_share;
GRANT USAGE ON DATABASE DB_B TO SHARE multi_db_share;
GRANT USAGE ON SCHEMA   DB_B.PUBLIC TO SHARE multi_db_share;
GRANT SELECT ON TABLE   DB_B.PUBLIC.T2 TO SHARE multi_db_share;

SHOW GRANTS TO SHARE multi_db_share;
```

## Key takeaways

- A share can include objects from multiple databases in the same
  account.
- The consumer sees them all under one mounted database — joins
  work seamlessly.
- The grant chain must succeed for every table; one missing
  `USAGE ON SCHEMA` breaks the share silently.
- Cross-account combines are still manual; one share cannot span
  producer accounts.

## What's next

Section 19 is **Data Sampling** — three short lectures on pulling
statistically valid subsets out of huge tables for testing, dev,
and ML training.