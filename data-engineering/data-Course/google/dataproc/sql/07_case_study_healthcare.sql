-- =====================================================================
-- 07_case_study_healthcare.sql
-- Course: Dataproc + PySpark for Big Data Engineers
-- Chapter: 11 — Healthcare Claims Processing case study
--
-- The complete healthcare model layer in BigQuery SQL. This is the
-- BigQuery-side counterpart to the PySpark job in chapter 11.
--
-- The model:
--
--   bronze.claims_payloads      raw NDJSON, exactly as landed
--        │
--        ▼  parse JSON, validate, quarantine rejects
--   gold.fact_claims            one row per claim_id
--        │
--        ├──▶ silver.dim_provider    keyed on provider_npi
--        └──▶ silver.dim_diagnosis   ICD-10 reference
--                │
--                ▼  aggregate + 30-day rolling z-score
--   mart.provider_spend
--
-- PHI note: the source JSON carries member_id and nothing else. No
-- name, no DOB, no SSN. If a real feed carried them, the parse
-- boundary in PySpark would drop them — fields never ingested cannot
-- leak.
--
-- Usage:
--   bq query --use_legacy_sql=false < 07_case_study_healthcare.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. bronze.claims_payloads — the landing zone
--
--    The payload arrives as a JSON-encoded STRING. It is kept that way
--    in bronze: the landing zone preserves what arrived, and the
--    structure is a business concern, not a landing concern.
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID`.bronze.claims_payloads (
  claim_id          STRING,
  provider_npi      STRING,
  member_id         STRING,
  service_date      STRING,
  submitted_at      STRING,
  claim_amount      STRING,
  diagnosis_payload STRING,
  procedure_codes   STRING,
  denial_code       STRING,
  denial_reason     STRING,
  source_file       STRING,
  ingested_at       TIMESTAMP NOT NULL
)
OPTIONS(
  description = "Raw claims extracts. diagnosis_payload holds a JSON-encoded string containing a dx array. Includes dirty rows.",
  labels = [("tier", "bronze"), ("domain", "healthcare")],
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);


-- ---------------------------------------------------------------------
-- 2. The ICD-10 validation regex.
--
--    The pattern is the standard ICD-10-CM format:
--
--        ^[A-TV-Z][0-9][0-9AB](\.[0-9A-TV-Z]{1,4})?$
--            │      │  │       └─ optional 1–4 alphanumeric characters
--            │      │  └─ 3rd character is a digit, 'A', or 'B'
--            │      └─ 2nd character is a digit
--            └─ 1st character is a letter from A-T or V-Z
--                             (U is reserved; V-Y are added codes)
--
--    The alphanumeric tail matters. Real ICD-10-CM codes carry a 7th
--    character that is often a LETTER, not a digit:
--
--      S06.0X0A   valid  (concussion, 7th character 'A')
--      X58.XX1A   valid  (external cause, 7th character 'A')
--
--    A pattern of `(\.[0-9]{1,4})?` would wrongly reject every one of
--    those codes. This is the single most common way an ICD regex gets
--    written wrong, and it silently quarantines real claims.
--
--    This is the SAME pattern the PySpark job uses
--    (chapter 11: ICD10_REGEX). The SQL and the Python validation
--    rules must agree, or the same claim gets two different verdicts
--    depending on which layer you ask.
--
--    BigQuery's REGEXP_CONTAINS uses RE2 syntax. The pattern is
--    anchored with ^ and $ so it matches the WHOLE field.
--
--    Examples:
--      E11.9    valid  (letter + 2 digits + . + 1 digit)
--      I10      valid
--      Z00.00   valid
--      S06.0X0A valid  (7th character is a letter)
--      A1.2     INVALID (only 1 digit after the letter)
--      12345    INVALID (starts with a digit)
--      E11.9x   INVALID (trailing character after the decimal)
--      U07.1    INVALID ('U' is reserved in the first position)
-- ---------------------------------------------------------------------

SELECT
  code,
  REGEXP_CONTAINS(code, r'^[A-TV-Z][0-9][0-9AB](\.[0-9A-TV-Z]{1,4})?$') AS is_structurally_valid
FROM UNNEST([
  'E11.9', 'I10', 'Z00.00', 'M54.5', 'S06.0X0A', 'X58.XX1A',
  'A1.2', '12345', 'E11.9x', '', 'J45.909'
]) AS code;


-- ---------------------------------------------------------------------
-- 3. bronze -> staging: parse the nested JSON and flatten the dx array.
--
--    The source stores the diagnosis codes as a JSON-encoded STRING —
--    the column holds the TEXT of a JSON array, not a native BigQuery
--    ARRAY. Two levels of parsing are needed:
--      1. PARSE_JSON turns the STRING into a JSON value.
--      2. UNNEST explodes that array into one row per element.
--
--    ⚠️ PARSE_JSON on a malformed string raises an error, so the
--    malformed input must be filtered out BEFORE it is parsed. The
--    guard below uses JSON_VALUE on the PARSED value to confirm the
--    payload is a well-formed JSON array, and only then hands it to
--    UNNEST. Without the guard, one bad row aborts the entire load.
--
--    The array is then UNNESTed to one row per (claim, diagnosis code).
--    That is the "explode the array" step — the same operation as
--    PySpark's explode().
-- ---------------------------------------------------------------------

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID`.staging.claims_dx_exploded AS
WITH parsed AS (
  SELECT
    b.claim_id,
    b.provider_npi,
    b.member_id,
    SAFE_CAST(b.service_date AS DATE) AS service_date,
    SAFE_CAST(b.submitted_at AS TIMESTAMP) AS submitted_at,
    SAFE_CAST(b.claim_amount AS NUMERIC(18,2)) AS claim_amount,
    b.denial_code,
    b.denial_reason,
    b.procedure_codes,
    b.source_file,
    -- PARSE_JSON returns a JSON value; JSON_QUERY then extracts the
    -- array as an ARRAY<JSON> so UNNEST can explode it.
    IF(
      b.diagnosis_payload IS NULL
        OR NOT JSON_IS_VALID(b.diagnosis_payload),
      CAST(NULL AS ARRAY<JSON>),
      JSON_QUERY(PARSE_JSON(b.diagnosis_payload), '$')
    ) AS dx_array
  FROM `YOUR_PROJECT_ID`.bronze.claims_payloads AS b
  WHERE b.claim_id IS NOT NULL
    AND b.claim_id != ''
)
SELECT
  p.claim_id,
  p.provider_npi,
  p.member_id,
  p.service_date,
  p.submitted_at,
  p.claim_amount,
  p.denial_code,
  p.denial_reason,
  p.procedure_codes,
  p.source_file,
  JSON_VALUE(dx.dx_json, '$.code') AS dx_code,
  JSON_VALUE(dx.dx_json, '$.description') AS dx_description,
  ROW_NUMBER() OVER (PARTITION BY p.claim_id ORDER BY JSON_VALUE(dx.dx_json, '$.code')) AS dx_ordinal,
  -- Same NULL-padding caveat as below: count the codes, not the rows.
  COUNTIF(dx.dx_json IS NOT NULL) OVER (PARTITION BY p.claim_id) AS dx_code_count
