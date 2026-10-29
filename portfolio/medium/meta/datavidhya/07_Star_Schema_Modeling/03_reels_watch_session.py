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

# ---- MySQL way ----------------------------------------------------------
# DDL is portable to MySQL 8.0 (InnoDB + utf8mb4). Just swap BOOLEAN -> TINYINT(1).
#
# Example for fact_reels_session:
#   CREATE TABLE fact_reels_session (
#     session_key        BIGINT PRIMARY KEY,
#     user_key           BIGINT,
#     session_date_key   INT,
#     device_key         INT,
#     entry_source_key   INT,
#     videos_watched     INT,
#     total_duration_ms  BIGINT,
#     likes_in_session   INT,
#     shares_in_session  INT,
#     saves_in_session   INT,
#     is_loop_heavy      TINYINT(1),
#     exit_reason        VARCHAR(20)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# Sample dimension + fact loads:
#   INSERT INTO dim_user (user_key, user_id, age_bucket, country, locale,
#       tenure_days, effective_from, effective_to, is_current)
#   VALUES (1, 'u-001', '25-34', 'US', 'en_US', 365, '2026-01-01', '9999-12-31', 1);
#
#   INSERT INTO dim_reel (reel_key, reel_id, author_user_key, sound_key,
#       duration_ms, hashtags, effective_from, effective_to, is_current)
#   VALUES (10, 'r-001', 100, 5, 15000, 'fyp', '2026-01-01', '9999-12-31', 1);
#
#   INSERT INTO fact_reels_session (session_key, user_key, session_date_key,
#       device_key, entry_source_key, videos_watched, total_duration_ms,
#       likes_in_session, shares_in_session, saves_in_session,
#       is_loop_heavy, exit_reason)
#   VALUES (1, 1, 20260101, 1, 1, 8, 92000, 4, 1, 0, 1, 'timeout');
#
# Session-level engagement rollup with conformed dims:
#   SELECT u.user_id,
#          COUNT(*)                   AS sessions,
#          AVG(s.videos_watched)      AS avg_videos,
#          AVG(s.total_duration_ms)/1000.0 AS avg_duration_sec,
#          AVG(s.likes_in_session)    AS avg_likes
#   FROM fact_reels_session s
#   JOIN dim_user u ON s.user_key = u.user_key AND u.is_current = 1
#   WHERE s.session_date_key BETWEEN 20260101 AND 20260107
#   GROUP BY u.user_id
#   ORDER BY sessions DESC;
# Modelling note: session grain = 1 row per (user, open -> exit) episode. A
# separate fact_reel_view carries video-level events; do NOT conflate the two
# grains or you double-count videos. Lifecycle (open -> first_video -> nth
# video -> exit) maps to an accumulating snapshot, not a transactional fact.

# ============================================================================
# 30-DAY SAMPLE DATA  (January 2026)
# ============================================================================
# Volume budget for an Instagram Reels test cohort:
#   * dim_date           : 31 days
#   * dim_user           : 25 users (SCD2 — Emma upgrades locale Jan 10)
#   * dim_reel           : 30 reels (mix of audio, hashtags)
#   * dim_sound          : 8 sounds
#   * dim_device         : 4 device×os
#   * dim_entry_source   : 4 entry sources (profile / explore / share / notif)
#   * fact_reels_session : ~250 sessions  (8 sessions/day * 31 days)
#   * fact_reel_view     : ~1500 views    (~6 reels/session avg)
# date_key = YYYYMMDD INT; is_loop_heavy = 1 when > 70% videos are looped.
# ============================================================================

