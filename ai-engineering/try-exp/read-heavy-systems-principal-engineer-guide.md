# Designing Read-Heavy Systems Like a Principal Engineer

## Why a single Instagram post can quietly melt a database — and how every layer in front of it earns its keep

> *“A viral post is written once and read millions of times.”*
> If your system treats those two numbers the same, you will spend your weekends on-call. If it treats them differently, you get to sleep.

I want to walk you through one of the most important patterns in system design — the **read-heavy pattern** — the way I would explain it to a senior engineer joining my team. Not the textbook version. The version that survives a launch, a Super Bowl ad, and a cold cache at 3 a.m.

By the end of this article, you will be able to:

- Explain *why* read-heavy systems need a different architecture than write-heavy ones.
- Sketch the five-layer read path from CDN to primary DB.
- Choose between cache-aside, write-through, and precomputed read models with intent.
- Handle the celebrity problem, the cache stampede, the cold start, and replication lag.
- Defend your design in a system design interview *and* in a real production review.

Let’s start with the uncomfortable truth.

---

## 1. The asymmetry that breaks naive designs

Picture Instagram. A celebrity with 300 million followers taps “post.” One write.

A few seconds later, 300 million people tap “refresh.” 300 million reads. The same single post.

The read-to-write ratio is **300,000,000 : 1** for that one piece of content. Over a day, the average user generates a handful of writes but consumes thousands of posts. The ratio across the entire product is somewhere between **100:1 and 10,000:1**.

```
Read:Write asymmetry in real systems
─────────────────────────────────────────────────────────────
Instagram feed      reads >> writes           ~10,000 : 1
Amazon product page reads >> writes           ~1,000  : 1
Twitter timeline    reads >> writes           ~500    : 1
Uber ride history   writes >> reads           ~1      : 100  (write-heavy!)
Bank ledger         balanced + strict         ~1      : 1
```

Here is the principle I tattoo on every new system design doc:

> **Do more work at write time so that every read does less work.**

Every technique in this article is a variation of that one sentence. Caching, replication, denormalization, materialized views, precomputed feeds — they are all just ways of saying “we already paid for this answer once, let’s not pay again.”

The trade is straightforward, and we should never pretend otherwise:

- **Time vs. space.** Storing more copies costs memory and disk.
- **Freshness vs. speed.** More copies means more chances they disagree.

The job of a principal engineer is not to maximize speed or to maximize freshness. It is to pick the **least expensive technique that meets the freshness budget of each surface**.

---

## 2. The naive design (and why it dies)

Let’s design the Instagram home feed the way a junior engineer would.

```
Open app → look up who I follow → fetch last 50 posts per account
         → merge → rank → hydrate author info, like counts
         → return first 20
```

Looks innocent. Let’s count the work for a user who follows 500 accounts:

```
Per open of the app
─────────────────────────────────────────────────────────────
1   SELECT id FROM follows WHERE follower = me              (500 rows)
500 SELECT * FROM posts WHERE author_id = ? ORDER BY ts    (50 rows each → 25,000 rows)
500 JOIN users ON author_id                                  (25,000 author lookups)
1   aggregation, ranking, sorting
─────────────────────────────────────────────────────────────
≈ 1,001 queries, ≈ 50,000 rows shuffled, all on one user action
```

Multiply by 500 million daily active users, and you realize the database is not slow. It is **structurally incapable of doing this work**.

The naive design has a single disease: **it recomputes the answer on every read**. The read-heavy pattern is the cure: **compute the answer once, store it, and serve the stored copy.**

---

## 3. The five layers that turn a dying database into a serving machine

Before we zoom in, here is the full anatomy. Every line in this diagram is a place we can put a copy of the data, and therefore a place we have to think about freshness.

