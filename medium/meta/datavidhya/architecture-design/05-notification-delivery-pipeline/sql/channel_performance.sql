-- =====================================================================
-- Channel performance & A/B test winners
-- =====================================================================

-- 1) Channel mix performance over time
SELECT
    DATE_TRUNC('hour', sent_ts) AS hour,
    channel,
    notification_type,
    COUNT(*) AS sent,
    AVG(CASE WHEN delivered_ts IS NOT NULL THEN 1.0 ELSE 0.0 END) AS delivery_rate,
    AVG(CASE WHEN opened_ts IS NOT NULL THEN 1.0 ELSE 0.0 END) AS open_rate
FROM notification_facts
WHERE sent_ts >= CURRENT_DATE - INTERVAL '1' DAY
GROUP BY DATE_TRUNC('hour', sent_ts), channel, notification_type
ORDER BY hour DESC, channel;

-- 2) A/B test variant performance — uses experiment_results from Problem 1
SELECT
    nf.variant_id,
    nf.notification_type,
    nf.channel,
    COUNT(*) AS n,
    AVG(CASE WHEN nf.opened_ts IS NOT NULL THEN 1.0 ELSE 0.0 END) AS open_rate,
    AVG(CASE WHEN nf.clicked_ts IS NOT NULL THEN 1.0 ELSE 0.0 END) AS ctr,
    AVG(CASE WHEN nf.converted_ts IS NOT NULL THEN 1.0 ELSE 0.0 END) AS conversion_rate
FROM notification_facts nf
WHERE nf.sent_ts >= CURRENT_DATE - INTERVAL '14' DAY
  AND nf.variant_id IS NOT NULL
GROUP BY nf.variant_id, nf.notification_type, nf.channel
ORDER BY nf.notification_type, nf.channel, conversion_rate DESC;
