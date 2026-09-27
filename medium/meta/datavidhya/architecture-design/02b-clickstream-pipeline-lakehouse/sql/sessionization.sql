-- =====================================================================
-- Sessionization — group events into sessions (30-min inactivity gap)
-- Window function with cumulative count of "new session" markers.
-- =====================================================================

WITH events_with_gap AS (
    SELECT
        user_id,
        event_id,
        event_ts,
        event_name,
        session_id,

        -- mark start of new session if gap > 30 min OR session_id changed
        CASE
            WHEN LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts) IS NULL THEN 1
            WHEN event_ts - LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts) > INTERVAL '30' MINUTE THEN 1
            WHEN session_id IS DISTINCT FROM LAG(session_id) OVER (PARTITION BY user_id ORDER BY event_ts) THEN 1
            ELSE 0
        END AS is_new_session
    FROM lakehouse.silver_events
    WHERE dt = DATE '2026-09-26'
),
sessions AS (
    SELECT
        user_id,
        event_id,
        event_ts,
        event_name,
        -- Session number per user (running total of new-session markers)
        SUM(is_new_session) OVER (PARTITION BY user_id ORDER BY event_ts) AS session_n,
        session_id AS client_session_id
    FROM events_with_gap
),
session_agg AS (
    SELECT
        user_id,
        session_n,
        MIN(event_ts)  AS started_ts,
        MAX(event_ts)  AS ended_ts,
        COUNT(*)       AS event_count,
        SUM(CASE WHEN event_name = 'page_view' THEN 1 ELSE 0 END) AS page_views,
        SUM(CASE WHEN event_name = 'click'     THEN 1 ELSE 0 END) AS clicks,
        SUM(CASE WHEN event_name = 'purchase'  THEN 1 ELSE 0 END) AS purchases,
        MAX(CASE WHEN event_name = 'purchase' THEN 1 ELSE 0 END) AS conversion_flag,
        -- First/last page from page_view events
        MAX(CASE WHEN event_name = 'page_view' THEN properties['page'] END) AS last_page
    FROM sessions
    GROUP BY user_id, session_n
)
SELECT
    user_id,
    session_n                                  AS session_id_internal,
    CONCAT(user_id, ':', CAST(session_n AS STRING)) AS session_id,
    started_ts,
    ended_ts,
    TIMESTAMPDIFF(SECOND, started_ts, ended_ts) AS duration_s,
    page_views,
    clicks,
    purchases,
    conversion_flag,
    last_page                                  AS exit_page
FROM session_agg;
