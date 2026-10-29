# Moving Averages / Rolling Windows

## Problem
Compute a 7-day rolling DAU to smooth weekday/weekend noise.

## How to Think
1. ROWS BETWEEN 6 PRECEDING AND CURRENT ROW = 7-row window.
2. For date gaps (missing days), use RANGE BETWEEN INTERVAL '6' DAY PRECEDING AND CURRENT ROW to keep window anchored to time.
3. Use partial-window AVG during the first 6 days (it'll average fewer rows).

## How to Remember
- **Pattern**: "AVG(col) OVER (ORDER BY dt ROWS BETWEEN N-1 PRECEDING AND CURRENT ROW)."
- ROWS = count rows. RANGE = span time/value.

## SQL (Presto / Hive)
```sql
SELECT dt, dau,
       AVG(dau) OVER (ORDER BY dt ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS dau_7d_avg
FROM daily_active_users;
```

## Common Mistakes
- Using RANGE with date gaps — missing dates shrink the window unexpectedly.
- Off-by-one: 7-day window = 6 PRECEDING + CURRENT.

## AI Use Cases
- Smoothing noisy time-series metrics.
- Anomaly detection (current vs rolling baseline).
- Time-series features for forecasting.
