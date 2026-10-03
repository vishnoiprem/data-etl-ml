# Model Entities for Feed Content and Shares (News Feed Data Model)

## 1. Simple way to think

- A News Feed is like a magazine rack personalized to you. Every time you open the app, the rack shows you ~20 items — posts, photos, short videos — and lets you like, comment, or share each.
- Behind the scenes, three things are happening: someone **created a piece of content**, the system **decided to show it to you**, and you **interacted with it**. Those are three separate events with three separate data models.
- The first challenge: posts come in different shapes. A text post is small (a sentence). A photo is bigger. A short video is huge. Trying to put them all in one table means lots of NULL columns and slow queries.
- The solution is a **polymorphic content table** — one `posts` table for shared fields (id, author, timestamp), and a separate `post_media` table for the type-specific stuff. Cleaner schema, faster queries.
- The second challenge: interactions. One user liking 1,000 different posts means 1,000 rows in `likes`. With a billion users, that's a *lot* of rows — but the pattern is always "user X did action Y on post Z at time T". That's a fact table.
- Shares are special: when you share a post, a *new* post is born. So a share is both an interaction AND new content. Model it as a self-referential link.
- Indexes matter more than you think. Without `(user_id, created_at DESC)` on posts, the feed query dies.

## 2. Interview write-up (how to solve it)

**Requirements clarification.** "Quick check — are we modeling the feed serving system, the analytics data model, or both? I'll assume analytics: tables optimized for 'how is this post performing' and 'what's this user engaging with'. Also — what's the rough scale? Let's say 500M DAU, 10B posts total, 100B interactions."

**Core entities.**

```
[User] ─creates─> [Post] ─has─> [PostMedia] (polymorphic)
                    │
                    ├──< [Like]
                    ├──< [Comment] ─< [CommentReply]
                    ├──< [Share] ──> [Post] (new post)
                    └──< [View] (impression)
```

**Data model (Postgres-style, OLTP).**

```sql
CREATE TABLE users (
  user_id        BIGINT PRIMARY KEY,
  username       VARCHAR(50) UNIQUE,
  display_name   VARCHAR(100),
  created_at     TIMESTAMPTZ,
  country_code   CHAR(2),
  -- profile fields
);

CREATE TABLE posts (
  post_id        BIGINT PRIMARY KEY,
  author_id      BIGINT REFERENCES users(user_id),
  post_type      VARCHAR(16),  -- 'text', 'image', 'video', 'share'
  text_content   TEXT,
  parent_post_id BIGINT REFERENCES posts(post_id),  -- for shares/reposts
  created_at     TIMESTAMPTZ,
  deleted_at     TIMESTAMPTZ,
  -- soft delete + moderation
);
CREATE INDEX idx_posts_author ON posts(author_id, created_at DESC);
CREATE INDEX idx_posts_recent ON posts(created_at DESC) WHERE deleted_at IS NULL;

CREATE TABLE post_media (
  media_id       BIGINT PRIMARY KEY,
  post_id        BIGINT REFERENCES posts(post_id),
  media_type     VARCHAR(16),  -- 'image', 'video'
  url            VARCHAR(500),
  thumbnail_url  VARCHAR(500),
  duration_s     INT,          -- NULL for images
  width_px       INT,
  height_px      INT,
  size_bytes     BIGINT
);
CREATE INDEX idx_media_post ON post_media(post_id);

CREATE TABLE likes (
  user_id        BIGINT,
  post_id        BIGINT,
  created_at     TIMESTAMPTZ,
  PRIMARY KEY (user_id, post_id)
);
CREATE INDEX idx_likes_post ON likes(post_id);

CREATE TABLE comments (
  comment_id     BIGINT PRIMARY KEY,
  post_id        BIGINT REFERENCES posts(post_id),
  author_id      BIGINT REFERENCES users(user_id),
  parent_comment_id BIGINT REFERENCES comments(comment_id),
  body           TEXT,
  created_at     TIMESTAMPTZ
);
CREATE INDEX idx_comments_post ON comments(post_id, created_at);

CREATE TABLE shares (
  share_id       BIGINT PRIMARY KEY,
  original_post_id BIGINT REFERENCES posts(post_id),
  sharer_id      BIGINT REFERENCES users(user_id),
  -- a share can have its own caption, but the new post is in `posts`
  created_at     TIMESTAMPTZ
);

CREATE TABLE impressions (
  user_id        BIGINT,
  post_id        BIGINT,
  feed_position  INT,        -- where in the feed it appeared
  seen_at        TIMESTAMPTZ,
  dwell_ms       INT,        -- 0 if scrolled past
  PRIMARY KEY (user_id, post_id, seen_at)
) PARTITION BY RANGE (seen_at);
```

