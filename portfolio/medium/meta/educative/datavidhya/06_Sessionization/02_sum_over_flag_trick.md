# SUM-over-flag Trick (Assign session_id with Cumulative Sum)

## Problem
Produce a session id column using only `SUM(flag) OVER (PARTITION BY user_id ORDER BY event_ts)` — no joins, no group-by aggregations, just a running counter derived from a 0/1 flag that marks session boundaries.

## How to Think
1. Compute a flag per row: `1` when this row starts a session, otherwise `0`.
2. Apply a cumulative `SUM` window function with `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`.
3. The counter monotonically increases by `1` at every session start, giving you the session sequence number per user.
4. Concatenate `user_id` and the counter for a unique session id.

## How to Remember
- **Pattern**: "Flag once, sum across." A single window, no joins.
- This is preferred over sessionizing via `GROUP BY`/`struct` because it preserves row-level detail.
- Same pattern works for grouping runs of identical states, gap-detection on any time-series.

## SQL (Presto / Hive)
```sql
SELECT
    user_id,
    event_ts,
    event_name,
    CAST(SUM(is_new) OVER (PARTITION BY user_id ORDER BY event_ts
                           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS BIGINT) AS session_seq
FROM (
    SELECT
        user_id,
        event_ts,
        event_name,
        CASE
            WHEN LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts) IS NULL THEN 1
            WHEN event_ts - LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts)
                 > INTERVAL '30' MINUTE THEN 1
            ELSE 0
        END AS is_new
    FROM events
) t
ORDER BY user_id, event_ts;
```

## Common Mistakes
- Forgetting `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` — without it, the default frame in some engines behaves differently.
- Mixing data types (string vs timestamp) inside the interval subtraction.
- Off-by-one: the very first event MUST be flagged `1` (handle NULL).
- Recomputing the flag and the SUM in the same SELECT — pre-compute in a CTE for clarity.

## AI Use Cases
- Streaming inference: every incoming event can be enriched with the running session_id on the fly.
- Sequence models: embedding the session position (1st, 2nd, ...) per user.
- Engagement dashboards: replace messy self-joins with a single window pass.
