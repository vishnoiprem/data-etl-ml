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

# ---- MySQL way ----------------------------------------------------------
# The star-schema DDL above is portable to MySQL with these adjustments:
#  - BOOLEAN -> TINYINT(1) (MySQL aliases BOOLEAN to TINYINT(1); explicit is clearer)
#  - DECIMAL/NUMBER precision is fine.
#  - Add ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 to every CREATE TABLE.
#
# Example for fact_listing (apply the same pattern to the other 5 tables):
#   CREATE TABLE fact_listing (
#     listing_key      BIGINT PRIMARY KEY,
#     seller_key       BIGINT,
#     category_key     BIGINT,
#     location_key     BIGINT,
#     listing_date_key INT,
#     status_key       INT,
#     price_listed     DECIMAL(12,2),
#     view_count       INT,
#     message_count    INT,
#     days_to_sale     INT
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# Sample dimension load (one row per dim):
#   INSERT INTO dim_date (date_key, full_date, day_of_week, month, quarter, year)
#   VALUES (20260101, '2026-01-01', 'Thursday', 1, 1, 2026);
#
#   INSERT INTO dim_seller (seller_key, seller_id, seller_name, tier, city,
#                           effective_from, effective_to, is_current)
#   VALUES (1, 's-001', 'Alice', 'power', 'Seattle', '2026-01-01', '9999-12-31', 1);
#
#   INSERT INTO fact_seller_daily (seller_key, date_key, active_listings,
#       listings_created, listings_sold, gross_sales, unique_viewers,
#       unique_messagers, avg_response_min, seller_rating)
#   VALUES (1, 20260101, 10, 2, 1, 250.00, 87, 12, 5.50, 4.80);
#
# Query (GMV by seller using conformed dims):
#   SELECT s.seller_id,
#          SUM(f.gross_sales) AS gmv,
#          SUM(f.listings_sold) AS units_sold
#   FROM fact_seller_daily f
#   JOIN dim_seller s ON f.seller_key = s.seller_key AND s.is_current = 1
#   WHERE f.date_key BETWEEN 20260101 AND 20260131
#   GROUP BY s.seller_id
#   ORDER BY gmv DESC;
# Caveat: SCD2 dimensions carry effective_from / effective_to / is_current. Always
# filter to is_current=1 unless you specifically need point-in-time history.