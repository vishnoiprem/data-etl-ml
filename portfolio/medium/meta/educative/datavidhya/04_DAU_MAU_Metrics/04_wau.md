# WAU (Weekly Active Users)

## Problem
For each calendar week, count distinct active users.

## How to Think
1. DATE_TRUNC('week', event_date) -> week bucket (Monday in Presto).
2. COUNT(DISTINCT user_id) per week.

## How to Remember
- **Pattern**: "DATE_TRUNC('week', dt), COUNT(DISTINCT user_id)."
- Note the locale (Presto = Monday, some engines = Sunday).

## SQL (Presto / Hive)
```sql
SELECT DATE_TRUNC('week', event_date) AS week_start,
       COUNT(DISTINCT user_id)         AS wau
FROM events
GROUP BY DATE_TRUNC('week', event_date)
ORDER BY 1;
```

## Common Mistakes
- Mixing week-of-year and week_start — different aggregations.
- Forgetting TZ shift issues — week boundaries change by TZ.

## AI Use Cases
- Weekly growth dashboards.
- WAU/MAU comparison for stickiness.
- Short-cycle engagement tracking.
