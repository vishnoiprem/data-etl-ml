# LAG / LEAD — Consecutive Session Compare

## Problem
For each user, compute the gap in seconds between consecutive event timestamps.

## How to Think
1. Partition by `user_id`, order by `ts`.
2. LAG reads the previous row's `ts`. Subtract from current `ts`.
3. Default behavior: first row in partition has no previous, returns NULL.
4. You can pass a third arg as default (e.g., `LAG(ts, 1, 0)`).

## How to Remember
- **Pattern**: "PARTITION BY user ORDER BY ts, then LAG(ts, 1)."
- LAG = backward, LEAD = forward.
- Difference LAG and LEAD only in direction.

## SQL (Presto / Hive)
```sql
SELECT user_id, ts,
       LAG(ts, 1) OVER (PARTITION BY user_id ORDER BY ts) AS prev_ts,
       UNIX_TIMESTAMP(ts) - UNIX_TIMESTAMP(LAG(ts, 1) OVER (PARTITION BY user_id ORDER BY ts)) AS delta_sec
FROM events;
```

## Common Mistakes
- Forgetting PARTITION BY — result is global, not per-user.
- Forgetting ORDER BY — undefined ordering, meaningless lag.
- Casting types — UNIX_TIMESTAMP expects a string timestamp.

## AI Use Cases
- Sequential feature engineering (time delta -> RNN/LSTM input).
- Churn prediction: gap between user sessions.
- Drop-off detection: long delays before the next funnel step.
