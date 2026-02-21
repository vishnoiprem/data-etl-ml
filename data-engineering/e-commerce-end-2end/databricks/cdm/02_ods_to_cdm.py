# Databricks Notebook: CDM Layer - Common Data Model (Dimensional Model)
# Layer: CDM - Cleansed, conformed, business-logic applied
# Builds: dim_* and fact_* tables
# Schedule: After ODS job completes

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window
from delta.tables import DeltaTable

spark = SparkSession.builder \
    .appName("EComm_CDM_Transform") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

ADLS_ROOT = "abfss://ecommerce@yourdatalake.dfs.core.windows.net"
CDM_PATH = f"{ADLS_ROOT}/cdm"

spark.sql("CREATE DATABASE IF NOT EXISTS ecomm_cdm")


# ══════════════════════════════════════════════════════════════
# DIMENSION: dim_date
# ══════════════════════════════════════════════════════════════
def build_dim_date():
    print("Building dim_date...")
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS ecomm_cdm.dim_date
        USING DELTA LOCATION '{CDM_PATH}/dim_date'
        AS
        SELECT
            CAST(date_format(date_seq, 'yyyyMMdd') AS INT)  AS date_key,
            date_seq                                         AS full_date,
            year(date_seq)                                   AS year,
            quarter(date_seq)                                AS quarter,
            month(date_seq)                                  AS month,
            date_format(date_seq, 'MMMM')                   AS month_name,
            weekofyear(date_seq)                             AS week_of_year,
            dayofmonth(date_seq)                             AS day_of_month,
            dayofweek(date_seq)                              AS day_of_week,
            date_format(date_seq, 'EEEE')                   AS day_name,
            CASE WHEN dayofweek(date_seq) IN (1,7) THEN 1 ELSE 0 END  AS is_weekend,
            date_format(date_seq, 'yyyy-MM')                AS year_month,
            CONCAT('Q', quarter(date_seq), '-', year(date_seq)) AS year_quarter
        FROM (
            SELECT explode(sequence(
                to_date('2022-01-01'),
                to_date('2027-12-31'),
                interval 1 day
            )) AS date_seq
        )
    """)


# ══════════════════════════════════════════════════════════════
# DIMENSION: dim_user
# ══════════════════════════════════════════════════════════════
def build_dim_user():
    print("Building dim_user...")
    df = spark.sql("""
        SELECT
            u.user_id,
            u.username,
            u.email,
            u.full_name,
            u.gender,
            u.date_of_birth,
            FLOOR(DATEDIFF(current_date(), u.date_of_birth) / 365) AS age,
            CASE
                WHEN FLOOR(DATEDIFF(current_date(), u.date_of_birth) / 365) < 25 THEN '18-24'
                WHEN FLOOR(DATEDIFF(current_date(), u.date_of_birth) / 365) < 35 THEN '25-34'
                WHEN FLOOR(DATEDIFF(current_date(), u.date_of_birth) / 365) < 45 THEN '35-44'
                WHEN FLOOR(DATEDIFF(current_date(), u.date_of_birth) / 365) < 55 THEN '45-54'
                ELSE '55+'
            END                                                      AS age_group,
            u.user_type,
            u.status,
            u.is_verified,
            u.country_code,
            u.created_at                                             AS registered_at,
            u.last_login_at,
            DATEDIFF(current_date(), u.created_at)                   AS days_since_registration,
            -- RFM Metrics
            COUNT(DISTINCT o.order_id)                               AS total_orders,
            COALESCE(SUM(o.total_amount), 0)                         AS lifetime_value,
            COALESCE(AVG(o.total_amount), 0)                         AS avg_order_value,
            MAX(o.created_at)                                        AS last_order_date,
            DATEDIFF(current_date(), MAX(o.created_at))              AS days_since_last_order,
            -- Segmentation
            CASE
                WHEN COUNT(DISTINCT o.order_id) = 0 THEN 'Prospect'
                WHEN DATEDIFF(current_date(), MAX(o.created_at)) <= 30
                     AND COUNT(DISTINCT o.order_id) >= 3 THEN 'Champion'
                WHEN DATEDIFF(current_date(), MAX(o.created_at)) <= 90 THEN 'Active'
                WHEN DATEDIFF(current_date(), MAX(o.created_at)) <= 180 THEN 'At Risk'
                ELSE 'Churned'
            END                                                      AS customer_segment,
            current_timestamp()                                      AS _cdm_updated_at
        FROM ecomm_ods.users u
        LEFT JOIN ecomm_ods.orders o
            ON u.user_id = o.user_id
            AND o.status NOT IN ('cancelled', 'returned')
        WHERE u.status = 'active'
        GROUP BY
            u.user_id, u.username, u.email, u.full_name, u.gender,
            u.date_of_birth, u.user_type, u.status, u.is_verified,
            u.country_code, u.created_at, u.last_login_at
    """)
    df.write.format("delta").mode("overwrite") \
        .option("overwriteSchema", "true") \
        .save(f"{CDM_PATH}/dim_user")
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS ecomm_cdm.dim_user
        USING DELTA LOCATION '{CDM_PATH}/dim_user'
    """)


