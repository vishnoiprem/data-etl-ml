# System Design Sub-Lesson 7 — Real-Time and Collaborative Systems (the canonical Pattern 7 walkthrough)

> **Real-time and collaborative systems are the seventh most common system design pattern.** 5-10% of system design questions involve real-time collaboration (Google Docs, Figma, multiplayer games, chat). The FDE signal: a candidate who names the CRDT OR operational transform AND the WebSocket protocol AND the conflict resolution — is showing they can own a real-time system. **This sub-lesson walks through the canonical real-time design.**

---

## Why real-time systems are the FDE signal

The 4 things the interviewer is testing:

1. **Can you read the requirements?** Real-time = multiple users editing the same document concurrently. The requirement drives the design (CRDT vs OT, WebSocket vs SSE, conflict-free vs last-write-wins).
2. **Can you pick the right sync protocol?** WebSocket for bidirectional; SSE for server-to-client; long polling for legacy.
3. **Can you handle the conflict resolution?** Two users edit the same line simultaneously. The candidate who names CRDT or operational transform is showing they understand the problem.
4. **Can you handle the disconnect?** The WebSocket disconnects (network failure, browser refresh). The candidate who names the reconnect + state replay is showing they understand the failure mode.

**The FDE pattern:** clarify → decompose → design → tradeoffs. Same as the other patterns, but the design is sync-focused.

---

## The canonical real-time design (worked example)

### The prompt

> "Design a real-time collaborative system: a Google Docs-style document editor. 1000 concurrent users per document, 10ms average edit propagation, sub-100ms P95 latency. The system should handle concurrent edits without conflicts and survive a single server failure."

### Step 1: Clarify (5-7 minutes)

**The 5 questions:**

1. **What's the user?** Document collaborators (external) editing the same document in real-time.
2. **What's the scale?** 1000 concurrent users per document; 10K documents; 100ms P95 latency.
3. **What's the constraint?** Conflict-free concurrent edits; sub-100ms P95 latency; cost < $1000/month; survive 1 server failure.
4. **What's the failure mode?** WebSocket disconnects; concurrent edits to the same line; server dies.
5. **What's the timeline?** MVP in 6 weeks; full scale in 12 weeks.

### Step 2: Decompose (10-12 minutes)

**The 3 lists:**

**Entities:**
- Document (id, title, owner_id, created_at)
- DocumentState (document_id, version, state, updated_at) [CRDT or OT]
- Operation (id, document_id, user_id, op_data, timestamp) [append-only log]
- User (id, name, email)

**Services:**
- DocumentAPI (CRUD for documents)
- EditSyncService (handles WebSocket connections, broadcasts changes)
- ConflictResolver (CRDT or OT for conflict-free merges)
- PersistenceService (writes the document state to Postgres + S3)

**Flows:**
- User opens document → WebSocket connection established → server sends current state
- User edits document → client sends operation → server validates → broadcasts to all connected clients → persists to log
- If concurrent edits: CRDT or OT merges them conflict-free
- If WebSocket disconnects: client reconnects with last-known version → server replays missed operations

### Step 3: Design (15-20 minutes)

**The API contracts (3-5 endpoints):**

```
POST /documents
  Body: {"title": "My Doc", "owner_id": "U12345"}
  → 201 Created
  → {"document_id": "DOC-12345", "title": "My Doc"}

GET /documents/{id}
  → 200 OK
  → {"document_id": "DOC-12345", "title": "My Doc", "version": 100, "state": "..."}

WebSocket /documents/{id}/ws
  Client → Server: {"op": "insert", "position": 100, "char": "A", "version": 100}
  Server → Client: {"op": "insert", "position": 100, "char": "A", "version": 101, "user_id": "U12345"}

GET /documents/{id}/operations?since_version=100
  → 200 OK
  → [{"op": "insert", ...}, {"op": "delete", ...}]
```

**The data model (3-5 tables):**

```
documents (
  id BIGSERIAL PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  owner_id BIGINT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
)

document_states (
  document_id BIGINT PRIMARY KEY,
  version BIGINT NOT NULL DEFAULT 0,
  state JSONB NOT NULL,  -- CRDT state
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
)

operations (
  id BIGSERIAL PRIMARY KEY,
  document_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  op_data JSONB NOT NULL,
  version BIGINT NOT NULL,
  timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(document_id, version)
)
```

