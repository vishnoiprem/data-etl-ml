"""
Q22: Social Media Platform   [Medium | Data Model — OLTP relational]
Tags: Many-to-Many

Core database for a social platform: users, posts, relationships, engagement.

THE QUESTION IS ABOUT MANY-TO-MANY. There are three different kinds here and
they need three different structures. Conflating them is the failure mode.

  1. DIRECTED, self-referencing  -> follows(follower_id, followee_id)
     I can follow you without you following me. Two rows for a mutual follow.

  2. UNDIRECTED, self-referencing -> friendship(user_a_id, user_b_id)
     Friendship is symmetric, so it must be stored EXACTLY ONCE. Enforce a
     canonical ordering with CHECK (user_a_id < user_b_id). Without it you get
     both (1,2) and (2,1), every count doubles, and no constraint can save you.
     The cost: every read must look in BOTH columns (UNION ALL flipped).

  3. USER x POST engagement -> reaction(user_id, post_id)
     Composite PK gives you "one reaction per user per post" for free.

POSTS AND COMMENTS — the real decision:
  Model comments as posts with a nullable parent_post_id (self-referencing
  hierarchy), rather than a separate comments table.
    + one ranking/moderation/delete path for all content
    + arbitrary nesting depth for free
    - recursive queries to fetch a thread; no FK-level guarantee that a
      top-level post cannot become someone's reply
  A separate `comments` table is also defensible IF comments can never nest and
  never need post-level features. Say the trade-off; do not just pick one.

WHAT AN INTERVIEWER WILL PUSH ON — feed reads:
  This schema is correct for WRITES and wrong for feed READS at scale. Building
  a feed means "posts from everyone I follow, ranked" — a join across follows
  and posts over billions of rows, per page load. Real answer: fan-out-on-write
  into a per-user materialised feed table, or a hybrid (fan-out-on-write for
  normal users, fan-out-on-read for celebrity accounts whose fan-out would be
  hundreds of millions of rows). Raising this unprompted is the senior signal.
"""
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("22-model-social-media-platform")
         .master("local[2]")
         .config("spark.sql.shuffle.partitions", "2")
         .config("spark.ui.showConsoleProgress", "false")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")


def expect(title, sql, expected_rows):
    """Run a query and assert its exact rows, in order. Decimal/float safe."""
    import decimal

    def norm(v):
        if isinstance(v, decimal.Decimal):
            return float(v)
        if isinstance(v, float):
            return round(v, 6)
        return v

    got = [tuple(norm(c) for c in r) for r in spark.sql(sql).collect()]
    exp = [tuple(norm(c) for c in r) for r in expected_rows]
    if got != exp:
        print(f"[FAIL] {title}")
        print(f"   expected: {exp}")
        print(f"   got:      {got}")
        raise AssertionError(title)
    print(f"[PASS] {title}")
    return got



DDL = """
CREATE TABLE users (
  user_id     BIGINT,        -- PK
  handle      VARCHAR(40),   -- UNIQUE
  created_at  TIMESTAMP
);

-- Self-referencing hierarchy: parent_post_id NULL = top-level post.
CREATE TABLE post (
  post_id        BIGINT,     -- PK
  author_id      BIGINT,     -- FK users
  parent_post_id BIGINT,     -- FK post (nullable) -> replies/comments
  content        STRING,
  created_at     TIMESTAMP
);

-- DIRECTED m:n. PK (follower_id, followee_id). CHECK (follower <> followee).
CREATE TABLE follows (
  follower_id  BIGINT,       -- FK users
  followee_id  BIGINT,       -- FK users
  created_at   TIMESTAMP
);

-- UNDIRECTED m:n, stored ONCE. PK (user_a_id, user_b_id).
-- CHECK (user_a_id < user_b_id)  <-- the constraint that makes this correct
CREATE TABLE friendship (
  user_a_id  BIGINT,         -- FK users
  user_b_id  BIGINT,         -- FK users
  status     VARCHAR(10),    -- CHECK IN ('pending','accepted','blocked')
  created_at TIMESTAMP
);

-- USER x POST. PK (user_id, post_id) => one reaction per user per post.
CREATE TABLE reaction (
  user_id       BIGINT,      -- FK users
  post_id       BIGINT,      -- FK post
  reaction_type VARCHAR(10), -- like/love/haha/wow/sad/angry
  created_at    TIMESTAMP
);
"""

spark.createDataFrame([
    (1, 2), (1, 3), (2, 1), (3, 1), (4, 1),
], ["follower_id", "followee_id"]).createOrReplaceTempView("follows")

# Canonical order maintained: user_a_id < user_b_id in every row.
spark.createDataFrame([
    (1, 2, "accepted"), (1, 3, "accepted"), (2, 3, "accepted"),
    (3, 4, "accepted"), (1, 5, "pending"),
], ["user_a_id", "user_b_id", "status"]).createOrReplaceTempView("friendship")

spark.createDataFrame([
    (1, 1, None), (2, 1, None), (3, 2, None), (4, 2, 1),
], ["post_id", "author_id", "parent_post_id"]).createOrReplaceTempView("post")

spark.createDataFrame([
    (2, 1, "like"), (3, 1, "love"), (4, 1, "like"), (1, 3, "like"),
], ["user_id", "post_id", "reaction_type"]).createOrReplaceTempView("reaction")

# 1. DIRECTED: follower counts read one column only. No flip needed.
expect("Q22 follower counts (directed)", """
SELECT followee_id, COUNT(*) AS followers
FROM follows GROUP BY followee_id ORDER BY followee_id
""", [(1, 3), (2, 1), (3, 1)])

