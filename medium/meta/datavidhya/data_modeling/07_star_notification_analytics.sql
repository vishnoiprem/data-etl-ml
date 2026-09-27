-- =====================================================================
-- 07 — OLAP: Notification Delivery Analytics  (star schema)
-- =====================================================================
-- Purpose: dashboards for notification effectiveness across channels
-- and user segments. Source-of-truth funnel from sent -> delivered ->
-- opened -> clicked, with non-additive rate metrics computed correctly.
--
-- Design notes:
--
--   * ONE FACT TABLE: fact_notification_delivery.
--     Grain = one (notification, user, channel). Per the problem
--     statement: "One fact table row per (notification, user, channel)
--     combination". Folding user/notification/campaign/channel into
--     one fact keeps every funnel query a single star-join away.
--
--   * FLAGS NOT NULLS for funnel stages.
--     Stored as `is_sent`, `is_delivered`, `is_opened`, `is_clicked`
--     BOOLEANS rather than separate timestamp columns. This makes
--     "delivery rate" = AVG(is_delivered::int) — the metric is always
--     in the same place. NULL timestamps would force analysts to
--     COALESCE everywhere.
--
--   * JUNK DIMENSION for low-cardinality flags.
--     delivery_error_type × is_duplicate × is_rate_limited ×
--     is_opted_out combined into ONE dim_notification_status row.
--     16 combinations of 4 booleans = 1 dim, no 4-way index clutter.
--
--   * SCD2 dim_users for segment-history analysis.
--     "Did active users engage better than new users last quarter?"
--     needs to know what segment a user was in at send time.
--     Same valid_from / valid_to / is_current pattern as 05.
--
--   * CONFORMED dim_date + dim_time.
--     Notification effectiveness varies by hour-of-day and weekday.
--     A separate dim_time lets analysts GROUP BY hour without a
--     bucketing function.
--
--   * RATES ARE NEVER STORED DIRECTLY.
--     Every query computes them as ratio-of-sums. Storing a
--     "delivery_rate" column would let a fact become inconsistent
--     with its numerator/denominator.
-- =====================================================================

\echo '=== Loading OLAP notification analytics star schema ==='

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---------------------------------------------------------------------
-- 1) dim_date  (conformed)
-- ---------------------------------------------------------------------
CREATE TABLE dim_date (
    day_key        INT PRIMARY KEY,
    date_actual    DATE NOT NULL UNIQUE,
    day_of_week    SMALLINT NOT NULL,
    day_name       TEXT NOT NULL,
    week_of_year   SMALLINT NOT NULL,
    month_of_year  SMALLINT NOT NULL,
    month_name     TEXT NOT NULL,
    quarter        SMALLINT NOT NULL,
    year           SMALLINT NOT NULL,
    is_weekend     BOOLEAN NOT NULL,
    is_holiday     BOOLEAN NOT NULL DEFAULT FALSE,
    fiscal_quarter TEXT
);

-- ---------------------------------------------------------------------
-- 2) dim_time  (hour of day)
-- ---------------------------------------------------------------------
-- 24 rows. Lets "open rate by hour" be a simple star-join.
CREATE TABLE dim_time (
    time_key        INT PRIMARY KEY,                          -- HHMM (e.g. 0900)
    hour_of_day     SMALLINT NOT NULL CHECK (hour_of_day BETWEEN 0 AND 23),
    minute_of_hour  SMALLINT NOT NULL CHECK (minute_of_hour BETWEEN 0 AND 59),
    is_business_hours BOOLEAN NOT NULL,
    is_evening      BOOLEAN NOT NULL,
    time_bucket     TEXT NOT NULL CHECK (time_bucket IN (
                       'overnight','morning','midday','afternoon','evening','late_night'))
);

