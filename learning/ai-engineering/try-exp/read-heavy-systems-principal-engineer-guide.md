# Designing Read-Heavy Systems Like a Principal Engineer

## Why one Instagram post can quietly melt a database — and what every layer in front of it actually does

> A viral post is written once and read millions of times. If your system treats both numbers the same, you will spend your weekends on call. If it treats them differently, you get to sleep.

I want to walk you through the read-heavy pattern the way I would explain it to a senior engineer joining my team. Not the textbook version. The version that survives a launch, a Super Bowl ad, and a cold cache at 3 a.m.

By the end, you will be able to:

- Explain why read-heavy systems need a different shape than write-heavy ones.
- Sketch the five layers from CDN to primary DB on a whiteboard.
- Choose between caching strategies on purpose.
- Handle the celebrity problem, the stampede, the cold start, and replication lag.
- Defend your design in a system design interview and in a real production review.

Let's start with the uncomfortable truth.

---

## 1. The asymmetry that breaks naive designs

Picture Instagram. A celebrity with 300 million followers taps post. One write.

A few seconds later, 300 million people tap refresh. 300 million reads. Same single post.

The read-to-write ratio is 300,000,000 to 1 for that one piece of content. Across the whole product, it's somewhere between 100:1 and 10,000:1.

```
Read vs Write ratios in real systems

  Instagram feed       reads >> writes       ~10,000 : 1
  Amazon product page  reads >> writes       ~1,000  : 1
  Twitter timeline     reads >> writes       ~500    : 1
  Uber ride history    writes >> reads      ~1      : 100  (write-heavy!)
  Bank ledger          balanced + strict    ~1      : 1
```

The one principle I write on every new design doc:

> Do more work at write time so that every read does less work.

Every technique in this article is a variation of that sentence. Caching, replication, denormalization, materialized views, precomputed feeds — they're all just ways of saying "we already paid for this answer once, let's not pay again."

There are two honest trades:

- Time vs space. Storing more copies costs memory and disk.
- Freshness vs speed. More copies means more chances they disagree.

The job of a principal engineer is not to maximize speed or to maximize freshness. It is to pick the cheapest technique that meets the freshness budget of each surface.

---

## 2. The naive design (and why it dies)

Design the Instagram home feed the way a junior engineer would:

```
Open app
  -> look up who I follow
  -> fetch last 50 posts per account
  -> merge, rank, hydrate author info and like counts
  -> return first 20
```

Looks innocent. Count the work for a user who follows 500 accounts:

```
Per app open:
  1   SELECT id FROM follows WHERE follower = me
  500 SELECT * FROM posts WHERE author_id = ? ORDER BY ts
  500 JOIN users ON author_id
  1   aggregation, ranking, sorting

Total: ~1,000 queries, ~50,000 rows shuffled
...all on one user action.
```

Multiply by 500 million daily active users and the database is not slow. It is structurally incapable of doing this work.

The naive design has one disease: it recomputes the answer on every read. The read-heavy pattern is the cure: compute it once, store it, serve the stored copy.

---

## 3. The five layers

Here is the full shape. Each layer is a place we can put a copy of the data, and therefore a place we have to think about freshness.

```
  Client (mobile / browser / device)
    |
    |--- static assets ---> CDN / Edge (1)
    |
    |--- API requests ---> Load Balancer
                              |
                              v
                         App servers (2)  <- stateless
                              |
                              v
                         Cache / Redis (3)
                              |
                              v
                         Read replicas (4)
                              |
                              v
                         Primary database (5)  <- all writes
```

The mental model: each layer catches what the layer above it missed. The request that survives all five is rare, and it had better be cheap.

Let me walk down the stack.

---

## 4. Layer 1 — CDN and edge caching

The cheapest read you can serve is one that never reaches your infrastructure. That's the CDN.

What lives at the edge:

- Static assets — images, video, JS bundles, fonts. Set far-future cache headers and version the URL.
- Semi-static content — rendered HTML for anonymous homepages, public profiles, product pages.
- Some API GETs — but carefully, with care for staleness.

The most important rule:

> Separate the URL from the content. If the content changes, change the URL. Never expect the CDN to "know" the content changed.

```
  https://cdn.example.com/avatar/<user_id>.jpg?v=<content_hash>
```

When the user updates their avatar, the hash changes, the URL changes, the CDN treats it as a brand-new object. No invalidation round trip. No stale avatar for six hours.

