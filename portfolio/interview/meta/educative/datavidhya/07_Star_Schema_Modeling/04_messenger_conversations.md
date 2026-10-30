# Messenger Conversations Fact + User Dim

## Problem
Meta Messenger handles billions of conversations per day across 1:1
chats, groups, rooms, and broadcast channels. The data model must
support analytics on conversation activity (length, participants,
message volume) and message-level analytics (sentiment, language,
attachments). Participants form a many-to-many relationship with
conversations.

## How to Think
1. List the metrics:
   - Active conversations per day / week.
   - Messages per conversation, average response time.
   - Participant growth in groups.
   - Language distribution and sentiment.
2. Identify the grains - one row = one:
   - Message sent.
   - Conversation thread.
   - (User, conversation) pair - bridge table.
3. Pick fact-table types:
   - `fact_message` -> transactional snapshot.
   - `fact_conversation` -> accumulating snapshot (created -> last
     message -> closed).
4. Design dimensions and SCD choices:
   - `dim_user` SCD2 - demographics, location, language shift.
   - `dim_conversation_type` SCD1 lookup.

## How to Remember
- **Pattern**: "Message fact + Conversation accumulating snapshot + bridge."
- **Grain mnemonic**: "One row = one message OR one conversation."
- Never model participants as a comma-separated column - use a bridge.

## Schema (DDL)
```sql
CREATE TABLE fact_message (
  message_key BIGINT PRIMARY KEY,
  conversation_key BIGINT, sender_key BIGINT,
  date_key INT, time_key INT,
  message_length INT, has_attachment BOOLEAN,
  attachment_type VARCHAR(20),
  is_reaction BOOLEAN, is_unsend BOOLEAN,
  is_first_in_thread BOOLEAN,
  language VARCHAR(10), sentiment_score DECIMAL(5,4)
);

CREATE TABLE fact_conversation (
  conversation_key BIGINT PRIMARY KEY,
  conversation_id VARCHAR(64),
  conversation_type VARCHAR(20),
  created_date_key INT, last_message_date_key INT,
  closed_date_key INT,
  participant_count INT, message_count INT,
  is_active BOOLEAN
);

CREATE TABLE bridge_conversation_participant (
  conversation_key BIGINT, user_key BIGINT,
  joined_date_key INT, left_date_key INT,
  role VARCHAR(20), is_muted BOOLEAN,
  PRIMARY KEY (conversation_key, user_key)
);
```

## Common Mistakes
- Storing participants in a comma-separated column on `fact_conversation`
  (breaks SCD and queries).
- Using only the message fact and aggregating conversations on the fly
  - slow for active-conversation dashboards.
- Forgetting `is_unsend` flag - sent-message counts become unreliable.

## AI Use Cases
- Smart Reply NLU trained on `fact_message` text + sentiment.
- Predict user re-engagement from conversation inactivity gaps.
- Spam / abuse detection via unusual send-rate per sender.
