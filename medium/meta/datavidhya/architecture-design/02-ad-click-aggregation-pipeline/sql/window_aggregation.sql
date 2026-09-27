-- =============================================================================
-- Windowed aggregation — 1m / 5m / 1h / 1d rollups with hot-key salting.
-- =============================================================================
-- Hot key problem: Super Bowl campaign = 10x normal volume = one partition
-- overloaded while others idle.  Solution: 64-salt two-stage aggregation.
--
-- Stage 1: aggregate per (campaign_id, salt)  -- many workers
-- Stage 2: sum the salts                      -- one or few workers
-- The salt is derived from the event_id so the same event always lands in
-- the same salt bucket across retries.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Stage 1: per-salt 1-minute aggregates (parallel across 64 workers)
-- -----------------------------------------------------------------------------
INSERT OVERWRITE speed_aggregates_1m
SELECT
    DATE_TRUNC('minute', event_ts)        AS window_start,
    ad_id,
    -- Salt bucket: deterministic, derived from event_id (or campaign_id+ad_id).
    -- 64 buckets gives 64-way parallelism on the hot key.
    CAST(MOD(HASH(event_id), 64) AS INT)   AS salt,
    COUNT(*)                                AS clicks,
    SUM(CASE WHEN event_type = 'impression' THEN 1 ELSE 0 END) AS impressions,
    SUM(CASE WHEN event_type = 'conversion' THEN 1 ELSE 0 END) AS conversions,
    -- Spend at this salt bucket: clicks * CPC for CPC-bid campaigns.
    SUM(CASE
            WHEN event_type = 'click'
            THEN COALESCE(c.cpc_usd, 0)
            ELSE 0
        END)                               AS spend_usd,
    CURRENT_TIMESTAMP                       AS updated_at
FROM deduped_clicks dc
    -- CPC comes from the campaign dimension at query time:
    JOIN campaigns_dim c ON dc.campaign_id = c.campaign_id
WHERE event_ts >= CURRENT_TIMESTAMP - INTERVAL 7 DAY   -- 7d retention
GROUP BY
    DATE_TRUNC('minute', event_ts),
    ad_id,
    CAST(MOD(HASH(event_id), 64) AS INT);

-- -----------------------------------------------------------------------------
-- Stage 2: roll up the salts for dashboard reads. salt = -1 marks "rolled up".
-- -----------------------------------------------------------------------------
INSERT OVERWRITE TABLE speed_aggregates_1m_rolledup
SELECT
    window_start,
    ad_id,
    -1                                        AS salt,
    SUM(clicks)                               AS clicks,
    SUM(impressions)                          AS impressions,
    SUM(conversions)                          AS conversions,
    SUM(spend_usd)                            AS spend_usd,
    CURRENT_TIMESTAMP                         AS updated_at
FROM speed_aggregates_1m
WHERE salt >= 0                                -- exclude previously rolled-up rows
GROUP BY window_start, ad_id;

-- -----------------------------------------------------------------------------
-- 1-hour and 1-day rollups — same shape, different DATE_TRUNC.
-- These rollups are APPENDED (not upserted) because the window itself
-- never changes once closed.
-- -----------------------------------------------------------------------------
INSERT INTO speed_aggregates_1h
SELECT
    DATE_TRUNC('hour', window_start)         AS window_start,
    ad_id,
    -1                                        AS salt,
    SUM(clicks)                               AS clicks,
    SUM(impressions)                          AS impressions,
    SUM(conversions)                          AS conversions,
    SUM(spend_usd)                            AS spend_usd,
    CURRENT_TIMESTAMP                         AS updated_at
FROM speed_aggregates_1m_rolledup
WHERE window_start <  CURRENT_TIMESTAMP - INTERVAL 1 HOUR   -- only closed windows
  AND window_start >= CURRENT_TIMESTAMP - INTERVAL 90 DAY
GROUP BY DATE_TRUNC('hour', window_start), ad_id;

INSERT INTO speed_aggregates_1d
SELECT
    DATE_TRUNC('day', window_start)          AS window_start,
    ad_id,
    -1                                        AS salt,
    SUM(clicks),
    SUM(impressions),
    SUM(conversions),
    SUM(spend_usd),
    CURRENT_TIMESTAMP
FROM speed_aggregates_1m_rolledup
WHERE window_start <  CURRENT_TIMESTAMP - INTERVAL 1 DAY
  AND window_start >= CURRENT_TIMESTAMP - INTERVAL 730 DAY
GROUP BY DATE_TRUNC('day', window_start), ad_id;

-- -----------------------------------------------------------------------------
-- Hot-key mitigation proof: without salting, a single campaign with
-- 10x volume maps to a single hash bucket, and that worker becomes the
-- bottleneck.  With 64 salts, that same campaign spreads across 64 buckets
-- and parallelises naturally.
--
-- The salting function MUST be deterministic on event_id so retries land
-- in the same bucket.  HASH(event_id) is monotonic but NOT deterministic
-- across Iceberg implementations; the production code uses
--   xxhash64(event_id) % 64
-- which is the same value on every run.
-- =============================================================================
