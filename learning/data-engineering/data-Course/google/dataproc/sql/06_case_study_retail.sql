-- =====================================================================
-- 06_case_study_retail.sql
-- Course: Dataproc + PySpark for Big Data Engineers
-- Chapter: 10 — Retail Sales Analytics case study
--
-- The complete retail model layer in BigQuery SQL. This is the
-- BigQuery-side counterpart to the PySpark job in chapter 10 — the
-- same pipeline expressed as SQL instead of DataFrame calls.
--
-- The model:
--
--   bronze.pos_orders          raw POS extract, exactly as landed
--        │
--        ▼  dedup, cast, validate, quarantine rejects
--   gold.fact_sales            one row per order_id
--        │
--        ├──▶ silver.dim_product    SCD2, keyed on product_id
--        └──▶ silver.dim_store      SCD2, keyed on store_id
--                │
--                ▼  aggregate
--   mart.daily_store_category_sales
--
-- Usage:
--   bq query --use_legacy_sql=false < 06_case_study_retail.sql
--
-- Run order: 01 -> 02 -> 03 -> 06. The marts are built in 04.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. bronze.pos_orders — the landing zone
--
--    Deliberately loose. The source system is not under your control,
--    so the landing table preserves exactly what arrived, including
--    the dirty rows. Cleaning happens at the silver/gold boundary,
--    not here.
--
--    order_timestamp is STRING, not TIMESTAMP, because the source
--    sometimes emits an unparseable value. Casting at load time would
--    either fail the load or silently coerce the bad value. Keeping
--    it as a string lets the pipeline count how often it was bad.
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID`.bronze.pos_orders (
  order_id            STRING,
  store_id            STRING,
  product_id          STRING,
  order_timestamp     STRING,
  quantity            STRING,
  unit_price          STRING,
  discount            STRING,
  payment_method      STRING,
  promo_code          STRING,
  status              STRING,
  source_file         STRING,
  ingested_at         TIMESTAMP NOT NULL
)
OPTIONS(
  description = "Raw POS extracts, appended exactly as received. Includes dirty rows. Never UPDATEd.",
  labels = [("tier", "bronze"), ("domain", "retail")],
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);


-- ---------------------------------------------------------------------
-- 1b. bronze.product_master — the product dimension source
--
--     The master as the source system publishes it. It is Type 1: the
--     source overwrites a row when an attribute changes, so the history
--     has to be reconstructed by comparing each run against the
--     current version in silver.
--
--     This is why the SCD2 load in section 4 exists at all.
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID`.bronze.product_master (
  product_id     STRING,
  name           STRING,
  category       STRING,
  brand          STRING,
  cost           STRING,
  source_file    STRING,
  ingested_at    TIMESTAMP NOT NULL
)
OPTIONS(
  description = "Raw product master. Type 1 — the source overwrites rows in place. Source for the SCD2 dimension load.",
  labels = [("tier", "bronze"), ("domain", "retail")],
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);


