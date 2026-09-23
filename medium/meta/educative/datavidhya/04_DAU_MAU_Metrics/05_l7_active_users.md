# L7 Active Users

## Problem
For each day, how many distinct users were active in the preceding 7 days (inclusive)?

## How to Think
1. For each day D, count distinct users with event_date in [D-6, D].
2. Self-join via a day-listing CTE.

## How to Remember
- **Pattern**: "L7(D) = COUNT(DISTINCT) WHERE event_date BETWEEN D-6 AND D."
- Inclusive of both endpoints.

## SQL (Presto / Hive)
```sql
WITH days AS (SELECT DISTINCT event_date AS dt FROM events)
SELECT d.dt,
       COUNT(DISTINCT e.user_id) AS l7_active_users
FROM days d
LEFT JOIN events e ON e.event_date BETWEEN DATE_SUB(d.dt, 6) AND d.dt
GROUP BY d.dt
ORDER BY d.dt;
```

## Common Mistakes
- Off-by-one: L7 should be 7 days, including today — that's `D-6 .. D` (6 preceding + 1 current).
- Counting events instead of users.

## AI Use Cases
- Reach metric for ad campaigns.
- Power-user targeting.
- Cohort feature for ranking.
