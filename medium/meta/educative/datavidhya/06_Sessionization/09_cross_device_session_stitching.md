# Cross-device Session Stitching (via login event)

## Problem
A user has multiple devices (phone, tablet, desktop). Without authentication, each device emits events under its own `device_id`. When the user logs in on one device, all events on that device (and other devices attributed via the login graph) should be stitched into one logical user session.

## How to Think
1. Identify "login anchor" events — those that carry both a `device_id` and a canonical `user_id`.
2. Propagate that `user_id` to all subsequent events on the same `device_id` (within a TTL) using `LAST_VALUE(user_id IGNORE NULLS) OVER (...)`.
3. The output gives every event a `canonical_user_id` (fallback: `anon`).
4. Run the standard lag → flag → cumsum sessionization, but partition by `canonical_user_id` instead of `device_id`.
5. Devices without a recent login within the TTL remain `anon` and never get stitched.

## How to Remember
- **Pattern**: "anchor → propagate → re-sessionize."
- `LAST_VALUE(... IGNORE NULLS)` is the canonical forward-fill within a partition.
- TTL is critical: choose based on product lifespan of a session anchor (Meta uses ~30 days).
- Stitching is lossy; some on-device re-use (kids on parent's tablet) will be mis-attributed.

## SQL (Presto / Hive)
```sql
WITH canonical AS (
    SELECT
        device_id, event_ts, event_name, user_id,
        COALESCE(
            LAST_VALUE(user_id IGNORE NULLS) OVER (
                PARTITION BY device_id ORDER BY event_ts
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ),
            'anon'
        ) AS canonical_user
    FROM events
),
stitched AS (
    SELECT
        *,
        LAG(event_ts) OVER (PARTITION BY canonical_user ORDER BY event_ts) AS prev_ts
    FROM canonical
)
SELECT
    canonical_user,
    device_id,
    event_ts,
    event_name,
    CONCAT(canonical_user, '_',
        SUM(CASE
                WHEN prev_ts IS NULL THEN 1
                WHEN event_ts - prev_ts > INTERVAL '30' MINUTE THEN 1
                ELSE 0
            END)
        OVER (PARTITION BY canonical_user ORDER BY event_ts)
    ) AS session_id
FROM stitched
ORDER BY canonical_user, event_ts;
```

## Common Mistakes
- Using `LAST_VALUE` without `IGNORE NULLS` — Presto returns NULL for the entire partition when a NULL exists.
- Stitching before deduplication; bots with the same `user_id` will inflate cross-device counts.
- Partitioning by `user_id` AND `device_id` (defeats the stitching).
- Picking too-long a TTL — a login from a year ago shouldn't propagate.

## AI Use Cases
- Cross-device ad attribution: an ad impression on mobile and a conversion on desktop count as one journey.
- Frequency capping: limit impressions per REAL user, not per device.
- Identity resolution feature: a real-user graph powers many downstream models (recsys, ads, safety).
