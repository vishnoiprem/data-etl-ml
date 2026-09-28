-- =====================================================================
-- 07 — OLAP: Notification Delivery Analytics  (MySQL 8.0+ star)
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
--     TINYINT(1) flags rather than separate timestamp columns. This
--     makes "delivery rate" = SUM(is_delivered)/SUM(is_sent) — the
--     metric is always in the same place. NULL timestamps would force
--     analysts to COALESCE everywhere.
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
--
-- MySQL 8.0+ conversion notes:
--   * TIMESTAMPTZ  -> DATETIME  (UTC stored)
--   * JSONB -> JSON
--   * BOOLEAN -> TINYINT(1)
--   * TEXT -> VARCHAR (length) / TEXT for large bodies
--   * pgcrypto -> removed (not needed here)
--   * generate_series(0, N) -> recursive CTE
--   * TIMESTAMP '...' + MAKE_INTERVAL(0,0,0,0,0,0, sec) -> literal + INTERVAL sec SECOND
--   * FROM t1 UPDATE ... FROM t2 WHERE -> MySQL multi-table UPDATE syntax
--   * RANDOM() < x -> RAND() < x
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1) dim_date  (conformed)
-- ---------------------------------------------------------------------
CREATE TABLE dim_date (
    day_key        INT PRIMARY KEY,
    date_actual    DATE NOT NULL,
    day_of_week    SMALLINT NOT NULL,
    day_name       VARCHAR(12) NOT NULL,
    week_of_year   SMALLINT NOT NULL,
    month_of_year  SMALLINT NOT NULL,
    month_name     VARCHAR(12) NOT NULL,
    quarter        SMALLINT NOT NULL,
    year           SMALLINT NOT NULL,
    is_weekend     TINYINT(1) NOT NULL,
    is_holiday     TINYINT(1) NOT NULL DEFAULT 0,
    fiscal_quarter VARCHAR(16),
    UNIQUE KEY uq_dim_date_actual (date_actual)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 2) dim_time  (hour of day)