Failure mode to remember: if your origin is down and the CDN has no stale-if-error directive, every cache miss becomes a 5xx. Set stale-if-error on anything user-visible.

---

## 5. Layer 2 — Application cache (Redis / Memcached)

Once a request reaches your app, the next cheap read is an in-memory key-value store. This is where most of your read amplification should be absorbed.

What you put here:

- User profiles and sessions
- Rendered feed pages for hot users
- Product documents
- Rate-limit counters
- Locks for stampede control

### The four cache strategies

There are four ways to use a cache. Pick deliberately.

```
Cache-aside    The app checks the cache. On miss, it reads the DB and populates.
               On writes, it invalidates or sets the key.
               This is the default. Most apps start here.

Read-through   Same behavior, but the cache library calls the DB on miss.
               Use when the cache library owns the lifecycle.

Write-through  Every write goes to the cache and the DB together.
               Slow writes, but the cache is never stale.

Write-behind   The app writes only the cache. The cache flushes to the DB async.
               Faster writes, but you can lose acknowledged writes if the cache dies.
               Use rarely and on purpose.
```

I have seen more outages from write-behind than from any other pattern. The cache process dies, the DB never gets the write, and the user is angry in a way that paging cannot fix.

### A real cache-aside implementation

```python
async def get_user_profile(user_id):
    key = f"user:{user_id}"

    cached = await redis.get(key)
    if cached:
        return json.loads(cached)

    profile = await db.fetchrow(
        "SELECT id, name, bio, avatar_url FROM users WHERE id = $1",
        user_id,
    )
    if not profile:
        # Cache the "not found" so we don't keep hammering the DB
        await redis.set(f"{key}:nf", "1", ex=60)
        return None

    # TTL with jitter so a whole key class doesn't expire at the same instant
    ttl = 300 + random.randint(0, 60)
    await redis.set(key, json.dumps(dict(profile)), ex=ttl)
    return dict(profile)
```

Two things worth noticing.

First, TTL with jitter. If every user profile expires at second 300, you have a stampede waiting to happen. The random offset spreads expirations across a minute.

Second, negative caching for misses. Without it, an attacker pounding GET /users/<random-uuid> walks straight through the cache and DDoSes your database.

### Treat cache keys as a schema

Cache keys are a first-class schema, not an afterthought. Document them:

```
  user:{user_id}                  -> UserProfile      TTL 300s + jitter
  user:{user_id}:followers:count  -> int              TTL 60s
  post:{post_id}                  -> Post             TTL 600s
  feed:{user_id}:home:v{version}  -> List[PostId]     TTL 120s
  product:{sku}                   -> ProductDocument  TTL 300s
```

The v{version} part is deliberate. When a user updates their profile, you don't need to find and delete every cached page that referenced them. You bump the version. Old keys become unreachable. More on this in the invalidation section.

---

## 6. Layer 3 — Load balancing (the silent prerequisite)

None of the layers above work if the app tier is stateful. A load balancer spreads requests across N app servers, but only if any app server can serve any request. If session state lives in a particular server's memory, you can't scale freely.

The pattern:

```
                Client
                  |
                  v
            Load balancer
                  |
        +---------+---------+---------+---------+
        |         |         |         |         |
        v         v         v         v         v
     App-01    App-02    App-03    App-04    App-05
        |         |         |         |         |
        +---------+---------+---------+---------+
                  |
                  v
              Redis + DB
```

Stateless app tier plus sticky state in Redis or the DB. That is what lets you answer "we have 5x traffic tomorrow" with "spin up 4x more app servers."

---

## 7. Layer 4 — Read replicas (and replication lag)

The primary database handles all writes. Those writes are asynchronously streamed to one or more replicas, which serve reads. This multiplies read throughput linearly with the number of replicas, without changing your queries at all.

```
                  writes
  Client ---------> Primary DB
                       |
                       |  async replication
                       |  (WAL shipping / change streams)
                       v
              +--------+--------+--------+
              v                 v        v
          Replica-1         Replica-2  Replica-3
              |                 |        |
              +--------+--------+--------+
                       |
                       v
                  reads served
```

The catch is the word asynchronous. Replicas lag. Usually 10–500ms, sometimes seconds under load. This is the source of the most common bug in read-heavy systems.

### The classic bug

