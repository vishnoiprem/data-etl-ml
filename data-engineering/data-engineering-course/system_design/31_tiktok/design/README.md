# 31 — TikTok-style Short-Form Video Feed

> **Lesson 31 of the System Design course — Media Streaming & Content Delivery**

A working design + implementation of a TikTok-style short-form
video service: post a video, watch it (with `watch_pct` so the
ranker can weight "completed watches" higher than mere impressions),
and get a per-user **For You** feed ranked by recency + engagement +
user-affinity (Jaccard on tag sets). The For You list is cached per
user for 60 seconds.

The video *bytes* are out of scope; we design around the *metadata*
path and the *ranking* path. The interesting design question is not
"how do we store a video" — the YouTube/Netflix lesson covers that
— but **how do we take ~1 M candidate videos and return 20 that
this specific user is most likely to watch through to the end**.

---

## 1. Requirements

### Functional
- **Create user**.
- **Post a short video** (`caption`, `duration_s`, `tags`).
- **Record a view** with `watch_pct` ∈ [0, 100]. Updates lifetime
  counters and the engagement signal.
- **Like a video**.
- **For You feed** for a user: top-`limit` videos ranked by
  recency + engagement + affinity to this user's history.
- **Get video** metadata.

### Non-functional
- **Read-heavy**: feeds dwarf posts (~10,000:1).
- **Read latency** for `/api/foryou/<id>` must be sub-50 ms p95.
  We cache the per-user ranked list for **60 s** so a returning
  user reads from cache.
- **High availability**: a ranking outage should not take the
  player offline — the cached list covers 60 s of reads.
- **Eventual consistency** for engagement counters is fine.

### Out of scope
- The video *bytes* (assumed served by S3 + CDN).
- Adaptive bitrate / transcoding.
- Comments, follows, DMs, search.
- Real ML model: we model affinity as **Jaccard on tag sets** —
  explainable, no training pipeline.

---

## 2. Capacity estimation

| Metric | Value |
|---|---|
| DAU | 500 M |
| Videos posted / day | 25 M → ~300 /sec avg, ~3 K /sec peak |
| Views / day | 50 B → ~600 K /sec avg, ~5 M /sec peak |
| For You reads / day | 100 B → ~1.2 M /sec avg, ~10 M /sec peak |
| Catalog size (active) | ~1 B short videos (90-day window) |
| Concurrent feed sessions (peak) | ~50 M |
| Per-video metadata | ~1 KB → ~1 TB for active catalog |
| Per-user watch history | last 500 video IDs → ~4 KB / user |
| For You cache (60 s TTL) | ~1 M active users → ~20 K list entries |

The lesson: the *ranking* path is the bottleneck, not the
*metadata* path. Caching the per-user list is the single biggest
optimization — it converts 1.2 M/sec ranking jobs into 1.2 M/sec
cache reads.

---

## 3. High-level design

```
                                    ┌───────────────────────┐
   poster ──► [ upload worker ] ──► │   Origin S3 / CDN     │  ◄── bytes
                                    └───────────────────────┘

   viewer ──►  ┌────────────────────────────────────────────────┐
                │  API / app (Flask, stateless, sharded)        │
                └────┬───────────┬────────────┬─────────────┬───┘
                     │           │            │             │
                     ▼           ▼            ▼             ▼
                ┌────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐
                │ Metadata│  │  For You │  │ Engagement│ │  Tag index  │
                │   DB   │  │  cache   │  │  signal   │  │ (in-mem)    │
                │(KV)    │  │ (60s/uid)│  │ (deque)   │  │             │
                └────────┘  └─────────┘  └─────────┘  └─────────────┘
                     │           │
                     │           └── hit ──► return ranked list
                     │           miss
                     │             │
                     ▼             ▼
                ┌────────────────────────┐
                │  Ranker (online)        │
                │  recency + engagement   │
                │  + Jaccard affinity     │
                └────────────────────────┘

   offline batch (nightly):  rebuild tag → video index from KV;
                              compute user × user co-watch matrix.
```

- **App tier**: stateless Flask replicas. Reads metadata, returns
  byte URLs, records views/likes.
- **Metadata DB**: sharded key-value store (KeyValueStore). User,
  video records, per-user watch history.
- **For You cache**: a per-user 60-second TTL list of ranked video
  IDs. Invalidated on any view the user records.
- **Engagement signal**: in-memory deque per video with the last
  24h of (timestamp, watch_seconds) pairs. Used for the engagement
  score.
- **Tag index**: an in-memory `tag → {video_id, ...}` map. Built
  on demand from the metadata DB; cheap because tags are few and
  per video is small.

---

## 4. API

