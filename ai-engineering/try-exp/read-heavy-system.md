Read-Heavy Systems
A viral post may be written once and read millions of times. How do systems like Instagram or Amazon serve that traffic without overwhelming the database? The answer is read-heavy scaling: compute an answer once, then serve copies instead of rebuilding it for every reader.

We can cache popular data, spread reads across replicas, and precompute expensive results. Each technique improves throughput by storing another copy of the data, which means accepting some amount of staleness. The design work is deciding where stale data is acceptable and how each copy gets refreshed.

static assets

API requests

Client

CDN / edge

Load balancer

App servers

Cache

Database

The read-heavy skeleton. The client fetches static assets from the CDN and API data through the load balancer, where a cache absorbs most reads before they reach the database.
Recognize this pattern
Use this pattern when reads greatly outnumber writes. Common examples include Design Instagram and Design Twitter.

The core idea
Reads and writes are rarely symmetric. An Instagram post is written once and read by thousands of followers. An Amazon product page changes a few times a day but is viewed millions of times. When the read:write ratio is 100:1 or 10,000:1, it makes sense to do more work at write time (or asynchronously) so every read does less work.

Every technique in this pattern follows that strategy. We can cache a result so repeated reads never touch the database, or replicate data so several machines serve reads in parallel. For feeds, rankings, and aggregations, we can precompute the answer so the request becomes a key-value lookup instead of a multi-table join.

This is a time and space tradeoff. Storing more copies makes reads cheaper, but those copies can diverge. Give each copy a freshness limit and a way to return to the source of truth.

The problem: computing answers at read time doesn't scale
Take "design the Instagram home feed" naively. When a user opens the app, you look up everyone they follow, fetch recent posts from each account, merge and rank the results, then hydrate each post with author info and like counts. That's several joins and aggregations, fanned across shards, on every single app open, for hundreds of millions of daily users. The database is overwhelmed long before real scale, and latency is bad even when it doesn't.

The same shape appears everywhere: a product page aggregating inventory, pricing, and reviews; a homepage ranking thousands of posts; a dashboard summing millions of events. The naive design recomputes the answer on every read. The pattern says: compute it once, store it, and serve the stored copy.

Five layers of read scaling
These techniques stack, and real systems usually use all of them, each catching what the layer above missed.

miss

miss

writes

async replication

Client

① CDN / edge

Load balancer

App servers

② App cache

③ Read replica

④ Primary DB

Layers
CDN and edge caching. Serves static and cacheable content physically near the user. The cheapest read you can serve, because it never reaches your infrastructure.
Application cache (Redis/Memcached). An in-memory store of hot objects, checked before any database call.
Read replicas. Serve reads that miss the cache, kept current by asynchronous replication from the primary. Multiplies read throughput, but replicas lag.
Primary database. Takes all writes and is the source of truth, protected by everything in front of it.
The three read paths a request can take, in increasing cost. Each layer catches what the one above it missed, and writes go to the primary.
1. CDN and edge caching
Serve static and semi-static content, such as images, video thumbnails, JavaScript bundles, and rendered pages, from edge servers near the user. The origin sees only cache misses. This is the cheapest read because the request never reaches the application infrastructure.

2. Application cache (Redis or Memcached)
How this gets asked
Stripe has asked candidates to design a distributed LRU cache. Expect the round to go straight past "add Redis" into eviction policy and how the cache stays correct as the underlying data changes.

An application cache is an in-memory store in front of the database. It holds frequently requested objects such as user profiles, session data, rendered feed pages, and product documents. Common access strategies include:

Cache-aside (check the cache, fall through to the DB on a miss, populate) is the default.
Read-through is the same behavior with the cache handling the DB fetch itself.
Write-through writes to cache and DB together, trading slower writes for a cache that's never stale.
Write-behind flushes to the DB asynchronously and can lose acknowledged writes if the cache dies; use it rarely and deliberately.
3. Load balancing
Everything above assumes requests are spread across a pool of app servers rather than piling onto one, which is what a load balancer does: distribute requests across the tier and stop routing to instances that fail their health check. It isn't specific to read-heavy systems, but it's what makes adding app servers a valid response to read growth, and it only works while the app tier stays stateless.

4. Read replicas
The primary database handles writes; changes replicate (usually asynchronously) to replica nodes that serve reads. This multiplies read throughput without touching the application's query patterns, but replication is asynchronous, so replicas lag behind. A user who just posted a comment and immediately reloads the page may not see it, unless you implement the read-your-own-writes strategy (see below).

5. Precomputed read models (denormalization)
Precomputed read models store data in the shape the reader needs, alongside its normalized, write-optimized form. This requires more storage and a reliable update path, but it can replace an expensive query with one lookup. Examples:

