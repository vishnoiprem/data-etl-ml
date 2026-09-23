# Session-level Metrics (Duration, Event Count)

## Problem
After assigning `session_id` to each event row, collapse the data to one row per session and compute: session start, end, duration (seconds), event count, and the count of unique event types.

## How to Think
1. Run the sessionization pipeline first to get a `session_id` column on every event.
2. `GROUP BY session_id` (and `user_id` for safety) — everything else is an aggregation.
3. Duration is `MAX(event_ts) - MIN(event_ts)`; in SQL express as `UNIX_TIMESTAMP(max) - UNIX_TIMESTAMP(min)` for seconds.
4. Event count is `COUNT(*)`. Unique event-type count is `COUNT(DISTINCT event_name)`.
5. Optionally capture first/last event name to identify landing and exit actions.

## How to Remember
- **Pattern**: "Sessionize, then GROUP BY session_id."
- Duration is a derived column — it lives in the post-aggregation layer, not the window layer.
- Watch out for single-event sessions: their duration will be 0.

## SQL (Presto / Hive)
```sql
WITH sessions AS (
    SELECT
        user_id, event_ts, event_name,
        CONCAT(user_id, '_',
            SUM(CASE
                    WHEN LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts) IS NULL THEN 1
                    WHEN event_ts - LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts)
                         > INTERVAL '30' MINUTE THEN 1
                    ELSE 0
                END)
            OVER (PARTITION BY user_id ORDER BY event_ts)
        ) AS session_id
    FROM events
)
SELECT
    user_id,
    session_id,
    MIN(event_ts)                                                AS session_start,
    MAX(event_ts)                                                AS session_end,
    DATE_DIFF('second', MIN(event_ts), MAX(event_ts))             AS duration_sec,
    COUNT(*)                                                     AS event_count,
    COUNT(DISTINCT event_name)                                   AS unique_event_types,
    APPROX_PERCENTILE(DATE_DIFF('second', MIN(event_ts), event_ts), 0.5)
        OVER (PARTITION BY user_id, session_id)                  AS median_event_offset_sec
FROM sessions
GROUP BY user_id, session_id
ORDER BY user_id, session_start;
```

## Common Mistakes
- Mixing up `duration_sec = max - min` vs `max(event_ts) - event_ts` (the latter is offset-from-start, not session duration).
- Counting `event_count` before filtering bot/duplicate events (it'll be inflated).
- Forgetting that a single-event session has zero duration — these often need to be reported separately as "bounces".

## AI Use Cases
- Engagement modeling: session duration as a label for retention prediction.
- Anomaly detection: sudden drop in average duration across a cohort.
- Feed ranking: weight recent short sessions differently from recent long sessions.
