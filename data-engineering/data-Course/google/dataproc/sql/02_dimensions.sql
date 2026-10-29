-- =====================================================================
-- 02_dimensions.sql
-- Course: Dataproc + PySpark for Big Data Engineers
--
-- The SILVER layer: conformed, slowly-changing dimensions.
--
-- Every dimension follows the same three rules:
--
--   1. A surrogate key (the *_sk column). It is INT64, it is dense, and
--      it is assigned by the pipeline — never by the source system.
--   2. A natural key (the business identifier). It is STRING, it comes
--      from the source, and it is what you join on when loading data.
--   3. SCD type 2 columns:
--        valid_from  DATE  -- when this version became current
--        valid_to    DATE  -- when this version stopped being current
--        is_current  BOOL  -- TRUE for the current version
--
-- The `valid_to` convention in this course: NULL means "still current".
-- The alternative — a far-future sentinel date like 9999-12-31 — is
-- equally valid but produces date arithmetic that has to special-case
-- the sentinel everywhere. NULL is easier to reason about.
--
-- Usage:
--   bq query --use_legacy_sql=false < 02_dimensions.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. silver.dim_product
--
--    The product master. A product can change category, brand, or cost
--    over time; each change closes the previous row and opens a new one.
--
--    CLUSTER BY product_id because every fact row joins on it. Clustering
--    sorts the physical blocks so the join reads a compact range instead
--    of scanning the whole dimension.
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID`.silver.dim_product (
  product_sk        INT64           NOT NULL,
  product_id        STRING          NOT NULL,
  product_name      STRING,
  category_id       STRING,
  category_name     STRING,
  brand             STRING,
  unit_cost         NUMERIC(18,2),
  currency_code     STRING,
  valid_from        DATE            NOT NULL,
  valid_to          DATE,
  is_current        BOOL            NOT NULL,
  loaded_at         TIMESTAMP       NOT NULL,
  source_file       STRING
)
CLUSTER BY product_id
OPTIONS(
  description = "SCD2 product dimension. One row per (product_id, version). valid_to IS NULL and is_current = TRUE identify the current version.",
  labels = [("tier", "silver"), ("entity", "product"), ("scd", "2")],
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);

-- ---------------------------------------------------------------------
-- 2. silver.dim_store
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID`.silver.dim_store (
  store_sk          INT64           NOT NULL,
  store_id          STRING          NOT NULL,
  store_name        STRING,
  city              STRING,
  state             STRING,
  region_id         STRING,
  region_name       STRING,
  store_format      STRING,
  sq_ft             INT64,
  valid_from        DATE            NOT NULL,
  valid_to          DATE,
  is_current        BOOL            NOT NULL,
  loaded_at         TIMESTAMP       NOT NULL,
  source_file       STRING
)
CLUSTER BY store_id
OPTIONS(
  description = "SCD2 store dimension. One row per (store_id, version). Store attribute changes (reformat, relocation) open a new version.",
  labels = [("tier", "silver"), ("entity", "store"), ("scd", "2")],
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);

