-- =====================================================================
-- 02 — OLTP: Multi-Channel Notification System
-- =====================================================================
-- Domain: an app that sends notifications to users across multiple
-- channels (email, push, SMS, in-app), triggered either by an event
-- (e.g. "you got a new follower") or on a schedule (e.g. "weekly
-- digest every Monday at 9am").
--
-- Design notes (read these before the DDL):
--
-- 1) notifications vs notification_deliveries are SPLIT.
--    A notification is the *intent* — "tell user 42 their order
--    shipped". A delivery is the *attempt* on a channel. One
--    notification fans out to N deliveries (email + push + SMS).
--    Each delivery has its own state (queued, sent, delivered,
--    opened, clicked, failed).
--
-- 2) templates are first-class. Hard-coding notification copy in
--    application code is a rookie mistake — it kills i18n, A/B
--    testing, and audit trails.
--
-- 3) user_notification_preferences is per-channel AND per-category.
--    Users opt out of "marketing email" but want "transactional
--    SMS". Granularity matters.
--
-- 4) notification_events is an append-only audit log. Every state
--    transition lands here. Useful for debugging delivery issues,
--    computing funnel metrics, and replay.
--
-- 5) Soft delete (deleted_at) everywhere. Hard-deleting a delivery
--    row destroys billing reconciliation.
-- =====================================================================

\echo '=== Loading OLTP notification schema ==='

BEGIN;

-- ---------------------------------------------------------------------
-- 1) users
-- ---------------------------------------------------------------------
CREATE TABLE users (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email         TEXT NOT NULL,
    phone_e164    TEXT,                              -- E.164 format, e.g. +447700900123
    locale        TEXT NOT NULL DEFAULT 'en_GB',
    timezone      TEXT NOT NULL DEFAULT 'UTC',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at    TIMESTAMPTZ,
    CONSTRAINT uq_users_email UNIQUE (email)
);

CREATE INDEX idx_users_phone    ON users(phone_e164) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_created  ON users(created_at DESC);

-- ---------------------------------------------------------------------
-- 2) notification_templates
-- ---------------------------------------------------------------------
CREATE TABLE notification_templates (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code            TEXT NOT NULL,                  -- e.g. 'order.shipped', 'weekly.digest'
    channel         TEXT NOT NULL CHECK (channel IN ('email','push','sms','in_app')),
    locale          TEXT NOT NULL DEFAULT 'en_GB',
    subject         TEXT,                           -- NULL for push/SMS
    body            TEXT NOT NULL,                  -- may contain {{placeholders}}
    version         INT  NOT NULL DEFAULT 1,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_template_code_locale_channel UNIQUE (code, locale, channel)
);

CREATE INDEX idx_templates_code  ON notification_templates(code) WHERE is_active;

-- ---------------------------------------------------------------------
-- 3) user_notification_preferences
-- ---------------------------------------------------------------------
CREATE TABLE user_notification_preferences (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category        TEXT NOT NULL CHECK (category IN ('transactional','marketing','social','digest','security')),
    channel         TEXT NOT NULL CHECK (channel IN ('email','push','sms','in_app')),
    is_enabled      BOOLEAN NOT NULL DEFAULT TRUE,
    quiet_hours_start TIME,                         -- e.g. 22:00
    quiet_hours_end   TIME,                         -- e.g. 07:00
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_pref_user_cat_chan UNIQUE (user_id, category, channel)
);

CREATE INDEX idx_prefs_user ON user_notification_preferences(user_id);

