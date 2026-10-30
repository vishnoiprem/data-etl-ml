"""
Problem 06: Facebook Groups Health
Meta product: "Facebook Groups - Group Health & Admin Analytics"

How to Think:
- Three related metrics: posts per group, members per group, activity
  (comments/reactions) per post.
- One grain per fact: (1) fact_group_post, (2) bridge_group_member
  with snapshot rows, (3) fact_post_engagement.
- Member count over time is a periodic snapshot fact, not a dim attribute.

How to Remember:
- Group membership is many-to-many - bridge table, not a column.
- Member count is a measure (fact), not a group attribute (dim).
- Activity is per-post, not per-group, to enable post-level analysis.

AI Use Cases
- Recommend groups to users based on interest embeddings.
- Predict group churn (declining posts + member drop).
- Detect toxic groups via negative reaction ratio.
"""

DDL = """
-- fact_group_post: one row per post published in a group
CREATE TABLE fact_group_post (
  group_post_key     BIGINT PRIMARY KEY,
  group_key          BIGINT NOT NULL,
  author_key         BIGINT NOT NULL,
  date_key           INT    NOT NULL,
  time_key           INT,
  post_id            VARCHAR(64),
  post_type          VARCHAR(20),            -- text / photo / poll / video
  has_tag            BOOLEAN,
  is_pinned          BOOLEAN,
  is_announcement    BOOLEAN,
  comment_count      INT DEFAULT 0,
  reaction_count     INT DEFAULT 0,
  share_count        INT DEFAULT 0
);

-- fact_group_member_snapshot: periodic snapshot - one row per (group, member, day)
CREATE TABLE fact_group_member_snapshot (
  snapshot_key       BIGINT PRIMARY KEY,
  group_key          BIGINT NOT NULL,
  user_key           BIGINT NOT NULL,
  date_key           INT    NOT NULL,        -- snapshot_date
  join_date_key      INT,
  member_role        VARCHAR(20),            -- admin / moderator / member
  is_active_30d      BOOLEAN,
  post_count_30d     INT,
  comment_count_30d  INT
);

-- fact_post_engagement: one row per reaction/comment on a group post
CREATE TABLE fact_post_engagement (
  engagement_key     BIGINT PRIMARY KEY,
  group_post_key     BIGINT NOT NULL,
  actor_key          BIGINT NOT NULL,
  date_key           INT    NOT NULL,
  reaction_type      VARCHAR(20),
  is_comment         BOOLEAN,
  comment_length     INT,
  sentiment_score    DECIMAL(5,4)
);

-- dim_group (SCD2 - privacy, name, description change)
CREATE TABLE dim_group (
  group_key          BIGINT PRIMARY KEY,
  group_id           VARCHAR(64),
  group_name         VARCHAR(200),
  privacy_type       VARCHAR(20),            -- public / closed / secret
  category           VARCHAR(100),
  member_count_current INT,
  created_date_key   INT,
  effective_from     DATE, effective_to DATE, is_current BOOLEAN
);
"""