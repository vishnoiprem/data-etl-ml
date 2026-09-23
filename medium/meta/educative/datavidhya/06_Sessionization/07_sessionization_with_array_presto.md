# Sessionization with Array-of-Events (Presto)

## Problem
Collapse sessionized events into a single row per session where each row carries a Presto `ARRAY<ROW(timestamp, event_name)>` representing the chronological list of events.

## How to Think
1. Compute `session_id` per row using the lag → flag → cumsum recipe.
2. `GROUP BY session_id`, aggregate with `MIN(event_ts)`, `MAX(event_ts)`.
3. Use Presto's `ARRAY_AGG(ROW(event_ts, event_name) ORDER BY event_ts)` to keep the chronological order.
4. Inspect first/last events with `events[1]` and `events[-1]`.
5. The resulting table has one row per session — perfect for ML pipelines that expect variable-length sequences.

## How to Remember
- **Pattern**: "sessionize → GROUP BY → ARRAY_AGG ... ORDER BY ts."
- `ROW(ts, name)` is a struct; `CAST(ROW(...) AS ROW(ts TIMESTAMP, name VARCHAR))` makes types explicit.
- Hive does not support `ROW()` literals — use `named_struct("ts", event_ts, "name", event_name)` instead.

## SQL (Presto)
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
    MIN(event_ts) AS session_start,
    MAX(event_ts) AS session_end,
    ARRAY_AGG(CAST(ROW(event_ts, event_name) AS ROW(ts TIMESTAMP, name VARCHAR))
              ORDER BY event_ts) AS events
FROM sessions
GROUP BY user_id, REGEXP_REPLACE(session_id, '^[^_]+_', '')
ORDER BY user_id, session_start;
```

## Common Mistakes
- Forgetting `ORDER BY event_ts` inside `ARRAY_AGG` — the array will be unordered.
- Using Hive `concat_ws` on the session sequence number with a literal user_id prefix — Presto's `ROW()` syntax differs.
- Producing huge arrays for power users (10k+ events) — add a max-length guard or sample.

## AI Use Cases
- Sequence-to-sequence models for next-event prediction.
- Session-level embeddings (mean-pool of event embeddings).
- Anomaly detection: compare each session's array against a learned normal distribution.