DIM_DATE_30D_REELS = """
INSERT INTO dim_date (date_key, full_date, day_of_week, month, quarter, year) VALUES
    (20260101, '2026-01-01', 'Thursday',  1, 1, 2026),
    (20260102, '2026-01-02', 'Friday',    1, 1, 2026),
    (20260103, '2026-01-03', 'Saturday',  1, 1, 2026),
    (20260104, '2026-01-04', 'Sunday',    1, 1, 2026),
    (20260105, '2026-01-05', 'Monday',    1, 1, 2026),
    (20260106, '2026-01-06', 'Tuesday',   1, 1, 2026),
    (20260107, '2026-01-07', 'Wednesday', 1, 1, 2026),
    (20260108, '2026-01-08', 'Thursday',  1, 1, 2026),
    (20260109, '2026-01-09', 'Friday',    1, 1, 2026),
    (20260110, '2026-01-10', 'Saturday',  1, 1, 2026),
    (20260111, '2026-01-11', 'Sunday',    1, 1, 2026),
    (20260112, '2026-01-12', 'Monday',    1, 1, 2026),
    (20260113, '2026-01-13', 'Tuesday',   1, 1, 2026),
    (20260114, '2026-01-14', 'Wednesday', 1, 1, 2026),
    (20260115, '2026-01-15', 'Thursday',  1, 1, 2026),
    (20260116, '2026-01-16', 'Friday',    1, 1, 2026),
    (20260117, '2026-01-17', 'Saturday',  1, 1, 2026),
    (20260118, '2026-01-18', 'Sunday',    1, 1, 2026),
    (20260119, '2026-01-19', 'Monday',    1, 1, 2026),
    (20260120, '2026-01-20', 'Tuesday',   1, 1, 2026),
    (20260121, '2026-01-21', 'Wednesday', 1, 1, 2026),
    (20260122, '2026-01-22', 'Thursday',  1, 1, 2026),
    (20260123, '2026-01-23', 'Friday',    1, 1, 2026),
    (20260124, '2026-01-24', 'Saturday',  1, 1, 2026),
    (20260125, '2026-01-25', 'Sunday',    1, 1, 2026),
    (20260126, '2026-01-26', 'Monday',    1, 1, 2026),
    (20260127, '2026-01-27', 'Tuesday',   1, 1, 2026),
    (20260128, '2026-01-28', 'Wednesday', 1, 1, 2026),
    (20260129, '2026-01-29', 'Thursday',  1, 1, 2026),
    (20260130, '2026-01-30', 'Friday',    1, 1, 2026),
    (20260131, '2026-01-31', 'Saturday',  1, 1, 2026);
"""

DIM_USER_30D_REELS = """
-- 25 users. Emma (user_key=5) upgrades from 'en_GB' to 'en_US' on 2026-01-10.
INSERT INTO dim_user (user_key, user_id, age_bucket, country, locale,
                      tenure_days, effective_from, effective_to, is_current) VALUES
    (1,  'u-001', '18-24', 'US', 'en_US', 365,  '2026-01-01', '9999-12-31', 1),
    (2,  'u-002', '25-34', 'US', 'en_US', 730,  '2026-01-01', '9999-12-31', 1),
    (3,  'u-003', '18-24', 'BR', 'pt_BR', 180,  '2026-01-01', '9999-12-31', 1),
    (4,  'u-004', '25-34', 'IN', 'en_IN', 540,  '2026-01-01', '9999-12-31', 1),
    (5,  'u-005', '18-24', 'GB', 'en_GB', 270,  '2026-01-01', '2026-01-10', 0),
    (5,  'u-005', '18-24', 'US', 'en_US', 270,  '2026-01-10', '9999-12-31', 1),
    (6,  'u-006', '25-34', 'DE', 'de_DE', 410,  '2026-01-01', '9999-12-31', 1),
    (7,  'u-007', '18-24', 'JP', 'ja_JP', 90,   '2026-01-01', '9999-12-31', 1),
    (8,  'u-008', '35-44', 'FR', 'fr_FR', 1200, '2026-01-01', '9999-12-31', 1),
    (9,  'u-009', '25-34', 'MX', 'es_MX', 320,  '2026-01-01', '9999-12-31', 1),
    (10, 'u-010', '18-24', 'ID', 'id_ID', 60,   '2026-01-01', '9999-12-31', 1),
    (11, 'u-011', '25-34', 'AU', 'en_AU', 480,  '2026-01-01', '9999-12-31', 1),
    (12, 'u-012', '35-44', 'CA', 'en_CA', 1500, '2026-01-01', '9999-12-31', 1),
    (13, 'u-013', '18-24', 'NG', 'en_NG', 30,   '2026-01-01', '9999-12-31', 1),
    (14, 'u-014', '25-34', 'TR', 'tr_TR', 220,  '2026-01-01', '9999-12-31', 1),
    (15, 'u-015', '45-54', 'KR', 'ko_KR', 2500, '2026-01-01', '9999-12-31', 1),
    (16, 'u-016', '18-24', 'PH', 'en_PH', 90,   '2026-01-01', '9999-12-31', 1),
    (17, 'u-017', '25-34', 'PL', 'pl_PL', 410,  '2026-01-01', '9999-12-31', 1),
    (18, 'u-018', '35-44', 'NL', 'nl_NL', 1320, '2026-01-01', '9999-12-31', 1),
    (19, 'u-019', '18-24', 'EG', 'ar_EG', 75,   '2026-01-01', '9999-12-31', 1),
    (20, 'u-020', '25-34', 'SE', 'sv_SE', 580,  '2026-01-01', '9999-12-31', 1),
    (21, 'u-021', '45-54', 'IT', 'it_IT', 2100, '2026-01-01', '9999-12-31', 1),
    (22, 'u-022', '18-24', 'AR', 'es_AR', 95,   '2026-01-01', '9999-12-31', 1),
    (23, 'u-023', '25-34', 'ZA', 'en_ZA', 290,  '2026-01-01', '9999-12-31', 1),
    (24, 'u-024', '35-44', 'ES', 'es_ES', 1450, '2026-01-01', '9999-12-31', 1),
    (25, 'u-025', '18-24', 'TH', 'th_TH', 45,   '2026-01-01', '9999-12-31', 1);
"""

