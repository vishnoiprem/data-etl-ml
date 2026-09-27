-- =====================================================================
-- 03 — OLTP: Social Media Platform  (users, posts, relationships, engagement)
-- =====================================================================
-- Companion to 03_oltp_social_media.sql. This version expands the
-- core design to cover the full problem statement: relationships
-- (follow / mute / block), nested comments, polymorphic likes,
-- notifications, hashtag indexing, spam/fake-account signals.
--
-- SCALE-NOTE: the prompt says 1B+ users and 100B+ posts. A single
-- Postgres instance CANNOT serve that scale, so the design here is
-- the OLTP SHAPE — the production system would shard users by
-- user_id (or hash(user_id)) and partition posts by created_at. The
-- schema below does NOT include those operational choices; it is the
-- normalised shape that the shards all share.
--
-- Design decisions:
--
--   * users are SHARDED. The id is a 64-bit number, allocated from
--     a separate sequence per shard so the global id space is unioned
--     by `shard_id || local_id`. Application code resolves global id
--     <-> (shard, local_id).
--
--   * FOLLOWS use a composite-PK join table, NOT two FK columns.
--     This makes "who follows user X" and "who does X follow" index-
--     only scans in opposite directions with no extra index. The
--     status column lets follow / mute / block share one table.
--
--   * POSTS are append-only from the user's perspective (with
--     soft-delete via deleted_at). Comments are recursive FK to
--     posts (top-level) and to comments (replies). Threading depth
--     is bounded at 5 in the application; the schema enforces
--     nothing because enforcing depth in SQL is more trouble than
--     it's worth.
--
--   * LIKES are POLYMORPHIC. They can target a post OR a comment.
--     Same pattern as the notification system: target_type +
--     target_id columns, composite UNIQUE on (target_type, target_id,
--     user_id).
--
--   * HASHTAGS are post <-> hashtag through a composite-PK join
--     table. Trending score is COMPUTED in the warehouse, not
--     materialised here — Postgres is the wrong tool for that.
--
--   * NOTIFICATIONS: a thin table that points back to the polymorphic
--     actor/target. Same shape as the rich notification system but
--     scoped to social events only.
--
--   * SPAM SIGNALS: a separate `user_signals` table. Keeping it out
--     of users lets the trust-and-safety team iterate without
--     migrations to the user table.
-- =====================================================================

\echo '=== Loading OLTP social media platform schema ==='

BEGIN;

-- pgcrypto for encode(digest(...)) — used in seed data to compute
-- polymorphic dedup fingerprints identical to what the application
-- would compute.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---------------------------------------------------------------------
-- 1) users
-- ---------------------------------------------------------------------
CREATE TABLE users (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    handle        TEXT NOT NULL,                            -- @alice, unique within the platform
    email         TEXT NOT NULL,
    display_name  TEXT,
    bio           TEXT,
    avatar_url    TEXT,
    is_verified   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at    TIMESTAMPTZ,
    CONSTRAINT uq_users_handle UNIQUE (handle),
    CONSTRAINT uq_users_email  UNIQUE (email)
);

CREATE INDEX idx_users_created ON users(created_at DESC);

-- ---------------------------------------------------------------------
-- 2) relationships  (follow / mute / block — same table, status differs)
-- ---------------------------------------------------------------------
-- Composite PK enforces "no duplicate relationships of the same kind"
-- without needing a UNIQUE constraint on top of two FK columns.
-- The CHECK on (follower_id <> followee_id) blocks self-relationships.
CREATE TABLE relationships (
    follower_id   BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    followee_id   BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status        TEXT   NOT NULL
                  CHECK (status IN ('following','muted','blocked','close_friend')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (follower_id, followee_id, status),
    CHECK (follower_id <> followee_id)
);

-- "Who follows X?" → index on followee_id (status filter optional).
CREATE INDEX idx_rel_followee ON relationships(followee_id, status);
-- "Who does X follow?" → reverse.
CREATE INDEX idx_rel_follower ON relationships(follower_id, status);

-- ---------------------------------------------------------------------
-- 3) posts
-- ---------------------------------------------------------------------
-- Posts are append-only. edit_history is a JSONB column rather than
-- a child table; production would store it in S3 with a pointer here.
CREATE TABLE posts (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    author_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body          TEXT NOT NULL CHECK (length(body) <= 4000),
    parent_post_id BIGINT REFERENCES posts(id) ON DELETE SET NULL,  -- reposts / quote-tweets
    media_urls    JSONB NOT NULL DEFAULT '[]'::jsonb,
    visibility    TEXT NOT NULL DEFAULT 'public'
                  CHECK (visibility IN ('public','followers','close_friends')),
    like_count    INTEGER NOT NULL DEFAULT 0,
    comment_count INTEGER NOT NULL DEFAULT 0,
    share_count   INTEGER NOT NULL DEFAULT 0,
    view_count    INTEGER NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at    TIMESTAMPTZ
);

