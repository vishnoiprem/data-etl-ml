---
l_id: L183
title: Warehouse Usage
duration: "5:00"
prereqs: ["L182"]
---

# L183 — Warehouse Usage

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 20 — Extra topics
> **Sub-group:** 7. Best Practices & Bonus
> **Duration:** 5:00

## Prereqs

L182 — Best practices.

## Key terms

- **Right-sizing** — picking the smallest warehouse that
  finishes the workload in an acceptable time.
- **Scaling policy** — Economy (cheaper, slower to start)
  vs Standard (more expensive, instant).
- **Multi-cluster** — running multiple clusters of the
  same size in parallel for high-concurrency workloads.
- **Concurrency** — how many queries are running at the
  same time.

## Lecture

Welcome back. Today's lecture is the warehouse sizing and
scaling playbook. By the end, you should be able to pick
the right warehouse for any workload and tune it for cost
and performance.

### Right-sizing: the rules

1. **Start small.** A `X-Small` warehouse. If the
   workload is slow, scale up. Most analytics workloads
   run fine on `Small` or `Medium`.
2. **Profile with `QUERY_HISTORY`.** Look at the
   `total_elapsed_time` column. The slowest 5% of queries
   are usually the ones to size for.
3. **Bigger is not always faster.** A 2XL warehouse
   running a 5-row query is *slower* than a Small —
   because the cluster startup time dominates. Use a
   bigger warehouse only for genuinely large queries.
4. **Mixed workloads need separate warehouses.** Don't
   run heavy ETL on the same warehouse as an interactive
   BI tool; the BI users will feel the ETL.

### The scaling policy

```sql
ALTER WAREHOUSE compute_wh SET
  MIN_CLUSTER_COUNT = 1
  MAX_CLUSTER_COUNT = 3
  SCALING_POLICY   = 'STANDARD';  -- or 'ECONOMY'
```

- **Standard**: the warehouse scales out *immediately*
  when a query queues. More expensive; better for
  latency-sensitive workloads.
- **Economy**: scales out only after the queue waits
  for ~6 seconds. Cheaper; better for batch.

For BI, use Standard. For batch ETL, use Economy.

### Auto-suspend

```sql
ALTER WAREHOUSE compute_wh SET AUTO_SUSPEND = 60;
```

Auto-suspend at 60 seconds is the production default.
Smaller values (e.g. 10s) save more credits but can
introduce cold-start latency. 60s is the sweet spot.

### The cost-arithmetic example

A `Medium` warehouse (4 credits/hour) running 24/7:
`24 × 4 = 96 credits/day ≈ 2880 credits/month`.

A `Medium` warehouse auto-suspended at 60s, running
8 hours of actual queries per day:
`8 × 4 = 32 credits/day ≈ 960 credits/month`.

The auto-suspend cut the cost by ~67% with no
performance change.

### Multi-cluster for high concurrency

If your BI tool has 50 users running dashboards at the
same time, a single cluster will queue them. A
multi-cluster warehouse (MAX_CLUSTER_COUNT = 5)
automatically adds clusters as needed:

```sql
ALTER WAREHOUSE compute_wh SET
  MIN_CLUSTER_COUNT = 1
  MAX_CLUSTER_COUNT = 5
  SCALING_POLICY   = 'STANDARD';
```

Each additional cluster is the same size as the first.
You pay for cluster seconds, not for the number of
clusters.

### A warehouse-per-purpose layout

```text
etl_wh          (Large,  Economy scaling)  for nightly ELT
bi_wh           (Medium, Standard, max 5) for BI tools
ad_hoc_wh       (Small,  Standard)         for analyst queries
admin_wh        (X-Small, Standard)        for one-off admin tasks
```

Four warehouses, four purposes. The `etl_wh` is large
because ETL is heavy; the `admin_wh` is small because it
runs once a day.

## Hands-on

```sql
-- Audit your warehouses
SHOW WAREHOUSES;

-- Right-size by looking at slow queries
SELECT warehouse_name,
       AVG(total_elapsed_time) AS avg_ms,
       MAX(total_elapsed_time) AS max_ms,
       COUNT(*)                AS query_count
FROM   TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE  start_time > DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP BY warehouse_name
ORDER BY max_ms DESC;
```

## Key takeaways

- Start with X-Small; scale up only if the workload
  is slow.
- Auto-suspend at 60s; saves 60%+ vs always-on.
- Standard scaling for BI; Economy for batch.
- Multi-cluster for high concurrency.

## What's next

L184 — Table design. The deeper dive on clustering, table
types, and naming conventions.