```
                          ┌──────────────────────────────────┐
                          │            CLIENT                │
                          │  (mobile app / browser / device) │
                          └──────────────┬───────────────────┘
                                         │  static assets / API
                                         ▼
            ┌────────────────────────────────────────────────────┐
            │  ①  CDN / EDGE                                   │  ← cheapest read
            │     (CloudFront, Cloudflare, Akamai)              │     (may never hit you)
            └──────────────┬────────────────────────────────────┘
                           │ miss → forward
                           ▼
            ┌────────────────────────────────────────────────────┐
            │              LOAD BALANCER                        │  ← spreads traffic,
            │        (ALB / NGINX / Envoy)                      │     keeps tier stateless
            └──────────────┬────────────────────────────────────┘
                           │
                           ▼
            ┌────────────────────────────────────────────────────┐
            │  ②  APP TIER  (stateless, horizontally scaled)     │  ← business logic
            └──────────────┬────────────────────────────────────┘
                           │
                           ▼
            ┌────────────────────────────────────────────────────┐
            │  ③  APPLICATION CACHE  (Redis / Memcached)         │  ← hot objects,
            │                                                    │     TTL or event-driven
            └──────────────┬────────────────────────────────────┘
                           │ miss
                           ▼
            ┌────────────────────────────────────────────────────┐
            │  ④  READ REPLICAS  (async replicas of primary)     │  ← multiplies read QPS
            └──────────────┬────────────────────────────────────┘
                           │ only the rare miss
                           ▼
            ┌────────────────────────────────────────────────────┐
            │  ⑤  PRIMARY DATABASE  (source of truth, writes)   │  ← most protected node
            └────────────────────────────────────────────────────┘
```

**The mental model:** each layer catches what the layer above it missed. The request that survives all five is rare, and it had better be cheap.

Let me walk down the stack.

---

## 4. Layer ① — CDN and edge caching

The CDN is the cheapest read you can serve, because **it never reaches your infrastructure**.

What lives at the edge:

- **Static assets:** images, video, JS bundles, fonts. Set far-future `Cache-Control: public, max-age=31536000, immutable` and version the URL.
- **Semi-static content:** rendered HTML for anonymous homepages, public profile pages, product detail pages.
- **API responses:** for *some* GETs, with care. Stripe’s homepage pricing JSON, GitHub’s public repo metadata.

The single most important rule for CDN work:

> **Separate the URL from the content.** If you change the content, change the URL (a hash, a version, a timestamp). Never expect the CDN to “know” the content changed.

```
https://cdn.example.com/avatar/<user_id>.jpg?v=<content_hash>
```

When the user updates their avatar, the hash changes, the URL changes, the CDN treats it as a brand-new object. No invalidation round-trip. No race conditions. No “stale avatar for 6 hours” bug.

**Failure mode to remember:** if your origin is down and the CDN has no `stale-if-error` directive, every cache miss becomes a 5xx. Set `stale-if-error=86400` for anything user-visible.

---

## 5. Layer ② — Application cache (Redis / Memcached)

Once a request actually reaches your application, the next cheap read is an in-memory key-value store: **Redis** or **Memcached**. This is where most of your read amplification should be absorbed.

What you put here:

- User profiles and session objects
- Rendered feed pages for hot users
- Product documents
- Rate-limit counters
- Distributed locks for stampede control

### 5.1 The four access strategies — pick deliberately

| Strategy        | Read path                                        | Write path                                       | When to use                              |
|-----------------|--------------------------------------------------|--------------------------------------------------|------------------------------------------|
| **Cache-aside** | App checks cache, falls through to DB on miss, populates | App writes to DB, then invalidates or sets cache | The default. Most apps start here.       |
| **Read-through**| App calls cache, cache library calls DB on miss  | App writes to DB, then writes to cache           | When the cache library owns the lifecycle |
| **Write-through**| App writes cache, cache writes DB synchronously | App writes cache, cache writes DB synchronously | When the cost of a stale read is high    |
| **Write-behind**| App writes cache only                            | App writes cache, cache flushes to DB async      | When you can lose acknowledged writes    |

I have seen more outages from **write-behind** than from any other pattern. The cache process dies, the DB never gets the write, and the user is angry in a way that paging cannot fix. Use write-behind rarely, deliberately, with WAL-equivalent semantics.

### 5.2 A real cache-aside implementation