CREATE INDEX idx_posts_author_created ON posts(author_id, created_at DESC)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_posts_created        ON posts(created_at DESC)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_posts_parent         ON posts(parent_post_id)
    WHERE parent_post_id IS NOT NULL;

-- ---------------------------------------------------------------------
-- 4) comments  (recursive — top-level post_id, replies thread on parent_comment_id)
-- ---------------------------------------------------------------------
-- A comment always belongs to a post. If parent_comment_id is NULL,
-- it's top-level. Otherwise it's a reply. We do NOT enforce a depth
-- limit in the schema — that's an application-layer invariant because
-- enforcing it in SQL requires triggers or recursive CTEs that the
-- application has to remember to maintain.
CREATE TABLE comments (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    post_id            BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    author_id          BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_comment_id  BIGINT REFERENCES comments(id) ON DELETE CASCADE,
    body               TEXT NOT NULL CHECK (length(body) <= 1000),
    like_count         INTEGER NOT NULL DEFAULT 0,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at         TIMESTAMPTZ
);

CREATE INDEX idx_comments_post_created ON comments(post_id, created_at)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_comments_parent       ON comments(parent_comment_id)
    WHERE parent_comment_id IS NOT NULL;

-- ---------------------------------------------------------------------
-- 5) likes  (POLYMORPHIC: target_type ∈ {'post','comment'})
-- ---------------------------------------------------------------------
-- The (target_type, target_id, user_id) UNIQUE constraint means a user
-- cannot like the same target twice. Re-likes after unlike are a new
-- row — different created_at, same key, so the unique key is unchanged
-- and unlike can DELETE rather than soft-mark.
--
-- target_type discriminator lets us put a single index on the pair
-- instead of separate post_likes / comment_likes tables that would
-- double the write traffic and lose the "user's recent activity" view.
CREATE TABLE likes (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    target_type  TEXT NOT NULL CHECK (target_type IN ('post','comment')),
    target_id    BIGINT NOT NULL,
    user_id      BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_like_target_user UNIQUE (target_type, target_id, user_id)
);

-- Per-target lookup ("who liked this post?").
CREATE INDEX idx_likes_target ON likes(target_type, target_id);
-- Per-user lookup ("what has this user liked?").
CREATE INDEX idx_likes_user ON likes(user_id, created_at DESC);

-- ---------------------------------------------------------------------
-- 6) shares  (also polymorphic — but smaller, so a separate table)
-- ---------------------------------------------------------------------
-- We split shares from likes because shares have different semantics
-- (a share can have a quote-tweet comment) and different lifecycle
-- (rarely deleted). Keeping them separate avoids polluting likes
-- with share-only fields.
CREATE TABLE shares (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    target_type   TEXT NOT NULL CHECK (target_type IN ('post','comment')),
    target_id     BIGINT NOT NULL,
    user_id       BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quote_text    TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_share_target_user UNIQUE (target_type, target_id, user_id)
);

CREATE INDEX idx_shares_target ON shares(target_type, target_id);
CREATE INDEX idx_shares_user   ON shares(user_id, created_at DESC);

-- ---------------------------------------------------------------------
-- 7) hashtags + post_hashtags
-- ---------------------------------------------------------------------
-- Hashtags are NORMALISED: one row per unique tag. The join table uses
-- a composite PK which doubles as the index for "posts tagged X" and
-- "tags on post Y" — no extra indexes needed.
CREATE TABLE hashtags (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tag          TEXT NOT NULL,                            -- without the #
    post_count   BIGINT NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_hashtags_tag UNIQUE (tag)
);

CREATE TABLE post_hashtags (
    post_id      BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    hashtag_id   BIGINT NOT NULL REFERENCES hashtags(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, hashtag_id)
);

-- "trending tag X" lookup. Reverse direction (tags per post) uses the PK.
CREATE INDEX idx_post_hashtags_hashtag ON post_hashtags(hashtag_id);

-- ---------------------------------------------------------------------
-- 8) notifications  (thin shim into the rich notification system)
-- ---------------------------------------------------------------------
-- For a social platform, notifications are mostly "X did Y to a thing
-- you authored". We model this with polymorphic actor + target and
-- the same dedup-fingerprint pattern.
CREATE TABLE social_notifications (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    actor_id        BIGINT REFERENCES users(id) ON DELETE SET NULL,
    event_type      TEXT NOT NULL
                    CHECK (event_type IN ('liked_post','liked_comment','commented',
                                          'followed','mentioned','shared','replied')),
    target_type     TEXT NOT NULL CHECK (target_type IN ('post','comment','user')),
    target_id       BIGINT,
    payload         JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    read_at         TIMESTAMPTZ,
    event_fingerprint TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_social_notif_fingerprint UNIQUE (event_fingerprint)
);

