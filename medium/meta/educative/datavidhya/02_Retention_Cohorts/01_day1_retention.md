# Day-1 Retention (D1)

## Problem
For each signup cohort (signup date), compute the % of users active exactly 1 day later.

## How to Think
1. Identify signup events and active events separately.
2. Self-join or use a window join: signups.user_id = activity.user_id AND activity.event_date = signup_date + 1.
3. Aggregate: retained / cohort_size.

## How to Remember
- **Pattern**: "Signups -> cohort by signup_date -> left join activity on user_id + day math -> retention = retained / cohort."
- D1 = DATE_ADD(signup_date, 1).

## SQL (Presto / Hive)
```sql
SELECT s.signup_date,
       COUNT(DISTINCT s.user_id)                                            AS cohort_size,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 1)
                           THEN s.user_id END)                              AS retained_d1,
       COUNT(DISTINCT CASE WHEN a.event_date = DATE_ADD(s.signup_date, 1)
                           THEN s.user_id END) * 1.0 / COUNT(DISTINCT s.user_id) AS d1_retention
FROM signups s
LEFT JOIN activity a ON s.user_id = a.user_id
GROUP BY s.signup_date;
```

## Common Mistakes
- Counting users instead of distinct users — same user with multiple events inflates retention.
- Using INNER JOIN instead of LEFT JOIN — drops users who never returned.
- Forgetting to cast dates properly.

## AI Use Cases
- Onboarding funnel health check.
- New-user activation modeling.
- Retention as a feature in recommendation systems.
