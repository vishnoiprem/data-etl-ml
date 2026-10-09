# Module 05 — Newsfeed (Ranked)

A Facebook-style home feed. Unlike a pure chronological timeline, the feed is
**ranked**: every candidate post is scored by recency, affinity (whether the
author is someone you follow), and an engagement-weight × popularity term. The
read path merges a materialized "fanout" feed with a lightweight ranker pass
so the wall stays fast even when the ranker is busy.

## Requirements

**Functional**

- Users sign up, follow / unfollow other users.
- Users author text posts (no media in this module — Instagram covers that).
- Engagement signals: `like`, `comment`, `share` — each increments a counter
  on the post.
- `GET /api/feed/<user_id>` returns a ranked list of posts to show on a user's
  home wall.
- Engagement updates invalidate the affected user's feed cache so the next
  reader sees fresh scores.

**Non-functional**

- Read-heavy (1k:1 read:write). p95 read latency < 50 ms in-process.
- Eventually-consistent engagement counters — a stale like count is fine.
- Ranker must be **degrade-able** to chronological order if the scoring
  subsystem throws.
- Cache must bound memory (LRU/TTL) and never return truly stale results.

## Capacity

| Quantity              | Assumption                |
| --------------------- | ------------------------- |
| DAU                   | 200 M                     |
| Posts/day             | 500 M                     |
| Read:write            | ~1,000 : 1                |
| Median follows        | 200 (fanout is small)     |
| Heavy creator follows | up to 50 k (skip fanout)  |
| Feed page size        | 20 posts                  |
| Posts scanned / page  | ~500 candidates           |
| Engagement events     | ~50 / post / lifetime     |

Back-of-envelope: ranking a single feed page = O(candidates × log candidates)
+ O(follows) for affinity. At 500 candidates with simple arithmetic scores
this is sub-millisecond per page; the bottleneck is the candidate-generation
fanout step, not the score function.

## High-level

```
                 ┌─────────────────────┐
   POST /posts ─►│  ingest / fanout    │──┐
                 └─────────────────────┘  │  push to materialized feeds
                                         ▼
                              ┌──────────────────────┐
                              │  KeyValueStore       │  posts, follows,
                              │  (posts/users/follow │  materialized feeds
                              │   /materialized)     │
                              └──────────────────────┘
                                         │
   GET /feed/<user> ─►  read materialized feed
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │  Ranker              │  score = recency *
                              │                      │   (1 + log10(eng+1)) +
                              │                      │   0.1 * affinity
                              └──────────────────────┘
                                         │
                                         ▼
                                ranked top-N  ──►  TTLCache (per user)
```

- **Ranking service** is a single Python function in this module. In
  production it would be a small C++/Java microservice; the contract is
  pure: it takes candidate post ids + a viewer and returns a scored,
  ordered list.
- **Fanout-hybrid** by default. We materialize the feed on write for users
  with < 1,000 followees (write path is fast and reads are O(1)). For
  "celebrities" with massive follower counts we skip the materialization
  and merge on read — same scoring function, but the candidate set is
  drawn from a per-author post log instead of the viewer's materialized
  list. This is the "fanout-on-read" half of the hybrid.

## API

| Method | Path                          | Body / Query                       | Returns                          |
| ------ | ----------------------------- | ---------------------------------- | -------------------------------- |
| POST   | `/api/users`                  | `{user_id, username, name}`        | `201 User`                       |
| POST   | `/api/follow`                 | `{follower_id, followee_id}`       | `200 {ok}`                       |
| POST   | `/api/unfollow`               | `{follower_id, followee_id}`       | `200 {ok}`                       |
| POST   | `/api/posts`                  | `{user_id, text}`                  | `201 Post`                       |
| POST   | `/api/posts/<id>/engage`      | `{kind: "like"\|"comment"\|"share"}`| `200 {counts}`                  |
| GET    | `/api/feed/<user_id>`         | `?limit=20`                        | `200 {posts:[…]}` (ranked)       |
| GET    | `/metrics`                    | —                                  | Prometheus-style text            |
| GET    | `/health`                     | —                                  | `200 {ok, stats}`                |
| GET    | `/`                           | —                                  | service description              |

## Data model

```python
User      { user_id, username, name, followers_count, following_count }
Post      { post_id, user_id, text, created_at,
            likes, comments, shares, engagement }
Follow    { follower_id -> [followee_id, ...] }  # mirrored both directions
Engagement{ post_id -> { likes, comments, shares } }  # counters in KV
```

