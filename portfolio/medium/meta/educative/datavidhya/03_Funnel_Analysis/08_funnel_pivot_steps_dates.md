# Funnel Pivot (Steps x Dates Matrix)

## Problem
Produce a matrix where rows are funnel steps and columns are dates (one column
per day). Each cell holds the distinct user count for that step on that date.

## How to Think
1. Group by (date, user) to get per-user per-day max step.
2. Then aggregate by (date, max_step) to get user counts.
3. Pivot step rows into columns (or date columns into rows -- whichever the
   downstream chart expects).
4. Use `na.fill(0)` for missing combinations -- NaN silently breaks dashboards.
5. Partition by `event_date` (date column) so the table is bucketed for pruning.

## How to Remember
- **Pattern**: "GROUP BY (date, user, max_step) -> pivot -> fillna 0."
- **Anti-pattern**: `pivot` without an explicit value list -- produces dynamic columns.
- **Watch out**: time zones -- always pin to UTC at the SQL boundary.

## SQL (Presto / Hive)
```sql
WITH step_users AS (
  SELECT event_date, user_id,
         MAX(CASE event_name
             WHEN 'impression'  THEN 1
             WHEN 'click'       THEN 2
             WHEN 'add_to_cart' THEN 3
             WHEN 'purchase'    THEN 4 END) AS max_step
  FROM events
  WHERE event_date BETWEEN CURRENT_DATE - INTERVAL '14' DAY
                       AND CURRENT_DATE
  GROUP BY event_date, user_id
),
buckets AS (
  SELECT event_date, max_step, COUNT(DISTINCT user_id) AS users
  FROM step_users
  GROUP BY event_date, max_step
)
SELECT max_step,
       SUM(CASE WHEN event_date = CURRENT_DATE     THEN users END) AS d0,
       SUM(CASE WHEN event_date = CURRENT_DATE - 1 THEN users END) AS d1,
       SUM(CASE WHEN event_date = CURRENT_DATE - 2 THEN users END) AS d2
       -- repeat per day ...
FROM buckets
GROUP BY max_step
ORDER BY max_step;
```

## Common Mistakes
- Using `pivot` without specifying value list -- unstable column order.
- Forgetting to fill 0 -- chart tools drop the bar instead of showing zero.
- Mismatching date ranges between pivot columns.

## AI Use Cases
- **Time-series forecasting**: pivot matrix as multi-variate input to LSTM/TFT.
- **Drift detection**: compare today's pivot against 28-day reference.
- **Anomaly detection**: per-cell deviation vs baseline triggers alerts.
- **Auto-scaling**: pivot informs per-step traffic patterns.
