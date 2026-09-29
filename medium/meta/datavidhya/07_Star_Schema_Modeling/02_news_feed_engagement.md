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

## Interview Questions (natural flow)

These escalate from scope to production reality. Ask in order; each answer unlocks the next.

### 1. Scope
> "Walk me through what News Feed analytics is supposed to answer. What's the daily question an ML engineer or ranking PM is asking?"

*Why it's natural:* anchors the model in a real consumer of the data, not the abstract idea of "engagement."

### 2. The split
> "You have three facts: impression, reaction, share. Why three instead of one `fact_engagement` wide table?"

*Why it's natural:* tests grain awareness. The cardinal-vice is mixing reactions with impressions and computing "engagement rate" — a non-additive ratio over a non-uniform denominator.

### 3. The metric trap
> "A junior analyst writes `AVG(reaction_count / impression_count)` to compute 'engagement rate.' What's wrong, and how would it show up in the dashboard?"

*Why it's natural:* classic interview answer. AVG-of-ratios is biased by post-level impression volume. The right metric is `SUM(reactions) / SUM(impressions)`.

### 4. Reaction ≠ impression
> "A user likes a post they've never seen in their feed (e.g. via a profile visit). Does that row land in `fact_post_impression`, `fact_post_reaction`, or both? Why?"

*Why it's natural:* tests understanding that impressions and reactions are different business events with different grains — the schema must allow them to exist independently.

### 5. The placement dimension
> "You have `placement_key`. PM asks why dwell time differs between 'Top of feed' and 'inline.' Walk me through the analysis."

*Why it's natural:* placement is the strongest confounder. Tests whether the candidate knows to *slice* a non-additive metric by placement before drawing conclusions.

### 6. SCD2 on dim_post
> "A post changes from 'photo' to 'video' (because the user swapped the media). For events from January, does it show up as photo or video in last-quarter's engagement analysis?"

*Why it's natural:* SCD2 application. Tests if the candidate understands that `effective_from/effective_to` on dim_post must align with the event timestamp.

### 7. Scale
> "10B impressions per day. What's the first thing to break, and what's the cheapest fix you'd ship?"

*Why it's natural:* signals production reality. Hot partitions on (post_key, date_key) are the usual answer; the fix is composite partitioning or pre-aggregation.

### 8. Edge case
> "A user reports 'I never saw this post in my feed, but I got 50 reactions on it.' Walk me through what the data model says vs what the UI says."

*Why it's natural:* tests whether the candidate can map between data semantics and user-facing reality. The data model may be right while the UI is broken — and vice versa.