| Method | Path | Body / Query | Returns |
|---|---|---|---|
| `POST` | `/api/users` | `{"name": "..."}` | `{"user_id": ..., "name": ...}` |
| `POST` | `/api/videos` | `{"user_id": ..., "caption": "...", "duration_s": N, "tags": [...]}` | video metadata |
| `POST` | `/api/videos/<id>/view` | `{"user_id": ..., "watch_pct": 0-100}` | `{"recorded": true, "views": N, "avg_watch_pct": ...}` |
| `POST` | `/api/videos/<id>/like` | `{"user_id": ...}` | `{"video_id": ..., "likes": N}` |
| `GET`  | `/api/foryou/<user_id>?limit=N` | `?limit=N` | `{"user_id": ..., "limit": N, "cached": bool, "results": [{video_id, caption, score}, ...]}` |
| `GET`  | `/api/videos/<id>` | — | video metadata |
| `GET`  | `/metrics` | — | counters + histograms |
| `GET`  | `/health` | — | `{"ok": true}` |
| `GET`  | `/` | — | service index |

Notes:
- The HTTP API does not return raw bytes — clients fetch from the
  CDN URL embedded in the metadata.
- The For You endpoint reports `cached: true|false` so a client can
  observe cache behaviour during dev.

---

## 5. Data model

### video
```
video:<id> = {
  "video_id":     int,
  "user_id":      int,            # creator
  "caption":      str,
  "duration_s":   int,            # hard-capped at 600 (10 min)
  "tags":         [str, ...],     # lowercased, deduped
  "created_at":   float,
  "views":        int,            # lifetime
  "likes":        int,            # lifetime
  "total_watch_s":float,           # sum of (watch_pct/100 * duration_s)
  "play_count":   int,            # how many views contributed
  "original_url": "s3://..."
}
```

### user
```
user:<id> = {"user_id": int, "name": str, "created_at": float}
```

### watch history (in-memory, capped)
```
watch:<user_id> = [(video_id, watch_pct), ...]   # most-recent-first, max 500
```

Persisted only conceptually — here it's an in-process deque.
In production it'd live in Redis or a wide-column store keyed on
user.

### For You cache (in-memory, 60s TTL)
```
foryou:<user_id> = [(video_id, caption, score), ...]   # ranked top-K
```

### tag index (in-memory)
```
tag:<tag> = {video_id, ...}
```

---

## 6. For You ranking

For a target user U, score every candidate video V with:

```
score(V) = w_recency * recency(V)
         + w_engagement * engagement(V)
         + w_affinity * jaccard(V.tags, U.tag_set)
```

We use `w_recency = 1`, `w_engagement = 2`, `w_affinity = 3` —
affinity wins because it's the most personalised signal.

### Recency

`recency = 0.5 ** (age_seconds / 6h)`. 6-hour half-life — a video
loses half its recency credit every 6 hours, so a 1-day-old
video gets ~6% of a fresh one.

### Engagement

`engagement = 0.5 * like_rate + 0.5 * avg_watch_pct`, where
`like_rate = likes / views` and `avg_watch_pct` is the average
percentage of the video each viewer actually watched. We
deliberately cap `avg_watch_pct` at 1.0 so a single binge-watcher
can't blow up the score.

### Affinity

```
jaccard(V.tags, U.tag_set) = |V.tags ∩ U.tag_set| / |V.tags ∪ U.tag_set|
```

where `U.tag_set` is the union of all tags on the videos in U's
recent watch history. Cold user → no affinity → score is 0.

### Candidate generation

Naively ranking every video is impossible. We pull candidates
from two sources:

1. **Tag expansion** — for every tag in U's history, pull the
   set of video_ids tagged with it.
2. **Recent uploads** — always mix in the most recent `5 × limit`
   videos for *exploration* (so a user with a stale history still
   sees new content).

Deduplicate, drop already-watched, bound to `FORYOU_CANDIDATE_POOL`
(default 200). This is the candidate set we actually rank.

---

## 7. Read path: For You

```
1. Client requests /api/foryou/<user_id>?limit=20.
2. App checks foryou_cache[user_id] (TTLCache, 60s).
   hit → return ranked list (no ranker call).
3. miss → check user exists.
   unknown → cold-start: rank by recency only.
4. Build candidate set: tag expansion + recent uploads.
5. Score each candidate: recency + engagement + Jaccard affinity.
6. Sort, take top-K, store in foryou_cache (60s), return top-`limit`.
```

Critical detail: **any view recorded by the user invalidates
their foryou_cache entry** (`foryou_cache.delete(foryou:<uid>)`).
This way, the user always sees a list that reflects *their last
view*, not a stale 60-second-old snapshot.

---

## 8. Write path: post video + record view

### Post video
```
1. Client POSTs /api/videos.
2. Validate (user exists, duration_s in (0, 600], tags is a list).
3. Generate snowflake video_id.
4. Persist video record (KV).
5. Update tag_index (in-memory).
6. Return metadata.
```

