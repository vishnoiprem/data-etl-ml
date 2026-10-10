---
l_id: L56
title: "Scaling out"
duration: "7:00"
prereqs:
  - L55 (Scaling up)
---

# L56 — Scaling out

> **Section:** 7 — Performance optimization
> **Duration:** 7:00

## Prereqs

- L55 — Scaling up

## Key terms

- **Multi-cluster warehouse** — a warehouse with
  `MIN_CLUSTER_COUNT > 1` or `MAX_CLUSTER_COUNT > 1`. Snowflake
  spins up extra clusters automatically under load.
- **Scale out** — adding clusters to absorb **concurrent
  queries** so they don't queue.
- **Scaling policy** — `STANDARD` (default), `ECONOMY`
  (cheaper, slower to add), or `AGGRESSIVE` (lowest latency,
  highest cost).
- **Cluster** — a single compute unit within a multi-cluster
  warehouse. Same T-shirt size as a single-cluster warehouse.

## Lecture

Scale up (L55) makes **one** query faster. Scale out makes
**many** queries fast at the same time. The mental model: scale
up is **more CPUs per query**; scale out is **more parallel
queries**.

### When scale out helps

- A **multi-tenant BI warehouse** where 50 analysts are
  running dashboards simultaneously.
- An **ELT tool** (dbt, Matillion) that fans out many small
  models in parallel.
- A **data app** where user requests translate into Snowflake
  queries.

When **not** to scale out: a single huge query. Scale up is
the right tool for that.

### Enable scale out

```sql
CREATE OR REPLACE WAREHOUSE bi_wh
    WITH
        WAREHOUSE_SIZE       = 'SMALL'
        MIN_CLUSTER_COUNT    = 1
        MAX_CLUSTER_COUNT    = 5
        SCALING_POLICY       = 'STANDARD'
        AUTO_SUSPEND         = 60
        AUTO_RESUME          = TRUE;
```

Two important points:

- `MIN_CLUSTER_COUNT = 1` means the warehouse always has at
  least one cluster running (so the first query is fast).
- `MAX_CLUSTER_COUNT = 5` means Snowflake can spin up to 5
  clusters under load. You pay for the **active** clusters
  only.

If you want a **minimum** of 2 clusters (e.g. to avoid cold
start during business hours), set `MIN_CLUSTER_COUNT = 2`.

### The scaling policies

```sql
ALTER WAREHOUSE bi_wh SET SCALING_POLICY = 'ECONOMY';
```

- **`STANDARD`** — adds a cluster when the queue has waited
  more than ~20 s. Balanced default.
- **`ECONOMY`** — waits longer before adding a cluster. Saves
  money, but adds latency under bursty load.
- **`AGGRESSIVE`** — adds a cluster as soon as the queue grows
  by 1 query. Lowest latency, highest cost.

For dashboards, `STANDARD` is almost always right. For
critical user-facing apps, `AGGRESSIVE`. For batch ELT where
the cost dominates, `ECONOMY`.

### Cost of scale out

| Cluster count | Wall-clock per query | Concurrent queries | Cost per second |
|---|---|---|---|
| 1 | 60 s | 1 | 2× |
| 2 | 30 s | 2 | 4× |
| 5 | 12 s | 5 | 10× |

Total cost scales with cluster count, but **throughput scales
linearly**. The cost is justified when the **alternative** is
users waiting — the dollar value of an analyst's time dwarfs
the credit cost.

### Inspect cluster activity

```sql
SELECT
    warehouse_name,
    cluster_number,
    start_time,
    end_time,
    credits_used
FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(
    DATE_RANGE_START => DATEADD('day', -1, CURRENT_TIMESTAMP()),
    WAREHOUSE_NAME   => 'BI_WH'
))
ORDER BY start_time DESC
LIMIT 50;
```

You'll see rows like `BI_WH | 1 | 09:00:00 | 09:30:00 | 0.05`
and `BI_WH | 2 | 09:15:00 | 09:18:00 | 0.02`. Cluster 2 was
spun up for a 3-minute spike at 9:15.

### Scale out vs scale up — decision tree

```text
Q: Is the workload one huge query or many concurrent queries?

    Many concurrent  →  scale OUT
    One huge         →  scale UP

Q: Is the queue growing but individual queries are still fast?

    Yes  →  scale OUT (with STANDARD policy)
    No   →  scale UP (one query needs more CPUs)
```

A 5-person BI team typically wants `SMALL` size, `MAX_CLUSTER_COUNT = 3`
— small per-query cost, but enough clusters to absorb
morning-spike concurrency.

### When scale out is the wrong tool

- **One very slow query.** A 6-hour scan on a `Small` will not
  become a 3-hour scan on a `Small` with 5 clusters — the
  query itself doesn't parallelise across clusters. Use scale
  up.
- **Cost-sensitive batch.** If you run a 1-hour ELT at 3 AM
  and no one is waiting, the cost of a 2-cluster setup is
  wasted. Use a single cluster.
- **Caching-dominated workloads.** With aggressive caching,
  most queries finish from cache in milliseconds; the queue
  rarely grows. Scale out adds cost for no benefit.

## Hands-on

Run the multi-cluster `bi_wh` `CREATE WAREHOUSE` from above.
Open the Query History in two browser tabs and run the same
`SELECT COUNT(*) FROM raw_orders_parquet` 5 times in each tab
back-to-back. Watch `BI_WH` spin up a second cluster in the
UI.

## Quiz prep

- What is the difference between scale up and scale out?
- What does `MAX_CLUSTER_COUNT` control?
- When is `AGGRESSIVE` scaling policy the right choice?

## Key takeaways

- Scale out is **more clusters**, not bigger clusters.
- It's the right tool for **concurrent** queries that would
  otherwise queue.
- Set `MIN_CLUSTER_COUNT = 1` and a sensible
  `MAX_CLUSTER_COUNT` per workload.
- `STANDARD` scaling policy is the right default for most BI
  workloads.

## What's next

In **L57 — Caching (Theory)** we look at the three caches that
make the **second** time you run a query almost free.