# Power-User Retention Curves (Top-Decile vs Median)

## Problem
Compare D7 retention of top-decile users (by lifetime engagement) vs median users.

## How to Think
1. Compute lifetime event count per user.
2. NTILE(10) to bucket into deciles.
3. Join bucket back, compute retention per decile.

## How to Remember
- **Pattern**: "NTILE -> bucket -> retention by bucket."
- Top-decile curve should dominate median.

## SQL (Presto / Hive)
```sql
WITH lifetime AS (
  SELECT user_id, COUNT(*) AS lifetime_events FROM activity GROUP BY user_id
),
buckets AS (
  SELECT user_id, NTILE(10) OVER (ORDER BY lifetime_events DESC) AS decile FROM lifetime
)
SELECT b.decile,
       COUNT(DISTINCT s.user_id) AS cohort,
       COUNT(DISTINCT CASE WHEN DATEDIFF(a.event_date, s.signup_date) BETWEEN 1 AND 7
                           THEN s.user_id END) AS d7_retained,
       COUNT(DISTINCT CASE WHEN DATEDIFF(a.event_date, s.signup_date) BETWEEN 1 AND 7
                           THEN s.user_id END) * 1.0 / COUNT(DISTINCT s.user_id) AS d7_retention
FROM signups s JOIN buckets b USING (user_id)
LEFT JOIN activity a ON a.user_id = s.user_id
GROUP BY b.decile ORDER BY 1;
```

## Common Mistakes
- Bucketing before filtering — inactive users skew the bucket assignment.
- Small cohort deciles (NTILE of 10 with < 100 users) -> noisy.

## AI Use Cases
- Power-user feature treatment.
- Tiered engagement strategy.
- Cohort forecasting by user segment.
