# Unbounded vs Bounded Rolling Retention

## Problem
Differentiate "active in [day+1, day+30]" (bounded) from "active any day after signup" (unbounded).

## How to Think
1. Bounded 30-day = DATEDIFF BETWEEN 1 AND 30.
2. Unbounded "ever returned" = DATEDIFF >= 1.
3. Unbounded grows with observation window; bounded is finite.

## How to Remember
- **Pattern**: "Bounded rolling N: BETWEEN 1 AND N. Unbounded: >= 1."
- Always state which one you're computing.

## SQL (Presto / Hive)
```sql
SELECT
  COUNT(DISTINCT s.user_id) AS cohort,
  COUNT(DISTINCT CASE WHEN DATEDIFF(a.event_date, s.signup_date) BETWEEN 1 AND 30 THEN s.user_id END) AS bounded_30d,
  COUNT(DISTINCT CASE WHEN DATEDIFF(a.event_date, s.signup_date) >= 1               THEN s.user_id END) AS unbounded
FROM signups s
LEFT JOIN activity a USING (user_id);
```

## Common Mistakes
- Comparing unbounded retention across cohorts of different ages — biased.
- Treating bounded rolling as "lifetime" — it's not.

## AI Use Cases
- Engagement windows for ML features.
- Re-engagement campaign windows.
- Lifetime value projection (bounded vs unbounded).