```
  1. User posts a comment  -> POST /posts/123 -> primary
  2. User reloads feed     -> GET /feed       -> routed to replica
  3. Replica hasn't seen the write yet
  4. User: "My comment disappeared!"
```

### The fix: read-your-own-writes

There are four techniques. The right answer is usually "all of them, applied surgically."

- Sticky session on the primary. After a write, pin that user's reads to the primary for a short window (5 seconds is fine).
- Monotonic reads. Route a single user to the same replica for the duration of a session, so the view never goes backward in time.
- Version tokens. The write returns a version. The client passes it on subsequent reads. The read path waits until the replica has caught up.
- Optimistic UI. Render the comment client-side immediately, marked as pending. Reconcile when the server confirms.

```
  User A writes -> primary
  User A reads  -> primary (pinned for 5s after write)
  User B reads  -> any replica (eventual is fine)
```

The trade is explicit. The writer pays a consistency cost so the rest of the world can stay eventually consistent.

---

## 8. Layer 5 — Precomputed read models (denormalization)

Caching stores the result of a single query. Precomputed read models store the answer to a question we know we'll be asked a thousand times, in exactly the shape we'll ask it.

Two big flavors.

### Materialized feeds (the Instagram story)

When a user posts, a fan-out worker pushes the post into every follower's precomputed timeline.

```
  Write path:
  User A posts -> Primary DB
                      |
                      v
                 Fan-out worker (Kafka consumer)
                      |
        +-------------+-------------+-------------+
        v             v             v             v
   follower-1's   follower-2's   follower-3's   follower-4's
   timeline       timeline       timeline       timeline
   (Redis)        (Redis)        (Redis)        (Redis)

  Read path:
  User opens app -> GET /feed
                 -> MGET all followees' timelines
                 -> merge, rank, hydrate
                 -> return top N
```

Reads become a single MGET. A multi-thousand-row join collapses into one round trip to Redis.

### Denormalized product document

Instead of joining five tables every time:

```sql
SELECT p.*, i.qty, pr.amount, r.avg_rating
FROM products p
JOIN inventory  i  ON i.sku  = p.sku
JOIN pricing    pr ON pr.sku = p.sku
JOIN reviews    r  ON r.sku  = p.sku
WHERE p.sku = ?
```

store one document:

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

Reads become a single GET product:ABC-123. Writes are event-driven. A price change emits product.price.changed. A consumer rebuilds and rewrites the document.

---

## 9. Fan-out on write vs fan-out on read (the celebrity problem)

The most common interview trap in this domain, and a real production failure mode.

### Fan-out on write (push)

When someone posts, immediately write the post into every follower's precomputed timeline.

```
  User posts -> for each follower: write post into their timeline
```

Reads are dirt cheap. Writes cost O(followers).

### Fan-out on read (pull)

Store nothing extra. Merge posts from followed accounts at read time.

```
  User reads -> fetch posts from everyone they follow, merge, rank
```

Writes are cheap. Reads are expensive. We're back to the naive design.

### The celebrity problem

A user with 100 million followers posts. Fan-out on write creates 100 million timeline writes. Even at 100k writes per second, that's 17 minutes of write amplification per celebrity tweet. Your Kafka is on fire, your replicas are lagging, and Taylor Swift broke your architecture.

The fix is hybrid fan-out, which is what Twitter actually does.

```
  Write path:
  For normal users (< some threshold, say 10k followers):
      fan out on write -> push into every follower's timeline
  For celebrities (> threshold):
      do NOT fan out
      just write to the primary

  Read path:
  For every user:
      1. Read precomputed timeline (covers normal follows)
      2. For each celebrity the user follows, pull recent posts
      3. Merge and rank by recency + engagement
```

If you say only "fan out on write" with no mention of the celebrity problem, you are signaling mid-level, not senior. The hybrid is the right answer.

---

## 10. Cache invalidation

Every copy of the data has a freshness budget. We must declare it.

```
  Surface                     Acceptable staleness     Technique
  ------------------------------------------------------------------------
  Public profile page         minutes                  CDN + TTL
  User's own profile          seconds                  CDN bypass + short Redis TTL
  Like count                  10 to 60 seconds         Cache-aside with TTL
  Follower count              5 to 15 minutes          Cache-aside or precomputed
  Inventory at PDP            30 to 60 seconds         Cache-aside with TTL
  Inventory at checkout       strong consistency       NO CACHE. Read primary.
  Account balance             strong consistency       NO CACHE. Read primary.
  Trending leaderboard        1 to 5 minutes           Periodic precompute
```

