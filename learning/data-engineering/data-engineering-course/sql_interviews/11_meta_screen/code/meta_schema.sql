-- Schema: 5 social-event tables for the 2026 Meta DE screen.
-- Conventions:
--   * Date columns are ISO 8601 TEXT (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).
--   * IDs are INTEGER.
--   * Booleans are INTEGER 0/1.
--   * All times are UTC.

DROP TABLE IF EXISTS instagram_story_events;
DROP TABLE IF EXISTS instagram_post;
DROP TABLE IF EXISTS facebook_post;
DROP TABLE IF EXISTS engagement_event;
DROP TABLE IF EXISTS whatsapp_message;
DROP TABLE IF EXISTS messenger_call;
DROP TABLE IF EXISTS messenger_event;
DROP TABLE IF EXISTS ad_auction_event;
DROP TABLE IF EXISTS ad_event;

-- Instagram: posts + story-view events.
CREATE TABLE instagram_post (
    post_id   INTEGER PRIMARY KEY,
    user_id   INTEGER NOT NULL,
    post_date TEXT    NOT NULL,         -- YYYY-MM-DD
    likes     INTEGER NOT NULL DEFAULT 0,
    comments  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE instagram_story_events (
    event_id        INTEGER PRIMARY KEY,
    user_id         INTEGER NOT NULL,
    country         TEXT    NOT NULL,
    event_ts        TEXT    NOT NULL,   -- YYYY-MM-DDTHH:MM:SS
    event_type      TEXT    NOT NULL,   -- view | reply | exit
    view_duration_ms INTEGER NOT NULL DEFAULT 0
);

-- Facebook: posts + engagement events.
CREATE TABLE facebook_post (
    post_id     INTEGER PRIMARY KEY,
    page_id     INTEGER NOT NULL,
    post_ts     TEXT    NOT NULL,
    impressions INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE engagement_event (
    event_id INTEGER PRIMARY KEY,
    post_id  INTEGER NOT NULL,
    user_id  INTEGER NOT NULL,
    event_ts TEXT    NOT NULL
);

-- WhatsApp: messages.
CREATE TABLE whatsapp_message (
    msg_id     INTEGER PRIMARY KEY,
    sender_id  INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    sent_ts    TEXT    NOT NULL
);

-- Messenger: events + calls.
CREATE TABLE messenger_event (
    event_id INTEGER PRIMARY KEY,
    user_id  INTEGER NOT NULL,
    event_ts TEXT    NOT NULL
);

CREATE TABLE messenger_call (
    call_id    INTEGER PRIMARY KEY,
    caller_id  INTEGER NOT NULL,
    callee_id  INTEGER NOT NULL,
    started_ts TEXT    NOT NULL,
    duration_s INTEGER NOT NULL,
    is_video   INTEGER NOT NULL  -- 0 or 1
);

-- Ads: events + auction events.
CREATE TABLE ad_event (
    event_id      INTEGER PRIMARY KEY,
    advertiser_id INTEGER NOT NULL,
    ad_set_id     INTEGER NOT NULL,
    event_ts      TEXT    NOT NULL,
    revenue       REAL    NOT NULL DEFAULT 0,
    spend         REAL    NOT NULL DEFAULT 0
);

CREATE TABLE ad_auction_event (
    auction_ts TEXT    NOT NULL,
    ad_id      INTEGER NOT NULL,
    bid_amount REAL    NOT NULL,
    won_flag   INTEGER NOT NULL
);

-- Sample data (deterministic, ~10 rows per table).
INSERT INTO instagram_post (post_id, user_id, post_date, likes, comments) VALUES
  (1, 101, '2026-01-01', 150, 20),
  (2, 101, '2026-01-03', 220, 35),
  (3, 101, '2026-01-05', 90,  10),
  (4, 102, '2026-01-02', 50,  5),
  (5, 102, '2026-01-04', 75,  8),
  (6, 103, '2026-01-01', 300, 60);

INSERT INTO instagram_story_events
  (event_id, user_id, country, event_ts, event_type, view_duration_ms) VALUES
  (1, 201, 'US', '2026-01-01T08:00:00', 'view', 5000),
  (2, 201, 'US', '2026-01-01T08:05:00', 'view', 3000),
  (3, 201, 'US', '2026-01-01T08:45:00', 'view', 4000),  -- 40 min later (new session)
  (4, 202, 'IN', '2026-01-01T09:00:00', 'view', 2000),
  (5, 202, 'IN', '2026-01-02T09:00:00', 'view', 2500),  -- next day (new session)
  (6, 203, 'US', '2026-01-01T10:00:00', 'view', 6000),
  (7, 203, 'US', '2026-01-02T10:00:00', 'view', 5500),
  (8, 203, 'US', '2026-01-03T10:00:00', 'view', 5000),
  (9, 203, 'US', '2026-01-04T10:00:00', 'view', 4500),  -- 4 consecutive days
  (10, 204, 'BR', '2026-01-01T12:00:00', 'view', 1000);

INSERT INTO facebook_post (post_id, page_id, post_ts, impressions) VALUES
  (1, 301, '2026-01-01T10:00:00', 1000),
  (2, 301, '2026-01-02T10:00:00', 1500),
  (3, 301, '2026-01-03T10:00:00', 800),
  (4, 302, '2026-01-01T11:00:00', 500),
  (5, 302, '2026-01-02T11:00:00', 600);

INSERT INTO engagement_event (event_id, post_id, user_id, event_ts) VALUES
  (1, 1, 401, '2026-01-01T10:05:00'),
  (2, 1, 402, '2026-01-01T10:10:00'),
  (3, 1, 403, '2026-01-01T10:30:00'),  -- peak hour-1 = 3
  (4, 2, 404, '2026-01-02T10:20:00'),
  (5, 2, 405, '2026-01-02T10:30:00'),
  (6, 3, 406, '2026-01-03T10:15:00');  -- 1

INSERT INTO whatsapp_message (msg_id, sender_id, receiver_id, sent_ts) VALUES
  (1, 501, 601, '2024-01-15T10:00:00'),
  (2, 501, 602, '2024-01-15T11:00:00'),
  (3, 501, 603, '2024-02-15T10:00:00'),
  (4, 501, 604, '2024-03-15T10:00:00'),
  (5, 501, 605, '2024-04-15T10:00:00'),
  (6, 501, 606, '2024-05-15T10:00:00'),
  (7, 501, 607, '2024-06-15T10:00:00'),  -- 6 distinct months
  (8, 501, 608, '2024-07-15T10:00:00'),
  (9, 501, 609, '2024-08-15T10:00:00'),
  (10, 502, 610, '2024-02-15T10:00:00');

INSERT INTO messenger_event (event_id, user_id, event_ts) VALUES
  (1, 701, '2026-01-15T08:00:00'),
  (2, 702, '2026-01-15T09:00:00'),
  (3, 703, '2026-01-15T10:00:00'),
  (4, 701, '2026-01-15T11:00:00');

INSERT INTO messenger_call (call_id, caller_id, callee_id, started_ts, duration_s, is_video) VALUES
  (1, 701, 702, '2026-01-15T08:30:00', 60,  1),  -- both 701 and 702 active
  (2, 702, 703, '2026-01-15T10:30:00', 120, 0),  -- audio
  (3, 704, 705, '2026-01-15T11:00:00', 30,  1);

INSERT INTO ad_event (event_id, advertiser_id, ad_set_id, event_ts, revenue, spend) VALUES
  (1, 801, 901, '2026-01-01T10:00:00', 100, 20),
  (2, 801, 901, '2026-01-02T10:00:00', 150, 25),
  (3, 801, 902, '2026-01-01T11:00:00', 200, 50),
  (4, 801, 902, '2026-01-02T11:00:00', 180, 45),
  (5, 801, 903, '2026-01-01T12:00:00', 50,  10),  -- low ROAS
  (6, 802, 904, '2026-01-01T13:00:00', 300, 60);

INSERT INTO ad_auction_event (auction_ts, ad_id, bid_amount, won_flag) VALUES
  ('2026-01-01T10:00:00', 1001, 1.50, 1),
  ('2026-01-01T10:00:01', 1002, 1.20, 0),
  ('2026-01-01T10:00:02', 1001, 1.60, 1),
  ('2026-01-01T10:00:03', 1003, 1.80, 0);
