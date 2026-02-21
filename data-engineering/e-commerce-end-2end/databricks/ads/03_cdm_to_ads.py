# Databricks Notebook: ADS Layer - Application Data Store
# Layer: ADS - Pre-aggregated, business-ready tables for BI & ML
# Builds: Aggregated metrics tables optimized for dashboard queries

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window

spark = SparkSession.builder \
    .appName("EComm_ADS_Aggregation") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

ADLS_ROOT = "abfss://ecommerce@yourdatalake.dfs.core.windows.net"
ADS_PATH = f"{ADLS_ROOT}/ads"

spark.sql("CREATE DATABASE IF NOT EXISTS ecomm_ads")


# ══════════════════════════════════════════════════════════════
# ADS: ads_daily_gmv  (GMV = Gross Merchandise Value)
# For: Executive dashboard, revenue tracking
# ══════════════════════════════════════════════════════════════
def build_ads_daily_gmv():
    print("Building ads_daily_gmv...")
    spark.sql(f"""
        CREATE OR REPLACE TABLE ecomm_ads.ads_daily_gmv
        USING DELTA LOCATION '{ADS_PATH}/ads_daily_gmv'
        PARTITIONED BY (order_date)
        AS
        SELECT
            CAST(fo.created_at AS DATE)                             AS order_date,
            dd.year,
            dd.quarter,
            dd.month,
            dd.month_name,
            dd.week_of_year,
            dd.is_weekend,
            -- Volume metrics
            COUNT(DISTINCT fo.order_id)                             AS total_orders,
            COUNT(DISTINCT fo.user_id)                              AS unique_buyers,
            COUNT(DISTINCT fo.seller_id)                            AS active_sellers,
            SUM(fo.item_count)                                      AS total_items_sold,
            -- Revenue metrics
            ROUND(SUM(fo.total_amount), 2)                          AS gross_merchandise_value,
            ROUND(SUM(fo.platform_commission), 2)                   AS platform_revenue,
            ROUND(SUM(fo.subtotal), 2)                              AS net_sales,
            ROUND(SUM(fo.shipping_fee), 2)                          AS total_shipping_fees,
            ROUND(SUM(fo.discount_amount + fo.voucher_discount), 2) AS total_discounts,
            -- AOV
            ROUND(SUM(fo.total_amount) / COUNT(DISTINCT fo.order_id), 2) AS avg_order_value,
            -- Conversion by status
            ROUND(COUNT(CASE WHEN fo.is_completed = 1 THEN 1 END) * 100.0
                  / NULLIF(COUNT(fo.order_id), 0), 2)              AS completion_rate_pct,
            ROUND(COUNT(CASE WHEN fo.is_cancelled = 1 THEN 1 END) * 100.0
                  / NULLIF(COUNT(fo.order_id), 0), 2)              AS cancellation_rate_pct,
            -- Payment breakdown
            SUM(CASE WHEN fo.payment_method = 'cod'         THEN fo.total_amount ELSE 0 END) AS cod_gmv,
            SUM(CASE WHEN fo.payment_method = 'credit_card' THEN fo.total_amount ELSE 0 END) AS card_gmv,
            SUM(CASE WHEN fo.payment_method = 'wallet'      THEN fo.total_amount ELSE 0 END) AS wallet_gmv,
            -- Running totals via window
            SUM(SUM(fo.total_amount)) OVER (
                PARTITION BY dd.year ORDER BY CAST(fo.created_at AS DATE)
                ROWS UNBOUNDED PRECEDING
            )                                                       AS ytd_gmv,
            current_timestamp()                                     AS _ads_updated_at
        FROM ecomm_cdm.fact_orders fo
        JOIN ecomm_cdm.dim_date dd
            ON fo.order_date_key = dd.date_key
        GROUP BY
            CAST(fo.created_at AS DATE), dd.year, dd.quarter, dd.month,
            dd.month_name, dd.week_of_year, dd.is_weekend
        ORDER BY order_date
    """)


