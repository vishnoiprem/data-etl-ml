# Junk / Degenerate Dimensions

## Problem
Meta events have many low-cardinality attributes: event type
(impression/click/hide), device class (mobile/tablet/TV), OS, browser,
network type, app version, and surface. Each is a tiny lookup but
adding all as separate dim tables explodes the model. Likewise, every
event has a transaction identifier (order_id, message_id) that has
no descriptive context - we still need to store it.

## How to Think
1. List the flags / low-cardinality attributes that would each become
   a separate dim if naive-modeled.
2. Bundle them into a single junk dimension with one surrogate key.
3. Identify transactional IDs that live only in the fact - they are
   degenerate dimensions.
4. Use the junk dim FK in the fact; use degenerate dim IDs for
   drill-through from aggregates to row detail.

## How to Remember
- **Pattern**: "Bundle low-cardinality flags into one junk dim.
  Embed transactional IDs as degenerate dims."
- **Grain mnemonic**: "One junk key replaces N flag columns."
- Junk dim rows are tiny (KBs), fully cached, great for BI filtering.
- Degenerate dim IDs are usually VARCHAR(64) - non-additive, used only
  for traceability and drill-through.

## Schema (DDL)
```sql
CREATE TABLE dim_event_junk (
  event_junk_key BIGINT PRIMARY KEY,
  event_type VARCHAR(30), event_category VARCHAR(30),
  device_class VARCHAR(20), os_name VARCHAR(20),
  browser_name VARCHAR(20), network_type VARCHAR(20),
  app_version VARCHAR(20), surface_type VARCHAR(20)
);

CREATE TABLE fact_user_event (
  event_key BIGINT PRIMARY KEY,
  user_key BIGINT, date_key INT, time_key INT,
  event_junk_key BIGINT,
  post_key BIGINT, dwell_ms INT, is_engaged BOOLEAN,
  transaction_id VARCHAR(64)             -- DEGENERATE dim
);

CREATE TABLE fact_order_txn (
  order_key BIGINT PRIMARY KEY,
  order_id VARCHAR(64),                 -- DEGENERATE dim
  buyer_key BIGINT, seller_key BIGINT,
  date_key INT, order_amount DECIMAL(10,2), quantity INT
);
```

## Common Mistakes
- Creating a separate dim table for each flag (8 dims of 4 rows each).
- Storing raw flag strings in the fact (denormalized, hard to filter).
- Promoting degenerate dim IDs to their own dim with no context.

## AI Use Cases
- Use `event_junk_key` as a categorical embedding input.
- App_version dimension captures release-cohort drift features.
- Degenerate IDs enable per-transaction debugging from dashboards.