```python
async def get_user_profile(user_id: str) -> dict:
    key = f"user:{user_id}"

    # 1. Try cache first
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)

    # 2. Miss → fetch from source of truth
    profile = await db.fetchrow(
        "SELECT id, name, bio, avatar_url FROM users WHERE id = $1",
        user_id,
    )
    if not profile:
        # 3a. Negative cache the "not found" for 60s
        await redis.set(f"{key}:nf", "1", ex=60)
        return None

    # 3b. Populate cache with TTL + jitter
    ttl = 300 + random.randint(0, 60)  # 5–6 min, jittered
    await redis.set(key, json.dumps(dict(profile)), ex=ttl)
    return dict(profile)
```

Two things to notice:

1. **TTL with jitter.** A whole class of keys (say, every user profile) all expiring at second 300 is a recipe for a stampede. The `+ random.randint(0, 60)` spreads expirations across a minute.
2. **Negative caching for misses.** Without it, an attacker pounding `GET /users/<random_uuid>` walks straight through the cache and DDoSes your database.

### 5.3 The cache key contract

I treat cache keys as a first-class schema, with a written-down contract:

```
user:{user_id}                  → UserProfile      (TTL 300s ± 60s jitter)
user:{user_id}:followers:count  → int              (TTL 60s)
post:{post_id}                  → Post             (TTL 600s)
feed:{user_id}:home:v{version}  → List[PostId]     (TTL 120s)
product:{sku}                   → ProductDocument  (TTL 300s)
```

The `v{version}` part is deliberate. When a user updates their profile, you do not need to find and delete every cached page that referenced them. You bump a version integer, and every key that includes the version misses. We’ll come back to this when we talk about invalidation.

---

## 6. Layer ③ — Load balancing (the silent prerequisite)

A subtle but important point: **none of the layers above work if the app tier is stateful**. The load balancer spreads requests across N app servers, but it can only do that if any app server can serve any request. If session state lives in a particular server’s memory, the load balancer can’t freely route, and you can’t freely scale.

The pattern is:

```
       Client
         │
         ▼
   ┌──────────────┐
   │ Load balancer│
   └──────┬───────┘
          │
   ┌──────┴──────────────────────────────┐
   ▼              ▼              ▼       ▼
 App-01       App-02       App-03   App-04    ← all stateless
   │              │              │       │
   └──────────────┴──────────────┴───────┘
                  │
                  ▼
              Redis + DB
```

Stateless app tier + sticky state in Redis/DB is what lets you answer “we have 5x traffic tomorrow” with “spin up 4x more app servers.”

---

## 7. Layer ④ — Read replicas (and replication lag)

The primary database handles all writes. Those writes are asynchronously streamed to one or more replicas, which serve reads. This **multiplies read throughput linearly with the number of replicas**, without changing the application’s query patterns at all.

```
                writes
   Client ─────────────────►  Primary DB
                              │
                              │  async replication
                              │  (WAL shipping / change streams)
                              ▼
              ┌──────────┬──────────┬──────────┐
              ▼          ▼          ▼          ▼
           Replica-1  Replica-2  Replica-3  Replica-4
              │          │          │          │
              └──────────┴─────┬────┴──────────┘
                                │
                                ▼
                          reads served
```

The catch is in the word **asynchronous**. Replicas lag. The lag is usually 10–500ms, but under load it can spike to seconds. This is the source of the most common bug in read-heavy systems.

### 7.1 The classic bug

```
1. User posts a comment  → POST /posts/123  → primary DB
2. User reloads feed     → GET /feed       → routed to replica
3. Replica hasn't seen the write yet → comment not in feed
4. User: "My comment disappeared!"
```

### 7.2 The fix: read-your-own-writes

There are four techniques, and the right answer is usually “all of them, applied surgically.”

1. **Sticky session on the primary.** After a write, pin *that user’s* reads to the primary for a short window (e.g. 5 seconds).
2. **Monotonic reads.** Route a single user to the same replica for the duration of a session, so the view never goes backward in time.
3. **Version tokens.** The write returns a `version` token. The client passes it on subsequent reads; the read path waits until the replica has caught up to at least that version.
4. **Optimistic UI.** Render the comment client-side immediately, marked as “pending,” and reconcile when the server confirms.

