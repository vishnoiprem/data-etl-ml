# DAU/MAU Stickiness

## Problem
For each month, compute the stickiness ratio: DAU / MAU.

## How to Think
1. Compute daily DAU per day.
2. Compute monthly MAU.
3. Aggregate avg(DAU) over the month, divide by MAU.

## How to Remember
- **Pattern**: "AVG(DAU) / MAU. Cap at 1 if needed."
- Stickiness is per-user when computed differently (see top-100 by stickiness).

## SQL (Presto / Hive)
```sql
WITH dau AS (
  SELECT DATE_TRUNC('month', event_date) AS month,
         event_date                      AS dt,
         COUNT(DISTINCT user_id)         AS dau
  FROM events GROUP BY 1, 2
),
mau AS (
  SELECT DATE_TRUNC('month', event_date) AS month,
         COUNT(DISTINCT user_id)         AS mau
  FROM events GROUP BY 1
)
SELECT d.month, AVG(d.dau) AS avg_dau, MAX(m.mau) AS mau,
       AVG(d.dau) * 1.0 / MAX(m.mau) AS stickiness
FROM dau d JOIN mau m USING (month)
GROUP BY d.month ORDER BY 1;
```

## Common Mistakes
- Dividing by 0 (no users in a month).
- Using DAU on day 1 and MAU for the month — different bases.

## AI Use Cases
- Engagement-quality metric (per-user stickiness is a powerful ML feature).
- Cohort health scoring.
- A/B test primary metric.
