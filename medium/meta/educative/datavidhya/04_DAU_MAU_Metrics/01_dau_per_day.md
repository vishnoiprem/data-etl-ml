# DAU per Day

## Problem
How many distinct users generated at least one event each day?

## How to Think
1. Group by calendar date (DATE(ts)).
2. COUNT(DISTINCT user_id) per day.
3. Grain: one row per day.

## How to Remember
- **Pattern**: "COUNT(DISTINCT user_id) GROUP BY DATE(ts)."
- Use DATE() or cast to DATE for clean grouping.

## SQL (Presto / Hive)
```sql
SELECT DATE(ts) AS dt, COUNT(DISTINCT user_id) AS dau
FROM events
GROUP BY DATE(ts)
ORDER BY dt;
```

## Common Mistakes
- Using COUNT(*) instead of COUNT(DISTINCT) — inflates DAU.
- Truncating to hour instead of day — wrong granularity.

## AI Use Cases
- Anomaly detection on DAU drops.
- Forecasting models use DAU as a target.
- Capacity planning.
