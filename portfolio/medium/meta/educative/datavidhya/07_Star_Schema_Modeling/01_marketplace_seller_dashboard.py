"""
Problem 01: Facebook Marketplace Seller Dashboard
Meta product: "Facebook Marketplace - Seller Analytics"

How to Think:
- Three grains matter: (1) listing-level (a seller posted an item),
  (2) order-level (a buyer purchased), (3) message-level (buyer-seller chat).
- Each grain answers a different metric: inventory, revenue, response rate.
- Build three fact tables that share dimensions (seller, buyer, category, date).

How to Remember:
- Grain statement must be the first DDL comment.
- One fact per grain, never mix grains.
- Share dims to enable cross-grain joins in BI tools.

AI Use Cases
- Power seller-level recommendations (churn risk, listing optimization).
- Forecast seller GMV per category per region.
- Detect fraudulent seller patterns across listing/order/message grains.
"""

DDL = """
-- fact_listing: one row per listing created by a seller
CREATE TABLE fact_listing (
  listing_key        BIGINT PRIMARY KEY,
  seller_key         BIGINT NOT NULL,
  category_key       BIGINT NOT NULL,
  date_key           INT    NOT NULL,   -- listing_created_date
  location_key       BIGINT NOT NULL,
  listing_price      DECIMAL(10,2),
  listing_status     VARCHAR(20),       -- active / sold / expired
  view_count         INT,
  favorite_count     INT,
  FOREIGN KEY (seller_key)   REFERENCES dim_seller(seller_key),
  FOREIGN KEY (category_key) REFERENCES dim_category(category_key),
  FOREIGN KEY (date_key)     REFERENCES dim_date(date_key)
);

-- fact_order: one row per completed order
CREATE TABLE fact_order (
  order_key          BIGINT PRIMARY KEY,
  listing_key        BIGINT NOT NULL,   -- links back to fact_listing
  seller_key         BIGINT NOT NULL,
  buyer_key          BIGINT NOT NULL,
  date_key           INT    NOT NULL,   -- order_date
  order_amount       DECIMAL(10,2),
  shipping_amount    DECIMAL(10,2),
  quantity           INT,
  FOREIGN KEY (seller_key) REFERENCES dim_seller(seller_key),
  FOREIGN KEY (buyer_key)  REFERENCES dim_buyer(buyer_key)
);

-- fact_message: one row per buyer-seller conversation message
CREATE TABLE fact_message (
  message_key        BIGINT PRIMARY KEY,
  seller_key         BIGINT NOT NULL,
  buyer_key          BIGINT NOT NULL,
  date_key           INT    NOT NULL,   -- message_sent_date
  time_key           INT,
  conversation_id    VARCHAR(64),
  message_length     INT,
  has_attachment     BOOLEAN,
  is_first_response  BOOLEAN           -- for seller response-time metric
);

-- dim_seller (SCD Type 2)
CREATE TABLE dim_seller (
  seller_key         BIGINT PRIMARY KEY,
  seller_id          VARCHAR(64),
  seller_name        VARCHAR(200),
  city               VARCHAR(100),
  region             VARCHAR(100),
  seller_rating      DECIMAL(3,2),
  effective_from     DATE,
  effective_to       DATE,
  is_current         BOOLEAN
);

-- dim_buyer (SCD Type 2)
CREATE TABLE dim_buyer (
  buyer_key          BIGINT PRIMARY KEY,
  buyer_id           VARCHAR(64),
  city               VARCHAR(100),
  country            VARCHAR(100),
  effective_from     DATE,
  effective_to       DATE,
  is_current         BOOLEAN
);

-- dim_category (SCD Type 1 - changes are corrections)
CREATE TABLE dim_category (
  category_key       BIGINT PRIMARY KEY,
  category_name      VARCHAR(200),
  parent_category    VARCHAR(200)
);

-- dim_location (SCD Type 2 - city names change)
CREATE TABLE dim_location (
  location_key       BIGINT PRIMARY KEY,
  city               VARCHAR(100),
  state              VARCHAR(100),
  country            VARCHAR(100),
  effective_from     DATE,
  effective_to       DATE,
  is_current         BOOLEAN
);

-- dim_date (conformed dimension - shared by all 3 facts)
CREATE TABLE dim_date (
  date_key           INT PRIMARY KEY,
  full_date          DATE,
  day_of_week        VARCHAR(10),
  month              INT,
  quarter            INT,
  year               INT,
  is_holiday         BOOLEAN
);
"""