"""
Problem 10: Bridge / Factless Tables for Many-to-Many
Meta product: "Facebook Groups - User Membership Analytics"

How to Think:
- Factless fact table: a "fact" with only foreign keys and no measures -
  used to record an event that has no numeric metric (e.g., "user was
  in group on this day", "student attended class").
- Bridge table: many-to-many between two entities (user-group
  membership, user-page likes) with effective dates.
- In Meta, user-group membership is the canonical example: a user can
  belong to many groups, a group has many users.

How to Remember:
- Factless fact = "it happened" record with only keys.
- Bridge = many-to-many with effective dating for history.
- A bridge with effective dates supports SCD analysis.

AI Use Cases
- Group recommendation from overlapping memberships.
- Predict user churn from membership inactivity.
- Detect spam networks via dense group-clique analysis.
"""

DDL = """
-- Factless fact: one row per (user, group, day) of active membership
CREATE TABLE fact_user_group_active (
  activity_key       BIGINT PRIMARY KEY,
  user_key           BIGINT NOT NULL,
  group_key          BIGINT NOT NULL,
  date_key           INT    NOT NULL,
  is_active          BOOLEAN DEFAULT TRUE,
  -- No measures. Its mere existence = "user was active in group today".
  PRIMARY KEY (user_key, group_key, date_key)
);

-- Bridge table: user-group membership with SCD2 effective dating
CREATE TABLE bridge_user_group (
  user_key           BIGINT NOT NULL,
  group_key          BIGINT NOT NULL,
  joined_date_key    INT    NOT NULL,
  left_date_key      INT,                 -- NULL = still a member
  member_role        VARCHAR(20),         -- 'admin','moderator','member'
  invitation_source  VARCHAR(30),         -- 'search','invite','suggested'
  is_muted           BOOLEAN,
  notification_level VARCHAR(20),
  PRIMARY KEY (user_key, group_key, joined_date_key)
);

-- dim_user (SCD2), dim_group (SCD2) - reused.
CREATE TABLE dim_user (
  user_key BIGINT PRIMARY KEY, user_id VARCHAR(64),
  country VARCHAR(50), age_band VARCHAR(10),
  effective_from DATE, effective_to DATE, is_current BOOLEAN
);

CREATE TABLE dim_group (
  group_key BIGINT PRIMARY KEY, group_id VARCHAR(64),
  group_name VARCHAR(200), privacy_type VARCHAR(20),
  category VARCHAR(100),
  effective_from DATE, effective_to DATE, is_current BOOLEAN
);

-- Query pattern:
-- SELECT g.group_name, COUNT(DISTINCT f.user_key) AS active_users
-- FROM fact_user_group_active f
-- JOIN dim_group g ON f.group_key = g.group_key AND g.is_current
-- WHERE f.date_key BETWEEN 20260901 AND 20260923
-- GROUP BY g.group_name;
"""