-- =====================================================================
-- 04_marts_and_aggregates.sql
-- Course: Dataproc + PySpark for Big Data Engineers
--
-- The MART layer: business-facing aggregates.
--
-- A mart table exists to answer a question without the BI layer ever
-- touching the fact table. The dashboard query "revenue by store by
-- category by day" against gold.fact_sales scans every transaction row
-- every time. Against mart.daily_store_category_sales it scans a few
-- thousand rows. That is the whole point.
--
-- Refresh pattern used here:
--   CREATE OR REPLACE TABLE ... AS SELECT ...
-- which is a full rebuild. It is idempotent by construction — running
-- it twice produces the same table. For large marts, switch to a
-- partition-scoped MERGE (see 08_pipeline_orchestration.sql).
--
-- Usage:
--   bq query --use_legacy_sql=false < 04_marts_and_aggregates.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. mart.daily_store_category_sales
--
--    Grain: one row per (sales_date, store_id, category_id).
--    Partitioned by sales_date so a dashboard's default "last 30 days"
--    filter prunes to 30 partitions.
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID`.mart.daily_store_category_sales (
  sales_date            DATE          NOT NULL,
  store_id              STRING        NOT NULL,
  store_name            STRING,
  region_id             STRING,
  region_name           STRING,
  category_id           STRING,
  category_name         STRING,
  order_count           INT64,
  units_sold            INT64,
  gross_amount          NUMERIC(18,2),
  discount_amount       NUMERIC(18,2),
  net_revenue           NUMERIC(18,2),
  tax_amount            NUMERIC(18,2),
  avg_basket_value      NUMERIC(18,2),
  avg_units_per_basket  NUMERIC(18,2),
  promo_order_count     INT64,
  promo_revenue         NUMERIC(18,2),
  loaded_at             TIMESTAMP     NOT NULL
)
PARTITION BY sales_date
CLUSTER BY store_id, category_id
OPTIONS(
  description = "Daily revenue by store and category. Grain: one row per (sales_date, store_id, category_id). Feeds the revenue dashboard.",
  labels = [("tier", "mart"), ("domain", "retail")],
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);

-- ---------------------------------------------------------------------
-- 2. mart.provider_spend_monthly
--
--    Grain: one row per (month_start, provider_id).
--    Monthly, not daily: provider spend is reviewed on a monthly cycle,
--    and a monthly grain keeps the table small enough to query without
--    a partition filter at all.
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID`.mart.provider_spend_monthly (
  month_start           DATE          NOT NULL,
  provider_id           STRING        NOT NULL,
  provider_name         STRING,
  provider_type         STRING,
  provider_state        STRING,
  claim_count           INT64,
  member_count          INT64,
  total_claim_amount    NUMERIC(18,2),
  avg_claim_amount      NUMERIC(18,2),
  denied_claim_count    INT64,
  denial_rate           NUMERIC(9,6),
  denied_amount         NUMERIC(18,2),
  paid_amount           NUMERIC(18,2),
  pct_of_provider_total NUMERIC(9,6),
  loaded_at             TIMESTAMP     NOT NULL
)
PARTITION BY month_start
CLUSTER BY provider_id
OPTIONS(
  description = "Monthly provider spend. Grain: one row per (month_start, provider_id). Denials and paid amounts included.",
  labels = [("tier", "mart"), ("domain", "healthcare")],
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);

-- ---------------------------------------------------------------------
-- 3. mart.provider_spend
--
--    The DAILY companion to mart.provider_spend_monthly above.
--
--    Grain: one row per (service_date, provider_id).
--
--    This table exists because monthly grain is too coarse to spot a
--    provider whose spend suddenly spikes. It carries a 30-day rolling
--    z-score computed against each provider's OWN trailing history —
--    see 07_case_study_healthcare.sql section 7 for the full window
--    frame discussion and why the frame excludes the current row.
--
--    Two tables, two grains, two questions:
--      provider_spend_monthly  -- "how much did this provider cost
--                                  us in Q3?"  (a review-cycle question)
--      provider_spend          -- "is this provider's spend today
--                                  normal for them?"  (a monitoring
--                                  question)
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID`.mart.provider_spend (
  service_date          DATE          NOT NULL,
  provider_id           STRING        NOT NULL,
  provider_name         STRING,
  provider_type         STRING,
  region_name           STRING,
  provider_state        STRING,
  claim_count           INT64,
  member_count          INT64,
  total_claim_amount    NUMERIC(18,2),
  avg_claim_amount      NUMERIC(18,2),
  denied_claim_count    INT64,
  denial_rate           NUMERIC(9,6),
  denied_amount         NUMERIC(18,2),
  spend_30d_mean        NUMERIC(18,2),
  spend_30d_stddev      NUMERIC(18,2),
  spend_zscore          FLOAT64,
  is_spend_anomaly      BOOL,
  anomaly_direction     STRING,
  loaded_at             TIMESTAMP     NOT NULL
)
PARTITION BY service_date
CLUSTER BY provider_id
OPTIONS(
  description = "Daily provider spend with denial metrics and a 30-day rolling z-score anomaly flag. Grain: one row per (service_date, provider_id).",
  labels = [("tier", "mart"), ("domain", "healthcare")],
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);

-- ---------------------------------------------------------------------
-- 4. mart.top_products
--
--    A leaderboard. Grain: one row per (period_date, product_id).
--    Re-ranked every period so "top 10" is a filter on rank, not a
--    window function computed at query time.
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID`.mart.top_products (
  period_date       DATE          NOT NULL,
  product_id        STRING        NOT NULL,
  product_name      STRING,
  category_id       STRING,
  category_name     STRING,
  rank              INT64,
  units_sold        INT64,
  net_revenue       NUMERIC(18,2),
  order_count       INT64,
  revenue_share_pct NUMERIC(9,6),
  loaded_at         TIMESTAMP     NOT NULL
)
PARTITION BY period_date
CLUSTER BY product_id
OPTIONS(
  description = "Product leaderboard per period. Grain: one row per (period_date, product_id). rank is recomputed each period.",
  labels = [("tier", "mart"), ("domain", "retail")],
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
);