The last two rows matter more than the first six. Not everything belongs in a cache. If you cache a bank balance and serve a withdrawal against a stale number, you have invented money. If you cache inventory at checkout and oversell by 30%, you have a customer service nightmare.

### Four invalidation strategies

```
  TTL expiry             Every entry dies after N seconds.
                         Simple, bounds staleness. Add jitter.
                         This is the default.

  Explicit invalidation  On write, DEL the key.
                         Precise. Miss one write path and you serve
                         stale data forever.

  Event-driven           The write publishes an event. A consumer rebuilds
                         affected read models. This is how denormalized
                         documents usually stay current.

  Versioned keys         Bump a version in the cache key. Old keys become
                         unreachable and expire naturally.
                         No DEL to forget.
```

### A worked example

User 42 changes their display name from "alice" to "Alice".

```
  Without versioning:
    1. UPDATE users SET name = 'Alice' WHERE id = 42
    2. DEL user:42
    3. DEL feed:42:home
    4. DEL feed:42:home:page:1
    5. DEL every comment cache referencing user 42   <- impossible
    6. ???

  With versioning:
    1. UPDATE users SET name = 'Alice' WHERE id = 42
    2. INCR user:42:version  -> v17
    3. Done. Every old key was feed:42:v16, which now misses.
       Old keys expire on their own TTL.
```

Versioned keys are the single biggest defensive technique I know in this space.

---

## 11. The failure modes that ruin weekends

Every layer in front of the database is a new way to fail. Here are the four that take down real systems.

### Cache stampede (the thundering herd)

A hot key expires. 50,000 concurrent requests all miss at the same instant. All 50,000 fan out to the database. The database melts.

```
  t=0     key hot:post:12345 expires
  t=0+ε   50,000 requests arrive simultaneously
  t=ε     50,000 concurrent SELECTs hit the database
  t=ε+τ   DB CPU 100%, p99 latency through the roof
```

Three mitigations, in order of importance.

First, TTL jitter. Never let a whole class of keys expire at the same instant.

Second, per-key locking. One request wins the lock and recomputes. The others wait.

Third, stale-while-revalidate. Serve the old value while one request refreshes in the background.

```python
async def get_post(post_id):
    key = f"post:{post_id}"
    val, ts = await redis.hmget(key, "value", "ts")

    if val and (now - ts) < STALE_TTL:
        return val                       # fresh

    if val:                             # stale but usable
        asyncio.create_task(refresh(post_id))
        return val                       # serve stale, refresh async

    # truly missing — single-flight
    async with redis.lock(f"{key}:lock", timeout=5):
        return await recompute(post_id)
```

### Cold start

A deploy, a FLUSHDB, or a cache node failure sends every request to the database at once. If the database can't survive an empty cache, the cache is not an optimization. It is a required dependency.

The rule I write on every design doc:

> Before you add caching, prove your database can survive an empty cache. Then add caching.

If it can't, your options are:

- Pre-warm the cache on deploy. Load the top-N keys from the DB before traffic arrives.
- Add a read-through fallback so the cache can rebuild itself.
- Scale the database first, then add caching.

### Hot keys

A celebrity profile or a viral product concentrates traffic on one cache node. Redis is single-threaded per shard. One hot key can saturate one shard while the others are idle.

Mitigations:

- Replicate the hot key across shards. Read from a random replica.
- Add an in-process LRU in front of Redis for the top 1% of keys.
- A local cache in each app server for the most extreme hot keys.

### Cache penetration

Attackers pound GET /users/<random-uuid>. Every request misses the cache, hits the database, returns nothing. Your database is doing useless work at scale.

The fix is to cache the "not found" result.

```python
async def get_user(user_id):
    key = f"user:{user_id}"

    cached = await redis.get(key)
    if cached is not None:
        return None if cached == "__missing__" else json.loads(cached)

    if await redis.get(f"{key}:nf"):
        return None                       # negative cache hit

    row = await db.fetchrow(...)
    if not row:
        await redis.set(f"{key}:nf", "1", ex=60)
        await redis.set(key, "__missing__", ex=60)
        return None
```

