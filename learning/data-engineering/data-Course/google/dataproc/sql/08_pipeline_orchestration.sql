-- =====================================================================
-- 08_pipeline_orchestration.sql
-- Course: Dataproc + PySpark for Big Data Engineers
--
-- A multi-statement BigQuery SCRIPT that chains the whole pipeline:
--
--   staging -> merge -> aggregate -> mart refresh
--
-- It demonstrates three things that matter in production:
--
--   1. DECLARE variables. The run date is a VARIABLE, never a literal
--      baked into the SQL. That is what makes a backfill possible:
--      change one line, run the script for 2026-09-01 instead.
--
--   2. Idempotent re-runs. Every write is either a CREATE OR REPLACE
--      (full rebuild) or a partition-scoped MERGE (upsert). Running
--      the script twice produces the same state as running it once.
--
--   3. Explicit control flow. IF/ELSE lets the script skip work that
--      is not needed and FAIL FAST when a precondition is not met.
--
-- Usage:
--   bq query --use_legacy_sql=false \
--     --script=08_pipeline_orchestration.sql \
--     --run_in_transaction=false
--
--   Or with parameters instead of editing the file:
--   bq query --use_legacy_sql=false \
--     "DECLARE run_date DATE DEFAULT CURRENT_DATE(); BEGIN CALL ...; END;" \
--     --script_uris=gs://bucket/08_pipeline_orchestration.sql
--
-- ⚠️ IMPORTANT: run with --run_in_transaction=false. BigQuery DDL
-- (CREATE TABLE, CREATE SCHEMA) cannot execute inside a transaction,
-- and the default for --run_in_transaction is TRUE for scripts.
-- =====================================================================

DECLARE project_id STRING DEFAULT 'YOUR_PROJECT_ID';
DECLARE run_date DATE DEFAULT DATE '2026-10-27';
DECLARE dim_product STRING DEFAULT 'silver.dim_product';
DECLARE dim_store STRING DEFAULT 'silver.dim_store';
DECLARE fact_sales STRING DEFAULT 'gold.fact_sales';
DECLARE mart_daily STRING DEFAULT 'mart.daily_store_category_sales';
DECLARE quarantine_table STRING DEFAULT 'gold.quarantine_rejected_sales';

-- Counters, so the final SELECT reports what the run actually did.
DECLARE rows_staged INT64 DEFAULT 0;
DECLARE rows_quarantined INT64 DEFAULT 0;
DECLARE rows_merged INT64 DEFAULT 0;
DECLARE rows_marted INT64 DEFAULT 0;