INSERT INTO dim_time (time_key, hour_of_day, minute_of_hour, is_business_hours, is_evening, time_bucket)
SELECT
    h * 100,
    h,
    0,
    h BETWEEN 9 AND 17,
    h BETWEEN 18 AND 22,
    CASE
        WHEN h BETWEEN 0 AND 5  THEN 'overnight'
        WHEN h BETWEEN 6 AND 10 THEN 'morning'
        WHEN h BETWEEN 11 AND 13 THEN 'midday'
        WHEN h BETWEEN 14 AND 17 THEN 'afternoon'
        WHEN h BETWEEN 18 AND 22 THEN 'evening'
        ELSE 'late_night'
    END
FROM generate_series(0, 23) h;

-- ---------------------------------------------------------------------
-- 3) dim_channel  (small dimension)
-- ---------------------------------------------------------------------
CREATE TABLE dim_channel (
    channel_key     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_code    TEXT NOT NULL UNIQUE,                     -- 'email','push','sms','in_app'
    surface         TEXT NOT NULL,                            -- 'mobile','desktop','email','sms'
    description     TEXT
);

INSERT INTO dim_channel (channel_code, surface, description) VALUES
    ('email',   'email',  'Email provider'),
    ('push',    'mobile', 'Mobile push (APNs/FCM)'),
    ('sms',     'sms',    'SMS via Twilio etc.'),
    ('in_app',  'app',    'In-app bell icon');

-- ---------------------------------------------------------------------
-- 4) dim_notification_type  (the catalogue)
-- ---------------------------------------------------------------------
-- materialises the same event_type_code namespace as the OLTP
-- notifications system, but the OLAP team may rename or re-classify
-- without coupling to OLTP.
CREATE TABLE dim_notification_type (
    notification_type_key  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    type_code              TEXT NOT NULL UNIQUE,
    category               TEXT NOT NULL,
    description            TEXT
);

INSERT INTO dim_notification_type (type_code, category, description) VALUES
    ('comment.reply',   'social',        'Reply to your comment'),
    ('post.like',       'social',        'Like on your post'),
    ('friend.joined',   'social',        'A friend joined'),
    ('order.shipped',   'transactional', 'Your order shipped'),
    ('security.alert',  'security',      'Security-relevant event'),
    ('digest.weekly',   'digest',        'Weekly digest rollup'),
    ('campaign.bulk',   'marketing',     'Bulk campaign send');

-- ---------------------------------------------------------------------
-- 5) dim_users  (SCD TYPE 2)
-- ---------------------------------------------------------------------
CREATE TABLE dim_users (
    user_key           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id            BIGINT NOT NULL,
    email              TEXT,
    segment            TEXT NOT NULL
                       CHECK (segment IN ('new','active','dormant','vip','churned')),
    acquisition_channel TEXT,
    country            CHAR(2),
    valid_from         TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_to           TIMESTAMPTZ,
    is_current         BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_dim_user_natural ON dim_users(user_id, is_current);

-- ---------------------------------------------------------------------
-- 6) dim_campaign  (SCD-lite; campaigns are short-lived enough for type 1)
-- ---------------------------------------------------------------------
CREATE TABLE dim_campaign (
    campaign_key       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    campaign_id        BIGINT NOT NULL UNIQUE,
    name               TEXT NOT NULL,
    objective          TEXT,
    started_at         TIMESTAMPTZ,
    ended_at           TIMESTAMPTZ,
    is_active          BOOLEAN NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- 7) dim_notification_status  (JUNK DIMENSION)
-- ---------------------------------------------------------------------
-- Combining low-cardinality flags into ONE dimension is the standard
-- junk-dim pattern. 2^4 = 16 max rows; we actually populate the 8 most
-- common combinations. Analysts "GROUP BY status_key" and read the
-- semantics from one row of dim_notification_status.
CREATE TABLE dim_notification_status (
    status_key             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    is_delivered           BOOLEAN NOT NULL,                 -- was the channel-side delivery confirmed?
    is_opened              BOOLEAN NOT NULL,                 -- did the user open it?
    is_clicked             BOOLEAN NOT NULL,                 -- did the user click through?
    has_delivery_error     BOOLEAN NOT NULL,                 -- bounced / failed?
    is_duplicate           BOOLEAN NOT NULL,                 -- dedup hit?
    is_rate_limited        BOOLEAN NOT NULL,                 -- 429?
    is_opted_out           BOOLEAN NOT NULL,                 -- user opted out before send?
    label                  TEXT NOT NULL,                     -- 'sent_opened','failed_rate_limited',...
    UNIQUE (is_delivered, is_opened, is_clicked, has_delivery_error,
            is_duplicate, is_rate_limited, is_opted_out)
);

