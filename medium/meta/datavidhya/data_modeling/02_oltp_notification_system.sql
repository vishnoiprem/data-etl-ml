-- =====================================================================
-- 02 — OLTP: Multi-Channel Notification System (MySQL 8.0+)
-- =====================================================================
-- Domain: an app that sends notifications to users across multiple
-- channels (email, push, SMS, in-app), triggered either by an event
-- (e.g. "you got a new follower") or on a schedule (e.g. "weekly
-- digest every Monday at 9am").
--
-- Design notes:
-- 1) notifications vs notification_deliveries are SPLIT.
--    A notification is the *intent* — "tell user 42 their order shipped".
--    A delivery is the *attempt* on a channel. One notification fans out
--    to N deliveries (email + push + SMS). Each delivery has its own
--    state (queued, sent, delivered, opened, clicked, failed).
--
-- 2) templates are first-class. Hard-coding notification copy in
--    application code is a rookie mistake — it kills i18n, A/B testing,
--    and audit trails.
--
-- 3) user_notification_preferences is per-channel AND per-category.
--    Users opt out of "marketing email" but want "transactional SMS".
--
-- 4) notification_events is an append-only audit log. Every state
--    transition lands here. Useful for debugging delivery issues,
--    computing funnel metrics, and replay.
--
-- 5) Soft delete (deleted_at) everywhere. Hard-deleting a delivery row
--    destroys billing reconciliation.
--
-- Time handling: ALL timestamps are stored in UTC (DATETIME, NOT NULL).
-- The `timezone` column on users is the user's PREFERRED display zone
-- (IANA name) for rendering — it never affects storage or comparison.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1) users
-- ---------------------------------------------------------------------
CREATE TABLE users (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    email         VARCHAR(254) NOT NULL,
    phone_e164    VARCHAR(20),                      -- E.164 format, e.g. +447700900123
    locale        VARCHAR(10) NOT NULL DEFAULT 'en_GB',
    timezone      VARCHAR(64) NOT NULL DEFAULT 'UTC',  -- user's PREFERRED display zone
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at    DATETIME,
    UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_users_phone    ON users(phone_e164);
CREATE INDEX idx_users_created  ON users(created_at);

-- ---------------------------------------------------------------------
-- 2) notification_templates
-- ---------------------------------------------------------------------
CREATE TABLE notification_templates (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    code            VARCHAR(64) NOT NULL,            -- e.g. 'order.shipped', 'weekly.digest'
    channel         VARCHAR(16) NOT NULL,
    locale          VARCHAR(10) NOT NULL DEFAULT 'en_GB',
    subject         VARCHAR(255),                   -- NULL for push/SMS
    body            TEXT NOT NULL,                   -- may contain {{placeholders}}
    version         INT  NOT NULL DEFAULT 1,
    is_active       TINYINT(1) NOT NULL DEFAULT 1,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_template_code_locale_channel (code, locale, channel),
    CONSTRAINT chk_template_channel CHECK (channel IN ('email','push','sms','in_app'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_templates_code  ON notification_templates(code);

-- ---------------------------------------------------------------------
-- 3) user_notification_preferences
-- ---------------------------------------------------------------------
CREATE TABLE user_notification_preferences (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    category        VARCHAR(16) NOT NULL,
    channel         VARCHAR(16) NOT NULL,
    is_enabled      TINYINT(1) NOT NULL DEFAULT 1,
    quiet_hours_start TIME,                         -- e.g. 22:00 (user's local time)
    quiet_hours_end   TIME,                         -- e.g. 07:00
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_pref_user_cat_chan (user_id, category, channel),
    CONSTRAINT fk_prefs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_pref_category CHECK (category IN ('transactional','marketing','social','digest','security')),
    CONSTRAINT chk_pref_channel  CHECK (channel  IN ('email','push','sms','in_app'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_prefs_user ON user_notification_preferences(user_id);

-- ---------------------------------------------------------------------
-- 4) notifications (the intent)
-- ---------------------------------------------------------------------
CREATE TABLE notifications (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    template_id     BIGINT,
    category        VARCHAR(16) NOT NULL,
    priority        SMALLINT NOT NULL DEFAULT 5,
    payload         JSON NOT NULL,                  -- variables for template rendering
    trigger_type    VARCHAR(16) NOT NULL,
    scheduled_for   DATETIME,                       -- when the worker should pick it up
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    delivered_at    DATETIME,                       -- populated when last delivery succeeds
    read_at         DATETIME,                       -- populated when user opens (in-app)
    deleted_at      DATETIME,
    CONSTRAINT fk_notif_user     FOREIGN KEY (user_id)     REFERENCES users(id)                     ON DELETE CASCADE,
    CONSTRAINT fk_notif_template FOREIGN KEY (template_id) REFERENCES notification_templates(id)   ON DELETE SET NULL,
    CONSTRAINT chk_notif_category    CHECK (category     IN ('transactional','marketing','social','digest','security')),
    CONSTRAINT chk_notif_priority    CHECK (priority BETWEEN 1 AND 10),
    CONSTRAINT chk_notif_trigger     CHECK (trigger_type IN ('event','scheduled','manual'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_notif_user_created   ON notifications(user_id, created_at);
CREATE INDEX idx_notif_scheduled     ON notifications(scheduled_for);
CREATE INDEX idx_notif_template      ON notifications(template_id);
CREATE INDEX idx_notif_unread        ON notifications(user_id, read_at);

-- ---------------------------------------------------------------------
-- 5) notification_deliveries (the per-channel attempts)
-- ---------------------------------------------------------------------
CREATE TABLE notification_deliveries (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
    notification_id     BIGINT NOT NULL,
    channel             VARCHAR(16) NOT NULL,
    status              VARCHAR(16) NOT NULL,
    provider            VARCHAR(32),                 -- 'sendgrid', 'fcm', 'twilio', 'apns'
    provider_message_id VARCHAR(128),                -- external ID for tracing
    attempt_count       SMALLINT NOT NULL DEFAULT 0,
    last_error          TEXT,
    queued_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_at             DATETIME,
    delivered_at        DATETIME,
    opened_at           DATETIME,
    clicked_at          DATETIME,
    failed_at           DATETIME,
    deleted_at          DATETIME,
    CONSTRAINT fk_deliv_notif FOREIGN KEY (notification_id) REFERENCES notifications(id) ON DELETE CASCADE,
    CONSTRAINT chk_deliv_channel CHECK (channel IN ('email','push','sms','in_app')),
    CONSTRAINT chk_deliv_status  CHECK (status  IN ('queued','sent','delivered','failed','bounced','opened','clicked'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_deliveries_notif       ON notification_deliveries(notification_id);
CREATE INDEX idx_deliveries_channel     ON notification_deliveries(channel, status);
CREATE INDEX idx_deliveries_status      ON notification_deliveries(status);
CREATE INDEX idx_deliveries_provider_id ON notification_deliveries(provider_message_id);

-- ---------------------------------------------------------------------
-- 6) notification_events (append-only audit log)
-- ---------------------------------------------------------------------
CREATE TABLE notification_events (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    notification_id BIGINT NOT NULL,
    delivery_id     BIGINT,
    event_type      VARCHAR(32) NOT NULL,
    payload         JSON NOT NULL,
    occurred_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_event_notif    FOREIGN KEY (notification_id) REFERENCES notifications(id)            ON DELETE CASCADE,
    CONSTRAINT fk_event_delivery FOREIGN KEY (delivery_id)     REFERENCES notification_deliveries(id) ON DELETE SET NULL,
    CONSTRAINT chk_event_type CHECK (event_type IN (
        'created','queued','sent','delivered','opened','clicked',
        'failed','bounced','opted_out','rate_limited'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_events_notif      ON notification_events(notification_id, occurred_at);
CREATE INDEX idx_events_delivery   ON notification_events(delivery_id, occurred_at);
CREATE INDEX idx_events_type_time  ON notification_events(event_type, occurred_at);

-- =====================================================================
-- Sample data
-- =====================================================================
-- All timestamps below are in UTC. CURRENT_TIMESTAMP returns UTC by
-- convention; do NOT use NOW() if your server is in a non-UTC zone —
-- use UTC_TIMESTAMP() instead. All DATE_SUB/INTERVAL math is in UTC.

INSERT INTO users (email, phone_e164, locale, timezone) VALUES
    ('alice.wong@example.com',   '+447700900101', 'en_GB', 'Europe/London'),
    ('bob.singh@example.com',    '+14155550101',  'en_US', 'America/Los_Angeles'),
    ('carla.rossi@example.com',  '+393331234567', 'it_IT', 'Europe/Rome'),
    ('dimitri.ivanov@example.com','+79161234567','ru_RU', 'Europe/Moscow'),
    ('emma.mueller@example.com', '+4915112345678','de_DE', 'Europe/Berlin'),
    ('fatima.ali@example.com',   '+971501234567', 'ar_AE', 'Asia/Dubai'),
    ('grace.kim@example.com',    '+821012345678', 'ko_KR', 'Asia/Seoul'),
    ('hiro.tanaka@example.com',  '+819012345678', 'ja_JP', 'Asia/Tokyo'),
    ('isabel.garcia@example.com','+34612345678',  'es_ES', 'Europe/Madrid'),
    ('james.obrien@example.com', '+353851234567', 'en_IE', 'Europe/Dublin');

INSERT INTO notification_templates (code, channel, locale, subject, body, version) VALUES
    ('order.shipped',  'email',  'en_GB', 'Your order #{{order_id}} has shipped',  'Hi {{name}}, your order is on its way. Track at {{url}}.', 1),
    ('order.shipped',  'push',   'en_GB', NULL,                                    'Your order #{{order_id}} has shipped', 1),
    ('weekly.digest',  'email',  'en_GB', 'Your weekly digest',                    'Here are the top {{count}} stories for you, {{name}}.', 1),
    ('new_follower',   'push',   'en_GB', NULL,                                    '{{follower_name}} started following you', 1),
    ('security.alert', 'email',  'en_GB', 'Security alert: new sign-in',           'We detected a new sign-in from {{location}}.', 1),
    ('security.alert', 'sms',    'en_GB', NULL,                                    'Security alert: new sign-in from {{location}}. Reply NO if this wasnt you.', 1),
    ('cart.reminder',  'email',  'en_GB', 'You left items in your cart',           '{{name}}, you have {{item_count}} items waiting.', 1),
    ('comment.reply',  'in_app', 'en_GB', NULL,                                    '{{replier_name}} replied to your comment.', 1),
    ('comment.reply',  'push',   'en_GB', NULL,                                    '{{replier_name}} replied: "{{snippet}}"', 1),
    ('payment.failed', 'email',  'en_GB', 'Action required: payment failed',       'We could not process your payment for order #{{order_id}}.', 1);

INSERT INTO user_notification_preferences (user_id, category, channel, is_enabled) VALUES
    (1, 'transactional', 'email', 1),  (1, 'transactional', 'sms',    1),  (1, 'marketing', 'email', 0),
    (2, 'transactional', 'email', 1),  (2, 'transactional', 'push',   1),  (2, 'marketing', 'email', 0),
    (3, 'transactional', 'email', 1),  (3, 'transactional', 'sms',    0),  (3, 'digest',    'email', 1),
    (4, 'transactional', 'email', 1),  (4, 'transactional', 'push',   1),  (4, 'marketing', 'email', 1),
    (5, 'transactional', 'email', 1),  (5, 'transactional', 'sms',    1),  (5, 'social',    'push',  1),
    (6, 'transactional', 'email', 1),  (6, 'transactional', 'sms',    1),  (6, 'marketing', 'email', 0),
    (7, 'transactional', 'email', 1),  (7, 'transactional', 'push',   1),  (7, 'digest',    'email', 1),
    (8, 'transactional', 'email', 1),  (8, 'transactional', 'push',   1),  (8, 'marketing', 'email', 0),
    (9, 'transactional', 'email', 1),  (9, 'transactional', 'sms',    1),  (9, 'social',    'push',  1),
    (10,'transactional', 'email', 1),  (10,'transactional', 'sms',    1),  (10,'marketing', 'email', 1);

INSERT INTO notifications (user_id, template_id, category, priority, payload, trigger_type, scheduled_for, created_at) VALUES
    (1, 1, 'transactional', 9, JSON_OBJECT('order_id','A1042','name','Alice','url','https://ex.com/t/A1042'),         'event',     NULL,                    DATE_SUB(UTC_TIMESTAMP(), INTERVAL 2 DAY)),
    (1, 2, 'transactional', 9, JSON_OBJECT('order_id','A1042'),                                                       'event',     NULL,                    DATE_SUB(UTC_TIMESTAMP(), INTERVAL 2 DAY)),
    (2, 4, 'social',        5, JSON_OBJECT('follower_name','Carla'),                                                  'event',     NULL,                    DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 DAY)),
    (3, 3, 'digest',        3, JSON_OBJECT('name','Carla','count',5),                                                 'scheduled', DATE_SUB(UTC_TIMESTAMP(), INTERVAL 3 DAY), DATE_SUB(UTC_TIMESTAMP(), INTERVAL 4 DAY)),
    (4, 5, 'security',     10, JSON_OBJECT('location','Moscow, RU'),                                                 'event',     NULL,                    DATE_SUB(UTC_TIMESTAMP(), INTERVAL 12 HOUR)),
    (4, 6, 'security',     10, JSON_OBJECT('location','Moscow, RU'),                                                 'event',     NULL,                    DATE_SUB(UTC_TIMESTAMP(), INTERVAL 12 HOUR)),
    (5, 7, 'marketing',     3, JSON_OBJECT('name','Emma','item_count',3),                                            'event',     NULL,                    DATE_SUB(UTC_TIMESTAMP(), INTERVAL 6 HOUR)),
    (6, 10,'transactional', 9, JSON_OBJECT('order_id','A1077'),                                                       'event',     NULL,                    DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 HOUR)),
    (7, 8, 'social',        5, JSON_OBJECT('replier_name','Hiro'),                                                    'event',     NULL,                    DATE_SUB(UTC_TIMESTAMP(), INTERVAL 30 MINUTE)),
    (7, 9, 'social',        5, JSON_OBJECT('replier_name','Hiro','snippet','totally agree'),                         'event',     NULL,                    DATE_SUB(UTC_TIMESTAMP(), INTERVAL 30 MINUTE)),
    (8, 3, 'digest',        3, JSON_OBJECT('name','Hiro','count',7),                                                  'scheduled', DATE_SUB(UTC_TIMESTAMP(), INTERVAL 2 DAY), DATE_SUB(UTC_TIMESTAMP(), INTERVAL 3 DAY)),
    (9, 4, 'social',        5, JSON_OBJECT('follower_name','James'),                                                 'event',     NULL,                    DATE_SUB(UTC_TIMESTAMP(), INTERVAL 15 MINUTE)),
    (10,5, 'security',     10, JSON_OBJECT('location','Dublin, IE'),                                                 'event',     NULL,                    DATE_SUB(UTC_TIMESTAMP(), INTERVAL 5 MINUTE)),
    (10,6, 'security',     10, JSON_OBJECT('location','Dublin, IE'),                                                 'event',     NULL,                    DATE_SUB(UTC_TIMESTAMP(), INTERVAL 5 MINUTE)),
    (1, 3, 'digest',        3, JSON_OBJECT('name','Alice','count',4),                                                 'scheduled', DATE_ADD(UTC_TIMESTAMP(), INTERVAL 5 DAY),  UTC_TIMESTAMP());

INSERT INTO notification_deliveries (notification_id, channel, status, provider, attempt_count, queued_at, sent_at, delivered_at, opened_at) VALUES
    (1,  'email', 'opened',   'sendgrid', 1, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 2 DAY), DATE_SUB(UTC_TIMESTAMP(), INTERVAL 2 DAY) + INTERVAL 5 SECOND,  DATE_SUB(UTC_TIMESTAMP(), INTERVAL 2 DAY) + INTERVAL 30 SECOND, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 DAY)),
    (1,  'push',  'delivered','fcm',      1, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 2 DAY), DATE_SUB(UTC_TIMESTAMP(), INTERVAL 2 DAY) + INTERVAL 2 SECOND,  DATE_SUB(UTC_TIMESTAMP(), INTERVAL 2 DAY) + INTERVAL 10 SECOND, NULL),
    (2,  'push',  'opened',   'fcm',      1, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 DAY), DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 DAY) + INTERVAL 2 SECOND,  DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 DAY) + INTERVAL 8 SECOND,  DATE_SUB(UTC_TIMESTAMP(), INTERVAL 20 HOUR)),
    (3,  'email', 'delivered','sendgrid', 1, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 3 DAY), DATE_SUB(UTC_TIMESTAMP(), INTERVAL 3 DAY) + INTERVAL 4 SECOND,  DATE_SUB(UTC_TIMESTAMP(), INTERVAL 3 DAY) + INTERVAL 40 SECOND, NULL),
    (3,  'push',  'failed',   'fcm',      2, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 3 DAY), DATE_SUB(UTC_TIMESTAMP(), INTERVAL 3 DAY) + INTERVAL 2 SECOND,  NULL, NULL),
    (4,  'email', 'opened',   'sendgrid', 1, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 12 HOUR), DATE_SUB(UTC_TIMESTAMP(), INTERVAL 12 HOUR) + INTERVAL 3 SECOND, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 12 HOUR) + INTERVAL 20 SECOND, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 11 HOUR)),
    (4,  'sms',   'delivered','twilio',   1, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 12 HOUR), DATE_SUB(UTC_TIMESTAMP(), INTERVAL 12 HOUR) + INTERVAL 5 SECOND, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 12 HOUR) + INTERVAL 15 SECOND, NULL),
    (5,  'email', 'clicked',  'sendgrid', 1, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 6 HOUR),  DATE_SUB(UTC_TIMESTAMP(), INTERVAL 6 HOUR) + INTERVAL 4 SECOND,  DATE_SUB(UTC_TIMESTAMP(), INTERVAL 6 HOUR) + INTERVAL 25 SECOND, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 5 HOUR)),
    (6,  'email', 'failed',   'sendgrid', 3, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 HOUR),  DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 HOUR) + INTERVAL 2 SECOND,  NULL, NULL),
    (7,  'in_app','opened',   NULL,       0, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 30 MINUTE), NULL, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 30 MINUTE), DATE_SUB(UTC_TIMESTAMP(), INTERVAL 25 MINUTE)),
    (7,  'push',  'delivered','apns',     1, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 30 MINUTE), DATE_SUB(UTC_TIMESTAMP(), INTERVAL 30 MINUTE) + INTERVAL 3 SECOND, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 30 MINUTE) + INTERVAL 12 SECOND, NULL),
    (8,  'push',  'opened',   'fcm',      1, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 15 MINUTE), DATE_SUB(UTC_TIMESTAMP(), INTERVAL 15 MINUTE) + INTERVAL 2 SECOND, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 15 MINUTE) + INTERVAL 7 SECOND,  DATE_SUB(UTC_TIMESTAMP(), INTERVAL 10 MINUTE)),
    (9,  'email', 'opened',   'sendgrid', 1, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 12 HOUR), DATE_SUB(UTC_TIMESTAMP(), INTERVAL 12 HOUR) + INTERVAL 3 SECOND, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 12 HOUR) + INTERVAL 18 SECOND, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 11 HOUR)),
    (9,  'sms',   'delivered','twilio',   1, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 12 HOUR), DATE_SUB(UTC_TIMESTAMP(), INTERVAL 12 HOUR) + INTERVAL 5 SECOND, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 12 HOUR) + INTERVAL 13 SECOND, NULL),
    (10, 'email', 'queued',   'sendgrid', 0, DATE_ADD(UTC_TIMESTAMP(), INTERVAL 5 DAY),  NULL, NULL, NULL);

