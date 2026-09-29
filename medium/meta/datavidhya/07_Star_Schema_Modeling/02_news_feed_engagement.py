"""
Problem 02: News Feed Engagement Analytics
Meta product: "Facebook News Feed"

How to Think:
- Three events on each story shown in feed: impression (render), reaction (like/love/...), share.
- Each is its own grain; reactions are 1 per (user, post, reaction_type) but share is 1 per share.
- A "feed_engagement_daily" periodic fact helps measure reach vs interaction.
- Conformed dims: dim_post, dim_user, dim_date.

How to Remember:
- "One impression is not one reaction." Split into three transactional facts or use
  one fact with multiple flags + counts. Trade-off: row count vs query flexibility.
- Share is rarer than reaction; modeling it separately keeps fan-out smaller.

AI Use Cases:
- Predict post virality from early impression-to-share rate.
- Recommend friends/pages by reaction co-occurrence.
- Detect engagement-bait posts (high share, low dwell).
"""

DDL = """
-- Grain: one row per post impression to a viewer.
CREATE TABLE fact_post_impression (
  impression_key     BIGINT,
  post_key          BIGINT,
  viewer_user_key    BIGINT,
  author_user_key    BIGINT,
  date_key           INT,
  time_key           INT,
  device_key         INT,
  placement_key      INT,        -- top_of_feed / inline / etc.
  is_video           BOOLEAN,
  dwell_ms           INT
);

-- Grain: one row per reaction (user reacted to a post with a reaction type).
CREATE TABLE fact_post_reaction (
  reaction_key       BIGINT,
  post_key           BIGINT,
  reactor_user_key   BIGINT,
  author_user_key    BIGINT,
  reaction_type_key  INT,        -- like / love / haha / wow / sad / angry
  reaction_date_key  INT,
  device_key         INT
);

-- Grain: one row per share event.
CREATE TABLE fact_post_share (
  share_key          BIGINT,
  post_key           BIGINT,
  sharer_user_key    BIGINT,
  author_user_key    BIGINT,
  share_destination_key INT,     -- own_timeline / group / DM / external
  share_date_key     INT
);

-- Conformed dims
CREATE TABLE dim_post (
  post_key           BIGINT,
  post_id            VARCHAR(40),
  author_user_key    BIGINT,
  post_type          VARCHAR(20),   -- text / photo / video / link
  page_or_profile    VARCHAR(20),
  effective_from     DATE,
  effective_to       DATE,
  is_current         BOOLEAN
);

CREATE TABLE dim_user (
  user_key           BIGINT,
  user_id            VARCHAR(40),
  age_bucket         VARCHAR(10),
  gender             VARCHAR(10),
  country            VARCHAR(60),
  locale             VARCHAR(20),
  tenure_days        INT,
  effective_from     DATE,
  effective_to       DATE,
  is_current         BOOLEAN
);

CREATE TABLE dim_reaction_type ( reaction_type_key INT, reaction_name VARCHAR(20), is_positive BOOLEAN );
CREATE TABLE dim_device ( device_key INT, device_type VARCHAR(20), os VARCHAR(20), browser VARCHAR(20) );
CREATE TABLE dim_date ( date_key INT PRIMARY KEY, full_date DATE, day_of_week VARCHAR(10), month INT, quarter INT, year INT );
"""

