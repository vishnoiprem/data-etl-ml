# 06 — YouTube / Netflix-style Video Sharing

> **Lesson 6 of the System Design course — Media-Heavy Systems**

A working design + implementation of a YouTube-style video sharing
service: upload metadata, watch / record views, browse trending, and
get simple co-watch based recommendations. Video *bytes* are out of
scope; we design around the *metadata* path and reason about how the
bytes get delivered (CDN, transcoding).

---

## 1. Requirements

### Functional
- **Upload** video metadata: title, duration, owner (user). (Bytes
  upload is assumed handled by a parallel blob store / S3 multipart
  flow.)
- **Watch** a video → records a view event.
- **Trending** list: top-N videos by views in the last minute
  (1-minute buckets, sliding).
- **Recommend** videos for a user: co-watch similarity — find users
  who watched similar videos, return the most popular videos *they*
  also watched, ranked.
- **Comments** (simplified): the API surface includes a `comments`
  list per video; storage is just a list of `{user_id, text, ts}`
  appended to the video record. We don't dwell on it — the design
  question is the read path, not moderation.

### Non-functional
- **Read-heavy** by orders of magnitude: views dwarf uploads (~10,000:1).
- **Read latency** is dominated by *bytes*, not metadata: the
  metadata read must complete in single-digit ms so the player can
  start requesting segments from the CDN.
- **High availability**: a single trending-list outage should *not*
  take playback offline.
- **Eventually consistent** for trending / recommendations is fine.

### Out of scope (for this lesson)
- DRM, payments, ads, live streaming, video search, abuse / take-down.
- True CDN integration — we model the cache layers, not the BGP.

---

## 2. Capacity estimation

| Metric | Value |
|---|---|
| MAU | 200 M users |
| DAU | 50 M (25%) |
| Uploads / day | 720 K → ~8 /sec avg, ~25 /sec peak |
| Views / day | 5 B → ~60 K /sec avg, ~250 K /sec peak |
| Concurrent watchers (peak) | ~1 M |
| Catalog size | 5 B videos, ~500 B metadata records (5y) |
| Metadata per video | ~2 KB (title, owner, durations, codec list) → ~10 TB |
| Video bytes per video (5y) | ~50 GB avg → ~250 EB total |
| Trending list recompute | once per minute, full scan of recent views |

The lesson: bytes (CDN/S3) dominate storage and bandwidth. Metadata
is dwarfed by the view stream, which is in turn dwarfed by raw egress.

---

## 3. High-level design

```
                   ┌───────────────┐
   player ────►──► │   CDN edge    │  ◄──── bytes (HLS/DASH segments)
                   └──────┬────────┘
                          │ miss
                   ┌──────▼────────┐
                   │  Origin S3    │  ◄──── bytes (HLS/DASH segments)
                   └──────┬────────┘
                          │ presigned URLs only
                          │
   client ────►──►  ┌─────▼────────┐  ┌────────────────────┐
                    │  API / app   │  │  Metadata DB       │
                    │  (Flask)     │─►│  (key-value)       │
                    └─────┬────────┘  └────────────────────┘
                          │
            ┌─────────────┼─────────────────┐
            ▼             ▼                 ▼
       ┌────────┐  ┌────────────┐   ┌──────────────┐
       │ Trending│ │ Recommend  │   │ Comments     │
       │ service │ │ service    │   │ service      │
       └────┬────┘  └─────┬──────┘   └──────┬───────┘
            │             │                │
            └─────────────┴────────────────┘
                          │
                   ┌──────▼────────┐
                   │  View events  │
                   │  (queue +     │
                   │   time bucket)│
                   └───────────────┘

   uploader ──► [ Transcoding worker ] ──► Origin S3 (multi-bitrate)
                  ▲
                  └── fall back to single quality if worker is offline
```

- **App tier**: stateless Flask replicas. Reads metadata, returns
  *byte URLs* (CDN / S3), records views.
- **Metadata DB**: sharded key-value store (`KeyValueStore` here).
  Video records, comments, user watch history.
- **Blob storage (S3)**: stores the original upload *and* the
  transcoded renditions. Never served directly to clients — always
  fronted by the CDN.
- **Transcoding worker**: takes a fresh upload, produces HLS / DASH
  segments at multiple bitrates, writes them to S3. If the worker is
  offline, the video stays at the *original* single quality — the
  app still plays, just no adaptive bitrate ladder.
- **Recommendation service**: offline job over user watch history
  building a "co-watch" graph. Online query: given a user's recent
  watch set, return top-N videos ranked by co-watch affinity.
- **Trending service**: rolling 1-minute view counts, recomputed
  every minute from the view-event stream.

---

## 4. API

