# 15 — Distributed LRU Cache

> **Lesson 15 of the Distributed Data Storage & Partitioning track**

A "distributed" LRU where multiple nodes each own a shard of the key
space via consistent hashing. On GET, the local node promotes the key
(recency); on miss, the node pretends to fetch from a peer (logged,
configurable). The result is an in-process simulation of a Memcached
fleet — same API shape, same key→node routing, no network.

---

## 1. Requirements

### Functional
- `PUT /api/cache/<key>` writes value to the owning node only.
- `GET /api/cache/<key>` reads from owning node; on miss, simulates a peer fetch.
- `GET /api/nodes` exposes the cluster topology + per-node stats.
- Show key → node mapping for inspectability.

### Non-functional
- **Even key distribution** across nodes — virtual nodes smooth skew.
- **Bounded memory** per node via per-node LRUCache.
- **High read QPS** at small scale.
- **Minimal movement** on add/remove — consistent hashing.

### Out of scope
- Cross-node replication.
- Real network — we simulate by counting peer-fetch operations.
- Persistence.

---

## 2. Capacity estimation

| Metric | Value |
|---|---|
| Nodes | 4–16 |
| LRU capacity per node | 100k entries |
| Total cache | N × 100k entries |
| Read QPS per node | 50–100k |
| Peer-fetch overhead | ≤ 5% of total reads |

---

## 3. High-level design

```
   client ──► [ router ] ──► consistent hash ring
                                │
                  ┌─────────────┼─────────────┐
                  ▼             ▼             ▼
               node-0        node-1        node-2  …  node-N
                  │             │             │
                  LRU           LRU           LRU  (LRUCache)
                  │             │             │
                 keys         keys          keys   (own shard only)
```

- `Router` knows all nodes + ring.
- Each `CacheNode` has its own `LRUCache`.
- `get(key)`: hash → node; node: local LRU hit? promote; else simulate peer (logged).

---

## 4. API

| Method | Path | Body / Params | Returns |
|---|---|---|---|
| `PUT`  | `/api/cache/<key>` | value (json or text) | `{"key", "node", "stored"}` |
| `GET`  | `/api/cache/<key>` | — | `{"key", "value", "node", "source": "local"\|"peer"}` |
| `DELETE` | `/api/cache/<key>` | — | `{"removed": bool}` |
| `GET`  | `/api/nodes` | — | list of nodes + per-node stats |
| `GET`  | `/api/ring` | — | ring positions for visibility |
| `GET`  | `/api/locate/<key>` | — | which node owns this key |
| `GET`  | `/metrics` | — | counters + histograms |
| `GET`  | `/health` | — | `{"ok": true}` |

---

## 5. Data model

### Routing ring
Each node has V virtual positions on the ring (default V=64).

### Per-node
- `LRUCache(max_entries=capacity)` — owns a slice of keys.
- `peer_fetches`: counter incremented on simulated cross-node reads.
- Standard LRU stats (hits, misses, evictions).

### Cross-node behavior
On `get(key)`:
1. Hash → owning node `N`.
2. `N.cache.get(key)`:
   - **hit** → return (promotes the key).
   - **miss** → simulated peer fetch: increment `peer_fetches` on `N`.
     In a real cluster this is an async gRPC; here we just return a
     structured "miss" payload that callers can detect.

---

## 6. Read/write path

### PUT
1. Hash key → owning node.
2. `node.cache.set(key, value)`.
3. Increment node.put count.

### GET
1. Hash key → owning node.
2. `node.cache.get(key)`:
   - hit → `node.cache_hits++`, source=`local`.
   - miss → `node.peer_fetches++`, source=`peer`.
3. Return payload; on miss, return `{"value": null, "source": "peer"}`.

---

## 7. Failure modes

| Failure | Mitigation |
|---|---|
| Node down | Simulated as a flag on the node; reads routed elsewhere by the ring (simple) — out of scope to re-route gracefully. |
| Hot key | LRU keeps it hot; eviction pressure on cold keys. |
| Node overload | LRU + capacity per node — soft isolation. |
| Cache stampede on cold key | Real systems use request coalescing / single-flight. |

---

## 8. Tradeoffs

- **Per-node LRU vs single global LRU**: per-node shards give us isolation
  (one node OOM doesn't bring down the cluster) at the cost of cross-node
  reads.
- **V virtual nodes (64)**: balances distribution vs lookup work.
- **No replication**: simulated distribution only — pure routing demo.
  Add KV-store style replication for a real cluster.

---

## 9. How the code maps to this design

| File | Role |
|---|---|
| `code/service.py` | `CacheNode`, `DistributedLRU` — nodes, ring, peer-fetch simulation. |
| `code/app.py` | Flask HTTP service exposing `/api/cache/<key>`. |
| `tests/test_service.py` | Ring distribution, LRU behavior, peer-fetch counter. |
| `tests/test_app.py` | HTTP-level tests using Flask test client. |
