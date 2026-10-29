# Frame Specification: ROWS vs RANGE

## Problem
Compute rolling 7-day event total per user, even when dates have gaps.

## How to Think
1. ROWS counts rows regardless of date gaps.
2. RANGE spans a value/time interval — covers all rows within the calendar window.
3. For sparse data with missing days, RANGE is correct.

## How to Remember
- **Pattern**: "ROWS = count. RANGE = value/time interval."
- For rolling-by-time on sparse data, RANGE BETWEEN INTERVAL 'N' DAY PRECEDING.

## SQL (Presto / Hive)
```sql
SELECT user_id, dt, events,
       SUM(events) OVER (PARTITION BY user_id ORDER BY dt
                        ROWS  BETWEEN 1 PRECEDING AND CURRENT ROW) AS sum_rows,
       SUM(events) OVER (PARTITION BY user_id ORDER BY dt
                        RANGE BETWEEN INTERVAL '7' DAY PRECEDING AND CURRENT ROW) AS sum_7d_range
FROM user_events;
```

## Common Mistakes
- Using ROWS with sparse dates — get fewer days than expected.
- Using RANGE on non-deterministic columns (e.g., floats).

## AI Use Cases
- Rolling time-windowed features for sparse event data.
- Causally correct aggregations around a reference event.
- Window behavior for irregular time series.