# ══════════════════════════════════════════════════════════════
# ADS: ads_product_performance
# For: Product management, catalog team
# ══════════════════════════════════════════════════════════════
def build_ads_product_performance():
    print("Building ads_product_performance...")
    spark.sql(f"""
        CREATE OR REPLACE TABLE ecomm_ads.ads_product_performance
        USING DELTA LOCATION '{ADS_PATH}/ads_product_performance'
        AS
        SELECT
            dp.product_id,
            dp.product_name,
            dp.category_name,
            dp.parent_category_name,
            dp.brand_name,
            dp.shop_name,
            dp.price_tier,
            dp.min_price,
            dp.max_price,
            dp.product_rating,
            dp.review_count,
            -- Sales metrics
            COUNT(DISTINCT foi.order_id)                             AS total_orders,
            COALESCE(SUM(foi.quantity), 0)                           AS units_sold,
            ROUND(COALESCE(SUM(foi.subtotal), 0), 2)                 AS total_revenue,
            ROUND(COALESCE(AVG(foi.unit_price), 0), 2)               AS avg_selling_price,
            ROUND(COALESCE(SUM(foi.gross_margin * foi.quantity), 0), 2) AS total_margin,
            ROUND(COALESCE(AVG(foi.margin_pct), 0), 2)               AS avg_margin_pct,
            -- Last 30 days
            COUNT(DISTINCT CASE WHEN fo.created_at >= current_date() - 30
                           THEN foi.order_id END)                    AS orders_last_30d,
            COALESCE(SUM(CASE WHEN fo.created_at >= current_date() - 30
                         THEN foi.quantity ELSE 0 END), 0)           AS units_last_30d,
            -- Views & conversion
            dp.total_views,
            dp.total_sold,
            ROUND(dp.total_sold * 100.0 / NULLIF(dp.total_views, 0), 4) AS view_to_purchase_rate,
            -- Inventory status
            COALESCE(SUM(inv.available_qty), 0)                      AS total_available_stock,
            COALESCE(SUM(inv.is_stockout), 0)                        AS sku_stockout_count,
            -- Rank within category
            DENSE_RANK() OVER (
                PARTITION BY dp.category_name
                ORDER BY SUM(foi.subtotal) DESC
            )                                                        AS revenue_rank_in_category,
            current_timestamp()                                      AS _ads_updated_at
        FROM ecomm_cdm.dim_product dp
        LEFT JOIN ecomm_cdm.fact_order_items foi ON dp.product_id = foi.product_id
        LEFT JOIN ecomm_cdm.fact_orders fo ON foi.order_id = fo.order_id
            AND fo.order_status NOT IN ('cancelled', 'returned')
        LEFT JOIN ecomm_cdm.fact_inventory_snapshot inv ON dp.product_id = inv.product_id
        GROUP BY ALL
    """)


# ══════════════════════════════════════════════════════════════
# ADS: ads_seller_scorecard
# For: Seller management, platform ops
# ══════════════════════════════════════════════════════════════
def build_ads_seller_scorecard():
    print("Building ads_seller_scorecard...")
    spark.sql(f"""
        CREATE OR REPLACE TABLE ecomm_ads.ads_seller_scorecard
        USING DELTA LOCATION '{ADS_PATH}/ads_seller_scorecard'
        AS
        SELECT
            ds.seller_id,
            ds.shop_name,
            ds.seller_type,
            ds.seller_tier,
            ds.warehouse_city,
            ds.commission_rate,
            ds.rating                                               AS seller_rating,
            ds.response_rate,
            ds.active_product_count,
            -- Revenue metrics
            ROUND(SUM(fo.total_amount), 2)                          AS total_gmv,
            ROUND(SUM(fo.platform_commission), 2)                   AS total_commission_paid,
            COUNT(DISTINCT fo.order_id)                             AS total_orders,
            COUNT(DISTINCT fo.user_id)                              AS unique_customers,
            ROUND(AVG(fo.total_amount), 2)                          AS avg_order_value,
            -- Performance
            ROUND(SUM(CASE WHEN fo.is_completed = 1 THEN fo.total_amount ELSE 0 END)
                  / NULLIF(SUM(fo.total_amount), 0) * 100, 2)       AS fulfillment_rate_pct,
            ROUND(AVG(CASE WHEN fo.is_completed = 1
                      THEN fo.fulfillment_days END), 1)             AS avg_fulfillment_days,
            ROUND(SUM(CASE WHEN fo.is_cancelled = 1 THEN 1 ELSE 0 END) * 100.0
                  / NULLIF(COUNT(fo.order_id), 0), 2)               AS cancellation_rate_pct,
            -- Last 30 / 90 days
            ROUND(SUM(CASE WHEN fo.created_at >= current_date() - 30
                      THEN fo.total_amount ELSE 0 END), 2)          AS gmv_last_30d,
            ROUND(SUM(CASE WHEN fo.created_at >= current_date() - 90
                      THEN fo.total_amount ELSE 0 END), 2)          AS gmv_last_90d,
            -- Rank on platform
            DENSE_RANK() OVER (ORDER BY SUM(fo.total_amount) DESC)  AS gmv_rank,
            current_timestamp()                                     AS _ads_updated_at
        FROM ecomm_cdm.dim_seller ds
        LEFT JOIN ecomm_cdm.fact_orders fo ON ds.seller_id = fo.seller_id
        GROUP BY ALL
    """)


