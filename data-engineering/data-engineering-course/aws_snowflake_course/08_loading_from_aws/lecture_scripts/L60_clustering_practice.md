---
l_id: L60
title: "Clustering - Practice"
duration: "8:00"
prereqs:
  - L59 (Clustering - Theory)
---

# L60 — Clustering — Practice

> **Section:** 8 — Loading from AWS
> **Duration:** 8:00

## Prereqs

- L59 — Clustering — Theory

## Key terms

- **`ALTER TABLE … CLUSTER BY`** — sets the clustering key
  and enables automatic clustering.
- **`ALTER TABLE … SUSPEND / RESUME RECLUSTER`** — temporarily
  disables reclustering during a bulk load.
- **Clustering ratio** — `SYSTEM$CLUSTERING_INFORMATION` gives
  the per-column partition overlap and depth.
- **Reclustering cost** — billed per credit-second; visible in
  the warehouse metering history as `AUTO_CLUSTERING`.

## Lecture

Theory from L59, now practice. We set a clustering key on
`raw_orders_parquet`, watch the depth drop, and measure the
**query-time** impact on a selective `WHERE order_ts = …`
query.

### Step 1 — measure the starting depth

```sql
SELECT SYSTEM$CLUSTERING_DEPTH('raw_orders_parquet') AS depth_before;
```

For a freshly loaded Parquet file, expect a depth of
`1.0 – 1.3` (the data is already in time order from the
`PUT`).

### Step 2 — set a clustering key

```sql
ALTER TABLE raw_orders_parquet CLUSTER BY (order_ts);
```

The `CLUSTER BY` clause is **declarative** — it doesn't
re-cluster the table immediately. It tells the automatic
clustering service "this is the sort order I want". The
service re-clusters in the background as needed.

### Step 3 — wait, then re-measure

```sql
-- Wait 2-3 minutes for the background re-clustering to make progress
SELECT SYSTEM$CLUSTERING_DEPTH('raw_orders_parquet') AS depth_after;
```

For our 1 GB table, the depth should drop toward `1.0`. For
a 10 TB table, the depth change is more dramatic.

### Step 4 — check the query profile

Run a selective query:

```sql
SELECT * FROM raw_orders_parquet
WHERE order_ts = '2026-09-15'::TIMESTAMP_LTZ;
```

Open the Query History and look at the `Partitions scanned`
vs `Partitions total`. For a perfectly clustered table, only
the partitions containing 2026-09-15 are scanned.

Compare with a non-clustered table:

```sql
-- Without clustering
ALTER TABLE raw_orders_parquet DROP CLUSTERING KEY;
SELECT * FROM raw_orders_parquet
WHERE order_ts = '2026-09-15'::TIMESTAMP_LTZ;
-- (note partitions scanned)
```

You'll see the non-clustered version scan **all** partitions;
the clustered version scans only a few.

### Step 5 — inspect the metadata

```sql
SELECT
    SYSTEM$CLUSTERING_INFORMATION('raw_orders_parquet') AS info;
```

Returns a JSON document with `cluster_by_columns`, `total_partition_count`,
`total_constant_partition_count`, `average_overlaps`,
`average_depth`, and a `partition_depth_histogram`. The
`average_depth` is the same number `CLUSTERING_DEPTH` returns.

### Multi-column clustering keys

You can cluster on **multiple columns**, in priority order:

```sql
ALTER TABLE raw_orders_parquet CLUSTER BY (order_ts, customer_id);
```

The first column is the dominant sort; the second column
breaks ties. Use multi-column keys when your queries filter
on a combination — e.g. "orders in September for customer
12345" benefits from `(order_ts, customer_id)`.

### Suspend during bulk loads

For a high-throughput bulk load, auto-clustering will fight
you (re-sorting as you insert). Suspend it:

```sql
ALTER TABLE raw_orders_parquet SUSPEND RECLUSTER;

COPY INTO raw_orders_parquet …;

ALTER TABLE raw_orders_parquet RESUME RECLUSTER;
```

The `SUSPEND RECLUSTER` is **session-scoped** in the sense
that it persists across statements; the `RESUME RECLUSTER`
turns automatic clustering back on.

### When not to bother

For the **vast majority** of tables, you should not set a
clustering key. The sign that clustering will help:

- Table > 1 TB.
- Queries are selective (filter on a specific value or
  range, not a full scan).
- The filter column is **not** the load timestamp (otherwise
  the data is already clustered).

If any of those doesn't apply, leave the table unclustered
and let the natural load order do its job.

### The "drop clustering key" pattern

Sometimes you cluster a table and the depth doesn't drop
(fewer micro-partitions than the clusterer wants to merge).
Drop the key:

```sql
ALTER TABLE raw_orders_parquet DROP CLUSTERING KEY;
```

`DROP CLUSTERING KEY` removes the cluster directive and
stops the auto-clusterer. The table layout is unchanged.

### Cost-aware pattern for 10 TB+ tables

```sql
-- During business hours: keep clustering off to save cost
ALTER TABLE huge_table SUSPEND RECLUSTER;

-- During off-peak: re-cluster in the background
ALTER TABLE huge_table RESUME RECLUSTER;
```

Pair this with a Task that toggles the setting at known
windows (covered in the Tasks section). For our 1 GB table
the cost is negligible and you can leave `RESUME RECLUSTER`
on permanently.

## Hands-on

Run steps 1–5. Compare the Query Profile of the
`WHERE order_ts = …` query with and without the clustering
key.

## Quiz prep

- Does `ALTER TABLE … CLUSTER BY` re-cluster immediately?
- How do you disable automatic clustering during a bulk load?
- What is the right clustering key for a multi-tenant
  orders table?

## Key takeaways

- `ALTER TABLE … CLUSTER BY` is **declarative**; the actual
  re-clustering runs in the background.
- `SYSTEM$CLUSTERING_INFORMATION` returns detailed JSON
  metadata about the current state.
- Use `SUSPEND / RESUME RECLUSTER` during bulk loads.
- Most tables **don't** need a clustering key — only large
  ones with selective queries benefit.

## What's next

In **L61 — Sign up for free trial (S3)** we set up an AWS
account so we can start using S3 instead of internal stages.