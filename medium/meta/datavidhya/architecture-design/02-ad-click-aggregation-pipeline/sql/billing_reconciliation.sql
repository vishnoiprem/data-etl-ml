-- Billing reconciliation — the AUTHORITATIVE path.
--
-- Runs T+1, after tier-2 fraud verdicts have landed. This is the query whose
-- output becomes an invoice, so every line of it is defensible in an audit.
--
--   billable = raw - tier1_rejected - duplicates - tier2_invalidated
--
-- computed as a JOIN over an IMMUTABLE log. Nothing is deleted, ever.
-- pyspark/billing_reconciliation.py asserts every property below.

-- ============================================ 1) the billable set
WITH raw_clicks AS (
    SELECT event_id, advertiser_id, campaign_id, ad_id, user_id,
           event_ts, cpc_usd, tier1_verdict
    FROM ads.raw_events
    WHERE event_type = 'click'
      AND event_date = DATE '2026-02-08'
),
-- tier 1 was decided at the edge, in microseconds
tier1_passed AS (
    SELECT * FROM raw_clicks WHERE tier1_verdict = 'accept'
),
-- dedup: fixed-from-first 60s windows (see sql/dedup_query.sql)
deduped AS (
    SELECT * FROM (
        SELECT t.*,
               ROW_NUMBER() OVER (
                   PARTITION BY user_id, ad_id,
                       CAST(FLOOR((UNIX_TIMESTAMP(event_ts) - UNIX_TIMESTAMP(
                           MIN(event_ts) OVER (PARTITION BY user_id, ad_id)
                       )) / 60) AS INT)
                   ORDER BY event_ts, event_id
               ) AS rn
        FROM tier1_passed t
    ) WHERE rn = 1
),
-- tier 2 arrives HOURS later. LEFT ANTI JOIN, not DELETE.
billable AS (
    SELECT d.*
    FROM deduped d
    LEFT ANTI JOIN ads.fraud_verdicts v
        ON v.event_id = d.event_id
       AND v.verdict = 'invalid'
       AND v.event_date = DATE '2026-02-08'
)

-- ============================================ 2) the ledger row
SELECT
    CONCAT(campaign_id, '|', CAST(DATE '2026-02-08' AS STRING)) AS ledger_id,
    advertiser_id,
    campaign_id,
    DATE '2026-02-08'                                AS billing_date,
    COUNT(*)                                         AS billable_clicks,
    ROUND(SUM(cpc_usd), 4)                           AS billable_spend,
    -- the exclusions go ON the invoice. Advertisers trust a number that shows
    -- its work far more than a smaller number with no explanation.
    (SELECT COUNT(*) FROM raw_clicks WHERE tier1_verdict <> 'accept')
                                                     AS excluded_tier1,
    (SELECT COUNT(*) FROM ads.fraud_verdicts
      WHERE verdict = 'invalid' AND event_date = DATE '2026-02-08')
                                                     AS excluded_tier2,
    (SELECT COUNT(*) FROM tier1_passed) - (SELECT COUNT(*) FROM deduped)
                                                     AS excluded_dupes,
    (SELECT COUNT(*) FROM raw_clicks)                AS raw_click_count,
    'original'                                       AS entry_type,
    CAST(NULL AS STRING)                             AS supersedes_id,
    (SELECT MAX(model_version) FROM ads.fraud_verdicts
      WHERE event_date = DATE '2026-02-08')          AS model_version,
    CURRENT_TIMESTAMP()                              AS computed_at
FROM billable
GROUP BY advertiser_id, campaign_id;

-- ============================================ 3) IDEMPOTENT write
-- At-least-once delivery means this job WILL re-run a day. With INSERT the
-- advertiser is billed twice; with MERGE the replay is a no-op.
-- pyspark/billing_reconciliation.py asserts a replay doubles an append sink
-- and leaves a merge sink unchanged, for any number of retries.
--
-- MERGE INTO ads.billing_ledger t
--   USING staged_ledger s
--      ON  t.campaign_id  = s.campaign_id
--      AND t.billing_date = s.billing_date
--      AND t.entry_type   = 'original'        -- the IDEMPOTENCY KEY
-- WHEN MATCHED     THEN UPDATE SET *
-- WHEN NOT MATCHED THEN INSERT *;

-- ============================================ 4) the adjustment record
-- The speed layer already showed a bigger number. We do NOT rewrite it --
-- we publish the delta.
SELECT
    s.campaign_id,
    s.window_start,
    SUM(s.clicks)                             AS provisional_clicks,
    MAX(b.billable_clicks)                    AS billable_clicks,
    SUM(s.clicks) - MAX(b.billable_clicks)    AS invalidated_clicks,
    ROUND(MAX(b.billable_spend) - SUM(s.spend_usd), 4) AS adjustment_usd,
    'adjustment'                              AS entry_type
FROM ads.agg_1hour s
JOIN ads.billing_ledger b
  ON  b.campaign_id  = s.campaign_id
  AND b.billing_date = DATE(s.window_start)
WHERE DATE(s.window_start) = DATE '2026-02-08'
GROUP BY s.campaign_id, s.window_start;

-- ============================================ 5) CONSERVATION (blocking QA)
-- Every raw click must land in exactly one bucket. A non-zero result means the
-- ledger is not auditable and billing must be HELD, not published.
SELECT
    raw_click_count
  - billable_clicks - excluded_tier1 - excluded_tier2 - excluded_dupes
        AS should_be_zero
FROM ads.billing_ledger
WHERE billing_date = DATE '2026-02-08' AND entry_type = 'original';

-- ============================================ 6) the dispute query
-- What you run when an advertiser asks "why $375 and not $435?". Only possible
-- because raw_events is immutable and verdicts are a separate table.
SELECT
    CASE WHEN r.tier1_verdict <> 'accept'        THEN 'tier1_' || r.tier1_verdict
         WHEN v.verdict = 'invalid'              THEN 'tier2_' || v.reason
         ELSE 'billable' END                     AS disposition,
    COUNT(*)                                     AS clicks,
    ROUND(SUM(r.cpc_usd), 2)                     AS usd,
    MAX(v.model_version)                         AS invalidated_by
FROM ads.raw_events r
LEFT JOIN ads.fraud_verdicts v
       ON v.event_id = r.event_id AND v.event_date = r.event_date
WHERE r.event_type = 'click'
  AND r.event_date = DATE '2026-02-08'
  AND r.campaign_id = 'c_superbowl'
GROUP BY 1
ORDER BY clicks DESC;

-- ============================================ 7) held-invoice guard
-- If the tier-2 scorer is lagging, DO NOT BILL. A day of delayed invoicing
-- costs far less than a day of billing fraud:
-- 1B clicks/day x 15% x $0.50 = $75M/day of exposure.
SELECT
    CASE WHEN MAX(scored_at) < CURRENT_TIMESTAMP() - INTERVAL 6 HOURS
         THEN 'HOLD_BILLING'
         ELSE 'OK_TO_BILL' END AS gate,
    MAX(scored_at)             AS latest_verdict
FROM ads.fraud_verdicts
WHERE event_date = DATE '2026-02-08';
