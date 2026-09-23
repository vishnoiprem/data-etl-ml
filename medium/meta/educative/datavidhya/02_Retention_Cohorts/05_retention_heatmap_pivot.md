# Retention Heatmap (Cohort x Day-N Pivot)

## Problem
Build a cohort heatmap: rows = signup-week, columns = week 0..7, cells = retention %.

## How to Think
1. Compute cohort_size per cohort.
2. Compute (cohort, week_offset, active_users) long-format table.
3. Pivot with MAX(CASE WHEN offset = N THEN ...) / cohort_size.

## How to Remember
- **Pattern**: "Long -> wide via SUM/MAX(CASE WHEN offset = N THEN rate END)."
- Self-join or pre-compute cohort_size for the denominator.

## SQL (Presto / Hive)
```sql
WITH cohort_sizes AS (
  SELECT DATE_TRUNC('week', signup_date) AS cohort_week,
         COUNT(DISTINCT user_id) AS cohort_size
  FROM signups GROUP BY 1
),
activity_long AS (
  SELECT DATE_TRUNC('week', s.signup_date) AS cohort_week,
         FLOOR(DATEDIFF(a.event_date, s.signup_date) / 7) AS week_offset,
         COUNT(DISTINCT s.user_id) AS active_users
  FROM signups s LEFT JOIN activity a USING (user_id)
  GROUP BY 1, 2
)
SELECT
  a.cohort_week,
  MAX(CASE WHEN week_offset = 0 THEN active_users END) * 1.0 / MAX(cs.cohort_size) AS w0,
  MAX(CASE WHEN week_offset = 1 THEN active_users END) * 1.0 / MAX(cs.cohort_size) AS w1,
  MAX(CASE WHEN week_offset = 2 THEN active_users END) * 1.0 / MAX(cs.cohort_size) AS w2
FROM activity_long a JOIN cohort_sizes cs USING (cohort_week)
GROUP BY 1 ORDER BY 1;
```

## Common Mistakes
- Forgetting cohort_size denominator — output looks like raw counts, not %.
- Using AVG instead of MAX — averages dilute the cell value.

## AI Use Cases
- Cohort dashboards (Mixpanel/Amplitude style).
- Heatmap visualization for retention.
- Feature creation (per-cohort retention rate) for ML.