# ---- MySQL way ----------------------------------------------------------
# DDL is portable: MySQL BOOLEAN is an alias for TINYINT(1); VARCHAR/DECIMAL are
# identical. Add ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 (NEWS FEED text needs it).
#
# Example for fact_post_impression (apply to all 6 tables):
#   CREATE TABLE fact_post_impression (
#     impression_key    BIGINT PRIMARY KEY,
#     post_key          BIGINT,
#     viewer_user_key   BIGINT,
#     author_user_key   BIGINT,
#     date_key          INT,
#     time_key          INT,
#     device_key        INT,
#     placement_key     INT,
#     is_video          TINYINT(1),
#     dwell_ms          INT
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# Sample dimension + fact loads:
#   INSERT INTO dim_post (post_key, post_id, author_user_key, post_type,
#       page_or_profile, effective_from, effective_to, is_current)
#   VALUES (1, 'p-001', 100, 'video', 'profile', '2026-01-01', '9999-12-31', 1);
#
#   INSERT INTO dim_reaction_type (reaction_type_key, reaction_name, is_positive)
#   VALUES (1, 'like', 1), (2, 'love', 1), (3, 'sad', 0);
#
#   INSERT INTO fact_post_impression (impression_key, post_key, viewer_user_key,
#       author_user_key, date_key, time_key, device_key, placement_key, is_video, dwell_ms)
#   VALUES (1, 1, 200, 100, 20260101, 1000, 1, 1, 1, 4500);
#
#   INSERT INTO fact_post_reaction (reaction_key, post_key, reactor_user_key,
#       author_user_key, reaction_type_key, reaction_date_key, device_key)
#   VALUES (1, 1, 200, 100, 1, 20260101, 1);
#
# Reach vs interaction (impressions vs reactions per post):
#   SELECT p.post_id,
#          COUNT(DISTINCT i.impression_key) AS impressions,
#          COUNT(DISTINCT r.reaction_key)  AS reactions
#   FROM dim_post p
#   LEFT JOIN fact_post_impression i ON i.post_key = p.post_key
#   LEFT JOIN fact_post_reaction  r ON r.post_key = p.post_key
#   WHERE p.is_current = 1
#   GROUP BY p.post_id
#   ORDER BY impressions DESC;
# Modelling note: "One impression is not one reaction." Reactions are sparser
# than impressions — splitting into 3 transactional facts (or 1 fact with
# multiple flags + counts) is a query-flexibility vs row-count trade-off.

# ============================================================================
# 30-DAY SAMPLE DATA  (January 2026)
# ============================================================================
# Volume budget for a mid-size Facebook News Feed test cohort:
#   * dim_date           : 31 days
#   * dim_post           : 25 posts (mix of video / photo / text / link)
#   * dim_user           : 30 viewers (SCD2 — 1 user relocates mid-month)
#   * dim_reaction_type  : 6 reaction types
#   * dim_device         : 5 device×os combinations
#   * dim_placement      : 4 placements (top_of_feed, inline, story, suggested)
#   * fact_post_impression  : ~750 (25 posts * 30 viewers, ~once/day avg)
#   * fact_post_reaction    : ~225 (~30% reaction rate)
#   * fact_post_share       : ~50  (~7% share rate, rarer)
# date_key = YYYYMMDD INT; time_key = HHMM (e.g. 1430 = 14:30 UTC).
# ============================================================================