-- ---------------------------------------------------------------------
-- 4) notifications (the intent)
-- ---------------------------------------------------------------------
CREATE TABLE notifications (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_id     BIGINT REFERENCES notification_templates(id) ON DELETE SET NULL,
    category        TEXT NOT NULL CHECK (category IN ('transactional','marketing','social','digest','security')),
    priority        SMALLINT NOT NULL DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    payload         JSONB NOT NULL DEFAULT '{}'::jsonb,   -- variables for template rendering
    trigger_type    TEXT NOT NULL CHECK (trigger_type IN ('event','scheduled','manual')),
    scheduled_for   TIMESTAMPTZ,                     -- when the worker should pick it up
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    delivered_at    TIMESTAMPTZ,                     -- populated when last delivery succeeds
    read_at         TIMESTAMPTZ,                     -- populated when user opens (in-app)
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_notif_user_created   ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notif_scheduled     ON notifications(scheduled_for)
    WHERE trigger_type = 'scheduled' AND delivered_at IS NULL;
CREATE INDEX idx_notif_template      ON notifications(template_id);
CREATE INDEX idx_notif_unread        ON notifications(user_id) WHERE read_at IS NULL AND deleted_at IS NULL;

-- ---------------------------------------------------------------------
-- 5) notification_deliveries (the per-channel attempts)
-- ---------------------------------------------------------------------
CREATE TABLE notification_deliveries (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    notification_id     BIGINT NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    channel             TEXT NOT NULL CHECK (channel IN ('email','push','sms','in_app')),
    status              TEXT NOT NULL CHECK (status IN ('queued','sent','delivered','failed','bounced','opened','clicked')),
    provider            TEXT,                       -- 'sendgrid', 'fcm', 'twilio', 'apns'
    provider_message_id TEXT,                       -- external ID for tracing
    attempt_count       SMALLINT NOT NULL DEFAULT 0,
    last_error          TEXT,
    queued_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    sent_at             TIMESTAMPTZ,
    delivered_at        TIMESTAMPTZ,
    opened_at           TIMESTAMPTZ,
    clicked_at          TIMESTAMPTZ,
    failed_at           TIMESTAMPTZ,
    deleted_at          TIMESTAMPTZ
);

