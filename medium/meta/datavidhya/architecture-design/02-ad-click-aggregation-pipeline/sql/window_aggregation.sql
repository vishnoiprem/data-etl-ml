-- Multi-grain aggregation + the Super Bowl hot key.
--
-- TUMBLING, not sliding. The problem says "sliding windows" but sliding windows
-- OVERLAP, so every click lands in N windows and the buckets no longer sum to
-- the total -- summing them inflates spend by exactly N.
-- pyspark/windowed_aggregation.py asserts a 5m/1m sliding window totals 5x.
--   billing  -> TUMBLING (disjoint, each click in exactly one bucket per grain)
--   trendline -> sliding is fine, as long as nobody SUMs it

-- ============================================ 1) the hot-key problem
-- One campaign at 10x volume hashes to ONE partition. That worker is the
-- bottleneck while the others idle.
--
--   SELECT campaign_id, COUNT(*) FROM deduped_clicks GROUP BY campaign_id;
--   -- c_superbowl   5,000,000    <- one task
--   -- c_other_a       500,000
--
-- "Add more partitions" does NOT fix this: the hot key still maps to one.

-- ============================================ 2) two-stage salted aggregation
-- Stage 1: aggregate on (campaign_id, salt) -> up to 64x parallelism
-- Stage 2: sum the partials -> identical answer
--
-- Salt on EVENT_ID, never on a business key. event_id is unique per event so it
-- spreads uniformly; salting on user_id inherits user skew and re-creates the
-- hot spot inside the salted key (224x imbalance on power-user traffic --
-- asserted in pyspark/windowed_aggregation.py).
WITH stage1 AS (
    SELECT
        advertiser_id,
        campaign_id,
        ad_id,
        PMOD(HASH(event_id), 64)                  AS salt,
        WINDOW(event_ts, '1 minute').start        AS window_start,
        WINDOW(event_ts, '1 minute').end          AS window_end,
        COUNT(*)                                  AS partial_clicks,
        SUM(cpc_usd)                              AS partial_spend
    FROM ads.deduped_clicks
    WHERE event_date = DATE '2026-02-08'
    GROUP BY advertiser_id, campaign_id, ad_id,
             PMOD(HASH(event_id), 64),
             WINDOW(event_ts, '1 minute')
)
SELECT
    window_start,
    window_end,
    advertiser_id,
    campaign_id,
    ad_id,
    SUM(partial_clicks)                AS clicks,
    SUM(partial_spend)                 AS spend_usd,
    TRUE                               AS is_provisional,  -- tier 2 pending
    CURRENT_TIMESTAMP()                AS updated_at
FROM stage1
GROUP BY window_start, window_end, advertiser_id, campaign_id, ad_id;

-- ============================================ 3) CTR needs both event types
-- Impressions and clicks live in the same raw table, so CTR is a conditional
-- aggregate -- not a join, which would fan out.
SELECT
    WINDOW(event_ts, '1 hour').start AS window_start,
    campaign_id,
    COUNT(CASE WHEN event_type = 'impression' THEN 1 END) AS impressions,
    COUNT(CASE WHEN event_type = 'click'      THEN 1 END) AS clicks,
    COUNT(CASE WHEN event_type = 'conversion' THEN 1 END) AS conversions,
    -- guard the denominator: an ad with 0 impressions has UNDEFINED CTR, not 0
    ROUND(100.0 * COUNT(CASE WHEN event_type = 'click' THEN 1 END)
          / NULLIF(COUNT(CASE WHEN event_type = 'impression' THEN 1 END), 0), 4)
        AS ctr_pct
FROM ads.raw_events
WHERE event_date = DATE '2026-02-08'
  AND tier1_verdict = 'accept'
GROUP BY campaign_id, WINDOW(event_ts, '1 hour');

-- NOTE: COUNT(event_type = 'click') would count EVERY row -- `false` is not
-- NULL. Use COUNT(CASE WHEN ...) or SUM(CASE WHEN ... THEN 1 ELSE 0 END).

-- ============================================ 4) the rollup (retention)
-- 1-min grain for 90 days is ~1.3 TRILLION rows. Roll up instead:
--   agg_1min  ->  7 days
--   agg_1hour -> 90 days   <- built FROM agg_1min, not from raw
--   agg_1day  ->  2 years
INSERT OVERWRITE ads.agg_1hour
SELECT
    DATE_TRUNC('HOUR', window_start)              AS window_start,
    DATE_TRUNC('HOUR', window_start) + INTERVAL 1 HOUR AS window_end,
    advertiser_id, campaign_id, ad_id,
    SUM(impressions) AS impressions,
    SUM(clicks)      AS clicks,
    SUM(conversions) AS conversions,
    SUM(spend_usd)   AS spend_usd,
    ROUND(100.0 * SUM(clicks) / NULLIF(SUM(impressions), 0), 4) AS ctr,
    MAX(is_provisional) AS is_provisional,   -- provisional if ANY minute is
    CURRENT_TIMESTAMP() AS updated_at
FROM ads.agg_1min
WHERE DATE(window_start) = DATE '2026-02-08'
GROUP BY DATE_TRUNC('HOUR', window_start), advertiser_id, campaign_id, ad_id;

-- Rolling up FROM agg_1min (not from raw) is deliberate: it guarantees the
-- grains reconcile by construction. Computing each grain independently from
-- raw invites them to disagree after a late-arriving backfill.

-- ============================================ 5) the reconciliation check
-- Every grain must total identically. Non-zero result = blocking failure.
-- SELECT
--     (SELECT SUM(clicks) FROM ads.agg_1min  WHERE DATE(window_start) = '2026-02-08')
--   - (SELECT SUM(clicks) FROM ads.agg_1hour WHERE DATE(window_start) = '2026-02-08')
--     AS should_be_zero;
