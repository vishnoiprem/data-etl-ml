# 26 — Facebook Messenger (1:1 Real-Time Chat)

> **Lesson 1 of 5 — Real-Time & Collaborative Systems**

A 1:1 chat service: two users hold a conversation, exchange messages in
near-real-time, and see each other's online/offline presence. Messages
are persisted so a user can read history when offline; presence is
ephemeral and driven by heartbeats.

---

## 1. Requirements

### Functional
- Create a conversation between two users.
- Send a message into a conversation (persisted, ordered by time).
- Fetch a message history for a conversation, optionally since a timestamp.
- Heartbeat-driven presence (online / offline) per user.
- Long-poll / SSE delivery of new messages to a connected user.

### Non-functional
- p99 send-to-deliver < 500 ms when both online.
- Messages durable across restarts.
- Presence TTL: a user with no heartbeat in 30s is considered offline.
- Idempotent message IDs (Snowflake) so retries do not duplicate.

### Out of scope
- Group chats (handled by `27_whatsapp`).
- Media attachments.
- Read receipts, typing indicators.

---

## 2. Capacity

| Metric | Value |
|---|---|
| Conversations | ~1B (toy: thousands) |
| Messages / day | ~10B (toy: thousands) |
| Avg message size | 200 bytes |
| Concurrent online users | ~100M |
| Heartbeat QPS | ~1M peak |

---

## 3. High-level

```
[client A] ──POST /messages──► [API] ──persist──► [Message store]
                              │     │
                              │     └─► [Inbox of user B]   (per-user list)
                              │
[client B] ──GET /messages?since=…──► [API] ──read──► [Message store]
                              │
                              └─► [SSE / long-poll]  ◄── pushed on new msg

[any client] ──POST /heartbeat──► [Presence store (TTL)]
            ──GET  /presence───►
```

Two key ideas:

- **Per-user inbox index.** Reads are always "give me the new messages for
  *me*". We materialize `inbox:<user_id> = [msg_id, ...]` so a 1:1 conversation
  fan-out is two writes (one per participant) and a read is a single inbox scan.
- **Ephemeral presence.** A heartbeat bumps a TTL key. A user is online
  iff their key exists. No durable presence log.

---

## 4. API

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/api/conversations` | `{"user_a", "user_b"}` | `{"conversation_id", ...}` |
| `POST` | `/api/conversations/<id>/messages` | `{"sender_id", "body"}` | `{"message_id", "ts", "conversation_id"}` |
| `GET`  | `/api/conversations/<id>/messages?since_ts=` | — | `{"messages": [...]}` |
| `POST` | `/api/users/<id>/heartbeat` | — | `{"user_id", "online": true, "ttl": 30}` |
| `GET`  | `/api/users/<id>/presence` | — | `{"user_id", "online": bool, "last_seen": ts}` |
| `GET`  | `/api/users/<id>/stream` | — | **SSE** of new messages |
| `GET`  | `/health`, `/metrics` | — | ops |

---

## 5. Data model

| Key | Value |
|---|---|
| `conv:<id>` | `{conversation_id, user_a, user_b, created_at}` |
| `msg:<id>` | `{message_id, conversation_id, sender_id, body, ts}` |
| `conv_msgs:<conv_id>` | ordered list of `message_id` (append-only) |
| `inbox:<user_id>` | ordered list of `message_id` (capped) |
| `presence:<user_id>` | `{"last_seen": ts}` (TTL: 30s) |

Snowflake IDs let us use the timestamp embedded in the ID for ordering,
which is convenient and avoids a separate clock dependency.

---

## 6. Read / Write paths

**Send:**
1. Generate Snowflake `message_id`.
2. Persist `msg:<id>`.
3. Append to `conv_msgs:<conv_id>`.
4. Append to `inbox:<user_a>` and `inbox:<user_b>`.
5. Notify any active SSE listener.

**Fetch since_ts:** scan `conv_msgs:<conv_id>`; return where `ts > since_ts`.

**Stream:** SSE — open a queue, register against `user_id`, emit on every
message addressed to that user, deregister on disconnect.

**Heartbeat:** write `presence:<user_id>` with 30s TTL.

---

## 7. Failure modes

- **API node dies** mid-send — message is durably written before ack;
  retry is safe because message_id is client-provided (or generated on
  the server and treated as idempotent for the same conversation+ts).
- **Presence stale** — TTL guarantees garbage collection; if the API
  layer is partitioned, the user simply appears offline.
- **SSE backpressure** — slow clients are dropped, presence is restored
  on reconnect via `since_ts`.

---

## 8. Tradeoffs

- **Per-user inbox** (chosen) vs. per-conversation read. Inbox wins for
  unread badges and multi-device sync; loses on storage amplification
  (each message copied N times for N participants — fine for 1:1).
- **SSE** vs. WebSockets. SSE is one-way (server→client) and works over
  HTTP/1.1, perfect for delivery. WebSockets add duplex complexity we
  don't need for 1:1.
- **30s heartbeat** is the WhatsApp/Messenger default — balances battery
  and "live" feel. A real prod system uses adaptive intervals based on
  app foreground state.

---

## 9. Code map

| File | Purpose |
|---|---|
| `code/service.py` | `MessengerService`: conversations, messages, inboxes, presence, fan-out. |
| `code/app.py` | Flask HTTP API, SSE stream endpoint, metrics. |
| `tests/test_service.py` | Conversation lifecycle, send/receive, inbox fan-out, presence, ordering. |
| `tests/test_app.py` | HTTP smoke + SSE subscribe. |
