# 30 — Google Docs (Collaborative Editing, Op Log)

> **Lesson 5 of 5 — Real-Time & Collaborative Systems**

A collaborative document editor: a doc is a string buffer; every edit
is an operation (`insert` or `delete`) at a position; the server keeps
the authoritative op log and applies ops in order; concurrent ops use
**line-level last-writer-wins** as a simple transformation strategy. A
Lamport-clock-like version counter advances on every op.

---

## 1. Requirements

### Functional
- Create a doc (with a title; empty body).
- Apply an op `{op, pos, text?}` to a doc.
- Read the current snapshot (the doc as a string).
- Read the op log.
- Track doc version (counter, advanced on every accepted op).
- Reject illegal ops (out-of-range positions, missing text).
- Concurrent ops at the same logical position: later op wins (toy LWW).

### Non-functional
- p99 apply < 100 ms for ops up to a few KB.
- Snapshot reconstruction from ops is O(ops) — fine for a few thousand
  ops; production would checkpoint periodically.

### Out of scope
- Real-time operational transform / CRDT math.
- Per-user cursors, selections, formatting.
- Rich text (bold, headings, links).
- Permissions / sharing.

---

## 2. Capacity

| Metric | Value |
|---|---|
| Active docs | ~10M (toy: thousands) |
| Ops / doc / minute | ~60 typing users → 600 ops/min |
| Avg op size | 5 bytes (one keystroke) |
| Snapshot size | ~50 KB median, ~MB for long docs |

---

## 3. High-level

```
[client] ──POST /api/docs/<id>/ops──► [API]
                                          │
                       ┌──────────────────┼──────────────────┐
                       ▼                  ▼                  ▼
                [op log]         [snapshot recompute]   [version++]
                       │
                       └─► [SSE /api/docs/<id>/stream] to peers

Read:
[client] ──GET /api/docs/<id>/snapshot──► [API] ──read cached snapshot──►
[client] ──GET /api/docs/<id>───────────► [API] ──read op log + version─►
```

Two important design choices:

- **Op log, not patch log.** Every keystroke is an op. The snapshot is
  derived. This makes "what changed" trivially auditable and lets new
  clients catch up.
- **Version counter is Lamport-like.** Every accepted op bumps
  `version`. Clients can send `if_version` to detect concurrent edits
  (a missing `if_version` field means "fire and forget"; we always
  apply in this toy model and let LWW at the line level resolve).

---

## 4. API

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/api/docs` | `{"title"}` | doc record |
| `GET`  | `/api/docs/<id>` | — | doc + version + op count |
| `POST` | `/api/docs/<id>/ops` | `{"op": "insert"\|"delete", "pos": int, "text"?: str, "client_id"?, "if_version"?}` | applied op result |
| `GET`  | `/api/docs/<id>/snapshot` | — | `{content, version}` |
| `GET`  | `/api/docs/<id>/ops` | — | full op log |
| `GET`  | `/api/docs/<id>/stream` | — | **SSE** of new ops |
| `GET`  | `/health`, `/metrics` | — | ops |

---

## 5. Data model

| Key | Value |
|---|---|
| `doc:<id>` | `{doc_id, title, version, op_count, created_at}` |
| `doc_snap:<id>` | `{content: str, version: int}` (cached snapshot) |
| `op:<doc_id>:<seq>` | `{seq, op, pos, text?, ts, client_id?}` (op log) |
| `doc_ops:<id>` | `[seq]` (ordered list) |
| `doc_seq:<id>` | int (next sequence number) |

---

## 6. Read / Write paths

**Apply op:**
1. Verify doc exists.
2. If `if_version` is set and doesn't match the current version, decide
   a conflict-resolution strategy. We use **LWW per line**: if the op
   falls on a line that already has a concurrent change, accept the
   later op's text (the client's local edit loses) at that line.
3. Validate position against snapshot.
4. Apply to cached snapshot (mutate in place).
5. Append to op log with the next seq, bump version, broadcast on SSE.

**Snapshot:** read `doc_snap:<id>`; if missing, replay op log to
reconstruct (we always cache, so this should be a cache miss only on
first read).

**Stream:** SSE — clients subscribe; ops are pushed as they are
accepted.

---

## 7. Failure modes

- **Op applied twice** — idempotent: we always re-validate position
  against the current snapshot; if already applied, the position has
  shifted and the duplicate is naturally rejected. Real systems use a
  client_nonce + dedup window.
- **Snapshot corruption** — op log is the source of truth; we can
  always replay to rebuild the snapshot.
- **SSE clients fall behind** — they reconnect and replay the op log
  from `version` (or from a checkpoint).

---

## 8. Tradeoffs

- **Op log (chosen) vs. patch log** — op log is human-readable and
  supports arbitrary transforms. A patch log (diff) is more compact
  but harder to inspect.
- **LWW per line (chosen) vs. full OT/CRDT** — LWW loses fine-grained
  concurrent edits within a single line, but is simple, deterministic,
  and demonstrably convergent. Real Google Docs uses a much more
  elaborate operational transform.
- **Version as a counter** — single-doc counter is fine; for a cluster
  we'd use a Lamport clock (per-replica counter, max on merge).

---

## 9. Code map

| File | Purpose |
|---|---|
| `code/service.py` | `DocsService`: op validation, application, LWW conflict resolution, snapshot, SSE listeners. |
| `code/app.py` | Flask HTTP API with SSE stream. |
| `tests/test_service.py` | Insert/delete, version counter, op log, conflict resolution. |
| `tests/test_app.py` | HTTP smoke for editing + snapshot. |
