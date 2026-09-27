-- =====================================================================
-- Content Moderation — Core Schema
-- =====================================================================

-- Content piece metadata
CREATE TABLE IF NOT EXISTS content (
    content_id     STRING          NOT NULL,
    user_id        STRING          NOT NULL,
    content_type   STRING          NOT NULL,    -- text | image | video
    text_payload   STRING,
    media_url      STRING,
    media_hash     STRING,                      -- perceptual hash (PhotoDNA etc.)
    language       STRING,
    created_ts     TIMESTAMP       NOT NULL,
    PRIMARY KEY (content_id)
) PARTITIONED BY (days(created_ts));

-- Per-modality model scores
CREATE TABLE IF NOT EXISTS content_scores (
    content_id     STRING          NOT NULL,
    modality       STRING          NOT NULL,    -- text | image | video_frame
    model_id       STRING          NOT NULL,
    model_version  STRING          NOT NULL,
    class_label    STRING          NOT NULL,    -- e.g. 'hate_speech', 'nudity', 'violence'
    score          DOUBLE          NOT NULL,    -- 0..1
    scored_ts      TIMESTAMP       NOT NULL,
    PRIMARY KEY (content_id, modality, model_id, class_label)
);

-- Final moderation decision
CREATE TABLE IF NOT EXISTS moderation_decisions (
    content_id     STRING          NOT NULL,
    decision       STRING          NOT NULL,    -- AUTO_REMOVE | AUTO_APPROVE | HUMAN_REVIEW
    severity_class STRING          NOT NULL,    -- SEVERE | HARMFUL | BORDERLINE | SAFE
    confidence     DOUBLE,
    threshold_used DOUBLE,
    model_versions ARRAY<STRING>,
    decided_ts     TIMESTAMP       NOT NULL,
    PRIMARY KEY (content_id)
);

-- Human review queue
CREATE TABLE IF NOT EXISTS review_queue (
    queue_id        STRING          NOT NULL,
    content_id      STRING          NOT NULL,
    priority        INT             NOT NULL,    -- 0 = highest
    sla_deadline_ts TIMESTAMP       NOT NULL,
    assigned_to     STRING,
    status          STRING          NOT NULL,    -- PENDING | ASSIGNED | DONE | EXPIRED
    enqueued_ts     TIMESTAMP       NOT NULL,
    PRIMARY KEY (queue_id)
) PARTITIONED BY (days(enqueued_ts));

-- Human review actions (audit trail)
CREATE TABLE IF NOT EXISTS human_review_actions (
    review_id     STRING          NOT NULL,
    queue_id      STRING          NOT NULL,
    reviewer_id   STRING          NOT NULL,
    content_id    STRING          NOT NULL,
    decision      STRING          NOT NULL,    -- REMOVE | APPROVE | ESCALATE
    rationale     STRING,
    is_appeal     BOOLEAN         DEFAULT FALSE,
    decided_ts    TIMESTAMP       NOT NULL,
    PRIMARY KEY (review_id)
);

-- Appeals
CREATE TABLE IF NOT EXISTS appeals (
    appeal_id     STRING          NOT NULL,
    content_id    STRING          NOT NULL,
    user_id       STRING          NOT NULL,
    reason        STRING,
    status        STRING          NOT NULL,    -- PENDING | DECIDED | REJECTED
    decided_by    STRING,
    decided_ts    TIMESTAMP,
    PRIMARY KEY (appeal_id)
);