`engagement = likes + 2*comments + 3*shares` is a single rollup used in the
score so the ranker only needs one number, not three. Engagement signals are
kept per-kind for analytics.

**Materialized feed** (`fanout:<viewer_id>`) is a list of `post_id`s capped
at `FEED_CAP = 1,000` posts. It is **the** read-path accelerator; the ranker
just re-orders whatever lives there (and, for celebrities, appends
read-time candidates from `posts_by:<author_id>`).

## Scoring formula

```
score(post, viewer, now) =
        1 / (age_hours + 2) ^ 1.5
      * (1 + log10(1 + engagement(post)))
      + 0.1 * affinity(viewer, post.author)
```

Where:

- `age_hours = (now - post.created_at) / 3600`. The `+ 2` and `^1.5` give
  a sharp recency curve: a 0-hour post beats a 24-hour post with
  ~17× weight, even with similar engagement.
- `engagement = likes + 2*comments + 3*shares`. `log10` tames outliers so
  one viral post doesn't completely dominate the wall.
- `affinity = 1.0` if the viewer follows the author, else `0.2`. The
  `+ 0.1 * affinity` term is a small constant boost; the dominant signal
  for non-followed content is recency × engagement (e.g. shares from
  friends-of-friends that bubbled up organically).

The 0.1 coefficient is intentionally small — affinity acts as a tie-breaker
and a "trust" signal, not a primary ranker.

## Read path

1. Pull `fanout:<viewer>` (or, for the viewer's own following-of-celebrities,
   also pull `posts_by:<author>` for each celebrity). This is the **candidate
   set**.
2. Hydrate post objects (one batched KV read).
3. Compute `score(post, viewer, now)` for each candidate.
4. Sort descending, take top `limit`.
5. Cache `(viewer, limit) -> ranked_post_ids` in a `TTLCache` with a 60s
   TTL. Engagement / new-post events bust the entry.

## Failure modes

- **Ranker throws / times out.** `rank_feed` falls back to chronological
  order — same candidates, no score. The user still sees a feed, just a
  less-personalized one. We log the exception and increment
  `ranker_fallback_total`.
- **KeyValueStore unavailable.** The HTTP layer returns 503. The KV is in
  memory in this module, so this is a placeholder for the real outage
  path; a production system would queue writes.
- **Feed cache poisoned** (e.g. we cached an empty feed because a write
  hadn't replicated). Cache TTL is short (60s) and engagement events bust
  individual keys. Self-healing within a minute.
- **Fanout queue stuck** for a popular user. Reads still work — the ranker
  just sees fewer candidates. The wall may feel "stale" but does not
  error.
- **Engagement counter drift.** Counters are incremented under the
  KeyValueStore lock but are not transactional across kinds. A crash
  between `like` and `comment` increments leaves a tiny skew, accepted
  in the spec.

## Tradeoffs

- **Ranker cost vs UX.** Each feed read scans ~500 candidates, hydrates
  them, and runs a Python expression per post. That's a few hundred µs in
  Python; a Java/C++ service would be sub-100 µs. The UX win of a
  ranked feed is huge (≈10–30% more time-on-site historically for
  ranked-vs-chrono), so the cost is worth it. The escape hatch
  (chrono fallback) keeps the cost off the critical path if the ranker
  ever becomes a bottleneck.
- **Materialized feed vs read-merge.** Materialization makes reads O(1) and
  ranking O(candidates). The downside is the write-amplification of
  fanout — a celebrity with 5M followers pays for that on every post. We
  mitigate with the hybrid: celebrities skip the fanout and are
  read-merged. The trade is more read work for the celebrity's followers
  (still cheap) vs. much less write work for the celebrity (huge win).
- **TTL vs invalidation.** We bust on writes (post create, engagement) and
  also use a 60s TTL. Pure invalidation would feel "live" but risks
  serving nothing during a write-storm. The 60s ceiling guarantees a
  non-empty feed even if invalidation drops.
- **Snowflake IDs** give us time-sortable post ids "for free", which
  means candidate generation can stop scanning once it hits old posts.

## Code map

| File                  | Purpose                                                       |
| --------------------- | ------------------------------------------------------------- |
| `code/service.py`     | `NewsfeedService` — user/follow/post/engagement + ranker.     |
| `code/app.py`         | Flask HTTP surface. `PORT` env, default 8005.                 |
| `tests/test_service.py` | ≥6 unit tests on the service.                              |
| `tests/test_app.py`   | ≥4 HTTP tests.                                                |
| `design/README.md`    | This document.                                                |
