# Facebook Marketplace Seller Dashboard

## Problem
Meta is building a seller analytics dashboard for Facebook Marketplace.
Sellers need to see how their listings perform, how many messages they
receive, and what revenue they generate. We need a star schema that
supports three distinct measurement grains so each dashboard tile
maps cleanly to a single fact table.

## How to Think
1. List the metrics the dashboard must answer:
   - Active listings per category per day.
   - Orders per seller per week (GMV).
   - First-response time and message volume.
   - Conversion: views -> messages -> orders.
2. Identify the grains - one row = one:
   - Listing created.
   - Order placed.
   - Message sent in a conversation.
3. Pick fact-table type per grain:
   - All three are transactional snapshots (event-level rows).
4. Design dimensions and SCD choices:
   - `dim_seller` and `dim_buyer` use SCD2 (history matters for cohort
     analysis and trend reports).
   - `dim_category` uses SCD1 (category corrections overwrite).
   - `dim_location` uses SCD2 (city/region reassignments).
   - `dim_date` is a conformed dimension shared by all three facts.

## How to Remember
- **Pattern**: "Metrics -> Grains -> Fact table types -> Dims with SCD."
- **Grain mnemonic**: "One row = one listing / one order / one message."
- **Conformed dims** (date, location, category) let you drill across
  facts without mismatched joins.
- A single seller key exists in all three facts, enabling 360-degree
  seller reporting.

## Schema (DDL)
```sql
-- fact_listing: one row per listing created
CREATE TABLE fact_listing (
  listing_key    BIGINT PRIMARY KEY,
  seller_key     BIGINT NOT NULL,
  category_key   BIGINT NOT NULL,
  date_key       INT    NOT NULL,
  location_key   BIGINT NOT NULL,
  listing_price  DECIMAL(10,2),
  listing_status VARCHAR(20),
  view_count     INT,
  favorite_count INT
);

-- fact_order: one row per completed order
CREATE TABLE fact_order (
  order_key       BIGINT PRIMARY KEY,
  listing_key     BIGINT NOT NULL,
  seller_key      BIGINT NOT NULL,
  buyer_key       BIGINT NOT NULL,
  date_key        INT    NOT NULL,
  order_amount    DECIMAL(10,2),
  shipping_amount DECIMAL(10,2),
  quantity        INT
);

-- fact_message: one row per message in a conversation
CREATE TABLE fact_message (
  message_key       BIGINT PRIMARY KEY,
  seller_key        BIGINT NOT NULL,
  buyer_key         BIGINT NOT NULL,
  date_key          INT    NOT NULL,
  conversation_id   VARCHAR(64),
  message_length    INT,
  has_attachment    BOOLEAN,
  is_first_response BOOLEAN
);

CREATE TABLE dim_seller (
  seller_key BIGINT PRIMARY KEY, seller_id VARCHAR(64),
  seller_name VARCHAR(200), city VARCHAR(100),
  effective_from DATE, effective_to DATE, is_current BOOLEAN
);
-- dim_buyer, dim_category, dim_location, dim_date defined similarly.
```

## Common Mistakes
- Mixing order and message data into one fact (different grains).
- Tracking seller rating as SCD1 when historical rating is needed for
  cohort comparisons.
- Forgetting `dim_date` as conformed - duplicated per fact breaks
  cross-grain dashboards.

## AI Use Cases
- Predict seller churn from listing decay + message response time.
- Recommend optimal listing price per category per location.
- Flag fraudulent seller patterns spanning all three grains.