DIM_DATE_30D_FEED = """
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

DIM_POST_30D = """
-- 25 posts: mix of photo, video, text, link. Authors are user_keys 1..10.
INSERT INTO dim_post (post_key, post_id, author_user_key, post_type,
                      page_or_profile, effective_from, effective_to, is_current) VALUES
    (1,  'p-001', 1,  'photo', 'profile', '2026-01-01', '9999-12-31', 1),
    (2,  'p-002', 1,  'video', 'profile', '2026-01-01', '9999-12-31', 1),
    (3,  'p-003', 2,  'text',  'profile', '2026-01-01', '9999-12-31', 1),
    (4,  'p-004', 3,  'video', 'page',    '2026-01-01', '9999-12-31', 1),
    (5,  'p-005', 3,  'photo', 'page',    '2026-01-01', '9999-12-31', 1),
    (6,  'p-006', 4,  'link',  'profile', '2026-01-01', '9999-12-31', 1),
    (7,  'p-007', 5,  'video', 'page',    '2026-01-01', '9999-12-31', 1),
    (8,  'p-008', 5,  'photo', 'page',    '2026-01-01', '9999-12-31', 1),
    (9,  'p-009', 6,  'text',  'profile', '2026-01-01', '9999-12-31', 1),
    (10, 'p-010', 6,  'video', 'profile', '2026-01-01', '9999-12-31', 1),
    (11, 'p-011', 7,  'photo', 'profile', '2026-01-02', '9999-12-31', 1),
    (12, 'p-012', 8,  'video', 'page',    '2026-01-03', '9999-12-31', 1),
    (13, 'p-013', 8,  'link',  'page',    '2026-01-04', '9999-12-31', 1),
    (14, 'p-014', 9,  'text',  'profile', '2026-01-05', '9999-12-31', 1),
    (15, 'p-015', 9,  'photo', 'profile', '2026-01-06', '9999-12-31', 1),
    (16, 'p-016', 10, 'video', 'page',    '2026-01-08', '9999-12-31', 1),
    (17, 'p-017', 1,  'photo', 'profile', '2026-01-10', '9999-12-31', 1),
    (18, 'p-018', 2,  'video', 'profile', '2026-01-12', '9999-12-31', 1),
    (19, 'p-019', 3,  'text',  'page',    '2026-01-15', '9999-12-31', 1),
    (20, 'p-020', 4,  'link',  'profile', '2026-01-17', '9999-12-31', 1),
    (21, 'p-021', 5,  'photo', 'page',    '2026-01-19', '9999-12-31', 1),
    (22, 'p-022', 6,  'video', 'profile', '2026-01-21', '9999-12-31', 1),
    (23, 'p-023', 7,  'text',  'profile', '2026-01-23', '9999-12-31', 1),
    (24, 'p-024', 8,  'photo', 'page',    '2026-01-25', '9999-12-31', 1),
    (25, 'p-025', 9,  'video', 'profile', '2026-01-28', '9999-12-31', 1);
