# Sessions per User per Day

## Problem
Given sessionized events, produce a daily report: for every `(user_id, day)` pair, how many distinct sessions did the user start that day, and how many events occurred in those sessions combined?

## How to Think
1. Compute `session_id` first (lag → flag → cumsum).
2. Derive `session_day = DATE(event_ts)` (or `date_trunc('day', event_ts)`).
3. `GROUP BY user_id, session_day`, then `COUNT(DISTINCT session_id)` for sessions and `COUNT(*)` for events.
4. Optional rollups: weekly averages, per-cohort comparison.
5. Filter out users with extreme values (bot candidates) before reporting.

## How to Remember
- **Pattern**: "session_id -> session_day -> GROUP BY user_id, session_day."
- A single session that crosses midnight: choose a rule — start-day or end-day — and stick to it. Most products use the start day.
- `COUNT(DISTINCT session_id)` is safe even if a user reuses a session_id by accident (the user_id prefix guarantees uniqueness).

## SQL (Presto / Hive)
```sql
WITH sessions AS (
    SELECT
        user_id,
        event_ts,
        CONCAT(user_id, '_',
            SUM(CASE
                    WHEN LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts) IS NULL THEN 1
                    WHEN event_ts - LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts)
                         > INTERVAL '30' MINUTE THEN 1
                    ELSE 0
                END)
            OVER (PARTITION BY user_id ORDER BY event_ts)
        ) AS session_id,
        DATE_TRUNC('day', event_ts) AS session_day
    FROM events
)
SELECT
    user_id,
    session_day,
    COUNT(DISTINCT session_id) AS sessions_in_day,
    COUNT(*)                   AS events_in_day
FROM sessions
GROUP BY user_id, session_day
ORDER BY user_id, session_day;
```

## Common Mistakes
- Counting sessions by counting event rows (events ≠ sessions).
- Mixing `DATE()` and `TIMESTAMP` types in the GROUP BY key — Presto and Hive are sometimes picky.
- Treating the day as UTC when the product is regional; align with the user's locale.
- Not partitioning the table on `session_day`, which causes expensive shuffles downstream.

## AI Use Cases
- KPI dashboards: DAU + sessions-per-DAU as one combined metric.
- Bot detection: flag users with >100 sessions/day.
- Capacity planning: peak session creation rate per hour per region.
