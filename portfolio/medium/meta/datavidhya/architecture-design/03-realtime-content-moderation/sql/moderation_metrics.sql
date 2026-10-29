-- =====================================================================
-- Moderation Metrics Dashboards
-- =====================================================================

-- 1) Per-class precision / recall (using human labels as ground truth)
WITH human_labels AS (
    SELECT content_id, decision AS human_decision
    FROM human_review_actions
    WHERE decided_ts >= CURRENT_DATE - INTERVAL '7' DAY
),
auto_decisions AS (
    SELECT content_id, decision, severity_class
    FROM moderation_decisions
    WHERE decided_ts >= CURRENT_DATE - INTERVAL '7' DAY
      AND decision = 'AUTO_REMOVE'      -- only auto-decisions
),
combined AS (
    SELECT
        a.severity_class,
        COUNT(*) AS total_auto_remove,
        SUM(CASE WHEN h.human_decision = 'REMOVE' THEN 1 ELSE 0 END) AS true_positives,
        SUM(CASE WHEN h.human_decision IN ('APPROVE','ESCALATE') THEN 1 ELSE 0 END) AS false_positives
    FROM auto_decisions a
    LEFT JOIN human_labels h USING (content_id)
    GROUP BY a.severity_class
)
SELECT
    severity_class,
    total_auto_remove,
    true_positives,
    false_positives,
    ROUND(100.0 * true_positives / NULLIF(total_auto_remove, 0), 2) AS precision_pct
FROM combined
ORDER BY severity_class;

-- 2) Reviewer SLA compliance
SELECT
    priority,
    COUNT(*) AS items,
    SUM(CASE WHEN decided_ts <= sla_deadline_ts THEN 1 ELSE 0 END) AS within_sla,
    ROUND(100.0 * SUM(CASE WHEN decided_ts <= sla_deadline_ts THEN 1 ELSE 0 END) / COUNT(*), 2) AS sla_pct,
    AVG(TIMESTAMPDIFF(MINUTE, enqueued_ts, decided_ts)) AS avg_review_min
FROM review_queue q
JOIN human_review_actions h USING (queue_id)
WHERE q.enqueued_ts >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY priority
ORDER BY priority;

-- 3) Appeal overturn rate (a proxy for FP rate on auto-removals)
SELECT
    DATE_TRUNC('day', a.decided_ts) AS day,
    COUNT(*) AS appeals,
    SUM(CASE WHEN a.status = 'DECIDED' AND h.decision = 'APPROVE' THEN 1 ELSE 0 END) AS overturned,
    ROUND(100.0 * SUM(CASE WHEN a.status = 'DECIDED' AND h.decision = 'APPROVE' THEN 1 ELSE 0 END) / COUNT(*), 2)
        AS overturn_pct
FROM appeals a
JOIN human_review_actions h USING (content_id)
WHERE a.decided_ts >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY DATE_TRUNC('day', a.decided_ts)
ORDER BY day DESC;
