-- =====================================================================
-- A/B Testing & Experimentation Platform — Core Schema
-- Target: Apache Iceberg / Delta Lake compatible
-- =====================================================================

-- 1) Experiments: the unit of business intent
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id        STRING          NOT NULL,
    name                 STRING          NOT NULL,
    owner_email          STRING          NOT NULL,
    status               STRING          NOT NULL,  -- DRAFT, RUNNING, PAUSED, CONCLUDED, ARCHIVED
    hypothesis           STRING,
    primary_metric_id    STRING,
    guardrail_metric_ids ARRAY<STRING>,
    variants             ARRAY<STRUCT<
                            variant_id: STRING,
                            name:       STRING,
                            allocation: DOUBLE       -- 0..1, must sum to 1
                         >>,
    layers               ARRAY<STRING>,             -- ['layer_1_feed'], for orthogonal bucketing
    mutex_group          STRING,                    -- mutually exclusive with other experiments in same group
    traffic_allocation   DOUBLE,                    -- 0..1 of users eligible for this experiment
    start_ts             TIMESTAMP,
    end_ts               TIMESTAMP,
    created_ts           TIMESTAMP       DEFAULT current_timestamp(),
    PRIMARY KEY (experiment_id)
) PARTITIONED BY (days(start_ts));

-- 2) Experiment assignments: (user, experiment) -> variant
-- Pre-computed; deterministic hash lives in the assignment service.
CREATE TABLE IF NOT EXISTS experiment_assignments (
    user_id         STRING          NOT NULL,
    experiment_id   STRING          NOT NULL,
    variant_id      STRING          NOT NULL,
    layer           STRING          NOT NULL,
    assigned_ts     TIMESTAMP       NOT NULL,
    PRIMARY KEY (user_id, experiment_id)
) PARTITIONED BY (days(assigned_ts));

-- 3) Events: raw user interactions
CREATE TABLE IF NOT EXISTS events (
    event_id        STRING          NOT NULL,   -- client-generated UUID; dedup key
    user_id         STRING          NOT NULL,
    event_ts        TIMESTAMP       NOT NULL,
    event_name      STRING          NOT NULL,   -- 'page_view','click','purchase',...
    properties      MAP<STRING, STRING>,
    experiment_tags ARRAY<STRING>,              -- experiment ids carried in payload
    ingested_ts     TIMESTAMP       DEFAULT current_timestamp(),
    PRIMARY KEY (event_id)
) PARTITIONED BY (days(event_ts));

-- 4) Metric definitions: declarative metric catalog
CREATE TABLE IF NOT EXISTS metric_definitions (
    metric_id       STRING          NOT NULL,
    name            STRING          NOT NULL,
    metric_type     STRING          NOT NULL,   -- PROPORTION, MEAN, COUNT, RATIO, QUANTILE
    sql_formula     STRING,                    -- e.g. SUM(purchase_amount)/COUNT(DISTINCT user_id)
    numerator_event STRING,
    denominator_event STRING,
    owner_email     STRING,
    is_guardrail    BOOLEAN         DEFAULT FALSE,
    PRIMARY KEY (metric_id)
);

-- 5) Per-user-per-day metrics (the workhorse table)
CREATE TABLE IF NOT EXISTS user_metric_daily (
    user_id         STRING          NOT NULL,
    experiment_id   STRING          NOT NULL,
    variant_id      STRING          NOT NULL,
    metric_id       STRING          NOT NULL,
    dt              DATE            NOT NULL,
    value           DOUBLE,
    pre_value       DOUBLE,                    -- for CUPED
    PRIMARY KEY (user_id, experiment_id, metric_id, dt)
) PARTITIONED BY (dt);

-- 6) Experiment results: statistical outputs
CREATE TABLE IF NOT EXISTS experiment_results (
    experiment_id   STRING          NOT NULL,
    metric_id       STRING          NOT NULL,
    variant_id      STRING          NOT NULL,
    dt              DATE,
    sample_size     BIGINT,
    point_estimate  DOUBLE,
    ci_low          DOUBLE,
    ci_high         DOUBLE,
    p_value         DOUBLE,
    sequential_p    DOUBLE,                    -- mSPRT p-value, always-valid
    is_significant  BOOLEAN,
    computed_ts     TIMESTAMP       DEFAULT current_timestamp(),
    PRIMARY KEY (experiment_id, metric_id, variant_id, dt)
);

-- 7) Guardrail alerts
CREATE TABLE IF NOT EXISTS guardrail_alerts (
    alert_id        STRING          NOT NULL,
    experiment_id   STRING          NOT NULL,
    metric_id       STRING          NOT NULL,
    variant_id      STRING,
    severity        STRING,                     -- WARN, CRITICAL
    observed_value  DOUBLE,
    threshold_value DOUBLE,
    triggered_ts    TIMESTAMP       DEFAULT current_timestamp(),
    auto_action     STRING,                     -- NONE, PAUSE_EXPERIMENT, ROLLBACK
    PRIMARY KEY (alert_id)
);
