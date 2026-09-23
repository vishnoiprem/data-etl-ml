# Detect Bounces (Single-event Sessions)

## Problem
A "bounce" is a session that contains exactly one event. Given sessionized data, list all bounce sessions along with the timestamp and event type of the lone event.

## How to Think
1. Run the sessionization pipeline; you have one row per event with a `session_id`.
2. `GROUP BY session_id` and count rows.
3. Filter to `HAVING COUNT(*) = 1`.
4. Join back (or project) to retrieve the timestamp and event_name of that sole event.
5. Aggregate bounce counts per user, surface, country, or campaign to prioritize fixes.

## How to Remember
- **Pattern**: "HAVING COUNT(*) = 1" — the SQL equivalent of `filter(col("c") == 1)` after `groupBy`.
- Bounces have `duration_sec = 0`, so duration-based filters work too, but they're ambiguous (a 1-second multi-event session looks the same). Prefer the explicit count.
- Most product analytics treat bounces as "non-engaged" and exclude them from session-time averages.

## SQL (Presto / Hive)
```sql
WITH sessions AS (
    SELECT
        user_id,
        event_ts,
        event_name,
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
    event_ts   AS bounce_at,
    event_name AS bounce_event
FROM sessions
GROUP BY user_id, session_id, event_ts, event_name
HAVING COUNT(*) = 1
ORDER BY user_id, bounce_at;
```

## Common Mistakes
- Defining a bounce as "duration = 0" — a real 2-event session faster than 1 second would be misclassified.
- Counting `event_count = 1` BEFORE removing client-side duplicate events (which would otherwise inflate bounce rate).
- Confusing "bounce" with "exit" — exit is the last event of any session; bounce is a session that had only one event.

## AI Use Cases
- Onboarding optimization: rank onboarding steps by bounce rate to prioritize redesigns.
- Spam/bot detection: aggregate bounce share per user; >80% is a strong signal.
- Ad relevance: bounce rate after a paid click is one of the most important ad-quality features.