BEGIN

  -- -------------------------------------------------------------------
  -- STEP 0: Guard rails
  --
  -- A pipeline that proceeds on bad input produces bad output. These
  -- checks are the script's version of the PySpark assertions.
  -- -------------------------------------------------------------------

  -- Refuse to run if the project ID was never substituted.
  IF project_id = 'YOUR_PROJECT_ID' THEN
    RAISE EXCEPTION
      'project_id is still the placeholder. Edit the DECLARE at the top of this script.';
  END IF;

  -- Refuse to run for a future date. A backfill goes backwards; a
  -- forward run loads tomorrow's data, which is always a bug.
  IF run_date > CURRENT_DATE() THEN
    RAISE EXCEPTION 'run_date % is in the future', run_date;
  END IF;

  -- -------------------------------------------------------------------
  -- STEP 1: STAGING
  --
  -- Rebuild the cleaned intermediate from the landing zone. The
  -- landing zone is append-only; the staging table is disposable and
  -- is rebuilt from scratch every run.
  --
  -- CREATE OR REPLACE is idempotent by construction: it drops the old
  -- table and writes a new one. There is no path by which a second run
  -- accumulates rows.
  -- -------------------------------------------------------------------

  CREATE OR REPLACE TABLE `YOUR_PROJECT_ID`.staging.pos_orders_clean AS
  SELECT
    order_id,
    SAFE_CAST(order_timestamp AS TIMESTAMP) AS order_ts,
    DATE(SAFE_CAST(order_timestamp AS TIMESTAMP)) AS sales_date,
    store_id,
    product_id,
    SAFE_CAST(quantity AS INT64) AS quantity,
    SAFE_CAST(unit_price AS NUMERIC(18,2)) AS unit_price,
    SAFE_CAST(discount AS NUMERIC(18,2)) AS discount_amount,
    SAFE_CAST(unit_price AS NUMERIC(18,2)) * SAFE_CAST(quantity AS INT64) AS gross_amount,
    (SAFE_CAST(unit_price AS NUMERIC(18,2)) * SAFE_CAST(quantity AS INT64))
      - SAFE_CAST(discount AS NUMERIC(18,2)) AS net_amount,
    payment_method,
    promo_code,
    status,
    source_file,
    CURRENT_TIMESTAMP() AS loaded_at
  FROM `YOUR_PROJECT_ID`.bronze.pos_orders
  WHERE order_id IS NOT NULL
    AND order_id != ''
    AND DATE(SAFE_CAST(order_timestamp AS TIMESTAMP)) = run_date
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY order_id
    ORDER BY ingested_at DESC
  ) = 1;

  SET rows_staged = (SELECT COUNT(*) FROM `YOUR_PROJECT_ID`.staging.pos_orders_clean);

  -- The rejects, with exactly one reason each.
  CREATE OR REPLACE TABLE `YOUR_PROJECT_ID`.staging.pos_orders_rejected AS
  SELECT
    order_id,
    store_id,
    product_id,
    order_timestamp,
    quantity,
    unit_price,
    discount,
    source_file,
    CASE
      WHEN order_id IS NULL OR order_id = '' THEN 'MISSING_ORDER_ID'
      WHEN SAFE_CAST(order_timestamp AS TIMESTAMP) IS NULL THEN 'UNPARSEABLE_TIMESTAMP'
      WHEN SAFE_CAST(unit_price AS NUMERIC(18,2)) IS NULL THEN 'UNPARSEABLE_PRICE'
      WHEN SAFE_CAST(quantity AS INT64) IS NULL THEN 'UNPARSEABLE_QUANTITY'
      WHEN SAFE_CAST(quantity AS INT64) <= 0 THEN 'NON_POSITIVE_QUANTITY'
      WHEN SAFE_CAST(unit_price AS NUMERIC(18,2)) < 0 THEN 'NEGATIVE_PRICE'
      ELSE 'UNKNOWN'
    END AS reject_reason,
    CURRENT_TIMESTAMP() AS rejected_at
  FROM `YOUR_PROJECT_ID`.bronze.pos_orders
  WHERE DATE(SAFE_CAST(order_timestamp AS TIMESTAMP)) = run_date
     OR order_id IS NULL
     OR order_id = ''
     OR SAFE_CAST(order_timestamp AS TIMESTAMP) IS NULL
     OR SAFE_CAST(unit_price AS NUMERIC(18,2)) IS NULL
     OR SAFE_CAST(quantity AS INT64) IS NULL
     OR SAFE_CAST(quantity AS INT64) <= 0
     OR SAFE_CAST(unit_price AS NUMERIC(18,2)) < 0;

  SET rows_quarantined = (SELECT COUNT(*) FROM `YOUR_PROJECT_ID`.staging.pos_orders_rejected);

  -- -------------------------------------------------------------------
  -- STEP 2: THE DIMENSION LOAD (SCD2)
  --
  -- Close the current version for changed products, then open the new
  -- one. Two separate MERGEs, in this order.
  --
  -- The surrogate key sequence is seeded here if it is missing. The
  -- NOT EXISTS guard makes the seed idempotent — a re-run does not
  -- reset the counter and reissue keys that are already in use.
  -- -------------------------------------------------------------------

  INSERT INTO `YOUR_PROJECT_ID`.staging.dim_product_sk_seq (dimension, next_sk)
  SELECT 'product', 1
  WHERE NOT EXISTS (
    SELECT 1 FROM `YOUR_PROJECT_ID`.staging.dim_product_sk_seq WHERE dimension = 'product'
  );

  CREATE OR REPLACE TABLE `YOUR_PROJECT_ID`.staging.product_changes AS
  SELECT
    m.product_id,
    m.product_name,
    m.category_name,
    m.brand,
    m.unit_cost,
    run_date AS effective_date
  FROM (
    SELECT
      product_id,
      name AS product_name,
      category AS category_name,
      brand,
      SAFE_CAST(cost AS NUMERIC(18,2)) AS unit_cost
    FROM `YOUR_PROJECT_ID`.bronze.product_master
  ) AS m
  LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_product AS p
    ON m.product_id = p.product_id
   AND p.is_current
  WHERE p.product_id IS NULL
     OR p.product_name IS DISTINCT FROM m.product_name
     OR p.category_name IS DISTINCT FROM m.category_name
     OR p.brand IS DISTINCT FROM m.brand
     OR p.unit_cost IS DISTINCT FROM m.unit_cost;

  -- 2.1 Close the current version.
  MERGE `YOUR_PROJECT_ID`.silver.dim_product AS t
  USING `YOUR_PROJECT_ID`.staging.product_changes AS s
  ON t.product_id = s.product_id
     AND t.is_current
  WHEN MATCHED THEN
    UPDATE SET
      t.valid_to = s.effective_date,
      t.is_current = FALSE,
      t.loaded_at = CURRENT_TIMESTAMP();

  -- 2.2 Open the new version.
  --
  --     The surrogate key is assigned PER ROW. A bare
  --     `(SELECT next_sk FROM ...)` would give every changed product
  --     the SAME key, silently creating duplicate surrogate keys.
  --     `next_sk + ROW_NUMBER() - 1` hands out a distinct, contiguous
  --     block of keys instead.
  MERGE `YOUR_PROJECT_ID`.silver.dim_product AS t
  USING (
    SELECT
      s.product_id,
      s.product_name,
      s.category_name,
      s.brand,
      s.unit_cost,
      s.effective_date,
      seq.next_sk + ROW_NUMBER() OVER (ORDER BY s.product_id) - 1 AS product_sk
    FROM `YOUR_PROJECT_ID`.staging.product_changes AS s
    CROSS JOIN (
      SELECT next_sk FROM `YOUR_PROJECT_ID`.staging.dim_product_sk_seq
      WHERE dimension = 'product'
    ) AS seq
  ) AS src
  ON t.product_id = src.product_id
     AND t.is_current
  WHEN NOT MATCHED THEN
    INSERT (
      product_sk, product_id, product_name, category_name, brand,
      unit_cost, valid_from, valid_to, is_current, loaded_at
    )
    VALUES (
      src.product_sk, src.product_id, src.product_name, src.category_name, src.brand,
      src.unit_cost, src.effective_date, NULL, TRUE, CURRENT_TIMESTAMP()
    );

  -- 2.3 Advance the sequence. MUST come after 2.2.
  UPDATE `YOUR_PROJECT_ID`.staging.dim_product_sk_seq
  SET next_sk = next_sk + (
    SELECT COUNT(*) FROM `YOUR_PROJECT_ID`.staging.product_changes
  )
  WHERE dimension = 'product';

  -- -------------------------------------------------------------------
  -- STEP 3: THE FACT MERGE
  --
  -- Scoped to run_date on both sides. Re-running for the same date
  -- updates the existing rows rather than appending duplicates.
  -- -------------------------------------------------------------------

  MERGE `YOUR_PROJECT_ID`.gold.fact_sales AS t
  USING (
    SELECT
      c.order_id,
      c.order_ts,
      c.sales_date,
      c.store_id,
      c.product_id,
      p.category_id,
      p.category_name,
      p.product_name,
      s.region_id,
      s.region_name,
      c.quantity,
      c.unit_price,
      c.discount_amount,
      CAST(0 AS NUMERIC(18,2)) AS tax_amount,
      c.net_amount,
      c.payment_method,
      c.promo_code,
      c.status,
      c.promo_code IS NOT NULL AND c.promo_code != '' AS is_promo,
      p.product_sk,
      s.store_sk,
      c.source_file,
      run_date AS fact_run_date,
      CURRENT_TIMESTAMP() AS loaded_at
    FROM `YOUR_PROJECT_ID`.staging.pos_orders_clean AS c
    LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_product AS p
      ON c.product_id = p.product_id AND p.is_current
    LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_store AS s
      ON c.store_id = s.store_id AND s.is_current
    WHERE c.sales_date = run_date
  ) AS src
  ON t.order_id = src.order_id
     AND t.sales_date = src.sales_date
  WHEN MATCHED THEN
    UPDATE SET
      t.order_ts = src.order_ts,
      t.store_id = src.store_id,
      t.product_id = src.product_id,
      t.category_id = src.category_id,
      t.category_name = src.category_name,
      t.product_name = src.product_name,
      t.region_id = src.region_id,
      t.region_name = src.region_name,
      t.quantity = src.quantity,
      t.unit_price = src.unit_price,
      t.discount_amount = src.discount_amount,
      t.tax_amount = src.tax_amount,
      t.net_amount = src.net_amount,
      t.payment_method = src.payment_method,
      t.promo_code = src.promo_code,
      t.status = src.status,
      t.is_promo = src.is_promo,
      t.product_sk = src.product_sk,
      t.store_sk = src.store_sk,
      t.source_file = src.source_file,
      t.run_date = src.fact_run_date,
      t.loaded_at = src.loaded_at
  WHEN NOT MATCHED THEN
    INSERT (
      order_id, order_ts, sales_date, store_id, product_id,
      category_id, category_name, product_name, region_id, region_name,
      quantity, unit_price, discount_amount, tax_amount, net_amount,
      payment_method, promo_code, status, is_promo,
      product_sk, store_sk, source_file, run_date, loaded_at
    )
    VALUES (
      src.order_id, src.order_ts, src.sales_date, src.store_id, src.product_id,
      src.category_id, src.category_name, src.product_name, src.region_id, src.region_name,
      src.quantity, src.unit_price, src.discount_amount, src.tax_amount, src.net_amount,
      src.payment_method, src.promo_code, src.status, src.is_promo,
      src.product_sk, src.store_sk, src.source_file, src.fact_run_date, src.loaded_at
    );

  SET rows_merged = (SELECT COUNT(*) FROM `YOUR_PROJECT_ID`.gold.fact_sales
                     WHERE sales_date = run_date);

  -- -------------------------------------------------------------------
  -- STEP 4: THE QUARANTINE MERGE
  -- -------------------------------------------------------------------

  MERGE `YOUR_PROJECT_ID`.gold.quarantine_rejected_sales AS t
  USING (
    SELECT
      r.order_id,
      r.store_id,
      r.product_id,
      r.order_timestamp,
      r.quantity,
      r.unit_price,
      r.discount,
      r.reject_reason,
      TO_JSON_STRING(STRUCT(
        r.order_id, r.store_id, r.product_id, r.order_timestamp,
        r.quantity, r.unit_price, r.discount
      )) AS raw_payload,
      r.source_file,
      run_date AS reject_run_date,
      CURRENT_TIMESTAMP() AS rejected_at
    FROM `YOUR_PROJECT_ID`.staging.pos_orders_rejected AS r
  ) AS src
  ON t.run_date = src.reject_run_date
     AND t.order_id = src.order_id
     AND t.reject_reason = src.reject_reason
  WHEN MATCHED THEN
    UPDATE SET
      t.raw_payload = src.raw_payload,
      t.source_file = src.source_file,
      t.rejected_at = src.rejected_at
  WHEN NOT MATCHED THEN
    INSERT (
      order_id, store_id, product_id, order_timestamp, quantity,
      unit_price, discount, reject_reason, raw_payload, source_file,
      run_date, rejected_at
    )
    VALUES (
      src.order_id, src.store_id, src.product_id, src.order_timestamp, src.quantity,
      src.unit_price, src.discount, src.reject_reason, src.raw_payload, src.source_file,
      src.reject_run_date, src.rejected_at
    );

  -- -------------------------------------------------------------------
  -- STEP 5: THE MART REFRESH
  --
  -- Full rebuild. For a mart large enough that a full rebuild is
  -- expensive, replace this with a partition-scoped MERGE keyed on
  -- sales_date — same idempotency guarantee, a fraction of the cost.
  --
  -- The join to dim_product is restricted to is_current. Without that
  -- filter the join fans out: a product with three versions would
  -- triple its fact rows.
  -- -------------------------------------------------------------------

  CREATE OR REPLACE TABLE `YOUR_PROJECT_ID`.mart.daily_store_category_sales
  PARTITION BY sales_date
  CLUSTER BY store_id, category_id
  OPTIONS(
    description = "Daily revenue by store and category. Rebuilt by 08_pipeline_orchestration.sql.",
    labels = [("tier", "mart"), ("domain", "retail")]
  ) AS
  SELECT
    f.sales_date,
    f.store_id,
    ANY_VALUE(s.store_name HAVING MAX s.loaded_at) AS store_name,
    ANY_VALUE(f.region_id HAVING MAX f.loaded_at) AS region_id,
    ANY_VALUE(f.region_name HAVING MAX f.loaded_at) AS region_name,
    f.category_id,
    ANY_VALUE(f.category_name HAVING MAX f.loaded_at) AS category_name,
    COUNT(DISTINCT f.order_id) AS order_count,
    SUM(f.quantity) AS units_sold,
    SUM(f.quantity * f.unit_price) AS gross_amount,
    SUM(f.discount_amount) AS discount_amount,
    SUM(f.net_amount) AS net_revenue,
    SUM(f.tax_amount) AS tax_amount,
    SAFE_DIVIDE(SUM(f.net_amount), COUNT(DISTINCT f.order_id)) AS avg_basket_value,
    SAFE_DIVIDE(SUM(f.quantity), COUNT(DISTINCT f.order_id)) AS avg_units_per_basket,
    COUNTIF(f.is_promo) AS promo_order_count,
    SUM(IF(f.is_promo, f.net_amount, 0)) AS promo_revenue,
    CURRENT_TIMESTAMP() AS loaded_at
  FROM `YOUR_PROJECT_ID`.gold.fact_sales AS f
  LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_product AS p
    ON f.product_id = p.product_id AND p.is_current
  LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_store AS s
    ON f.store_id = s.store_id AND s.is_current
  WHERE f.status = 'COMPLETED'
    AND f.net_amount IS NOT NULL
  GROUP BY f.sales_date, f.store_id, f.category_id;

  SET rows_marted = (SELECT COUNT(*) FROM `YOUR_PROJECT_ID`.mart.daily_store_category_sales);

  -- -------------------------------------------------------------------
  -- STEP 6: POST-RUN VALIDATION
  --
  -- The script checks its own output. If the reconciliation fails,
  -- the whole script fails and the caller knows something went wrong
  -- without reading the logs.
  -- -------------------------------------------------------------------

  -- 6.1 No duplicate keys in the fact for the run date.
  IF (
    SELECT COUNT(*) - COUNT(DISTINCT order_id)
    FROM `YOUR_PROJECT_ID`.gold.fact_sales
    WHERE sales_date = run_date
  ) > 0 THEN
    RAISE EXCEPTION
      'Duplicate order_ids in gold.fact_sales for %', run_date;
  END IF;

  -- 6.2 Fact revenue must equal mart revenue.
  IF (
    SELECT SUM(net_amount)
    FROM `YOUR_PROJECT_ID`.gold.fact_sales
    WHERE status = 'COMPLETED'
  ) != (
    SELECT SUM(net_revenue)
    FROM `YOUR_PROJECT_ID`.mart.daily_store_category_sales
  ) THEN
    RAISE EXCEPTION
      'Reconciliation failed: gold.fact_sales net_amount <> mart.daily_store_category_sales net_revenue';
  END IF;

  -- 6.3 No orphan dimensions.
  IF (
    SELECT COUNT(*)
    FROM `YOUR_PROJECT_ID`.gold.fact_sales AS f
    LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_product AS p
      ON f.product_id = p.product_id AND p.is_current
    WHERE p.product_id IS NULL
      AND f.sales_date = run_date
  ) > 0 THEN
    RAISE EXCEPTION
      'Orphan product_ids in gold.fact_sales for %', run_date;
  END IF;

  -- 6.4 The quarantine rate must be under the agreed threshold.
  IF (
    SELECT SAFE_DIVIDE(rows_quarantined, rows_staged + rows_quarantined)
  ) > 0.05 THEN
    RAISE EXCEPTION
      'Quarantine rate exceeded 5%%: % of % rows rejected',
      rows_quarantined, rows_staged + rows_quarantined;
  END IF;

  -- -------------------------------------------------------------------
  -- STEP 7: The run report.
  --
  -- This is the script's return value. The orchestrator that called
  -- the script reads these counts to decide whether to alert.
  -- -------------------------------------------------------------------

  SELECT
    run_date,
    project_id,
    rows_staged,
    rows_quarantined,
    rows_merged,
    rows_marted,
    SAFE_DIVIDE(rows_quarantined, rows_staged + rows_quarantined) AS quarantine_rate,
    (SELECT COUNT(*) FROM `YOUR_PROJECT_ID`.gold.fact_sales
     WHERE sales_date = run_date) AS fact_rows_verified,
    (SELECT COUNT(DISTINCT order_id) FROM `YOUR_PROJECT_ID`.gold.fact_sales
     WHERE sales_date = run_date) AS distinct_orders_verified,
    'SUCCESS' AS run_status;

