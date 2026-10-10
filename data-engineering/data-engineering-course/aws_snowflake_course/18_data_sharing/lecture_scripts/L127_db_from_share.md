---
l_id: L127
title: Creating a database from share
duration: "4:30"
prereqs: ["L126"]
---

# L127 — Creating a database from share

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 18 — Data Sharing
> **Duration:** 4:30

## Prereqs

L126 — Creating a reader account. You should now know how to set
up *both* ends of a share.

## Key terms

- **`CREATE DATABASE ... FROM SHARE`** — the consumer-side DDL that
  mounts a shared database locally.
- **Mounted database** — read-only database backed by the
  producer's micro-partitions.
- **Refresh** — the consumer does not need to refresh; changes are
  visible as soon as the producer commits them.

## Lecture

Welcome back. We just built the producer side end to end. Today we
flip to the **consumer side** — the simple half. Everything the
consumer needs to do to consume a share is *one* SQL statement.

### The one-liner

```sql
-- On the consumer account
CREATE DATABASE partner_sales
FROM SHARE  PRODUCER_ACCOUNT_LOCATOR.sales_share;
```

Three things happen:

1. Snowflake creates a new database called `partner_sales` in the
   consumer account.
2. The database has a single schema (and any others the producer
   exposed) containing the granted tables.
3. The bytes are still in the producer's storage; the consumer's
   compute now reaches across the cloud to read them.

```sql
-- What you can do immediately after
SELECT * FROM partner_sales.public.orders LIMIT 100;

-- What you cannot do
INSERT INTO partner_sales.public.orders VALUES (...);  -- ERROR
```

The database is *read-only*. You can query, but you can't write to
shared tables.

### Naming the database

The database name on the consumer side is up to the consumer. Two
different consumers can each call their mount `partner_sales` even
though they're pointing at the same producer share. Snowflake
identifies the share by the producer's locator + share name, not by
the consumer's database name.

### Seeing live updates

There's no refresh, no schedule, no cache layer the consumer has to
manage. The moment a producer's table changes, the consumer's next
query sees the new rows. This is the property that makes sharing
strictly better than ETL for most B2B scenarios.

### Permissions

A consumer needs `CREATE DATABASE` on their own account, which
defaults to `SYSADMIN` and any role with the
`CREATE DATABASE` privilege on the account.

### Dropping the mounted database

```sql
DROP DATABASE partner_sales;
```

Dropping the mounted database does **not** revoke the share — the
producer's share still exists. The consumer just loses the local
mount.

## Hands-on

If you have a partner account (or a sandbox you control):

```sql
-- On the consumer account
USE ROLE SYSADMIN;
CREATE DATABASE acme_orders
FROM SHARE  <your_producer_locator>.sales_share;

SELECT * FROM acme_orders.public.orders LIMIT 10;
```

If you don't have a partner account yet, you can use Snowflake's
**Marketplace** to consume a real share — see L181.

## Key takeaways

- `CREATE DATABASE x FROM SHARE locator.share_name` is the entire
  consumer-side flow.
- The mounted database is read-only; you cannot `INSERT` into
  shared tables.
- Updates are live; no refresh is needed.
- The consumer picks the database name; it's a local alias.

## What's next

L128 covers the access-control setup on the consumer side — making
sure the right humans in the consumer account can query the
mounted database.