# Facebook Groups Health

## Problem
Facebook Groups is a community product with public, closed, and
secret groups. Admins need to see posts per group, member growth,
and engagement health (reactions, comments, sentiment). The schema
must support "is this group healthy?" KPIs and ML signals for
group recommendations.

## How to Think
1. List the metrics:
   - Posts per group per day / week.
   - Active members (posted or commented in last 30 days).
   - Reaction distribution and comment sentiment.
   - Member growth rate.
2. Identify the grains - one row = one:
   - Group post.
   - (Group, member, day) snapshot.
   - Reaction/comment event on a group post.
3. Pick fact-table types:
   - `fact_group_post` -> transactional snapshot.
   - `fact_group_member_snapshot` -> periodic snapshot (daily roll-up
     of member activity).
   - `fact_post_engagement` -> transactional snapshot.
4. Design dimensions and SCD choices:
   - `dim_group` SCD2 (privacy changes, name updates).
   - `dim_user` (shared conformed dim).

## How to Remember
- **Pattern**: "Three facts at three grains + SCD2 group dim."
- **Grain mnemonic**: "One row = one post, one snapshot, one engagement."
- Member count is a measure, not a dim attribute - it changes daily.

## Schema (DDL)
```sql
CREATE TABLE fact_group_post (
  group_post_key BIGINT PRIMARY KEY,
  group_key BIGINT, author_key BIGINT,
  date_key INT, time_key INT,
  post_type VARCHAR(20),
  comment_count INT, reaction_count INT, share_count INT
);

CREATE TABLE fact_group_member_snapshot (
  snapshot_key BIGINT PRIMARY KEY,
  group_key BIGINT, user_key BIGINT,
  date_key INT,                          -- snapshot date
  join_date_key INT,
  member_role VARCHAR(20),
  is_active_30d BOOLEAN,
  post_count_30d INT, comment_count_30d INT
);

CREATE TABLE fact_post_engagement (
  engagement_key BIGINT PRIMARY KEY,
  group_post_key BIGINT, actor_key BIGINT,
  date_key INT,
  reaction_type VARCHAR(20),
  is_comment BOOLEAN, comment_length INT,
  sentiment_score DECIMAL(5,4)
);

CREATE TABLE dim_group (
  group_key BIGINT PRIMARY KEY,
  group_id VARCHAR(64), group_name VARCHAR(200),
  privacy_type VARCHAR(20), category VARCHAR(100),
  effective_from DATE, effective_to DATE, is_current BOOLEAN
);
```

## Common Mistakes
- Treating member_count as a `dim_group` attribute (loses history).
- Modeling only at group grain and missing post-level engagement.
- Storing all members as a comma-separated column.

## AI Use Cases
- Group recommendations from user interest + group embeddings.
- Group churn prediction (drop in posts and active members).
- Toxic-group detection via negative reaction ratio.