INSERT INTO notification_events (notification_id, delivery_id, event_type, occurred_at) VALUES
    (1, 1, 'created',     DATE_SUB(UTC_TIMESTAMP(), INTERVAL 2 DAY)),
    (1, 1, 'queued',      DATE_SUB(UTC_TIMESTAMP(), INTERVAL 2 DAY) + INTERVAL 1 SECOND),
    (1, 1, 'sent',        DATE_SUB(UTC_TIMESTAMP(), INTERVAL 2 DAY) + INTERVAL 5 SECOND),
    (1, 1, 'delivered',   DATE_SUB(UTC_TIMESTAMP(), INTERVAL 2 DAY) + INTERVAL 30 SECOND),
    (1, 1, 'opened',      DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 DAY)),
    (3, 3, 'failed',      DATE_SUB(UTC_TIMESTAMP(), INTERVAL 3 DAY) + INTERVAL 2 SECOND),
    (4, 5, 'sent',        DATE_SUB(UTC_TIMESTAMP(), INTERVAL 12 HOUR)),
    (4, 5, 'opened',      DATE_SUB(UTC_TIMESTAMP(), INTERVAL 11 HOUR)),
    (6, 9, 'failed',      DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 HOUR)),
    (6, 9, 'rate_limited',DATE_SUB(UTC_TIMESTAMP(), INTERVAL 50 MINUTE)),
    (10,15,'queued',      DATE_ADD(UTC_TIMESTAMP(), INTERVAL 5 DAY));