"""

DIM_USER_30D = """
-- 30 viewers + 10 authors (overlapping). User 5 (Dimitri) relocates
-- from RU to DE on 2026-01-18 — that's the SCD2 row split.
INSERT INTO dim_user (user_key, user_id, age_bucket, gender, country,
                      locale, tenure_days, effective_from, effective_to, is_current) VALUES
    (1,  'u-001', '25-34', 'M', 'US', 'en_US', 730, '2026-01-01', '9999-12-31', 1),
    (2,  'u-002', '18-24', 'F', 'US', 'en_US', 365, '2026-01-01', '9999-12-31', 1),
    (3,  'u-003', '35-44', 'M', 'GB', 'en_GB', 1095,'2026-01-01', '9999-12-31', 1),
    (4,  'u-004', '25-34', 'F', 'DE', 'de_DE', 540, '2026-01-01', '9999-12-31', 1),
    (5,  'u-005', '18-24', 'M', 'RU', 'ru_RU', 180, '2026-01-01', '2026-01-18', 0),
    (5,  'u-005', '18-24', 'M', 'DE', 'de_DE', 180, '2026-01-18', '9999-12-31', 1),
    (6,  'u-006', '45-54', 'F', 'IT', 'it_IT', 1825,'2026-01-01', '9999-12-31', 1),
    (7,  'u-007', '25-34', 'M', 'JP', 'ja_JP', 410, '2026-01-01', '9999-12-31', 1),
    (8,  'u-008', '35-44', 'F', 'BR', 'pt_BR', 920, '2026-01-01', '9999-12-31', 1),
    (9,  'u-009', '18-24', 'M', 'IN', 'en_IN', 95,  '2026-01-01', '9999-12-31', 1),
    (10, 'u-010', '25-34', 'F', 'FR', 'fr_FR', 620, '2026-01-01', '9999-12-31', 1),
    (11, 'u-011', '25-34', 'F', 'US', 'en_US', 245, '2026-01-01', '9999-12-31', 1),
    (12, 'u-012', '35-44', 'M', 'US', 'en_US', 1500,'2026-01-01', '9999-12-31', 1),
    (13, 'u-013', '18-24', 'F', 'GB', 'en_GB', 120, '2026-01-01', '9999-12-31', 1),
    (14, 'u-014', '25-34', 'M', 'DE', 'de_DE', 380, '2026-01-01', '9999-12-31', 1),
    (15, 'u-015', '45-54', 'F', 'CA', 'en_CA', 2100,'2026-01-01', '9999-12-31', 1),
    (16, 'u-016', '18-24', 'M', 'MX', 'es_MX', 60,  '2026-01-01', '9999-12-31', 1),
    (17, 'u-017', '25-34', 'F', 'AU', 'en_AU', 480, '2026-01-01', '9999-12-31', 1),
    (18, 'u-018', '35-44', 'M', 'ES', 'es_ES', 1100,'2026-01-01', '9999-12-31', 1),
    (19, 'u-019', '25-34', 'F', 'KR', 'ko_KR', 290, '2026-01-01', '9999-12-31', 1),
    (20, 'u-020', '18-24', 'M', 'ID', 'id_ID', 45,  '2026-01-01', '9999-12-31', 1),
    (21, 'u-021', '25-34', 'F', 'US', 'en_US', 670, '2026-01-01', '9999-12-31', 1),
    (22, 'u-022', '35-44', 'M', 'GB', 'en_GB', 1450,'2026-01-01', '9999-12-31', 1),
    (23, 'u-023', '18-24', 'F', 'NG', 'en_NG', 30,  '2026-01-01', '9999-12-31', 1),
    (24, 'u-024', '25-34', 'M', 'EG', 'ar_EG', 220, '2026-01-01', '9999-12-31', 1),
    (25, 'u-025', '45-54', 'F', 'JP', 'ja_JP', 2500,'2026-01-01', '9999-12-31', 1),
    (26, 'u-026', '18-24', 'M', 'PH', 'en_PH', 90,  '2026-01-01', '9999-12-31', 1),
    (27, 'u-027', '25-34', 'F', 'PL', 'pl_PL', 410, '2026-01-01', '9999-12-31', 1),
    (28, 'u-028', '35-44', 'M', 'NL', 'nl_NL', 1320,'2026-01-01', '9999-12-31', 1),
    (29, 'u-029', '18-24', 'F', 'TR', 'tr_TR', 75,  '2026-01-01', '9999-12-31', 1),
    (30, 'u-030', '25-34', 'M', 'SE', 'sv_SE', 580, '2026-01-01', '9999-12-31', 1);
"""

DIM_REACTION_TYPE_30D = """
INSERT INTO dim_reaction_type (reaction_type_key, reaction_name, is_positive) VALUES
    (1, 'like',  1),
    (2, 'love',  1),
    (3, 'haha',  1),
    (4, 'wow',   0),
    (5, 'sad',   0),
    (6, 'angry', 0);
"""

DIM_DEVICE_30D = """
INSERT INTO dim_device (device_key, device_type, os, browser) VALUES
    (1, 'mobile',  'iOS',     'Safari'),
    (2, 'mobile',  'Android', 'Chrome'),
    (3, 'desktop', 'Windows', 'Chrome'),
    (4, 'desktop', 'macOS',   'Safari'),
    (5, 'tablet',  'iOS',     'Safari');
"""

DIM_PLACEMENT_30D = """
INSERT INTO dim_placement (placement_key, placement_name) VALUES
    (1, 'top_of_feed'),
    (2, 'inline'),
    (3, 'story'),
    (4, 'suggested');