# 2. UNDIRECTED: must read BOTH columns. This is the price of storing once.
expect("Q22 friend counts (undirected, both directions)", """
WITH both_ways AS (
    SELECT user_a_id AS user_id, user_b_id AS friend_id
    FROM friendship WHERE status = 'accepted'
    UNION ALL
    SELECT user_b_id AS user_id, user_a_id AS friend_id
    FROM friendship WHERE status = 'accepted'
)
SELECT user_id, COUNT(DISTINCT friend_id) AS friends
FROM both_ways GROUP BY user_id ORDER BY user_id
""", [(1, 2), (2, 2), (3, 3), (4, 1)])

# The WRONG version, asserted. Grouping by user_a_id alone counts only
# friendships you happened to initiate. User 3 reports 1 friend instead of 3.
expect("Q22 WRONG: single-column group-by undercounts", """
SELECT user_a_id AS user_id, COUNT(*) AS friends
FROM friendship WHERE status = 'accepted'
GROUP BY user_a_id ORDER BY user_a_id
""", [(1, 2), (2, 1), (3, 1)])

# 3. Mutual friends — the classic self-join on the normalised relation.
expect("Q22 mutual friends of user 1 and user 2", """
WITH both_ways AS (
    SELECT user_a_id AS user_id, user_b_id AS friend_id
    FROM friendship WHERE status = 'accepted'
    UNION ALL
    SELECT user_b_id AS user_id, user_a_id AS friend_id
    FROM friendship WHERE status = 'accepted'
)
SELECT a.friend_id AS mutual_friend
FROM both_ways a
JOIN both_ways b ON b.friend_id = a.friend_id
WHERE a.user_id = 1 AND b.user_id = 2
  AND a.friend_id NOT IN (1, 2)
ORDER BY mutual_friend
""", [(3,)])

# 4. Engagement per post. LEFT JOINs so zero-engagement posts still appear —
#    a post with no reactions is a product signal, not a row to drop.
expect("Q22 engagement per post (reactions + replies)", """
SELECT p.post_id,
       COUNT(DISTINCT r.user_id) AS reactions,
       COUNT(DISTINCT c.post_id) AS replies
FROM post p
LEFT JOIN reaction r ON r.post_id = p.post_id
LEFT JOIN post c     ON c.parent_post_id = p.post_id
GROUP BY p.post_id
ORDER BY p.post_id
""", [(1, 3, 1), (2, 0, 0), (3, 1, 0), (4, 0, 0)])

# ---- MySQL way ----------------------------------------------------------
# DDL-only. Translate the three many-to-many relationships explicitly:
# follows is DIRECTED (composite PK), friendship is UNDIRECTED with a
# canonical-order CHECK (user_a_id < user_b_id), reactions are user x post.
# Spark's STRING -> JSON; BOOLEAN -> TINYINT(1). Add real FK constraints and
# useful indexes (follower_id and followee_id get separate indexes because
# fan-out reads hit both directions). Two example dimension inserts:
#
# CREATE TABLE users (
#     user_id    BIGINT       NOT NULL AUTO_INCREMENT,
#     handle     VARCHAR(40)  NOT NULL,
#     created_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
#     PRIMARY KEY (user_id),
#     UNIQUE KEY uq_users_handle (handle)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE posts (
#     post_id      BIGINT      NOT NULL AUTO_INCREMENT,
#     author_id    BIGINT      NOT NULL,
#     parent_post_id BIGINT    NULL,        -- self-referencing for comment threads
#     body         TEXT        NOT NULL,
#     created_at   TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
#     PRIMARY KEY (post_id),
#     KEY ix_posts_author      (author_id, created_at DESC),
#     KEY ix_posts_parent      (parent_post_id),
#     CONSTRAINT fk_posts_author FOREIGN KEY (author_id)      REFERENCES users(user_id),
#     CONSTRAINT fk_posts_parent FOREIGN KEY (parent_post_id) REFERENCES posts(post_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE follows (
#     follower_id BIGINT NOT NULL,
#     followee_id BIGINT NOT NULL,
#     created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
#     PRIMARY KEY (follower_id, followee_id),
#     KEY ix_follows_followee (followee_id),
#     CONSTRAINT chk_follows_not_self CHECK (follower_id <> followee_id),
#     CONSTRAINT fk_follows_follower FOREIGN KEY (follower_id) REFERENCES users(user_id),
#     CONSTRAINT fk_follows_followee FOREIGN KEY (followee_id) REFERENCES users(user_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE friendship (
#     user_a_id BIGINT NOT NULL,
#     user_b_id BIGINT NOT NULL,
#     created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
#     PRIMARY KEY (user_a_id, user_b_id),
#     KEY ix_friend_b (user_b_id),
#     CONSTRAINT chk_friend_canonical CHECK (user_a_id < user_b_id),
#     CONSTRAINT fk_friend_a FOREIGN KEY (user_a_id) REFERENCES users(user_id),
#     CONSTRAINT fk_friend_b FOREIGN KEY (user_b_id) REFERENCES users(user_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE reaction (
#     user_id    BIGINT    NOT NULL,
#     post_id    BIGINT    NOT NULL,
#     kind       VARCHAR(16) NOT NULL DEFAULT 'like',
#     created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
#     PRIMARY KEY (user_id, post_id),
#     KEY ix_reaction_post (post_id),
#     CONSTRAINT fk_reaction_user FOREIGN KEY (user_id) REFERENCES users(user_id),
#     CONSTRAINT fk_reaction_post FOREIGN KEY (post_id) REFERENCES posts(post_id)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
#
# -- Example dimension rows. Real users/posts/etc. would be inserted by the
# -- application; the schema itself only needs the seed.
# INSERT INTO users (user_id, handle) VALUES (1, 'alice'), (2, 'bob'), (3, 'carol');
# INSERT INTO follows (follower_id, followee_id) VALUES (1, 2), (1, 3), (2, 3);
