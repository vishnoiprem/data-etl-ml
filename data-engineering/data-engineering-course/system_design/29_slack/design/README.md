# 29 — Slack (Channels, Threads, Mentions, Search)

> **Lesson 4 of 5 — Real-Time & Collaborative Systems**

A workplace messaging platform: workspaces contain channels; messages
live in channels or in threads under a parent message; users can be
mentioned with `@user`; and a flat inverted index supports keyword
search across messages.

---

## 1. Requirements

### Functional
- Create a workspace.
- Create a channel inside a workspace.
- Post a message to a channel (optionally as a thread reply to a parent).
- Read a channel's message history.
- Read a thread (all replies under a parent).
- Parse `@mentions` from message bodies.
- Search messages by keyword (toy inverted index).

### Non-functional
- p99 send-to-channel < 200 ms.
- Threads must load with O(replies) regardless of channel size.
- Search is eventually consistent (we index on write).

### Out of scope
- Real-time push (we expose SSE for completeness, but tests don't require it).
- Reactions, file uploads, voice huddles.
- Workspace invites / permissions / RBAC.

---

## 2. Capacity

| Metric | Value |
|---|---|
| Workspaces | ~1M (toy: thousands) |
| Channels / workspace | median 20, max 5k |
| Messages / day | ~3B (toy: thousands) |
| Mentions / message | 0–10 typical |
| Search QPS | ~50k peak |

---

## 3. High-level

```
[client] ──POST /channels/<id>/messages──► [API]
                                            │
                       ┌────────────────────┼────────────────────┐
                       ▼                    ▼                    ▼
              [msg store]          [channel_msgs:<id>]    [thread:<parent>: [replies]]
                                            │
                       mentions: extract @user, push notification
                       index:     add terms to inverted index
                                          │
                                          ▼
                              [search index]    (term -> [msg_id])
```

Two storage shapes:

- **Channel feed**: `channel_msgs:<channel_id>` = `[msg_id]` (capped).
- **Thread replies**: `thread:<parent_id>` = `[msg_id]` (ordered by ts).
  Loading a thread does not need to scan the whole channel.

A simple in-memory **inverted index** maps `term -> [msg_id]`. We
tokenize on whitespace + lowercase + strip punctuation.

---

## 4. API

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/api/workspaces` | `{"name"}` | workspace record |
| `POST` | `/api/workspaces/<id>/channels` | `{"name", "creator_id"}` | channel record |
| `POST` | `/api/channels/<id>/messages` | `{"user_id", "body", "thread_to"?}` | message record |
| `GET`  | `/api/channels/<id>/messages?limit=&since_ts=` | — | message list |
| `GET`  | `/api/channels/<id>/threads/<msg_id>` | — | thread (parent + replies) |
| `GET`  | `/api/search?q=` | — | search results |
| `GET`  | `/health`, `/metrics` | — | ops |

---

## 5. Data model

| Key | Value |
|---|---|
| `ws:<id>` | `{workspace_id, name, created_at}` |
| `ch:<id>` | `{channel_id, workspace_id, name, creator_id, created_at}` |
| `msg:<id>` | `{message_id, channel_id, user_id, body, thread_to?, mentions: [uid], ts}` |
| `channel_msgs:<channel_id>` | `[message_id]` |
| `thread:<parent_id>` | `[message_id]` (replies) |
| `user_mentions:<user_id>` | `[message_id]` (for notifications) |
| `idx:<term>` | `[message_id]` (inverted index) |

---

## 6. Read / Write paths

**Send:**
1. Mint Snowflake id.
2. Parse body for `@\w+` mentions; resolve to user_ids (we treat any
   string after `@` as a user_id for the toy model).
3. Persist msg.
4. If `thread_to` is set, append to `thread:<parent_id>` (and verify
   the parent is a top-level message in the same channel).
5. Else append to `channel_msgs:<channel_id>`.
6. Index terms into `idx:<term>`.
7. Update `user_mentions:<uid>`.

**Search:** tokenize query; for each term, fetch `idx:<term>`, intersect
across terms, return up to N messages sorted by recency.

---

## 7. Failure modes

- **Index drift** — index write is best-effort; a periodic reindex can
  rebuild from the message log. Our toy model writes inline so drift
  is bounded by process lifetime.
- **Hot channel** — channel message lists are capped; old messages
  remain queryable via search (index) and per-message fetch.
- **Search miss on rare terms** — index entries are small lists; we
  cap each entry to the last 1000 message ids.

---

## 8. Tradeoffs

- **Toy inverted index (chosen) vs. ElasticSearch**. The toy is fine
  for thousands of messages; production uses ES for sharded, scored
  retrieval with stemming and synonyms.
- **Mentions as user-id strings** — Slack uses display names; we
  accept any `@token` for simplicity and to keep the test surface
  small.
- **Threading in a separate list** — keeps a long channel from being
  dominated by thread replies, and makes thread fetch O(replies).

---

## 9. Code map

| File | Purpose |
|---|---|
| `code/service.py` | `SlackService`: workspaces, channels, messages, threading, mention parsing, inverted index. |
| `code/app.py` | Flask HTTP API. |
| `tests/test_service.py` | Workspace/channel lifecycle, threading, mentions, search. |
| `tests/test_app.py` | HTTP smoke for posting + searching. |