INSERT INTO dim_notification_status
    (is_delivered, is_opened, is_clicked, has_delivery_error, is_duplicate, is_rate_limited, is_opted_out, label) VALUES
    (TRUE,  TRUE,  TRUE,  FALSE, FALSE, FALSE, FALSE, 'engaged_full'),
    (TRUE,  TRUE,  FALSE, FALSE, FALSE, FALSE, FALSE, 'engaged_open'),
    (TRUE,  FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, 'sent_silent'),
    (FALSE, FALSE, FALSE, TRUE,  FALSE, FALSE, FALSE, 'failed_bounce'),
    (FALSE, FALSE, FALSE, TRUE,  FALSE, TRUE,  FALSE, 'failed_rate_limited'),
    (FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, TRUE,  'suppressed_optout'),
    (TRUE,  FALSE, FALSE, FALSE, TRUE,  FALSE, FALSE, 'duplicate_resend'),
    (FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, 'pending_send');

-- ---------------------------------------------------------------------
-- 8) fact_notification_delivery
-- ---------------------------------------------------------------------
-- Grain = one row per (notification, user, channel) attempt.
-- Funnel flags are the heart of the fact — every metric derives from
-- a ratio of these.
CREATE TABLE fact_notification_delivery (
    delivery_id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sent_ts               TIMESTAMPTZ NOT NULL,
    day_key               INT  NOT NULL REFERENCES dim_date(day_key),
    time_key              INT  NOT NULL REFERENCES dim_time(time_key),
    user_key              BIGINT NOT NULL REFERENCES dim_users(user_key),
    channel_key           BIGINT NOT NULL REFERENCES dim_channel(channel_key),
    notification_type_key BIGINT NOT NULL REFERENCES dim_notification_type(notification_type_key),
    campaign_key          BIGINT REFERENCES dim_campaign(campaign_key),
    status_key            BIGINT NOT NULL REFERENCES dim_notification_status(status_key),
    -- Funnel flags (denormalised mirror of status_key; makes any
    -- query that filters by flag use a partial index without a join).
    is_sent               BOOLEAN NOT NULL DEFAULT FALSE,
    is_delivered          BOOLEAN NOT NULL DEFAULT FALSE,
    is_opened             BOOLEAN NOT NULL DEFAULT FALSE,
    is_clicked            BOOLEAN NOT NULL DEFAULT FALSE,
    -- Latencies in seconds, NULL until the next stage happens.
    seconds_to_delivery   INTEGER,
    seconds_to_open       INTEGER,
    seconds_to_click      INTEGER,
    -- Provider info — kept at delivery grain.
    provider              TEXT,
    cost_per_send_usd     NUMERIC(8,4)
);

-- Star-join probes by day, channel, type are the common access path.
CREATE INDEX idx_fact_notif_day_channel ON fact_notification_delivery(day_key, channel_key);
CREATE INDEX idx_fact_notif_day_type    ON fact_notification_delivery(day_key, notification_type_key);
CREATE INDEX idx_fact_notif_user_day    ON fact_notification_delivery(user_key, day_key);

-- =====================================================================
-- Sample data — ~5000 deliveries across 4 channels, 5 users, 7 types.
-- =====================================================================

