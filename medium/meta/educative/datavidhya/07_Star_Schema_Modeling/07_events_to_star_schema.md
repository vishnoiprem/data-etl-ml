# Events Table to Star Schema with Shared Dimensions

## Problem
Meta's data infrastructure ingests a single wide events stream from
many products (Feed, Reels, Stories, Marketplace, Groups). Each
event has `event_name`, `user_id`, `timestamp`, and a JSON payload.
The raw stream is great for replay, but BI tools and ML pipelines
need a star schema with shared dimensions and clear facts.

## How to Think
1. List the metrics per product surface:
   - Feed: impressions, dwell, hides.
   - Reels: views, watch time, completion.
   - Stories: tap-forward, exit, replies.
2. Identify the grains - one row = one:
   - Feed event.
   - Reel event.
   - Story event.
3. Pick fact-table types:
   - All three are transactional snapshots (event-grain).
4. Design shared dimensions:
   - `dim_user` SCD2 - shared across all Meta products.
   - `dim_date`, `dim_time` - conformed time dims.
   - `dim_country` SCD2 (country reassignments).
   - `dim_surface`, `dim_device` SCD1 lookups.
   - `dim_event_type` - junk dim for low-cardinality event names.

## How to Remember
- **Pattern**: "Wide events -> N facts at N grains + conformed dims."
- **Grain mnemonic**: "One row = one product-specific event."
- Conformed dimensions = same business key, same data type, same
  meaning across all facts.

## Schema (DDL)
```sql
CREATE TABLE fact_feed_event (
  feed_event_key BIGINT PRIMARY KEY,
  user_key BIGINT, post_key BIGINT, author_key BIGINT,
  date_key INT, time_key INT,
  surface_key BIGINT, device_key BIGINT, country_key BIGINT,
  event_type_key BIGINT, dwell_ms INT, rank_position INT
);

CREATE TABLE fact_reel_event (
  reel_event_key BIGINT PRIMARY KEY,
  user_key BIGINT, reel_key BIGINT, creator_key BIGINT,
  date_key INT, time_key INT,
  surface_key BIGINT, device_key BIGINT, country_key BIGINT,
  event_type_key BIGINT,
  watch_ms INT, completion_rate DECIMAL(5,4)
);

CREATE TABLE fact_story_event (
  story_event_key BIGINT PRIMARY KEY,
  user_key BIGINT, story_key BIGINT,
  date_key INT, time_key INT,
  surface_key BIGINT, device_key BIGINT, country_key BIGINT,
  event_type_key BIGINT, view_duration_ms INT
);

CREATE TABLE dim_event_type (
  event_type_key BIGINT PRIMARY KEY,
  event_name VARCHAR(50), category VARCHAR(50)
);
-- dim_user, dim_date, dim_time, dim_country, dim_surface, dim_device.
```

## Common Mistakes
- Keeping a single wide event table in the warehouse - impossible to
  index efficiently and columns become nullable chaos.
- Using different keys for the same user across products.
- Putting low-cardinality flags (event_type) directly on the fact
  instead of a junk dim.

## AI Use Cases
- Cross-surface engagement score per user (joins across three facts).
- Unified feature store feeding ranking models.
- Anomaly detection on event volume per surface per country.
