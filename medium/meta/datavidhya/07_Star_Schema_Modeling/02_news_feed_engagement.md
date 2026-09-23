# News Feed Engagement Analytics

## Problem
Facebook News Feed needs to analyze how stories (posts) perform: how often they were
shown, how users reacted, and how often they were shared. Each event has its own
grain and its own business meaning.

## How to Think
1. List the metrics:
   - Impressions per post, dwell time, completion-rate for video.
   - Reactions by type (like, love, haha, ...).
   - Shares by destination (timeline, group, DM, external).
2. Identify the grains:
   - `fact_post_impression`: one row per (viewer, post, render event).
   - `fact_post_reaction`: one row per (reactor, post, reaction type).
   - `fact_post_share`: one row per share event.
3. Pick fact-table type:
   - All three are transactional (event-level).
   - Optionally a `fact_post_daily` periodic snapshot for quick dashboard queries.
4. Dimensions and SCD:
   - `dim_post` SCD2 (post_type / page_or_profile can change).
   - `dim_user` SCD2 (country, locale, tenure shift over time).
   - `dim_device`, `dim_reaction_type` SCD1.

## How to Remember
- **Pattern**: "Metrics -> Grains -> Fact table types -> Dims with SCD."
- **Grain mnemonic**:
  - "One impression = one viewer saw one post once."
  - "One reaction = one user pressed one reaction type on one post."
  - "One share = one user shared one post once."
- A reaction is NOT an impression. Never collapse them.

## Schema (DDL)
```sql
CREATE TABLE fact_post_impression (
  impression_key BIGINT, post_key BIGINT, viewer_user_key BIGINT,
  author_user_key BIGINT, date_key INT, time_key INT,
  device_key INT, placement_key INT, is_video BOOLEAN, dwell_ms INT
);

CREATE TABLE fact_post_reaction (
  reaction_key BIGINT, post_key BIGINT, reactor_user_key BIGINT,
  author_user_key BIGINT, reaction_type_key INT,
  reaction_date_key INT, device_key INT
);

CREATE TABLE fact_post_share (
  share_key BIGINT, post_key BIGINT, sharer_user_key BIGINT,
  author_user_key BIGINT, share_destination_key INT, share_date_key INT
);

CREATE TABLE dim_post (
  post_key BIGINT, post_id VARCHAR(40), author_user_key BIGINT,
  post_type VARCHAR(20), page_or_profile VARCHAR(20),
  effective_from DATE, effective_to DATE, is_current BOOLEAN
);

CREATE TABLE dim_user (
  user_key BIGINT, user_id VARCHAR(40), age_bucket VARCHAR(10),
  gender VARCHAR(10), country VARCHAR(60), locale VARCHAR(20),
  tenure_days INT, effective_from DATE, effective_to DATE, is_current BOOLEAN
);

CREATE TABLE dim_reaction_type ( reaction_type_key INT, reaction_name VARCHAR(20), is_positive BOOLEAN );
CREATE TABLE dim_device ( device_key INT, device_type VARCHAR(20), os VARCHAR(20), browser VARCHAR(20) );
CREATE TABLE dim_date ( date_key INT PRIMARY KEY, full_date DATE, day_of_week VARCHAR(10), month INT, quarter INT, year INT );
```

## Common Mistakes
- Conflating reaction count and impression count in one fact -> wrong ratios.
- Using post_id (natural key) as the join key -> duplicates after edits.
- Forgetting to dimension `placement` (Top-of-feed vs inline changes dwell massively).
- Treating reactions as numeric "count" only; the type dimension is critical.

## AI Use Cases
- Predict post virality from early impression-to-share slope.
- Detect engagement-bait (high share, low dwell, low positive reaction).
- Recommend pages based on reaction co-occurrence vectors.