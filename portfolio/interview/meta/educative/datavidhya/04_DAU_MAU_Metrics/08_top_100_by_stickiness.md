# Top-100 Users by Stickiness

## Problem
Return the top 100 users ranked by per-user stickiness (active days in last 28 / 28).

## How to Think
1. Count distinct active days per user in the last 28 days.
2. Divide by 28.
3. ORDER BY stickiness DESC, LIMIT 100.

## How to Remember
- **Pattern**: "active_days / 28.0. ORDER BY DESC, LIMIT 100."
- Be explicit about the window anchor date.

## SQL (Presto / Hive)
```sql
WITH bounds AS (SELECT MAX(event_date) AS end_date FROM events)
SELECT user_id,
       COUNT(DISTINCT event_date) / 28.0 AS stickiness
FROM events, bounds
WHERE event_date BETWEEN DATE_SUB(end_date, 27) AND end_date
GROUP BY user_id
ORDER BY stickiness DESC
LIMIT 100;
```

## Common Mistakes
- Using a hardcoded "today" — backfill breaks.
- Counting events instead of distinct days.

## AI Use Cases
- Power-user identification for beta programs.
- ML feature for personalization.
- Reward-program eligibility.