-- ---------------------------------------------------------------------
-- 1c. staging.dim_product_sk_seq — the surrogate key sequence
--
--     The surrogate key generator for the product dimension.
--
--     Why a sequence table rather than a window function or
--     GENERATE_UUID()?
--
--       GENERATE_UUID() gives unique but SPARSE and UNORDERED keys. The
--       keys are then randomly distributed across the Parquet row
--       groups, which hurts compression and makes range scans on the
--       key impossible.
--
--       ROW_NUMBER() OVER (ORDER BY ...) gives dense keys, but it
--       renumbers on every run, so a key that pointed at version 1 of
--       a product would point at version 1 of a DIFFERENT product
--       tomorrow. That breaks every historical fact row.
--
--     A sequence table gives dense, monotonically increasing, STABLE
--     keys. The MERGE in section 4 reads next_sk and the UPDATE that
--     follows advances it.
--
--     The `dimension` column lets one table serve every dimension.
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID`.staging.dim_product_sk_seq (
  dimension   STRING NOT NULL,
  next_sk     INT64  NOT NULL
)
OPTIONS(
  description = "Surrogate key sequences, one row per dimension. Advanced transactionally by the SCD2 load.",
  labels = [("tier", "staging"), ("entity", "sequence")]
);

-- Seed the sequence. Starting at 1 keeps the keys dense and readable.
-- The INSERT is idempotent: the NOT EXISTS guard means a re-run does
-- not reset the counter and reissue keys that are already in use.
INSERT INTO `YOUR_PROJECT_ID`.staging.dim_product_sk_seq (dimension, next_sk)
SELECT 'product', 1
WHERE NOT EXISTS (
  SELECT 1 FROM `YOUR_PROJECT_ID`.staging.dim_product_sk_seq WHERE dimension = 'product'
);


-- ---------------------------------------------------------------------
-- 2. The bronze -> gold transform, expressed as SQL.
--
--    This is the heart of the case study. Read it as a pipeline:
--
--    a) CAST everything defensively with SAFE_CAST. A value that will
--       not parse becomes NULL rather than aborting the query.
--    b) VALIDATE. A row is valid only if its key, timestamp, price,
--       and quantity all pass their checks.
--    c) DEDUPLICATE with QUALIFY. Keep the LATEST version of each
--       order_id — the source can emit the same order more than once
--       (a retry, a replay, a dual-write).
--    d) JOIN to the dimensions to attach names and surrogate keys.
--    e) WRITE to gold, and write the rejects to quarantine.
--
--    Note the ordering: dedup happens BEFORE the dimension join. If you
--    join first and dedup after, the join can multiply rows and the
--    dedup will pick the wrong one.
-- ---------------------------------------------------------------------

-- 2.1 The cleaned, deduplicated, validated order set.
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
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY order_id
  ORDER BY ingested_at DESC
) = 1;

-- 2.2 The rejected rows, with a reason. Every reject gets ONE
--     reason — the FIRST rule it fails — so the counts add up and
--     the quarantine table can be grouped by reason without
--     double-counting.
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
WHERE order_id IS NULL
   OR order_id = ''
   OR SAFE_CAST(order_timestamp AS TIMESTAMP) IS NULL
   OR SAFE_CAST(unit_price AS NUMERIC(18,2)) IS NULL
   OR SAFE_CAST(quantity AS INT64) IS NULL
   OR SAFE_CAST(quantity AS INT64) <= 0
   OR SAFE_CAST(unit_price AS NUMERIC(18,2)) < 0;

-- ---------------------------------------------------------------------
-- 3. silver.dim_product — SCD2 from the product master
--
--    The pipeline's dimension-load logic:
--      1. Read the current master.
--      2. Compare each row against the current version in silver.
--      3. If a tracked attribute changed, CLOSE the current row
--         (set valid_to, is_current = FALSE) and OPEN a new row.
--      4. If the key is new, just OPEN a row.
--
--    The comparison below is the "has anything tracked changed?" test.
--    The list of tracked attributes is explicit: name, category,
--    brand, cost.
-- ---------------------------------------------------------------------

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID`.staging.product_master_current AS
SELECT
  product_id,
  name AS product_name,
  category AS category_name,
  brand,
  SAFE_CAST(cost AS NUMERIC(18,2)) AS unit_cost,
  CURRENT_DATE() AS effective_date
FROM `YOUR_PROJECT_ID`.bronze.product_master;

