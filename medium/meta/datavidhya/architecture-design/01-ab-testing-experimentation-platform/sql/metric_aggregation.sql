-- =====================================================================
-- Metric Aggregation Pipeline (batch / hourly)
--
-- Reads:   events (silver layer)
-- Writes:  user_metric_daily
-- Pattern: explode events to (user, experiment, metric) grain
-- =====================================================================

-- Per-user-per-experiment-per-metric rollup
-- NOTE: GROUP BY must NOT include metric_def field names (event_field, num_field,
-- denom_field); doing so produces a cross-product when multiple metric defs
-- share the same numerator_event. Group by user × exp × metric × dt only.
INSERT INTO user_metric_daily
WITH metric_events AS (
    SELECT
        e.user_id,
        e.experiment_id,
        a.variant_id,
        m.metric_id,
        m.metric_type,
        CAST(e.event_ts AS DATE) AS dt,
        -- Resolve the metric value expression up front (one per row)
        CASE m.metric_type
            WHEN 'COUNT'      THEN 1.0
            WHEN 'PROPORTION' THEN CAST(e.properties[m.event_field] AS DOUBLE)
            WHEN 'MEAN'       THEN CAST(e.properties[m.event_field] AS DOUBLE)
            WHEN 'RATIO'      THEN
                  CAST(e.properties[m.num_field]  AS DOUBLE)
                / NULLIF(CAST(e.properties[m.denom_field] AS DOUBLE), 0)
            ELSE NULL
        END AS value
    FROM events e
    JOIN experiment_assignments a
      ON e.user_id = a.user_id
     AND e.experiment_id = a.experiment_id
    JOIN metric_definitions m
      ON e.event_name = COALESCE(m.numerator_event, e.event_name)
    WHERE CAST(e.event_ts AS DATE) = DATE '2026-09-26'
)
SELECT
    user_id, experiment_id, variant_id, metric_id, dt,
    AVG(value) AS value,
    NULL       AS pre_value    -- filled by separate backfill job
FROM metric_events
GROUP BY user_id, experiment_id, variant_id, metric_id, dt;