FROM parsed AS p
LEFT JOIN UNNEST(p.dx_array) AS dx
ON TRUE;


-- ---------------------------------------------------------------------
-- 4. The validation rules, expressed as SQL predicates.
--
--    Each rule produces a boolean. A claim is valid when ALL of them
--    are true. A claim with NO valid diagnosis codes is rejected —
--    "all codes bad" is as unusable as "no codes".
--
--    The PySpark job in chapter 11 applies the same rules. Keeping
--    the two in sync is the point of writing them down.
-- ---------------------------------------------------------------------

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID`.staging.claims_validated AS
WITH code_validity AS (
  SELECT
    claim_id,
    -- COUNTIF(dx_code IS NOT NULL), not COUNT(*): a claim with an
    -- empty diagnosis array is LEFT-JOIN-padded with one NULL row.
    -- COUNT(*) would report codes_found = 1 for a claim that actually
    -- has zero codes, and the "NO_DIAGNOSIS_CODES" rule would never
    -- fire.
    COUNTIF(dx_code IS NOT NULL) AS codes_found,
    COUNTIF(REGEXP_CONTAINS(dx_code, r'^[A-TV-Z][0-9][0-9AB](\.[0-9A-TV-Z]{1,4})?$')) AS codes_structurally_valid,
    COUNTIF(REGEXP_CONTAINS(dx_code, r'^[A-TV-Z][0-9][0-9AB](\.[0-9A-TV-Z]{1,4})?$')
            AND dx_code IN (SELECT icd10_code FROM `YOUR_PROJECT_ID`.silver.dim_diagnosis WHERE is_current)) AS codes_fully_valid
  FROM `YOUR_PROJECT_ID`.staging.claims_dx_exploded
  GROUP BY claim_id
),
base AS (
  SELECT
    b.claim_id,
    b.provider_npi,
    b.member_id,
    b.service_date,
    b.submitted_at,
    b.claim_amount,
    b.denial_code,
    b.denial_reason,
    b.procedure_codes,
    b.source_file,
    v.codes_found,
    v.codes_structurally_valid,
    v.codes_fully_valid,
    -- The first structurally-valid code is the primary diagnosis.
    (SELECT dx_code
     FROM `YOUR_PROJECT_ID`.staging.claims_dx_exploded AS d
     WHERE d.claim_id = b.claim_id
       AND REGEXP_CONTAINS(d.dx_code, r'^[A-TV-Z][0-9][0-9AB](\.[0-9A-TV-Z]{1,4})?$')
     ORDER BY d.dx_ordinal
     LIMIT 1) AS primary_dx_code
  FROM `YOUR_PROJECT_ID`.bronze.claims_payloads AS b
  LEFT JOIN code_validity AS v
    ON b.claim_id = v.claim_id
  WHERE b.claim_id IS NOT NULL AND b.claim_id != ''
)
SELECT
  base.*,
  CASE
    WHEN service_date IS NULL THEN 'INVALID_SERVICE_DATE'
    WHEN submitted_at IS NULL THEN 'INVALID_SUBMITTED_AT'
    WHEN service_date > DATE '2026-10-27' THEN 'FUTURE_SERVICE_DATE'
    WHEN claim_amount IS NULL THEN 'NULL_CLAIM_AMOUNT'
    WHEN claim_amount < 0 THEN 'NEGATIVE_CLAIM_AMOUNT'
    WHEN claim_amount > 1000000 THEN 'IMPLAUSIBLE_CLAIM_AMOUNT'
    WHEN provider_npi IS NULL OR provider_npi = '' THEN 'MISSING_PROVIDER'
    WHEN codes_found = 0 THEN 'NO_DIAGNOSIS_CODES'
    WHEN codes_structurally_valid = 0 THEN 'ALL_DX_CODES_MALFORMED'
    ELSE 'VALID'
  END AS validation_status
FROM base;


-- ---------------------------------------------------------------------
-- 5. gold.fact_claims — the validated claims.
--
--    The MERGE is scoped to the run date on both sides, which makes
--    the load idempotent.
-- ---------------------------------------------------------------------

MERGE `YOUR_PROJECT_ID`.gold.fact_claims AS t
USING (
  SELECT
    v.claim_id,
    v.member_id,
    v.provider_npi AS provider_id,
    v.service_date,
    v.submitted_at,
    v.claim_amount,
    v.primary_dx_code,
    v.codes_found AS dx_code_count,
    -- procedure_codes is a JSON-encoded string array in bronze. Parse it
    -- to count the elements. The JSON_IS_VALID guard matters: a claim
    -- whose procedure_codes field is corrupt would otherwise abort the
    -- whole load with a PARSE_JSON error.
    IF(
      v.procedure_codes IS NULL OR NOT JSON_IS_VALID(v.procedure_codes),
      0,
      ARRAY_LENGTH(JSON_QUERY(PARSE_JSON(v.procedure_codes), '$'))
    ) AS procedure_count,
    v.denial_code IS NOT NULL AND v.denial_code != '' AS is_denied,
    v.denial_code,
    v.denial_reason,
    p.provider_sk,
    p.provider_name,
    p.provider_type,
    v.source_file,
    DATE(v.submitted_at) AS run_date,
    CURRENT_TIMESTAMP() AS loaded_at
  FROM `YOUR_PROJECT_ID`.staging.claims_validated AS v
  LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_provider AS p
    ON v.provider_npi = p.provider_npi AND p.is_current
  WHERE v.validation_status = 'VALID'
    AND DATE(v.submitted_at) = DATE '2026-10-27'
) AS src
ON t.claim_id = src.claim_id
   AND t.service_date = src.service_date
WHEN MATCHED THEN
  UPDATE SET
    t.member_id = src.member_id,
    t.provider_id = src.provider_id,
    t.submitted_at = src.submitted_at,
    t.claim_amount = src.claim_amount,
    t.primary_dx_code = src.primary_dx_code,
    t.dx_code_count = src.dx_code_count,
    t.procedure_count = src.procedure_count,
    t.is_denied = src.is_denied,
    t.denial_code = src.denial_code,
    t.denial_reason = src.denial_reason,
    t.provider_sk = src.provider_sk,
    t.provider_name = src.provider_name,
    t.provider_type = src.provider_type,
    t.source_file = src.source_file,
    t.run_date = src.run_date,
    t.loaded_at = src.loaded_at
WHEN NOT MATCHED THEN
  INSERT (
    claim_id, member_id, provider_id, service_date, submitted_at,
    claim_amount, primary_dx_code, dx_code_count, procedure_count,
    is_denied, denial_code, denial_reason,
    provider_sk, provider_name, provider_type,
    source_file, run_date, loaded_at
  )
  VALUES (
    src.claim_id, src.member_id, src.provider_id, src.service_date, src.submitted_at,
    src.claim_amount, src.primary_dx_code, src.dx_code_count, src.procedure_count,
    src.is_denied, src.denial_code, src.denial_reason,
    src.provider_sk, src.provider_name, src.provider_type,
    src.source_file, src.run_date, src.loaded_at
  );


-- ---------------------------------------------------------------------
-- 6. gold.quarantine_rejected_claims — persist the rejects.
--
--    Note the ORDER of the rules in the CASE. It matches the order the
--    validation_status column was computed in, so a row that fails
--    several rules always reports the same reason.
-- ---------------------------------------------------------------------

MERGE `YOUR_PROJECT_ID`.gold.quarantine_rejected_claims AS t
USING (
  SELECT
    v.claim_id,
    v.member_id,
    v.provider_npi AS provider_id,
    v.service_date,
    v.claim_amount,
    v.validation_status AS reject_reason,
    TO_JSON_STRING(STRUCT(
      v.claim_id, v.provider_npi, v.member_id, v.service_date,
      v.submitted_at, v.claim_amount, v.denial_code, v.denial_reason
    )) AS raw_payload,
    v.source_file,
    DATE '2026-10-27' AS run_date,
    CURRENT_TIMESTAMP() AS rejected_at
  FROM `YOUR_PROJECT_ID`.staging.claims_validated AS v
  WHERE v.validation_status != 'VALID'
) AS src
ON t.run_date = src.run_date
   AND t.claim_id = src.claim_id
   AND t.reject_reason = src.reject_reason
WHEN MATCHED THEN
  UPDATE SET
    t.raw_payload = src.raw_payload,
    t.source_file = src.source_file,
    t.rejected_at = src.rejected_at
WHEN NOT MATCHED THEN
  INSERT (
    claim_id, member_id, provider_id, service_date, claim_amount,
    reject_reason, raw_payload, source_file, run_date, rejected_at
  )
  VALUES (
    src.claim_id, src.member_id, src.provider_id, src.service_date, src.claim_amount,
    src.reject_reason, src.raw_payload, src.source_file, src.run_date, src.rejected_at
  );


-- ---------------------------------------------------------------------
-- 7. mart.provider_spend — daily spend with a rolling z-score.
--
--    THE ROLLING Z-SCORE.
--
--    A provider's spend on a given day is anomalous if it deviates
--    from that provider's OWN recent history. Comparing every provider
--    to a global average would flag a large hospital every day.
--
--    The z-score is:
--        z = (x - mean(window)) / stddev(window)
--
--    where the window is the TRAILING 30 days for that provider,
--    EXCLUDING the current row. Including the current row would pull
--    the mean toward the value being tested, shrinking the z-score and
--    making real anomalies harder to detect.
--
--    The RANGE BETWEEN 29 PRECEDING AND 1 PRECEDING frame does exactly
--    that exclusion. There is no way to express "the previous 29 rows
--    but not this one" with a single unbounded frame.
--
--    The frame also needs a MIN_ROWS equivalent: for a provider with
--    only three days of history, a 3-day mean is noise. BigQuery's
--    window functions do not have a min_rows clause, so we filter on
--    the row count explicitly with COUNT(*) OVER (...).
-- ---------------------------------------------------------------------

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID`.mart.provider_spend
PARTITION BY service_date
CLUSTER BY provider_id
OPTIONS(
  description = "Daily provider spend with denial metrics and a 30-day rolling z-score anomaly flag. The window excludes the current row.",
  labels = [("tier", "mart"), ("domain", "healthcare")],
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
) AS
WITH daily AS (
  SELECT
    c.service_date,
    c.provider_id,
    ANY_VALUE(c.provider_name HAVING MAX c.loaded_at) AS provider_name,
    ANY_VALUE(c.provider_type HAVING MAX c.loaded_at) AS provider_type,
    ANY_VALUE(p.state HAVING MAX p.loaded_at) AS provider_state,
    COUNT(*) AS claim_count,
    COUNT(DISTINCT c.member_id) AS member_count,
    SUM(c.claim_amount) AS total_claim_amount,
    COUNTIF(c.is_denied) AS denied_claim_count,
    SUM(IF(c.is_denied, c.claim_amount, 0)) AS denied_amount
  FROM `YOUR_PROJECT_ID`.gold.fact_claims AS c
  LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_provider AS p
    ON c.provider_id = p.provider_npi AND p.is_current
  GROUP BY c.service_date, c.provider_id
),
rolling AS (
  SELECT
    daily.*,
    AVG(total_claim_amount) OVER (
      PARTITION BY provider_id
      ORDER BY service_date
      RANGE BETWEEN INTERVAL 29 DAY PRECEDING AND INTERVAL 1 DAY PRECEDING
    ) AS spend_30d_mean,
    STDDEV_POP(total_claim_amount) OVER (
      PARTITION BY provider_id
      ORDER BY service_date
      RANGE BETWEEN INTERVAL 29 DAY PRECEDING AND INTERVAL 1 DAY PRECEDING
    ) AS spend_30d_stddev,
    COUNT(*) OVER (
      PARTITION BY provider_id
      ORDER BY service_date
      RANGE BETWEEN INTERVAL 29 DAY PRECEDING AND INTERVAL 1 DAY PRECEDING
    ) AS history_days
  FROM daily
),
scored AS (
  SELECT
    rolling.*,
    CASE
      WHEN history_days < 7 THEN NULL
      WHEN spend_30d_stddev IS NULL OR spend_30d_stddev = 0 THEN NULL
      ELSE (total_claim_amount - spend_30d_mean) / spend_30d_stddev
    END AS spend_zscore
  FROM rolling
)
SELECT
  service_date,
  provider_id,
  provider_name,
  provider_type,
  -- ⚠️ A bare `NULL` would be inferred as INT64 by BigQuery, which does
  --    not match the STRING column the table schema declares. Always
  --    CAST a typed NULL.
  CAST(NULL AS STRING) AS region_name,
  provider_state,
  claim_count,
  member_count,
  total_claim_amount,
  SAFE_DIVIDE(total_claim_amount, claim_count) AS avg_claim_amount,
  denied_claim_count,
  SAFE_DIVIDE(denied_claim_count, claim_count) AS denial_rate,
  denied_amount,
  spend_30d_mean,
  spend_30d_stddev,
  spend_zscore,
  CASE
    WHEN spend_zscore IS NULL THEN FALSE
    WHEN ABS(spend_zscore) >= 3 THEN TRUE
    ELSE FALSE
  END AS is_spend_anomaly,
  CASE
    WHEN spend_zscore IS NULL THEN 'NORMAL'
    WHEN spend_zscore >= 3 THEN 'SPIKE'
    WHEN spend_zscore <= -3 THEN 'DUMP'
    ELSE 'NORMAL'
  END AS anomaly_direction,
  CURRENT_TIMESTAMP() AS loaded_at