Materialized feeds. When a user posts, a fan-out worker pushes each new post into every follower's timeline list.
Denormalized product document. Store one assembled JSON blob instead of a six-table join.
Precomputed aggregates. Update counts, leaderboards, and trending lists incrementally on write, or compute totals on a scheduled interval.
Fan-out on write vs. fan-out on read
Fan-out on write (push): when someone posts, immediately write the post into every follower's precomputed timeline. Reads are extremely cheap; writes cost 
O
(
followers
)
O(followers).
Fan-out on read (pull): store nothing extra, and merge posts from followed accounts at read time. Writes are cheap; reads are expensive.
Push works well when read volume dwarfs write volume, as it does in many social products. It breaks on the celebrity problem: one post from an account with 100M followers creates 100M timeline writes. Use a hybrid instead. Fan out on write for normal accounts, pull posts from accounts above a follower threshold, and merge both sources when the user reads the feed.

Red flag
Fan-out on write for everyone, with no answer for the account with 100M followers.

Freshness and cache invalidation
A like count may tolerate being 30 seconds behind. A checkout price cannot. Assign each product surface a freshness budget, then choose the least expensive technique that meets it instead of applying one consistency rule to the whole system.

Once you have copies, you need an update story. The main options for cache invalidation, in increasing effort, are:

TTL expiry (every entry dies after N seconds; simple, bounds staleness, add jitter so a popular key class doesn't expire everywhere at once),
Explicit invalidation on write (precise, but miss one write path and you serve stale data indefinitely)
Event-driven invalidation (the write publishes an event and a consumer rebuilds affected read models; this is how denormalized documents usually stay current, and it pairs with event-driven and pub/sub)
Versioned keys (bump a version in the cache key so readers miss the fresh copy).
Note
Different data types may need different invalidation strategies.

Tradeoffs and considerations
Every layer in front of the database introduces another failure mode. Let's account for the common ones.

Cache stampede. A hot key expires and thousands of concurrent requests all recompute it at once. Mitigate with per-key locking so one request recomputes while others wait, stale-while-revalidate to serve the old value during the refresh, and TTL jitter so a whole key class doesn't expire together.
Cold start. A deploy, flush, or cache failure sends every request to the database at once. If the database cannot survive an empty cache, the cache is a required dependency rather than an optional optimization.
Hot keys. Traffic for one celebrity profile concentrates on a single cache node. Replicate the hot key across nodes, or put a small in-process cache in front of it.
Cache penetration. Repeated requests for keys that don't exist bypass the cache entirely and hit the database every time. Cache the "not found" result, or use a Bloom filter.
Replication lag. A user posts, reloads, and cannot see the new post because the replica has not caught up. The fixes are collectively called read-your-own-writes: pin the user's reads to the primary briefly after a write, keep them on one replica for a monotonic view, carry a version token that a replica must catch up to, or render the action optimistically on the client. The writer sees a consistent view while other users can remain eventually consistent.

Deep dive
Sizing math, eviction, and layered topology
When to use it, and when not to
Reach for these techniques when:

Reads exceed writes by 10x or more. Feeds, catalogs, content sites, and dashboards all sit here comfortably.
The same result is requested repeatedly by many users. One computed answer serves thousands of readers.
Latency targets are tight but the query is expensive. Precomputing moves the cost off the read path.
Traffic is spiky. A cache absorbs peaks that would otherwise reach the database.
Leave them alone when:

The workload is write-heavy or balanced. Precomputing read models for data written constantly and read rarely is wasted work.
You need strong consistency. Payments and account balances should not be served from a stale cache. That is transactional workflows territory.
The system isn't under pressure yet. Caching adds an invalidation surface and a new failure mode, so it needs to earn its place.
Common pitfalls
Adding Redis with no invalidation story. Every cached value needs a refresh or invalidation path.
Ignoring the cold start. If the database can't survive an empty cache, a routine flush becomes an outage.
No stampede control. One hot key expiring takes the database down with it.
Forgetting replication lag. This is what breaks "user posts, user immediately sees post."
Denormalized read models with no owner. They rot silently, so design the rebuild and backfill path alongside the incremental update.
Leveling signals
Mid-level	Identifies the workload as read-heavy and says so explicitly. Adds a CDN for static content and a cache-aside Redis layer with TTLs. Adds read replicas and knows writes still go to the primary.
Senior	Chooses fan-out on write vs. read deliberately and raises the celebrity problem and the hybrid without being asked. Has an invalidation strategy per data type, names replication lag, and designs read-your-own-writes. Protects the database with stampede control, request coalescing, stale-while-revalidate, and TTL jitter, and watches cache hit rate and replica lag.
Staff+	Justifies the consistency model and freshness budget per surface, including where caching must not be used like payments. Reasons about cost of fan-out writes vs. read-time compute, cache memory vs. DB capacity, precompute vs. lazily loading. Considers failure modes like cache flushing and cold starts.