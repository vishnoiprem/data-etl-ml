# 02 — Typeahead / Search Suggestions

> **Lesson 2 of 6 — Read-Heavy Systems**

When a user types "flas" in a search box, we want to instantly return
"flask", "flash", "flashlight", ranked by frequency. Sub-100ms latency
on every keystroke, billions of queries/day.

---

## 1. Requirements

### Functional
- Given a prefix, return top-K most frequent matching words.
- K is small (5–10). Cap the result list.
- Case-insensitive.
- Suggestion freshness: dictionary updated daily (we don't handle live
  edits here).

### Non-functional
- **p99 < 100 ms** at the edge.
- **QPS**: 100k+ peak (read-heavy).
- Availability: highly available; users hate a slow / down search box.

### Out of scope
- Personalized ranking.
- Spelling correction.
- Multi-language.

---

## 2. Capacity

| Metric | Value |
|---|---|
| Queries/sec | 100k peak |
| Avg prefix length | 4 chars |
| Dictionary size | 1M words (toy), 10M+ real |
| Top-K | 10 |

---

## 3. Data structures

A **Trie** is the canonical structure:

- Each node has children keyed by character.
- Each node holds a max-heap / sorted-list of top-K words descending by
  frequency under that prefix.
- Lookups: walk the prefix in O(p), then pop top-K from the node in
  O(K log K) ≈ O(1) since K is small.

For our toy dictionary we use a simpler **sorted-list per node**, built
once at startup. Real systems (Elasticsearch, Solr) use FSTs
(Finite State Transducers) for O(1) prefix lookups with a sorted list
embedded directly in the structure. We document this tradeoff in §10.

---

## 4. API

| Method | Path | Body / Query | Returns |
|---|---|---|---|
| `GET` | `/suggest?q=flas&k=5` | — | `{"q": "flas", "suggestions": [{"word": "flask", "freq": 999999}, ...]}` |
| `POST` | `/api/reload` | — | `{"loaded": N, "ms": M}` (rebuilds the trie) |
| `GET` | `/metrics` | — | counters + histograms |
| `GET` | `/health` | — | `{"ok": true}` |

---

## 5. Index build

1. Load the dictionary (one word per line, JSONL with `word`, `freq`).
2. Lowercase + sort by freq desc, dedupe.
3. Walk each character, appending the word to the node's top-K.
4. Persist a snapshot to disk so the next start is instant.

A daily cron rebuilds the index off the hot path.

---

## 6. Query path

```
GET /suggest?q=flas&k=5
  └─► walk trie: f→l→a→s, hit node "flas:"
        └─► read precomputed top-K
              └─► return JSON
```

Latency breakdown:
- Trie walk: 4 pointer dereferences ≈ 50 ns.
- Top-K read: pointer to a Python list, slice → ~1 µs.
- JSON encode: ~20 µs.

**Total well under 1 ms per query** in this toy version; production
adds network and serialization.

---

## 7. Caching

- **In-process LRU** keyed by `(prefix, K)`: prefix queries are
  extremely repetitive ("flas" gets typed millions of times).
- **Edge cache** (CDN / Varnish) for the most common prefixes —
  cache the JSON of the top-10 result for `/suggest?q=th`.

---

## 8. Sharding

In production:
- Partition the dictionary by first letter (or first 2 letters for
  finer shards). Each shard hosts its own trie.
- The query router sends the query to the right shard by prefix.
- Top-K is computed per shard; final merge keeps the global top-K
  (we over-fetch K from each shard).

---

## 9. Failure modes

| Failure | Mitigation |
|---|---|
| Trie corrupted | Fall back to scanning dictionary; degrade to slow but correct. |
| Hot prefix overload | Edge cache + per-process LRU + request coalescing. |
| Index rebuild crashes | Keep last-known-good snapshot; atomic swap. |

---

## 10. Tradeoffs

- **Trie vs FST**: trie is simple; FST is ~10× smaller and faster.
- **Top-K precomputed vs queried on demand**: precompute wins; query
  cost is constant.
- **In-memory vs on-disk**: in-memory is fast; size is the constraint.
  For 10M words × ~100B/node we hit ~1 GB, which fits on one box.
- **Per-language**: separate trie per language, route by Accept-Language.

---

## 11. Code map

| File | Role |
|---|---|
| `code/trie.py` | The trie + sorted-top-K node. |
| `code/service.py` | TypeaheadService — loads the dictionary, exposes `suggest`. |
| `code/app.py` | Flask HTTP service. |
| `tests/test_trie.py` | Trie unit tests. |
| `tests/test_service.py` | Service-level tests. |
| `tests/test_app.py` | HTTP-level tests. |
