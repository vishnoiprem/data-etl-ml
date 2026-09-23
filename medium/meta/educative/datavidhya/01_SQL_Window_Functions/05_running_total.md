# Running Total / Cumulative SUM

## Problem
Compute cumulative daily ad revenue so PMs can see when each campaign hits milestones.

## How to Think
1. Default frame is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`.
2. For date-typed columns, use `ROWS BETWEEN` for deterministic behavior at ties.
3. Add PARTITION BY to reset per group (e.g., per campaign).

## How to Remember
- **Pattern**: "SUM(col) OVER (ORDER BY dt) -> running total."
- Add PARTITION BY to reset per key.

## SQL (Presto / Hive)
```sql
SELECT dt, revenue,
       SUM(revenue) OVER (ORDER BY dt ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cum_revenue
FROM daily_revenue;
```

## Common Mistakes
- Using RANGE on duplicates — RANGE treats ties as a single group; ROWS counts each row.
- Forgetting ORDER BY — result is just SUM over the whole partition.

## AI Use Cases
- Cumulative ad spend / revenue tracking.
- Time-to-target detection.
- Sequential training labels for time-series ML.