| Method | Path | Body / Query | Returns |
|---|---|---|---|
| `POST` | `/api/users` | `{"name": "..."}` | `{"user_id": ..., "name": ...}` |
| `POST` | `/api/videos` | `{"user_id": ..., "title": ..., "duration_s": ...}` | `{"video_id": ..., ...}` |
| `GET`  | `/api/videos/<id>` | — | metadata + view count + comments |
| `POST` | `/api/videos/<id>/view` | `{"user_id": ...}` | `{"recorded": true, "views": N}` |
| `GET`  | `/api/trending?limit=10` | `?limit=N` | `[{video_id, title, views_in_last_min}, ...]` |
| `GET`  | `/api/recommend/<user_id>?limit=10` | `?limit=N` | `[{video_id, title, score}, ...]` |
| `GET`  | `/metrics` | — | counters + histograms |
| `GET`  | `/health` | — | `{"ok": true}` |
| `GET`  | `/` | — | service index |

Notes:
- The HTTP API does not return raw bytes — clients fetch the actual
  HLS playlist or MP4 from the CDN URL returned in metadata.
- `record_view` is intentionally idempotent at the *minute* level
  (we don't want 1000 view events from a refresh storm); for this
  lesson we simply append and count.

---

## 5. Data model

### video
```
video:<id> = {
  "video_id":     int,
  "user_id":      int,           # uploader
  "title":        str,
  "duration_s":   int,
  "created_at":   float,
  "views":        int,           # total views (lifetime)
  "renditions":   ["240p", "480p", "720p", "1080p"],   # empty if transcoder offline
  "original_url": str,           # S3 / CDN URL of the master file
  "comments":     [{"user_id": int, "text": str, "ts": float}, ...]
}
```

### view
We do *not* persist every view as a row — at 250 K/sec that's
unsustainable. Instead we keep:
- `video:<id>:views` — lifetime counter, persisted.
- An in-memory `deque` of recent view timestamps, capped at
  `MAX_RECENT_VIEWS` (e.g. 10 K) per video, used for
  *trending-in-last-minute* and *co-watch* scoring.

A real system would feed views through Kafka and aggregate in
batch jobs. Here we use the in-process `deque` so the unit tests
are deterministic.

### user
```
user:<id> = {"user_id": int, "name": str, "created_at": float}
watch:<user_id> = [<video_id>, <video_id>, ...]    # recent, capped
```

The `watch:<user_id>` list is the co-watch recommendation source.

---

## 6. Hot video read path

`GET /api/videos/<id>` (or the player asking for metadata before
requesting bytes):

```
1. Player asks for video metadata.
2. Edge cache (CDN or local) ──hit──► return metadata + CDN URL.
                                  miss
3. App reads TTLCache. Hit → return. (L1 cache, ~5 min TTL.)
4. App reads KeyValueStore. Hit → populate cache, return.
5. App returns the manifest URL (e.g. https://cdn.example/<id>/master.m3u8).
6. Player fetches the manifest from the CDN.
7. CDN ──hit──► stream segments. miss
8. CDN fetches from origin S3, caches for N days, streams.
9. Player downloads segments adaptively (ABR — see §10).
```

Key things to notice:
- Metadata read is parallel to the byte path — we never block the
  player on a slow DB.
- The TTLCache is small and read-only-with-rare-write: writes happen
  on upload, reads on every play. We pre-warm the *trending* videos
  into it on each trending recompute.
- The CDN edge cache holds *segments*, not metadata. Each segment
  URL is a stable hash, so cache hit rate is very high (~98% on
  popular content).

---

## 7. Trending

Trending is *what's hot right now*, not *what's popular all time*.
We want a 1-minute sliding window of views.

Implementation:
- A `defaultdict(deque)` keyed by `video_id`. Each entry holds the
  last `WINDOW_SECONDS` of view timestamps.
- On every `record_view`, append `time.time()` to the deque and
  pop the head while it's older than `now - WINDOW_SECONDS`.
- `trending(limit)` walks the dict, counts the deque length, sorts
  descending, returns top `limit`.

This is the standard "ring of timestamps" pattern. In production:
- The view event goes to a Kafka topic.
- A Flink / Spark Streaming job maintains the same structure, keyed
  on `(video_id, minute_bucket)`, in RocksDB state.
- A separate job emits a "top-N" snapshot every minute to a Redis
  sorted set — that's what the API reads from.

Why *1-minute buckets* and not lifetime views? Because lifetime
views are a popularity measure, not a *trending* measure. A
video uploaded last week with 10 M views should not out-trend a
live stream that's pulling 200 K views / minute.

---

## 8. Recommendation

Algorithm: **co-watch by user-watch history**.

```
For a target user U with recent watch list W = [v1, v2, v3]:
  for each video vi in W:
    for each user U' who also watched vi:
      weight[U'] += 1            # how similar they are to U
  candidates = union over (U' in top-K similar users) of their watch sets
  score[video] = sum over (U' in similar) of (similarity[U'] * 1[U' watched video])
  exclude videos already in W
  return top-N scored videos
```

Why this works:
- Users who watched the *same* videos tend to want the *same* next
  video. Co-watch is a strong, easy signal.
- It needs no embeddings, no ML serving infra. It runs in O(|W| ×
  avg_co_watchers) and is trivially explainable.

Production refinements (out of scope):
- Weight by recency of co-watch.
- Penalize overly-popular videos (they get recommended to everyone,
  drown out niche but relevant ones).
- Blend with content features (title / topic) and a learned ranker.

---

## 9. Failure modes

| Failure | What happens | Mitigation |
|---|---|---|
| **CDN miss → origin fetch** | First viewer in a region pays the S3 latency (~200 ms). Subsequent viewers hit the CDN. | Pre-warm CDN on upload complete; use long TTL on segments. |
| **CDN POP down** | All traffic for that region reroutes to nearest POP, increasing latency. | Multi-POP failover; health-check anycast. |
| **Metadata DB read timeout** | `get_video` returns 5xx, player can't start. App-side retry with idempotency. | Read-replica, circuit-breaker, serve `stale-while-revalidate` from L1 cache. |
| **Transcoder offline** | New uploads land but only the original (single-bitrate) rendition is playable. | Flag the video as `single-quality`, fall back to original MP4 in the player. App still works — just no ABR. |
| **Trending service down** | Trending tab errors out; playback unaffected. | Cache last good snapshot for 5 min; degrade silently. |
| **View-event queue backpressure** | Views are dropped or batched, lifetime counters lag. | Decouple view-write from read-write: ack first, aggregate later. |
| **Hot-key skew** (a single viral video) | All viewers hit the same metadata key. | TTLCache + CDN edge already absorb this. If DB becomes the bottleneck, add a `hot-shard` or in-memory replica. |

---

## 10. Tradeoffs

### Push CDN vs pull CDN
- **Pull (default)**: edge fetches from origin on first miss.
  Simpler, no upload coordination, but first viewer pays latency.
- **Push**: on upload complete (and after transcode), origin POSTs
  segments to each POP. First viewer is fast, but you pay for
  egress to every POP even if the video only goes viral in one
  region.

We pick **pull with pre-warm-on-trending**: most popular videos are
proactively pushed to the top 5 POPs, the long tail is pulled.

### Server-side ABR vs client-side ABR
- **Client-side ABR** (industry standard, what HLS/DASH enable): the
  player picks bitrate based on measured bandwidth. Server just
  serves the manifest. Better for heterogeneous networks.
- **Server-side ABR**: a manifest server picks bitrate per request
  based on the client's IP / device hint. More control, but
  more state, more ways to get it wrong.

We pick **client-side ABR with a server hint**: the metadata
response includes a "suggested starting bitrate" based on the
viewer's network class (Wi-Fi vs cellular), but the player is
free to ignore it.

### Push trending recompute vs streaming aggregation
- **Push (what we model)**: every minute, recompute the top-N from
  the window, write a single Redis sorted set. Reads are O(log N).
  1 minute of staleness, but cheap.
- **Streaming (Kafka + Flink)**: incremental, always-fresh top-N.
  More accurate, more infra, harder to operate.

For this course we pick push — same shape, simpler to reason about.

### Co-watch vs embedding-based recommenders
- Co-watch: explainable, fast, no training pipeline. Misses
  cold-start and content-side signals.
- Embedding-based (two-tower, ALS): more accurate, but needs an
  offline training job and an online vector index.

Real systems *blend*: co-watch for cold users, embeddings for
warm users, always with a content-based fallback for new uploads.

---

## 11. Code map

```
06_yt_or_netflix/
├── design/README.md            # this file
├── code/
│   ├── __init__.py
│   ├── service.py              # VideoService (no HTTP, pure logic)
│   └── app.py                  # Flask wrapper
└── tests/
    ├── __init__.py
    ├── test_service.py         # ≥6 unit tests on VideoService
    └── test_app.py             # ≥4 HTTP tests
```

- `VideoService` owns: video metadata, view deques, trending window,
  recommendation. Pure Python; takes `KeyValueStore` + `TTLCache` so
  tests are deterministic and persistence is swappable.
- `app.py` is the Flask wrapper. All endpoints are thin: parse,
  delegate, return JSON. Metrics are collected at the HTTP layer.
- Sample data lives at `system_design/sample_data/videos.jsonl` —
  not loaded automatically; you can use it to seed the service in
  `loadtest.py` (left as an exercise).
