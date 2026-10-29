# MAU (Monthly Active Users)

## Problem
For each calendar month, count distinct active users.

## How to Think
1. DATE_TRUNC('month', event_date) -> month bucket.
2. COUNT(DISTINCT user_id) per month.

## How to Remember
- **Pattern**: "DATE_TRUNC('month', dt), COUNT(DISTINCT user_id)."
- One row per month.

## SQL (Presto / Hive)
```sql
SELECT DATE_TRUNC('month', event_date) AS month,
       COUNT(DISTINCT user_id)         AS mau
FROM events
GROUP BY DATE_TRUNC('month', event_date)
ORDER BY 1;
```

## Common Mistakes
- Using EXTRACT(MONTH FROM dt) — drops the year.
- Forgetting that a user active on Jan 31 and Feb 1 counts in BOTH months.

## AI Use Cases
- Monthly executive dashboards.
- LTV projection.
- Cohort analysis input.
