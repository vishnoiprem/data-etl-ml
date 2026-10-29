-- Ad Click Aggregation Pipeline — Iceberg DDL
--
-- Layer discipline, top to bottom:
--   raw_events        immutable, append-only, 1 year        <- source of truth
--   fraud_verdicts    tier-2 ML output, separate table      <- never mutates raw
--   agg_*             pre-aggregated serving tables         <- speed layer
--   billing_ledger    append-only, 7 years (legal)          <- authoritative
--
-- The single most important property: raw_events is NEVER updated or deleted.
-- Fraud is excluded by JOIN at read time, which is what makes an advertiser
-- dispute reconstructible three years later.

-- ============================================================ raw (immutable)
CREATE TABLE IF NOT EXISTS ads.raw_events (
    event_id            STRING   NOT NULL,   -- UUIDv7: time-sortable, stamped at edge
    event_type          STRING   NOT NULL,   -- impression | click | conversion
    ad_id               STRING   NOT NULL,
    campaign_id         STRING   NOT NULL,
    advertiser_id       STRING   NOT NULL,
    user_id             STRING,              -- NULL for logged-out; see Unknown member
    session_id          STRING,
    event_ts            TIMESTAMP NOT NULL,  -- CLIENT time: what the user did
    ingest_ts           TIMESTAMP NOT NULL,  -- SERVER time: what we can trust
    ms_since_impression BIGINT,              -- tier-1 fraud signal
    device_type         STRING,
    country             STRING,
    ip_hash             STRING,              -- hashed at edge; raw IP is not retained
    asn                 INT,
    user_agent_hash     STRING,
    cpc_usd             DECIMAL(10, 4),      -- bid at auction time, immutable
    tier1_verdict       STRING,              -- accept | reject:<reason>
    kafka_partition     INT,                 -- provenance, for replay debugging
    kafka_offset        BIGINT
)
USING iceberg
PARTITIONED BY (days(event_ts), hours(event_ts))
TBLPROPERTIES (
    'write.format.default'          = 'parquet',
    'write.parquet.compression-codec' = 'zstd',
    -- target ~512MB files: big enough to scan efficiently, small enough that a
    -- single-hour backfill rewrite is cheap
    'write.target-file-size-bytes'  = '536870912',
    'history.expire.max-snapshot-age-ms' = '604800000'  -- 7d of time travel
);

-- WHY TWO TIMESTAMPS: event_ts is client-supplied and therefore attacker-
-- controlled (a bot can claim any time). Window assignment uses event_ts so
-- legitimate mobile clients with clock drift are attributed correctly, but
-- tier-1 fraud compares the two and rejects implausible skew.

-- ============================================================ fraud (tier 2)
CREATE TABLE IF NOT EXISTS ads.fraud_verdicts (
    event_id      STRING    NOT NULL,
    verdict       STRING    NOT NULL,   -- invalid | suspicious | valid
    score         DOUBLE    NOT NULL,   -- 0..1 model confidence
    reason        STRING    NOT NULL,   -- coordinated_click_farm | datacenter | ...
    model_version STRING    NOT NULL,   -- so a re-score is attributable
    scored_at     TIMESTAMP NOT NULL,
    event_date    DATE      NOT NULL    -- partition key, copied from the event
)
USING iceberg
PARTITIONED BY (event_date)
TBLPROPERTIES ('write.format.default' = 'parquet');

-- model_version matters: when the model improves you re-score history, and the
-- billing ledger must be able to say WHICH model invalidated a click.

