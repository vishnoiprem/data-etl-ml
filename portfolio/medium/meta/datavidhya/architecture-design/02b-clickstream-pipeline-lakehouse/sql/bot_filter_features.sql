-- =====================================================================
-- Bot filtering analytics — keep tabs on what's getting blocked
-- =====================================================================

-- 1) Bot funnel breakdown
SELECT
    event_date,
    ingest_status,
    COUNT(*) AS event_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY event_date), 2) AS pct
FROM lakehouse.bronze_events
WHERE event_date >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY event_date, ingest_status
ORDER BY event_date DESC, event_count DESC;

-- 2) Top bot user-agents
SELECT
    user_agent,
    COUNT(DISTINCT user_id) AS bot_users,
    COUNT(*)                AS bot_events
FROM lakehouse.bronze_events
WHERE event_date >= CURRENT_DATE - INTERVAL '1' DAY
  AND ingest_status LIKE 'BOT_%'
  AND user_agent IS NOT NULL
GROUP BY user_agent
ORDER BY bot_events DESC
LIMIT 20;

-- 3) Per-user events/second — suspicious rate
SELECT
    user_id,
    event_date,
    COUNT(*)              AS events_today,
    MAX(events_per_sec)   AS peak_eps
FROM (
    SELECT
        user_id,
        CAST(event_ts AS DATE) AS event_date,
        event_ts,
        -- 5-second window events/sec
        COUNT(*) OVER (
            PARTITION BY user_id
            ORDER BY event_ts
            RANGE BETWEEN INTERVAL '5' SECOND PRECEDING AND CURRENT ROW
        ) / 5.0 AS events_per_sec
    FROM lakehouse.silver_events
    WHERE event_date = CURRENT_DATE - 1
) t
GROUP BY user_id, event_date
HAVING events_today > 100 AND peak_eps > 5
ORDER BY peak_eps DESC
LIMIT 50;