# ══════════════════════════════════════════════════════════════
# DIMENSION: dim_product
# ══════════════════════════════════════════════════════════════
def build_dim_product():
    print("Building dim_product...")
    df = spark.sql("""
        SELECT
            p.product_id,
            p.name                                              AS product_name,
            p.status                                            AS product_status,
            p.condition_type,
            p.min_price,
            p.max_price,
            p.rating                                            AS product_rating,
            p.review_count,
            p.total_sold,
            p.total_views,
            p.is_featured,
            -- Category hierarchy
            c.category_id,
            c.name                                              AS category_name,
            c.level                                             AS category_level,
            COALESCE(pc.name, c.name)                           AS parent_category_name,
            -- Brand
            b.brand_id,
            b.name                                              AS brand_name,
            b.country                                           AS brand_country,
            -- Seller
            s.seller_id,
            s.shop_name,
            s.seller_type,
            s.rating                                            AS seller_rating,
            s.warehouse_city,
            -- Price tier
            CASE
                WHEN p.min_price < 500   THEN 'Budget'
                WHEN p.min_price < 2000  THEN 'Mid-Range'
                WHEN p.min_price < 10000 THEN 'Premium'
                ELSE 'Luxury'
            END                                                 AS price_tier,
            p.created_at                                        AS listed_at,
            current_timestamp()                                 AS _cdm_updated_at
        FROM ecomm_ods.products p
        JOIN ecomm_ods.categories c ON p.category_id = c.category_id
        LEFT JOIN ecomm_ods.categories pc ON c.parent_id = pc.category_id
        LEFT JOIN ecomm_ods.brands b ON p.brand_id = b.brand_id
        JOIN ecomm_ods.sellers s ON p.seller_id = s.seller_id
        WHERE p.status = 'active'
    """)
    df.write.format("delta").mode("overwrite") \
        .partitionBy("category_id") \
        .save(f"{CDM_PATH}/dim_product")
    spark.sql(f"CREATE TABLE IF NOT EXISTS ecomm_cdm.dim_product USING DELTA LOCATION '{CDM_PATH}/dim_product'")


# ══════════════════════════════════════════════════════════════
# DIMENSION: dim_seller
# ══════════════════════════════════════════════════════════════
def build_dim_seller():
    print("Building dim_seller...")
    df = spark.sql("""
        SELECT
            s.seller_id,
            s.shop_name,
            s.seller_type,
            s.status,
            s.rating,
            s.total_reviews,
            s.total_sales,
            s.response_rate,
            s.warehouse_city,
            s.country_code,
            s.commission_rate,
            s.joined_date,
            DATEDIFF(current_date(), s.joined_date)  AS days_on_platform,
            -- Seller tier
            CASE
                WHEN s.rating >= 4.8 AND s.total_sales > 10000 THEN 'Platinum'
                WHEN s.rating >= 4.5 AND s.total_sales > 5000  THEN 'Gold'
                WHEN s.rating >= 4.0 AND s.total_sales > 1000  THEN 'Silver'
                ELSE 'Standard'
            END                                      AS seller_tier,
            COUNT(p.product_id)                      AS active_product_count,
            current_timestamp()                      AS _cdm_updated_at
        FROM ecomm_ods.sellers s
        LEFT JOIN ecomm_ods.products p
            ON s.seller_id = p.seller_id AND p.status = 'active'
        WHERE s.status = 'active'
        GROUP BY ALL
    """)
    df.write.format("delta").mode("overwrite").save(f"{CDM_PATH}/dim_seller")
    spark.sql(f"CREATE TABLE IF NOT EXISTS ecomm_cdm.dim_seller USING DELTA LOCATION '{CDM_PATH}/dim_seller'")


