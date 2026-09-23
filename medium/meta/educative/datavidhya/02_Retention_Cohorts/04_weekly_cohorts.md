# Weekly Retention Cohorts

## Problem
Group signups by signup-week; for each cohort, count distinct users active at week-offset 0..8.

## How to Think
1. Truncate signup_date to the week boundary (DATE_TRUNC('week', signup_date)).
2. week_offset = FLOOR(DATEDIFF(event_date, signup_date) / 7).
3. Aggregate (cohort, offset) -> distinct active users.

## How to Remember
- **Pattern**: "DATE_TRUNC('week', dt) -> cohort. DATEDIFF/7 -> offset."
- Keep week_offset as a column — easy to pivot later.

## SQL (Presto / Hive)
```sql
SELECT
  DATE_TRUNC('week', s.signup_date)                                AS cohort_week,
  FLOOR(DATEDIFF(a.event_date, s.signup_date) / 7)                 AS week_offset,
  COUNT(DISTINCT s.user_id)                                        AS active_users
FROM signups s
LEFT JOIN activity a USING (user_id)
GROUP BY 1, 2
ORDER BY 1, 2;
```

## Common Mistakes
- Locale differences — DATE_TRUNC('week') starts on Monday in Presto but Sunday in some engines.
- Dividing DATEDIFF by 7 directly without FLOOR — partial weeks round wrong.

## AI Use Cases
- Cohort dashboards (AppsFlyer, Amplitude style).
- Long-term retention tracking.
- Churn-risk feature engineering.
