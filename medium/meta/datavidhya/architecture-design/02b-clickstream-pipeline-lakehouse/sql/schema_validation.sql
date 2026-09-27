-- =====================================================================
-- Schema validation queries
-- =====================================================================

-- 1) Required-field null counts (monitoring)
SELECT
    event_date,
    SUM(CASE WHEN event_id IS NULL THEN 1 ELSE 0 END) AS null_event_id,
    SUM(CASE WHEN user_id  IS NULL THEN 1 ELSE 0 END) AS null_user_id,
    SUM(CASE WHEN event_ts IS NULL THEN 1 ELSE 0 END) AS null_event_ts,
    SUM(CASE WHEN event_name IS NULL OR event_name = '' THEN 1 ELSE 0 END) AS blank_event_name,
    COUNT(*) AS total_rows,
    100.0 * SUM(CASE WHEN event_id IS NULL OR user_id IS NULL
                       OR event_ts IS NULL OR event_name IS NULL OR event_name = ''
                     THEN 1 ELSE 0 END) / COUNT(*) AS reject_pct
FROM lakehouse.bronze_events
WHERE event_date >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY event_date
ORDER BY event_date DESC;

-- 2) Unknown event names → quarantine candidates
SELECT
    event_name,
    COUNT(*) AS occurrences
FROM lakehouse.bronze_events
WHERE event_date >= CURRENT_DATE - INTERVAL '1' DAY
  AND event_name NOT IN (
    'page_view','click','scroll','form_submit','purchase',
    'signup','login','logout','share','comment','like','search'
  )
GROUP BY event_name
ORDER BY occurrences DESC
LIMIT 50;

-- 3) Schema drift — new keys in properties map
WITH exploded AS (
    SELECT event_date, k.key
    FROM lakehouse.silver_events
    LATERAL VIEW EXPLODE(properties) k AS key
    WHERE event_date >= CURRENT_DATE - INTERVAL '7' DAY
)
SELECT key, COUNT(DISTINCT event_date) AS days_seen
FROM exploded
GROUP BY key
ORDER BY days_seen DESC
LIMIT 100;