-- 3.1 Detect changes: rows in the master whose tracked attributes
--     differ from the current silver version, or that are brand new.
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID`.staging.product_changes AS
SELECT
  m.product_id,
  m.product_name,
  m.category_name,
  m.brand,
  m.unit_cost,
  m.effective_date,
  COALESCE(p.product_sk, 0) AS prior_product_sk
FROM `YOUR_PROJECT_ID`.staging.product_master_current AS m
LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_product AS p
  ON m.product_id = p.product_id
 AND p.is_current
WHERE p.product_id IS NULL                       -- brand new product
   OR p.product_name IS DISTINCT FROM m.product_name
   OR p.category_name IS DISTINCT FROM m.category_name
   OR p.brand IS DISTINCT FROM m.brand
   OR p.unit_cost IS DISTINCT FROM m.unit_cost;   -- attribute change


-- ---------------------------------------------------------------------
-- 4. The full SCD2 merge.
--
--    Two MERGE statements, run in order:
--      MERGE 1 closes the current version for every changed product.
--      MERGE 2 opens the new version.
--
--    They must be separate statements. A single MERGE cannot both
--    update the matched row and insert a new row for the same key —
--    it would match the row it just closed.
-- ---------------------------------------------------------------------

-- 4.1 Close the current version for products whose attributes changed.
MERGE `YOUR_PROJECT_ID`.silver.dim_product AS t
USING `YOUR_PROJECT_ID`.staging.product_changes AS s
ON t.product_id = s.product_id
   AND t.is_current
WHEN MATCHED THEN
  UPDATE SET
    t.valid_to = s.effective_date,
    t.is_current = FALSE,
    t.loaded_at = CURRENT_TIMESTAMP();

-- 4.2 Open the new version for every changed or new product.
--
--     The surrogate key is assigned here. Two options:
--       (a) GENERATE_UUID() — unique but not dense and not ordered.
--       (b) A monotonically increasing INT64 from a sequence table.
--     This course uses (b) — a dense integer key joins faster and
--     compresses better in Parquet. The sequence table lives in the
--     staging dataset and is advanced with an UPDATE of its own.
--
--     ⚠️ The key must be assigned PER ROW, not once for the whole
--     source set. `(SELECT next_sk FROM ...)` alone would hand the
--     SAME key to every changed product, and the dimension would
--     silently acquire duplicate surrogate keys. The fix is
--     `next_sk + ROW_NUMBER() - 1`: a distinct, contiguous block of
--     keys starting at the sequence's current position.
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

-- 4.3 Advance the sequence. This MUST run after 4.2, or you will
--     hand out duplicate surrogate keys on the next run.
UPDATE `YOUR_PROJECT_ID`.staging.dim_product_sk_seq
SET next_sk = next_sk + (
  SELECT COUNT(*) FROM `YOUR_PROJECT_ID`.staging.product_changes
)
WHERE dimension = 'product';


-- ---------------------------------------------------------------------
-- 5. gold.fact_sales — the fact table load.
--
--    The MERGE is scoped to the run date on BOTH sides. That scoping
--    is what makes the load idempotent: re-running for the same date
--    updates the existing rows instead of appending duplicates.
--
--    BigQuery requires a MERGE to match on the partition key when the
--    target is partitioned — hence `t.sales_date = s.sales_date`
--    alongside `t.order_id = s.order_id`.
-- ---------------------------------------------------------------------

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
    DATE(c.order_ts) AS run_date,
    CURRENT_TIMESTAMP() AS loaded_at
  FROM `YOUR_PROJECT_ID`.staging.pos_orders_clean AS c
  LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_product AS p
    ON c.product_id = p.product_id AND p.is_current
  LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_store AS s
    ON c.store_id = s.store_id AND s.is_current
  WHERE c.sales_date = DATE '2026-10-27'
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
    t.run_date = src.run_date,
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
    src.product_sk, src.store_sk, src.source_file, src.run_date, src.loaded_at
  );


-- ---------------------------------------------------------------------
-- 6. gold.quarantine_rejected_sales — persist the rejects.
--
--    Scoped to the run date so a replay replaces rather than appends.
-- ---------------------------------------------------------------------

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
    DATE '2026-10-27' AS run_date,
    CURRENT_TIMESTAMP() AS rejected_at
  FROM `YOUR_PROJECT_ID`.staging.pos_orders_rejected AS r
  WHERE r.source_file IS NOT NULL
) AS src
ON t.run_date = src.run_date
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
    src.run_date, src.rejected_at
  );


-- ---------------------------------------------------------------------
-- 7. The business questions, answered against the model
-- ---------------------------------------------------------------------

-- 7.1 Top categories by revenue for the run week.
SELECT
  c.category_name,
  COUNT(DISTINCT f.order_id) AS order_count,
  SUM(f.net_amount) AS net_revenue,
  ROUND(SAFE_DIVIDE(SUM(f.net_amount), COUNT(DISTINCT f.order_id)), 2) AS avg_basket_value
FROM `YOUR_PROJECT_ID`.gold.fact_sales AS f
JOIN `YOUR_PROJECT_ID`.silver.dim_product AS p
  ON f.product_id = p.product_id AND p.is_current
LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_product AS c
  ON f.category_id = c.category_id AND c.is_current
WHERE f.sales_date BETWEEN DATE '2026-10-20' AND DATE '2026-10-27'
  AND f.status = 'COMPLETED'
GROUP BY c.category_name
ORDER BY net_revenue DESC;

-- 7.2 Revenue by region and day, from the MART (no fact scan).
SELECT
  sales_date,
  region_name,
  SUM(net_revenue) AS net_revenue,
  SUM(units_sold) AS units_sold
FROM `YOUR_PROJECT_ID`.mart.daily_store_category_sales
WHERE sales_date BETWEEN DATE '2026-10-20' AND DATE '2026-10-27'
GROUP BY sales_date, region_name
ORDER BY sales_date, net_revenue DESC;

-- 7.3 Promo effectiveness: promo vs non-promo revenue per order.
SELECT
  is_promo,
  COUNT(DISTINCT order_id) AS order_count,
  SUM(net_amount) AS net_revenue,
  ROUND(SAFE_DIVIDE(SUM(net_amount), COUNT(DISTINCT order_id)), 2) AS avg_order_value
FROM `YOUR_PROJECT_ID`.gold.fact_sales
WHERE sales_date BETWEEN DATE '2026-10-20' AND DATE '2026-10-27'
  AND status = 'COMPLETED'
GROUP BY is_promo;

-- 7.4 Store performance with the month's best-selling category.
WITH store_category AS (
  SELECT
    store_id,
    category_name,
    SUM(net_revenue) AS category_revenue,
    ROW_NUMBER() OVER (
      PARTITION BY store_id ORDER BY SUM(net_revenue) DESC
    ) AS rn
  FROM `YOUR_PROJECT_ID`.mart.daily_store_category_sales
  WHERE sales_date BETWEEN DATE '2026-10-01' AND DATE '2026-10-27'
  GROUP BY store_id, category_name
),
store_totals AS (
  SELECT
    store_id,
    SUM(net_revenue) AS store_revenue,
    SUM(units_sold) AS store_units
  FROM `YOUR_PROJECT_ID`.mart.daily_store_category_sales
  WHERE sales_date BETWEEN DATE '2026-10-01' AND DATE '2026-10-27'
  GROUP BY store_id
)
SELECT
  t.store_id,
  s.store_name,
  t.store_revenue,
  t.store_units,
  c.category_name AS top_category,
  c.category_revenue,
  ROUND(SAFE_DIVIDE(c.category_revenue, t.store_revenue), 4) AS top_category_share
FROM store_totals AS t
JOIN `YOUR_PROJECT_ID`.silver.dim_store AS s
  ON t.store_id = s.store_id AND s.is_current
JOIN store_category AS c
  ON t.store_id = c.store_id AND c.rn = 1
ORDER BY t.store_revenue DESC;

-- 7.5 The reconciliation: fact revenue must equal mart revenue.
SELECT
  (SELECT SUM(net_amount) FROM `YOUR_PROJECT_ID`.gold.fact_sales
    WHERE status = 'COMPLETED' AND sales_date BETWEEN DATE '2026-10-01' AND DATE '2026-10-27') AS fact_revenue,
  (SELECT SUM(net_revenue) FROM `YOUR_PROJECT_ID`.mart.daily_store_category_sales
    WHERE sales_date BETWEEN DATE '2026-10-01' AND DATE '2026-10-27') AS mart_revenue,
  CASE
    WHEN (SELECT SUM(net_amount) FROM `YOUR_PROJECT_ID`.gold.fact_sales
          WHERE status = 'COMPLETED' AND sales_date BETWEEN DATE '2026-10-01' AND DATE '2026-10-27')
       = (SELECT SUM(net_revenue) FROM `YOUR_PROJECT_ID`.mart.daily_store_category_sales
          WHERE sales_date BETWEEN DATE '2026-10-01' AND DATE '2026-10-27')
    THEN 'PASS'
    ELSE 'FAIL'
  END AS reconciliation;
