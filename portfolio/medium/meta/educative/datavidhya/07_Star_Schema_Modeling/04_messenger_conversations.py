"""
Problem 04: Messenger Conversations Fact + User Dim
Meta product: "Meta Messenger - Conversation Analytics"

How to Think:
- Conversation grain: one row per conversation thread (1:1 or group).
- Message grain: one row per message - separate fact for engagement depth.
- A group conversation has multiple participants - handled via bridge
  table `bridge_conversation_participant` (many-to-many).
- Two facts share the same dims: date, user, conversation_type.

How to Remember:
- Conversations = accumulating snapshot (start, last_message, status).
- Messages = transactional snapshot (event-grain).
- Participants require a bridge, not a flag column.

AI Use Cases
- Smart replies / NLU training on the message fact.
- Predict conversation churn / user re-engagement likelihood.
- Detect spam and abuse patterns via message rate per sender.
"""

DDL = """
-- fact_message: one row per message sent
CREATE TABLE fact_message (
  message_key        BIGINT PRIMARY KEY,
  conversation_key   BIGINT NOT NULL,
  sender_key         BIGINT NOT NULL,        -- dim_user
  date_key           INT    NOT NULL,
  time_key           INT,
  message_id         VARCHAR(64),
  message_length     INT,
  has_attachment     BOOLEAN,
  attachment_type    VARCHAR(20),            -- image / video / file / audio
  is_reaction        BOOLEAN,
  is_unsend          BOOLEAN,
  is_first_in_thread BOOLEAN,
  language           VARCHAR(10),
  sentiment_score    DECIMAL(5,4)
);

-- fact_conversation: one row per conversation thread (accumulating snapshot)
CREATE TABLE fact_conversation (
  conversation_key      BIGINT PRIMARY KEY,
  conversation_id       VARCHAR(64),
  conversation_type     VARCHAR(20),         -- '1to1' or 'group'
  created_date_key      INT,
  created_time_key      INT,
  last_message_date_key INT,
  last_message_time_key INT,
  closed_date_key       INT,                 -- NULL while active
  participant_count     INT,
  message_count         INT,
  is_active             BOOLEAN,
  last_message_sender_key BIGINT
);

-- bridge: many-to-many between conversation and user
CREATE TABLE bridge_conversation_participant (
  conversation_key BIGINT NOT NULL,
  user_key         BIGINT NOT NULL,
  joined_date_key  INT,
  left_date_key    INT,                     -- NULL = still in
  role             VARCHAR(20),             -- 'admin','member'
  is_muted         BOOLEAN,
  PRIMARY KEY (conversation_key, user_key)
);

-- dim_user (SCD2)
CREATE TABLE dim_user (
  user_key       BIGINT PRIMARY KEY,
  user_id        VARCHAR(64),
  country        VARCHAR(50),
  age_band       VARCHAR(10),
  language       VARCHAR(10),
  effective_from DATE, effective_to DATE, is_current BOOLEAN
);

-- dim_conversation_type (SCD1 - lookup)
CREATE TABLE dim_conversation_type (
  type_key     BIGINT PRIMARY KEY,
  type_name    VARCHAR(20)                  -- '1to1','group','room','channel'
);
"""