**Key design decisions.**
- **Polymorphic content**: keep common fields in `posts`, type-specific in `post_media`. Avoids NULL hell and one giant denormalized row.
- **Shares as new posts**: a share creates a row in `posts` with `post_type='share'` and `parent_post_id` set. Counts as both an interaction and new content.
- **Composite keys on interactions**: `(user_id, post_id)` on likes prevents duplicates and makes "did this user like this post?" a single index lookup.
- **Impressions as a partitioned fact table**: this is the largest table by far. Partition by day, archive after 90 days.

**Scale considerations.** This OLTP schema doesn't survive 100B rows in Postgres. The pattern is: hot data in Postgres with sharding (Vitess, Citus), cold/analytical in the warehouse. Or use a wide-column store (Cassandra, ScyllaDB) for the interaction tables.

**Failure modes.** Hot authors: a celebrity's posts dominate the `posts` table — need to shard or use a feed-generation cache. Vanity metrics drift: like counts become approximate after a threshold. Soft-deletes bloat tables: archive deleted posts nightly.

## 3. Best optimized solution

**Refined architecture.**

```
[OLTP: Vitess-sharded MySQL]  -- hot interactions, last 30 days
        │
        ├──CDC (Debezium)──> Kafka ──> [Warehouse: Snowflake]
        │                                    │
[Wide-column: Cassandra]   <──async writes──┤
  (impressions, likes)                       v
                                        [Aggregates + ML features]
```

**Storage choices by access pattern.**
- **Postgres/Vitess**: posts, users, comments — strong consistency, joins, moderate volume.
- **Cassandra**: impressions and likes — write-heavy, simple access patterns, time-series-shaped.
- **Object store (S3) + Iceberg**: media files, archived data, ML training tables.
- **Redis**: counters, "did I like this?", feed caches.

**Partitioning/sharding.**
- Shard `posts` and `comments` by `author_id` (each user's data on one shard — keeps queries local).
- Shard `interactions` by `post_id` (analytics by post is the dominant access pattern).
- Impressions: partition by `seen_at` weekly, drop after 1 year.

**Indexes that actually matter.**
- `(author_id, created_at DESC)` on posts — feed generation.
- `(post_id)` on likes and comments — count and display.
- `(user_id, seen_at DESC)` on impressions — "what did I see today".

**Polymorphic alternatives considered.** We rejected a single wide `posts` table (too many NULLs, schema changes break everything) and a fully normalized `post_text` / `post_image` / `post_video` split (too many joins). The base + media table hits the sweet spot.

**Why it's optimal.**
- Sharding by access pattern keeps hot reads/writes on one shard — feed generation stays sub-100ms.
- Polymorphic content model scales to new types (polls, live streams) without schema rewrites.
- CDC into a warehouse means the OLTP path is fast and the analytics path is decoupled — you can rebuild any aggregate.
- Soft-deletes + moderation columns live on the same row, so takedowns are atomic.

**What the interviewer is really testing:** They want to see you model polymorphic content cleanly (this trips up a lot of candidates), treat interactions as fact tables, and reason about scale. Meta specifically looks for: shares as new posts, impression tracking, soft-delete for moderation, and the realization that the OLTP schema doesn't survive at Facebook scale — you need sharding or a separate analytics store.