```
User A writes ──► primary
                  │
User A reads ────► primary (pinned for 5s after write)
User B reads ────► any replica (eventual consistency is fine)
```

The trade is explicit: **the writer pays a consistency cost so the rest of the world can stay eventually consistent**.

---

## 8. Layer ⑤ — Precomputed read models (denormalization)

Caching is “store the result of this query.” Precomputed read models are “store the answer to a question we know we’ll be asked a thousand times, in exactly the shape we’ll ask it.”

The two big flavors:

### 8.1 Materialized feeds (the Instagram story)

When a user posts, a fan-out worker pushes the post into every follower’s precomputed timeline.

```
                    Write path
                    ───────────
User A posts         ┌────────────────────────┐
   │                 │  Fan-out worker        │
   ▼                 │  (Kafka consumer)      │
Primary DB           └────────────┬───────────┘
                                 │
                ┌────────────────┼────────────────┐
                ▼                ▼                ▼
        follower-1's       follower-2's       follower-3's
        timeline list      timeline list      timeline list
        (Redis)            (Redis)            (Redis)

                    Read path
                    ──────────
User opens app → GET /feed
                 → MGET timelines for all followees
                 → merge, rank, hydrate
                 → return top N
```

**Reads become a single MGET.** A multi-thousand-row join collapses into a single network round-trip to Redis.

### 8.2 Denormalized product document

Instead of:

```sql
SELECT p.*, i.qty, pr.amount, r.avg_rating
FROM products p
JOIN inventory i ON i.sku = p.sku
JOIN pricing   pr ON pr.sku = p.sku
JOIN reviews   r  ON r.sku  = p.sku
WHERE p.sku = ?
```

you store one document in Redis or Elasticsearch:

```json
{
  "sku": "ABC-123",
  "name": "Wireless Headphones",
  "price": 199.00,
  "inventory": { "warehouse-1": 42, "warehouse-2": 17 },
  "rating": 4.6,
  "review_count": 1283,
  "last_updated": "2026-09-29T14:48:01Z"
}
```

Reads become a single `GET product:ABC-123`. Writes are event-driven: a price change emits `product.price.changed`, a consumer rebuilds and rewrites the document.

---

## 9. Fan-out on write vs. fan-out on read (the celebrity problem)

The most common interview trap in this domain, and a real production failure mode.

### 9.1 Fan-out on write (push)

```
User posts ──► for each follower: write post into their timeline
```

- Reads are dirt cheap (one MGET).
- Writes cost O(followers).

### 9.2 Fan-out on read (pull)

```
User reads ──► fetch posts from everyone they follow, merge, rank
```

- Writes are cheap.
- Reads are expensive (back to the naive design).

### 9.3 The celebrity problem

A user with **100M followers** posts. Fan-out-on-write creates 100M timeline writes. Even at 100k writes/sec, that is **17 minutes of write amplification per celebrity tweet**. Your Kafka is on fire, your replicas are lagging, your database is exhausted, and Taylor Swift broke your architecture.

The fix is **hybrid fan-out**, which is what Twitter actually does:

```
Write path
──────────
For normal users (< some follower threshold, say 10k):
    fan out on write — push into every follower's timeline

For celebrities (> threshold):
    do NOT fan out on write
    just write the post to the primary

Read path
─────────
For every user:
    1. Read precomputed timeline (covers normal follows)
    2. For each celebrity the user follows, pull recent posts
    3. Merge and rank by recency + engagement signals
```

This is the **right** answer for any system design interview that mentions feeds. If you say only “fan out on write” with no mention of the celebrity problem, you are signaling mid-level, not senior.

---

## 10. Cache invalidation — the hard part

We have been pretending the cache is always fresh. It is not. Every copy of the data has a **freshness budget**, and we must declare it.

