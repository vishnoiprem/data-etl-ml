"""
Problem 08: Fact Table Type Decision
Meta product: "Meta Data Warehouse - Fact Type Patterns"

How to Think:
- Three fact types to know cold:
  1) Transactional snapshot - one row per event (impression, click,
     message sent). Most Meta product facts are this.
  2) Periodic snapshot - one row per entity per time period
     (account_balance_daily, group_member_daily).
  3) Accumulating snapshot - one row per lifecycle, with date keys
     for each milestone (order: order_date, ship_date, delivery_date).
- Decision tree:
  - Discrete event that occurs once -> transactional.
  - Level/running state at a time grain -> periodic.
  - Process with known milestones -> accumulating.

How to Remember:
- Transactional = point-in-time event.
- Periodic = state-at-end-of-period.
- Accumulating = pipeline lifecycle row with multiple date keys.

AI Use Cases
- Choose right grain for feature freshness (transactional is freshest).
- Avoid over-aggregation (periodic loses intra-day detail).
- Build pipeline-progress dashboards with accumulating snapshot.
"""

DDL = """
-- 1) Transactional snapshot example: a Marketplace order line.
CREATE TABLE fact_marketplace_order_txn (
  order_line_key  BIGINT PRIMARY KEY,
  order_id        VARCHAR(64),
  listing_key     BIGINT,
  seller_key      BIGINT,
  buyer_key       BIGINT,
  date_key        INT,
  time_key        INT,
  order_amount    DECIMAL(10,2),
  quantity        INT,
  payment_method  VARCHAR(20)
);

-- 2) Periodic snapshot example: advertiser daily account balance.
CREATE TABLE fact_advertiser_balance_daily (
  balance_key     BIGINT PRIMARY KEY,
  advertiser_key  BIGINT,
  date_key        INT,
  starting_spend  DECIMAL(12,4),
  ending_spend    DECIMAL(12,4),
  spend_today     DECIMAL(12,4),
  impressions_today INT,
  clicks_today    INT,
  conversions_today INT
);

-- 3) Accumulating snapshot example: Reels creator payout pipeline.
CREATE TABLE fact_creator_payout_pipeline (
  payout_key       BIGINT PRIMARY KEY,
  creator_key      BIGINT,
  payout_period    VARCHAR(20),           -- '2026-09'
  revenue_date_key INT,                   -- revenue earned on
  eligibility_date_key INT,               -- eligibility checked on
  review_date_key  INT,                    -- compliance reviewed on
  approval_date_key INT,                   -- finance approved on
  payout_date_key  INT,                    -- actually paid on
  payout_amount_usd DECIMAL(12,4),
  current_status   VARCHAR(30)            -- 'pending','approved','paid','failed'
);
"""