CREATE INDEX idx_social_notif_user_unread ON social_notifications(user_id)
    WHERE is_read = FALSE;

-- Polymorphic target lookup: "show every notification referencing post 42".
-- Same pattern as the rich notification system.
CREATE INDEX idx_social_notif_target ON social_notifications(target_type, target_id);

-- ---------------------------------------------------------------------
-- 9) user_signals  (spam / fake-account / trust signals)
-- ---------------------------------------------------------------------
-- Trust & safety maintains these signals out-of-band. Decoupling them
-- from users means schema changes to signals never require a user
-- migration. Each signal is one row per (user_id, signal_type) pair;
-- values are JSONB so the signal schema can evolve per-type.
CREATE TABLE user_signals (
    user_id      BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    signal_type  TEXT NOT NULL
                 CHECK (signal_type IN (
                     'fake_account_probability','spam_score',
                     'engagement_quality','content_category','age_restricted')),
    value        JSONB NOT NULL,                            -- {"score":0.97,"model":"v3"}
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, signal_type)
);

CREATE INDEX idx_signals_type_updated ON user_signals(signal_type, updated_at DESC);

-- =====================================================================
-- Sample data
-- =====================================================================

INSERT INTO users (handle, email, display_name, is_verified) VALUES
    ('alice',   'alice@example.com',  'Alice',   FALSE),
    ('bob',     'bob@example.com',    'Bob',     FALSE),
    ('carla',   'carla@example.com',  'Carla',   TRUE),
    ('dimitri', 'dimitri@example.com','Dimitri', FALSE),
    ('emma',    'emma@example.com',   'Emma',    FALSE);

-- Alice follows Bob, Carla, Dimitri. Bob follows Carla. Carla follows Alice.
-- Emma blocked Bob (toxic interaction). Bob muted Carla.
INSERT INTO relationships (follower_id, followee_id, status) VALUES
    (1, 2, 'following'),
    (1, 3, 'following'),
    (1, 4, 'following'),
    (2, 3, 'following'),
    (3, 1, 'following'),
    (5, 2, 'blocked'),
    (2, 3, 'muted');

-- A handful of posts.
INSERT INTO posts (author_id, body, like_count, comment_count) VALUES
    (1, 'Hello, world!', 3, 1),
    (2, 'Migrating our analytics stack today', 5, 0),
    (3, 'Verified check ✓', 12, 2),
    (4, 'New article out on Postgres internals', 8, 0);

-- A comment thread on post #3.
INSERT INTO comments (post_id, author_id, body, like_count) VALUES
    (3, 1, 'Congrats!', 0),
    (3, 4, 'Welcome aboard', 0),
    -- A reply to comment #1.
    (3, 2, 'Congrats from me too', 0);

-- Re-parent comment #2's parent_comment_id manually (the auto id won't match).
UPDATE comments SET parent_comment_id = 1 WHERE id = 2;

-- Likes: polymorphic across posts and comments.
INSERT INTO likes (target_type, target_id, user_id) VALUES
    ('post',    1, 2), ('post',    1, 3), ('post',    1, 4),
    ('post',    2, 1), ('post',    2, 3), ('post',    2, 4), ('post',    2, 5),
    ('post',    3, 1), ('post',    3, 2), ('post',    3, 4), ('post',    3, 5),
    ('post',    4, 1), ('post',    4, 2), ('post',    4, 3), ('post',    4, 5),
    ('comment', 1, 2),
    ('comment', 3, 1);

-- Hashtags and post_hashtags.
INSERT INTO hashtags (tag, post_count) VALUES
    ('postgres', 2), ('analytics', 1), ('welcome', 1);

INSERT INTO post_hashtags (post_id, hashtag_id) VALUES
    (2, 2),                        -- post #2 tagged 'analytics'
    (4, 1),                        -- post #4 tagged 'postgres'
    (3, 3);                        -- post #3 tagged 'welcome'

UPDATE hashtags SET post_count = 2 WHERE tag = 'postgres';
UPDATE hashtags SET post_count = 1 WHERE tag IN ('analytics', 'welcome');

-- Social notifications.
INSERT INTO social_notifications
    (user_id, actor_id, event_type, target_type, target_id, event_fingerprint)
