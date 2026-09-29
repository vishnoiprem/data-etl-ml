# Marketplace Seller Dashboard (3 fact tables at 3 grains)

## Problem
Facebook Marketplace gives sellers a dashboard showing what they listed, what sold,
how much they earned, and how engaged buyers are. The metrics span three different
business events, so they must live in three different fact tables, all sharing the
same conformed dimensions.

## How to Think
1. List the metrics the dashboard must answer:
   - Listings posted, active listings, days-on-market.
   - Orders, items sold, GMV, conversion rates.
   - Daily seller activity (views, messages, response time, rating).
2. Identify the grains:
   - `fact_listing`: one row per listing (lifecycle of the listing itself).
   - `fact_order`: one row per order (transaction event).
   - `fact_seller_daily`: one row per seller per day (periodic snapshot).
3. Pick fact-table types:
   - listing -> transactional (one row per listing-creation event).
   - order -> transactional (one row per order line).
   - seller_daily -> periodic snapshot (one row per day, refreshed).
4. Design dimensions with SCD:
   - SCD2 on `dim_seller` and `dim_category` (attributes change over time).
   - SCD1 on `dim_location`, `dim_date`.
5. Conformed dims (seller, category, date, location) appear in all three facts.

## How to Remember
- **Pattern**: "Metrics -> Grains -> Fact table types -> Dims with SCD."
- **Grain mnemonic**:
  - "One row = one listing."
  - "One row = one order."
  - "One row = one seller per day."
- **Conformed dim rule**: A dim used by multiple facts must have the same key,
  same meaning, same attributes across all facts.

## Schema (DDL)
```sql
CREATE TABLE fact_listing (
  listing_key BIGINT, seller_key BIGINT, category_key BIGINT,
  location_key BIGINT, listing_date_key INT, status_key INT,
  price_listed DECIMAL(12,2), view_count INT, message_count INT, days_to_sale INT
);

CREATE TABLE fact_order (
  order_key BIGINT, listing_key BIGINT, buyer_key BIGINT, seller_key BIGINT,
  category_key BIGINT, order_date_key INT, ship_date_key INT,
  quantity INT, gross_amount DECIMAL(12,2), net_amount DECIMAL(12,2),
  shipping_fee DECIMAL(12,2), order_status VARCHAR(20)
);

CREATE TABLE fact_seller_daily (
  seller_key BIGINT, date_key INT, active_listings INT,
  listings_created INT, listings_sold INT, gross_sales DECIMAL(14,2),
  unique_viewers INT, unique_messagers INT,
  avg_response_min DECIMAL(8,2), seller_rating DECIMAL(3,2)
);

CREATE TABLE dim_seller (
  seller_key BIGINT, seller_id VARCHAR(40), seller_name VARCHAR(80),
  tier VARCHAR(20), city VARCHAR(60),
  effective_from DATE, effective_to DATE, is_current BOOLEAN
);

CREATE TABLE dim_category (
  category_key BIGINT, category_id VARCHAR(40),
  category_name VARCHAR(100), parent_category VARCHAR(100),
  effective_from DATE, effective_to DATE, is_current BOOLEAN
);

CREATE TABLE dim_date ( date_key INT PRIMARY KEY, full_date DATE, day_of_week VARCHAR(10), month INT, quarter INT, year INT );
CREATE TABLE dim_location ( location_key BIGINT, city VARCHAR(60), region VARCHAR(60), country VARCHAR(60) );
```

## Common Mistakes
- Putting order metrics inside `fact_listing` -> corrupts grain, double counts.
- Using `dim_seller` as SCD1 when sellers can change tier/city -> history lost.
- Calling `fact_seller_daily` a "transaction" fact -> it is a periodic snapshot.
- Mixing seller-grain rows with listing-grain rows in the same dashboard query
  without an aggregate awareness rule.

## AI Use Cases
- Forecast seller GMV by category and city.
- Detect likely-to-churn sellers (drop in listing creation).
- Recommend price band per category from sell-through features.

## Interview Questions (natural flow)

These escalate from scope to production reality. Ask in order; each answer unlocks the next.

### 1. Scope
> "Walk me through what this dashboard is meant to answer. What does the seller see when they log in Monday morning?"

*Why it's natural:* anchors the model in user value, not table counts. Tests if you start with the question or jump to the schema.

### 2. The split
> "You split listing, order, and seller-daily into three facts. Why three? What would break if I asked you to merge them into one wide table?"

*Why it's natural:* forces the candidate to defend grain purity. The right answer references double-counting and aggregate-awareness.

### 3. The snapshot
> "`fact_seller_daily` is a periodic snapshot. How do you refresh it, and what happens to it if a seller is deleted mid-quarter?"

*Why it's natural:* tests understanding of snapshot semantics vs transactional. Real production answer involves partition swaps or late-arriving rows.

### 4. SCD2 history
> "A seller upgrades from 'standard' to 'pro' tier on Mar 15. In Q2 GMV-by-tier analysis, does the March numbers land under 'standard' or 'pro'?"

*Why it's natural:* SCD2 is only valuable if you know when the historical version applies. Most candidates hand-wave this.

### 5. Conformed-dim failure mode
> "Marketing adds a new seller attribute 'preferred_category' to `dim_seller`. Ops renames the column to 'favorite_cat'. What breaks in the three fact tables?"

*Why it's natural:* tests if the candidate understands that conformed means *conformed in name AND semantics*, not just shared key.

### 6. Metric integrity
> "PM asks for 'conversion rate per listing'. What's the denominator — views, messages, or saved searches? Where in the schema does that decision live?"

*Why it's natural:* exposes the gap between schema and business definition. The honest answer is "it's a metric-layer decision, not a schema column."

### 7. Scale
> "At 50M orders this design is fine. At 5B, what breaks first, and what's the cheapest fix you'd ship?"

*Why it's natural:* signals you understand operational reality — partitioning, pre-aggregation, columnar formats all live here.

### 8. Extensibility
> "PM wants a 'live auctions' channel tomorrow. How many files do you touch, and which one is risky?"

*Why it's natural:* simulates real work. Right answer is small (a new fact + dim), but the *risky* part is the seller_daily snapshot logic.