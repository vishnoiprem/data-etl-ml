# Bracket Retention (D1 + D7 + D28 in one query)

## Problem
Compute D1, D7, and D28 retention in a single query, one row per cohort.

## How to Think
1. One LEFT JOIN of signups -> activity.
2. Multiple CASE WHEN clauses inside COUNT(DISTINCT ...) — one per bracket.
3. Compute cohort size once with COUNT(DISTINCT user_id).

## How to Remember
- **Pattern**: "One join, three CASE WHENs -> three bracket retentions."
- Each CASE WHEN only counts users active at exactly the offset date.

## SQL (Presto / Hive)
```sql
SELECT s.signup_date,
       COUNT(DISTINCT s.user_id)                                                                AS cohort_size,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 1)  THEN s.user_id END) AS retained_d1,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 7)  THEN s.user_id END) AS retained_d7,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 28) THEN s.user_id END) AS retained_d28
FROM signups s
LEFT JOIN activity a USING (user_id)
GROUP BY s.signup_date;
```

## Common Mistakes
- Counting retained in punctual terms when rolling is needed.
- Forgetting to divide by cohort_size — output is raw counts, not rates.

## AI Use Cases
- Single dashboard query covering all brackets.
- Cohort summary tables for executive reporting.
- A/B test retention delta computation.
