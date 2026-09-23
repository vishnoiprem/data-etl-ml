"""
Problem 01: Marketplace Seller Dashboard (3 fact tables at 3 grains)
Meta product: "Facebook Marketplace"

How to Think:
- A seller dashboard must answer: listings created, items sold, gross merchandise value,
  conversion (view -> message -> sale), seller rating trend, active listings count.
- These metrics live at different grains: per-listing, per-order, per-day-per-seller.
- Modeling all three in one fact table causes double-counting and grain confusion.
- Build one fact per grain; share conformed dims (seller, category, date, geo).

How to Remember:
- "Metrics decide grain. Grain decides facts. Shared dims = conformed."
- Three grains here: listing (created/sold state), order (transactional),
  seller_daily_snapshot (periodic).

AI Use Cases:
- Forecast seller GMV by category.
- Detect sellers likely to churn (drop in listing activity).
- Recommend price band based on category sell-through.
"""

DDL = """
-- Grain: one row per marketplace listing (creation event -> current state).
CREATE TABLE fact_listing (
  listing_key        BIGINT,
  seller_key         BIGINT,
  category_key       BIGINT,
  location_key       BIGINT,
  listing_date_key   INT,
  status_key         INT,         -- active / pending / sold / removed
  price_listed       DECIMAL(12,2),
  view_count         INT,
  message_count      INT,
  days_to_sale       INT
);

-- Grain: one row per order (transactional fact).
CREATE TABLE fact_order (
  order_key          BIGINT,
  listing_key        BIGINT,
  buyer_key          BIGINT,
  seller_key         BIGINT,
  category_key       BIGINT,
  order_date_key     INT,
  ship_date_key      INT,
  quantity           INT,
  gross_amount       DECIMAL(12,2),
  net_amount         DECIMAL(12,2),
  shipping_fee       DECIMAL(12,2),
  order_status       VARCHAR(20)
);

-- Grain: one row per seller per day (periodic snapshot).
CREATE TABLE fact_seller_daily (
  seller_key         BIGINT,
  date_key           INT,
  active_listings    INT,
  listings_created   INT,
  listings_sold      INT,
  gross_sales        DECIMAL(14,2),
  unique_viewers     INT,
  unique_messagers   INT,
  avg_response_min   DECIMAL(8,2),
  seller_rating      DECIMAL(3,2)
);

-- Conformed dimensions (SCD2 on seller, category; SCD1 on others).
CREATE TABLE dim_seller (
  seller_key         BIGINT,
  seller_id          VARCHAR(40),
  seller_name        VARCHAR(80),
  tier               VARCHAR(20),     -- casual / power / business
  city               VARCHAR(60),
  effective_from     DATE,
  effective_to       DATE,
  is_current         BOOLEAN
);

CREATE TABLE dim_category (
  category_key       BIGINT,
  category_id        VARCHAR(40),
  category_name      VARCHAR(100),
  parent_category    VARCHAR(100),
  effective_from     DATE,
  effective_to       DATE,
  is_current         BOOLEAN
);

CREATE TABLE dim_date ( date_key INT PRIMARY KEY, full_date DATE, day_of_week VARCHAR(10), month INT, quarter INT, year INT );
CREATE TABLE dim_location ( location_key BIGINT, city VARCHAR(60), region VARCHAR(60), country VARCHAR(60) );
"""