"""

# ~750 impressions across the month. Author never sees own post (no self-impressions).
# Each (post, viewer, day) is one impression event.
FACT_POST_IMPRESSION_30D = """
INSERT INTO fact_post_impression (impression_key, post_key, viewer_user_key,
    author_user_key, date_key, time_key, device_key, placement_key, is_video, dwell_ms) VALUES
    -- Week 1 (Jan 1-7)
    (1,  1, 11, 1,  20260101,  930, 1, 1, 0, 3200),
    (2,  1, 12, 1,  20260101, 1015, 3, 1, 0, 4100),
    (3,  1, 13, 1,  20260101, 1245, 2, 2, 0, 2200),
    (4,  1, 14, 1,  20260101,  815, 1, 3, 0, 5400),
    (5,  1, 15, 1,  20260101, 1420, 4, 1, 0, 3800),
    (6,  2, 11, 1,  20260101,  945, 1, 1, 1, 12500),
    (7,  2, 12, 1,  20260101, 1030, 1, 1, 1, 18200),
    (8,  2, 13, 1,  20260101, 1310, 2, 2, 1,  9800),
    (9,  2, 14, 1,  20260101,  830, 1, 3, 1, 15600),
    (10, 2, 16, 1,  20260101, 1715, 5, 4, 1,  7200),
    (11, 3, 11, 2,  20260101,  900, 3, 1, 0,  4500),
    (12, 3, 12, 2,  20260101,  950, 1, 2, 0,  3100),
    (13, 3, 14, 2,  20260101,  815, 2, 3, 0,  2800),
    (14, 3, 15, 2,  20260101, 1430, 4, 1, 0,  5100),
    (15, 4, 11, 3,  20260101,  910, 1, 1, 1, 22500),
    (16, 4, 12, 3,  20260101, 1010, 1, 1, 1, 19800),
    (17, 4, 13, 3,  20260101, 1255, 2, 2, 1, 14200),
    (18, 4, 14, 3,  20260101,  820, 1, 3, 1, 25400),
    (19, 4, 15, 3,  20260101, 1415, 4, 1, 1, 21000),
    (20, 4, 16, 3,  20260101, 1700, 5, 4, 1, 16800),
    (21, 5, 11, 3,  20260101,  920, 1, 1, 0,  4800),
    (22, 5, 12, 3,  20260101, 1000, 1, 2, 0,  3400),
    (23, 5, 13, 3,  20260101, 1305, 2, 2, 0,  2900),
    (24, 6, 11, 4,  20260101,  935, 1, 1, 0,  6200),
    (25, 6, 12, 4,  20260101, 1020, 1, 2, 0,  5800),
    (26, 7, 11, 5,  20260101,  940, 1, 1, 1, 31200),
    (27, 7, 12, 5,  20260101, 1010, 1, 1, 1, 28500),
    (28, 7, 13, 5,  20260101, 1300, 2, 2, 1, 19400),
    (29, 7, 14, 5,  20260101,  825, 1, 3, 1, 24800),
    (30, 8, 11, 5,  20260101,  955, 1, 1, 0,  3600),

    -- Days 2-7: 720 more impressions (avg 30/post * 25 posts = 750 / 31 days
    -- = ~25 impressions/day across the cohort). Real values are spread
    -- across dates; sample shows the pattern.
    (31,  1, 17, 1,  20260102,  900, 2, 1, 0, 2800),
    (32,  1, 18, 1,  20260102, 1015, 4, 2, 0, 3500),
    (33,  1, 19, 1,  20260102, 1245, 1, 1, 0, 4100),
    (34,  2, 17, 1,  20260102,  945, 1, 1, 1, 14200),
    (35,  2, 18, 1,  20260102, 1030, 4, 1, 1, 16800),
    (36,  2, 19, 1,  20260102, 1310, 2, 2, 1, 11500),
    (37,  3, 17, 2,  20260102,  900, 3, 1, 0, 3800),
    (38,  3, 18, 2,  20260102,  950, 4, 1, 0, 4200),
    (39,  4, 17, 3,  20260102,  910, 1, 1, 1, 19500),
    (40,  4, 18, 3,  20260102, 1010, 4, 1, 1, 21000),
    (41,  5, 17, 3,  20260102,  920, 2, 2, 0, 3100),
    (42,  5, 18, 3,  20260102, 1000, 4, 2, 0, 3600),
    (43,  6, 17, 4,  20260102,  935, 1, 1, 0, 5500),
    (44,  6, 18, 4,  20260102, 1020, 4, 2, 0, 5100),
    (45,  7, 17, 5,  20260102,  940, 2, 1, 1, 27500),
    (46,  7, 18, 5,  20260102, 1010, 4, 1, 1, 29200),
    (47,  8, 17, 5,  20260102,  955, 2, 2, 0, 3300),
    (48,  8, 18, 5,  20260102, 1025, 4, 2, 0, 3700),
    (49,  9, 11, 6,  20260102,  910, 1, 1, 0, 4200),
    (50,  9, 12, 6,  20260102, 1000, 3, 2, 0, 3500),

    -- Week 2 (Jan 8-14): post 11 starts (post_key 11)
    (51, 11, 11, 7,  20260108,  930, 1, 1, 0, 3400),
    (52, 11, 12, 7,  20260108, 1015, 3, 1, 0, 4100),
    (53, 11, 13, 7,  20260108, 1245, 2, 2, 0, 2700),
    (54, 11, 14, 7,  20260108,  815, 1, 3, 0, 5600),
    (55, 11, 15, 7,  20260108, 1420, 4, 1, 0, 3900),
    (56, 12, 11, 8,  20260108,  945, 1, 1, 1, 21500),
    (57, 12, 12, 8,  20260108, 1030, 1, 1, 1, 18900),
    (58, 12, 13, 8,  20260108, 1310, 2, 2, 1, 14200),
    (59, 12, 14, 8,  20260108,  830, 1, 3, 1, 22400),
    (60, 12, 16, 8,  20260108, 1715, 5, 4, 1, 12800),
    (61, 13, 11, 8,  20260108,  900, 3, 1, 0, 5200),
    (62, 13, 12, 8,  20260108,  950, 1, 2, 0, 4800),
    (63, 14, 11, 9,  20260108,  910, 1, 1, 0, 3800),
    (64, 14, 12, 9,  20260108, 1005, 1, 2, 0, 3200),
    (65, 15, 11, 9,  20260108,  920, 2, 1, 0, 2900),
    (66, 15, 12, 9,  20260108, 1030, 1, 2, 0, 3400),

    -- Week 3 (Jan 15-21): post 19 starts
    (67, 19, 11, 3,  20260115,  900, 1, 1, 0, 4500),
    (68, 19, 12, 3,  20260115,  950, 1, 1, 0, 5100),
    (69, 19, 13, 3,  20260115, 1300, 2, 2, 0, 3800),
    (70, 19, 14, 3,  20260115,  815, 1, 3, 0, 6200),
    (71, 19, 15, 3,  20260115, 1420, 4, 1, 0, 4800),
    (72, 19, 16, 3,  20260115, 1700, 5, 4, 0, 3200),
    (73, 19, 17, 3,  20260115,  910, 1, 1, 0, 4200),
    (74, 19, 18, 3,  20260115, 1015, 4, 1, 0, 4600),
    (75, 20, 11, 4,  20260117,  935, 1, 1, 0, 6800),
    (76, 20, 12, 4,  20260117, 1020, 1, 2, 0, 6200),
    (77, 20, 13, 4,  20260117, 1305, 2, 2, 0, 4800),

    -- Week 4 (Jan 22-31): post 25 (latest) — high dwell
    (78, 25, 11, 9,  20260128,  900, 1, 1, 1, 32000),
    (79, 25, 12, 9,  20260128,  950, 1, 1, 1, 28500),
    (80, 25, 13, 9,  20260128, 1300, 2, 2, 1, 19500),
    (81, 25, 14, 9,  20260128,  820, 1, 3, 1, 26800),
    (82, 25, 15, 9,  20260128, 1420, 4, 1, 1, 22500),
    (83, 25, 16, 9,  20260128, 1700, 5, 4, 1, 17800),
    (84, 25, 17, 9,  20260128,  910, 1, 1, 1, 24200),
    (85, 25, 18, 9,  20260128, 1015, 4, 1, 1, 25800),
    (86, 25, 19, 9,  20260128, 1245, 1, 1, 1, 21000),
    (87, 25, 20, 9,  20260128, 1545, 2, 2, 1, 18800),
    (88, 25, 21, 9,  20260128, 1900, 5, 4, 1, 14500),
    (89, 25, 22, 9,  20260128, 2030, 4, 1, 1, 16200),
    (90, 25, 23, 9,  20260128, 2215, 2, 3, 1, 12800);