# ══════════════════════════════════════════════════════════════
# ADS: ads_customer_rfm  (Recency, Frequency, Monetary)
# For: CRM, marketing campaigns
# ══════════════════════════════════════════════════════════════
def build_ads_customer_rfm():
    print("Building ads_customer_rfm...")
    spark.sql(f"""
        CREATE OR REPLACE TABLE ecomm_ads.ads_customer_rfm
        USING DELTA LOCATION '{ADS_PATH}/ads_customer_rfm'
        AS
        WITH rfm_base AS (
            SELECT
                fo.user_id,
                DATEDIFF(current_date(), MAX(fo.created_at))    AS recency_days,
                COUNT(DISTINCT fo.order_id)                     AS frequency,
                ROUND(SUM(fo.total_amount), 2)                  AS monetary
            FROM ecomm_cdm.fact_orders fo
            WHERE fo.order_status NOT IN ('cancelled', 'returned')
            GROUP BY fo.user_id
        ),
        rfm_scores AS (
            SELECT *,
                NTILE(5) OVER (ORDER BY recency_days ASC)   AS r_score,
                NTILE(5) OVER (ORDER BY frequency DESC)     AS f_score,
                NTILE(5) OVER (ORDER BY monetary DESC)      AS m_score
            FROM rfm_base
        )
        SELECT
            r.user_id,
            du.full_name,
            du.email,
            du.country_code,
            du.customer_segment,
            r.recency_days,
            r.frequency,
            r.monetary,
            r.r_score,
            r.f_score,
            r.m_score,
            (r.r_score + r.f_score + r.m_score)             AS total_rfm_score,
            -- RFM Segment
            CASE
                WHEN r.r_score >= 4 AND r.f_score >= 4 AND r.m_score >= 4 THEN 'Champions'
                WHEN r.r_score >= 3 AND r.f_score >= 3 AND r.m_score >= 3 THEN 'Loyal Customers'
                WHEN r.r_score >= 4 AND r.f_score <= 2                    THEN 'New Customers'
                WHEN r.r_score <= 2 AND r.f_score >= 3 AND r.m_score >= 3 THEN 'At Risk'
                WHEN r.r_score <= 2 AND r.f_score <= 2 AND r.m_score <= 2 THEN 'Lost Customers'
                WHEN r.r_score >= 3 AND r.m_score >= 4                    THEN 'Potential Loyalists'
                ELSE 'Needs Attention'
            END                                             AS rfm_segment,
            current_timestamp()                             AS _ads_updated_at
        FROM rfm_scores r
        JOIN ecomm_cdm.dim_user du ON r.user_id = du.user_id
    """)