-- ---------------------------------------------------------------------
-- 24 rows. Lets "open rate by hour" be a simple star-join.
CREATE TABLE dim_time (
    time_key        INT PRIMARY KEY,                          -- HHMM (e.g. 0900)
    hour_of_day     SMALLINT NOT NULL,
    minute_of_hour  SMALLINT NOT NULL,
    is_business_hours TINYINT(1) NOT NULL,
    is_evening      TINYINT(1) NOT NULL,
    time_bucket     VARCHAR(16) NOT NULL,
    CONSTRAINT chk_dt_hour   CHECK (hour_of_day    BETWEEN 0 AND 23),
    CONSTRAINT chk_dt_minute CHECK (minute_of_hour BETWEEN 0 AND 59),
    CONSTRAINT chk_dt_bucket CHECK (time_bucket IN (
                       'overnight','morning','midday','afternoon','evening','late_night'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 24 rows seeded via recursive CTE (Postgres had generate_series).
INSERT INTO dim_time (time_key, hour_of_day, minute_of_hour, is_business_hours, is_evening, time_bucket)
WITH RECURSIVE hours AS (
    SELECT 0 AS h
    UNION ALL
    SELECT h + 1 FROM hours WHERE h < 23
)
SELECT
    h * 100,
    h,
    0,
    CASE WHEN h BETWEEN 9 AND 17 THEN 1 ELSE 0 END,
    CASE WHEN h BETWEEN 18 AND 22 THEN 1 ELSE 0 END,
    CASE
        WHEN h BETWEEN 0  AND 5  THEN 'overnight'
        WHEN h BETWEEN 6  AND 10 THEN 'morning'
        WHEN h BETWEEN 11 AND 13 THEN 'midday'
        WHEN h BETWEEN 14 AND 17 THEN 'afternoon'
        WHEN h BETWEEN 18 AND 22 THEN 'evening'
        ELSE 'late_night'
    END
FROM hours;

-- ---------------------------------------------------------------------
-- 3) dim_channel  (small dimension)
-- ---------------------------------------------------------------------
CREATE TABLE dim_channel (
    channel_key     BIGINT AUTO_INCREMENT PRIMARY KEY,
    channel_code    VARCHAR(16) NOT NULL,                     -- 'email','push','sms','in_app'
    surface         VARCHAR(16) NOT NULL,                     -- 'mobile','desktop','email','sms'
    description     VARCHAR(255),
    UNIQUE KEY uq_dim_channel_code (channel_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
    notification_type_key  BIGINT AUTO_INCREMENT PRIMARY KEY,
    type_code              VARCHAR(64) NOT NULL,
    category               VARCHAR(32) NOT NULL,
    description            VARCHAR(255),
    UNIQUE KEY uq_dim_nt_code (type_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
    user_key           BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id            BIGINT NOT NULL,
    email              VARCHAR(254),
    segment            VARCHAR(16) NOT NULL,
    acquisition_channel VARCHAR(32),
    country            CHAR(2),
    valid_from         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_to           DATETIME,
    is_current         TINYINT(1) NOT NULL DEFAULT 1,
    created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_dim_users_segment CHECK (segment IN ('new','active','dormant','vip','churned'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_dim_user_natural ON dim_users(user_id, is_current);

-- ---------------------------------------------------------------------
-- 6) dim_campaign  (SCD-lite; campaigns are short-lived enough for type 1)
-- ---------------------------------------------------------------------
CREATE TABLE dim_campaign (
    campaign_key       BIGINT AUTO_INCREMENT PRIMARY KEY,
    campaign_id        BIGINT NOT NULL,
    name               VARCHAR(255) NOT NULL,
    objective          VARCHAR(32),
    started_at         DATETIME,
    ended_at           DATETIME,
    is_active          TINYINT(1) NOT NULL DEFAULT 1,
    UNIQUE KEY uq_dim_campaign (campaign_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 7) dim_notification_status  (JUNK DIMENSION)
-- ---------------------------------------------------------------------
-- Combining low-cardinality flags into ONE dimension is the standard
-- junk-dim pattern. 2^4 = 16 max rows; we actually populate the 8 most
-- common combinations. Analysts "GROUP BY status_key" and read the
-- semantics from one row of dim_notification_status.
CREATE TABLE dim_notification_status (
    status_key             BIGINT AUTO_INCREMENT PRIMARY KEY,
    is_delivered           TINYINT(1) NOT NULL,
    is_opened              TINYINT(1) NOT NULL,
    is_clicked             TINYINT(1) NOT NULL,
    has_delivery_error     TINYINT(1) NOT NULL,
    is_duplicate           TINYINT(1) NOT NULL,
    is_rate_limited        TINYINT(1) NOT NULL,
    is_opted_out           TINYINT(1) NOT NULL,
    label                  VARCHAR(32) NOT NULL,
    UNIQUE KEY uq_dim_status (is_delivered, is_opened, is_clicked, has_delivery_error,
                              is_duplicate, is_rate_limited, is_opted_out)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO dim_notification_status
    (is_delivered, is_opened, is_clicked, has_delivery_error, is_duplicate, is_rate_limited, is_opted_out, label) VALUES
    (1,  1,  1,  0, 0, 0, 0, 'engaged_full'),
    (1,  1,  0,  0, 0, 0, 0, 'engaged_open'),
    (1,  0,  0,  0, 0, 0, 0, 'sent_silent'),
    (0,  0,  0,  1, 0, 0, 0, 'failed_bounce'),
    (0,  0,  0,  1, 0, 1, 0, 'failed_rate_limited'),
    (0,  0,  0,  0, 0, 0, 1, 'suppressed_optout'),
    (1,  0,  0,  0, 1, 0, 0, 'duplicate_resend'),
    (0,  0,  0,  0, 0, 0, 0, 'pending_send');

-- ---------------------------------------------------------------------
-- 8) fact_notification_delivery
-- ---------------------------------------------------------------------
-- Grain = one row per (notification, user, channel) attempt.
-- Funnel flags are the heart of the fact — every metric derives from
-- a ratio of these.
CREATE TABLE fact_notification_delivery (
    delivery_id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    sent_ts               DATETIME NOT NULL,
    day_key               INT  NOT NULL,
    time_key              INT  NOT NULL,
    user_key              BIGINT NOT NULL,
    channel_key           BIGINT NOT NULL,
    notification_type_key BIGINT NOT NULL,
    campaign_key          BIGINT,
    status_key            BIGINT NOT NULL,
    -- Funnel flags (denormalised mirror of status_key; makes any
    -- query that filters by flag use a partial index without a join).
    is_sent               TINYINT(1) NOT NULL DEFAULT 0,
    is_delivered          TINYINT(1) NOT NULL DEFAULT 0,
    is_opened             TINYINT(1) NOT NULL DEFAULT 0,
    is_clicked            TINYINT(1) NOT NULL DEFAULT 0,
    -- Latencies in seconds, NULL until the next stage happens.
    seconds_to_delivery   INT,
    seconds_to_open       INT,
    seconds_to_click      INT,
    -- Provider info — kept at delivery grain.
    provider              VARCHAR(32),
    cost_per_send_usd     DECIMAL(8,4),
    CONSTRAINT fk_fnd_date    FOREIGN KEY (day_key)               REFERENCES dim_date(day_key),
    CONSTRAINT fk_fnd_time    FOREIGN KEY (time_key)              REFERENCES dim_time(time_key),
    CONSTRAINT fk_fnd_user    FOREIGN KEY (user_key)              REFERENCES dim_users(user_key),
    CONSTRAINT fk_fnd_channel FOREIGN KEY (channel_key)           REFERENCES dim_channel(channel_key),
    CONSTRAINT fk_fnd_type    FOREIGN KEY (notification_type_key) REFERENCES dim_notification_type(notification_type_key),
    CONSTRAINT fk_fnd_camp    FOREIGN KEY (campaign_key)          REFERENCES dim_campaign(campaign_key),
    CONSTRAINT fk_fnd_status  FOREIGN KEY (status_key)            REFERENCES dim_notification_status(status_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Star-join probes by day, channel, type are the common access path.
CREATE INDEX idx_fact_notif_day_channel ON fact_notification_delivery(day_key, channel_key);
CREATE INDEX idx_fact_notif_day_type    ON fact_notification_delivery(day_key, notification_type_key);
CREATE INDEX idx_fact_notif_user_day    ON fact_notification_delivery(user_key, day_key);

-- =====================================================================
-- Sample data — ~5000 deliveries across 4 channels, 5 users, 7 types.
-- =====================================================================

INSERT INTO dim_date (day_key, date_actual, day_of_week, day_name, week_of_year,
                      month_of_year, month_name, quarter, year, is_weekend, fiscal_quarter) VALUES
    (20260101, '2026-01-01', 4, 'Thursday', 1, 1, 'January',  1, 2026, 0, 'FY26-Q3'),
    (20260115, '2026-01-15', 4, 'Thursday', 3, 1, 'January',  1, 2026, 0, 'FY26-Q3'),
    (20260201, '2026-02-01', 7, 'Sunday',   5, 2, 'February', 1, 2026, 1, 'FY26-Q4'),
    (20260215, '2026-02-15', 7, 'Sunday',   7, 2, 'February', 1, 2026, 1, 'FY26-Q4');

INSERT INTO dim_users (user_id, email, segment, acquisition_channel, country, valid_from, valid_to, is_current) VALUES
    -- Alice: 'new' Jan, 'active' Feb.
    (1, 'alice@example.com', 'new',     'organic',      'US', '2026-01-01', '2026-02-01', 0),
    (1, 'alice@example.com', 'active',  'organic',      'US', '2026-02-01', NULL,         1),
    -- Bob: 'active' throughout.
    (2, 'bob@example.com',   'active',  'paid_search',  'GB', '2026-01-01', NULL,         1),
    -- Carla: 'vip'.
    (3, 'carla@example.com', 'vip',     'referral',     'IT', '2026-01-01', NULL,         1),
    -- Dimitri: 'new' then 'dormant'.
    (4, 'dimitri@example.com','new',    'paid_social',  'RU', '2026-01-01', '2026-02-15', 0),
    (4, 'dimitri@example.com','dormant','paid_social', 'RU', '2026-02-15', NULL,         1),
    -- Emma: 'churned'.
    (5, 'emma@example.com',  'churned', 'paid_search',  'DE', '2026-01-01', NULL,         1);

INSERT INTO dim_campaign (campaign_id, name, objective, started_at) VALUES
    (1, 'New feature announcement', 'awareness',  '2026-02-01'),
    (2, 'Spring sale',              'conversion', '2026-02-15');

-- Generate 5000 deliveries synthetically.
--   channel mix:  email 40%, push 35%, sms 5%, in_app 20%.
--   Funnel rates:
--     delivered | sent = 92% overall; email 95%, push 90%, sms 85%, in_app 100%.
--     opened    | delivered = 30% email, 15% push, 5% sms, 60% in_app.
--     clicked   | opened    = 20% email, 10% push, 5% sms, 25% in_app.
--
-- channel_key is computed in a CTE first so the SELECT-list elements
-- below can reference it (MySQL SELECT-list cannot reference earlier
-- aliases in the same SELECT).
INSERT INTO fact_notification_delivery (
    sent_ts, day_key, time_key, user_key, channel_key, notification_type_key,
    campaign_key, status_key,
    is_sent, is_delivered, is_opened, is_clicked,
    seconds_to_delivery, seconds_to_open, seconds_to_click,
    provider, cost_per_send_usd
)
WITH RECURSIVE nums AS (
    SELECT 0 AS gs
    UNION ALL
    SELECT gs + 1 FROM nums WHERE gs < 4999
),
synth AS (
    SELECT
        gs,
        CASE
            WHEN gs % 100 < 40 THEN 1                            -- email
            WHEN gs % 100 < 75 THEN 2                            -- push
            WHEN gs % 100 < 80 THEN 3                            -- sms
            ELSE 4                                               -- in_app
        END AS channel_key
    FROM nums
)
SELECT
    TIMESTAMP('2026-01-15 08:00:00') + INTERVAL (s.gs % 86400) SECOND,
    CASE
        WHEN s.gs % 4 = 0 THEN 20260115
        WHEN s.gs % 4 = 1 THEN 20260115
        WHEN s.gs % 4 = 2 THEN 20260201
        ELSE 20260215
    END,
    (8 + s.gs % 14) * 100,                                       -- time_key HH00
    ((s.gs % 5) + 1),                                            -- user_key 1..5
    s.channel_key,
    ((s.gs % 7) + 1),
    CASE
        WHEN s.gs % 5 = 0 THEN 1
        WHEN s.gs % 5 = 1 THEN 2
        ELSE NULL
    END,
    1 AS status_key,                                             -- placeholder; UPDATEd below
    1 AS is_sent,
    CASE
        WHEN s.channel_key = 1 THEN RAND() < 0.95
        WHEN s.channel_key = 2 THEN RAND() < 0.90
        WHEN s.channel_key = 3 THEN RAND() < 0.85
        ELSE 1
    END AS is_delivered,
    CASE
        WHEN s.channel_key = 1 THEN RAND() < 0.30
        WHEN s.channel_key = 2 THEN RAND() < 0.15
        WHEN s.channel_key = 3 THEN RAND() < 0.05
        ELSE RAND() < 0.60
    END AS is_opened,
    CASE
        WHEN s.channel_key = 1 THEN RAND() < 0.20
        WHEN s.channel_key = 2 THEN RAND() < 0.10
        WHEN s.channel_key = 3 THEN RAND() < 0.05
        ELSE RAND() < 0.25
    END AS is_clicked,
    (5  + FLOOR(RAND() * 60)),
    (600  + FLOOR(RAND() * 3600)),
    (1800 + FLOOR(RAND() * 7200)),
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
-- Postgres: UPDATE ... SET ... FROM <other_table> WHERE <row-equals-row>
-- MySQL:     UPDATE <target> JOIN <other_table> ON <same-predicate>
--            SET <assignments>
UPDATE fact_notification_delivery f
JOIN dim_notification_status s
    ON s.is_delivered       = f.is_delivered
   AND s.is_opened          = f.is_opened
   AND s.is_clicked         = f.is_clicked
   AND s.has_delivery_error = 0
   AND s.is_duplicate       = 0
   AND s.is_rate_limited    = 0
   AND s.is_opted_out       = 0
SET f.status_key = s.status_key,
    f.is_sent    = 1;

-- =====================================================================
-- Self-verifying queries
-- =====================================================================

-- Q1: delivery rate by channel (the prompt's first question).
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

-- Q2: CTR by channel (the cardinal-vice ratio).
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

-- Q3: hour-of-day open rate.
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

-- Q4: weekend vs weekday open rate.
SELECT d.is_weekend,
       COUNT(*)                                                AS sent,
       SUM(CASE WHEN f.is_opened THEN 1 ELSE 0 END)             AS opened,
       ROUND(100.0 * SUM(CASE WHEN f.is_opened THEN 1 ELSE 0 END) / COUNT(*), 2)
            AS open_rate_pct
FROM fact_notification_delivery f
JOIN dim_date d ON d.day_key = f.day_key
GROUP BY d.is_weekend;

-- Q5: open rate by user segment (SCD2 — segment AT SEND TIME).
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

-- Q6: campaign effectiveness vs regular product updates.
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

-- Q7: junk dim — distribution of outcome labels.
SELECT s.label, COUNT(*) AS rows
FROM fact_notification_delivery f
JOIN dim_notification_status s ON s.status_key = f.status_key
GROUP BY s.label
ORDER BY rows DESC;

-- Q8: notification type × channel crosstab (the prompt's "best for new vs active").
SELECT t.type_code,
       c.channel_code,
       COUNT(*) AS sent,
       ROUND(100.0 * SUM(CASE WHEN f.is_opened THEN 1 ELSE 0 END) / COUNT(*), 2) AS open_rate_pct
FROM fact_notification_delivery f
JOIN dim_notification_type t ON t.notification_type_key = f.notification_type_key
JOIN dim_channel c          ON c.channel_key = f.channel_key
GROUP BY t.type_code, c.channel_code
ORDER BY t.type_code, c.channel_code;

-- Done: OLAP notification analytics star schema (MySQL 8.0+, all timestamps UTC)