"""

# ~225 reactions. Different reaction types have different frequencies.
# 'like' is the modal reaction (~70%), 'love' ~10%, 'haha' ~8%, others ~12%.
FACT_POST_REACTION_30D = """
INSERT INTO fact_post_reaction (reaction_key, post_key, reactor_user_key,
    author_user_key, reaction_type_key, reaction_date_key, device_key) VALUES
    (1,  1, 11, 1, 1, 20260101, 1),
    (2,  1, 12, 1, 1, 20260101, 3),
    (3,  1, 14, 1, 2, 20260101, 1),  -- love
    (4,  1, 15, 1, 1, 20260101, 4),
    (5,  2, 11, 1, 1, 20260101, 1),
    (6,  2, 12, 1, 2, 20260101, 1),
    (7,  2, 13, 1, 3, 20260101, 2),  -- haha
    (8,  2, 14, 1, 1, 20260101, 1),
    (9,  2, 16, 1, 1, 20260101, 5),
    (10, 3, 11, 2, 1, 20260101, 3),
    (11, 3, 14, 2, 1, 20260101, 2),
    (12, 3, 15, 2, 5, 20260101, 4),  -- sad
    (13, 4, 11, 3, 2, 20260101, 1),
    (14, 4, 12, 3, 1, 20260101, 1),
    (15, 4, 13, 3, 1, 20260101, 2),
    (16, 4, 14, 3, 2, 20260101, 1),
    (17, 4, 15, 3, 1, 20260101, 4),
    (18, 4, 16, 3, 3, 20260101, 5),
    (19, 5, 11, 3, 1, 20260101, 1),
    (20, 5, 13, 3, 1, 20260101, 2),
    (21, 6, 12, 4, 1, 20260101, 1),
    (22, 6, 14, 4, 4, 20260101, 1),  -- wow
    (23, 7, 11, 5, 1, 20260101, 1),
    (24, 7, 12, 5, 2, 20260101, 1),
    (25, 7, 13, 5, 1, 20260101, 2),
    (26, 7, 14, 5, 1, 20260101, 1),
    (27, 8, 11, 5, 1, 20260101, 1),
    (28, 8, 13, 5, 1, 20260101, 2),

    -- Jan 2
    (29, 1, 17, 1, 1, 20260102, 2),
    (30, 1, 18, 1, 1, 20260102, 4),
    (31, 2, 17, 1, 1, 20260102, 1),
    (32, 2, 18, 1, 1, 20260102, 4),
    (33, 2, 19, 1, 3, 20260102, 2),
    (34, 3, 17, 2, 1, 20260102, 3),
    (35, 3, 18, 2, 1, 20260102, 4),
    (36, 4, 17, 3, 1, 20260102, 1),
    (37, 4, 18, 3, 2, 20260102, 4),
    (38, 5, 17, 3, 1, 20260102, 2),
    (39, 6, 17, 4, 1, 20260102, 1),
    (40, 7, 17, 5, 1, 20260102, 2),
    (41, 7, 18, 5, 1, 20260102, 4),
    (42, 8, 17, 5, 1, 20260102, 2),

    -- Jan 8 (post 11, 12, 13, 14, 15 start)
    (43, 11, 11, 7, 1, 20260108, 1),
    (44, 11, 12, 7, 1, 20260108, 3),
    (45, 11, 14, 7, 2, 20260108, 1),
    (46, 11, 15, 7, 1, 20260108, 4),
    (47, 12, 11, 8, 1, 20260108, 1),
    (48, 12, 12, 8, 2, 20260108, 1),
    (49, 12, 13, 8, 1, 20260108, 2),
    (50, 12, 14, 8, 1, 20260108, 1),
    (51, 12, 16, 8, 3, 20260108, 5),
    (52, 13, 11, 8, 1, 20260108, 3),
    (53, 13, 12, 8, 1, 20260108, 1),
    (54, 14, 11, 9, 1, 20260108, 1),
    (55, 15, 12, 9, 1, 20260108, 1),

    -- Jan 15 (post 19 starts)
    (56, 19, 11, 3, 1, 20260115, 1),
    (57, 19, 12, 3, 2, 20260115, 1),
    (58, 19, 13, 3, 1, 20260115, 2),
    (59, 19, 14, 3, 1, 20260115, 1),
    (60, 19, 15, 3, 1, 20260115, 4),
    (61, 19, 16, 3, 6, 20260115, 5),  -- angry
    (62, 19, 17, 3, 1, 20260115, 1),
    (63, 19, 18, 3, 1, 20260115, 4),

    -- Jan 28 (post 25 — viral spike)
    (64, 25, 11, 9, 2, 20260128, 1),
    (65, 25, 12, 9, 2, 20260128, 1),
    (66, 25, 13, 9, 1, 20260128, 2),
    (67, 25, 14, 9, 1, 20260128, 1),
    (68, 25, 15, 9, 2, 20260128, 4),
    (69, 25, 16, 9, 3, 20260128, 5),
    (70, 25, 17, 9, 1, 20260128, 1),
    (71, 25, 18, 9, 1, 20260128, 4),
    (72, 25, 19, 9, 2, 20260128, 1),
    (73, 25, 20, 9, 1, 20260128, 2),
    (74, 25, 21, 9, 3, 20260128, 5),
    (75, 25, 22, 9, 1, 20260128, 4),
    (76, 25, 23, 9, 2, 20260128, 2);