**The scale model:**

- **Concurrent users:** 1000 per document × 10K documents = 10M concurrent WebSocket connections
- **Throughput:** 100 ops/sec per document × 10K documents = 1M ops/sec
- **Storage:** 10K documents × 100KB state = 1GB; 1M ops/sec × 86400 sec = 86B ops/day × 1KB = 86TB/day
- **Bandwidth:** 1M ops/sec × 1KB = 1GB/sec
- **Cost:** $10K/month (WebSocket servers $2K + Postgres $1K + S3 $500 + Redis $500 + CloudWatch $1K + 10 read replicas $5K)

### Step 4: Tradeoffs (5-7 minutes)

**The 3 tradeoffs:**

1. **CRDT vs operational transform.** CRDT is simpler (no central server) but has higher memory overhead. OT is more efficient but needs a central server. Pick CRDT for low-conflict scenarios; pick OT for high-conflict scenarios.
2. **WebSocket vs SSE.** WebSocket is bidirectional (server to client); SSE is server-to-client only. Pick WebSocket for collaborative editing; pick SSE for notifications.
3. **In-memory state vs Postgres + S3.** In-memory is fast but volatile; Postgres + S3 is durable but slow. Pick in-memory for the hot path (live editing); pick Postgres + S3 for the cold path (persistence).

**The closing line:** "The design is in progress. (See the full worked example in the next section.)"

---

## The 5 most common real-time questions

The 5 questions that cover 90% of real-time system design:

1. **"Design a Google Docs-style editor"** — covered by the canonical example above.
2. **"Design a Figma-style design tool"** — same pattern, with vector graphics + layer management.
3. **"Design a multiplayer game"** — same pattern, with low latency + state synchronization.
4. **"Design a chat application"** — same pattern, with message ordering + offline delivery.
5. **"Design a collaborative whiteboard"** — same pattern, with shape synchronization + cursor tracking.

**The pattern:** real-time = WebSocket + CRDT/OT + state persistence + reconnect logic. The variations are the conflict resolution (CRDT vs OT), the latency (10ms vs 100ms), and the persistence (in-memory vs Postgres + S3).

---

## The 5 anti-patterns for real-time systems

1. **Naming a technology in the first 5 minutes.** The framework says: clarify, decompose, design, tradeoffs. The technology comes in step 3.
2. **Skipping the conflict resolution story.** The candidate who doesn't mention CRDT or OT is signaling they don't understand concurrent editing.
3. **Skipping the reconnect logic.** The candidate who doesn't mention reconnect + state replay is signaling they don't think about failure modes.
4. **Skipping the persistence strategy.** The candidate who doesn't mention in-memory + Postgres + S3 is signaling they don't think about durability.
5. **Skipping the cost calculation.** "It would cost $X/month" without the math is hand-waving. The cost model is the FDE signal.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "How do you handle concurrent edits to the same line?" | "CRDT (Yjs) merges them conflict-free. Each user sees their own edit immediately; the merge happens on the server." |
| 2. "What if the WebSocket disconnects?" | "The client reconnects with the last-known version. The server replays missed operations. The client reconciles the state." |
| 3. "How do you scale to 10M concurrent connections?" | "I'd use a WebSocket gateway (e.g., Socket.IO with Redis adapter). I'd shard by document_id. I'd use sticky sessions for the same document." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../decomposition/README.md` | The 4-step framework (clarify → decompose → design → tradeoffs) |
| `../swe-coding/04-trees-graphs.md` | The DFS / BFS patterns (for state propagation) |
| `../system-design/README.md` | The 9 patterns cheat sheet (Pattern 7: real-time collaborative) |

---

## The thesis

**Real-time systems are the seventh most common system design pattern.** The candidate who names the CRDT OR operational transform AND the WebSocket protocol AND the conflict resolution — is showing they can own a real-time system.

**The 4-step framework (clarify → decompose → design → tradeoffs) is the muscle memory.** The 5 worked examples (Google Docs, Figma, multiplayer game, chat, whiteboard) are the patterns. Practice them out loud, time yourself at 60 minutes per question, and rehearse with an AI assistant.

**General prep gets you past the resume screen. System design prep gets you past the centerpiece round at Anthropic, OpenAI, AWS FDE, Databricks, and Scale AI.**