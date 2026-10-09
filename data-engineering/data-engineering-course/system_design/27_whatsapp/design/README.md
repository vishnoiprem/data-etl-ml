# 27 — WhatsApp (Group Chat + E2E Encryption)

> **Lesson 2 of 5 — Real-Time & Collaborative Systems**

A group messaging service: create a group, add members, send messages
(plain text or media references), and read history. We model the
end-to-end encryption layer as a per-group "key" — in reality this
would be derived via X3DH (Signal) or MLS (Messaging Layer Security);
our service only stores the key id, never sees plaintext at rest in
production.

---

## 1. Requirements

### Functional
- Create a group with a name and an initial member list.
- Add / remove members.
- Send a message (text or media) to a group.
- Read group history.
- List groups a user belongs to.

### Non-functional
- Group fan-out must be O(members) writes per message; read is O(1).
- Each message is associated with a "key id" so receivers know which
  decryption key to apply (we model the key as opaque bytes).
- Media references are stored as URLs (the blob lives in object storage
  in production; we keep optional `media_b64` for toy/demo use).

### Out of scope
- Real X3DH / MLS key exchange.
- Voice/video calls.
- Status (stories).
- Disappearing messages timer enforcement.

---

## 2. Capacity

| Metric | Value |
|---|---|
| Groups | ~10M (toy: thousands) |
| Avg group size | 50 members |
| Largest group size | 1024 (WhatsApp cap) |
| Messages / day | ~100B (toy: thousands) |
| Fan-out cost | 50 writes per message median |

---

## 3. High-level

```
[member client] ──POST /groups/<id>/messages──► [API]
                                                    │
                       ┌────────────────────────────┤
                       ▼                            ▼
            [Message store]                  [Per-group inbox lists]
                  (msg:<id>)                (inbox:<user_id>:groups[g])
                       │
                       └─► [fan-out: N writes, one per member]
                                            │
                                            ▼
[each member] ◄── SSE / long-poll ──── [inbox]
```

The encryption story:

- Every group has a `key_id` (rotated when membership changes — we just
  bump the version on add/remove).
- Each message records `key_id` + an `encrypted_body` placeholder.
  In our toy model, the body field is the "ciphertext" and the
  per-group key is stored alongside the group record. In production the
  server never sees plaintext.

---

## 4. API

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/api/groups` | `{"name", "creator_id", "members": [...]}` | group record |
| `GET`  | `/api/groups/<id>` | — | group record |
| `POST` | `/api/groups/<id>/members` | `{"user_id"}` | updated group |
| `DELETE` | `/api/groups/<id>/members/<user_id>` | — | updated group |
| `POST` | `/api/groups/<id>/messages` | `{"sender_id", "body", "media_url"?}` | message record |
| `GET`  | `/api/groups/<id>/messages?since_ts=&limit=` | — | message list |
| `GET`  | `/api/users/<id>/groups` | — | groups the user is in |
| `GET`  | `/health`, `/metrics` | — | ops |

---

## 5. Data model

| Key | Value |
|---|---|
| `group:<id>` | `{group_id, name, creator_id, members: [uid], key_id, key_version, created_at}` |
| `gmsg:<id>` | `{message_id, group_id, sender_id, body, media_url?, key_id, ts}` |
| `gmsgs:<group_id>` | ordered `[message_id]` (capped) |
| `user_groups:<user_id>` | `[group_id]` |
| `inbox:<user_id>` | `[message_id]` (across all groups) |

---

## 6. Read / Write paths

**Send:** generate Snowflake id, store msg, append to group list, fan out
to each member's inbox, bump group message counter.

**History:** scan `gmsgs:<group_id>`, optional `since_ts` filter, return
resolved messages (with `key_id` for client-side decryption).

**Media:** clients upload bytes to object storage out-of-band, then send
a message with `media_url`. We additionally allow `media_b64` for toy
testing without a real bucket.

---

## 7. Failure modes

- **Member removed mid-send** — we capture membership at send time so
  the user gets the message and is removed afterwards. (Real systems
  re-encrypt for the new member set.)
- **Group key rotation** — we bump `key_version` and `key_id` on every
  membership change. Old messages stay encrypted under old keys (which
  are still distributed to remaining members in production; we don't
  model that fan-out here).
- **Hot groups** — large groups create write amplification. In
  production this is mitigated by per-member push queues with
  coalescing; our toy model writes per-member directly.

---

## 8. Tradeoffs

- **Per-group inbox vs. per-user inbox** — we keep a per-user cross-group
  inbox so the client can show unread badges across all groups; the
  group list is the source of truth for messages in a group.
- **Key management** — the toy model stores the symmetric key on the
  group record. A real client never trusts the server with plaintext;
  it would receive `key_id` and look up the actual key from local
  secure storage or a sender-encrypted blob.
- **Fan-out** — eager (chosen) for groups ≤ 256; for very large groups
  we'd switch to a pull model where the client subscribes to a group
  stream.

---

## 9. Code map

| File | Purpose |
|---|---|
| `code/service.py` | `WhatsAppService`: groups, members, messages, fan-out, key rotation. |
| `code/app.py` | Flask HTTP API, metrics, health. |
| `tests/test_service.py` | Group lifecycle, fan-out, media, key rotation. |
| `tests/test_app.py` | HTTP smoke for full group conversation. |