-- ---------------------------------------------------------------------
-- 3. silver.dim_provider
--
--    Healthcare case study. A provider can change name, type, or
--    contract status. Contract_start / contract_end capture the
--    commercial relationship; valid_from / valid_to capture the
--    attribute version.
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID`.silver.dim_provider (
  provider_sk       INT64           NOT NULL,
  provider_npi      STRING          NOT NULL,
  provider_name     STRING,
  provider_type     STRING,
  tax_id            STRING,
  city              STRING,
  state             STRING,
  contract_start    DATE,
  contract_end      DATE,
  is_active         BOOL,
  valid_from        DATE            NOT NULL,
  valid_to          DATE,
  is_current        BOOL            NOT NULL,
  loaded_at         TIMESTAMP       NOT NULL,
  source_file       STRING
)
CLUSTER BY provider_npi
OPTIONS(
  description = "SCD2 provider dimension, keyed on NPI. provider_name is a business name, not a person identifier.",
  labels = [("tier", "silver"), ("entity", "provider"), ("scd", "2")],
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);

-- ---------------------------------------------------------------------
-- 4. silver.dim_diagnosis
--
--    The ICD-10 code reference. This is a Type 1 dimension in practice
--    — a code's description does not change — but it carries the same
--    SCD2 columns so the model is uniform across every domain.
--
--    is_valid is the reference-data validation flag: TRUE when the code
--    matches the ICD-10 structural pattern and exists in the reference
--    set. The pipeline uses it to decide whether a claim's diagnosis
--    code is acceptable.
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID`.silver.dim_diagnosis (
  diagnosis_sk      INT64           NOT NULL,
  icd10_code        STRING          NOT NULL,
  description       STRING,
  category          STRING,
  chapter           STRING,
  is_valid          BOOL            NOT NULL,
  valid_from        DATE            NOT NULL,
  valid_to          DATE,
  is_current        BOOL            NOT NULL,
  loaded_at         TIMESTAMP       NOT NULL,
  source_file       STRING
)
CLUSTER BY icd10_code
OPTIONS(
  description = "ICD-10 diagnosis code reference with validity flags. is_valid = FALSE marks codes that fail the ICD-10 structural regex.",
  labels = [("tier", "silver"), ("entity", "diagnosis"), ("scd", "2")],
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);

-- ---------------------------------------------------------------------
-- 5. Verify the dimensions landed
-- ---------------------------------------------------------------------

SELECT
  'dim_product' AS dimension,
  COUNT(*) AS total_rows,
  COUNTIF(is_current) AS current_rows,
  COUNTIF(NOT is_current) AS historical_rows,
  COUNT(DISTINCT product_id) AS distinct_natural_keys
FROM `YOUR_PROJECT_ID`.silver.dim_product
UNION ALL
SELECT
  'dim_store',
  COUNT(*),
  COUNTIF(is_current),
  COUNTIF(NOT is_current),
  COUNT(DISTINCT store_id)
FROM `YOUR_PROJECT_ID`.silver.dim_store
UNION ALL
SELECT
  'dim_provider',
  COUNT(*),
  COUNTIF(is_current),
  COUNTIF(NOT is_current),
  COUNT(DISTINCT provider_npi)
FROM `YOUR_PROJECT_ID`.silver.dim_provider
UNION ALL
SELECT
  'dim_diagnosis',
  COUNT(*),
  COUNTIF(is_current),
  COUNTIF(NOT is_current),
  COUNT(DISTINCT icd10_code)
FROM `YOUR_PROJECT_ID`.silver.dim_diagnosis;

-- ---------------------------------------------------------------------
-- 6. SCD2 integrity checks
--
--    Check A: every natural key must have EXACTLY ONE current version.
--             FAIL looks like: a key with 0 current rows (the pipeline
--             closed the old version but never opened the new one) or a
--             key with 2+ current rows (two loads both inserted a new
--             version without closing the previous).
--
--    Check B: no overlapping validity ranges. FAIL looks like: a key
--             where one version's valid_from falls inside another
--             version's [valid_from, valid_to) window.
-- ---------------------------------------------------------------------

-- Check A — exactly one current version per natural key.
SELECT
  product_id,
  COUNTIF(is_current) AS current_version_count
FROM `YOUR_PROJECT_ID`.silver.dim_product
GROUP BY product_id
HAVING COUNTIF(is_current) <> 1
ORDER BY product_id;

-- Check B — overlapping validity windows.
WITH ordered AS (
  SELECT
    product_id,
    valid_from,
    valid_to,
    LAG(valid_to) OVER (PARTITION BY product_id ORDER BY valid_from) AS prev_valid_to
  FROM `YOUR_PROJECT_ID`.silver.dim_product
)
SELECT
  product_id,
  valid_from,
  valid_to,
  prev_valid_to
FROM ordered
WHERE prev_valid_to IS NOT NULL
  AND valid_from < prev_valid_to
ORDER BY product_id, valid_from;