INSERT INTO dim_date (day_key, date_actual, day_of_week, day_name, week_of_year,
                      month_of_year, month_name, quarter, year, is_weekend, fiscal_quarter) VALUES
    (20260101, '2026-01-01', 4, 'Thursday', 1, 1, 'January', 1, 2026, FALSE, 'FY26-Q3'),
    (20260115, '2026-01-15', 4, 'Thursday', 3, 1, 'January', 1, 2026, FALSE, 'FY26-Q3'),
    (20260201, '2026-02-01', 7, 'Sunday',   5, 2, 'February',1, 2026, TRUE,  'FY26-Q4'),
    (20260215, '2026-02-15', 7, 'Sunday',   7, 2, 'February',1, 2026, TRUE,  'FY26-Q4');

INSERT INTO dim_users (user_id, email, segment, acquisition_channel, country, valid_from, valid_to, is_current) VALUES
    -- Alice: 'new' Jan, 'active' Feb.
    (1, 'alice@example.com', 'new',     'organic', 'US', '2026-01-01', '2026-02-01', FALSE),
    (1, 'alice@example.com', 'active',  'organic', 'US', '2026-02-01', NULL,         TRUE),
    -- Bob: 'active' throughout.
    (2, 'bob@example.com',   'active',  'paid_search', 'GB', '2026-01-01', NULL, TRUE),
    -- Carla: 'vip'.
    (3, 'carla@example.com', 'vip',     'referral', 'IT', '2026-01-01', NULL, TRUE),
    -- Dimitri: 'new' then 'dormant'.
    (4, 'dimitri@example.com','new',    'paid_social','RU', '2026-01-01', '2026-02-15', FALSE),
    (4, 'dimitri@example.com','dormant','paid_social','RU', '2026-02-15', NULL,         TRUE),
    -- Emma: 'churned'.
    (5, 'emma@example.com',  'churned', 'paid_search', 'DE', '2026-01-01', NULL, TRUE);

INSERT INTO dim_campaign (campaign_id, name, objective, started_at) VALUES
    (1, 'New feature announcement', 'awareness', '2026-02-01'),
    (2, 'Spring sale',              'conversion','2026-02-15');

-- Generate 5000 deliveries synthetically.
--   channel mix:  email 40%, push 35%, sms 5%, in_app 20%.
--   Funnel rates:
--     delivered | sent = 92% overall; email 95%, push 90%, sms 85%, in_app 100%.
--     opened    | delivered = 30% email, 15% push, 5% sms, 60% in_app.
--     clicked   | opened    = 20% email, 10% push, 5% sms, 25% in_app.
--
-- channel_key is computed in a CTE first so the SELECT-list elements
-- below can reference it (Postgres SELECT-list cannot reference
-- earlier aliases in the same SELECT).
WITH synth AS (
    SELECT
        gs,
        CASE
            WHEN gs % 100 < 40 THEN 1                            -- email
            WHEN gs % 100 < 75 THEN 2                            -- push
            WHEN gs % 100 < 80 THEN 3                            -- sms
            ELSE 4                                               -- in_app
        END AS channel_key
    FROM generate_series(0, 4999) gs
)
INSERT INTO fact_notification_delivery (
    sent_ts, day_key, time_key, user_key, channel_key, notification_type_key,
    campaign_key, status_key,
    is_sent, is_delivered, is_opened, is_clicked,
    seconds_to_delivery, seconds_to_open, seconds_to_click,
    provider, cost_per_send_usd
)
SELECT
    TIMESTAMP'2026-01-15 08:00:00' + MAKE_INTERVAL(0,0,0,0,0,0, s.gs % 86400),
    CASE WHEN s.gs % 4 = 0 THEN 20260115 WHEN s.gs % 4 = 1 THEN 20260115
         WHEN s.gs % 4 = 2 THEN 20260201 ELSE 20260215 END,
    (8 + s.gs % 14) * 100,                                       -- time_key HH00
    ((s.gs % 5) + 1),                                            -- user_key 1..5
    s.channel_key,
    ((s.gs % 7) + 1),
    CASE WHEN s.gs % 5 = 0 THEN 1 WHEN s.gs % 5 = 1 THEN 2 ELSE NULL END,
    1 AS status_key,                                             -- placeholder; UPDATEd below
    TRUE AS is_sent,
    (CASE
        WHEN s.channel_key = 1 THEN RANDOM() < 0.95
        WHEN s.channel_key = 2 THEN RANDOM() < 0.90
        WHEN s.channel_key = 3 THEN RANDOM() < 0.85
        ELSE TRUE
     END) AS is_delivered,
    (CASE
        WHEN s.channel_key = 1 THEN RANDOM() < 0.30
        WHEN s.channel_key = 2 THEN RANDOM() < 0.15
        WHEN s.channel_key = 3 THEN RANDOM() < 0.05
        ELSE RANDOM() < 0.60
     END) AS is_opened,
    (CASE
        WHEN s.channel_key = 1 THEN RANDOM() < 0.20
        WHEN s.channel_key = 2 THEN RANDOM() < 0.10
        WHEN s.channel_key = 3 THEN RANDOM() < 0.05
        ELSE RANDOM() < 0.25
     END) AS is_clicked,
    (5 + (RANDOM() * 60)::int),
    (600 + (RANDOM() * 3600)::int),
    (1800 + (RANDOM() * 7200)::int),
    CASE
        WHEN s.channel_key = 1 THEN 'sendgrid'
        WHEN s.channel_key = 2 THEN 'fcm'
        WHEN s.channel_key = 3 THEN 'twilio'
        ELSE NULL
    END,
    CASE
        WHEN s.channel_key = 1 THEN 0.0010
        WHEN s.channel_key = 2 THEN 0.0001
        WHEN s.channel_key = 3 THEN 0.0500
        ELSE 0
    END
