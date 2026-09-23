# Custom Gap Threshold (e.g., 10 min)

## Problem
Generalize the classic sessionization to an arbitrary inactivity gap (10 minutes in this case). The interviewer wants to see that the threshold is a parameter, not a magic number baked into the WHERE clause.

## How to Think
1. Take the same `lag → flag → cumsum` flow.
2. Replace the hard-coded 30-minute literal with a variable: in PySpark pass it as a Python constant; in Presto use a session parameter `${gap_minutes}` or a typed literal.
3. Document the threshold near the top of the SQL or job code, so analysts can search-and-replace safely.
4. Re-run on production data and compare session counts vs the 30-min baseline to validate.

## How to Remember
- **Pattern**: "Always parameterize the gap." Even when the spec says 30, write it as a variable so dashboards can be regenerated at 10, 20, or 60.
- 10 min = 600 seconds = `INTERVAL '10' MINUTE`.
- Add unit tests: synthetic events with gaps exactly equal to the threshold should still belong to the SAME session (strict `>`).

## SQL (Presto / Hive)
```sql
WITH lagged AS (
    SELECT
        user_id, event_ts, event_name,
        LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts) AS prev_ts
    FROM events
)
SELECT
    user_id,
    MIN(event_ts) AS session_start,
    MAX(event_ts) AS session_end,
    TIMESTAMPDIFF(MINUTE, MIN(event_ts), MAX(event_ts)) AS duration_min,
    COUNT(*)        AS event_count,
    CONCAT(user_id, '_',
        SUM(CASE
                WHEN prev_ts IS NULL THEN 1
                WHEN event_ts - prev_ts > INTERVAL '10' MINUTE THEN 1
                ELSE 0
            END)
        OVER (PARTITION BY user_id ORDER BY event_ts)
    ) AS session_id
FROM lagged
GROUP BY user_id, event_name, event_ts, prev_ts;
```

## Common Mistakes
- Off-by-one on `>` vs `>=`: the threshold should be a strict greater-than.
- Changing only the Python constant and forgetting to update the SQL sample (or vice versa).
- Using local 30-min history as a baseline without verifying schema/sort order.

## AI Use Cases
- Bandit-based threshold tuning per surface (Feed vs Stories vs Reels).
- Sensitivity reporting: how do engagement metrics move when the gap changes?
- Anomaly detection: alert when a user's typical session length shifts beyond a learned band.
