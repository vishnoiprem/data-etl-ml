---
l_id: L122
title: Understanding data sharing
duration: "4:30"
prereqs: ["L121"]
---

# L122 — Understanding data sharing

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 18 — Data Sharing
> **Duration:** 4:30

## Prereqs

L121 — Zero-Copy Cloning recap. Sharing depends on the same
micro-partition model that makes clones free.

## Key terms

- **Producer** — the Snowflake account that *owns* the data being
  shared.
- **Consumer** — the Snowflake account that *reads* the data.
- **Share** — the named object that lists which databases,
  schemas, and tables the producer is willing to expose.
- **No copy** — sharing is metadata only. The bytes never leave
  the producer's storage layer; the consumer's compute just reads
  them remotely.

## Lecture

Welcome to section 18. The last three sections gave you safety nets
(Time Travel, Fail Safe, table types) and a free clone operation
(zero-copy). Today we use that same machinery for a different job:
**giving other Snowflake accounts read-only access to your data
without copying a single row**.

### What a share actually is

A *share* is a named Snowflake object that bundles together a list
of:

- databases (or schemas within a database)
- tables, secure views, materialized views, dynamic tables
- functions (in some editions)

You then grant that share to one or more Snowflake accounts. Those
accounts see the listed objects as a database in their own account —
but the underlying storage is still in your account, billed to you.

```text
    producer account (your org)         consumer account (partner)
    ───────────────────────────         ─────────────────────────
    ┌─────────────┐                    ┌─────────────────────────┐
    │  share:     │                    │  db: partner_sales      │
    │  ┌────────┐ │      share         │   └─ schema: public     │
    │  │db.s.t  │ │ ─────────────────▶ │      └─ table: orders   │
    │  └────────┘ │                    │                         │
    └─────────────┘                    └─────────────────────────┘
    storage: yours                     compute: theirs (billed to them)
```

### Why this is so much better than ETL

Without sharing, you would:

1. Copy data from your account to S3 (storage + egress).
2. Load the S3 files into their account (compute).
3. Schedule the whole thing (more compute).

With sharing, the bytes never move. Their query engine reaches into
your storage layer, reads what it's allowed to read, and returns
results. **Their compute, your storage, zero duplication**.

### Real-world use cases

- **B2B data distribution.** You're a vendor; your customers want
  daily sales data. Share, don't ETL.
- **Centralized finance, distributed subsidiaries.** The HQ account
  holds the master data; subsidiaries consume a slice.
- **Vendor-managed sandboxes.** A Snowflake Marketplace provider
  shares a dataset; you consume it as a database.

### Limits

- Sharing is **read-only** by design. Consumers can never `INSERT`
  into your tables.
- You cannot share dynamic tables or external tables (only their
  underlying storage if configured).
- You can only share with accounts that are on a compatible
  edition (most editions qualify).

## Hands-on

```sql
-- Producer side: preview a share (no objects attached yet)
CREATE SHARE my_first_share;

DESCRIBE SHARE my_first_share;
-- No databases yet — we add them in L123.
```

## Key takeaways

- A share is a named, read-only bundle of database objects.
- Sharing is metadata-only; storage stays with the producer,
  compute is paid by the consumer.
- Sharing replaces most B2B ETL pipelines.
- Sharing is read-only — by design.

## What's next

L123 covers the SQL surface of shares — `CREATE`, `GRANT
REFERENCE`, `ALTER`.