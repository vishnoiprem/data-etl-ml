# Day-28 Retention (D28)

## Problem
Of users who signed up, what % were active within 28 days of signup?

## How to Think
1. Punctual D28 = active exactly on day +28.
2. Rolling D28 = active at least once in [day+1, day+28] — preferred in Meta for habit tracking.
3. Same query, different range condition.

## How to Remember
- **Pattern**: "Punctual: DATEDIFF = 28. Rolling: DATEDIFF BETWEEN 1 AND 28."
- Be explicit about which one the interviewer wants.

## SQL (Presto / Hive)
```sql
SELECT
  COUNT(DISTINCT s.user_id) AS cohort,
  COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 28) THEN s.user_id END) AS punctual_d28,
  COUNT(DISTINCT CASE WHEN DATEDIFF(a.event_date, s.signup_date) BETWEEN 1 AND 28
                      THEN s.user_id END) AS rolling_d28
FROM signups s
LEFT JOIN activity a USING (user_id);
```

## Common Mistakes
- Confusing punctual vs rolling — interview answer depends on the question.
- Using DATEDIFF with timestamps instead of dates — sub-day offsets cause incorrect joins.

## AI Use Cases
- Habit-formation tracking.
- 28-day re-engagement campaigns.
- Long-tail retention modeling.