VALUES
    (1, 2, 'liked_post', 'post', 1, encode(digest('post|1|liked_post|2|1', 'sha256'), 'hex')),
    (1, 3, 'commented',  'post', 1, encode(digest('post|1|commented|3|1',  'sha256'), 'hex')),
    (2, 1, 'followed',   'user', 1, encode(digest('user|1|followed|1|2',    'sha256'), 'hex')),
    (3, 1, 'followed',   'user', 1, encode(digest('user|1|followed|1|3',    'sha256'), 'hex')),
    (3, 4, 'commented',  'post', 3, encode(digest('post|3|commented|4|3',    'sha256'), 'hex'));

-- Trust & safety signals.
INSERT INTO user_signals (user_id, signal_type, value) VALUES
    (5, 'spam_score',              '{"score":0.92,"model":"v3"}'),
    (5, 'fake_account_probability','{"score":0.45,"model":"v3"}'),
    (4, 'engagement_quality',      '{"score":0.81,"model":"v2"}');

COMMIT;

-- =====================================================================
-- Self-verifying queries
-- =====================================================================

\echo ''
\echo '--- Q1: dedup UNIQUE blocks a duplicate like ---'
DO $$
BEGIN
    BEGIN
        INSERT INTO likes (target_type, target_id, user_id)
        VALUES ('post', 1, 2);
        RAISE EXCEPTION 'dedup failed: duplicate like was inserted';
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE 'PASS: UNIQUE blocked the duplicate like';
    END;
END;
$$;

\echo ''
\echo '--- Q2: who follows Alice AND Alice follows them back (mutual) ---'
SELECT a.follower_id, u.handle
FROM relationships a
JOIN relationships b ON b.follower_id = a.followee_id
                    AND b.followee_id = a.follower_id
                    AND b.status = 'following'
JOIN users u ON u.id = a.follower_id
WHERE a.followee_id = (SELECT id FROM users WHERE handle = 'alice')
  AND a.status = 'following';

\echo ''
\echo '--- Q3: trending hashtags (most posts in last 30d) ---'
SELECT h.tag, COUNT(ph.post_id) AS posts_in_30d
FROM hashtags h
JOIN post_hashtags ph ON ph.hashtag_id = h.id
JOIN posts p           ON p.id = ph.post_id
WHERE p.created_at >= now() - interval '30 days'
  AND p.deleted_at IS NULL
GROUP BY h.tag
ORDER BY posts_in_30d DESC;

\echo ''
\echo '--- Q4: nested comments thread on post #3 (top-level + replies) ---'
SELECT c.id, c.parent_comment_id, u.handle AS author, c.body
FROM comments c
JOIN users u ON u.id = c.author_id
WHERE c.post_id = 3 AND c.deleted_at IS NULL
ORDER BY c.parent_comment_id NULLS FIRST, c.created_at;

\echo ''
\echo '--- Q5: polymorphic likes — most-liked targets across types ---'
SELECT target_type, target_id, COUNT(*) AS likes
FROM likes
GROUP BY target_type, target_id
ORDER BY likes DESC
LIMIT 5;

\echo ''
\echo '--- Q6: users with high spam signals (T&S view) ---'
SELECT u.id, u.handle, s.signal_type, s.value
FROM users u
JOIN user_signals s ON s.user_id = u.id
WHERE s.signal_type IN ('spam_score','fake_account_probability')
  AND (s.value->>'score')::numeric >= 0.5
ORDER BY (s.value->>'score')::numeric DESC;

\echo ''
\echo '--- Q7: Alice''s feed — posts by users she follows, newest first ---'
SELECT p.id, u.handle AS author, p.body, p.created_at
FROM posts p
JOIN users u ON u.id = p.author_id
WHERE p.author_id IN (
    SELECT followee_id FROM relationships
    WHERE follower_id = (SELECT id FROM users WHERE handle = 'alice')
      AND status = 'following'
)
AND p.deleted_at IS NULL
AND p.visibility IN ('public','followers')
ORDER BY p.created_at DESC;

\echo ''
\echo '--- Q8: notifications for Alice (unread only) ---'
SELECT n.id, u.handle AS actor, n.event_type, n.target_type, n.target_id, n.created_at
FROM social_notifications n
LEFT JOIN users u ON u.id = n.actor_id
WHERE n.user_id = (SELECT id FROM users WHERE handle = 'alice')
  AND n.is_read = FALSE
ORDER BY n.created_at DESC;

\echo ''
\echo '--- Q9: polymorphic dedup — UNIQUE on (target_type, target_id, user_id) ---'
-- A user can't like the same post twice AND can't like a post and a
-- comment with the same id twice (because the (target_type, target_id)
-- pair is the key). We verify uniqueness by counting.
SELECT
    (SELECT COUNT(*) FROM likes) AS total_likes,
    (SELECT COUNT(DISTINCT (target_type, target_id, user_id)) FROM likes) AS unique_like_keys
;

\echo ''
\echo '=== Done: OLTP social media platform ==='
