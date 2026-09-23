"""
Problem 03: Reels Watch-Session Model
Meta product: "Instagram/Facebook Reels"

How to Think:
- A "watch session" is one user opening Reels and scrolling through N short videos.
- Metrics: session duration, videos watched, completion rate, like/save/share per session.
- Grain: one row per watch session (not per video).
- A separate video-level fact captures per-video metrics (impressions, likes).
- Conformed dims: dim_user, dim_video (reel), dim_date, dim_sound.

How to Remember:
- "Session = one continuous viewing episode." Multiple videos per session.
- Use an accumulating snapshot when session has lifecycle stages
  (open -> first_video -> nth_video -> exit). Otherwise transactional.

AI Use Cases:
- Predict session length from first-3-video engagement features.
- Cluster sessions to find "binge" vs "bounce" patterns.
- Recommend next reel based on session context.
"""

DDL = """
-- Grain: one row per Reels watch session (user open -> exit).
CREATE TABLE fact_reels_session (
  session_key        BIGINT,
  user_key           BIGINT,
  session_date_key   INT,
  device_key         INT,
  entry_source_key   INT,           -- profile / explore / notification / share
  videos_watched     INT,
  total_duration_ms  BIGINT,
  likes_in_session   INT,
  shares_in_session  INT,
  saves_in_session   INT,
  is_loop_heavy      BOOLEAN,
  exit_reason        VARCHAR(20)    -- user_exit / app_killed / error / timeout
);

-- Grain: one row per (user, reel) viewed in a session (video-level event).
CREATE TABLE fact_reel_view (
  view_key           BIGINT,
  session_key        BIGINT,
  user_key           BIGINT,
  reel_key           BIGINT,
  author_key         BIGINT,
  position_in_session INT,
  view_date_key      INT,
  watch_duration_ms     INT,
  video_duration_ms     INT,
  completion_pct     DECIMAL(5,2),
  liked              BOOLEAN,
  shared             BOOLEAN,
  saved              BOOLEAN
);

-- Conformed dims
CREATE TABLE dim_reel (
  reel_key           BIGINT,
  reel_id            VARCHAR(40),
  author_user_key    BIGINT,
  sound_key          BIGINT,
  duration_ms        INT,
  hashtags           VARCHAR(20),
  effective_from     DATE,
  effective_to       DATE,
  is_current         BOOLEAN
);

CREATE TABLE dim_user (
  user_key           BIGINT, user_id VARCHAR(40), age_bucket VARCHAR(10),
  country VARCHAR(60), locale VARCHAR(20), tenure_days INT,
  effective_from DATE, effective_to DATE, is_current BOOLEAN
);

CREATE TABLE dim_sound ( sound_key BIGINT, sound_id VARCHAR(40), sound_name VARCHAR(120), artist VARCHAR(120), is_original BOOLEAN );
CREATE TABLE dim_device ( device_key INT, device_type VARCHAR(20), os VARCHAR(20), browser VARCHAR(20) );
CREATE TABLE dim_entry_source ( source_key INT, source_name VARCHAR(40) );
CREATE TABLE dim_date ( date_key INT PRIMARY KEY, full_date DATE, day_of_week VARCHAR(10), month INT, quarter INT, year INT );
"""