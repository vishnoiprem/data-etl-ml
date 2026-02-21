-- ============================================================
-- SCB AML Platform — Hive CDM Layer DDL
-- Customer Data Model: Unified cross-country schema
-- All 15 countries merged into common structure
-- ============================================================

CREATE DATABASE IF NOT EXISTS cdm;

-- ────────────────────────────────────────────
-- 1. CDM UNIFIED CUSTOMER (Customer 360)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cdm.dim_customer_unified (
    golden_entity_id        STRING      COMMENT 'Canonical ID linking all country representations',
    customer_id             STRING      COMMENT 'Source system customer ID',
    customer_name           STRING      COMMENT 'Standardised Latin-script name',
    name_local_script       STRING,
    name_variants           ARRAY<STRING>  COMMENT 'All known name spellings',
    date_of_birth           DATE,
    nationality             STRING,
    id_type                 STRING,
    id_number               STRING,
    risk_rating             STRING,
    composite_risk_score    INT         COMMENT '0-100 AML composite score',
    pep_flag                STRING,
    pep_grade               STRING,
    kyc_status              STRING,
    kyc_date                DATE,
    kyc_age_days            INT         COMMENT 'Days since last KYC refresh',
    source_countries        ARRAY<STRING>  COMMENT 'Countries where entity appears',
    source_system           STRING,
    banking_lines           ARRAY<STRING>  COMMENT 'core_banking | retail | cib',
    created_dt              DATE,
    updated_dt              DATE
)
PARTITIONED BY (country_code STRING, dt STRING)
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');

-- ────────────────────────────────────────────
-- 2. CDM UNIFIED ACCOUNT
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cdm.dim_account_unified (
    account_id          STRING,
    golden_entity_id    STRING,
    customer_id         STRING,
    account_type        STRING,
    account_status      STRING,
    currency            STRING,
    currency_usd_rate   DECIMAL(10,6),
    opening_date        DATE,
    closing_date        DATE,
    country_code        STRING
)
PARTITIONED BY (dt STRING)
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY');

-- ────────────────────────────────────────────
-- 3. CDM UNIFIED TRANSACTION
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cdm.fact_transaction_unified (
    txn_id              STRING,
    golden_entity_id    STRING,
    customer_id         STRING,
    account_id          STRING,
    txn_type            STRING,
    amount              DECIMAL(18,2),
    currency            STRING,
    amount_usd          DECIMAL(18,2),
    txn_date            DATE,
    channel             STRING,
    counterparty_id     STRING,
    counterparty_golden_entity_id STRING,
    is_cross_border     BOOLEAN,
    sender_country      STRING,
    receiver_country    STRING,
    source_system       STRING
)
PARTITIONED BY (country_code STRING, dt STRING)
STORED AS ORC
TBLPROPERTIES ('orc.compress' = 'SNAPPY', 'retention.period' = '7years');
