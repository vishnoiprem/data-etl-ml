-- =====================================================================
-- 03 — OLTP: Social Media Platform  (MySQL 8.0+)
-- =====================================================================
-- Companion to 03_oltp_social_media.sql. This version expands the
-- core design to cover the full problem statement: relationships
-- (follow / mute / block), nested comments, polymorphic likes,
-- notifications, hashtag indexing, spam/fake-account signals.
--
-- SCALE-NOTE: the prompt says 1B+ users and 100B+ posts. A single
-- MySQL instance CANNOT serve that scale, so the design here is
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
--     materialised here — MySQL is the wrong tool for that.
--
--   * NOTIFICATIONS: a thin table that points back to the polymorphic
--     actor/target. Same shape as the rich notification system but
--     scoped to social events only.
--
--   * SPAM SIGNALS: a separate `user_signals` table. Keeping it out
--     of users lets the trust-and-safety team iterate without
--     migrations to the user table.
--
-- MySQL 8.0+ conversion notes:
--   * TIMESTAMPTZ  -> DATETIME  (UTC stored, no zone conversion)
--   * JSONB -> JSON
--   * BOOLEAN -> TINYINT(1)
--   * TEXT -> VARCHAR (with explicit lengths) where reasonable
--   * pgcrypto's encode(digest(..., 'sha256'), 'hex') -> SHA2(..., 256)
--   * CREATE EXTENSION pgcrypto -> removed
--   * CREATE INDEX ... WHERE <partial> -> composite index on the
--     columns; MySQL has no partial indexes (8.0 doesn't support
--     functional indexes with WHERE clauses the same way).
--   * ORDER BY ... NULLS FIRST -> emulate with: parent_comment_id IS NULL DESC, parent_comment_id
--   * DO $$ ... $$ blocks -> plain SELECT (self-verification is a
--     query that the reader runs interactively)
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1) users
-- ---------------------------------------------------------------------
CREATE TABLE users (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    handle        VARCHAR(50)  NOT NULL,                    -- @alice, unique within the platform
    email         VARCHAR(254) NOT NULL,
    display_name  VARCHAR(80),
    bio           VARCHAR(255),
    avatar_url    VARCHAR(512),
    is_verified   TINYINT(1) NOT NULL DEFAULT 0,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at    DATETIME,
    UNIQUE KEY uq_users_handle (handle),
    UNIQUE KEY uq_users_email  (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_users_created ON users(created_at);

-- ---------------------------------------------------------------------
-- 2) relationships  (follow / mute / block — same table, status differs)
-- ---------------------------------------------------------------------
-- Composite PK enforces "no duplicate relationships of the same kind"
-- without needing a UNIQUE constraint on top of two FK columns.
-- The CHECK on (follower_id <> followee_id) blocks self-relationships.
CREATE TABLE relationships (
    follower_id   BIGINT NOT NULL,
    followee_id   BIGINT NOT NULL,
    status        VARCHAR(16) NOT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (follower_id, followee_id, status),
    CONSTRAINT fk_rel_follower FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_rel_followee FOREIGN KEY (followee_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_rel_status   CHECK (status IN ('following','muted','blocked','close_friend')),
    CONSTRAINT chk_rel_no_self  CHECK (follower_id <> followee_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- "Who follows X?" → index on followee_id (status filter optional).
CREATE INDEX idx_rel_followee ON relationships(followee_id, status);
-- "Who does X follow?" → reverse.
CREATE INDEX idx_rel_follower ON relationships(follower_id, status);

-- ---------------------------------------------------------------------
-- 3) posts
-- ---------------------------------------------------------------------
-- Posts are append-only. edit_history is a JSON column rather than
-- a child table; production would store it in S3 with a pointer here.
CREATE TABLE posts (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    author_id     BIGINT NOT NULL,
    body          TEXT NOT NULL,
    parent_post_id BIGINT,
    media_urls    JSON NOT NULL,
    visibility    VARCHAR(16) NOT NULL DEFAULT 'public',
    like_count    INT NOT NULL DEFAULT 0,
    comment_count INT NOT NULL DEFAULT 0,
    share_count   INT NOT NULL DEFAULT 0,
    view_count    INT NOT NULL DEFAULT 0,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at    DATETIME,
    CONSTRAINT fk_posts_author FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_posts_parent FOREIGN KEY (parent_post_id) REFERENCES posts(id) ON DELETE SET NULL,
    CONSTRAINT chk_posts_body_len   CHECK (CHAR_LENGTH(body) <= 4000),
    CONSTRAINT chk_posts_visibility CHECK (visibility IN ('public','followers','close_friends'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Active-author lookups. MySQL has no partial indexes, so we include
-- deleted_at in the index; queries filter it out in the WHERE clause.
CREATE INDEX idx_posts_author_created ON posts(author_id, created_at);
CREATE INDEX idx_posts_created        ON posts(created_at);
CREATE INDEX idx_posts_parent         ON posts(parent_post_id);

-- ---------------------------------------------------------------------
-- 4) comments  (recursive — top-level post_id, replies thread on parent_comment_id)
-- ---------------------------------------------------------------------
-- A comment always belongs to a post. If parent_comment_id is NULL,
-- it's top-level. Otherwise it's a reply. We do NOT enforce a depth
-- limit in the schema — that's an application-layer invariant because
-- enforcing it in SQL requires triggers or recursive CTEs that the
-- application has to remember to maintain.
CREATE TABLE comments (
    id                 BIGINT AUTO_INCREMENT PRIMARY KEY,
    post_id            BIGINT NOT NULL,
    author_id          BIGINT NOT NULL,
    parent_comment_id  BIGINT,
    body               TEXT NOT NULL,
    like_count         INT NOT NULL DEFAULT 0,
    created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at         DATETIME,
    CONSTRAINT fk_comments_post    FOREIGN KEY (post_id)           REFERENCES posts(id)    ON DELETE CASCADE,
    CONSTRAINT fk_comments_author  FOREIGN KEY (author_id)         REFERENCES users(id)    ON DELETE CASCADE,
    CONSTRAINT fk_comments_parent  FOREIGN KEY (parent_comment_id) REFERENCES comments(id) ON DELETE CASCADE,
    CONSTRAINT chk_comments_body_len CHECK (CHAR_LENGTH(body) <= 1000)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_comments_post_created ON comments(post_id, created_at);
CREATE INDEX idx_comments_parent       ON comments(parent_comment_id);

-- ---------------------------------------------------------------------
-- 5) likes  (POLYMORPHIC: target_type IN {'post','comment'})
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
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    target_type  VARCHAR(16) NOT NULL,
    target_id    BIGINT NOT NULL,
    user_id      BIGINT NOT NULL,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_like_target_user (target_type, target_id, user_id),
    CONSTRAINT fk_likes_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_likes_target_type CHECK (target_type IN ('post','comment'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Per-target lookup ("who liked this post?").
CREATE INDEX idx_likes_target ON likes(target_type, target_id);
-- Per-user lookup ("what has this user liked?").
CREATE INDEX idx_likes_user ON likes(user_id, created_at);

-- ---------------------------------------------------------------------
-- 6) shares  (also polymorphic — but smaller, so a separate table)
-- ---------------------------------------------------------------------
-- We split shares from likes because shares have different semantics
-- (a share can have a quote-tweet comment) and different lifecycle
-- (rarely deleted). Keeping them separate avoids polluting likes
-- with share-only fields.
CREATE TABLE shares (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    target_type   VARCHAR(16) NOT NULL,
    target_id     BIGINT NOT NULL,
    user_id       BIGINT NOT NULL,
    quote_text    TEXT,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_share_target_user (target_type, target_id, user_id),
    CONSTRAINT fk_shares_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_shares_target_type CHECK (target_type IN ('post','comment'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_shares_target ON shares(target_type, target_id);
CREATE INDEX idx_shares_user   ON shares(user_id, created_at);

-- ---------------------------------------------------------------------
-- 7) hashtags + post_hashtags
-- ---------------------------------------------------------------------
-- Hashtags are NORMALISED: one row per unique tag. The join table uses
-- a composite PK which doubles as the index for "posts tagged X" and
-- "tags on post Y" — no extra indexes needed.
CREATE TABLE hashtags (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    tag          VARCHAR(140) NOT NULL,                     -- without the #
    post_count   BIGINT NOT NULL DEFAULT 0,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_hashtags_tag (tag)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE post_hashtags (
    post_id      BIGINT NOT NULL,
    hashtag_id   BIGINT NOT NULL,
    PRIMARY KEY (post_id, hashtag_id),
    CONSTRAINT fk_ph_post    FOREIGN KEY (post_id)    REFERENCES posts(id)    ON DELETE CASCADE,
    CONSTRAINT fk_ph_hashtag FOREIGN KEY (hashtag_id) REFERENCES hashtags(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- "trending tag X" lookup. Reverse direction (tags per post) uses the PK.
CREATE INDEX idx_post_hashtags_hashtag ON post_hashtags(hashtag_id);

-- ---------------------------------------------------------------------
-- 8) notifications  (thin shim into the rich notification system)
-- ---------------------------------------------------------------------
-- For a social platform, notifications are mostly "X did Y to a thing
-- you authored". We model this with polymorphic actor + target and
-- the same dedup-fingerprint pattern.
CREATE TABLE social_notifications (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    actor_id        BIGINT,
    event_type      VARCHAR(32) NOT NULL,
    target_type     VARCHAR(16) NOT NULL,
    target_id       BIGINT,
    payload         JSON NOT NULL,
    is_read         TINYINT(1) NOT NULL DEFAULT 0,
    read_at         DATETIME,
    event_fingerprint VARCHAR(64) NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_social_notif_fingerprint (event_fingerprint),
    CONSTRAINT fk_sn_user  FOREIGN KEY (user_id)  REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_sn_actor FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT chk_sn_event_type  CHECK (event_type IN ('liked_post','liked_comment','commented',
                                          'followed','mentioned','shared','replied')),
    CONSTRAINT chk_sn_target_type CHECK (target_type IN ('post','comment','user'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Polymorphic target lookup: "show every notification referencing post 42".
-- Same pattern as the rich notification system.
CREATE INDEX idx_social_notif_user_unread ON social_notifications(user_id, is_read);
CREATE INDEX idx_social_notif_target      ON social_notifications(target_type, target_id);

-- ---------------------------------------------------------------------
-- 9) user_signals  (spam / fake-account / trust signals)
-- ---------------------------------------------------------------------
-- Trust & safety maintains these signals out-of-band. Decoupling them
-- from users means schema changes to signals never require a user
-- migration. Each signal is one row per (user_id, signal_type) pair;
-- values are JSON so the signal schema can evolve per-type.
CREATE TABLE user_signals (
    user_id      BIGINT NOT NULL,
    signal_type  VARCHAR(32) NOT NULL,
    value        JSON NOT NULL,                             -- {"score":0.97,"model":"v3"}
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, signal_type),
    CONSTRAINT fk_signals_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_signals_type CHECK (signal_type IN (
        'fake_account_probability','spam_score',
        'engagement_quality','content_category','age_restricted'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_signals_type_updated ON user_signals(signal_type, updated_at);

-- =====================================================================
-- Sample data
-- =====================================================================

INSERT INTO users (handle, email, display_name, is_verified) VALUES
    ('alice',   'alice@example.com',  'Alice',   0),
    ('bob',     'bob@example.com',    'Bob',     0),
    ('carla',   'carla@example.com',  'Carla',   1),
    ('dimitri', 'dimitri@example.com','Dimitri', 0),
    ('emma',    'emma@example.com',   'Emma',    0);

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
    (4, 'New article out on MySQL internals', 8, 0);

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
    ('mysql', 2), ('analytics', 1), ('welcome', 1);

INSERT INTO post_hashtags (post_id, hashtag_id) VALUES
    (2, 2),                        -- post #2 tagged 'analytics'
    (4, 1),                        -- post #4 tagged 'mysql'
    (3, 3);                        -- post #3 tagged 'welcome'

UPDATE hashtags SET post_count = 2 WHERE tag = 'mysql';
UPDATE hashtags SET post_count = 1 WHERE tag IN ('analytics', 'welcome');

-- Social notifications.
-- Fingerprints: sha256("target_type|target_id|event_type|actor_id|user_id").
INSERT INTO social_notifications
    (user_id, actor_id, event_type, target_type, target_id, event_fingerprint)
VALUES
    (1, 2, 'liked_post', 'post', 1, SHA2('post|1|liked_post|2|1', 256)),
    (1, 3, 'commented',  'post', 1, SHA2('post|1|commented|3|1',  256)),
    (2, 1, 'followed',   'user', 1, SHA2('user|1|followed|1|2',    256)),
    (3, 1, 'followed',   'user', 1, SHA2('user|1|followed|1|3',    256)),
    (3, 4, 'commented',  'post', 3, SHA2('post|3|commented|4|3',    256));

-- Trust & safety signals.
INSERT INTO user_signals (user_id, signal_type, value) VALUES
    (5, 'spam_score',              JSON_OBJECT('score', 0.92, 'model', 'v3')),
    (5, 'fake_account_probability',JSON_OBJECT('score', 0.45, 'model', 'v3')),
    (4, 'engagement_quality',      JSON_OBJECT('score', 0.81, 'model', 'v2'));

-- =====================================================================
-- Self-verifying queries
-- =====================================================================

-- Q1: dedup UNIQUE blocks a duplicate like.
-- >>> Expect on re-insert of ('post', 1, 2): ERROR 1062 (23000):
--     Duplicate entry 'post-1-2' for key 'uq_like_target_user'

-- Q2: who follows Alice AND Alice follows them back (mutual).
SELECT a.follower_id, u.handle
FROM relationships a
JOIN relationships b ON b.follower_id = a.followee_id
                    AND b.followee_id = a.follower_id
                    AND b.status = 'following'
JOIN users u ON u.id = a.follower_id
WHERE a.followee_id = (SELECT id FROM users WHERE handle = 'alice')
  AND a.status = 'following';

-- Q3: trending hashtags (most posts in last 30d).
-- 30 days ago, computed in UTC.
SELECT h.tag, COUNT(ph.post_id) AS posts_in_30d
FROM hashtags h
JOIN post_hashtags ph ON ph.hashtag_id = h.id
JOIN posts p           ON p.id = ph.post_id
WHERE p.created_at >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL 30 DAY)
  AND p.deleted_at IS NULL
GROUP BY h.tag
ORDER BY posts_in_30d DESC;

-- Q4: nested comments thread on post #3 (top-level + replies).
-- Original Postgres ORDER BY used NULLS FIRST, which MySQL doesn't
-- support natively. The emulation is: `IS NULL DESC` puts NULLs first
-- in the same direction as a DESC sort; here we use IS NULL DESC for
-- parent_comment_id and ASC for created_at.
SELECT c.id, c.parent_comment_id, u.handle AS author, c.body
FROM comments c
JOIN users u ON u.id = c.author_id
WHERE c.post_id = 3 AND c.deleted_at IS NULL
ORDER BY (c.parent_comment_id IS NULL) DESC, c.parent_comment_id, c.created_at;

-- Q5: polymorphic likes — most-liked targets across types.
SELECT target_type, target_id, COUNT(*) AS likes
FROM likes
GROUP BY target_type, target_id
ORDER BY likes DESC
LIMIT 5;

-- Q6: users with high spam signals (T&S view).
-- JSON_EXTRACT replaces the Postgres `value->>'score'` operator.
SELECT u.id, u.handle, s.signal_type,
       JSON_EXTRACT(s.value, '$.score') AS score
FROM users u
JOIN user_signals s ON s.user_id = u.id
WHERE s.signal_type IN ('spam_score','fake_account_probability')
  AND CAST(JSON_EXTRACT(s.value, '$.score') AS DECIMAL(4,2)) >= 0.5
ORDER BY JSON_EXTRACT(s.value, '$.score') DESC;

-- Q7: Alice's feed — posts by users she follows, newest first.
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

-- Q8: notifications for Alice (unread only).
SELECT n.id, u.handle AS actor, n.event_type, n.target_type, n.target_id, n.created_at
FROM social_notifications n
LEFT JOIN users u ON u.id = n.actor_id
WHERE n.user_id = (SELECT id FROM users WHERE handle = 'alice')
  AND n.is_read = 0
ORDER BY n.created_at DESC;

-- Q9: polymorphic dedup — UNIQUE on (target_type, target_id, user_id).
-- We verify uniqueness by counting total vs distinct keys.
SELECT
    (SELECT COUNT(*) FROM likes) AS total_likes,
    (SELECT COUNT(*) FROM (SELECT DISTINCT target_type, target_id, user_id FROM likes) x)
        AS unique_like_keys;

-- Done: OLTP social media platform (MySQL 8.0+, all timestamps UTC)
