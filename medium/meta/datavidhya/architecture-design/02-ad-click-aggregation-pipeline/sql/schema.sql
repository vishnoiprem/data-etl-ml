-- =============================================================================
-- Ad Click Aggregation Pipeline — Iceberg DDL
-- =============================================================================
-- Seven layers, each owned by a different consumer with a different SLA.
-- The shape follows the README's "one immutable log, two consumers" split.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. raw_ad_events — Kafka's durable counterpart (also archived from Kafka
--    topic raw_ad_events before dedup, so we can replay).
--    Grain: one row per ingest event (post-collector, pre-dedup).
--    Retention: 1 year.  Partitioned by ingest hour for time-range scans.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw_ad_events (
    event_id        STRING        NOT NULL
        COMMENT 'UUIDv7 stamped at the collector; the global dedup key',
    event_ts        TIMESTAMP     NOT NULL
        COMMENT 'Client-reported timestamp; used for windowing',
    ingest_ts       TIMESTAMP     NOT NULL
        COMMENT 'Server-side ingestion time; used for watermark',
    event_type      STRING        NOT NULL
        COMMENT 'impression | click | conversion',
    user_id         STRING        NOT NULL,
    ad_id           BIGINT        NOT NULL,
    campaign_id     BIGINT        NOT NULL,
    advertiser_id   BIGINT        NOT NULL,
    geo_country     STRING,
    device_class    STRING,
    placement       STRING,
    revenue_usd     DECIMAL(18, 6)
        COMMENT 'Only set on conversion events',
    fraud_tier1     BOOLEAN       NOT NULL DEFAULT FALSE
        COMMENT 'TRUE if the collector dropped it; row kept for audit only',
    raw_payload     MAP<STRING, STRING>
)
PARTITIONED BY (hours(ingest_ts))
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd',
    'write.target-file-size-bytes' = '134217728',
    'history.expire.max-snapshot-age-ms' = '31536000000'  -- 1 year
);

-- -----------------------------------------------------------------------------
-- 2. deduped_clicks — Kafka topic, mirrored as an Iceberg table for batch
--    consumers that want to reprocess. The partition key changes here
--    (from hash(user_id) -> hash(campaign_id, salt)).
--    Grain: one row per UNIQUE click after the 60s dedup window.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS deduped_clicks (
    event_id        STRING        NOT NULL,
    event_ts        TIMESTAMP     NOT NULL,
    user_id         STRING        NOT NULL,
    ad_id           BIGINT        NOT NULL,
    campaign_id     BIGINT        NOT NULL,
    salt            INT           NOT NULL
        COMMENT 'salting bucket 0..63; the hot-key mitigator',
    PRIMARY KEY (event_id)
) PARTITIONED BY (hours(event_ts), bucket(64, campaign_id, salt));

-- -----------------------------------------------------------------------------
-- 3. fraud_verdicts — async tier-2 outputs. Append-only.
--    Grain: one row per invalidated event (only emitted if fraud).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fraud_verdicts (
    event_id        STRING        NOT NULL,
    scored_ts       TIMESTAMP     NOT NULL,
    verdict         STRING        NOT NULL
        COMMENT 'invalid | suspicious | clean',
    score           DOUBLE        NOT NULL,
    reason          STRING
        COMMENT 'click_farm | coordinated_network | conversion_anomaly | device_farm',
    PRIMARY KEY (event_id)
)
PARTITIONED BY (days(scored_ts))
TBLPROPERTIES ('write.parquet.compression-codec' = 'zstd');

