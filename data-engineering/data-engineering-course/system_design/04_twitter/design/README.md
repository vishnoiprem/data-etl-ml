# 04 — Twitter / X (Microblogging Timeline)

> **Lesson 4 of 6 — Write-Heavy Fanout**

A microblogging service: users post short tweets, follow each other, and
view a personalized home timeline of recent tweets from the people they
follow, in reverse chronological order. The defining design choice is
how to deliver a tweet to millions of timelines cheaply.

---

## 1. Requirements

### Functional
- Create a user.
- Follow / unfollow another user.
- Post a tweet (text, optional `retweet_of` referencing another tweet).
- Like a tweet.
- View the home timeline: recent tweets from everyone I follow (incl. RTs),
  newest first, with celebrity tweets merged in at read time.
- Fetch a single tweet by id.

### Non-functional
- p99 home-timeline read < 200 ms.
- Tweets must reach the follower's timeline within a few seconds (eventual
  consistency is fine).
- Service must scale to 100M+ users and 500M+ tweets/day.
- Operationally cheap: a tweet from a normal user must not be a "big
  write" against the whole platform.

### Out of scope
- Replies / threads, DMs, search, ranking, ads, video, polls.
- Authentication. We trust `user_id` in the body.

---

## 2. Capacity

| Metric | Value |
|---|---|
| MAU | 100M (toy 500) |
| Tweets / day | 500M (toy ~20k) |
| Avg followers | ~200, but a long tail — top 0.01% have >1M |
| Timeline reads | 100k QPS peak |
| Tweets per timeline read | page of ~20 |

Back-of-envelope: at 500M tweets/day = ~6k QPS average, ~60k QPS peak.
Each tweet writes a row to the tweet store, and — for *normal* users —
one row per follower in the materialized feed list. If 99% of authors
have <10k followers, we can avoid fanning out the other 1% entirely
(see §8 — the **celebrity threshold**).

---

## 3. High-level

```
[client] ──► [API gateway] ──► [Tweet service] ──► [Tweet store (KV)]
                                        │
                                        ├─► [Fanout-on-write worker]
                                        │     │
                                        │     └─► [Per-user feed list (KV)]
                                        │
                                        └─► [Celebrity bucket] (pull at read)
                                                  │
[reader]   ──► [Timeline service] ──► [Per-user feed list]
                                  ├─► [Celebrity bucket]   # merge at read
                                  └─► [Tweet store] (batch lookup)
```

Two read-paths meet at "merge & rank":

- **Fanout-on-write (push)** — for normal authors (< celebrity_threshold
  followers), the tweet is pushed into each follower's materialised feed
  at write time. Read is then O(1) lookups against a list.
- **Pull-on-read** — for celebrities, we don't push to anyone. At read
  time, we look at the celebrities the viewer follows, fetch their
  recent tweets, and merge them with the materialised list.

The combination is the **hybrid delivery** model Twitter itself describes.

---

## 4. API

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/api/users` | `{user_id, username, name}` | user |
| `POST` | `/api/follow` | `{follower_id, followee_id}` | `{ok: true}` |
| `POST` | `/api/unfollow` | `{follower_id, followee_id}` | `{ok: true}` |
| `POST` | `/api/tweets` | `{user_id, text, retweet_of?}` | tweet |
| `GET`  | `/api/tweets/<id>` | — | tweet |
| `POST` | `/api/tweets/<id>/like` | — | `{tweet_id, likes}` |
| `GET`  | `/api/timeline/<user_id>?limit=` | — | `{user_id, tweets: [...]}` |
| `GET`  | `/metrics` | — | counters + histograms |
| `GET`  | `/health` | — | `{ok: true}` |
| `GET`  | `/` | — | service index |

---

## 5. Data model

```
tweet:        { tweet_id (snowflake), user_id, text, created_at,
                 likes, retweet_of: int|None, retweet_of_user: int|None }
user:         { user_id, username, name, followers_count, following_count }
follow:       adjacency lists keyed by follower_id / followee_id
feed_entry:   (user_id, tweet_id, ts)   # materialised home timeline
celeb:        (user_id)                 # "followers_count >= threshold"
```

Stores (all `KeyValueStore` in this course):

| Store | Key | Value | Shard-by (prod) |
|---|---|---|---|
| `tweets`     | `tweet:<id>`            | tweet dict | tweet_id |
| `users`      | `user:<id>`             | user dict  | user_id |
| `follows`    | `follow:<uid>` / `followed_by:<uid>` | list[int] | follower_id / followee_id |
| `feeds`      | `feed:<uid>`            | list of tweet_ids (capped) | user_id |
| `celeb_meta` | `celeb:<uid>`           | `{tweet_id: ts, ...}` last N | user_id |

Caching: a `TTLCache` for the assembled timeline, plus an in-process
TTLCache for tweet lookups. In prod these become Redis.

---

## 6. Home-timeline read path (hybrid)

```
GET /api/timeline/<user_id>?limit=20
  cache_key = "tl:" + user_id + ":" + limit
  cached = timeline_cache.get(cache_key)
  if cached: return cached                          # O(1)

  ids = feed_store.get("feed:" + user_id) or []     # pushed entries
  pushed = [Tweet(**t) for t in batch_get_tweets(ids)]

  celebs = [c for c in following(user_id)
            if is_celeb(c, threshold=10_000)]        # cheap O(follows)
  pulled = []
  for c in celebs:
      recent = celeb_store.get("celeb:" + c) or {}  # last N tweet_ids
      pulled.extend(get_tweets(recent.keys()))

  merged = merge_by_created_at_desc(pushed + pulled)[:limit]
  timeline_cache.set(cache_key, merged, ttl=60s)
  return merged
