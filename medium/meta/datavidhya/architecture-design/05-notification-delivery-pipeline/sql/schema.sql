-- =====================================================================
-- Notification Pipeline — Schema
-- =====================================================================

CREATE TABLE IF NOT EXISTS notifications_sent (
    notification_id       STRING          NOT NULL,
    notification_group_id STRING,                       -- shared across channels
    user_id               STRING          NOT NULL,
    channel               STRING          NOT NULL,    -- push|email|sms|in_app
    notification_type     STRING          NOT NULL,    -- marketing|transactional|system
    template_id           STRING,
    campaign_id           STRING,
    variant_id            STRING,                       -- A/B test variant
    sent_ts               TIMESTAMP       NOT NULL,
    user_pixel_opted_in   BOOLEAN,                      -- email privacy flag
    PRIMARY KEY (notification_id)
) PARTITIONED BY (days(sent_ts));

CREATE TABLE IF NOT EXISTS notification_events (
    event_id     STRING          NOT NULL,
    notification_id        STRING,
    notification_group_id  STRING,
    user_id                STRING,
    event_type             STRING,         -- delivered | opened | clicked | converted | dismissed | unsubscribed
    event_ts               TIMESTAMP       NOT NULL,
    metadata               MAP<STRING, STRING>,
    PRIMARY KEY (event_id)
) PARTITIONED BY (days(event_ts));

-- One row per notification (deduped across channels) with all engagement facts
CREATE TABLE IF NOT EXISTS notification_facts (
    notification_group_id STRING  NOT NULL,
    user_id               STRING  NOT NULL,
    channels_sent         ARRAY<STRING>,
    notification_type     STRING,
    campaign_id           STRING,
    variant_id            STRING,
    sent_ts               TIMESTAMP,
    delivered_ts          TIMESTAMP,        -- earliest across channels
    opened_ts             TIMESTAMP,        -- earliest across channels
    clicked_ts            TIMESTAMP,
    converted_ts          TIMESTAMP,
    attributed_open       BOOLEAN,
    attributed_click      BOOLEAN,
    attributed_convert    BOOLEAN,
    attribution_window_end TIMESTAMP,
    PRIMARY KEY (notification_group_id)
) PARTITIONED BY (days(sent_ts));

-- Per-user fatigue metrics
CREATE TABLE IF NOT EXISTS user_fatigue_daily (
    user_id              STRING  NOT NULL,
    dt                   DATE    NOT NULL,
    notifs_sent_24h      BIGINT,
    notifs_sent_7d       BIGINT,
    open_rate_7d         DOUBLE,
    dismiss_rate_7d      DOUBLE,
    unsubscribe_count_30d BIGINT,
    fatigue_score        DOUBLE,
    fatigue_tier         STRING,             -- 'healthy' | 'warn' | 'critical'
    PRIMARY KEY (user_id, dt)
) PARTITIONED BY (dt);
