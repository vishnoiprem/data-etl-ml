# Day 26 — System Design Mock Interview
**Module 19** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

Today is a **full 45-minute mock system design interview**, compressed to 30 min coding + 20 min discussion.

The interviewer says: "Design a real-time chat application that supports 1M concurrent users, end-to-end encryption, and message history."

You have 30 seconds to think, then 5 minutes to clarify, 10 minutes to draw the diagram, 10 minutes to deep-dive, 5 minutes to wrap up.

---

## 2. Technical concepts (20 min)

### The system: real-time chat
- 1M concurrent users
- End-to-end encryption (E2EE)
- Message history (per user, per conversation)
- Typing indicators
- Read receipts
- Push notifications for offline users
- Group chats (up to 500 people)

### High-level
```
Client (mobile/web)
  ↕ WebSocket
Chat Gateway (stateless, sticky sessions)
  ↕
Message Queue (Kafka)
  ↕
Message Service (persists to Cassandra)
  ↕
Presence Service (Redis)
  ↕
Push Notification Service (APNs/FCM)
```

### Capacity
- 1M concurrent, each sending 1 msg/min = 16k msg/s peak.
- Message size: 1 KB. Bandwidth: 16 MB/s. Easy.
- Storage: 1M × 100 msgs/day × 1 KB = 100 GB/day. Cassandra handles this.
- WebSocket connections: 1M per gateway. Use 100 gateways, 10k connections each.

### E2EE
- Client generates key pair. Public key in DB. Private key in secure storage.
- Each message encrypted with recipient's public key.
- Server never sees plaintext. Can't read messages. Can't comply with wiretaps.
- Tradeoff: no server-side search, no spam detection.

### Presence
- Redis hash: `presence:user_id → {online: true, last_seen: ts}`.
- TTL 30s; client refreshes every 10s.
- On disconnect, the TTL expires and user is "offline".

### Message ordering
- Per-conversation: each message has a `seq` number.
- Server assigns `seq` from a counter (or Lamport clock for distributed).
- Client receives messages in `seq` order; resequence if out of order.

### Failure modes
- WebSocket drops: client reconnects with last `seq`; server sends missed messages.
- Gateway dies: clients reconnect to a different gateway; session is stateless.
- Message queue down: messages buffer in client; send on reconnect.
- Cassandra down: messages buffer in queue; replay when up.

---

## 3. Coding (30 min)

Build the **chat gateway** skeleton. `backend/app/routes/chat.py`:

```python
"""Minimal chat gateway using Server-Sent Events (stand-in for WebSocket)."""
import asyncio
import json
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/chat", tags=["chat"])

# In-memory stores (in prod: Redis + Cassandra)
_messages: dict[str, list[dict]] = defaultdict(list)  # conv_id -> messages
_presence: dict[str, float] = {}  # user_id -> last_seen_ts


@router.get("/stream/{conv_id}")
async def stream(conv_id: str, user_id: str = Query(...)):
    async def gen():
        last_seq = 0
        while True:
            # Send any new messages
            for msg in _messages[conv_id]:
                if msg["seq"] > last_seq:
                    yield f"data: {json.dumps(msg)}\n\n"
                    last_seq = msg["seq"]
            # Heartbeat
            yield ": heartbeat\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/send")
async def send(conv_id: str, body: dict):
    msg = {
        "id": str(uuid.uuid4()),
        "seq": len(_messages[conv_id]) + 1,
        "user_id": body["user_id"],
        "text": body["text"],
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    _messages[conv_id].append(msg)
    return {"seq": msg["seq"]}


@router.post("/heartbeat")
def heartbeat(user_id: str):
    _presence[user_id] = datetime.now(timezone.utc).timestamp()
    return {"online": True}
```

### Sample I/O
- POST `/chat/send?conv_id=c1` `{"user_id":"u1","text":"hi"}` → `{"seq":1}`
- GET `/chat/stream/c1?user_id=u1` → SSE stream

### Line-by-line
- `defaultdict(list)` — auto-creates empty list on first access.
- `: heartbeat\n\n` — SSE comment, ignored by client but keeps the connection alive.
- `_presence` is a stub; in prod it would be Redis with TTL.

---

## 4. Debugging & tests (20 min)

### Bug 1: WebSocket scale
**Fix:** sticky sessions at the LB. Use a connection ID + consistent hashing to map to a gateway.

### Bug 2: message reordering
**Fix:** server-assigned monotonic `seq`; client discards duplicates and waits for missing seqs.

### Bug 3: E2EE key exchange
**Fix:** use X3DH (Signal protocol) or MLS (Messaging Layer Security).

### Bug 4: backpressure
**Fix:** client-side buffer of 1000 msgs; older msgs are dropped with a warning.

### Test
```python
def test_send_and_stream(client):
    client.post("/chat/send?conv_id=c1", json={"user_id": "u1", "text": "hi"})
    r = client.get("/chat/stream/c1?user_id=u1")
    assert "data:" in r.text
```

---

## 5. Mock interview practice (20 min)

This is the full 45-min mock. Time yourself.

**Q1 — "How do you scale to 1M concurrent WebSocket connections?"**
> 100 stateless gateways, 10k connections each. Sticky LB by connection-id. Presence in Redis with TTL. Messages persisted to Cassandra per conversation.

**Q2 — "How do you ensure message ordering?"**
> Per-conversation monotonic `seq` from the server. Client tracks last received seq; requests backfill if gaps.

**Q3 — "How do you implement E2EE?"**
> Each user has a key pair. Public key stored server-side. Private key in OS secure enclave. Messages encrypted client-side with recipient's public key. Server never sees plaintext.

**Q4 — "How do you handle offline message delivery?"**
> When a user is offline, the message service writes to their mailbox in Cassandra. On reconnect, the client requests `messages since seq=X` and gets back the full backlog.

**Q5 — "How do you scale to 10M concurrent?"**
> Multi-region. GeoDNS. Per-region gateways. Cross-region message replication via Kafka MirrorMaker. Tradeoff: cross-region message ordering is harder.

---

## 6. Success criteria check
- [ ] I can draw the high-level diagram cold.
- [ ] I can estimate capacity.
- [ ] I can describe presence, ordering, E2EE.
- [ ] I can list 4 failure modes.

## 7. Grade yourself 0–10
| Area | Score |
|---|---|
| Correctness | /10 |
| Code quality | /10 |
| Debugging | /10 |
| API design | /10 |
| Frontend implementation | /10 |
| Performance | /10 |
| Testing | /10 |
| Communication | /10 |
| **Total** | **/80** |

## 8. Coding assignment
**Add typing indicators: POST `/chat/typing?conv_id=c1` with `{user_id}`; subscribers receive a typing event.**

### Rubric (0–10)
- 0: doesn't compile
- 4: typing event sent
- 6: TTL on typing state
- 8: no typing for self
- 10: aggregate multiple users

### Solution
```python
_TYPING: dict[str, dict[str, float]] = defaultdict(dict)  # conv -> {user_id -> ts}
@router.post("/typing")
def typing(conv_id: str, user_id: str):
    _TYPING[conv_id][user_id] = time.time()
    return {"typing": list(_TYPING[conv_id].keys())}
```

**Time: 90 min**

---

## Capstone done

You now have:
- **Days 1–21:** full-stack + testing + debugging
- **Days 22–26:** system design + AI domain

For full Meta/Google prep, see `docs/META_GOOGLE_REALITY_CHECK.md` and the supplemental 8-week plan.
