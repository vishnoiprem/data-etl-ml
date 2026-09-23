# L28 Active Users

## Problem
For each day, how many distinct users were active in the preceding 28 days (inclusive)?

## How to Think
1. For each day D, count distinct users with event_date in [D-27, D].
2. Self-join via a day-listing CTE.

## How to Remember
- **Pattern**: "L28(D) = COUNT(DISTINCT) WHERE event_date BETWEEN D-27 AND D."
- 28 = D-27 + current.

## SQL (Presto / Hive)
```sql
WITH days AS (SELECT DISTINCT event_date AS dt FROM events)
SELECT d.dt,
       COUNT(DISTINCT e.user_id) AS l28_active_users
FROM days d
LEFT JOIN events e ON e.event_date BETWEEN DATE_SUB(d.dt, 27) AND d.dt
GROUP BY d.dt
ORDER BY d.dt;
```

## Common Mistakes
- Using BETWEEN D-28 AND D — gives a 29-day window.
- Counting events instead of distinct users.

## AI Use Cases
- Habit-formation metric.
- Engagement features for ranking.
- Lifecycle-stage classification.
