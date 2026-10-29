-- =====================================================================
-- Attribution queries
-- =====================================================================

-- 1) Per-channel funnel for last 7 days
SELECT
    channel,
    notification_type,
    COUNT(DISTINCT notification_id)             AS sent,
    COUNT(DISTINCT CASE WHEN delivered_ts IS NOT NULL THEN notification_id END) AS delivered,
    COUNT(DISTINCT CASE WHEN opened_ts IS NOT NULL THEN notification_id END)    AS opened,
    COUNT(DISTINCT CASE WHEN clicked_ts IS NOT NULL THEN notification_id END)   AS clicked,
    COUNT(DISTINCT CASE WHEN converted_ts IS NOT NULL THEN notification_id END) AS converted,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN delivered_ts IS NOT NULL THEN notification_id END)
               / NULLIF(COUNT(DISTINCT notification_id), 0), 2) AS delivery_rate,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN opened_ts IS NOT NULL THEN notification_id END)
               / NULLIF(COUNT(DISTINCT CASE WHEN delivered_ts IS NOT NULL THEN notification_id END), 0), 2)
        AS open_rate,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN clicked_ts IS NOT NULL THEN notification_id END)
               / NULLIF(COUNT(DISTINCT CASE WHEN opened_ts IS NOT NULL THEN notification_id END), 0), 2)
        AS ctr
FROM notification_facts
WHERE sent_ts >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY channel, notification_type
ORDER BY channel, notification_type;

-- 2) Attribution breakdown — how often push → app open vs email → click
WITH attributed AS (
    SELECT
        channel,
        notification_type,
        SUM(CASE WHEN attributed_open  THEN 1 ELSE 0 END) AS attributed_opens,
        SUM(CASE WHEN attributed_click THEN 1 ELSE 0 END) AS attributed_clicks,
        SUM(CASE WHEN attributed_convert THEN 1 ELSE 0 END) AS attributed_converts
    FROM notification_facts
    WHERE sent_ts >= CURRENT_DATE - INTERVAL '7' DAY
    GROUP BY channel, notification_type
)
SELECT * FROM attributed;

-- 3) Attribution window distribution (do opens happen at +5min or +25min?)
SELECT
    FLOOR(EXTRACT(EPOCH FROM opened_ts - sent_ts) / 60) AS open_minute_bucket,
    COUNT(*) AS n_opens
FROM notification_facts
WHERE sent_ts >= CURRENT_DATE - INTERVAL '7' DAY
  AND attributed_open = TRUE
GROUP BY FLOOR(EXTRACT(EPOCH FROM opened_ts - sent_ts) / 60)
ORDER BY open_minute_bucket
LIMIT 30;