END;


-- =====================================================================
-- APPENDIX: A partition-scoped MERGE refresh for the mart.
--
-- Use this instead of the full rebuild in STEP 5 when the mart is
-- large enough that rebuilding it all is wasteful. It refreshes ONE
-- partition (one day) and leaves the rest untouched — same
-- idempotency guarantee, a fraction of the bytes scanned.
--
-- ⚠️ A MERGE on a partitioned target must match on the partition key.
--    That is why the ON clause includes sales_date.
-- =====================================================================

-- MERGE `YOUR_PROJECT_ID`.mart.daily_store_category_sales AS t
-- USING (
--   SELECT
--     f.sales_date,
--     f.store_id,
--     f.category_id,
--     ANY_VALUE(f.category_name HAVING MAX f.loaded_at) AS category_name,
--     ANY_VALUE(f.region_id HAVING MAX f.loaded_at) AS region_id,
--     ANY_VALUE(f.region_name HAVING MAX f.loaded_at) AS region_name,
--     COUNT(DISTINCT f.order_id) AS order_count,
--     SUM(f.quantity) AS units_sold,
--     SUM(f.quantity * f.unit_price) AS gross_amount,
--     SUM(f.discount_amount) AS discount_amount,
--     SUM(f.net_amount) AS net_revenue,
--     SUM(f.tax_amount) AS tax_amount,
--     CURRENT_TIMESTAMP() AS loaded_at
--   FROM `YOUR_PROJECT_ID`.gold.fact_sales AS f
--   WHERE f.sales_date = DATE '2026-10-27'
--     AND f.status = 'COMPLETED'
--   GROUP BY f.sales_date, f.store_id, f.category_id
-- ) AS s
-- ON t.sales_date = s.sales_date
--    AND t.store_id = s.store_id
--    AND t.category_id = s.category_id
-- WHEN MATCHED THEN
--   UPDATE SET
--     t.order_count = s.order_count,
--     t.units_sold = s.units_sold,
--     t.gross_amount = s.gross_amount,
--     t.discount_amount = s.discount_amount,
--     t.net_revenue = s.net_revenue,
--     t.tax_amount = s.tax_amount,
--     t.loaded_at = s.loaded_at
-- WHEN NOT MATCHED THEN
--   INSERT (
--     sales_date, store_id, category_id, category_name, region_id,
--     region_name, order_count, units_sold, gross_amount, discount_amount,
--     net_revenue, tax_amount, loaded_at
--   )
--   VALUES (
--     s.sales_date, s.store_id, s.category_id, s.category_name, s.region_id,
--     s.region_name, s.order_count, s.units_sold, s.gross_amount, s.discount_amount,
--     s.net_revenue, s.tax_amount, s.loaded_at
--   );
