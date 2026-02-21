-- ============================================================
-- ClickHouse Schema: Real-Time E-Commerce Analytics
-- Engine: MergeTree family (optimized for time-series analytics)
-- ============================================================

CREATE DATABASE IF NOT EXISTS ecomm_realtime;
USE ecomm_realtime;


-- ============================================================
-- Real-Time Order Metrics (from Flink 1-min window)
-- ============================================================
CREATE TABLE IF NOT EXISTS rt_order_metrics (
    window_start     DateTime,
    window_end       DateTime,
    city             String,
    gmv              Float64,
    order_count      UInt32,
    unique_buyers    UInt32,
    avg_order_value  Float64,
    computed_at      DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(computed_at)
PARTITION BY toYYYYMMDD(window_start)
ORDER BY (window_start, city)
TTL window_start + INTERVAL 90 DAY;


-- ============================================================
-- Real-Time Funnel Metrics (from Flink 5-min window)
-- ============================================================
CREATE TABLE IF NOT EXISTS rt_funnel_metrics (
    window_start              DateTime,
    window_end                DateTime,
    platform                  String,
    views                     UInt64,
    add_to_cart               UInt64,
    purchases                 UInt64,
    view_to_cart_rate         Float32,
    cart_to_purchase_rate     Float32,
    overall_conversion_rate   Float32,
    computed_at               DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(computed_at)
PARTITION BY toYYYYMMDD(window_start)
ORDER BY (window_start, platform)
TTL window_start + INTERVAL 90 DAY;


-- ============================================================
-- Live Order Stream (append-only CDC)
-- ============================================================
CREATE TABLE IF NOT EXISTS rt_orders_stream (
    order_id         UInt64,
    user_id          UInt64,
    seller_id        UInt64,
    status           LowCardinality(String),
    payment_method   LowCardinality(String),
    total_amount     Decimal(15, 2),
    city             String,
    op               String,          -- c/u/d
    event_time       DateTime64(3)
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(event_time)
ORDER BY (event_time, order_id)
TTL event_time + INTERVAL 30 DAY;


-- ============================================================
-- Hourly GMV Materialized View
-- ============================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hourly_gmv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMMDD(hour)
ORDER BY (hour, city)
POPULATE AS
SELECT
    toStartOfHour(event_time)  AS hour,
    city,
    count()                    AS order_count,
    sum(total_amount)          AS gmv,
    uniqExact(user_id)         AS unique_buyers
FROM rt_orders_stream
WHERE op IN ('c')
  AND status != 'cancelled'
GROUP BY hour, city;


-- ============================================================
-- User Event Stream (clickstream)
-- ============================================================
CREATE TABLE IF NOT EXISTS rt_user_events (
    event_id         UInt64,
    user_id          Nullable(UInt64),
    session_id       String,
    event_type       LowCardinality(String),
    entity_id        Nullable(UInt64),
    device_type      LowCardinality(String),
    platform         LowCardinality(String),
    event_time       DateTime64(6)
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(event_time)
ORDER BY (event_time, session_id)
TTL event_time + INTERVAL 7 DAY;


-- ============================================================
-- Real-Time Inventory Alerts
-- ============================================================
CREATE TABLE IF NOT EXISTS rt_inventory_alerts (
    alert_id         UUID DEFAULT generateUUIDv4(),
    sku_id           UInt64,
    warehouse_id     UInt32,
    alert_type       LowCardinality(String),  -- 'STOCKOUT', 'LOW_STOCK', 'REORDER'
    current_qty      Int32,
    threshold        Int32,
    message          String,
    created_at       DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (created_at, sku_id)
TTL created_at + INTERVAL 14 DAY;


-- ============================================================
-- Real-Time Payment Status Tracking
-- ============================================================
CREATE TABLE IF NOT EXISTS rt_payment_events (
    payment_id       UInt64,
    order_id         UInt64,
    gateway          LowCardinality(String),
    amount           Decimal(15, 2),
    currency         FixedString(3),
    status           LowCardinality(String),
    event_time       DateTime64(3)
) ENGINE = ReplacingMergeTree(event_time)
PARTITION BY toYYYYMMDD(event_time)
ORDER BY (event_time, payment_id)
TTL event_time + INTERVAL 60 DAY;


-- ============================================================
-- Dashboard: Live KPI View
-- ============================================================
CREATE VIEW IF NOT EXISTS v_live_kpi AS
SELECT
    'Today'                                                              AS period,
    toStartOfDay(now())                                                  AS as_of,
    countIf(op = 'c')                                                    AS new_orders_today,
    sumIf(total_amount, op = 'c' AND status != 'cancelled')              AS gmv_today,
    uniqExactIf(user_id, op = 'c')                                       AS unique_buyers_today,
    round(sumIf(total_amount, op = 'c') / nullIf(countIf(op = 'c'), 0), 2) AS aov_today
FROM rt_orders_stream
WHERE event_time >= toStartOfDay(now());


-- ============================================================
-- Query: GMV last 24 hours by hour
-- ============================================================
-- SELECT
--     toStartOfHour(event_time) AS hour,
--     city,
--     count() AS orders,
--     sum(total_amount) AS gmv,
--     uniqExact(user_id) AS buyers
-- FROM rt_orders_stream
-- WHERE event_time >= now() - INTERVAL 24 HOUR
--   AND op = 'c'
-- GROUP BY hour, city
-- ORDER BY hour DESC, gmv DESC;