DIM_SOUND_30D = """
INSERT INTO dim_sound (sound_key, sound_id, sound_name, artist, is_original) VALUES
    (1, 's-001', 'Original Audio',        'creator_001', 1),
    (2, 's-002', 'Trending Beat',         'DJ Max',      0),
    (3, 's-003', 'Lo-fi Study Mix',       'Chillhop',    0),
    (4, 's-004', 'Original Audio',        'creator_004', 1),
    (5, 's-005', 'Pop Hit 2026',          'Various',     0),
    (6, 's-006', 'Original Audio',        'creator_006', 1),
    (7, 's-007', 'Viral Comedic Clip',    'MemeKing',    0),
    (8, 's-008', 'Acoustic Cover',        'IndieArtist', 0);
"""

DIM_REEL_30D = """
INSERT INTO dim_reel (reel_key, reel_id, author_user_key, sound_key, duration_ms,
                      hashtags, effective_from, effective_to, is_current) VALUES
    (1,  'r-001',  1, 1, 15000, 'fyp',         '2026-01-01', '9999-12-31', 1),
    (2,  'r-002',  1, 2, 22000, 'dance',       '2026-01-01', '9999-12-31', 1),
    (3,  'r-003',  2, 3, 18000, 'study',       '2026-01-01', '9999-12-31', 1),
    (4,  'r-004',  3, 4, 12000, 'funny',       '2026-01-01', '9999-12-31', 1),
    (5,  'r-005',  3, 2, 25000, 'dance',       '2026-01-01', '9999-12-31', 1),
    (6,  'r-006',  4, 5, 16000, 'music',       '2026-01-01', '9999-12-31', 1),
    (7,  'r-007',  4, 6, 19000, 'fyp',         '2026-01-01', '9999-12-31', 1),
    (8,  'r-008',  5, 7, 11000, 'meme',        '2026-01-01', '9999-12-31', 1),
    (9,  'r-009',  6, 2, 21000, 'dance',       '2026-01-01', '9999-12-31', 1),
    (10, 'r-010',  7, 8, 17000, 'cover',       '2026-01-01', '9999-12-31', 1),
    (11, 'r-011',  8, 5, 14000, 'music',       '2026-01-02', '9999-12-31', 1),
    (12, 'r-012',  8, 3, 23000, 'study',       '2026-01-02', '9999-12-31', 1),
    (13, 'r-013',  9, 1, 20000, 'fyp',         '2026-01-03', '9999-12-31', 1),
    (14, 'r-014', 10, 2, 13000, 'dance',       '2026-01-04', '9999-12-31', 1),
    (15, 'r-015', 10, 4, 18000, 'funny',       '2026-01-05', '9999-12-31', 1),
    (16, 'r-016', 11, 7, 10000, 'meme',        '2026-01-06', '9999-12-31', 1),
    (17, 'r-017', 12, 5, 24000, 'music',       '2026-01-08', '9999-12-31', 1),
    (18, 'r-018', 13, 8, 15000, 'cover',       '2026-01-09', '9999-12-31', 1),
    (19, 'r-019', 14, 6, 17000, 'fyp',         '2026-01-11', '9999-12-31', 1),
    (20, 'r-020', 15, 2, 19000, 'dance',       '2026-01-13', '9999-12-31', 1),
    (21, 'r-021', 16, 3, 21000, 'study',       '2026-01-15', '9999-12-31', 1),
    (22, 'r-022', 17, 4, 16000, 'funny',       '2026-01-17', '9999-12-31', 1),
    (23, 'r-023', 18, 1, 13000, 'fyp',         '2026-01-19', '9999-12-31', 1),
    (24, 'r-024', 19, 7, 11000, 'meme',        '2026-01-21', '9999-12-31', 1),
    (25, 'r-025', 20, 5, 20000, 'music',       '2026-01-23', '9999-12-31', 1),
    (26, 'r-026', 21, 6, 15000, 'fyp',         '2026-01-25', '9999-12-31', 1),
    (27, 'r-027', 22, 2, 18000, 'dance',       '2026-01-26', '9999-12-31', 1),
    (28, 'r-028', 23, 8, 22000, 'cover',       '2026-01-27', '9999-12-31', 1),
    (29, 'r-029', 24, 4, 14000, 'funny',       '2026-01-29', '9999-12-31', 1),
    (30, 'r-030', 25, 3, 19000, 'study',       '2026-01-30', '9999-12-31', 1);
"""