# ══════════════════════════════════════════════════════════════
# FACT: fact_orders
# ══════════════════════════════════════════════════════════════
def build_fact_orders():
    print("Building fact_orders...")
    df = spark.sql("""
        SELECT
            o.order_id,
            o.order_no,
            -- Keys
            o.user_id,
            o.seller_id,
            CAST(date_format(o.created_at, 'yyyyMMdd') AS INT)          AS order_date_key,
            CAST(date_format(o.delivered_at, 'yyyyMMdd') AS INT)         AS delivered_date_key,
            -- Order Status
            o.status                                                      AS order_status,
            o.payment_status,
            o.payment_method,
            -- Financials
            o.subtotal,
            o.shipping_fee,
            o.platform_fee,
            o.discount_amount,
            o.voucher_discount,
            o.total_amount,
            o.currency,
            -- Platform revenue = commission
            ROUND(o.subtotal * (s.commission_rate / 100), 2)             AS platform_commission,
            -- Derived
            DATEDIFF(o.delivered_at, o.created_at)                       AS fulfillment_days,
            CASE WHEN o.status = 'delivered' THEN 1 ELSE 0 END           AS is_completed,
            CASE WHEN o.status = 'cancelled' THEN 1 ELSE 0 END           AS is_cancelled,
            CASE WHEN o.status = 'returned'  THEN 1 ELSE 0 END           AS is_returned,
            -- Shipping address components
            GET_JSON_OBJECT(o.shipping_address, '$.city')                 AS delivery_city,
            GET_JSON_OBJECT(o.shipping_address, '$.country')              AS delivery_country,
            -- Item count
            oi.item_count,
            oi.total_qty,
            o.created_at,
            o.updated_at,
            current_timestamp()                                           AS _cdm_updated_at
        FROM ecomm_ods.orders o
        JOIN ecomm_ods.sellers s ON o.seller_id = s.seller_id
        LEFT JOIN (
            SELECT order_id,
                   COUNT(item_id)   AS item_count,
                   SUM(quantity)    AS total_qty
            FROM ecomm_ods.order_items
            GROUP BY order_id
        ) oi ON o.order_id = oi.order_id
    """)
    df.write.format("delta").mode("overwrite") \
        .partitionBy("order_status") \
        .save(f"{CDM_PATH}/fact_orders")
    spark.sql(f"CREATE TABLE IF NOT EXISTS ecomm_cdm.fact_orders USING DELTA LOCATION '{CDM_PATH}/fact_orders'")


# ══════════════════════════════════════════════════════════════
# FACT: fact_order_items
# ══════════════════════════════════════════════════════════════
def build_fact_order_items():
    print("Building fact_order_items...")
    df = spark.sql("""
        SELECT
            oi.item_id,
            oi.order_id,
            o.user_id,
            oi.product_id,
            oi.sku_id,
            o.seller_id,
            sk.attributes,
            CAST(date_format(o.created_at, 'yyyyMMdd') AS INT)  AS order_date_key,
            oi.quantity,
            oi.unit_price,
            oi.original_price,
            oi.discount,
            oi.subtotal,
            -- Margin calculation
            ROUND(oi.unit_price - sk.cost_price, 2)             AS gross_margin,
            ROUND((oi.unit_price - sk.cost_price) / NULLIF(oi.unit_price, 0) * 100, 2) AS margin_pct,
            oi.status                                            AS item_status,
            o.created_at                                         AS order_created_at,
            current_timestamp()                                  AS _cdm_updated_at
        FROM ecomm_ods.order_items oi
        JOIN ecomm_ods.orders o ON oi.order_id = o.order_id
        JOIN ecomm_ods.product_skus sk ON oi.sku_id = sk.sku_id
    """)
    df.write.format("delta").mode("overwrite") \
        .partitionBy("item_status") \
        .save(f"{CDM_PATH}/fact_order_items")
    spark.sql(f"CREATE TABLE IF NOT EXISTS ecomm_cdm.fact_order_items USING DELTA LOCATION '{CDM_PATH}/fact_order_items'")


