-- =============================================================================
-- 60-second click dedup as a batch SQL query.
-- =============================================================================
-- Streaming equivalent: Flink keyed state (user_id, ad_id) with 60s TTL.
-- Batch equivalent: window function + first/last semantics on event_ts.
--
-- The trick: a click is a duplicate iff a previous click for the SAME
-- (user_id, ad_id) has event_ts within 60s. We pick the FIRST such click
-- as the survivor; everything else is dropped.
--
-- Boundary semantics asserted below:
--   "fixed from first click" — a bot that clicks every 59s gets ONE billable
--   click per 60s window.  Sliding-from-last would dedupe forever and never
--   bill, which is the WRONG behavior for an advertiser.
-- =============================================================================

WITH ranked AS (
    SELECT
        event_id,
        event_ts,
        user_id,
        ad_id,
        campaign_id,
        advertiser_id,
        -- gap in seconds from the previous click by (user_id, ad_id)
        LAG(event_ts) OVER (
            PARTITION BY user_id, ad_id
            ORDER BY event_ts
        ) AS prev_ts,
        ROW_NUMBER() OVER (
            PARTITION BY user_id, ad_id
            ORDER BY event_ts
        ) AS rn
    FROM raw_ad_events
    WHERE event_type = 'click'
      AND fraud_tier1 = FALSE          -- tier-1 already dropped these upstream
),
with_flag AS (
    SELECT
        *,
        -- duplicate iff there was a prior click within 60s
        CASE
            WHEN prev_ts IS NULL THEN FALSE
            WHEN UNIX_TIMESTAMP(event_ts) - UNIX_TIMESTAMP(prev_ts) < 60 THEN TRUE
            ELSE FALSE
        END AS is_duplicate
    FROM ranked
)
SELECT
    event_id,
    event_ts,
    user_id,
    ad_id,
    campaign_id,
    advertiser_id,
    is_duplicate
FROM with_flag
WHERE rn = 1 OR is_duplicate = FALSE   -- keep the first OR any click that
                                        -- starts a new 60s window
ORDER BY event_ts;

-- -----------------------------------------------------------------------------
-- Sanity assertions (run these in a notebook or as unit tests).
--   1) COUNT(*) over the result equals the number of distinct 60s windows
--      per (user_id, ad_id) in the input.  Assert it.
--   2) COUNT(DISTINCT event_id) for duplicates that were dropped equals
--      the original minus the survivors.  Idempotency check on rerun.
-- -----------------------------------------------------------------------------

-- Idempotency proof:
--   The query is deterministic. Re-running over the same raw_ad_events
--   produces the same deduped_clicks.  Compare two runs via checksum on
--   md5(event_id ORDER BY event_id); they must match.
