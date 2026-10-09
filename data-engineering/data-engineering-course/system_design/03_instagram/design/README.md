# 03 — Instagram (Photo Sharing)

> **Lesson 3 of 6 — Read-Heavy Systems**

A photo-sharing service: users upload images, follow each other, and
view a personalized home feed of recent photos from people they follow.

---

## 1. Requirements

### Functional
- Upload a photo (image bytes + caption).
- View a single photo with metadata.
- Follow / unfollow another user.
- View the home feed: recent photos from people I follow, in time order.

### Non-functional
- **Read-heavy** — feeds are read orders of magnitude more than uploaded.
- p99 feed latency < 200 ms.
- Image bytes served from object storage (S3 / GCS / MinIO in prod).
- 100M+ users, 1B+ photos in production.

### Out of scope
- Stories, Reels, DMs, Explore ranking.
- Search.

---

## 2. Capacity

| Metric | Value |
|---|---|
| Photos | 1B (toy 5k) |
| Avg photo size | 200 KB (raw), 4 sizes stored → ~1 MB / photo |
| Total storage | ~1 PB raw images + 1 PB derivatives |
| Feed reads | 100k QPS peak |

---

## 3. High-level

```
[uploader] ──► [API] ──► [Object store (S3)]    # blob = image bytes
                       └► [Metadata DB]          # url, caption, user, ts
                       └► [Fanout worker]        # write to follower feeds
                                          │
                                          ▼
                              [Feed cache / Redis]   # feed:<user_id> = [photo_ids]
                                          │
                                          ▼
[viewer]   ──► [API] ──► [Feed cache] ──► [Object store CDN for images]
```

Two key choices:

- **Image bytes** live in object storage, not the DB. We only store URLs
  in the metadata DB.
- **Home feed** is materialized per-user. Two strategies:
  - **Fanout-on-write** (push): on upload, write the photo_id into every
    follower's feed list. O(followers) writes per upload. Read is O(1).
  - **Fanout-on-read** (pull): on read, query the photos of everyone
    I follow and merge. O(follows) reads per feed view.

We default to **fanout-on-write** (the original Instagram choice) because
reads are 100× writes. We document the hybrid in §10.

---

## 4. API

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/api/photos` | `{"user_id", "caption", "image_data": base64}` | `{"photo_id", "url", ...}` |
| `GET`  | `/api/photos/<id>` | — | full record |
| `POST` | `/api/follow` | `{"follower_id", "followee_id"}` | `{"ok": true}` |
| `POST` | `/api/unfollow` | `{"follower_id", "followee_id"}` | `{"ok": true}` |
| `GET`  | `/api/feed/<user_id>?limit=20` | — | `{"feed": [photo, ...]}` |
| `GET`  | `/api/users/<id>/photos` | — | user's own photos |
| `GET`  | `/metrics` | — | counters + histograms |
| `GET`  | `/health` | — | `{"ok": true}` |

---

## 5. Data model

```
photo:        { photo_id, user_id, caption, image_url, created_at, likes }
user:         { user_id, username, name, followers_count, following_count }
follow:       (follower_id, followee_id)        # social graph
feed_entry:   (user_id, photo_id, created_at)  # materialized feed
```

For storage we use a `KeyValueStore` per collection. In production:
- `photos` → sharded by `photo_id` (Cassandra / DynamoDB).
- `follows` → sharded by `follower_id` (graph DB or adjacency list).
- `feed_entries` → Redis list per user, capped (e.g. last 1000 photos).

---

## 6. Image bytes

We don't actually store binary images in this course — we generate a
deterministic placeholder URL (`https://cdn.example.com/photos/<id>.jpg`)
and skip the bytes. In a real system, you'd:

1. Receive a multipart upload.
2. Stream to S3, get a key back.
3. Trigger an async worker to produce 4 sizes (thumb, small, medium, large).
4. CDN-front S3 with cache-control headers and per-size paths.

For load tests we generate fake bytes via the seed script.

---

## 7. Feed read path

```
GET /api/feed/<user_id>?limit=20
  └─► cache_hit("feed:" + user_id)? return
  └─► feed_store.list(user_id, limit)
        └─► for each photo_id, photo_store.get(photo_id)  # batched
  └─► cache.set("feed:" + user_id, result, ttl=60s)
  └─► return
```

Reads are O(limit) and very fast. Cache hit rate on home feeds is
very high in production (>95%) because feeds change slowly.

---

## 8. Fanout-on-write deep dive

```
POST /api/photos
  └─► persist photo
  └─► enqueue fanout_job { photo_id, user_id }
                              │
                              ▼
            [Fanout worker pool]
              for follower in followers(user_id):
                feed_store.lpush("feed:" + follower, photo_id)
                feed_store.ltrim("feed:" + follower, 0, 999)   # cap
```

Cost per upload = O(followers). Mitigations:
- **Lazy fanout**: skip celebrities; pull at read time.
- **Batched writes**: pipeline the LPUSH calls.
- **Async**: don't block the upload on fanout (return 201, fanout in
  background).

---

## 9. Failure modes

| Failure | Mitigation |
|---|---|
| Hot celebrity upload (millions of followers) | Hybrid fanout: store in a "celebrity bucket" merged at read time. |
| Feed cache miss storm | Rate-limit per-user feed reads; serve stale-while-revalidate. |
| Object store unavailable | Photos stay invisible; upload fails. Reads for other users OK. |

---

## 10. Tradeoffs

- **Fanout-on-write vs fanout-on-read**: write-heavy, read-light user?
  Read-time. Celebrity user? Hybrid. Default user? Write-time.
- **Eventual consistency**: a follower's feed may lag the upload by
  seconds. Acceptable.
- **Photo likes**: not modeled in this lesson; in production a
  separate `likes` service + counter service.

---

## 11. Code map

| File | Role |
|---|---|
| `code/service.py` | InstagramService: photos, follows, feed. |
| `code/app.py` | Flask HTTP service. |
| `tests/test_service.py` | Service unit tests. |
| `tests/test_app.py` | HTTP tests. |
