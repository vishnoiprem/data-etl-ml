# Bridge / Factless Tables for Many-to-Many

## Problem
User-group membership at Facebook is many-to-many: a user can join
many groups, and each group has many users. We must support:
- "How many users were active in group X today?"
- "When did user Y join group Z? Are they still in?"
- "Which groups does user A belong to right now?"
A simple fact table cannot hold a multi-valued dimension, and a
single dim side does not work either. We need a bridge table plus
a factless fact for activity.

## How to Think
1. List the metrics:
   - Active members per group per day (factless fact).
   - Membership joins / leaves over time (bridge effective dates).
   - Members by role, invitation source, notification level.
2. Identify the grains:
   - Bridge: one row per (user, group, joined_date) - SCD2 history.
   - Factless fact: one row per (user, group, date) of active membership.
3. Pick fact-table type:
   - Bridge = bridge table (not a fact).
   - Factless fact = transactional snapshot with no measures.
4. Design dimensions:
   - `dim_user` SCD2, `dim_group` SCD2.

## How to Remember
- **Pattern**: "Bridge for M:N with effective dates + factless for
  daily activity."
- **Grain mnemonic**:
  - Bridge: "One row = one (user, group) membership period."
  - Factless: "One row = one (user, group, day) active day."
- Factless fact's existence IS the metric - no measures needed.

## Schema (DDL)
```sql
CREATE TABLE bridge_user_group (
  user_key BIGINT, group_key BIGINT,
  joined_date_key INT, left_date_key INT,
  member_role VARCHAR(20),
  invitation_source VARCHAR(30),
  is_muted BOOLEAN, notification_level VARCHAR(20),
  PRIMARY KEY (user_key, group_key, joined_date_key)
);

CREATE TABLE fact_user_group_active (
  activity_key BIGINT PRIMARY KEY,
  user_key BIGINT, group_key BIGINT, date_key INT,
  is_active BOOLEAN DEFAULT TRUE,
  PRIMARY KEY (user_key, group_key, date_key)
);

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
```

## Common Mistakes
- Modeling membership as a column on `dim_user` (violates 1NF).
- Using a comma-separated list of group_ids on `dim_user`.
- Confusing bridge with factless fact - bridge captures the
  relationship; factless captures daily activity.

## AI Use Cases
- Group recommendation from overlapping memberships.
- Churn prediction from membership inactivity gaps.
- Spam-network detection via dense group-clique analysis.