-- =====================================================================
-- 5. Refresh logic
-- =====================================================================

-- ---------------------------------------------------------------------
-- 5.1 Rebuild mart.daily_store_category_sales from the fact table.
--
--     Two dimension joins, two different purposes:
--
--       silver.dim_store   AS st   -- store_name (a store attribute)
--       silver.dim_product AS p    -- category_name (a product attribute)
--
--     Both are LEFT JOINs on purpose: a transaction whose product or
--     store is missing from the dimension must still appear in revenue.
--     A dimension row is not required for a transaction to be real money.
--
--     Both joins are restricted to is_current = TRUE so the fact joins
--     to exactly one dimension row. Joining without that filter would
--     multiply the fact rows by the number of product versions.
--
--     Note the aliases: `st` and `p`, not `s`. Reusing one letter for
--     two dimensions is how `s.store_name` ends up pointing at the
--     product table.
-- ---------------------------------------------------------------------

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID`.mart.daily_store_category_sales
PARTITION BY sales_date
CLUSTER BY store_id, category_id
OPTIONS(
  description = "Daily revenue by store and category. Rebuilt from gold.fact_sales, silver.dim_store and silver.dim_product.",
  labels = [("tier", "mart"), ("domain", "retail")],
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
) AS
SELECT
  f.sales_date,
  f.store_id,
  ANY_VALUE(st.store_name HAVING MAX st.loaded_at) AS store_name,
  ANY_VALUE(f.region_id HAVING MAX f.loaded_at) AS region_id,
  ANY_VALUE(f.region_name HAVING MAX f.loaded_at) AS region_name,
  f.category_id,
  ANY_VALUE(p.category_name HAVING MAX p.loaded_at) AS category_name,
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
LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_store AS st
  ON f.store_id = st.store_id
 AND st.is_current
LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_product AS p
  ON f.product_id = p.product_id
 AND p.is_current
WHERE f.status = 'COMPLETED'
  AND f.net_amount IS NOT NULL
GROUP BY f.sales_date, f.store_id, f.category_id;

-- ---------------------------------------------------------------------
-- 5.2 Rebuild mart.provider_spend_monthly.
--
--     The month grain comes from DATE_TRUNC(submitted_at, MONTH). The
--     partition column month_start is derived the same way, so the
--     partition filter and the aggregation always agree.
--
--     ⚠️ Do NOT join back to the fact table to pick up an attribute
--     such as region_name. That join matches every claim in the
--     provider-month, fanning the rows out, and the downstream
--     `SUM(...) OVER (PARTITION BY month_start)` would then be
--     computed over a multiplied set — silently producing a wrong
--     percentage. Aggregate every attribute you need inside the CTE,
--     where the rows are still at their natural grain.
-- ---------------------------------------------------------------------

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID`.mart.provider_spend_monthly
PARTITION BY month_start
CLUSTER BY provider_id
OPTIONS(
  description = "Monthly provider spend. Rebuilt from gold.fact_claims.",
  labels = [("tier", "mart"), ("domain", "healthcare")],
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
) AS
WITH monthly AS (
  SELECT
    DATE_TRUNC(c.submitted_at, MONTH) AS month_start,
    c.provider_id,
    ANY_VALUE(c.provider_name HAVING MAX c.loaded_at) AS provider_name,
    ANY_VALUE(c.provider_type HAVING MAX c.loaded_at) AS provider_type,
    ANY_VALUE(p.state HAVING MAX p.loaded_at) AS provider_state,
    COUNT(*) AS claim_count,
    COUNT(DISTINCT c.member_id) AS member_count,
    SUM(c.claim_amount) AS total_claim_amount,
    COUNTIF(c.is_denied) AS denied_claim_count,
    SUM(IF(c.is_denied, c.claim_amount, 0)) AS denied_amount,
    SUM(IF(COALESCE(c.is_denied, FALSE), 0, c.claim_amount)) AS paid_amount
  FROM `YOUR_PROJECT_ID`.gold.fact_claims AS c
  LEFT JOIN `YOUR_PROJECT_ID`.silver.dim_provider AS p
    ON c.provider_id = p.provider_npi AND p.is_current
  WHERE c.submitted_at IS NOT NULL
  GROUP BY DATE_TRUNC(c.submitted_at, MONTH), c.provider_id
)
SELECT
  m.month_start,
  m.provider_id,
  m.provider_name,
  m.provider_type,
  m.provider_state,
  m.claim_count,
  m.member_count,
  m.total_claim_amount,
  SAFE_DIVIDE(m.total_claim_amount, m.claim_count) AS avg_claim_amount,
  m.denied_claim_count,
  SAFE_DIVIDE(m.denied_claim_count, m.claim_count) AS denial_rate,
  m.denied_amount,
  m.paid_amount,
  SAFE_DIVIDE(
    m.total_claim_amount,
    SUM(m.total_claim_amount) OVER (PARTITION BY m.month_start)
  ) AS pct_of_provider_total,
  CURRENT_TIMESTAMP() AS loaded_at
