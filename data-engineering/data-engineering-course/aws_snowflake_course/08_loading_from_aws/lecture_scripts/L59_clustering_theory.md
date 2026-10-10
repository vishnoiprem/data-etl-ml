---
l_id: L59
title: "Clustering - Theory"
duration: "7:00"
prereqs:
  - L58 (Maximize Caching)
---

# L59 — Clustering — Theory

> **Section:** 8 — Loading from AWS
> **Duration:** 7:00

## Prereqs

- L58 — Maximize Caching

## Key terms

- **Micro-partition** — Snowflake's storage unit. Each
  micro-partition is a columnar file holding 50–500 MB of
  uncompressed data.
- **Clustering key** — one or more columns Snowflake uses to
  sort micro-partitions physically. Improves pruning for
  queries that filter on those columns.
- **Clustering depth** — Snowflake's metric of how well a
  table is clustered. Lower is better.
- **Automatic clustering** — Snowflake's background service
  that re-clusters a table on your behalf. Billed per second.
- **Natural clustering** — the order in which data is loaded.
  Append-heavy tables are often naturally clustered on the
  load timestamp.

## Lecture

Clustering is the most over-asked-about feature in Snowflake.
Most tables **don't need it**. A small number of very large
tables benefit enormously. This lecture is the theory so you
can tell the two apart.

### What "clustering" means in Snowflake

Snowflake stores tables as **micro-partitions** — columnar
files of 50–500 MB. Each micro-partition has metadata about
the **min and max value of every column** in the partition.
That metadata is what the query history cache (L57) uses to
**prune** micro-partitions that can't contain the rows your
query is looking for.

Clustering is the act of **sorting micro-partitions** so that
related rows live in the same partition. A well-clustered
table looks like this:

```text
Partition 1: order_ts 2026-09-01 .. 2026-09-05
Partition 2: order_ts 2026-09-06 .. 2026-09-12
Partition 3: order_ts 2026-09-13 .. 2026-09-20
```

A query `WHERE order_ts = '2026-09-08'` only needs to scan
partition 2. Without clustering, the same query might scan
**all** partitions.

### Clustering depth

`SYSTEM$CLUSTERING_DEPTH('table_name')` returns a single
number representing how "out of order" the partitions are.
The metric is on a log scale:

| Depth | What it means |
|---|---|
| 1.0 | Perfectly clustered |
| 1.1 – 2.0 | Mostly clustered; small benefit from re-clustering |
| 2.0 – 4.0 | Noticeable improvement possible |
| > 4.0 | Definitely worth re-clustering |

You almost never see `1.0` in production; an append-only
table loaded in time order will hover around `1.0 – 1.5`.

### When to use clustering

The decision rule of thumb:

- **Table is < 1 TB** and queries touch most of the table →
  **don't cluster**. Pruning matters less when the table is
  small.
- **Table is > 1 TB and queries are selective** (filter on
  specific dates, customers, regions) → **cluster** on the
  filter column.
- **Table is append-only and loaded in time order** →
  **already clustered on the load timestamp**. No action
  needed.
- **Table is heavily updated / deleted** → re-clustering
  cost may exceed the pruning benefit.

For our `raw_orders_parquet` (1 GB, append-only, loaded in
date order), clustering on `order_ts` is essentially free —
the data is already sorted.

### Automatic clustering

```sql
ALTER TABLE raw_orders_parquet CLUSTER BY (order_ts);
```

This **doesn't** re-cluster immediately. It tells Snowflake
to run the **automatic clustering service** in the background,
which re-sorts micro-partitions when the average depth exceeds
a threshold. You pay per second for the background
re-clustering, billed under a separate credit pool.

For tiny tables, the cost is ~free. For 50 TB tables, the
cost can be hundreds of credits a month.

### Cluster keys vs sort keys vs indexes

Snowflake has **no** indexes and **no** explicit sort keys.
The clustering key is a **physical ordering hint** that
Snowflake uses to lay out micro-partitions. It is not a
primary key, not a unique constraint, and not enforced.

You can have a clustering key on a column with duplicates
(`order_ts` has many duplicates). It just means many rows
per micro-partition share the same value — fine.

### The cost of clustering

Three things to budget for:

1. **Background re-clustering** — automatic clustering bills
   per second. Disable it during a one-off bulk load and
   re-enable afterwards.
2. **Increased storage** — clustered tables are slightly
   larger because of the sort overhead.
3. **Slower loads** — Snowflake might re-cluster as it
   ingests, slowing the `COPY INTO`. For high-throughput
   pipelines, disable auto-clustering during the load and
   re-enable once the load completes.

### A quick experiment

```sql
-- Look at the current clustering depth
SELECT SYSTEM$CLUSTERING_DEPTH('raw_orders_parquet') AS depth_before;

ALTER TABLE raw_orders_parquet CLUSTER BY (order_ts);

-- Wait a few minutes; then check
SELECT SYSTEM$CLUSTERING_DEPTH('raw_orders_parquet') AS depth_after;
```

You'll see the depth drop. The Query Profile for a
`WHERE order_ts = ...` query should also show a much smaller
`Partitions scanned / Partitions total` ratio.

## Hands-on

Run the `SYSTEM$CLUSTERING_DEPTH` query on your
`raw_orders_parquet`. Note the depth. We'll set a clustering
key in L60 and re-measure.

## Quiz prep

- What is a micro-partition?
- What does `SYSTEM$CLUSTERING_DEPTH` measure?
- When should you **not** cluster a table?

## Key takeaways

- A **micro-partition** is a 50–500 MB columnar file.
- **Clustering key** = column(s) Snowflake uses to sort
  micro-partitions.
- Most tables don't need clustering; **only large tables with
  selective queries** benefit.
- Automatic clustering is a paid background service — disable
  it during bulk loads if cost matters.

## What's next

In **L60 — Clustering — Practice** we set a clustering key on
`raw_orders_parquet` and watch the depth metric improve.