```

Why hybrid:

- A normal tweet reaches the read path via a single LPUSH per follower at
  write time, then a list trim at read time. The timeline lookup itself
  is a Redis range scan in prod.
- A celebrity tweet (e.g. *Elon*) would force a write to 100M+ lists if
  we blindly fanned out. So we never write it into anyone's feed — the
  celeb bucket is a *bounded* recent-tweets list keyed by the author.
  Read-side we look at the celebs the viewer follows and merge in.

---

## 7. Tweet creation (write path)

```
POST /api/tweets {user_id, text, retweet_of?}
  t = Tweet(snowflake.next_id(), user_id, text, ts=now,
            retweet_of=retweet_of or None)
  tweet_store.set("tweet:" + t.tweet_id, t)

  if retweet_of:                                  # 7a. retweet branch
      original = tweet_store.get("tweet:" + retweet_of)
      t.retweet_of_user = original.user_id
      tweet_store.set("tweet:" + t.tweet_id, t)   # update with lineage
      fanout(t)                                   # still fanout as the RT
      return t

  if is_celeb(user_id):                           # 7b. celeb branch
      celeb_store.lpush_keep_last("celeb:" + user_id, t.tweet_id, N=200)
      return t                                    # NO fanout

  fanout(t)                                       # 7c. normal fanout
  return t

def fanout(t):
  for follower in followers_of(t.user_id):
      _push_to_feed(follower, t.tweet_id)
```

Notes:

- We check `is_celeb` *before* fanning out, so a celebrity who is followed
  by 100M people writes to the celeb bucket only — O(1) work, not O(N).
- Retweets are first-class tweets. They carry `retweet_of`/`retweet_of_user`
  so the UI can render "RT @user" without a second lookup. We still
  fanout an RT into the follower's feed (this is how the RT spreads).

---

## 8. Fanout-on-write deep dive

```
                 +-----------------------+
POST /tweets ──► | is_celeb(author)?     |── yes ──► celeb bucket only
                 +-----------------------+
                          │ no
                          ▼
                for follower in followers(author):
                    feed = feed_store.get("feed:" + follower) or []
                    feed.append(tweet_id)
                    feed = feed[-FEED_CAP:]      # cap last 1000
                    feed_store.set("feed:" + follower, feed)
                    timeline_cache.delete("tl:" + follower + ":*")  # bust
```

Cost model:

| Author | Followers | Per-tweet writes |
|---|---|---|
| Normal (median, ~200 followers) | 200 | 200 |
| Power user (~10k followers) | 10k | 10k |
| Celebrity (>10k followers) | 100M | **0** (pull at read) |

Mitigations baked in:

- **Celebrity threshold** (`CELEB_THRESHOLD = 10_000`): above this, the
  celeb bucket takes over.
- **Bounded feed list** (`FEED_CAP = 1000`): each user's feed list is
  trimmed so it never grows unbounded. Older entries fall off the end.
- **Async fanout** (in prod): return 201 immediately, fanout in a worker
  pool. In this course we do it inline for simplicity, but the structure
  is identical.
- **Cache invalidation**: every push to a follower busts that follower's
  timeline cache key. We re-merge lazily on the next read.

In production Twitter uses a similar hybrid; the celeb threshold is
what makes a *normal* author's tweet cheap.

---

## 9. Failure modes

| Failure | Mitigation |
|---|---|
| Celebrity tweet storms one user's feed (we cap it) | `FEED_CAP` trim; older entries drop. |
| Fanout worker dies mid-fanout | Re-queue with `tweet_id`; idempotent LPUSH is fine if the list is a set or if we accept "appears twice" (we accept — RT ordering is best-effort). |
| Celeb bucket overflows | Bounded list (`CELEB_BUCKET_CAP = 200`); older celeb tweets fall off and become pull-on-history reads. |
| Cache stale (we just fanned out, but cache says old) | `timeline_cache.delete` on every push; new readers see the fresh merge. |
| Follower count drift (users are added/removed while we fanout) | Acceptable; re-fanout on next follow change. |

---

## 10. Tradeoffs

- **Pure fanout-on-write** — fast reads, but celebrity tweets are a
  write-amplification disaster.
- **Pure fanout-on-read** — fast writes, but every timeline read costs
  `O(follows × recent_tweets_per_follow)`. For a user following 1000
  accounts this is 1000s of reads per page view. Bad.
- **Hybrid (this design)** — best of both. We pay `O(followers)` for
  normal users and `O(num_celebs_followed)` at read time. The threshold
  keeps both small.
- **Eventual consistency** — a tweet appears in the follower's timeline
  within seconds. We do not implement 2-phase commit.
- **Retweets as first-class** — every RT is a real tweet row. Simpler
  than a separate RT table, slightly more storage.
- **Snowflake IDs** — time-sortable, fit in 64 bits, allow efficient
  range scans and natural merge ordering.

---

## 11. Code map

| File | Role |
|---|---|
| `code/service.py` | `TwitterService`: users, follows, tweets, timeline (hybrid), likes. |
| `code/app.py`     | Flask HTTP service. |
| `tests/test_service.py` | Unit tests for the service (incl. celebrity hybrid, retweets). |
| `tests/test_app.py`     | HTTP tests via Flask test client. |