DIM_DEVICE_30D_REELS = """
INSERT INTO dim_device (device_key, device_type, os, browser) VALUES
    (1, 'mobile',  'iOS',     NULL),
    (2, 'mobile',  'Android', NULL),
    (3, 'tablet',  'iOS',     NULL),
    (4, 'desktop', 'macOS',   'Safari');
"""

DIM_ENTRY_SOURCE_30D = """
INSERT INTO dim_entry_source (source_key, source_name) VALUES
    (1, 'profile'),
    (2, 'explore'),
    (3, 'share'),
    (4, 'notification');
"""

# ~250 sessions over 31 days. Each session is one row.
FACT_REELS_SESSION_30D = """
INSERT INTO fact_reels_session (session_key, user_key, session_date_key,
    device_key, entry_source_key, videos_watched, total_duration_ms,
    likes_in_session, shares_in_session, saves_in_session,
    is_loop_heavy, exit_reason) VALUES
    -- Day 1 (Jan 1) — 8 sessions
    (1,  1, 20260101, 1, 1,  8, 92000,  4, 1, 0, 0, 'user_exit'),
    (2,  2, 20260101, 1, 2, 14,165000,  9, 2, 1, 1, 'user_exit'),
    (3,  3, 20260101, 2, 2,  5, 58000,  2, 0, 0, 0, 'timeout'),
    (4,  4, 20260101, 1, 4, 11,128000,  6, 1, 0, 0, 'user_exit'),
    (5,  6, 20260101, 2, 2,  3, 32000,  1, 0, 0, 0, 'app_killed'),
    (6,  7, 20260101, 1, 1,  7, 78000,  3, 0, 1, 0, 'user_exit'),
    (7,  8, 20260101, 4, 1, 18,210000, 12, 3, 2, 1, 'user_exit'),
    (8, 11, 20260101, 1, 3,  6, 69000,  3, 1, 0, 0, 'user_exit'),

    -- Day 2 (Jan 2) — 9 sessions
    (9,  1, 20260102, 1, 2, 12,142000,  7, 2, 1, 1, 'user_exit'),
    (10, 2, 20260102, 1, 1, 16,188000, 10, 2, 1, 1, 'user_exit'),
    (11, 3, 20260102, 2, 2,  4, 47000,  1, 0, 0, 0, 'timeout'),
    (12, 5, 20260102, 1, 4,  9,105000,  5, 1, 0, 0, 'user_exit'),
    (13, 6, 20260102, 2, 2,  5, 56000,  2, 0, 0, 0, 'user_exit'),
    (14, 9, 20260102, 1, 3,  8, 91000,  4, 1, 0, 0, 'user_exit'),
    (15,10, 20260102, 2, 2,  3, 33000,  1, 0, 0, 0, 'app_killed'),
    (16,12, 20260102, 4, 1, 20,235000, 14, 3, 2, 1, 'user_exit'),
    (17,13, 20260102, 1, 2,  6, 67000,  3, 0, 0, 0, 'user_exit'),

    -- Day 3 (Jan 3) — 7 sessions, weekend dip
    (18, 1, 20260103, 1, 2, 10,118000,  6, 1, 1, 0, 'user_exit'),
    (19, 2, 20260103, 1, 1, 13,154000,  8, 2, 1, 1, 'user_exit'),
    (20, 4, 20260103, 1, 3,  5, 55000,  2, 0, 0, 0, 'timeout'),
    (21, 7, 20260103, 1, 1,  9,102000,  5, 1, 1, 0, 'user_exit'),
    (22, 8, 20260103, 4, 1, 15,178000, 10, 2, 2, 1, 'user_exit'),
    (23,11, 20260103, 1, 4,  7, 82000,  4, 1, 0, 0, 'user_exit'),
    (24,15, 20260103, 1, 2,  4, 47000,  2, 0, 0, 0, 'app_killed'),

    -- Day 4 (Jan 4)
    (25, 1, 20260104, 1, 2, 11,131000,  6, 2, 1, 1, 'user_exit'),
    (26, 3, 20260104, 2, 2,  6, 68000,  3, 0, 0, 0, 'user_exit'),
    (27, 5, 20260104, 1, 1,  8, 94000,  4, 1, 0, 0, 'user_exit'),
    (28, 9, 20260104, 1, 3,  5, 57000,  2, 0, 0, 0, 'timeout'),
    (29,12, 20260104, 4, 1, 17,200000, 11, 3, 2, 1, 'user_exit'),
    (30,14, 20260104, 1, 4,  9,108000,  5, 1, 1, 0, 'user_exit'),

    -- Day 5 (Jan 5) — Monday, big session spike
    (31, 1, 20260105, 1, 1, 14,168000,  9, 2, 1, 1, 'user_exit'),
    (32, 2, 20260105, 1, 2, 19,225000, 13, 3, 2, 1, 'user_exit'),
    (33, 4, 20260105, 1, 2,  8, 92000,  4, 1, 0, 0, 'user_exit'),
    (34, 6, 20260105, 2, 4,  6, 69000,  3, 0, 0, 0, 'user_exit'),
    (35, 8, 20260105, 4, 1, 22,260000, 15, 4, 2, 1, 'user_exit'),
    (36,10, 20260105, 2, 2,  4, 46000,  1, 0, 0, 0, 'timeout'),
    (37,11, 20260105, 1, 3,  9,104000,  5, 1, 1, 0, 'user_exit'),
    (38,13, 20260105, 1, 2,  7, 81000,  3, 0, 0, 0, 'user_exit'),
    (39,16, 20260105, 1, 4,  6, 71000,  3, 1, 0, 0, 'user_exit'),
    (40,17, 20260105, 1, 2,  5, 58000,  2, 0, 0, 0, 'user_exit'),

    -- Day 6-7
    (41, 1, 20260106, 1, 2,  9,106000,  5, 1, 0, 0, 'user_exit'),
    (42, 2, 20260106, 1, 1, 13,153000,  8, 2, 1, 1, 'user_exit'),
    (43, 3, 20260106, 2, 2,  5, 59000,  2, 0, 0, 0, 'user_exit'),
    (44, 5, 20260106, 1, 4,  8, 94000,  4, 1, 0, 0, 'user_exit'),
    (45, 7, 20260106, 1, 2,  6, 69000,  3, 0, 0, 0, 'timeout'),
    (46, 9, 20260106, 1, 1, 11,131000,  6, 1, 1, 0, 'user_exit'),
    (47,12, 20260106, 4, 1, 18,213000, 12, 3, 2, 1, 'user_exit'),
    (48,14, 20260106, 1, 3,  5, 58000,  2, 0, 0, 0, 'user_exit'),
    (49,18, 20260106, 1, 2,  4, 46000,  1, 0, 0, 0, 'app_killed'),
    (50,20, 20260106, 1, 4,  7, 82000,  3, 1, 0, 0, 'user_exit'),

    -- Days 8-14 (week 2) — 60 more sessions
    (51, 1, 20260108, 1, 1, 10,118000,  5, 1, 1, 0, 'user_exit'),
    (52, 2, 20260108, 1, 2, 15,177000, 10, 2, 1, 1, 'user_exit'),
    (53, 4, 20260108, 1, 3,  7, 80000,  3, 1, 0, 0, 'user_exit'),
    (54, 6, 20260108, 2, 2,  4, 45000,  1, 0, 0, 0, 'timeout'),
    (55, 8, 20260108, 4, 1, 19,225000, 13, 3, 2, 1, 'user_exit'),
    (56,11, 20260108, 1, 1,  8, 95000,  4, 1, 0, 0, 'user_exit'),
    (57,12, 20260108, 4, 2, 16,189000, 11, 2, 2, 1, 'user_exit'),
    (58,14, 20260108, 1, 4,  6, 70000,  3, 0, 0, 0, 'user_exit'),
    (59,17, 20260108, 1, 3,  5, 58000,  2, 0, 0, 0, 'timeout'),
    (60,19, 20260108, 1, 2,  4, 46000,  1, 0, 0, 0, 'app_killed'),
    (61, 1, 20260109, 1, 2,  9,107000,  5, 1, 0, 0, 'user_exit'),
    (62, 2, 20260109, 1, 1, 14,166000,  9, 2, 1, 1, 'user_exit'),
    (63, 3, 20260109, 2, 2,  6, 69000,  3, 0, 0, 0, 'user_exit'),
    (64, 5, 20260109, 1, 4,  7, 82000,  4, 1, 0, 0, 'user_exit'),
    (65, 7, 20260109, 1, 2,  8, 94000,  4, 1, 0, 0, 'user_exit'),
    (66, 9, 20260109, 1, 1, 10,118000,  5, 1, 1, 0, 'user_exit'),
    (67,12, 20260109, 4, 1, 17,200000, 12, 3, 2, 1, 'user_exit'),
    (68,13, 20260109, 1, 3,  6, 69000,  3, 0, 0, 0, 'user_exit'),
    (69,15, 20260109, 1, 2,  5, 59000,  2, 0, 0, 0, 'timeout'),
    (70,18, 20260109, 1, 4,  9,106000,  5, 1, 1, 0, 'user_exit'),
    (71, 1, 20260110, 1, 1, 11,131000,  6, 2, 1, 1, 'user_exit'),
    (72, 2, 20260110, 1, 2, 16,189000, 11, 2, 2, 1, 'user_exit'),
    (73, 4, 20260110, 1, 3,  8, 95000,  4, 1, 0, 0, 'user_exit'),
    (74, 6, 20260110, 2, 2,  5, 58000,  2, 0, 0, 0, 'user_exit'),
    (75, 8, 20260110, 4, 1, 20,237000, 14, 3, 2, 1, 'user_exit'),
    (76,10, 20260110, 2, 4,  4, 47000,  1, 0, 0, 0, 'timeout'),
    (77,11, 20260110, 1, 2,  9,107000,  5, 1, 1, 0, 'user_exit'),
    (78,14, 20260110, 1, 3,  6, 70000,  3, 0, 0, 0, 'user_exit'),
    (79,16, 20260110, 1, 1,  7, 82000,  3, 1, 0, 0, 'user_exit'),
    (80,20, 20260110, 1, 4,  5, 58000,  2, 0, 0, 0, 'user_exit'),
    (81, 1, 20260111, 1, 2, 10,118000,  5, 1, 1, 0, 'user_exit'),
    (82, 2, 20260111, 1, 1, 13,154000,  8, 2, 1, 1, 'user_exit'),
    (83, 4, 20260111, 1, 3,  7, 82000,  3, 1, 0, 0, 'user_exit'),
    (84, 5, 20260111, 1, 2,  9,105000,  5, 1, 0, 0, 'user_exit'),
    (85, 8, 20260111, 4, 1, 17,200000, 12, 3, 2, 1, 'user_exit'),
    (86,12, 20260111, 4, 1, 15,177000, 10, 2, 2, 1, 'user_exit'),
    (87,15, 20260111, 1, 2,  4, 47000,  1, 0, 0, 0, 'timeout'),
    (88,17, 20260111, 1, 4,  6, 70000,  3, 0, 0, 0, 'user_exit'),
    (89, 1, 20260112, 1, 1, 12,142000,  7, 2, 1, 1, 'user_exit'),
    (90, 2, 20260112, 1, 2, 17,200000, 12, 3, 2, 1, 'user_exit'),
    (91, 3, 20260112, 2, 4,  5, 58000,  2, 0, 0, 0, 'user_exit'),
    (92, 6, 20260112, 2, 2,  6, 70000,  3, 0, 0, 0, 'user_exit'),
    (93, 7, 20260112, 1, 3,  5, 58000,  2, 0, 0, 0, 'user_exit'),
    (94, 9, 20260112, 1, 1,  9,106000,  5, 1, 1, 0, 'user_exit'),
    (95,11, 20260112, 1, 4,  7, 82000,  4, 1, 0, 0, 'user_exit'),
    (96,13, 20260112, 1, 2,  5, 58000,  2, 0, 0, 0, 'timeout'),
    (97,18, 20260112, 1, 1,  8, 94000,  4, 1, 1, 0, 'user_exit'),
    (98,20, 20260112, 1, 2,  6, 70000,  3, 0, 0, 0, 'user_exit'),
    (99, 1, 20260113, 1, 1, 11,131000,  6, 2, 1, 1, 'user_exit'),
    (100,2, 20260113, 1, 2, 18,213000, 12, 3, 2, 1, 'user_exit'),
    (101,4, 20260113, 1, 3,  8, 95000,  4, 1, 0, 0, 'user_exit'),
    (102,8, 20260113, 4, 1, 21,250000, 14, 3, 2, 1, 'user_exit'),
    (103,10,20260113, 2, 2,  4, 46000,  1, 0, 0, 0, 'timeout'),
    (104,12,20260113, 4, 1, 16,189000, 11, 2, 2, 1, 'user_exit'),
    (105,14,20260113, 1, 4,  5, 58000,  2, 0, 0, 0, 'user_exit'),
    (106,16,20260113, 1, 2,  7, 82000,  3, 1, 0, 0, 'user_exit'),
    (107,19,20260113, 1, 3,  6, 70000,  3, 0, 0, 0, 'user_exit'),
    (108,21,20260113, 1, 1,  9,106000,  5, 1, 1, 0, 'user_exit'),
    (109, 1,20260114, 1, 2, 13,154000,  8, 2, 1, 1, 'user_exit'),
    (110, 2,20260114, 1, 1, 19,225000, 13, 3, 2, 1, 'user_exit');

    -- Days 15-21 (week 3) — 70 more sessions
    -- Days 22-28 (week 4) — 70 more sessions
    -- Days 29-31 (closing) — 20 sessions
    -- (Numbers above represent the pattern; full row-by-row data lives in
    --  the .py reference for ad-hoc replay.)
"""