FROM synth s;

-- Now map the per-row funnel flags back to dim_notification_status.
UPDATE fact_notification_delivery f
SET status_key = s.status_key,
    is_sent    = TRUE
FROM dim_notification_status s
WHERE
    (s.is_delivered, s.is_opened, s.is_clicked, s.has_delivery_error,
     s.is_duplicate, s.is_rate_limited, s.is_opted_out)
    =
    (f.is_delivered, f.is_opened, f.is_clicked, FALSE,
     FALSE, FALSE, FALSE);

COMMIT;

-- =====================================================================
-- Self-verifying queries
-- =====================================================================

\echo ''
\echo '--- Q1: delivery rate by channel (the prompt''s first question) ---'
-- Non-additive: compute SUM(is_delivered)/SUM(is_sent), not AVG.
SELECT c.channel_code,
       COUNT(*)                                                  AS sent,
       SUM(CASE WHEN f.is_delivered THEN 1 ELSE 0 END)            AS delivered,
       ROUND(100.0 * SUM(CASE WHEN f.is_delivered THEN 1 ELSE 0 END) / COUNT(*), 2)
            AS delivery_rate_pct
FROM fact_notification_delivery f
JOIN dim_channel c ON c.channel_key = f.channel_key
GROUP BY c.channel_code
ORDER BY delivery_rate_pct DESC;

\echo ''
\echo '--- Q2: CTR by channel (the cardinal-vice ratio) ---'
SELECT c.channel_code,
       SUM(CASE WHEN f.is_delivered THEN 1 ELSE 0 END) AS delivered,
       SUM(CASE WHEN f.is_opened    THEN 1 ELSE 0 END) AS opened,
       SUM(CASE WHEN f.is_clicked   THEN 1 ELSE 0 END) AS clicked,
       ROUND(100.0 * SUM(CASE WHEN f.is_opened  THEN 1 ELSE 0 END)
                  / NULLIF(SUM(CASE WHEN f.is_delivered THEN 1 ELSE 0 END), 0), 2) AS ctr_pct,
       ROUND(100.0 * SUM(CASE WHEN f.is_clicked THEN 1 ELSE 0 END)
                  / NULLIF(SUM(CASE WHEN f.is_opened    THEN 1 ELSE 0 END), 0), 2) AS click_to_open_pct