FROM monthly AS m;

-- ---------------------------------------------------------------------
-- 5.3 Rebuild mart.top_products.
--
--     Two stages: aggregate to (date, product), then rank within each
--     date. The window function is over the ALREADY-aggregated rows,
--     so it is cheap.
--
--     Note the QUALIFY usage: it filters on the window result in one
--     step instead of wrapping the query in a subquery and adding
--     WHERE rank <= 10.
-- ---------------------------------------------------------------------

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID`.mart.top_products
PARTITION BY period_date
CLUSTER BY product_id
OPTIONS(
  description = "Product leaderboard per period. Rebuilt from gold.fact_sales.",
  labels = [("tier", "mart"), ("domain", "retail")],
  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 YEAR)
) AS
WITH product_daily AS (
  SELECT
    f.sales_date AS period_date,
    f.product_id,
    ANY_VALUE(f.product_name HAVING MAX f.loaded_at) AS product_name,
    ANY_VALUE(f.category_id HAVING MAX f.loaded_at) AS category_id,
    ANY_VALUE(f.category_name HAVING MAX f.loaded_at) AS category_name,
    SUM(f.quantity) AS units_sold,
    SUM(f.net_amount) AS net_revenue,
    COUNT(DISTINCT f.order_id) AS order_count
  FROM `YOUR_PROJECT_ID`.gold.fact_sales AS f
  WHERE f.status = 'COMPLETED'
    AND f.net_amount IS NOT NULL
  GROUP BY f.sales_date, f.product_id
),
ranked AS (
  SELECT
    product_daily.*,
    ROW_NUMBER() OVER (
      PARTITION BY period_date
      ORDER BY net_revenue DESC, units_sold DESC, product_id
    ) AS rank,
    SUM(net_revenue) OVER (PARTITION BY period_date) AS period_total_revenue
  FROM product_daily
  QUALIFY rank <= 10
)
SELECT
  r.period_date,
  r.product_id,
  r.product_name,
  r.category_id,
  r.category_name,
  r.rank,
  r.units_sold,
  r.net_revenue,
  r.order_count,
  SAFE_DIVIDE(r.net_revenue, r.period_total_revenue) AS revenue_share_pct,
  CURRENT_TIMESTAMP() AS loaded_at
FROM ranked AS r;

-- ---------------------------------------------------------------------
-- 6. Verify the marts
--
--    The critical reconciliation: the mart total must equal the fact
--    total. A mismatch means the join dropped or duplicated rows.
--
--    FAIL looks like: mart_net_revenue <> fact_net_revenue. It is
--    always a join fan-out or a filter mismatch.
-- ---------------------------------------------------------------------

SELECT
  (SELECT SUM(net_amount) FROM `YOUR_PROJECT_ID`.gold.fact_sales WHERE status = 'COMPLETED') AS fact_net_revenue,
  (SELECT SUM(net_revenue) FROM `YOUR_PROJECT_ID`.mart.daily_store_category_sales) AS mart_net_revenue,
  (SELECT COUNT(DISTINCT order_id) FROM `YOUR_PROJECT_ID`.gold.fact_sales WHERE status = 'COMPLETED') AS fact_orders,
  (SELECT SUM(order_count) FROM `YOUR_PROJECT_ID`.mart.daily_store_category_sales) AS mart_orders;
