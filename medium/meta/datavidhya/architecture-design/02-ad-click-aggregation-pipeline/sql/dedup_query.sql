-- Dedup: "same user + same ad within 60 seconds = 1 click"
--
-- Two forms. Both are needed, and they must agree:
--   A) STREAMING  -- what Flink/Spark Structured Streaming runs continuously
--   B) BATCH      -- what the reconciliation job re-runs over the raw log
--
-- If A and B disagree, the dashboard and the invoice diverge for reasons that
-- have nothing to do with fraud, which is the worst kind of bug to debug.
-- pyspark/dedup_clicks.py asserts they agree.

-- ============================================================ A) STREAMING
-- Spark Structured Streaming, 3.5+. The watermark is what bounds the state.
--
--   spark.readStream.format("kafka").load()
--        .withWatermark("event_ts", "60 seconds")
--        .dropDuplicatesWithinWatermark(["user_id", "ad_id"])
--
-- Flink SQL equivalent:
--
--   SELECT * FROM (
--       SELECT *, ROW_NUMBER() OVER (
--                     PARTITION BY user_id, ad_id, window_start
--                     ORDER BY event_ts) AS rn
--       FROM TABLE(TUMBLE(TABLE raw_clicks, DESCRIPTOR(event_ts), INTERVAL '60' SECOND))
--   ) WHERE rn = 1;
--
-- DO NOT use plain dropDuplicates() on a stream: state is unbounded and the job
-- OOMs. Over a year of clicks that is ~21 TiB of state
-- (see python/capacity_model.py).

-- ============================================================ B) BATCH
-- Windows are FIXED-FROM-FIRST: the window opens at a key's first click and
-- closes 60s later. Clicks inside it are one logical click.
--
-- The alternative (sliding-from-last, where each click extends the window) is
-- a real bug: a bot clicking every 59s is deduped forever and billed once,
-- ever. See python/dedup_state.py, which asserts both.
WITH anchored AS (
    SELECT
        event_id, user_id, ad_id, campaign_id, advertiser_id,
        event_ts, cpc_usd,
        MIN(event_ts) OVER (PARTITION BY user_id, ad_id) AS first_click_ts
    FROM ads.raw_events
    WHERE event_type = 'click'
      AND tier1_verdict = 'accept'          -- tier-1 fraud already excluded
      AND event_date = DATE '2026-02-08'    -- partition pruning
),
windowed AS (
    SELECT
        *,
        -- window ordinal: clicks sharing one are the same logical click
        CAST(FLOOR(
            (UNIX_TIMESTAMP(event_ts) - UNIX_TIMESTAMP(first_click_ts)) / 60
        ) AS INT) AS dedup_window
    FROM anchored
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY user_id, ad_id, dedup_window
            -- event_id as tiebreak so a REPLAY keeps the same survivor.
            -- Without it, two clicks on the same millisecond make the billed
            -- event_id non-deterministic and the ledger unreproducible.
            ORDER BY event_ts, event_id
        ) AS rn
    FROM windowed
)
SELECT
    event_id, user_id, ad_id, campaign_id, advertiser_id, event_ts, cpc_usd
FROM ranked
WHERE rn = 1;

-- ============================================================ the audit side
-- The duplicates are WRITTEN OUT, not discarded. billable + duplicates must
-- equal raw, or speed/batch reconciliation can never balance.
--
-- INSERT INTO ads.rejected_events
-- SELECT event_id, 'duplicate', CURRENT_TIMESTAMP(), DATE(event_ts)
-- FROM ranked WHERE rn > 1;

-- ============================================================ the QA check
-- Run this after every dedup batch. A non-empty result is a blocking failure.
-- SELECT user_id, ad_id, dedup_window, COUNT(*)
-- FROM deduped_clicks
-- GROUP BY user_id, ad_id, dedup_window
-- HAVING COUNT(*) > 1;