CREATE INDEX idx_deliveries_notif       ON notification_deliveries(notification_id);
CREATE INDEX idx_deliveries_channel     ON notification_deliveries(channel, status);
CREATE INDEX idx_deliveries_status      ON notification_deliveries(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_deliveries_provider_id ON notification_deliveries(provider_message_id);

-- ---------------------------------------------------------------------
-- 6) notification_events (append-only audit log)
-- ---------------------------------------------------------------------
CREATE TABLE notification_events (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    notification_id BIGINT NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    delivery_id     BIGINT REFERENCES notification_deliveries(id) ON DELETE SET NULL,
    event_type      TEXT NOT NULL CHECK (event_type IN (
                        'created','queued','sent','delivered','opened','clicked',
                        'failed','bounced','opted_out','rate_limited')),
    payload         JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_events_notif      ON notification_events(notification_id, occurred_at);
CREATE INDEX idx_events_delivery   ON notification_events(delivery_id, occurred_at);
CREATE INDEX idx_events_type_time  ON notification_events(event_type, occurred_at DESC);

-- =====================================================================
-- Sample data
-- =====================================================================

INSERT INTO users (email, phone_e164, locale, timezone) VALUES
    ('alice.wong@example.com',   '+447700900101', 'en_GB', 'Europe/London'),
    ('bob.singh@example.com',    '+14155550101',  'en_US', 'America/Los_Angeles'),
    ('carla.rossi@example.com',  '+393331234567', 'it_IT', 'Europe/Rome'),
    ('dimitri.ivanov@example.com','+79161234567','ru_RU', 'Europe/Moscow'),
    ('emma.müller@example.com',  '+4915112345678','de_DE', 'Europe/Berlin'),
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
    (1, 'transactional', 'email', TRUE),  (1, 'transactional', 'sms',    TRUE),  (1, 'marketing', 'email', FALSE),
    (2, 'transactional', 'email', TRUE),  (2, 'transactional', 'push',   TRUE),  (2, 'marketing', 'email', FALSE),
    (3, 'transactional', 'email', TRUE),  (3, 'transactional', 'sms',    FALSE), (3, 'digest',    'email', TRUE),
    (4, 'transactional', 'email', TRUE),  (4, 'transactional', 'push',   TRUE),  (4, 'marketing', 'email', TRUE),
    (5, 'transactional', 'email', TRUE),  (5, 'transactional', 'sms',    TRUE),  (5, 'social',    'push',  TRUE),
    (6, 'transactional', 'email', TRUE),  (6, 'transactional', 'sms',    TRUE),  (6, 'marketing', 'email', FALSE),
    (7, 'transactional', 'email', TRUE),  (7, 'transactional', 'push',   TRUE),  (7, 'digest',    'email', TRUE),
    (8, 'transactional', 'email', TRUE),  (8, 'transactional', 'push',   TRUE),  (8, 'marketing', 'email', FALSE),
    (9, 'transactional', 'email', TRUE),  (9, 'transactional', 'sms',    TRUE),  (9, 'social',    'push',  TRUE),
    (10,'transactional', 'email', TRUE),  (10,'transactional', 'sms',    TRUE),  (10,'marketing', 'email', TRUE);

INSERT INTO notifications (user_id, template_id, category, priority, payload, trigger_type, scheduled_for, created_at) VALUES
    (1, 1, 'transactional', 9, '{"order_id":"A1042","name":"Alice","url":"https://ex.com/t/A1042"}', 'event',     NULL,           now() - interval '2 days'),
    (1, 2, 'transactional', 9, '{"order_id":"A1042"}', 'event', NULL,           now() - interval '2 days'),
    (2, 4, 'social',        5, '{"follower_name":"Carla"}',                          'event',     NULL,           now() - interval '1 day'),
    (3, 3, 'digest',        3, '{"name":"Carla","count":5}',                          'scheduled', now() - interval '3 days', now() - interval '4 days'),
    (4, 5, 'security',     10, '{"location":"Moscow, RU"}',                          'event',     NULL,           now() - interval '12 hours'),
    (4, 6, 'security',     10, '{"location":"Moscow, RU"}',                          'event',     NULL,           now() - interval '12 hours'),
    (5, 7, 'marketing',     3, '{"name":"Emma","item_count":3}',                       'event',     NULL,           now() - interval '6 hours'),
    (6, 10,'transactional', 9, '{"order_id":"A1077"}',                                'event',     NULL,           now() - interval '1 hour'),
    (7, 8, 'social',        5, '{"replier_name":"Hiro"}',                             'event',     NULL,           now() - interval '30 minutes'),
    (7, 9, 'social',        5, '{"replier_name":"Hiro","snippet":"totally agree"}',    'event',     NULL,           now() - interval '30 minutes'),
    (8, 3, 'digest',        3, '{"name":"Hiro","count":7}',                            'scheduled', now() - interval '2 days', now() - interval '3 days'),
    (9, 4, 'social',        5, '{"follower_name":"James"}',                            'event',     NULL,           now() - interval '15 minutes'),
    (10,5, 'security',     10, '{"location":"Dublin, IE"}',                            'event',     NULL,           now() - interval '5 minutes'),
    (10,6, 'security',     10, '{"location":"Dublin, IE"}',                            'event',     NULL,           now() - interval '5 minutes'),
    (1, 3, 'digest',        3, '{"name":"Alice","count":4}',                            'scheduled', now() + interval '5 days',  now());

INSERT INTO notification_deliveries (notification_id, channel, status, provider, attempt_count, queued_at, sent_at, delivered_at, opened_at) VALUES
    (1,  'email', 'opened',   'sendgrid', 1, now() - interval '2 days', now() - interval '2 days' + interval '5 seconds', now() - interval '2 days' + interval '30 seconds', now() - interval '1 day'),
    (1,  'push',  'delivered','fcm',      1, now() - interval '2 days', now() - interval '2 days' + interval '2 seconds', now() - interval '2 days' + interval '10 seconds', NULL),
    (2,  'push',  'opened',   'fcm',      1, now() - interval '1 day',  now() - interval '1 day' + interval '2 seconds', now() - interval '1 day' + interval '8 seconds', now() - interval '20 hours'),
    (3,  'email', 'delivered','sendgrid', 1, now() - interval '3 days', now() - interval '3 days' + interval '4 seconds', now() - interval '3 days' + interval '40 seconds', NULL),
    (3,  'push',  'failed',   'fcm',      2, now() - interval '3 days', now() - interval '3 days' + interval '2 seconds', NULL, NULL),
    (4,  'email', 'opened',   'sendgrid', 1, now() - interval '12 hours', now() - interval '12 hours' + interval '3 seconds', now() - interval '12 hours' + interval '20 seconds', now() - interval '11 hours'),
    (4,  'sms',    'delivered','twilio',   1, now() - interval '12 hours', now() - interval '12 hours' + interval '5 seconds', now() - interval '12 hours' + interval '15 seconds', NULL),
    (5,  'email', 'clicked',  'sendgrid', 1, now() - interval '6 hours',  now() - interval '6 hours' + interval '4 seconds', now() - interval '6 hours' + interval '25 seconds', now() - interval '5 hours'),
    (6,  'email', 'failed',   'sendgrid', 3, now() - interval '1 hour',   now() - interval '1 hour' + interval '2 seconds', NULL, NULL),
    (7,  'in_app','opened',   NULL,       0, now() - interval '30 minutes', NULL, now() - interval '30 minutes', now() - interval '25 minutes'),
    (7,  'push',  'delivered','apns',     1, now() - interval '30 minutes', now() - interval '30 minutes' + interval '3 seconds', now() - interval '30 minutes' + interval '12 seconds', NULL),
    (8,  'push',  'opened',   'fcm',      1, now() - interval '15 minutes', now() - interval '15 minutes' + interval '2 seconds', now() - interval '15 minutes' + interval '7 seconds', now() - interval '10 minutes'),
    (9,  'email', 'opened',   'sendgrid', 1, now() - interval '12 hours', now() - interval '12 hours' + interval '3 seconds', now() - interval '12 hours' + interval '18 seconds', now() - interval '11 hours'),
    (9,  'sms',   'delivered','twilio',   1, now() - interval '12 hours', now() - interval '12 hours' + interval '5 seconds', now() - interval '12 hours' + interval '13 seconds', NULL),
    (10, 'email', 'queued',   'sendgrid', 0, now() + interval '5 days', NULL, NULL, NULL);

INSERT INTO notification_events (notification_id, delivery_id, event_type, occurred_at) VALUES
    (1, 1, 'created',  now() - interval '2 days'),
    (1, 1, 'queued',   now() - interval '2 days' + interval '1 second'),
    (1, 1, 'sent',     now() - interval '2 days' + interval '5 seconds'),
    (1, 1, 'delivered',now() - interval '2 days' + interval '30 seconds'),
    (1, 1, 'opened',   now() - interval '1 day'),
    (3, 3, 'failed',   now() - interval '3 days' + interval '2 seconds'),
    (4, 5, 'sent',     now() - interval '12 hours'),
    (4, 5, 'opened',   now() - interval '11 hours'),
    (6, 9, 'failed',   now() - interval '1 hour'),
    (6, 9, 'rate_limited', now() - interval '50 minutes'),
    (10,15,'queued',   now() + interval '5 days');

COMMIT;

-- =====================================================================
-- Example queries
-- =====================================================================

\echo ''
\echo '--- Q1: Delivery rate per channel (last 7 days) ---'
-- Business question: which channel delivers successfully most often?
SELECT
    d.channel,
    COUNT(*)                                                AS total_attempts,
    COUNT(*) FILTER (WHERE d.status IN ('delivered','opened','clicked')) AS successful,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE d.status IN ('delivered','opened','clicked'))
              / NULLIF(COUNT(*), 0),
        2
    ) AS delivery_rate_pct
