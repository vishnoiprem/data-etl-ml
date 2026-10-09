# 39 — Reddit Homepage

> **Lesson 5 of 6 — Read-Heavy Systems · Design the Reddit Homepage**

The Reddit homepage is the canonical "feed" problem at large scale:
personalized, ranked, with hundreds of millions of votes per day.

---

## 1. Requirements

### Functional
- Subreddits (communities), posts, comments, votes (up/down).
- Home feed: ranked posts from subscribed subreddits + r/all.
- Subreddit feed: ranked posts in one community.
- Vote (up/down), karma accumulation.

### Non-functional
- **Read-heavy** — homepage reads outnumber writes 100:1.
- Latency p99 < 300 ms for homepage.
- Eventually consistent for vote counts (acceptable to be a few seconds
  behind).
- Hundreds of millions of posts; billions of votes.

### Out of scope
- DMs, chat, mod tools.

---

## 2. Capacity

| Metric | Value |
|---|---|
| Subscribers | 500M+ |
| Active subreddits | 100k+ |
| Posts/day | ~1M |
| Votes/day | ~100M |
| Homepage reads/day | ~5B |
| Avg posts per subreddit feed | 50 (top), 1000 (new) |

---

## 3. High-level

```
[client] ──► [Edge / CDN] ──► [API] ──► [Feed service] ──► [Ranking service]
                                       │                    │
                                       │                    └─► [Vote aggregator]
                                       │
                                       └─► [Post / Comment DB] (sharded)
                                       └─► [Vote log] (Kafka / Kinesis)
                                       └─► [Materialized subreddit top lists]
```

The key insight: we don't compute the homepage from raw votes in real
time. We **precompute** ranked lists per subreddit and merge them at
read time, with user-affinity adjustments.

---

## 4. Ranking (the heart of the system)

Reddit's hot-score formula (Wilson interval-based, simplified):

```
score = log10(max(|s|, 1)) * sign(s) + (ts - epoch) / 45000
```

Where:
- `s` = upvotes - downvotes
- `ts` = post creation timestamp
- `epoch` = a fixed constant
- `sign(s)` = +1 or -1

The first term rewards votes; the second rewards recency. The magic is
the log dampens early votes, so a post that hits 10k votes doesn't
dominate forever — it eventually gets outranked by fresher posts.

We implement this directly. See `service.py`.

---

## 5. API

| Method | Path | Returns |
|---|---|---|
| `POST` | `/api/subreddits` | `{"id", "name"}` |
| `POST` | `/api/users/{id}/subscribe` | `{"ok": true}` |
| `POST` | `/api/subreddits/{id}/posts` | new post |
| `POST` | `/api/posts/{id}/vote` | `{"score", "hot_score"}` |
| `GET`  | `/api/subreddits/{id}/?sort=hot|new|top` | list |
| `GET`  | `/api/users/{id}/home?limit=` | merged home feed |
| `GET`  | `/metrics` | counters |
| `GET`  | `/health` | `{"ok": true}` |

---

## 6. Read path: homepage

```
GET /api/users/{id}/home
  └─► fetch subscribed subreddits
  └─► for each subreddit, fetch precomputed top-K (cached in Redis)
  └─► merge + re-rank by recency × user-affinity (e.g. subscribed bonus)
  └─► cap to limit, return
```

The heavy lifting is **precomputed**. Subreddit top-K updates
incrementally as votes arrive.

---

## 7. Vote write path

```
POST /api/posts/{id}/vote {user_id, dir: +1|-1|0}
  └─► idempotency: lookup existing vote
  └─► if changed, append to vote-log (Kafka topic)
  └─► async: vote aggregator updates per-post counters
  └─► async: hot-score recompute for affected subreddits
  └─► cache invalidation
```

We don't recompute the homepage on every vote. We recompute the
subreddit's top-K (much smaller).

---

## 8. Failure modes

| Failure | Mitigation |
|---|---|
| Vote log consumer lag | Eventually-consistent vote counts; UI shows "loading" for a sec. |
| Hot-score recompute slow | Cache last-known good; show slightly stale. |
| Reddit hug-of-death (viral post) | Edge cache + rate-limit per-IP. |
| Trending spike | Pre-warm cached lists. |

---

## 9. Tradeoffs

- **Materialized lists vs compute on read**: materialized wins. Vote
  log enables incremental updates.
- **Hot vs New vs Top**: three sort modes, three storage strategies.
  We support all three in this lesson.
- **Vote dedup**: a user can vote once. Store `(post_id, user_id, dir)`
  in a set or unique index.

---

## 10. Code map

| File | Role |
|---|---|
| `code/service.py` | RedditService with subreddits, posts, votes, ranking. |
| `code/app.py` | Flask HTTP service. |
| `tests/test_service.py` | Service tests including hot-score ordering. |
| `tests/test_app.py` | HTTP tests. |
