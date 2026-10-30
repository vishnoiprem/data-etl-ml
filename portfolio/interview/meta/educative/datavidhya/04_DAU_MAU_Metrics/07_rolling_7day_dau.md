# 7-Day Rolling DAU

## Problem
For each day, the average DAU over the trailing 7 days.

## How to Think
1. Compute per-day DAU first.
2. Apply a 7-row moving average: window with ROWS BETWEEN 6 PRECEDING AND CURRENT ROW.
3. Use RANGE for time-based windows when days may be missing.

## How to Remember
- **Pattern**: "AVG(dau) OVER (ORDER BY dt ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)."
- ROWS = count; RANGE = time span.

## SQL (Presto / Hive)
```sql
SELECT event_date, dau,
       AVG(dau) OVER (ORDER BY event_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS dau_7d_avg
FROM dau_temp
ORDER BY event_date;
```

## Common Mistakes
- Using RANGE on sparse dates — shrinks the window when gaps exist.
- Off-by-one: 7-day = 6 PRECEDING + CURRENT.

## AI Use Cases
- Anomaly detection (current vs rolling baseline).
- Time-series forecasting baseline.
