"""
Problem 09: Junk / Degenerate Dimensions
Meta product: "Meta Platform - Low-Cardinality Attributes"

How to Think:
- Junk dim: a small dimension that bundles many low-cardinality flags
  (event_type, device_class, OS, browser, app_version, network_type).
- Degenerate dim: a dimension stored directly in the fact (no separate
  dim table) - usually transactional IDs like order_id, transaction_id,
  message_id.
- Both keep the fact table clean and reduce NULLs.

How to Remember:
- Junk dim = small lookup of unrelated flags.
- Degenerate dim = transaction ID embedded in fact row.
- Avoid creating a dim table for each flag - bundle into one junk dim.

AI Use Cases
- Use junk dim keys as categorical features in models.
- Degenerate dim IDs enable drill-through from aggregate to row detail.
- Versioning via junk dim captures app_release cohort features.
"""

DDL = """
-- Single junk dim covering many low-cardinality attributes
CREATE TABLE dim_event_junk (
  event_junk_key    BIGINT PRIMARY KEY,
  event_type        VARCHAR(30),          -- 'impression','click','hide'
  event_category    VARCHAR(30),          -- 'positive','negative','neutral'
  device_class      VARCHAR(20),          -- 'mobile','tablet','desktop','tv'
  os_name           VARCHAR(20),          -- 'iOS','Android','Web','SmartTV'
  browser_name      VARCHAR(20),          -- 'Chrome','Safari','FB-InApp','Other'
  network_type      VARCHAR(20),          -- 'wifi','cellular','ethernet','unknown'
  app_version       VARCHAR(20),          -- 'fb.android.451.0.0.30'
  surface_type      VARCHAR(20)           -- 'feed','reels','stories','marketplace'
);

-- Fact uses one junk dim FK instead of 8 flag columns
CREATE TABLE fact_user_event (
  event_key         BIGINT PRIMARY KEY,
  user_key          BIGINT NOT NULL,
  date_key          INT    NOT NULL,
  time_key          INT,
  event_junk_key    BIGINT,               -- single FK to junk dim
  post_key          BIGINT,
  dwell_ms          INT,
  is_engaged        BOOLEAN,
  transaction_id    VARCHAR(64)           -- DEGENERATE dim: order_id, msg_id
);

-- Degenerate dimension example: order transaction ID lives in fact
CREATE TABLE fact_order_txn (
  order_key         BIGINT PRIMARY KEY,
  order_id          VARCHAR(64),          -- DEGENERATE dim - no separate dim_order
  buyer_key         BIGINT, seller_key    BIGINT,
  date_key          INT,
  order_amount      DECIMAL(10,2),
  quantity          INT
);
-- No dim_order because there is no additional descriptive context
-- beyond the fact; the ID is enough for drill-through.
"""