FROM scored;


-- ---------------------------------------------------------------------
-- 8. The business questions
-- ---------------------------------------------------------------------

-- 8.1 Monthly provider spend — the finance view.
SELECT
  DATE_TRUNC(service_date, MONTH) AS month_start,
  provider_id,
  ANY_VALUE(provider_name HAVING MAX loaded_at) AS provider_name,
  SUM(total_claim_amount) AS total_spend,
  COUNT(*) AS active_days,
  ROUND(SAFE_DIVIDE(SUM(total_claim_amount), COUNT(*)), 2) AS avg_daily_spend
FROM `YOUR_PROJECT_ID`.mart.provider_spend
GROUP BY month_start, provider_id
ORDER BY month_start DESC, total_spend DESC;

-- 8.2 The anomalies. These are the rows a human needs to look at.
SELECT
  service_date,
  provider_id,
  provider_name,
  total_claim_amount,
  spend_30d_mean,
  spend_30d_stddev,
  spend_zscore,
  anomaly_direction,
  claim_count
FROM `YOUR_PROJECT_ID`.mart.provider_spend
WHERE is_spend_anomaly
ORDER BY ABS(spend_zscore) DESC;

-- 8.3 Denial rate by provider type, with the paid/denied split.
SELECT
  provider_type,
  COUNT(*) AS provider_days,
  SUM(total_claim_amount) AS total_claim_amount,
  SUM(denied_amount) AS denied_amount,
  SUM(total_claim_amount) - SUM(denied_amount) AS paid_amount,
  ROUND(SAFE_DIVIDE(SUM(denied_claim_count), SUM(claim_count)), 4) AS denial_rate