### Record view
```
1. Client POSTs /api/videos/<id>/view {user_id, watch_pct}.
2. Validate (video exists, user exists, watch_pct in [0, 100]).
3. Compute contributed_s = watch_pct/100 * duration_s.
4. video.views += 1
   video.total_watch_s += contributed_s
   video.play_count += 1
5. Append (now, contributed_s) to engagement[video_id] deque;
   pop head while older than 24h.
6. Push (video_id, watch_pct) onto watch_history[user_id] deque.
7. Persist video.
8. Invalidate foryou_cache[user_id] (engagement changed; user
   may want a fresh feed).
```

Why invalidate on every view? Because the For You cache is short
(60s) anyway, and the user is *actively watching* — they'll
re-request the feed soon, and the new list should reflect their
just-recorded watch.

---

## 9. Failure modes

| Failure | What happens | Mitigation |
|---|---|---|
| **For You cache cold for hot user** | Cold user → cold-start (recency-only). | 60s TTL is short; cache repopulates on next call. |
| **Tag index stale** | Candidates miss recently-tagged videos. | Rebuild on demand by scanning metadata; periodic background rebuild. |
| **Engagement deque overflow** | Older entries silently dropped. | Bound at 5 K entries per video; for production use Kafka → Flink. |
| **Video bytes miss in CDN** | Player buffers; first viewer pays origin latency. | Pre-warm on `post_video` ack; long TTL on segments. |
| **Write QPS spike** (viral post) | `record_view` queue grows; counters lag. | Ack first, aggregate later (Kafka). Here: synchronous + best-effort. |
| **Cache stampede** on a hot user's TTL expiry | All replicas re-rank simultaneously. | Single-flight / request coalescing; jittered TTL. |
| **Ranking service down** | `/api/foryou` returns 5xx, player still works. | Serve last-good snapshot, degrade to recency-only ranking. |
| **Corrupt For You cache** | A bad cache entry returns garbage. | TTLCache auto-expires; nothing persisted. |

---

## 10. Tradeoffs

### Jaccard vs embeddings for affinity
- **Jaccard (what we model)**: explainable, no training, fast
  (O(|tags_u| × |tags_v|) per pair). Misses *latent* similarity
  — two videos about "skateboarding" and "surfing" don't share a
  tag.
- **Embeddings (two-tower, ALS)**: catches latent similarity,
  more accurate, but needs an offline training pipeline and an
  online vector index (Faiss / Milvus / ScaNN).

Real TikTok *blends* — Jaccard for cold users (no embedding
needed), embeddings for warm users. We pick Jaccard because it
keeps the design on a single whiteboard.

### Push ranking vs pull ranking
- **Pull (what we model)**: ranker runs on every cache miss.
  Simple. Costly at peak (1.2 M rank/sec).
- **Push**: offline batch ranks the candidate pool per user
  every N minutes; cache reads the precomputed list. Cheap reads.
  Stale for N minutes.

Production: precompute the *candidate* set offline; do the
*fine-grained scoring* online. We model the online path.

### 60-second cache vs no cache
- **No cache**: every read is a fresh rank. 1.2 M rank/sec is
  the size of a small cluster.
- **60s cache**: most users re-request within 60s (they keep
  scrolling). Cache hit rate is ~80% on engaged users. This
  cuts the ranker load by 5×.
- **Longer cache (5+ min)**: stale, especially for active
  users. 60s is the sweet spot.

### Persist watch history vs sample
- **Persist every watch** (what we do, capped at 500): accurate
  affinity, can recompute on demand.
- **Sample** (e.g. reservoir sampling): bounded storage, but
  affinity is approximate.

500 entries × 4 KB/user = 2 GB for 500 K active users. Cheap.
Persist.

---

## 11. Code map

```
31_tiktok/
├── design/README.md            # this file
├── code/
│   ├── __init__.py
│   ├── service.py              # TikTokService (no HTTP, pure logic)
│   └── app.py                  # Flask wrapper
└── tests/
    ├── __init__.py
    ├── test_service.py         # ≥5 unit tests on TikTokService
    └── test_app.py             # ≥4 HTTP tests
```

- `TikTokService` owns: users, video metadata, engagement deques,
  per-user watch history, tag index, For You ranker + cache. Pure
  Python; takes `KeyValueStore` + `TTLCache` so tests are
  deterministic and persistence is swappable.
- `app.py` is the Flask wrapper. All endpoints are thin: parse,
  delegate, return JSON. Metrics are collected at the HTTP layer.
- The For You cache is a *separate* TTLCache from the metadata
  cache, so we can monitor `foryou_cache_hits` independently and
  tune TTLs separately.