-- =====================================================================
-- Example queries
-- =====================================================================

-- Q1: Delivery rate per channel (last 7 days)
-- Business question: which channel delivers successfully most often?
SELECT
    d.channel,
    COUNT(*)                                                  AS total_attempts,
    SUM(CASE WHEN d.status IN ('delivered','opened','clicked') THEN 1 ELSE 0 END) AS successful,
    ROUND(
        100.0 * SUM(CASE WHEN d.status IN ('delivered','opened','clicked') THEN 1 ELSE 0 END)
              / NULLIF(COUNT(*), 0),
        2
    ) AS delivery_rate_pct
FROM notification_deliveries d
WHERE d.queued_at >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY d.channel
ORDER BY delivery_rate_pct DESC;

-- Q2: Opt-out rate by category
-- Business question: what fraction of users have disabled each channel-category combo?
SELECT
    p.category,
    p.channel,
    COUNT(*) AS total_prefs,
    SUM(CASE WHEN p.is_enabled = 0 THEN 1 ELSE 0 END) AS opted_out,
    ROUND(100.0 * SUM(CASE WHEN p.is_enabled = 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS opt_out_pct
FROM user_notification_preferences p
GROUP BY p.category, p.channel
ORDER BY opt_out_pct DESC;

-- Q3: Channel mix by user (most-used channel per user)
SELECT user_id, channel, n_deliveries
FROM (
    SELECT
        n.user_id,
        d.channel,
        COUNT(*) AS n_deliveries,
        ROW_NUMBER() OVER (PARTITION BY n.user_id ORDER BY COUNT(*) DESC) AS rn
    FROM notifications n
    JOIN notification_deliveries d ON d.notification_id = n.id
    WHERE d.status NOT IN ('queued','failed')
    GROUP BY n.user_id, d.channel
) t
WHERE rn = 1
ORDER BY n_deliveries DESC;

-- Q4: Time from send to open (engagement speed)
-- Business question: how fast do users engage after delivery?
SELECT
    d.channel,
    COUNT(*) AS n_opens,
    ROUND(AVG(TIMESTAMPDIFF(SECOND, d.delivered_at, d.opened_at)) / 60, 2) AS avg_minutes_to_open,
    ROUND(AVG(TIMESTAMPDIFF(SECOND, d.delivered_at, d.opened_at)) / 60, 2) AS median_minutes_to_open
FROM notification_deliveries d
WHERE d.opened_at IS NOT NULL
  AND d.delivered_at IS NOT NULL
  AND d.delivered_at >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY d.channel;

-- Q5: Failed deliveries by provider + error category
SELECT
    d.provider,
    SUM(CASE WHEN d.status = 'failed'  THEN 1 ELSE 0 END) AS n_failed,
    SUM(CASE WHEN d.status = 'bounced' THEN 1 ELSE 0 END) AS n_bounced,
    ROUND(
        100.0 * SUM(CASE WHEN d.status IN ('failed','bounced') THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS failure_pct
FROM notification_deliveries d
GROUP BY d.provider
ORDER BY failure_pct DESC;

-- Q6: Users with high notification fatigue (>5 in last 24h)
SELECT
    n.user_id,
    u.email,
    COUNT(*) AS n_notifications
FROM notifications n
JOIN users u ON u.id = n.user_id
WHERE n.created_at >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL 24 HOUR)
  AND n.deleted_at IS NULL
GROUP BY n.user_id, u.email
HAVING COUNT(*) > 5
ORDER BY n_notifications DESC;

-- Q7: Funnel — created -> delivered -> opened -> clicked
SELECT
    SUM(CASE WHEN e.event_type = 'created'   THEN 1 ELSE 0 END) AS created_n,
    SUM(CASE WHEN e.event_type = 'delivered'THEN 1 ELSE 0 END) AS delivered_n,
    SUM(CASE WHEN e.event_type = 'opened'   THEN 1 ELSE 0 END) AS opened_n,
    SUM(CASE WHEN e.event_type = 'clicked'  THEN 1 ELSE 0 END) AS clicked_n,
    ROUND(100.0 * SUM(CASE WHEN e.event_type = 'delivered' THEN 1 ELSE 0 END)
              / NULLIF(SUM(CASE WHEN e.event_type = 'created' THEN 1 ELSE 0 END), 0), 2) AS pct_delivered,
    ROUND(100.0 * SUM(CASE WHEN e.event_type = 'opened'    THEN 1 ELSE 0 END)
              / NULLIF(SUM(CASE WHEN e.event_type = 'delivered' THEN 1 ELSE 0 END), 0), 2) AS pct_opened,
    ROUND(100.0 * SUM(CASE WHEN e.event_type = 'clicked'   THEN 1 ELSE 0 END)
              / NULLIF(SUM(CASE WHEN e.event_type = 'opened'    THEN 1 ELSE 0 END), 0), 2) AS pct_clicked
FROM notification_events e
WHERE e.occurred_at >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL 30 DAY);

-- Q8: Notification volume by template (last 30 days)
SELECT
    t.code,
    t.channel,
    COUNT(*) AS n_sent,
    SUM(CASE WHEN d.status = 'opened' THEN 1 ELSE 0 END) AS n_opened,
    ROUND(100.0 * SUM(CASE WHEN d.status = 'opened' THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 2) AS open_rate_pct
FROM notifications n
JOIN notification_templates t ON t.id = n.template_id
JOIN notification_deliveries d ON d.notification_id = n.id
WHERE n.created_at >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY t.code, t.channel
ORDER BY n_sent DESC;

-- Done: OLTP notification system (MySQL 8.0+, all timestamps UTC)