| Surface                | Acceptable staleness | Technique                                    |
|------------------------|----------------------|----------------------------------------------|
| Public profile page    | Minutes              | CDN cache + TTL                              |
| User’s own profile     | Seconds              | CDN bypass on auth + short Redis TTL         |
| Like count             | 10–60 seconds        | Cache-aside with TTL                         |
| Follower count         | 5–15 minutes         | Cache-aside + TTL, or precomputed counter    |
| Inventory at PDP       | 30–60 seconds        | Cache-aside with TTL                         |
| Inventory at checkout  | Strong consistency   | **No cache.** Read primary.                  |
| Account balance        | Strong consistency   | **No cache.** Read primary.                  |
| Trending leaderboard   | 1–5 minutes          | Periodic precomputation + cache-aside        |

The last two rows matter more than the first six. **Not everything belongs in a cache.** If you cache a bank balance and serve a withdrawal against a stale number, you have invented money. If you cache inventory and oversell by 30%, you have a customer service nightmare.

### 10.1 Four invalidation strategies

```
Invalidation strategy ladder  (least → most effort)
─────────────────────────────────────────────────────────────
TTL expiry              "every entry dies after N seconds"
Explicit invalidation   "on write, DEL the key"
Event-driven            "write publishes event, consumer rebuilds"
Versioned keys          "bump version, old keys become unreachable"
```

**TTL** is the universal default. Simple, bounds staleness, easy to reason about. Pair it with jitter.

**Explicit invalidation** is precise but dangerous. You must own *every* write path. Miss one — a backfill job, an admin tool, a migration script — and the cache serves stale data forever.

**Event-driven invalidation** is how production-grade denormalized read models stay current. The write publishes `user.updated` to Kafka, a consumer reads the event, rebuilds the affected documents, and writes them back to Redis/Elasticsearch. This is the right answer when the read model is non-trivial.

**Versioned keys** sidestep invalidation entirely. The cache key is `feed:{user_id}:v{version}`. When the user updates their profile, you bump their version. Old keys become unreachable and expire naturally. There is no `DEL` to forget.

### 10.2 A worked example

User 42 changes their display name from “alice” to “Alice”.

```
Without versioning:
    1. UPDATE users SET name = 'Alice' WHERE id = 42
    2. DEL user:42
    3. DEL feed:42:home             ← easy
    4. DEL feed:42:home:page:1      ← if you paginate
    5. DEL every comment cache referencing user 42   ← IMPOSSIBLE
    6. ???

With versioning:
    1. UPDATE users SET name = 'Alice' WHERE id = 42
    2. INCR user:42:version  → v17
    3. Done. Every key was feed:42:v16, which now misses.
       Old keys expire on their own TTL.
```

Versioned keys are the single biggest defensive technique I know in this space.

---

## 11. The failure modes that ruin weekends

Every layer in front of the database is a new way to fail. Here are the four that take down real systems.

### 11.1 Cache stampede (the “thundering herd”)

A hot key expires. 50,000 concurrent requests all miss at the same instant. All 50,000 fan out to the database. The database melts.

```
Time t=0     key hot:post:12345 expires
Time t=0+ε   50,000 requests arrive simultaneously
Time t=ε     50,000 concurrent SELECTs hit the database
Time t=ε+τ   DB CPU 100%, p99 latency through the roof
```

Mitigations, in order of importance:

1. **TTL jitter** — never let a whole class of keys expire at the same instant.
2. **Per-key locking** — one request wins the lock and recomputes; the others wait or serve stale.
3. **Stale-while-revalidate** — serve the old value while one request refreshes in the background.

```python
async def get_post(post_id):
    key = f"post:{post_id}"
    val, ts = await redis.hmget(key, "value", "ts")

    if val and (now - ts) < STALE_TTL:
        return val                          # fresh

    if val:                                # stale but usable
        asyncio.create_task(refresh(post_id))
        return val                          # serve stale, revalidate async

    # truly missing — single-flight
    async with redis.lock(f"{key}:lock", timeout=5):
        return await recompute(post_id)
```

### 11.2 Cold start

A deploy, a `FLUSHDB`, or a cache node failure sends every request to the database at once. If the database can’t survive an empty cache, the cache is not an optimization — it is a **required dependency**.

The rule:

> **Before you add caching, prove your database can survive an empty cache. Then add caching.**

If it can’t survive, your options are:

- Pre-warm the cache on deploy (load top-N keys from DB).
- Add a read-through fallback so the cache can rebuild itself.
- Scale the database first, *then* add caching.

