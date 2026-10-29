-- ============================================================
-- SCB AML Platform — Hive ADS Layer DDL
-- Analytical Data Store: AML-ready tables consumed by:
--   • Rules engine
--   • Risk scoring engine
--   • Alert generation
--   • Lucid Search indexing
-- ============================================================

CREATE DATABASE IF NOT EXISTS ads;

-- ────────────────────────────────────────────
-- 1. CUSTOMER RISK PROFILE
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ads.customer_risk_profile (
    golden_entity_id        STRING,
    customer_name           STRING,
    name_variants           ARRAY<STRING>,
    date_of_birth           DATE,
    nationality             STRING,
    pep_flag                STRING,
    pep_grade               STRING,
    -- Risk Scores
    crs_score               INT     COMMENT 'Customer Risk Score 0-100',
    trs_score               INT     COMMENT 'Transaction Risk Score 0-100',
    nrs_score               INT     COMMENT 'Network Risk Score 0-100',
    composite_aml_score     INT     COMMENT 'Weighted composite 0-100',
    risk_band               STRING  COMMENT 'LOW | MEDIUM | HIGH | CRITICAL',
    -- Behavioural Metrics
    txn_count_30d           INT,
    txn_volume_30d_usd      DECIMAL(18,2),
    avg_txn_size_usd        DECIMAL(18,2),
    max_txn_size_usd        DECIMAL(18,2),
    unique_counterparties   INT,
    unique_countries_30d    INT,
    cross_border_vol_usd    DECIMAL(18,2),
    -- KYC
    kyc_status              STRING,
    kyc_age_days            INT,
    -- Flags
    has_sanctions_match     BOOLEAN,
    sanctions_match_score   INT,
    structuring_flag        BOOLEAN,
    dormant_account_flag    BOOLEAN,
    -- Metadata
    profile_date            DATE,
    country_code            STRING
)
PARTITIONED BY (dt STRING)
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');

-- ────────────────────────────────────────────
-- 2. TRANSACTION MONITORING FEED
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ads.txn_monitoring_feed (
    txn_id                  STRING,
    golden_entity_id        STRING,
    customer_name           STRING,
    txn_type                STRING,
    amount_usd              DECIMAL(18,2),
    txn_date                DATE,
    is_cross_border         BOOLEAN,
    sender_country          STRING,
    receiver_country        STRING,
    -- AML Flags
    exceeds_ctr_threshold   BOOLEAN,
    structuring_suspect     BOOLEAN,
    high_risk_counterparty  BOOLEAN,
    sanctions_hit           BOOLEAN,
    -- Risk context
    customer_risk_band      STRING,
    alert_generated         BOOLEAN,
    country_code            STRING
)
PARTITIONED BY (dt STRING)
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');

-- ────────────────────────────────────────────
-- 3. SANCTIONS SCREENING RESULT
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ads.sanctions_screening_result (
    screening_id            STRING,
    golden_entity_id        STRING,
    customer_name           STRING,
    matched_list_source     STRING  COMMENT 'OFAC | UN | EU | MAS_SG | ...',
    matched_entity_name     STRING,
    match_score             INT     COMMENT '0-100',
    match_type              STRING  COMMENT 'exact | fuzzy | phonetic',
    disposition             STRING  COMMENT 'pending | true_match | false_positive',
    analyst_id              STRING,
    disposition_date        DATE,
    screening_date          DATE,
    country_code            STRING
)
PARTITIONED BY (dt STRING)
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');

-- ────────────────────────────────────────────
-- 4. AML ALERT MASTER
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ads.aml_alert_master (
    alert_id                STRING,
    golden_entity_id        STRING,
    customer_name           STRING,
    alert_type              STRING  COMMENT 'STR | SAR | CTR | INTERNAL',
    alert_reason            STRING,
    alert_score             INT,
    risk_band               STRING,
    status                  STRING  COMMENT 'open | under_review | escalated | closed | filed',
    assigned_analyst        STRING,
    created_date            DATE,
    due_date                DATE    COMMENT 'Regulatory SLA deadline',
    filed_date              DATE,
    regulatory_body         STRING  COMMENT 'MAS | FCA | FinCEN | ...',
    country_code            STRING
)
PARTITIONED BY (dt STRING)
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');

-- ────────────────────────────────────────────
-- 5. AML FEATURE STORE
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ads.aml_feature_store (
    golden_entity_id            STRING,
    feature_date                DATE,
    -- Velocity features
    txn_count_1d                INT,
    txn_count_7d                INT,
    txn_count_30d               INT,
    txn_count_90d               INT,
    txn_volume_1d_usd           DECIMAL(18,2),
    txn_volume_7d_usd           DECIMAL(18,2),
    txn_volume_30d_usd          DECIMAL(18,2),
    volume_change_pct_7d        DECIMAL(6,2)   COMMENT 'Volume change vs prior week %',
    -- Structuring features
    count_just_below_threshold  INT    COMMENT 'Txns 85-100% of CTR threshold',
    structuring_score           INT,
    -- Cross-border features
    unique_countries_30d        INT,
    high_risk_country_vol_usd   DECIMAL(18,2),
    cross_border_ratio          DECIMAL(5,2),
    -- Network graph features
    degree_centrality           DECIMAL(6,4),
    betweenness_centrality      DECIMAL(6,4),
    unique_counterparties_30d   INT,
    -- Behavioural features
    avg_txn_size_usd            DECIMAL(18,2),
    avg_txn_size_change_pct     DECIMAL(6,2),
    dormancy_days               INT,
    channel_diversity_score     DECIMAL(4,2),
    -- KYC features
    kyc_age_days                INT,
    risk_rating_changes_12m     INT,
    pep_flag                    STRING,
    country_code                STRING
)
PARTITIONED BY (dt STRING)
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');
