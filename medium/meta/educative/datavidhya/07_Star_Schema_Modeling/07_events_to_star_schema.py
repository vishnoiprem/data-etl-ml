"""
Problem 07: Events Table -> Star Schema with Shared Dimensions
Meta product: "Meta Platform Events -> Conformed Star Schema"

How to Think:
- Source: a single wide events table (event_name, user_id, timestamp,
  payload JSON) for News Feed, Reels, Stories, Marketplace, etc.
- Conformed dimensions across the platform: dim_user, dim_date, dim_time,
  dim_device, dim_country, dim_app_surface.
- One fact per logical event type, all sharing the conformed dims.
- Why split: different event types have different metrics.

How to Remember:
- "One event type, one fact" - even when source is one big events table.
- Conformed dims let us join any two facts in BI without key drift.
- Junk dim (event_type, surface, device_class) absorbs low-cardinality flags.

AI Use Cases
- Cross-surface user engagement scoring.
- Unified feature store: same dim keys across models.
- Single user view across Feed, Reels, Stories, Marketplace.
"""

DDL = """
-- Source (deconstructed): raw event stream becomes multiple facts.
-- raw_event_payload table is for replay; production BI uses the facts.

-- fact_feed_event (subset of events from News Feed)
CREATE TABLE fact_feed_event (
  feed_event_key BIGINT PRIMARY KEY,
  user_key       BIGINT NOT NULL,
  post_key       BIGINT,
  author_key     BIGINT,
  date_key       INT    NOT NULL,
  time_key       INT,
  surface_key    BIGINT,
  device_key     BIGINT,
  country_key    BIGINT,
  event_type_key BIGINT,                  -- junk dim: impression, click, hide
  dwell_ms       INT,
  rank_position  INT,
  payload        JSON
);

-- fact_reel_event (subset from Reels)
CREATE TABLE fact_reel_event (
  reel_event_key BIGINT PRIMARY KEY,
  user_key       BIGINT, reel_key BIGINT, creator_key BIGINT,
  date_key INT, time_key INT,
  surface_key BIGINT, device_key BIGINT, country_key BIGINT,
  event_type_key BIGINT,                  -- view, like, share, complete
  watch_ms INT, completion_rate DECIMAL(5,4)
);

-- fact_story_event (subset from Stories)
CREATE TABLE fact_story_event (
  story_event_key BIGINT PRIMARY KEY,
  user_key BIGINT, story_key BIGINT,
  date_key INT, time_key INT,
  surface_key BIGINT, device_key BIGINT, country_key BIGINT,
  event_type_key BIGINT,                  -- impression, tap_forward, exit
  view_duration_ms INT
);

-- Shared / conformed dimensions:
-- dim_user (SCD2), dim_date, dim_time, dim_country (SCD2),
-- dim_surface (SCD1), dim_device (SCD1).

-- dim_event_type (junk dim)
CREATE TABLE dim_event_type (
  event_type_key  BIGINT PRIMARY KEY,
  event_name      VARCHAR(50),            -- 'impression','click','hide'
  category        VARCHAR(50)             -- 'positive','negative','neutral'
);
"""