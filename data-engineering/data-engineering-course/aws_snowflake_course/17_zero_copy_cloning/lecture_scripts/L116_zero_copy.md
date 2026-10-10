---
l_id: L116
title: Understanding Zero-Copy Cloning
duration: "5:00"
prereqs: ["L115"]
---

# L116 — Understanding Zero-Copy Cloning

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 17 — Zero-Copy Cloning
> **Duration:** 5:00

## Prereqs

L115 — Transient + Temporary tables & schemas. You should understand
that Snowflake storage is columnar and micro-partitioned.

## Key terms

- **Micro-partition** — Snowflake's on-disk storage unit. Each
  table is a set of immutable, compressed micro-partitions plus a
  metadata layer that says which partitions hold which data.
- **Zero-copy clone** — a new table whose metadata initially points
  to the *same* micro-partitions as the source. No bytes are copied.
- **Divergence** — the moment the source and clone each add or
  modify a different row. From that point on, they need distinct
  micro-partitions and the clone starts to cost storage.

## Lecture

Welcome to section 17. This is the lecture where most people fall in
love with Snowflake. **Zero-Copy Cloning** lets you create a perfect
copy of a table, schema, or entire database in *under a second*, with
*zero extra storage* at the moment of creation. You can clone a
multi-petabyte table on a free trial account. The trick is metadata,
not magic.

### Why it's possible

Snowflake stores every table as a set of immutable micro-partitions.
Each micro-partition has a stable ID, and every table keeps a metadata
record listing the IDs it considers "live". When you run
`CREATE TABLE ... CLONE`, Snowflake simply copies the metadata record
— a tiny object — and gives the new table its own name.

```text
        source table                       clone table
        ────────────                      ───────────
metadata: [mp-101, mp-102, mp-103]   metadata: [mp-101, mp-102, mp-103]
                  │                            │
                  └──── shared micro-partitions ─┘
                          (zero bytes copied)
```

The two tables now look identical to every query, but the underlying
partitions are shared. Storage cost at this instant is the same as a
single table.

### When storage starts to accrue

The deal is "until they diverge". If you `INSERT` into the source and
the clone, Snowflake writes a new micro-partition for each write —
those new partitions are owned by exactly one of the two tables, so
the storage used to compute it has effectively doubled for that row.
The longer both tables live and evolve, the closer you get to
double-storage. If the clone is purely read-only (a backup, a report
mirror), divergence is zero and so is the storage.

### Common use cases

- **Dev / test from production**: `CREATE TABLE DEV.PUBLIC.ORDERS
  CLONE PROD.PUBLIC.ORDERS;` — instant, isolated, free.
- **ELT backup**: before a heavy transformation job, clone the
  source table. If the job blows up, swap back.
- **Reproducible analytics**: snapshot a table at a point in time
  for a finance close.

### The mental model

Treat every clone as "a metadata pointer that becomes its own copy the
moment you change it". Cheap to make, free to read, expensive to mutate
both sides of.

## Hands-on

```sql
USE SCHEMA DEMO_DB.PUBLIC;

-- A 10 million row table
CREATE OR REPLACE TABLE ORDERS AS
  SELECT SEQ4()                              AS id,
         UNIFORM(1, 10000, RANDOM())         AS amount,
         CURRENT_TIMESTAMP()                 AS created
  FROM TABLE(GENERATOR(ROWCOUNT => 10000000));

-- Time the clone
SET t0 = (SELECT CURRENT_TIMESTAMP());
CREATE OR REPLACE TABLE ORDERS_BACKUP CLONE ORDERS;
SET t1 = (SELECT CURRENT_TIMESTAMP());

SELECT $t1 - $t0 AS clone_seconds;
-- Typically < 1s even for the 10M row table.
```

## Key takeaways

- Zero-copy clone is a metadata-only operation; no bytes are
  copied at clone time.
- Source and clone share micro-partitions until they diverge.
- Cloning is instantaneous and works on tables, schemas, and
  databases.
- Storage cost grows only as the source and clone diverge.

## What's next

In L117 we'll write the actual `CREATE TABLE ... CLONE` syntax for
single tables and see the first divergence with our own eyes.