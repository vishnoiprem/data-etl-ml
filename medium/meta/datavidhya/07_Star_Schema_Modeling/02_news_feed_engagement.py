"""
Problem 02: News Feed Engagement Analytics
Meta product: "Facebook News Feed"

How to Think:
- Three events on each story shown in feed: impression (render), reaction (like/love/...), share.
- Each is its own grain; reactions are 1 per (user, post, reaction_type) but share is 1 per share.
- A "feed_engagement_daily" periodic fact helps measure reach vs interaction.
- Conformed dims: dim_post, dim_user, dim_date.

How to Remember:
- "One impression is not one reaction." Split into three transactional facts or use
  one fact with multiple flags + counts. Trade-off: row count vs query flexibility.
- Share is rarer than reaction; modeling it separately keeps fan-out smaller.

AI Use Cases:
- Predict post virality from early impression-to-share rate.
- Recommend friends/pages by reaction co-occurrence.
- Detect engagement-bait posts (high share, low dwell).
"""

DDL = """
-- Grain: one row per post impression to a viewer.
CREATE TABLE fact_post_impression (
  impression_key     BIGINT,
  post_key          BIGINT,
  viewer_user_key    BIGINT,
  author_user_key    BIGINT,
  date_key           INT,
  time_key           INT,
  device_key         INT,
  placement_key      INT,        -- top_of_feed / inline / etc.
  is_video           BOOLEAN,
  dwell_ms           INT
);

-- Grain: one row per reaction (user reacted to a post with a reaction type).
CREATE TABLE fact_post_reaction (
  reaction_key       BIGINT,
  post_key           BIGINT,
  reactor_user_key   BIGINT,
  author_user_key    BIGINT,
  reaction_type_key  INT,        -- like / love / haha / wow / sad / angry
  reaction_date_key  INT,
  device_key         INT
);

-- Grain: one row per share event.
CREATE TABLE fact_post_share (
  share_key          BIGINT,
  post_key           BIGINT,
  sharer_user_key    BIGINT,
  author_user_key    BIGINT,
  share_destination_key INT,     -- own_timeline / group / DM / external
  share_date_key     INT
);

-- Conformed dims
CREATE TABLE dim_post (
  post_key           BIGINT,
  post_id            VARCHAR(40),
  author_user_key    BIGINT,
  post_type          VARCHAR(20),   -- text / photo / video / link
  page_or_profile    VARCHAR(20),
  effective_from     DATE,
  effective_to       DATE,
  is_current         BOOLEAN
);

CREATE TABLE dim_user (
  user_key           BIGINT,
  user_id            VARCHAR(40),
  age_bucket         VARCHAR(10),
  gender             VARCHAR(10),
  country            VARCHAR(60),
  locale             VARCHAR(20),
  tenure_days        INT,
  effective_from     DATE,
  effective_to       DATE,
  is_current         BOOLEAN
);

CREATE TABLE dim_reaction_type ( reaction_type_key INT, reaction_name VARCHAR(20), is_positive BOOLEAN );
CREATE TABLE dim_device ( device_key INT, device_type VARCHAR(20), os VARCHAR(20), browser VARCHAR(20) );
CREATE TABLE dim_date ( date_key INT PRIMARY KEY, full_date DATE, day_of_week VARCHAR(10), month INT, quarter INT, year INT );
"""