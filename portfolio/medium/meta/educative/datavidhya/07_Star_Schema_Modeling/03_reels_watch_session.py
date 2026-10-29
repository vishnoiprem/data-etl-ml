"""
Problem 03: Reels Watch-Session Model
Meta product: "Instagram Reels / Facebook Reels - Watch Analytics"

How to Think:
- One session = one continuous watch where the viewer did not leave
  the Reels surface for more than N seconds. Inside a session we
  watch many Reels (each Reel play is a row).
- Two grains: (1) reel_view (one row per Reel played in a session)
  and (2) session_summary (one row per session for funnel metrics).
- Use accumulating snapshot for sessions if we track start/end and
  exit reason. For reel_view itself, transactional snapshot.

How to Remember:
- "One row = one reel_view" is the fine-grained engagement fact.
- Sessions are modeled as accumulating snapshots with start/end keys
  for funnel analytics.
- Loop detection: a Reel looped N times is N rows in reel_view.

AI Use Cases
- Train Reels ranking model (watch time, completion rate features).
- Detect addictive content patterns via session length distribution.
- Recommend next reel via collaborative filtering on watch sequences.
"""

DDL = """
-- fact_reel_view: one row per Reel play within a session
CREATE TABLE fact_reel_view (
  reel_view_key      BIGINT PRIMARY KEY,
  session_key        BIGINT NOT NULL,
  viewer_key         BIGINT NOT NULL,
  reel_key           BIGINT NOT NULL,
  creator_key        BIGINT NOT NULL,
  date_key           INT    NOT NULL,
  time_key           INT,
  view_position      INT,                   -- nth Reel in the session
  watch_time_ms      INT,                   -- actual playback time
  reel_duration_ms   INT,                   -- for completion_rate
  completion_rate    DECIMAL(5,4),
  is_loop            BOOLEAN,
  is_skipped         BOOLEAN,               -- watched < 1s
  is_liked           BOOLEAN,
  is_shared          BOOLEAN,
  sound_key          BIGINT,
  FOREIGN KEY (session_key) REFERENCES dim_session(session_key),
  FOREIGN KEY (viewer_key)  REFERENCES dim_user(user_key),
  FOREIGN KEY (reel_key)    REFERENCES dim_reel(reel_key),
  FOREIGN KEY (creator_key) REFERENCES dim_user(user_key)
);

-- dim_session (accumulating snapshot - one row per session)
CREATE TABLE dim_session (
  session_key        BIGINT PRIMARY KEY,
  session_id         VARCHAR(64),
  viewer_key         BIGINT,
  session_start_key  INT,                   -- date_key
  session_end_key    INT,                   -- date_key when closed
  start_timestamp    TIMESTAMP,
  end_timestamp      TIMESTAMP,
  session_duration_s INT,
  reel_count         INT,
  exit_reason        VARCHAR(30)            -- 'app_exit','switch_surface','timeout'
);

-- dim_reel (SCD2 - Reel metadata changes: title, audio, visibility)
CREATE TABLE dim_reel (
  reel_key           BIGINT PRIMARY KEY,
  reel_id            VARCHAR(64),
  creator_key        BIGINT,
  reel_type          VARCHAR(20),           -- short / long / ad
  audio_name         VARCHAR(200),
  created_at         TIMESTAMP,
  effective_from     DATE,
  effective_to       DATE,
  is_current         BOOLEAN
);

-- dim_sound (SCD1 - audio tracks)
CREATE TABLE dim_sound (
  sound_key          BIGINT PRIMARY KEY,
  sound_id           VARCHAR(64),
  sound_name         VARCHAR(200),
  artist             VARCHAR(200)
);

-- dim_user (SCD2) reused across Meta products (conformed).
"""