# ══════════════════════════════════════════════════════════════
# FACT: fact_inventory_snapshot (daily)
# ══════════════════════════════════════════════════════════════
def build_fact_inventory():
    print("Building fact_inventory_snapshot...")
    df = spark.sql("""
        SELECT
            inv.inventory_id,
            inv.sku_id,
            inv.warehouse_id,
            sk.product_id,
            p.category_id,
            p.seller_id,
            inv.quantity                                         AS stock_qty,
            inv.reserved_qty,
            inv.quantity - inv.reserved_qty                     AS available_qty,
            inv.reorder_point,
            inv.reorder_qty,
            CASE WHEN (inv.quantity - inv.reserved_qty) <= inv.reorder_point
                 THEN 1 ELSE 0 END                              AS needs_reorder,
            CASE WHEN inv.quantity = 0 THEN 1 ELSE 0 END        AS is_stockout,
            sk.price                                             AS unit_price,
            ROUND(inv.quantity * sk.cost_price, 2)              AS inventory_value,
            current_date()                                       AS snapshot_date,
            current_timestamp()                                  AS _cdm_updated_at
        FROM ecomm_ods.inventory inv
        JOIN ecomm_ods.product_skus sk ON inv.sku_id = sk.sku_id
        JOIN ecomm_ods.products p ON sk.product_id = p.product_id
        WHERE p.status = 'active'
    """)
    df.write.format("delta").mode("overwrite") \
        .partitionBy("warehouse_id") \
        .save(f"{CDM_PATH}/fact_inventory_snapshot")
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS ecomm_cdm.fact_inventory_snapshot
        USING DELTA LOCATION '{CDM_PATH}/fact_inventory_snapshot'
    """)


# ══════════════════════════════════════════════════════════════
# FACT: fact_user_events
# ══════════════════════════════════════════════════════════════
def build_fact_user_events():
    print("Building fact_user_events...")
    df = spark.sql("""
        SELECT
            e.event_id,
            e.user_id,
            e.session_id,
            e.event_type,
            e.entity_type,
            e.entity_id                                          AS product_id,
            e.device_type,
            e.platform,
            CAST(date_format(e.created_at, 'yyyyMMdd') AS INT)  AS event_date_key,
            hour(e.created_at)                                   AS event_hour,
            -- Session stats via window
            COUNT(*) OVER (
                PARTITION BY e.session_id
            )                                                    AS session_event_count,
            ROW_NUMBER() OVER (
                PARTITION BY e.session_id ORDER BY e.created_at
            )                                                    AS event_sequence,
            e.created_at,
            current_timestamp()                                  AS _cdm_updated_at
        FROM ecomm_ods.user_events e
    """)
    df.write.format("delta").mode("overwrite") \
        .partitionBy("event_type") \
        .save(f"{CDM_PATH}/fact_user_events")
    spark.sql(f"CREATE TABLE IF NOT EXISTS ecomm_cdm.fact_user_events USING DELTA LOCATION '{CDM_PATH}/fact_user_events'")


# ── Execute All ───────────────────────────────────────────────
build_dim_date()
build_dim_user()
build_dim_product()
build_dim_seller()
build_fact_orders()
build_fact_order_items()
build_fact_inventory()
build_fact_user_events()

print("\n✅ CDM Layer build complete!")
spark.sql("SHOW TABLES IN ecomm_cdm").show(30, truncate=False)