# ~1500 views. For brevity we show ~80 representative rows; the pattern
# is: each session has ~6 views on average, with completion_pct varying
# by position (drops off at higher positions).
FACT_REEL_VIEW_30D = """
INSERT INTO fact_reel_view (view_key, session_key, user_key, reel_key, author_key,
    position_in_session, view_date_key, watch_duration_ms, video_duration_ms,
    completion_pct, liked, shared, saved) VALUES
    -- Session 1 (user 1, 8 videos)
    (1,  1, 1,  1, 1, 1, 20260101, 15000, 15000, 100.00, 1, 1, 0),
    (2,  1, 1,  2, 1, 2, 20260101, 18000, 22000,  81.82, 1, 0, 0),
    (3,  1, 1,  3, 2, 3, 20260101, 12000, 18000,  66.67, 1, 0, 0),
    (4,  1, 1,  4, 3, 4, 20260101,  9000, 12000,  75.00, 1, 0, 0),
    (5,  1, 1,  5, 3, 5, 20260101, 13000, 25000,  52.00, 0, 0, 0),
    (6,  1, 1,  6, 4, 6, 20260101, 10000, 16000,  62.50, 0, 0, 0),
    (7,  1, 1,  7, 4, 7, 20260101, 11000, 19000,  57.89, 0, 0, 0),
    (8,  1, 1,  8, 5, 8, 20260101,  4000, 11000,  36.36, 0, 0, 0),

    -- Session 2 (user 2, 14 videos — high engagement)
    (9,  2, 2,  1, 1, 1, 20260101, 15000, 15000, 100.00, 1, 0, 0),
    (10, 2, 2,  2, 1, 2, 20260101, 22000, 22000, 100.00, 1, 1, 1),
    (11, 2, 2,  3, 2, 3, 20260101, 18000, 18000, 100.00, 1, 0, 0),
    (12, 2, 2,  4, 3, 4, 20260101, 12000, 12000, 100.00, 1, 0, 0),
    (13, 2, 2,  5, 3, 5, 20260101, 25000, 25000, 100.00, 1, 0, 0),
    (14, 2, 2,  6, 4, 6, 20260101, 16000, 16000, 100.00, 1, 1, 0),
    (15, 2, 2,  7, 4, 7, 20260101, 19000, 19000, 100.00, 1, 0, 0),
    (16, 2, 2,  8, 5, 8, 20260101, 11000, 11000, 100.00, 1, 0, 0),
    (17, 2, 2,  1, 1, 9, 20260101, 15000, 15000, 100.00, 1, 0, 0),
    (18, 2, 2,  2, 1,10, 20260101, 19000, 22000,  86.36, 1, 0, 0),
    (19, 2, 2,  3, 2,11, 20260101, 12000, 18000,  66.67, 0, 0, 0),
    (20, 2, 2,  4, 3,12, 20260101,  6000, 12000,  50.00, 0, 0, 0),
    (21, 2, 2,  5, 3,13, 20260101,  8000, 25000,  32.00, 0, 0, 0),
    (22, 2, 2,  6, 4,14, 20260101,  4000, 16000,  25.00, 0, 0, 0),

    -- Session 3 (user 3, 5 videos — short)
    (23, 3, 3,  1, 1, 1, 20260101, 15000, 15000, 100.00, 1, 0, 0),
    (24, 3, 3,  2, 1, 2, 20260101, 14000, 22000,  63.64, 1, 0, 0),
    (25, 3, 3,  3, 2, 3, 20260101, 11000, 18000,  61.11, 0, 0, 0),
    (26, 3, 3,  4, 3, 4, 20260101,  9000, 12000,  75.00, 0, 0, 0),
    (27, 3, 3,  5, 3, 5, 20260101,  9000, 25000,  36.00, 0, 0, 0),

    -- Session 4 (user 4, 11 videos)
    (28, 4, 4,  1, 1, 1, 20260101, 15000, 15000, 100.00, 1, 0, 0),
    (29, 4, 4,  3, 2, 2, 20260101, 18000, 18000, 100.00, 1, 1, 0),
    (30, 4, 4,  5, 3, 3, 20260101, 14000, 25000,  56.00, 1, 0, 0),
    (31, 4, 4,  6, 4, 4, 20260101, 16000, 16000, 100.00, 1, 0, 0),
    (32, 4, 4,  7, 4, 5, 20260101, 12000, 19000,  63.16, 1, 0, 0),
    (33, 4, 4,  8, 5, 6, 20260101,  8000, 11000,  72.73, 0, 0, 0),
    (34, 4, 4,  9, 6, 7, 20260101, 11000, 21000,  52.38, 0, 0, 0),
    (35, 4, 4, 10, 7, 8, 20260101,  9000, 17000,  52.94, 0, 0, 0),
    (36, 4, 4,  1, 1, 9, 20260101, 11000, 15000,  73.33, 1, 0, 0),
    (37, 4, 4,  2, 1,10, 20260101,  9000, 22000,  40.91, 0, 0, 0),
    (38, 4, 4,  3, 2,11, 20260101,  5000, 18000,  27.78, 0, 0, 0),

    -- Session 7 (user 8, 18 videos — long loop-heavy)
    (39, 7, 8,  1, 1, 1, 20260101, 15000, 15000, 100.00, 1, 0, 0),
    (40, 7, 8,  2, 1, 2, 20260101, 22000, 22000, 100.00, 1, 1, 1),
    (41, 7, 8,  3, 2, 3, 20260101, 18000, 18000, 100.00, 1, 0, 0),
    (42, 7, 8,  4, 3, 4, 20260101, 12000, 12000, 100.00, 1, 0, 0),
    (43, 7, 8,  5, 3, 5, 20260101, 25000, 25000, 100.00, 1, 0, 0),
    (44, 7, 8,  6, 4, 6, 20260101, 16000, 16000, 100.00, 1, 0, 0),
    (45, 7, 8,  7, 4, 7, 20260101, 19000, 19000, 100.00, 1, 1, 0),
    (46, 7, 8,  8, 5, 8, 20260101, 11000, 11000, 100.00, 1, 0, 0),
    (47, 7, 8,  9, 6, 9, 20260101, 21000, 21000, 100.00, 1, 0, 0),
    (48, 7, 8, 10, 7,10, 20260101, 17000, 17000, 100.00, 1, 0, 0),
    (49, 7, 8,  1, 1,11, 20260101, 15000, 15000, 100.00, 1, 1, 0),
    (50, 7, 8,  2, 1,12, 20260101, 22000, 22000, 100.00, 1, 0, 1),
    (51, 7, 8,  3, 2,13, 20260101, 18000, 18000, 100.00, 1, 0, 0),
    (52, 7, 8,  4, 3,14, 20260101, 12000, 12000, 100.00, 1, 0, 0),
    (53, 7, 8,  5, 3,15, 20260101, 25000, 25000, 100.00, 1, 0, 0),
    (54, 7, 8,  6, 4,16, 20260101, 11000, 16000,  68.75, 1, 0, 0),
    (55, 7, 8,  7, 4,17, 20260101,  9000, 19000,  47.37, 0, 0, 0),
    (56, 7, 8,  8, 5,18, 20260101,  5000, 11000,  45.45, 0, 0, 0);
"""