FROM notification_deliveries d
WHERE d.queued_at >= now() - interval '7 days'
GROUP BY d.channel
ORDER BY delivery_rate_pct DESC;

\echo ''
\echo '--- Q2: Opt-out rate by category ---'
-- Business question: what fraction of users have disabled each channel-category combo?
SELECT
    p.category,
    p.channel,
    COUNT(*) AS total_prefs,
    COUNT(*) FILTER (WHERE NOT p.is_enabled) AS opted_out,
    ROUND(100.0 * COUNT(*) FILTER (WHERE NOT p.is_enabled) / COUNT(*), 2) AS opt_out_pct
FROM user_notification_preferences p
GROUP BY p.category, p.channel
ORDER BY opt_out_pct DESC;

\echo ''
\echo '--- Q3: Channel mix by user (most-used channel per user) ---'
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

\echo ''
\echo '--- Q4: Time from send to open (engagement speed) ---'
-- Business question: how fast do users engage after delivery?
SELECT
    d.channel,
    COUNT(*) AS n_opens,
    ROUND(AVG(EXTRACT(EPOCH FROM (d.opened_at - d.delivered_at)) / 60)::numeric, 2) AS avg_minutes_to_open,
    ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (d.opened_at - d.delivered_at))))::numeric / 60, 2) AS median_minutes_to_open
