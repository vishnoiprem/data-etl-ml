-- ============================================================
-- SCB AML Platform — Hive ODS Layer DDL
-- Phase 2: Raw Staging Tables (per-country schema)
-- Convention: ods_{country_code}.{table_name}_raw
-- ============================================================

-- Usage: Replace {COUNTRY} with country code (sg, hk, my, etc.)
-- Run via: hive -f ods_tables.sql --hivevar COUNTRY=sg

SET hivevar:COUNTRY=sg;  -- override at runtime

-- ────────────────────────────────────────────
-- 1. CUSTOMER RAW
-- ────────────────────────────────────────────
CREATE DATABASE IF NOT EXISTS ods_${hivevar:COUNTRY};

CREATE EXTERNAL TABLE IF NOT EXISTS ods_${hivevar:COUNTRY}.customer_raw (
    customer_id         STRING      COMMENT 'Unique customer identifier',
    customer_name       STRING      COMMENT 'Name in Latin script',
    name_local_script   STRING      COMMENT 'Name in original script (Arabic/Chinese/Thai)',
    name_latin          STRING      COMMENT 'Transliterated Latin name',
    date_of_birth       STRING      COMMENT 'ISO 8601 format YYYY-MM-DD',
    nationality         STRING      COMMENT 'ISO country code',
    id_type             STRING      COMMENT 'passport | national_id | nric | company_reg',
    id_number           STRING      COMMENT 'ID document number',
    risk_rating         STRING      COMMENT 'low | medium | high',
    pep_flag            STRING      COMMENT 'Y | N',
    pep_grade           STRING      COMMENT 'A (direct) | B (associate) | C (family)',
    source_system       STRING      COMMENT 'core_banking | retail | cib',
    load_timestamp      TIMESTAMP   COMMENT 'ETL load time',
    source_file         STRING      COMMENT 'Source file or table name'
)
PARTITIONED BY (
    country_code STRING  COMMENT 'ISO country code for data sovereignty',
    dt           STRING  COMMENT 'Partition date YYYYMMDD'
)
STORED AS ORC
LOCATION '/raw/${hivevar:COUNTRY}/customer_raw/'
TBLPROPERTIES (
    'orc.compress'         = 'SNAPPY',
    'retention.period'     = '7years',
    'data.classification'  = 'CONFIDENTIAL'
);

-- ────────────────────────────────────────────
-- 2. ACCOUNT RAW
-- ────────────────────────────────────────────
CREATE EXTERNAL TABLE IF NOT EXISTS ods_${hivevar:COUNTRY}.account_raw (
    account_id      STRING,
    customer_id     STRING,
    account_type    STRING    COMMENT 'savings | current | credit | trade_finance | loan',
    account_status  STRING    COMMENT 'active | dormant | closed',
    currency        STRING    COMMENT 'ISO currency code',
    opening_date    STRING,
    closing_date    STRING,
    load_timestamp  TIMESTAMP,
    source_file     STRING
)
PARTITIONED BY (country_code STRING, dt STRING)
STORED AS ORC
LOCATION '/raw/${hivevar:COUNTRY}/account_raw/'
TBLPROPERTIES ('orc.compress' = 'SNAPPY');

-- ────────────────────────────────────────────
-- 3. TRANSACTION RAW (Retail)
-- ────────────────────────────────────────────
CREATE EXTERNAL TABLE IF NOT EXISTS ods_${hivevar:COUNTRY}.transaction_raw (
    txn_id              STRING,
    account_id          STRING,
    customer_id         STRING,
    txn_type            STRING    COMMENT 'deposit | withdrawal | transfer | remittance | card_payment',
    amount              DECIMAL(18,2),
    currency            STRING,
    amount_usd          DECIMAL(18,2)  COMMENT 'Normalised to USD using daily FX',
    txn_date            STRING,
    txn_time            STRING,
    channel             STRING    COMMENT 'branch | atm | online | mobile',
    counterparty_id     STRING,
    counterparty_bank   STRING,
    source_system       STRING,
    load_timestamp      TIMESTAMP
)
PARTITIONED BY (country_code STRING, dt STRING)
STORED AS ORC
LOCATION '/raw/${hivevar:COUNTRY}/transaction_raw/'
TBLPROPERTIES ('orc.compress' = 'SNAPPY', 'retention.period' = '7years');

-- ────────────────────────────────────────────
-- 4. WIRE TRANSFER RAW (CIB — SWIFT MT103/MT202)
-- ────────────────────────────────────────────
CREATE EXTERNAL TABLE IF NOT EXISTS ods_${hivevar:COUNTRY}.wire_transfer_raw (
    wire_id                 STRING,
    swift_msg_type          STRING    COMMENT 'MT103 | MT202 | MT202COV',
    sender_customer_id      STRING,
    sender_country          STRING,
    sender_bank_bic         STRING,
    receiver_customer_id    STRING,
    receiver_country        STRING,
    receiver_bank_bic       STRING,
    amount                  DECIMAL(18,2),
    currency                STRING,
    amount_usd              DECIMAL(18,2),
    value_date              STRING,
    purpose_code            STRING    COMMENT 'TRADE | INVEST | FAMILY | SALARY | UNKNOWN',
    reference_number        STRING,
    load_timestamp          TIMESTAMP
)
PARTITIONED BY (country_code STRING, dt STRING)
STORED AS ORC
LOCATION '/raw/${hivevar:COUNTRY}/wire_transfer_raw/'
TBLPROPERTIES ('orc.compress' = 'SNAPPY');

-- ────────────────────────────────────────────
-- 5. KYC RECORDS RAW
-- ────────────────────────────────────────────
CREATE EXTERNAL TABLE IF NOT EXISTS ods_${hivevar:COUNTRY}.kyc_raw (
    kyc_id                      STRING,
    customer_id                 STRING,
    kyc_status                  STRING    COMMENT 'verified | pending | expired | rejected',
    kyc_date                    STRING,
    kyc_officer                 STRING,
    id_verified                 BOOLEAN,
    address_verified            BOOLEAN,
    source_of_funds_verified    BOOLEAN,
    risk_rating                 STRING,
    pep_flag                    STRING,
    load_timestamp              TIMESTAMP
)
PARTITIONED BY (country_code STRING, dt STRING)
STORED AS ORC
LOCATION '/raw/${hivevar:COUNTRY}/kyc_raw/'
TBLPROPERTIES ('orc.compress' = 'SNAPPY');

-- ────────────────────────────────────────────
-- 6. RELATIONSHIP / BENEFICIAL OWNERSHIP RAW
-- ────────────────────────────────────────────
CREATE EXTERNAL TABLE IF NOT EXISTS ods_${hivevar:COUNTRY}.relationship_raw (
    rel_id              STRING,
    entity_id           STRING,
    related_entity_id   STRING,
    relationship_type   STRING  COMMENT 'beneficial_owner | director | spouse | parent_company | subsidiary',
    link_strength       DECIMAL(4,2)  COMMENT '0.0 to 1.0',
    effective_date      STRING,
    load_timestamp      TIMESTAMP
)
PARTITIONED BY (country_code STRING, dt STRING)
STORED AS ORC
LOCATION '/raw/${hivevar:COUNTRY}/relationship_raw/'
TBLPROPERTIES ('orc.compress' = 'SNAPPY');
