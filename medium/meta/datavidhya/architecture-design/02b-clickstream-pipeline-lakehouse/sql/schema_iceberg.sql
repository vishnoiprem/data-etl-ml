-- =====================================================================
-- Clickstream Lakehouse — Iceberg DDL
--
-- Three layers:
--   bronze_events  – raw, immutable, bot-tagged, 7d TTL
--   silver_events  – cleaned, deduped, bot-filtered, Z-ORDER user_id
--   gold_user_features_daily – user-day grain aggregations for ML/exp
-- =====================================================================

CREATE NAMESPACE IF NOT EXISTS lakehouse;

-- ---------------------------------------------------------------------
-- BRONZE: raw events, every payload preserved (bots tagged, not deleted)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lakehouse.bronze_events (
    event_id       STRING          NOT NULL,
    user_id        STRING          NOT NULL,
    session_id     STRING,
    event_ts       TIMESTAMP       NOT NULL,
    received_ts    TIMESTAMP       NOT NULL,
    event_name     STRING          NOT NULL,
    platform       STRING,                              -- web / ios / android / server
    app_version    STRING,
    country        STRING,
    device_class   STRING,
    user_agent     STRING,
    ip_hash        STRING,
    properties     MAP<STRING, STRING>,
    context        MAP<STRING, STRING>,
    ingest_status  STRING,                              -- OK / BOT_STAGE1 / BOT_STAGE2 / BOT_STAGE3 / INVALID
    bot_score      DOUBLE,
    PRIMARY KEY (event_id)
) PARTITIONED BY (days(event_ts))
  TBLPROPERTIES (
    'format-version'    = '2',
    'write.format.default' = 'parquet',
    'write.parquet.compression-codec' = 'snappy',
    'gc.enabled'        = 'true',
    'history.expire.max-snapshot-age-ms' = '604800000'    -- 7d
  );

-- ---------------------------------------------------------------------
-- SILVER: only human events, deduped, enriched
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lakehouse.silver_events (
    event_id       STRING          NOT NULL,
    user_id        STRING          NOT NULL,
    session_id     STRING,
    event_ts       TIMESTAMP       NOT NULL,
    event_name     STRING          NOT NULL,
    platform       STRING,
    country        STRING,
    device_class   STRING,
    properties     MAP<STRING, STRING>,
    user_traits    MAP<STRING, STRING>,
    experiment_ids ARRAY<STRING>,
    dt             DATE            NOT NULL,
    PRIMARY KEY (event_id)
) PARTITIONED BY (dt)
  TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd',
    'history.expire.max-snapshot-age-ms' = '15552000000'   -- 180d
  );

-- ---------------------------------------------------------------------
-- GOLD: user × day feature rollups for ML / experimentation
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lakehouse.gold_user_features_daily (
    user_id            STRING  NOT NULL,
    dt                 DATE    NOT NULL,
    page_views         BIGINT,
    clicks             BIGINT,
    scrolls            BIGINT,
    purchases          BIGINT,
    form_submits       BIGINT,
    purchase_revenue   DOUBLE,
    session_count      BIGINT,
    total_session_secs BIGINT,
    distinct_pages     BIGINT,
    platform_top       STRING,
    country            STRING,
    PRIMARY KEY (user_id, dt)
) PARTITIONED BY (dt);

-- ---------------------------------------------------------------------
-- GOLD: session-level (for funnel analysis, dashboards)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lakehouse.gold_session_metrics (
    session_id         STRING  NOT NULL,
    user_id            STRING  NOT NULL,
    started_ts         TIMESTAMP,
    ended_ts           TIMESTAMP,
    duration_s         BIGINT,
    page_view_count    BIGINT,
    click_count        BIGINT,
    conversion_flag    BOOLEAN,
    entry_page         STRING,
    exit_page          STRING,
    dt                 DATE,
    PRIMARY KEY (session_id)
) PARTITIONED BY (dt);