### 11.3 Hot keys

A celebrity profile or a viral product concentrates traffic on one cache node. Redis is single-threaded per shard; one hot key can saturate one shard while the others are idle.

Mitigations:

- **Replicate the hot key** to N shards, read from a random replica.
- **In-process LRU** in front of Redis for the top 1% of keys.
- **Local cache** at each app server for the most extreme hot keys.

### 11.4 Cache penetration

Attackers pound `GET /users/<random-uuid>`. Every request misses the cache, hits the database, returns nothing. Your database is doing useless work at scale.

```python
async def get_user(user_id):
    key = f"user:{user_id}"

    cached = await redis.get(key)
    if cached is not None:
        return json.loads(cached) if cached != "__missing__" else None

    if await redis.get(f"{key}:nf"):
        return None                       # negative cache hit

    row = await db.fetchrow(...)
    if not row:
        await redis.set(f"{key}:nf", "1", ex=60)
        await redis.set(key, "__missing__", ex=60)
        return None
```

For very large keyspaces, add a **Bloom filter** in front of the cache: if the Bloom filter says “definitely not in the set,” don’t bother hitting the cache at all.

---

## 12. Replication lag, revisited — the full read-your-own-writes toolkit

Let me show all four read-your-own-writes techniques in one diagram, because you will need them in different combinations.

```
                     ┌──────────────┐
                     │   Client     │
                     └──────┬───────┘
                            │ POST /comment
                            ▼
                     ┌──────────────┐
                     │  Primary DB  │
                     └──────┬───────┘
                            │ returns version=v17
                            │
                            ▼
                     ┌──────────────┐
                     │  Client UI   │  ← renders optimistically
                     └──────┬───────┘
                            │ GET /feed?since=v17
                            ▼
              ┌─────────────────────────────┐
              │   Read router               │
              │   - if user wrote recently: │
              │       pin to primary (5s)   │
              │   - else:                   │
              │       route to replica,     │
              │       wait until replica    │
              │       reaches v17           │
              └─────────────────────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │    Feed      │
                     └──────────────┘
```

The key insight: **this is per-user, not global**. You do not pay the consistency cost for the entire world. Only the writer does, briefly.

---

## 13. When to use the pattern (and when not to)

### Use it when

- **Read:write ratio is ≥ 10:1.** Feeds, catalogs, content sites, dashboards.
- **The same result is requested by many users.** One computed answer serves many readers.
- **Latency budgets are tight and the query is expensive.** Precompute it.
- **Traffic is spiky.** A cache absorbs peaks that would otherwise reach the database.

### Do not use it when

- **The workload is write-heavy or balanced.** Precomputing read models for data written constantly and read rarely is wasted work.
- **You need strong consistency.** Payments, account balances, inventory at checkout, anything financial — do not cache. Read the primary. Period.
- **The system isn’t under pressure yet.** Caching adds an invalidation surface, a new failure mode, and ongoing maintenance cost. It needs to earn its place.

---

## 14. Common pitfalls (the ones I see in production reviews)

1. **Adding Redis with no invalidation story.** Every cached value needs a refresh or invalidation path. If you can’t write it down, don’t cache it.
2. **Ignoring the cold start.** If the database can’t survive an empty cache, a routine `FLUSHDB` is an outage.
3. **No stampede control.** One hot key expiring takes the database down with it.
4. **Forgetting replication lag.** This is the bug that breaks “user posts, user immediately sees post.”
5. **Denormalized read models with no owner.** They rot silently. Design the rebuild and backfill path *alongside* the incremental update, not later.
6. **No freshness budget per surface.** One consistency rule for the whole system is wrong. The home feed can be 30 seconds stale; the checkout price cannot.
7. **Caching the wrong things.** Account balances, inventory at checkout, financial ledgers. Just don’t.

---

## 15. The interview answer, structured

If a question like “Design Instagram” or “Design Twitter” shows up, this is the structure I would answer with.

