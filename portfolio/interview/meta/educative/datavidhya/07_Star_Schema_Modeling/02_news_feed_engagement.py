"""
Problem 02: News Feed Engagement Analytics
Meta product: "Facebook News Feed - Engagement Insights"

How to Think:
- One grain: one impression-event (a post shown to a user in a feed session).
- Reactions and shares are separate event facts - they can also be modeled
  as metrics on the impression fact with flags, OR as their own fact table.
- We pick: one consolidated engagement fact with reaction type and a
  flag for share - keeps joins simple for BI.

How to Remember:
- Engagement facts are typically transactional (event-grain) and very
  high volume - prefer narrow rows and aggregations at query time.
- Keep author_key and viewer_key as separate FKs to enable two-sided
  analytics (creator view and consumer view).

AI Use Cases
- Personalize News Feed ranking (engagement likelihood per post).
- Detect low-quality / clickbait content via reaction mix.
- Predict viral posts early from velocity of shares.
"""

DDL = """
-- fact_feed_engagement: one row per impression event with reaction outcome
CREATE TABLE fact_feed_engagement (
  engagement_key     BIGINT PRIMARY KEY,
  post_key           BIGINT NOT NULL,         -- dim_post
  viewer_key         BIGINT NOT NULL,         -- dim_user (consumer)
  author_key         BIGINT NOT NULL,         -- dim_user (creator)
  date_key           INT    NOT NULL,
  time_key           INT    NOT NULL,
  surface_key        BIGINT NOT NULL,         -- News Feed vs Groups vs Search
  rank_position      INT,                     -- position in feed
  impression_id      VARCHAR(64),
  reaction_type      VARCHAR(20),             -- like / love / wow / angry / null
  is_reaction        BOOLEAN,
  is_share           BOOLEAN,
  is_hide            BOOLEAN,
  is_comment         BOOLEAN,
  dwell_time_ms      INT,
  FOREIGN KEY (post_key)   REFERENCES dim_post(post_key),
  FOREIGN KEY (viewer_key) REFERENCES dim_user(user_key),
  FOREIGN KEY (author_key) REFERENCES dim_user(user_key)
);

-- dim_post (SCD2 - posts are edited frequently)
CREATE TABLE dim_post (
  post_key           BIGINT PRIMARY KEY,
  post_id            VARCHAR(64),
  author_key         BIGINT,
  post_type          VARCHAR(20),             -- text / photo / video / link
  language           VARCHAR(10),
  created_at         TIMESTAMP,
  effective_from     DATE,
  effective_to       DATE,
  is_current         BOOLEAN
);

-- dim_user (SCD2 - age, city, interests change)
CREATE TABLE dim_user (
  user_key           BIGINT PRIMARY KEY,
  user_id            VARCHAR(64),
  age_band           VARCHAR(10),
  gender             VARCHAR(10),
  country            VARCHAR(50),
  city               VARCHAR(50),
  tenure_days        INT,
  effective_from     DATE,
  effective_to       DATE,
  is_current         BOOLEAN
);

-- dim_surface (SCD1 - small lookup)
CREATE TABLE dim_surface (
  surface_key        BIGINT PRIMARY KEY,
  surface_name       VARCHAR(50)              -- 'newsfeed', 'groups', 'search'
);

-- dim_date / dim_time (conformed)
CREATE TABLE dim_date (
  date_key INT PRIMARY KEY, full_date DATE,
  day_of_week VARCHAR(10), month INT, quarter INT, year INT
);

CREATE TABLE dim_time (
  time_key INT PRIMARY KEY, hour INT, minute INT,
  part_of_day VARCHAR(20)                    -- morning / afternoon / evening / night
);
"""