-- -----------------------------------------------------------------------------
-- 4. speed_aggregates — Druid/Pinot equivalent (modelled as Iceberg for
--    portability). 1-min grain, 7 days retention.
--    Grain: (window_start, ad_id, salt).  salt=-1 means rolled-up (sum-of-salts).
--    The PRIMARY KEY is what makes the upsert idempotent.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS speed_aggregates_1m (
    window_start    TIMESTAMP     NOT NULL,
    ad_id           BIGINT        NOT NULL,
    salt            INT           NOT NULL DEFAULT -1,
    clicks          BIGINT        NOT NULL,
    impressions     BIGINT        NOT NULL,
    conversions     BIGINT        NOT NULL,
    spend_usd       DECIMAL(18, 6) NOT NULL,
    updated_at      TIMESTAMP     NOT NULL,
    PRIMARY KEY (window_start, ad_id, salt)
) PARTITIONED BY (hours(window_start))
TBLPROPERTIES ('format-version' = '2');

-- Hourly and daily grain (90 days / 2 years)
CREATE TABLE IF NOT EXISTS speed_aggregates_1h
    LIKE speed_aggregates_1m PARTITIONED BY (days(window_start));
CREATE TABLE IF NOT EXISTS speed_aggregates_1d
    LIKE speed_aggregates_1m PARTITIONED BY (months(window_start));

-- -----------------------------------------------------------------------------
-- 5. billing_ledger — append-only invoice lines. NEVER mutated; corrections
--    land as additional rows (the accounting principle of immutability).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS billing_ledger (
    ledger_id       BIGINT        NOT NULL,
    advertiser_id   BIGINT        NOT NULL,
    campaign_id     BIGINT        NOT NULL,
    period_start    DATE          NOT NULL,
    period_end      DATE          NOT NULL,
    billable_clicks BIGINT        NOT NULL,
    cpc_usd         DECIMAL(18, 6) NOT NULL,
    gross_usd       DECIMAL(18, 6) NOT NULL,
    adjustment_usd  DECIMAL(18, 6) NOT NULL DEFAULT 0,
    net_usd         DECIMAL(18, 6) NOT NULL,
    issued_at       TIMESTAMP     NOT NULL,
    PRIMARY KEY (ledger_id)
) PARTITIONED BY (months(period_start))
TBLPROPERTIES ('format-version' = '2');

-- -----------------------------------------------------------------------------
-- 6. adjustment_records — the public delta between speed and batch.
--    When the batch layer disagrees with the speed layer, it emits a
--    row here rather than mutating either. This is what makes the
--    pipeline auditable.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS adjustment_records (
    adjustment_id   BIGINT        NOT NULL,
    period_start    DATE          NOT NULL,
    period_end      DATE          NOT NULL,
    advertiser_id   BIGINT        NOT NULL,
    campaign_id     BIGINT        NOT NULL,
    delta_clicks    BIGINT        NOT NULL
        COMMENT 'positive = speed under-counted; negative = over-counted',
    delta_usd       DECIMAL(18, 6) NOT NULL,
    reason          STRING        NOT NULL
        COMMENT 'tier2_fraud | dedup_backfill | late_event | reconciliation',
    published_at    TIMESTAMP     NOT NULL,
    PRIMARY KEY (adjustment_id)
) PARTITIONED BY (months(period_start));

-- -----------------------------------------------------------------------------
-- 7. rejected_events / duplicate_events — audit trails.  Used for dispute
--    resolution and for tuning tier-1 fraud thresholds.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rejected_events (
    event_id        STRING        NOT NULL,
    event_ts        TIMESTAMP     NOT NULL,
    rule            STRING        NOT NULL
        COMMENT 'datacenter_ip | bot_ua | malformed | rate_limit | per_user_burst',
    payload         MAP<STRING, STRING>,
    PRIMARY KEY (event_id)
) PARTITIONED BY (days(event_ts));

CREATE TABLE IF NOT EXISTS duplicate_events (
    event_id        STRING        NOT NULL,
    first_event_id  STRING        NOT NULL
        COMMENT 'the click that won the dedup race',
    delta_ms        BIGINT        NOT NULL,
    PRIMARY KEY (event_id)
) PARTITIONED BY (days(event_ts));