# ══════════════════════════════════════════════════════════════
# ADS: ads_category_trends  (daily, 90-day rolling)
# For: Merchandising, buying team
# ══════════════════════════════════════════════════════════════
def build_ads_category_trends():
    print("Building ads_category_trends...")
    spark.sql(f"""
        CREATE OR REPLACE TABLE ecomm_ads.ads_category_trends
        USING DELTA LOCATION '{ADS_PATH}/ads_category_trends'
        PARTITIONED BY (order_date)
        AS
        SELECT
            CAST(fo.created_at AS DATE)                             AS order_date,
            dp.parent_category_name,
            dp.category_name,
            COUNT(DISTINCT fo.order_id)                             AS orders,
            SUM(foi.quantity)                                       AS units_sold,
            ROUND(SUM(foi.subtotal), 2)                             AS revenue,
            ROUND(AVG(foi.unit_price), 2)                           AS avg_price,
            COUNT(DISTINCT fo.user_id)                              AS unique_buyers,
            -- 7-day MA
            ROUND(AVG(SUM(foi.subtotal)) OVER (
                PARTITION BY dp.category_name
                ORDER BY CAST(fo.created_at AS DATE)
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ), 2)                                                   AS revenue_7d_ma,
            -- 30-day MA
            ROUND(AVG(SUM(foi.subtotal)) OVER (
                PARTITION BY dp.category_name
                ORDER BY CAST(fo.created_at AS DATE)
                ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
            ), 2)                                                   AS revenue_30d_ma,
            current_timestamp()                                     AS _ads_updated_at
        FROM ecomm_cdm.fact_order_items foi
        JOIN ecomm_cdm.fact_orders fo ON foi.order_id = fo.order_id
            AND fo.order_status NOT IN ('cancelled', 'returned')
        JOIN ecomm_cdm.dim_product dp ON foi.product_id = dp.product_id
        GROUP BY CAST(fo.created_at AS DATE), dp.parent_category_name, dp.category_name
    """)


# ══════════════════════════════════════════════════════════════
# ADS: ads_warehouse_efficiency
# For: Operations, logistics team, ML input
# ══════════════════════════════════════════════════════════════
def build_ads_warehouse_efficiency():
    print("Building ads_warehouse_efficiency...")
    spark.sql(f"""
        CREATE OR REPLACE TABLE ecomm_ads.ads_warehouse_efficiency
        USING DELTA LOCATION '{ADS_PATH}/ads_warehouse_efficiency'
        AS
        SELECT
            w.warehouse_id,
            w.name                                              AS warehouse_name,
            w.code,
            w.city,
            w.capacity_sqm,
            -- Inventory metrics
            COUNT(DISTINCT inv.sku_id)                          AS total_skus,
            SUM(inv.stock_qty)                                  AS total_stock_units,
            SUM(inv.available_qty)                              AS available_units,
            SUM(inv.is_stockout)                                AS stockout_skus,
            ROUND(SUM(inv.is_stockout) * 100.0 / COUNT(inv.sku_id), 2) AS stockout_rate_pct,
            SUM(inv.needs_reorder)                              AS skus_needing_reorder,
            ROUND(SUM(inv.inventory_value), 2)                  AS total_inventory_value,
            -- Throughput (orders shipped from this warehouse)
            COUNT(DISTINCT sh.shipment_id)                      AS total_shipments,
            ROUND(AVG(CASE WHEN sh.status = 'delivered'
                     THEN DATEDIFF(sh.delivered_at, sh.created_at) END), 1) AS avg_delivery_days,
            SUM(CASE WHEN sh.status = 'delivered' THEN 1 ELSE 0 END) AS delivered_count,
            SUM(CASE WHEN sh.status = 'failed'    THEN 1 ELSE 0 END) AS failed_deliveries,
            -- Utilization (rough: assume 1 unit = 0.01 sqm)
            ROUND(SUM(inv.stock_qty) * 0.01 / NULLIF(w.capacity_sqm, 0) * 100, 2) AS capacity_utilization_pct,
            current_timestamp()                                 AS _ads_updated_at
        FROM ecomm_ods.warehouses w
        LEFT JOIN ecomm_cdm.fact_inventory_snapshot inv ON w.warehouse_id = inv.warehouse_id
        LEFT JOIN ecomm_ods.shipments sh ON sh.shipment_id IS NOT NULL  -- join via order logic
        GROUP BY ALL
    """)


# ── Execute All ────────────────────────────────────────────────
build_ads_daily_gmv()
build_ads_product_performance()
build_ads_seller_scorecard()
build_ads_customer_rfm()
build_ads_category_trends()
build_ads_warehouse_efficiency()

print("\n✅ ADS Layer build complete!")
spark.sql("SHOW TABLES IN ecomm_ads").show(20, truncate=False)
