---
l_id: L55
title: "Scaling up"
duration: "7:00"
prereqs:
  - L54 (Implement dedicated virtual warehouse)
---

# L55 — Scaling up

> **Section:** 7 — Performance optimization
> **Duration:** 7:00

## Prereqs

- L54 — Implement dedicated virtual warehouse

## Key terms

- **`ALTER WAREHOUSE … SET WAREHOUSE_SIZE`** — the command to
  resize. Takes effect for the next query; the current query
  finishes on the old size.
- **Linear scaling** — for purely compute-bound queries,
  doubling the warehouse size roughly halves the wall-clock
  time at the **same total cost**.
- **Diminishing returns** — once a query is I/O bound (reading
  from S3) or memory bound (large hash join), adding compute
  stops helping.

## Lecture

"Scale up" is the simplest performance lever in Snowflake: make
the warehouse bigger. Each step doubles the resources **and the
per-second credit cost**, but the **wall-clock** for a
compute-bound query drops roughly linearly. Total cost is
approximately the same; you trade latency for parallelism.

### Resize a warehouse

```sql
ALTER WAREHOUSE loading_wh SET WAREHOUSE_SIZE = 'LARGE';
```

The change is **non-disruptive**: in-flight queries finish on
the old size, the warehouse resumes on the new size. You can
also do this from the UI: **Warehouses → loading_wh →
Configure → Size**.

### When scale up helps

Compute-bound queries. A query that spends most of its time
**scanning + filtering + joining** in CPU. Typical signals:

- "Partitions scanned" is large and "Bytes scanned" is large.
- The query profile shows a wide green bar (compute) and
  narrow blue bars (I/O).
- A 2× size bump gives a noticeable latency drop.

For our 10 GB `raw_orders_parquet` table:

| Warehouse size | Wall-clock (s) | Credits used | $ (approx) |
|---|---|---|---|
| Small   | 90 | 1.5 | $6 |
| Medium  | 50 | 1.7 | $7 |
| Large   | 30 | 2.0 | $8 |
| X-Large | 20 | 2.7 | $11 |

Same query, **same cost band**. The savings are in **waiting
time**, not in dollars.

### When scale up does **not** help

Three scenarios where bigger is not better:

1. **I/O-bound queries** — if the bottleneck is reading 100 GB
   from S3, doubling CPUs doesn't halve the wall-clock. You're
   waiting on the network, not the CPU.
2. **Result-set-bound queries** — if the bottleneck is sending
   a huge result to the client, more compute doesn't help.
3. **Single-threaded code paths** — some Snowflake operators
   (e.g. certain sorts) don't parallelise past a point.

### A scale-up experiment you can run

```sql
USE WAREHOUSE loading_wh;

-- Run with current size
SELECT COUNT(*) FROM raw_orders_parquet;   -- note wall-clock

-- Resize
ALTER WAREHOUSE loading_wh SET WAREHOUSE_SIZE = 'XLARGE';

-- Re-run
SELECT COUNT(*) FROM raw_orders_parquet;   -- wall-clock should drop
```

Open the Query History and compare the two queries'
`Total_elapsed_time`. With a 10 GB table you should see a
**3–4× speedup** from Small → X-Large.

### Auto-scale for predictable spikes

For **predictable** spikes (a 2 GB CSV that arrives every
night), resize on a schedule using a Task or a cron-driven
stored procedure:

```sql
-- Run at 1:55 AM, before the load
ALTER WAREHOUSE loading_wh SET WAREHOUSE_SIZE = 'X-LARGE';
-- Run at 3:00 AM, after the load
ALTER WAREHOUSE loading_wh SET WAREHOUSE_SIZE = 'MEDIUM';
```

Or use the **Resource Monitor → Scale** actions in the UI. We
cover cron-driven tasks later in the course.

### Pitfall — leaving the warehouse at the big size

The most common scale-up mistake is to **forget to scale
back down**. A `Large` warehouse left running 24/7 bills
roughly 8× what an `X-Small` does for the same idle time.
Pair every scale-up with a scale-down (Task, calendar, or
just a note in your runbook).

### Cost-aware sizing rule of thumb

- **Loading a multi-GB file**: `Medium`–`Large`. The few extra
  minutes you save are worth the bigger size.
- **Ad-hoc analyst queries**: `Small`–`Medium`. Most queries
  are selective and finish in seconds.
- **Dashboards**: `X-Small`–`Small`. Frequent short queries;
  the per-second cost dominates.
- **Materialised view refresh**: `Large`–`X-Large`. The
  refresh is the bottleneck; the cost is one-shot.

## Hands-on

Run the scale-up experiment above. Note the wall-clock
difference. Then `ALTER WAREHOUSE loading_wh SET
WAREHOUSE_SIZE = 'MEDIUM';` to leave the warehouse at a
reasonable size for the rest of the course.

## Quiz prep

- Does scale up save total cost or wall-clock time?
- What kinds of queries benefit most from scale up?
- What is the most common scale-up mistake?

## Key takeaways

- Scale up is **`ALTER WAREHOUSE … SET WAREHOUSE_SIZE`**.
- Compute-bound queries scale roughly linearly; **total cost
  is roughly flat**, only wall-clock changes.
- I/O-bound and result-bound queries don't benefit.
- **Always scale back down** to avoid idle-cost surprises.

## What's next

In **L56 — Scaling out** we'll look at the complementary
lever: adding **clusters** to a multi-cluster warehouse so
many concurrent users don't queue.