FROM `YOUR_PROJECT_ID`.mart.provider_spend
WHERE provider_type IS NOT NULL
GROUP BY provider_type
ORDER BY total_claim_amount DESC;

-- 8.4 Diagnosis code mix, from the fact table.
SELECT
  primary_dx_code,
  d.description,
  d.category,
  COUNT(*) AS claim_count,
  SUM(claim_amount) AS total_claim_amount
FROM `YOUR_PROJECT_ID`.gold.fact_claims AS c
LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_diagnosis AS d
  ON c.primary_dx_code = d.icd10_code AND d.is_current
WHERE c.service_date BETWEEN DATE '2026-10-01' AND DATE '2026-10-27'
GROUP BY primary_dx_code, d.description, d.category
ORDER BY claim_count DESC
LIMIT 20;

-- 8.5 The quarantine report — what failed and why.
SELECT
  reject_reason,
  COUNT(*) AS rejected_claims,
  SUM(claim_amount) AS rejected_amount,
  MIN(run_date) AS first_seen,
  MAX(run_date) AS last_seen
FROM `YOUR_PROJECT_ID`.gold.quarantine_rejected_claims
GROUP BY reject_reason
ORDER BY rejected_claims DESC;

-- 8.6 The reconciliation: fact claims must equal the mart's claim count.
SELECT
  (SELECT COUNT(*) FROM `YOUR_PROJECT_ID`.gold.fact_claims
    WHERE service_date BETWEEN DATE '2026-10-01' AND DATE '2026-10-27') AS fact_claims,
  (SELECT SUM(claim_count) FROM `YOUR_PROJECT_ID`.mart.provider_spend
    WHERE service_date BETWEEN DATE '2026-10-01' AND DATE '2026-10-27') AS mart_claims,
  (SELECT COUNT(*) FROM `YOUR_PROJECT_ID`.gold.fact_claims
    WHERE service_date BETWEEN DATE '2026-10-01' AND DATE '2026-10-27'
    AND is_denied) AS denied_claims,
  (SELECT SUM(denied_claim_count) FROM `YOUR_PROJECT_ID`.mart.provider_spend
    WHERE service_date BETWEEN DATE '2026-10-01' AND DATE '2026-10-27') AS mart_denied,
  CASE
    WHEN (SELECT COUNT(*) FROM `YOUR_PROJECT_ID`.gold.fact_claims
          WHERE service_date BETWEEN DATE '2026-10-01' AND DATE '2026-10-27')
       = (SELECT SUM(claim_count) FROM `YOUR_PROJECT_ID`.mart.provider_spend
          WHERE service_date BETWEEN DATE '2026-10-01' AND DATE '2026-10-27')
    THEN 'PASS'
    ELSE 'FAIL'
  END AS reconciliation;