-- ============================================================ serving (speed)
-- Grain: one row per (campaign, ad, window_start). salt is present so the
-- two-stage salted aggregation can write partials before the final merge.
CREATE TABLE IF NOT EXISTS ads.agg_1min (
    window_start  TIMESTAMP NOT NULL,
    window_end    TIMESTAMP NOT NULL,
    advertiser_id STRING    NOT NULL,
    campaign_id   STRING    NOT NULL,
    ad_id         STRING    NOT NULL,
    impressions   BIGINT    NOT NULL,
    clicks        BIGINT    NOT NULL,     -- deduped, tier-1 filtered
    conversions   BIGINT    NOT NULL,
    spend_usd     DECIMAL(18, 4) NOT NULL,
    ctr           DOUBLE,                 -- clicks / impressions, NULL if 0 impr
    is_provisional BOOLEAN  NOT NULL,     -- TRUE until tier-2 reconciliation
    updated_at    TIMESTAMP NOT NULL
)
USING iceberg
PARTITIONED BY (days(window_start))
TBLPROPERTIES ('write.format.default' = 'parquet');

-- is_provisional is the column that makes the Lambda split honest. The
-- dashboard renders "provisional" when it is TRUE. Advertisers tolerate a
-- revisable number; they do not tolerate a number that silently changed.

-- Same shape at coarser grains. The ROLLUP is a retention decision:
-- 1-min for 90 days would be ~1.3 TRILLION rows (see python/capacity_model.py).
CREATE TABLE IF NOT EXISTS ads.agg_1hour LIKE ads.agg_1min USING iceberg;
CREATE TABLE IF NOT EXISTS ads.agg_1day  LIKE ads.agg_1min USING iceberg;

-- Retention, enforced by policy not by hope:
--   agg_1min   7 days   (incident debugging)
--   agg_1hour  90 days  (the stated requirement)
--   agg_1day   2 years+ (trend analysis)

-- ============================================================ billing (batch)
-- APPEND-ONLY. A correction is a new row, never an UPDATE.
CREATE TABLE IF NOT EXISTS ads.billing_ledger (
    ledger_id        STRING    NOT NULL,
    advertiser_id    STRING    NOT NULL,
    campaign_id      STRING    NOT NULL,
    billing_date     DATE      NOT NULL,
    billable_clicks  BIGINT    NOT NULL,
    billable_spend   DECIMAL(18, 4) NOT NULL,
    excluded_tier1   BIGINT    NOT NULL,   -- shown on the invoice, for trust
    excluded_tier2   BIGINT    NOT NULL,
    excluded_dupes   BIGINT    NOT NULL,
    raw_click_count  BIGINT    NOT NULL,   -- so conservation is verifiable
    entry_type       STRING    NOT NULL,   -- original | adjustment | credit
    supersedes_id    STRING,               -- links an adjustment to its original
    model_version    STRING,
    computed_at      TIMESTAMP NOT NULL
)
USING iceberg
PARTITIONED BY (billing_date)
TBLPROPERTIES ('write.format.default' = 'parquet');

-- raw_click_count is on the ledger deliberately: it lets an auditor check
-- billable + excluded_* = raw without touching the raw table.

-- Idempotency key for the reconciliation MERGE. Re-running a day REPLACES its
-- original entry rather than adding a second one.
-- MERGE INTO ads.billing_ledger t
--   USING staged s
--      ON t.campaign_id = s.campaign_id
--     AND t.billing_date = s.billing_date
--     AND t.entry_type = 'original'
-- WHEN MATCHED THEN UPDATE SET *
-- WHEN NOT MATCHED THEN INSERT *;

-- ============================================================ audit
CREATE TABLE IF NOT EXISTS ads.rejected_events (
    event_id   STRING    NOT NULL,
    reason     STRING    NOT NULL,   -- tier1 reason, or 'duplicate'
    rejected_at TIMESTAMP NOT NULL,
    event_date DATE      NOT NULL
)
USING iceberg
PARTITIONED BY (event_date, reason)
TBLPROPERTIES ('write.format.default' = 'parquet');

-- Rejections are RETAINED. Two reasons: a rising rejection rate is the earliest
-- signal that the fraud rules are misfiring on real traffic, and an advertiser
-- asking "where did my clicks go" needs an answer.
