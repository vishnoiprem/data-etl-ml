-- =============================================================================
-- Billing reconciliation — the AUTHORITATIVE billable-click query.
-- =============================================================================
-- Speed layer = provisional, revisable.
-- Batch layer = exact, after async fraud signals have settled.
--
-- billable_clicks = raw_clicks
--                - tier1_rejected (already excluded upstream of raw_events)
--                - tier2_verdicts (joined from fraud_verdicts)
--                - within 60s dedup (handled by joining deduped_clicks)
--
-- The query is idempotent: re-running over the same input produces the
-- same billing_ledger rows.  That makes at-least-once delivery safe.
-- =============================================================================

INSERT OVERWRITE billing_ledger
SELECT
    -- ledger_id: deterministic so reruns overwrite, never duplicate
    HASH(CONCAT_WS('|', advertiser_id, campaign_id, period_start)) AS ledger_id,
    advertiser_id,
    campaign_id,
    period_start,
    period_end,
    COUNT(*) AS billable_clicks,
    AVG(c.cpc_usd) AS cpc_usd,
    SUM(c.cpc_usd) AS gross_usd,
    -- adjustment_usd is filled in by the speed-vs-batch diff (see below)
    0.0 AS adjustment_usd,
    SUM(c.cpc_usd) AS net_usd,           -- equal to gross on first issuance
    CURRENT_TIMESTAMP AS issued_at
FROM (
    -- Deduped click stream, filtered to billable:
    --   - exclude tier-2 fraud verdicts (LEFT JOIN ... WHERE verdict IS NULL)
    --   - exclude any future-dated or null-ts events
    --   - only count events within the period
    SELECT
        dc.event_id,
        dc.event_ts,
        dc.user_id,
        dc.ad_id,
        dc.campaign_id,
        c.advertiser_id
    FROM deduped_clicks dc
        JOIN campaigns_dim c  ON dc.campaign_id = c.campaign_id
        LEFT JOIN fraud_verdicts fv ON dc.event_id = fv.event_id
    WHERE fv.event_id IS NULL             -- not invalidated by tier-2
      AND dc.event_ts >= TIMESTAMP '2025-01-01'   -- period_start of this run
      AND dc.event_ts <  TIMESTAMP '2025-02-01'   -- period_end  of this run
      AND dc.event_ts IS NOT NULL
) billable
    JOIN campaigns_dim c ON billable.campaign_id = c.campaign_id
    -- Period is fixed for a monthly run; here we hard-code for clarity.
    -- In production: pass via session variable.
    CROSS JOIN (SELECT DATE '2025-01-01' AS period_start,
                       DATE '2025-02-01' AS period_end) p
GROUP BY advertiser_id, campaign_id, period_start, period_end;

-- -----------------------------------------------------------------------------
-- Adjustment records — the public delta vs. the speed layer.
-- When the speed layer under-counted (tier-2 fraud invalidated clicks that
-- had already been shown as spend), we publish an adjustment row.
-- -----------------------------------------------------------------------------
INSERT INTO adjustment_records
SELECT
    HASH(CONCAT_WS('|', s.advertiser_id, s.campaign_id, s.period_start,
                   'speed_vs_batch')) AS adjustment_id,
    s.period_start,
    s.period_end,
    s.advertiser_id,
    s.campaign_id,
    -- positive = batch saw MORE billable clicks (speed under-counted)
    -- negative = batch saw FEWER (speed over-counted, typically fraud)
    b.billable_clicks - s.billable_clicks AS delta_clicks,
    (b.billable_clicks - s.billable_clicks) * s.avg_cpc AS delta_usd,
    'tier2_fraud' AS reason,
    CURRENT_TIMESTAMP AS published_at
FROM speed_aggregates_1d_rolledup_monthly s
    JOIN billing_ledger b
      ON s.advertiser_id = b.advertiser_id
     AND s.campaign_id   = b.campaign_id
     AND s.period_start  = b.period_start
WHERE b.billable_clicks != s.billable_clicks;

-- -----------------------------------------------------------------------------
-- Idempotency: the OVERWRITE on billing_ledger is keyed by deterministic
-- ledger_id.  Reruns replace, never append.  Adjustment records use
-- INSERT (append-only) but their PK is also deterministic, so duplicate
-- inserts are caught by PRIMARY KEY violation.
--
-- Compare this with an APPEND-mode sink: that double-bills on replay and
-- is the bug to call out in the interview.
-- =============================================================================
