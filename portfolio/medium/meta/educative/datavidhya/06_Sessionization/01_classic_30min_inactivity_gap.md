# Classic 30-min Inactivity Gap Sessionization

## Problem
Given a stream of user events (`user_id`, `event_ts`, `event_name`), assign each event to a session such that two consecutive events belong to the same session only if they occurred within 30 minutes of each other. A gap longer than 30 minutes starts a new session.

## How to Think
1. Partition by `user_id` and order by `event_ts` using a window function.
2. Use `LAG(event_ts)` to fetch the previous timestamp within the user partition.
3. Compute a boolean flag `is_new_session = (prev_ts IS NULL) OR (event_ts - prev_ts > 30 min)`.
4. Take a cumulative `SUM(is_new_session)` over the same window to get a session sequence number per user.
5. Concatenate `user_id` and the sequence number to form a unique `session_id`.

## How to Remember
- **Pattern**: "lag → flag → cumsum" — the canonical three-step recipe for gap-based sessionization.
- The very first event for any user always starts a new session (prev_ts IS NULL).
- 30 minutes is industry default (Google Analytics); Meta often uses 30 minutes as well.

## SQL (Presto / Hive)
```sql
WITH lagged AS (
  SELECT user_id, event_ts, event_name,
         LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts) AS prev_ts
  FROM events
),
flags AS (
  SELECT user_id, event_ts, event_name,
         CASE
           WHEN prev_ts IS NULL THEN 1
           WHEN (event_ts - prev_ts) > INTERVAL '30' MINUTE THEN 1
           ELSE 0
         END AS is_new_session
  FROM lagged
)
SELECT user_id, event_ts, event_name,
       CONCAT(user_id, '_', SUM(is_new_session) OVER (PARTITION BY user_id ORDER BY event_ts)) AS session_id
FROM flags
ORDER BY user_id, event_ts;
```

## Common Mistakes
- Forgetting to handle NULL for the first event per user.
- Using wall-clock instead of user-local time for the threshold (time-zone blind sessions).
- Partitioning by both `user_id` AND `day` when events span across day boundaries — this breaks sessions that cross midnight.
- Comparing timestamps as strings instead of casting to `TIMESTAMP`.

## AI Use Cases
- Session-level conversion modeling: predict purchase probability given events in the active session.
- Churn signals: sudden change in session length distribution per user.
- Personalization: real-time ranking models consume the current session's event sequence as features.