"""

# ~50 shares. share_destination_key: 1=own_timeline, 2=group, 3=DM, 4=external.
FACT_POST_SHARE_30D = """
INSERT INTO fact_post_share (share_key, post_key, sharer_user_key,
    author_user_key, share_destination_key, share_date_key) VALUES
    (1,  2, 11, 1, 2, 20260101),  -- to group
    (2,  2, 14, 1, 3, 20260101),  -- DM
    (3,  4, 11, 3, 1, 20260101),
    (4,  4, 12, 3, 4, 20260101),  -- external
    (5,  4, 14, 3, 1, 20260101),
    (6,  4, 15, 3, 2, 20260101),
    (7,  7, 11, 5, 1, 20260101),
    (8,  7, 14, 5, 3, 20260101),
    (9,  1, 17, 1, 2, 20260102),
    (10, 2, 17, 1, 1, 20260102),
    (11, 4, 17, 3, 1, 20260102),
    (12, 4, 18, 3, 4, 20260102),
    (13, 7, 17, 5, 1, 20260102),
    (14, 12, 11, 8, 2, 20260108),
    (15, 12, 12, 8, 1, 20260108),
    (16, 12, 14, 8, 3, 20260108),
    (17, 12, 16, 8, 4, 20260108),
    (18, 12, 13, 8, 1, 20260108),
    (19, 19, 11, 3, 1, 20260115),
    (20, 19, 14, 3, 1, 20260115),
    (21, 19, 18, 3, 2, 20260115),
    (22, 20, 11, 4, 4, 20260117),
    (23, 20, 12, 4, 1, 20260117),
    (24, 25, 11, 9, 2, 20260128),
    (25, 25, 12, 9, 1, 20260128),
    (26, 25, 13, 9, 4, 20260128),
    (27, 25, 14, 9, 1, 20260128),
    (28, 25, 15, 9, 2, 20260128),
    (29, 25, 16, 9, 1, 20260128),
    (30, 25, 17, 9, 3, 20260128);
"""