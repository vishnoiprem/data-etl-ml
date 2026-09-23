# Gaps and Islands — Consecutive Streak Detection

## Problem
For each user, find their consecutive-day login streaks.

## How to Think
1. ROW_NUMBER() per user ordered by date.
2. `date - rn = island_id` — within a consecutive run, the difference is constant.
3. GROUP BY (user_id, island_id) to get start, end, and length of each streak.

## How to Remember
- **Pattern**: "date - ROW_NUMBER() = island id."
- Same island_id rows are consecutive.

## SQL (Presto / Hive)
```sql
WITH base AS (
  SELECT user_id, dt,
         ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY dt) AS rn
  FROM user_logins
)
SELECT user_id,
       DATE_SUB(dt, rn) AS island_id,
       MIN(dt) AS streak_start,
       MAX(dt) AS streak_end,
       COUNT(*) AS days
FROM base
GROUP BY user_id, island_id;
```

## Common Mistakes
- Casting dates — DATE_SUB expects a date, not a string.
- Forgetting to cast `dt` to DATE.

## AI Use Cases
- Streak detection (login streaks, purchase streaks).
- Activity burst detection.
- Consecutive-event windowing.