For very large keyspaces, add a Bloom filter in front of the cache. If the Bloom filter says "definitely not in the set," don't bother hitting the cache.

### Replication lag (again, briefly)

User posts, reloads, can't see the post because the replica hasn't caught up. The full toolkit is in section 7. The summary: stick the writer to the primary briefly, use version tokens, render optimistically on the client.

---

## 12. When to use this pattern (and when not to)

Reach for these techniques when:

- Read:write ratio is 10x or more. Feeds, catalogs, content sites, dashboards.
- The same result is requested by many users. One computed answer serves many readers.
- Latency budgets are tight and the query is expensive. Precompute it.
- Traffic is spiky. A cache absorbs peaks that would otherwise reach the database.

Leave them alone when:

- The workload is write-heavy or balanced. Precomputing read models for data written constantly and read rarely is wasted work.
- You need strong consistency. Payments, account balances, inventory at checkout. Do not cache them. Read the primary. Period.
- The system isn't under pressure yet. Caching adds an invalidation surface and a new failure mode. It needs to earn its place.

---

## 13. Common pitfalls (the ones I see in production reviews)

1. Adding Redis with no invalidation story. Every cached value needs a refresh or invalidation path. If you can't write it down, don't cache it.
2. Ignoring the cold start. If the database can't survive an empty cache, a routine FLUSHDB is an outage.
3. No stampede control. One hot key expiring takes the database down with it.
4. Forgetting replication lag. This is the bug that breaks "user posts, user immediately sees post."
5. Denormalized read models with no owner. They rot silently. Design the rebuild and backfill path alongside the incremental update, not later.
6. No freshness budget per surface. One consistency rule for the whole system is wrong. The home feed can be 30 seconds stale. The checkout price cannot.
7. Caching the wrong things. Account balances, inventory at checkout, financial ledgers. Just don't.

---

## 14. The interview answer, structured

If a question like "Design Instagram" or "Design Twitter" shows up, here is the structure.

```
1. Read-heavy. Estimate the read:write ratio (~10,000:1).
2. Skeleton:
       Client -> CDN -> Load Balancer -> App tier
              -> Redis -> Replicas -> Primary
3. Static assets at CDN.
4. Read path for feed:
       hybrid fan-out (push for normal, pull for celebrities)
       -> MGET timelines from Redis
       -> merge, rank, hydrate from profile cache
       -> return top N
5. Write path:
       primary -> event stream -> fan-out workers -> timelines
6. Freshness budgets:
       home feed: 30s eventual
       own profile / own posts: read-your-writes (sticky primary for 5s)
       like counts: cache-aside 60s TTL
7. Failure modes I will defend against:
       cache stampede -> TTL jitter + single-flight locks + stale-while-revalidate
       cold start -> pre-warm + read-through
       hot keys -> replicate across shards + local LRU
       cache penetration -> negative cache + bloom filter
       replication lag -> read-your-own-writes
8. Tradeoffs I am making:
       storage vs read latency
       fan-out on write cost vs fan-out on read cost (hybrid)
       eventual consistency for most surfaces, strong only for the writer
```

A mid-level answer stops at step 5. A senior answer covers step 7. A staff+ answer ties it all to cost, freshness budgets, and the explicit decision not to cache some surfaces.

---

## 15. Closing thought

Read-heavy scaling is not one decision. It is a stack of small decisions, each trading a little staleness for a lot of throughput. The art is in declaring the staleness budget per surface, choosing the least expensive layer that meets it, and defending every layer against its specific failure mode.

The next time someone writes "just add Redis" in a design doc, you know the next twelve questions.

```
  Add Redis for what?
  With what TTL?
  With what jitter?
  Invalidated how?
  What's the freshness budget?
  What happens at cold start?
  What happens on stampede?
  What if the key is hot?
  What if it doesn't exist?
  What if the user just wrote?
  What does this cost vs DB capacity?
  Who owns the rebuild path?
```

If you can answer those, you are designing at the level this pattern deserves.

---

If this helped, three things:

1. Drop a comment with the system you are currently designing. I would love to sanity-check the freshness budgets.
2. Share this with one engineer about to walk into a system design round.
3. Follow for more deep-dives on data-intensive systems.

Part 2 — the sizing math and cost tradeoffs — is live too. Link in comments.

— Principal Engineer. The diagrams are free. The math is what they pay me for.
