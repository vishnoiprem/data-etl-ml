# 13 — Distributed Key-Value Store (consistent hashing + replication)

> **Lesson 13 of the Distributed Data Storage & Partitioning track**

A from-scratch distributed KV store built on a consistent-hash ring with
virtual nodes and configurable replication. The ring is a stand-in for
DynamoDB / Cassandra: keys map to a primary, and writes propagate to the
next N-1 ring members as replicas.

---

## 1. Requirements

### Functional
- `PUT key value` — write to primary + N-1 next-ring replicas.
- `GET key` — read from primary (or quorum of replicas if requested).
- Cluster management — add/remove server nodes; re-balance the ring.
- Inspect the cluster — list servers, show ring distribution.

### Non-functional
- **Even key distribution** — virtual nodes smooth the skew.
- **Minimal key reshuffling on add/remove** — only `K / N` keys move.
- **Configurable replication factor** (R=1..N).
- **No external dependencies** — runs in a single Python process.

### Out of scope
- Real network calls between nodes (we simulate with in-process stores).
- Vector clocks / Dynamo-style conflict resolution.
- Persistence to disk (use `KeyValueStore` per "server").

---

## 2. Capacity estimation

| Metric | Value |
|---|---|
| Cluster size | 3–100 servers |
| Virtual nodes per server | 100–500 (default 128) |
| Replication factor | 3 (typical) |
| Hash space | 2^32 (32-bit ring) |
| Read QPS per node | 10k–100k |
| Write QPS per node | 1k–10k |

Key insight: with V=128 virtual nodes per server and N=10 servers, the
ring has 1280 points — distribution is balanced to within ±5% per server.

---

## 3. High-level design

```
                  consistent hash ring (0 .. 2^32)
                  ─────────────────────────────
   s0@v0  s1@v0  s2@v0  s0@v1  s1@v1  s2@v1  ...  (128 per server)
       \    |    /
        \   |   /
         ring positions
              │
        ┌─────┼──────┐
        │  key "user:42"  hash = 0xA13F...B27
        │  → clockwise → s2 (primary)
        │  → replicas  → s2, s0, s1
        └─────┬──────┘
              ▼
   [ s2 put ] ── async replicate ──► [ s0 put ]
                                ──► [ s1 put ]
```

- **Ring** is sorted list of `(hash, server_id)`.
- `key → primary`: walk ring clockwise from `hash(key)`, first node wins.
- `key → replicas`: primary plus the next R-1 distinct servers.
- **Virtual nodes** spread each server across many ring positions.

---

## 4. API

| Method | Path | Body / Params | Returns |
|---|---|---|---|
| `POST` | `/api/put` | `{"key": "...", "value": ...}` | `{"key", "primary", "replicas", "acks"}` |
| `GET`  | `/api/get/{key}` | optional `?quorum=N` | `{"key", "value", "source", "replica_hits"}` |
| `POST` | `/api/cluster/servers` | `{"servers": ["s0","s1",...],"replication":3,"vnodes":128}` | full cluster state |
| `GET`  | `/api/cluster` | — | list servers, ring stats, replication factor |
| `GET`  | `/api/ring` | — | sorted ring positions |
| `GET`  | `/metrics` | — | counters + histograms |
| `GET`  | `/health` | — | `{"ok": true}` |

---

## 5. Data model

### Ring
```
ring: list[tuple[int, str]] = sorted by hash, ascending
      each entry = (position_hash, server_id)
```
Distinct virtual nodes per server ensure independent positions.

### Per-server store
`KeyValueStore(name="kv_<server_id>")` — in-memory, JSON-persisted.
Each server sees the same `key → value` for the keys it's responsible
for (as primary or replica).

### Metadata
- `replication_factor` (R): how many copies of every key.
- `vnodes_per_server` (V): how many ring positions per server.
- `write_quorum`, `read_quorum` (W, R' in Dynamo notation; here simplified).

---

## 6. Read path

`GET /api/get/{key}`:

1. `h = hash(key)`; find primary = first server clockwise from `h`.
2. Read from primary. If found, return.
3. If primary is "down" (simulated via flag), try next replica.
4. If `quorum > 1`, return once we have K agreeing replicas.
5. On total miss, return 404.

Simulated failure mode: callers may pass `?simulate_fail=primary` to
force a replica read. The metric `replica_fallback_total` tracks this.

---

## 7. Write path

`POST /api/put {"key", "value"}`:

1. Find primary + R-1 replicas (clockwise).
2. Write to primary first, then fan out to replicas. Each replica
   acknowledges with a synthetic ACK.
3. Return list of `replicas` that ACKed + total ack count.
4. Optional `?w=R` requires R ACKs before returning; otherwise best-effort.

Replication is **synchronous within the process** (loop). In a real
system this would be a gRPC fan-out; the design point is identical.

---

## 8. Failure modes

| Failure | Mitigation |
|---|---|
| Single node down | Reads/writes still succeed on remaining R-1 replicas. |
| Network partition | Hinted-handoff write log on a reachable neighbor (out of scope). |
| Hot key (viral) | Consistent hashing doesn't help — needs caching layer. |
| Hash skew | More virtual nodes → tighter balance. |
| Replica divergence | Last-writer-wins (timestamp) — sufficient for KV; CRDTs for sets. |

---

## 9. Tradeoffs

- **Virtual nodes**: more vnodes = better balance, more memory + lookup time.
  We pick 128 — the same constant used by Dynamo and Cassandra.
- **Replication factor**: R=3 is the default sweet spot. R=5 for critical
  data, R=2 for ephemeral caches.
- **Synchronous replication**: simple, slow. Async is faster but loses
  consistency. Quorum is the middle ground.
- **Hash function**: SHA-256 truncated to 32 bits is fine for a course;
  MD5 or xxhash are used in production.

---

## 10. How the code maps to this design

| File | Role |
|---|---|
| `code/service.py` | `ConsistentHashRing`, `KVCluster`, `KVStore` — pure logic, no Flask. |
| `code/app.py` | Flask HTTP service: put/get endpoints, cluster mgmt, metrics. |
| `tests/test_service.py` | Ring distribution, replication, fallback tests. |
| `tests/test_app.py` | HTTP-level tests for put/get/cluster endpoints. |