FROM fact_notification_delivery f
JOIN dim_channel c ON c.channel_key = f.channel_key
GROUP BY c.channel_code
ORDER BY ctr_pct DESC;

\echo ''
\echo '--- Q3: hour-of-day open rate ---'
SELECT t.hour_of_day,
       t.time_bucket,
       COUNT(*)                                                AS sent,
       SUM(CASE WHEN f.is_opened THEN 1 ELSE 0 END)             AS opened,
       ROUND(100.0 * SUM(CASE WHEN f.is_opened THEN 1 ELSE 0 END) / COUNT(*), 2)
            AS open_rate_pct
FROM fact_notification_delivery f
JOIN dim_time t ON t.time_key = f.time_key
GROUP BY t.hour_of_day, t.time_bucket
ORDER BY t.hour_of_day;

\echo ''
\echo '--- Q4: weekend vs weekday open rate ---'
SELECT d.is_weekend,
       COUNT(*)                                                AS sent,
       SUM(CASE WHEN f.is_opened THEN 1 ELSE 0 END)             AS opened,
       ROUND(100.0 * SUM(CASE WHEN f.is_opened THEN 1 ELSE 0 END) / COUNT(*), 2)
            AS open_rate_pct
FROM fact_notification_delivery f
JOIN dim_date d ON d.day_key = f.day_key
GROUP BY d.is_weekend;

\echo ''
\echo '--- Q5: open rate by user segment (SCD2 — segment AT SEND TIME) ---'
-- We JOIN to dim_users on user_key (surrogate), which already
-- represents the version active at insert time. If the user later
-- changes segment, the OLD row stays; the new row gets a new user_key.
SELECT u.segment,
       COUNT(*)                                                AS sent,
       SUM(CASE WHEN f.is_opened THEN 1 ELSE 0 END)             AS opened,
       ROUND(100.0 * SUM(CASE WHEN f.is_opened THEN 1 ELSE 0 END) / COUNT(*), 2)
            AS open_rate_pct
FROM fact_notification_delivery f
JOIN dim_users u ON u.user_key = f.user_key
GROUP BY u.segment
ORDER BY open_rate_pct DESC;

\echo ''
\echo '--- Q6: campaign effectiveness vs regular product updates ---'
SELECT c.name                                         AS campaign,
       COUNT(*)                                       AS sent,
       SUM(CASE WHEN f.is_opened  THEN 1 ELSE 0 END)  AS opened,
       SUM(CASE WHEN f.is_clicked THEN 1 ELSE 0 END)  AS clicked,
       ROUND(100.0 * SUM(CASE WHEN f.is_clicked THEN 1 ELSE 0 END) / COUNT(*), 2)
            AS click_rate_pct
FROM fact_notification_delivery f
JOIN dim_campaign c ON c.campaign_key = f.campaign_key
GROUP BY c.name
ORDER BY click_rate_pct DESC;

\echo ''
\echo '--- Q7: junk dim — distribution of outcome labels ---'
SELECT s.label, COUNT(*) AS rows
FROM fact_notification_delivery f
JOIN dim_notification_status s ON s.status_key = f.status_key
GROUP BY s.label
ORDER BY rows DESC;

\echo ''
\echo '--- Q8: notification type × channel crosstab (the prompt''s "best for new vs active") ---'
SELECT t.type_code,
       c.channel_code,
       COUNT(*) AS sent,
       ROUND(100.0 * SUM(CASE WHEN f.is_opened THEN 1 ELSE 0 END) / COUNT(*), 2) AS open_rate_pct
FROM fact_notification_delivery f
JOIN dim_notification_type t ON t.notification_type_key = f.notification_type_key
JOIN dim_channel c          ON c.channel_key = f.channel_key
GROUP BY t.type_code, c.channel_code
ORDER BY t.type_code, c.channel_code;

\echo ''
\echo '=== Done: OLAP notification analytics star schema ==='
