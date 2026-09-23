# Reels Watch-Session Model

## Problem
Reels needs a data model that answers: how long are watch sessions, how many reels
fit in a session, what makes a user keep watching, and which reels drive exits.
Sessions are the natural unit of analysis, not individual videos.

## How to Think
1. List the metrics:
   - Session duration, videos-per-session, completion %, like/share/save per session.
   - Per-reel engagement during a session.
   - Entry-source breakdown (profile vs explore vs share).
2. Identify the grains:
   - `fact_reels_session`: one row per session.
   - `fact_reel_view`: one row per (user, reel) view inside a session.
3. Pick fact-table types:
   - `fact_reels_session` -> accumulating snapshot if you track lifecycle stages,
     otherwise transactional (one row per session open event).
   - `fact_reel_view` -> transactional.
4. Dimensions and SCD:
   - `dim_reel` SCD2 (hashtags/audio/visibility change).
   - `dim_user` SCD2, `dim_sound` SCD1, `dim_device` SCD1.

## How to Remember
- **Pattern**: "Metrics -> Grains -> Fact table types -> Dims with SCD."
- **Grain mnemonic**:
  - "One session = one continuous viewing episode."
  - "One view = one reel shown once in a session."
- Session-level metrics (sums, ratios) live in the session fact;
  reel-level metrics live in the view fact. Don't mix.

## Schema (DDL)
```sql
CREATE TABLE fact_reels_session (
  session_key BIGINT, user_key BIGINT, session_date_key INT,
  device_key INT, entry_source_key INT,
  videos_watched INT, total_duration_ms BIGINT,
  likes_in_session INT, shares_in_session INT, saves_in_session INT,
  is_loop_heavy BOOLEAN, exit_reason VARCHAR(20)
);

CREATE TABLE fact_reel_view (
  view_key BIGINT, session_key BIGINT, user_key BIGINT, reel_key BIGINT,
  author_key BIGINT, position_in_session INT, view_date_key INT,
  watch_duration_ms INT, video_duration_ms INT, completion_pct DECIMAL(5,2),
  liked BOOLEAN, shared BOOLEAN, saved BOOLEAN
);

CREATE TABLE dim_reel (
  reel_key BIGINT, reel_id VARCHAR(40), author_user_key BIGINT,
  sound_key BIGINT, duration_ms INT, hashtags VARCHAR(20),
  effective_from DATE, effective_to DATE, is_current BOOLEAN
);

CREATE TABLE dim_user (
  user_key BIGINT, user_id VARCHAR(40), age_bucket VARCHAR(10),
  country VARCHAR(60), locale VARCHAR(20), tenure_days INT,
  effective_from DATE, effective_to DATE, is_current BOOLEAN
);

CREATE TABLE dim_sound ( sound_key BIGINT, sound_id VARCHAR(40), sound_name VARCHAR(120), artist VARCHAR(120), is_original BOOLEAN );
CREATE TABLE dim_device ( device_key INT, device_type VARCHAR(20), os VARCHAR(20), browser VARCHAR(20) );
CREATE TABLE dim_entry_source ( source_key INT, source_name VARCHAR(40) );
CREATE TABLE dim_date ( date_key INT PRIMARY KEY, full_date DATE, day_of_week VARCHAR(10), month INT, quarter INT, year INT );
```

## Common Mistakes
- Modeling each reel impression as a "session" -> destroys session-level metrics.
- Forgetting `position_in_session` -> cannot model drop-off curves.
- Storing `total_duration_ms` only at the view grain -> must aggregate carefully.
- Ignoring entry source; it is the strongest predictor of session length.

## AI Use Cases
- Predict session length from the first 3 reels' completion %.
- Cluster sessions into "binge", "casual", "bounce" for product analytics.
- Next-reel recommendation conditioned on session position.