FROM notification_deliveries d
WHERE d.opened_at IS NOT NULL
  AND d.delivered_at IS NOT NULL
  AND d.delivered_at >= now() - interval '30 days'
GROUP BY d.channel;

\echo ''
\echo '--- Q5: Failed deliveries by provider + error category ---'
SELECT
    d.provider,
    COUNT(*) FILTER (WHERE d.status = 'failed') AS n_failed,
    COUNT(*) FILTER (WHERE d.status = 'bounced') AS n_bounced,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE d.status IN ('failed','bounced')) / COUNT(*),
        2
    ) AS failure_pct
FROM notification_deliveries d
GROUP BY d.provider
ORDER BY failure_pct DESC;

\echo ''
\echo '--- Q6: Users with high notification fatigue (>5 in last 24h) ---'
SELECT
    n.user_id,
    u.email,
    COUNT(*) AS n_notifications
FROM notifications n
JOIN users u ON u.id = n.user_id
WHERE n.created_at >= now() - interval '24 hours'
  AND n.deleted_at IS NULL
GROUP BY n.user_id, u.email
HAVING COUNT(*) > 5
ORDER BY n_notifications DESC;

\echo ''
\echo '--- Q7: Funnel — created -> delivered -> opened -> clicked ---'
WITH stages AS (
    SELECT
        COUNT(*) FILTER (WHERE e.event_type = 'created')    AS created_n,
        COUNT(*) FILTER (WHERE e.event_type = 'delivered') AS delivered_n,
        COUNT(*) FILTER (WHERE e.event_type = 'opened')    AS opened_n,
        COUNT(*) FILTER (WHERE e.event_type = 'clicked')   AS clicked_n
    FROM notification_events e
    WHERE e.occurred_at >= now() - interval '30 days'
)
SELECT
    created_n,
    delivered_n,
    opened_n,
    clicked_n,
    ROUND(100.0 * delivered_n / NULLIF(created_n,0), 2)    AS pct_delivered,
    ROUND(100.0 * opened_n    / NULLIF(delivered_n,0), 2) AS pct_opened,
    ROUND(100.0 * clicked_n   / NULLIF(opened_n,0), 2)    AS pct_clicked
FROM stages;

\echo ''
\echo '--- Q8: Notification volume by template (last 30 days) ---'
SELECT
    t.code,
    t.channel,
    COUNT(*) AS n_sent,
    COUNT(*) FILTER (WHERE d.status = 'opened') AS n_opened,
    ROUND(100.0 * COUNT(*) FILTER (WHERE d.status = 'opened') / NULLIF(COUNT(*),0), 2) AS open_rate_pct
FROM notifications n
JOIN notification_templates t ON t.id = n.template_id
JOIN notification_deliveries d ON d.notification_id = n.id
WHERE n.created_at >= now() - interval '30 days'
GROUP BY t.code, t.channel
ORDER BY n_sent DESC;

\echo ''
\echo '=== Done: OLTP notification system ==='
