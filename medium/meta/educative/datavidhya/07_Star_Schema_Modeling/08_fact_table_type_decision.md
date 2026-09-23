# Fact Table Type Decision

## Problem
At Meta we build many data products and must choose the right fact
table type: transactional snapshot, periodic snapshot, or
accumulating snapshot. Choosing wrong leads to over-counted metrics,
lossy aggregations, or pipelines that cannot answer "where in the
lifecycle is this entity?"

## How to Think
1. Transactional snapshot - one row per discrete event:
   - News Feed impression, click, hide.
   - Marketplace order placed.
   - Message sent.
   - Best for: event-level analytics, freshness, ML features.
2. Periodic snapshot - one row per entity per time period:
   - Advertiser daily balance.
   - Group member count per day.
   - Account active_users per day.
   - Best for: "what was the level at end of period?" queries.
3. Accumulating snapshot - one row per process lifecycle:
   - Order: order_date, ship_date, delivery_date, return_date.
   - Creator payout: revenue_date, eligibility_date, payout_date.
   - Job application: applied_date, screen_date, offer_date.
   - Best for: pipeline dashboards with multiple milestones.

## How to Remember
- **Pattern**: "Event -> transactional. State-at-period -> periodic.
  Lifecycle with milestones -> accumulating."
- **Grain mnemonic**:
  - Transactional: "One row = one event."
  - Periodic: "One row = one (entity, period)."
  - Accumulating: "One row = one process, with multiple date keys."

## Schema (DDL)
```sql
-- Transactional
CREATE TABLE fact_marketplace_order_txn (
  order_line_key BIGINT PRIMARY KEY,
  order_id VARCHAR(64), listing_key BIGINT,
  seller_key BIGINT, buyer_key BIGINT,
  date_key INT, time_key INT,
  order_amount DECIMAL(10,2), quantity INT
);

-- Periodic
CREATE TABLE fact_advertiser_balance_daily (
  balance_key BIGINT PRIMARY KEY,
  advertiser_key BIGINT, date_key INT,
  starting_spend DECIMAL(12,4),
  ending_spend DECIMAL(12,4),
  spend_today DECIMAL(12,4)
);

-- Accumulating
CREATE TABLE fact_creator_payout_pipeline (
  payout_key BIGINT PRIMARY KEY,
  creator_key BIGINT, payout_period VARCHAR(20),
  revenue_date_key INT, eligibility_date_key INT,
  review_date_key INT, approval_date_key INT,
  payout_date_key INT,
  payout_amount_usd DECIMAL(12,4),
  current_status VARCHAR(30)
);
```

## Common Mistakes
- Using periodic snapshot for event-grain data (loses intra-day detail).
- Using transactional for state-at-period metrics (huge rows, slow scans).
- Using accumulating for events with no defined milestones.

## AI Use Cases
- Pick the right grain for fresh ML features (transactional wins).
- Build pipeline-health dashboards from accumulating snapshots.
- Forecast periodic metrics using time-series models on snapshots.