```
1. Read-heavy? Yes. Estimate the read:write ratio (~10,000:1).
2. Skeleton:
       Client → CDN → Load Balancer → App tier → Redis → Replicas → Primary
3. Static assets at CDN.
4. Read path for feed:
       hybrid fan-out (push for normal, pull for celebrities)
       → MGET timelines from Redis
       → merge, rank, hydrate from profile cache
       → return top N
5. Write path:
       primary → event stream → fan-out workers → update per-follower timelines
6. Freshness budgets:
       home feed: 30s eventual
       own profile / own posts: read-your-writes (sticky primary for 5s)
       like counts: cache-aside 60s TTL
7. Failure modes I will defend against:
       cache stampede → TTL jitter + single-flight locks + stale-while-revalidate
       cold start → pre-warm + read-through
       hot keys → replica across shards + local LRU
       cache penetration → negative cache + bloom filter
       replication lag → read-your-own-writes (sticky + monotonic + version tokens + optimistic UI)
8. Tradeoffs I am making:
       storage vs. read latency (more copies = faster but possibly stale)
       fan-out on write cost vs. fan-out on read cost (hybrid)
       eventual consistency for most surfaces, strong only for the writer
```

A mid-level answer stops at step 5. A senior answer covers step 7. A staff+ answer ties it all to cost, freshness budgets, and the explicit decision *not* to cache some surfaces.

---

## 16. The summary diagram

```
                              ┌──────────────────────────────────────┐
                              │              CLIENT                 │
                              └────────────────┬─────────────────────┘
                                               │
                            static assets      │ API requests
                            ▼                  ▼
                  ┌────────────────────┐   ┌─────────────┐
                  │  ① CDN / EDGE      │   │  Load Bal.  │
                  │   - hashed URLs    │   └──────┬──────┘
                  │   - stale-if-error │          │
                  └────────────────────┘          ▼
                                        ┌────────────────────┐
                                        │   ② APP TIER       │  stateless,
                                        │   - business logic │  horizontally
                                        │   - local LRU      │  scaled
                                        └─────────┬──────────┘
                                                  │
                                                  ▼
                                        ┌────────────────────┐
                                        │  ③ APP CACHE       │
                                        │   - Redis          │
                                        │   - TTL + jitter   │
                                        │   - single-flight  │
                                        │   - versioned keys │
                                        └─────────┬──────────┘
                                                  │ miss
                                                  ▼
                                        ┌────────────────────┐
                                        │  ④ READ REPLICAS   │
                                        │   - async repl.    │
                                        │   - read-your-     │
                                        │     own-writes     │
                                        └─────────┬──────────┘
                                                  │ rare miss
                                                  ▼
                                        ┌────────────────────┐
                                        │  ⑤ PRIMARY DB      │  source of truth,
                                        │   - all writes     │  most protected
                                        └────────────────────┘

  Freshness budgets:   CDN days • Redis seconds-minutes • Replicas 10-500ms lag
                       • Primary: strong consistency
  Invalidation:        TTL + jitter • explicit DEL • event-driven • versioned keys
  Failure defenses:    stampede locks • stale-while-revalidate • negative cache •
                       bloom filter • cold-start pre-warm • hot-key replication
```

---

## 17. Closing thought

Read-heavy scaling is not one decision. It is **a stack of small decisions, each trading a little staleness for a lot of throughput**. The art is in declaring the staleness budget per surface, choosing the least expensive layer that meets it, and defending every layer against its specific failure mode.

The next time you open a design doc and someone has written “just add Redis,” you’ll know what the next twelve questions should be.

> *Add Redis for what? With what TTL? With what jitter? Invalidated how? What happens at cold start? What happens on stampede? What if the key is hot? What if it doesn’t exist? What’s the freshness budget? What if the user just wrote?*

If you can answer those, you are designing at the level this pattern deserves.

---

**If this helped, the three things I’d ask you to do:**

1. Drop a comment with the system you’re currently designing — I’d love to sanity-check the freshness budgets.
2. Share this with one engineer who is about to walk into a system design round.
3. Follow for more deep-dives on data-intensive systems.

— *Principal Engineer, ex-Stripe / Cloudflare, current staff IC at a fintech you’ve probably used today.*
