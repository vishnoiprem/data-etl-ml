-- =====================================================================
-- Metric Aggregation Pipeline (batch / hourly)
--
-- Reads:   events (silver layer)
-- Writes:  user_metric_daily
-- Pattern: explode events to (user, experiment, metric) grain
-- =====================================================================

-- Per-user-per-experiment-per-metric rollup
INSERT INTO user_metric_daily
SELECT
    e.user_id,
    e.experiment_id,
    a.variant_id,
    m.metric_id,
    CAST(e.event_ts AS DATE) AS dt,

    -- Metric value depends on metric_type
    CASE m.metric_type
        WHEN 'COUNT'      THEN COUNT(*)
        WHEN 'PROPORTION' THEN AVG(
                                 CAST(e.properties[m.event_field] AS DOUBLE)
                             )
        WHEN 'MEAN'       THEN AVG(
                                 CAST(e.properties[m.event_field] AS DOUBLE)
                             )
        WHEN 'RATIO'      THEN
                             SUM(CAST(e.properties[m.num_field]  AS DOUBLE))
                           / NULLIF(SUM(CAST(e.properties[m.denom_field] AS DOUBLE)), 0)
        ELSE NULL
    END AS value,

    -- Pre-experiment value for CUPED (last 7 days before assignment)
    NULL AS pre_value  -- filled by a separate backfill job
FROM events e
JOIN experiment_assignments a
  ON e.user_id = a.user_id
 AND e.experiment_id = a.experiment_id
JOIN metric_definitions m
  ON e.event_name = COALESCE(m.numerator_event, e.event_name)
WHERE CAST(e.event_ts AS DATE) = DATE '2026-09-26'
GROUP BY
    e.user_id, e.experiment_id, a.variant_id, m.metric_id,
    CAST(e.event_ts AS DATE),
    m.metric_type, m.event_field, m.num_field, m.denom_field;
