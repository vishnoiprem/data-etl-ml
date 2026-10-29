-- reconciliation.sql — the nightly safety net.
--
-- Compares the CDC destination in BigQuery against a nightly extract of
-- the source, and returns ONLY the rows that differ.
--
-- This is the check that catches everything the pipeline's own metrics
-- miss: a wrong merge key, a dropped event, a failed delete, a schema
-- change. It compares VALUES, never counts — a row-count check passes
-- with a wrong merge key, because the count stays plausible.
--
-- Run with:
--   bq query --use_legacy_sql=false --max_rows 100 < sql/reconciliation.sql
--
-- The source side is a table you refresh nightly:
--   CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.datastream.customers_source_snapshot` AS
--   SELECT * FROM `YOUR_PROJECT_ID.reconciliation.customers_source`;

WITH
source AS (
    SELECT
        customer_id,
        first_name,
        last_name,
        email,
        region,
        tier
    FROM `YOUR_PROJECT_ID.datastream.customers_source_snapshot`
),

destination AS (
    SELECT
        customer_id,
        first_name,
        last_name,
        email,
        region,
        tier
    FROM `YOUR_PROJECT_ID.datastream.customers`
),

-- Rows the source has and the destination does not.
missing AS (
    SELECT
        'MISSING_IN_DESTINATION' AS discrepancy,
        s.customer_id,
        s.first_name,
        s.last_name,
        s.email,
        s.region,
        s.tier
    FROM source s
    LEFT JOIN destination d USING (customer_id)
    WHERE d.customer_id IS NULL
),

-- Rows the destination has and the source does not. Usually a delete
-- that was never applied, or a row from a previous table state.
extra AS (
    SELECT
        'EXTRA_IN_DESTINATION' AS discrepancy,
        d.customer_id,
        d.first_name,
        d.last_name,
        d.email,
        d.region,
        d.tier
    FROM destination d
    LEFT JOIN source s USING (customer_id)
    WHERE s.customer_id IS NULL
),

-- Rows present in both, but with different values. This is where a wrong
-- merge key shows up — usually as a large number of rows differing in a
-- field that was overwritten.
differing AS (
    SELECT
        'VALUE_MISMATCH' AS discrepancy,
        s.customer_id,
        s.first_name,
        s.last_name,
        s.email,
        s.region,
        s.tier
    FROM source s
    JOIN destination d USING (customer_id)
    WHERE s.first_name  IS DISTINCT FROM d.first_name
       OR s.last_name   IS DISTINCT FROM d.last_name
       OR s.email       IS DISTINCT FROM d.email
       OR s.region      IS DISTINCT FROM d.region
       OR s.tier        IS DISTINCT FROM d.tier
)

SELECT * FROM missing
UNION ALL
SELECT * FROM extra
UNION ALL
SELECT * FROM differing
ORDER BY discrepancy, customer_id;
