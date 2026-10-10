-- Schemas for the 5 most-asked Meta DE data-modeling questions (2026).
-- See design/04_concrete_solutions.md for the worked solutions.
--
-- This file is runnable: `python3 tests/test_onsite_schemas.py` exercises
-- the CREATE TABLE statements and a sample INSERT + query for each.

-- ====================================================================
-- Q1: Reels performance star schema (IG Reels surface)
-- ====================================================================
DROP TABLE IF EXISTS reel_hashtag_bridge;
DROP TABLE IF EXISTS reel_audio_bridge;
DROP TABLE IF EXISTS fct_reel_view;
DROP TABLE IF EXISTS dim_algorithm_version;

CREATE TABLE dim_algorithm_version (
    algorithm_version_id  INTEGER PRIMARY KEY,
    algorithm_name        TEXT    NOT NULL,
    parameters_json       TEXT    NOT NULL,
    valid_from            TEXT    NOT NULL,
    valid_to              TEXT    NOT NULL DEFAULT '9999-12-31',
    is_current            INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE fct_reel_view (
    event_date              TEXT    NOT NULL,
    hour_bucket             INTEGER NOT NULL,
    reel_id                 INTEGER NOT NULL,
    viewer_id               INTEGER NOT NULL,
    algorithm_version_id    INTEGER NOT NULL,
    n_views                 INTEGER NOT NULL DEFAULT 0,
    n_likes                 INTEGER NOT NULL DEFAULT 0,
    n_shares                INTEGER NOT NULL DEFAULT 0,
    n_saves                 INTEGER NOT NULL DEFAULT 0,
    n_completes             INTEGER NOT NULL DEFAULT 0,
    view_duration_ms        INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (event_date, hour_bucket, reel_id, viewer_id, algorithm_version_id)
) WITHOUT ROWID;

CREATE TABLE reel_hashtag_bridge (
    reel_id     INTEGER NOT NULL,
    hashtag_id  INTEGER NOT NULL,
    PRIMARY KEY (reel_id, hashtag_id)
) WITHOUT ROWID;

CREATE TABLE reel_audio_bridge (
    reel_id   INTEGER NOT NULL,
    audio_id  INTEGER NOT NULL,
    PRIMARY KEY (reel_id, audio_id)
) WITHOUT ROWID;

-- Sample data: 3 algorithm versions (SCD2 history), 6 reel-view rows.
INSERT INTO dim_algorithm_version
    (algorithm_version_id, algorithm_name, parameters_json, valid_from, valid_to, is_current) VALUES
  (1, 'reels_v1', '{"threshold":0.3}',  '2026-01-01', '2026-01-15', 0),
  (2, 'reels_v2', '{"threshold":0.4}',  '2026-01-15', '2026-02-01', 0),
  (3, 'reels_v3', '{"threshold":0.5}',  '2026-02-01', '9999-12-31', 1);

INSERT INTO fct_reel_view
    (event_date, hour_bucket, reel_id, viewer_id, algorithm_version_id,
     n_views, n_likes, n_shares, n_saves, n_completes, view_duration_ms) VALUES
  ('2026-02-15', 10, 1001, 901, 3, 5, 2, 1, 1, 4, 45000),
  ('2026-02-15', 10, 1001, 902, 3, 3, 1, 0, 0, 2, 12000),
  ('2026-02-15', 11, 1002, 901, 3, 8, 3, 2, 1, 6, 80000),
  ('2026-02-15', 11, 1002, 903, 3, 2, 0, 0, 0, 1, 5000),
  ('2026-02-15', 12, 1003, 902, 3, 1, 0, 0, 0, 0, 2000),
  ('2026-02-15', 12, 1003, 904, 3, 4, 1, 0, 0, 3, 30000);

INSERT INTO reel_hashtag_bridge (reel_id, hashtag_id) VALUES
  (1001, 1), (1001, 2), (1002, 3), (1003, 1), (1003, 4);

INSERT INTO reel_audio_bridge (reel_id, audio_id) VALUES
  (1001, 10), (1002, 11), (1003, 10);

-- ====================================================================
-- Q2: Cross-platform unified-user behavior (UA surface)
-- ====================================================================
DROP TABLE IF EXISTS fct_user_event;
DROP TABLE IF EXISTS user_identity_bridge;

CREATE TABLE user_identity_bridge (
    unified_user_id    INTEGER NOT NULL,
    platform           TEXT    NOT NULL,
    platform_user_id   INTEGER NOT NULL,
    valid_from         TEXT    NOT NULL,
    valid_to           TEXT    NOT NULL DEFAULT '9999-12-31',
    PRIMARY KEY (platform, platform_user_id, valid_from)
) WITHOUT ROWID;

CREATE TABLE fct_user_event (
    event_date         TEXT    NOT NULL,
    event_ts           TEXT    NOT NULL,
    unified_user_id    INTEGER NOT NULL,
    platform           TEXT    NOT NULL,
    event_type         TEXT    NOT NULL,
    content_id         INTEGER,
    session_id         INTEGER,
    PRIMARY KEY (event_date, event_ts, unified_user_id, event_type)
) WITHOUT ROWID;

-- Sample data: user 1 is on both IG and WA; user 2 is FB-only.
INSERT INTO user_identity_bridge
    (unified_user_id, platform, platform_user_id, valid_from) VALUES
  (1, 'IG', 101, '2026-01-01'),
  (1, 'WA', 201, '2026-01-01'),
  (2, 'FB', 102, '2026-01-01'),
  (3, 'IG', 103, '2026-01-01');

INSERT INTO fct_user_event
    (event_date, event_ts, unified_user_id, platform, event_type, content_id, session_id) VALUES
  ('2026-02-15', '2026-02-15T10:00:00', 1, 'IG', 'view',  5001, 1),
  ('2026-02-15', '2026-02-15T10:05:00', 1, 'IG', 'like',  5001, 1),
  ('2026-02-15', '2026-02-15T14:00:00', 1, 'WA', 'send',  NULL, 2),
  ('2026-02-15', '2026-02-15T18:30:00', 2, 'FB', 'view',  5002, 3),
  ('2026-02-16', '2026-02-16T09:00:00', 3, 'IG', 'view',  5003, 4);

-- ====================================================================
-- Q3: Ads Auction (real-time bid + historical)
-- ====================================================================
DROP TABLE IF EXISTS fct_impression;
DROP TABLE IF EXISTS fct_auction_event;
DROP TABLE IF EXISTS dim_ad_set;

CREATE TABLE dim_ad_set (
    ad_set_id        INTEGER PRIMARY KEY,
    advertiser_id    INTEGER NOT NULL,
    name             TEXT    NOT NULL,
    campaign_state   TEXT    NOT NULL,
    budget_cents     INTEGER NOT NULL,
    valid_from       TEXT    NOT NULL,
    valid_to         TEXT    NOT NULL DEFAULT '9999-12-31',
    is_current       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE fct_auction_event (
    auction_ts    TEXT    NOT NULL,
    auction_id    INTEGER NOT NULL,
    ad_id         INTEGER NOT NULL,
    advertiser_id INTEGER NOT NULL,
    user_id       INTEGER,
    bid_amount    REAL    NOT NULL,
    won_flag      INTEGER NOT NULL,
    PRIMARY KEY (auction_ts, auction_id)
) WITHOUT ROWID;

CREATE TABLE fct_impression (
    auction_id    INTEGER PRIMARY KEY,
    ad_id         INTEGER NOT NULL,
    user_id       INTEGER,
    impression_ts TEXT    NOT NULL,
    revenue_cents INTEGER NOT NULL DEFAULT 0
);

-- Sample data: 5 auctions, 3 won, 2 impressions for the 3 won auctions.
INSERT INTO dim_ad_set
    (ad_set_id, advertiser_id, name, campaign_state, budget_cents, valid_from, is_current) VALUES
  (1, 801, 'spring_sale',  'active',   100000, '2026-01-01', 0),
  (2, 801, 'spring_sale',  'active',   200000, '2026-02-01', 1),
  (3, 802, 'winter_clear', 'paused',    50000, '2026-01-01', 1);

INSERT INTO fct_auction_event
    (auction_ts, auction_id, ad_id, advertiser_id, user_id, bid_amount, won_flag) VALUES
  ('2026-02-15T10:00:00', 1, 1, 801, 901, 1.50, 1),
  ('2026-02-15T10:00:01', 2, 2, 801, 902, 1.20, 0),
  ('2026-02-15T10:00:02', 3, 1, 801, 903, 1.60, 1),
  ('2026-02-15T10:00:03', 4, 3, 802, 904, 1.80, 0),
  ('2026-02-15T10:00:04', 5, 2, 801, 905, 1.40, 1);

INSERT INTO fct_impression (auction_id, ad_id, user_id, impression_ts, revenue_cents) VALUES
  (1, 1, 901, '2026-02-15T10:00:00', 250),
  (3, 1, 903, '2026-02-15T10:00:02', 300),
  (5, 2, 905, '2026-02-15T10:00:04', 180);

-- ====================================================================
-- Q4: Ride-share transactional (Marketplace surface)
-- ====================================================================
DROP TABLE IF EXISTS fct_trip_event;
DROP TABLE IF EXISTS fct_trip;

CREATE TABLE fct_trip (
    trip_id        INTEGER PRIMARY KEY,
    rider_id       INTEGER NOT NULL,
    driver_id      INTEGER NOT NULL,
    city_id        INTEGER NOT NULL,
    request_ts     TEXT    NOT NULL,
    pickup_ts      TEXT,
    dropoff_ts     TEXT,
    status         TEXT    NOT NULL,
    fare_cents     INTEGER NOT NULL
);

CREATE TABLE fct_trip_event (
    event_date   TEXT    NOT NULL,
    event_ts     TEXT    NOT NULL,
    trip_id      INTEGER NOT NULL,
    event_type   TEXT    NOT NULL,
    city_id      INTEGER NOT NULL,
    PRIMARY KEY (event_date, event_ts, trip_id)
) WITHOUT ROWID;

INSERT INTO fct_trip
    (trip_id, rider_id, driver_id, city_id, request_ts, pickup_ts, dropoff_ts, status, fare_cents) VALUES
  (1, 1001, 2001, 50, '2026-02-15T10:00:00', '2026-02-15T10:05:00', '2026-02-15T10:25:00', 'completed', 1500),
  (2, 1002, 2002, 50, '2026-02-15T10:30:00', '2026-02-15T10:33:00', '2026-02-15T11:00:00', 'completed', 2200),
  (3, 1003, 2001, 50, '2026-02-15T11:00:00', NULL,                     NULL,                       'cancelled', 0);

INSERT INTO fct_trip_event
    (event_date, event_ts, trip_id, event_type, city_id) VALUES
  ('2026-02-15', '2026-02-15T10:00:00', 1, 'requested', 50),
  ('2026-02-15', '2026-02-15T10:05:00', 1, 'pickup',    50),
  ('2026-02-15', '2026-02-15T10:25:00', 1, 'dropoff',   50),
  ('2026-02-15', '2026-02-15T10:30:00', 2, 'requested', 50),
  ('2026-02-15', '2026-02-15T10:33:00', 2, 'pickup',    50),
  ('2026-02-15', '2026-02-15T11:00:00', 2, 'dropoff',   50),
  ('2026-02-15', '2026-02-15T11:00:00', 3, 'cancelled', 50);

-- ====================================================================
-- Q5: Metric-investigation (PA / IG surface)
-- ====================================================================
DROP TABLE IF EXISTS fct_metric_value;
DROP TABLE IF EXISTS dim_metric;

CREATE TABLE dim_metric (
    metric_id   INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL,
    definition  TEXT    NOT NULL,
    owner_team  TEXT    NOT NULL
);

CREATE TABLE fct_metric_value (
    metric_id      INTEGER NOT NULL,
    time_bucket    TEXT    NOT NULL,
    segment_id     INTEGER NOT NULL,
    value          REAL    NOT NULL,
    sample_size    INTEGER NOT NULL,
    PRIMARY KEY (metric_id, time_bucket, segment_id)
) WITHOUT ROWID;

INSERT INTO dim_metric (metric_id, name, definition, owner_team) VALUES
  (1, 'reels_like_rate', 'n_likes / n_views', 'IG Reels'),
  (2, 'reels_complete_rate', 'n_completes / n_views', 'IG Reels');

INSERT INTO fct_metric_value (metric_id, time_bucket, segment_id, value, sample_size) VALUES
  -- reels_like_rate for segment 1 (US, mobile) over 4 days
  (1, '2026-02-12', 1, 0.42, 1_000_000),
  (1, '2026-02-13', 1, 0.41, 1_050_000),
  (1, '2026-02-14', 1, 0.30, 1_100_000),  -- <-- THE DROP
  (1, '2026-02-15', 1, 0.28, 1_080_000),
  -- reels_like_rate for segment 2 (US, desktop) over the same 4 days
  (1, '2026-02-12', 2, 0.40, 200_000),
  (1, '2026-02-13', 2, 0.41, 210_000),
  (1, '2026-02-14', 2, 0.40, 220_000),
  (1, '2026-02-15', 2, 0.41, 215_000);
