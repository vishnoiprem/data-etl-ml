# News Feed Engagement Analytics

## Problem
Meta wants to analyze News Feed engagement: how many impressions a
post gets, what reactions it received, and whether it was shared.
The schema must support both creator-side analytics ("how is my post
performing?") and consumer-side ("what kind of content do I engage
with?"). Volume is in the trillions of rows per day.

## How to Think
1. List the metrics:
   - Impressions per post per surface per day.
   - Reaction distribution per post (like vs love vs angry).
   - Share velocity (shares in first 1h / 24h).
   - Negative feedback rate (hide, "see less").
2. Identify the grain - one row = one impression event. Reactions and
   shares can co-occur with the impression, so model them as columns
   with flags rather than separate fact tables to keep BI simple.
3. Pick fact-table type: transactional snapshot (event-grain).
4. Design dimensions and SCD choices:
   - `dim_post` SCD2 because posts are edited, unlisted, or deleted.
   - `dim_user` SCD2 because demographics and location change.
   - `dim_surface` SCD1 (small lookup, corrections only).
   - `dim_date` and `dim_time` are conformed.

## How to Remember
- **Pattern**: "Event-grain fact + flags + conformed dims."
- **Grain mnemonic**: "One row = one impression event."
- For very wide tables, consider splitting reaction events into a
  separate `fact_reaction` if the cardinality balloons.

## Schema (DDL)
```sql
CREATE TABLE fact_feed_engagement (
  engagement_key  BIGINT PRIMARY KEY,
  post_key        BIGINT, viewer_key      BIGINT, author_key      BIGINT,
  date_key        INT,    time_key        INT,    surface_key     BIGINT,
  rank_position   INT,
  reaction_type   VARCHAR(20),
  is_reaction     BOOLEAN, is_share BOOLEAN,
  is_hide         BOOLEAN, is_comment BOOLEAN,
  dwell_time_ms   INT
);
-- dim_post (SCD2), dim_user (SCD2), dim_surface (SCD1),
-- dim_date, dim_time.
```

## Common Mistakes
- Storing aggregate counters on `dim_post` - they break the star schema
  rule that all metrics live in facts.
- Treating shares as a separate fact when they share the impression
  grain - causes 2x row scans in joins.
- Using SCD1 on `dim_user` and losing historical demographics for
  cohort analysis.

## AI Use Cases
- Train News Feed ranking models on reaction labels.
- Detect clickbait: high impression count but low dwell_time and high
  hide rate.
- Forecast viral posts from share velocity in the first hour.
