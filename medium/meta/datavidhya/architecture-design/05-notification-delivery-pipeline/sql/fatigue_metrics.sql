-- =====================================================================
-- Fatigue metrics
-- =====================================================================

-- 1) Daily fatigue score distribution
SELECT
    dt,
    fatigue_tier,
    COUNT(*) AS users
FROM user_fatigue_daily
WHERE dt >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY dt, fatigue_tier
ORDER BY dt DESC, fatigue_tier;

-- 2) Users at risk of unsubscribing (top 1% by fatigue score)
SELECT
    user_id,
    dt,
    notifs_sent_24h,
    notifs_sent_7d,
    open_rate_7d,
    fatigue_score,
    fatigue_tier
FROM user_fatigue_daily
WHERE dt = CURRENT_DATE - 1
  AND fatigue_tier IN ('warn', 'critical')
ORDER BY fatigue_score DESC
LIMIT 1000;

-- 3) Aggregate fatigue impact on engagement (did fatigue score predict engagement drop?)
WITH cohort AS (
    SELECT
        fatigue_tier,
        AVG(CASE WHEN open_rate_7d < 0.10 THEN 1.0 ELSE 0.0 END) AS low_engagement_pct,
        AVG(open_rate_7d) AS avg_open_rate
    FROM user_fatigue_daily
    WHERE dt = CURRENT_DATE - 1
    GROUP BY fatigue_tier
)
SELECT * FROM cohort;
