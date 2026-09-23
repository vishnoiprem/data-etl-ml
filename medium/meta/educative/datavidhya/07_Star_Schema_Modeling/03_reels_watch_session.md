# Reels Watch-Session Model

## Problem
Reels is a short-form video feed on Instagram and Facebook. We need
to analyze how viewers watch Reels: how long they watch, whether
they loop, whether they skip, and how a watch session flows.
The model must answer "what makes a session long and engaging?"

## How to Think
1. List the metrics:
   - Average watch time per Reel.
   - Completion rate by creator / audio / category.
   - Session length and Reels-per-session.
   - Skip rate vs loop rate.
2. Identify the grains - one row = one:
   - Reel view (a specific Reel played by a specific viewer).
   - Session (a continuous watch period ending when the user exits).
3. Pick fact-table types:
   - `fact_reel_view` -> transactional snapshot.
   - `dim_session` -> accumulating snapshot (start/end dates tracked
     across the session lifecycle).
4. Design dimensions and SCD choices:
   - `dim_reel` SCD2 because Reels are edited, re-audited, or
     removed and historical attributes matter for trend analysis.
   - `dim_sound` SCD1 (audio metadata corrections).
   - `dim_user` SCD2 (shared conformed user dim).

## How to Remember
- **Pattern**: "Fine-grained event fact + session accumulating snapshot."
- **Grain mnemonic**: "One row = one Reel play, one row = one session."
- A loop counts as multiple `reel_view` rows - never pre-aggregate.

## Schema (DDL)
```sql
CREATE TABLE fact_reel_view (
  reel_view_key   BIGINT PRIMARY KEY,
  session_key     BIGINT, viewer_key      BIGINT,
  reel_key        BIGINT, creator_key     BIGINT,
  date_key        INT,    time_key        INT,
  view_position   INT, watch_time_ms      INT,
  reel_duration_ms INT, completion_rate   DECIMAL(5,4),
  is_loop BOOLEAN, is_skipped BOOLEAN,
  is_liked BOOLEAN, is_shared BOOLEAN,
  sound_key BIGINT
);

CREATE TABLE dim_session (
  session_key       BIGINT PRIMARY KEY,
  session_id        VARCHAR(64), viewer_key BIGINT,
  session_start_key INT, session_end_key INT,
  start_timestamp   TIMESTAMP, end_timestamp TIMESTAMP,
  session_duration_s INT, reel_count INT,
  exit_reason       VARCHAR(30)
);
-- dim_reel (SCD2), dim_sound (SCD1), dim_user (SCD2),
-- dim_date, dim_time.
```

## Common Mistakes
- Pre-aggregating watch time on `dim_reel` and losing granularity.
- Treating a session as a single fact row and losing per-Reel details.
- Ignoring loops and skipping - both are critical ranking signals.

## AI Use Cases
- Reels ranking model trained on `watch_time_ms / completion_rate`.
- Detect addictive loops (high `is_loop` ratio + high session count).
- Sound recommendation: trending sounds correlated with long sessions.
