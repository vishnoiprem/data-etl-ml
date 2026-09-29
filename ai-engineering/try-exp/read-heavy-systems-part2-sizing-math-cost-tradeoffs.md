# Designing Read-Heavy Systems, Part 2 — The Sizing Math and Cost Tradeoffs a Principal Engineer Actually Does on a Whiteboard

## Where Part 1 left off, and why "just add Redis" is the most expensive sentence in system design

> *Part 1* showed you the five layers — CDN, app tier, cache, replicas, primary — and the patterns that go in each one. The diagrams were clean. The architecture looked correct.
>
> *This article* is about what happens when the design doc meets procurement.
>
> If you have ever been asked "how much will this cost?" or "is this sized for the Super Bowl?" and answered with vibes, this is for you.

By the end of this article, you will be able to:

- Back-of-envelope the QPS, storage, and bandwidth for a read-heavy system from a one-line product description.
- Decide between *more cache memory* and *more replica count* using a concrete formula, not a feeling.
- Reason about fan-out-on-write cost at scale (including the Twitter cost-of-a-celebrity-tweet math).
- Build a freshness × cost matrix that a finance partner can sign off on.
- Defend sizing decisions in a design review *and* an executive Q&A.

Let’s get the calculator out.

---

## 1. The sizing ritual — what to write on the whiteboard first

Every sizing exercise I run starts with five numbers, in this order. If you cannot fill these in, you are not ready to talk about cache or replicas.

```
┌──────────────────────────────────────────────────────────────────────┐
│                    THE 5 NUMBERS                                       │
├──────────────────────────┬───────────────────────────────────────────┤
│ 1. DAU / MAU             │  Daily / monthly active users             │
│ 2. Actions per user / day│  Reads + writes, broken down              │
│ 3. Peak QPS              │  Avg × burst factor (3–10x is normal)    │
│ 4. Read:write ratio      │  Determines read-heavy vs balanced        │
│ 5. Object size           │  Avg payload size in bytes                │
└──────────────────────────┴───────────────────────────────────────────┘
```

For Instagram-style feed:

```
DAU                         500,000,000
App opens per user / day    8
Total reads / day           4,000,000,000
Posts created / day         100,000,000
Read : write ratio          ~40 : 1   (across the whole product)
                          (but per-post it's 1000s : 1, see §2)
Avg post object size        1.5 KB
Avg feed page size          50 KB    (20 posts + metadata)
```

Let’s derive the rest.

---

## 2. Two different ratios, two different architectures

This is where most engineers slip in interviews and in design docs.

```
Per-user ratio:    reads/day per user ÷ writes/day per user
                   8 opens × 20 posts = 160 reads/day
                   0.2 posts/day
                   ratio = 800 : 1   (this user is read-heavy)

Per-content ratio: views per piece of content ÷ lifetime
                   viral post = 10M views in 24h
                   1 write
                   ratio = 10,000,000 : 1   (this content is read-heavy)
```

The per-user ratio says "cache the user profile, cache the feed page."
The per-content ratio says "fan out the post into follower timelines, CDN the media, denormalize the engagement counters."

Both are true. You need both for a complete design.

---

## 3. The QPS math (with the burst factor, not without it)

Peak QPS is **not** average QPS. A useful rule of thumb:

```
Peak QPS ≈ Avg QPS × burst factor
          where burst factor ∈ [3, 10] for most consumer apps
                       ∈ [1.5, 3] for B2B / internal
                       ∈ [10, 50] for live events / sports / launches
```

For our Instagram example:

```
Avg reads/sec = 4,000,000,000 ÷ 86,400 ≈ 46,296 reads/sec
Peak reads/sec (burst=5x)            ≈ 230,000 reads/sec
Avg writes/sec = 100,000,000 ÷ 86,400 ≈ 1,157 writes/sec
Peak writes/sec (burst=3x)           ≈ 3,500 writes/sec
```

**This is where the read-heavy pattern earns its keep.** 230k reads/sec vs 3.5k writes/sec. The primary DB only has to handle the writes. Everything else is layered.

Now, what does each layer absorb?

```
Layer          Target hit rate   Reads absorbed   Cost per million reads
─────────────────────────────────────────────────────────────────────────
CDN / edge        60%              138,000 /s       $0.05  (origin shielded)
App cache (Redis) 30% of remaining  27,600 /s       $0.40  (Redis r6g.large × few)
Read replicas     99% of remaining   6,300 /s       $8.00  (db.r6g.4xlarge × few)
Primary DB        1% of remaining      63 /s       $50.00  (read-side, but rare)
─────────────────────────────────────────────────────────────────────────
Total absorbed:    230,000 reads/sec
Primary sees:        63 reads/sec  + 3,500 writes/sec
```

The primary sees **two orders of magnitude less traffic** than the user-facing path. That is the whole point of the pattern. Now let me price each layer honestly.

---

## 4. Sizing the cache (Redis memory math)

Cache sizing is the single most-undersized line item in most designs. People allocate "some Redis" and then ship. Three months later they are paging because of evictions.

### 4.1 Working set size

```
Working set = (number of hot objects) × (avg object size) × (overhead factor)

For Instagram:
  hot users (top 1%)         = 5,000,000
  avg user profile size      = 2 KB
  working set                = 5,000,000 × 2 KB = 10 GB
  + JSON overhead (~30%)     = 13 GB
  + Redis internal overhead  = 18 GB
  + fragmentation buffer     = 30%  →  26 GB
  → round up to 32 GB Redis
```

For the product detail page cache:

```
Working set:
  catalog SKUs               = 50,000,000
  % that is hot (top 10%)    = 5,000,000
  avg product doc            = 4 KB
  working set                = 20 GB raw → 32 GB with overhead
```

### 4.2 The 80/20 rule for cache sizing

In practice, **80% of requests hit 20% of keys**. That means:

- If your cache is too small to hold the 20%, eviction kills you.
- If your cache holds exactly the 20%, you have ~95% hit rate.
- If your cache holds 50% of all keys, you have ~99% hit rate.

The decision is between "size for 95% hit rate cheaply" vs "size for 99% hit rate expensively." A principal engineer chooses the former, then measures.

```
Cache size        Hit rate    Cost / mo (Redis)    Miss cost / mo
──────────────────────────────────────────────────────────────────
32 GB             ~95%        $400                 $5,000
128 GB            ~99%        $1,600               $500
512 GB            ~99.5%      $6,400               $50
──────────────────────────────────────────────────────────────────
Diminishing returns past 99%. The cheap option (95%) is usually right.
```

### 4.3 Eviction policy matters more than you think

```
Policy              Behavior                             Use case
──────────────────────────────────────────────────────────────────
allkeys-lru         Evict least recently used            General default
allkeys-lfu         Evict least frequently used          Better for skewed workloads
volatile-lru         Only evict keys with TTL set         When you have a mix
volatile-ttl         Evict shortest-TTL first             Avoid this, surprising behavior
noeviction           Return error on full                 When you must not lose data
```

I default to **allkeys-lfu** for read-heavy workloads since Redis 4.0+. LFU outperforms LRU on the long tail of "not-recent-but-very-popular" keys (e.g., breaking news, viral products).

---

## 5. Sizing read replicas (the "just add a replica" trap)

Every junior engineer thinks adding a replica halves the read load. It does not, and here is why.

### 5.1 The replica math

```
Primary DB capacity           = 10,000 reads/sec at p99 < 50ms
Replica capacity              = ~8,000 reads/sec at p99 < 50ms
                              (10–20% lower than primary due to replication lag,
                               single-threaded apply on most engines, lock contention)

Replicas to handle R reads    = ceil(R / 8,000)
```

But the real constraint is **replication lag**, not capacity:

```
If replicas lag, the application starts shedding load
or serving stale data, which manifests as user-visible bugs
long before the replica is "full."

Rule of thumb:
  - Keep replica CPU under 60% sustained
  - Keep replica IO under 70% sustained
  - Alert on replica lag > 1s p99
```

### 5.2 The replica placement problem

```
Single-region setup:
  Primary us-east-1
  Replicas us-east-1 × 3    ← same AZ for low lag, or cross-AZ for HA

Multi-region setup:
  Primary us-east-1
  Replicas us-west-2 × 2, eu-west-1 × 2
  Cross-region replication lag: 100–500ms typical
  Read-your-writes becomes critical at this scale
```

### 5.3 When replicas stop helping

A read replica is useless if the query itself is the bottleneck. Watch for:

- **Full table scans** — replicas will scan just as slowly.
- **Multi-shard joins** — replica doesn't help if the data isn't co-located.
- **Lock contention on the primary** — replica reads don't relieve write locks, because replica read consistency uses snapshots that may force I/O.

If the query is the problem, the answer is a precomputed read model (denormalized document), not another replica.

---

## 6. The fan-out cost (the math nobody does)

This is where I see the most expensive mistakes. Let me work the Twitter problem end-to-end.

### 6.1 Pure fan-out-on-write, naive

```
User with N followers posts one tweet.

Write amplification      = N writes (one per follower)
Disk write per follower  = ~200 bytes (tweet ID + author + ts + metadata)
Total disk write         = N × 200 bytes

For N = 100,000,000 followers:
  Total = 100M × 200 B = 20 GB written per tweet

At 100k writes/sec sustained write throughput:
  Time to fan out = 100M / 100k = 1,000 seconds ≈ 17 minutes

That's 17 minutes of write amplification for ONE tweet.
```

### 6.2 Real cost per tweet (with infra)

```
Component                     Cost
────────────────────────────────────────────────────
Redis memory for timelines    $0.50 / tweet (stored for ~7 days)
Kafka fan-out messages        $0.10 / tweet
Compute for fan-out workers   $0.30 / tweet
Replica replication traffic   $0.05 / tweet
────────────────────────────────────────────────────
Total fan-out cost / tweet    ~$1.00

For 100M followers, that's $1.00 of infra to deliver one tweet.

If the celebrity tweets 10x/day = $10/day.
At 100 celebrities = $1,000/day = $365k/year JUST for fan-out.
```

This is not hypothetical. This is why Twitter uses hybrid fan-out.

### 6.3 The hybrid math

```
Threshold T = follower count above which you pull instead of push

For T = 10,000:
  Number of users above T           ≈ 50,000 (long-tail celebrities)
  Avg followers of those users      ≈ 500,000
  Posts/day from those users        ≈ 200,000
  Pull cost / post (read at fetch)  ≈ $0.001
  Total pull cost / day             ≈ $200

For all users below T:
  Posts/day                         ≈ 99,800,000
  Avg followers                     ≈ 200
  Push cost / post                  ≈ $0.0002
  Total push cost / day             ≈ $20,000

Hybrid total / day                  ≈ $20,200
Pure push total / day               ≈ $100,000+ (and broken)

Savings: ~80% infra cost.
```

The threshold T is itself a tunable, and where you set it is a principal-engineer decision: too low and you pay pull costs on everyone, too high and the celebrity problem bites.

```
Hybrid fan-out economics
────────────────────────────────────────────────────
T = 1,000      → too low, mostly pull, read costs dominate
T = 100,000    → too high, push overflows on top celebrities
T = 10,000     → sweet spot for Twitter-scale
T = 50,000     → sweet spot for Instagram-scale
```

---

## 7. The freshness × cost matrix (the artifact for finance)

When I take a design to a VP-Eng or finance review, I bring this exact table. Every surface, one row, with the cost of being right vs being wrong.

```
┌──────────────────────┬────────────┬──────────────┬──────────┬──────────┐
│ Surface              │ Staleness  │ Layer        │ Infra    │ Cost of  │
│                      │ budget     │              │ $/month  │ staleness│
├──────────────────────┼────────────┼──────────────┼──────────┼──────────┤
│ Home feed            │ 30s        │ Redis + rep. │ $4,000   │ Low      │
│ User profile (own)   │ strong     │ Primary      │ $200     │ N/A      │
│ User profile (other) │ 5 min      │ Redis TTL    │ $600     │ Low      │
│ Like count           │ 60s        │ Redis counter│ $400     │ Low      │
│ Follower count       │ 15 min     │ Precomputed  │ $200     │ Low      │
│ Trending list        │ 5 min      │ Periodic job │ $300     │ Medium   │
│ Product detail       │ 60s        │ Redis doc    │ $1,500   │ Medium   │
│ Inventory (PDP)      │ 30s        │ Redis        │ $400     │ Medium   │
│ Inventory (checkout) │ strong     │ Primary      │ $200     │ N/A      │
│ Account balance      │ strong     │ Primary      │ $200     │ N/A      │
│ Search results       │ 5 min      │ ES replica   │ $3,000   │ Low      │
│ CDN static assets    │ 1 year     │ CDN          │ $800     │ None     │
└──────────────────────┴────────────┴──────────────┴──────────┴──────────┘

Total:                       $11,800 / month
vs. all-primary baseline:    $90,000 / month  (cost of NOT scaling reads)
Savings:                     ~87%
```

This is the single artifact that turns a design review from "are we sure?" into "yes, here is the math." I have never had finance push back on a design that included this table.

---

## 8. The cache-memory-vs-DB-capacity decision

The hardest sizing question is: **"We can either add 128 GB to Redis or upgrade the DB. Which is better?"**

### 8.1 The formula

```
Cost per request served
  from cache    = cache_cost / (QPS × hit_rate × 31,536,000)
  from DB       = db_cost    / (QPS × miss_rate × 31,536,000)

Add cache if:   cache_cost / hit_rate   <   db_cost / miss_rate
```

Worked example:

```
Current state:
  QPS             = 50,000
  Hit rate        = 80%
  Redis cost      = $2,000 / month
  DB cost         = $20,000 / month

Cost per cache hit:
  $2,000 / (50,000 × 0.8 × 2,592,000)  ≈ $0.0000000194 ≈ negligible

Cost per DB read:
  $20,000 / (50,000 × 0.2 × 2,592,000) ≈ $0.00000077   ≈ 40x more

Decision:  doubling Redis spend to bump hit rate 80% → 95%
  ΔRedis cost                = +$2,000 / month
  DB queries avoided         = 50,000 × 0.15 × 86,400 = 648M / day
  DB cost reduction (est 15%): -$3,000 / month
  Net savings                = $1,000 / month

Plus:
  p99 latency reduction:  80ms → 15ms (cache absorbs spikes)
  DB headroom for writes:  +15% capacity unlocked
```

The **non-obvious win** is the last line. Adding cache often unlocks DB headroom for *writes*, which are usually the binding constraint.

### 8.2 When NOT to add cache

```
Skip cache if:
  ✗  QPS < 1,000  (the DB can probably handle it)
  ✗  Hit rate would be < 50% (cache is paying for misses)
  ✗  Working set > 10x Redis budget (constant thrashing)
  ✗  Data is highly relational / multi-table by nature (cache the doc, not the query)
  ✗  Strong consistency is mandatory for the surface
```

### 8.3 The precompute-vs-lazy-load decision

For expensive queries (multi-table joins, aggregations):

```
                        Precomputed                Lazy
─────────────────────────────────────────────────────────────────
Read cost               O(1) lookup                O(complex query)
Write cost              O(delta recompute)         O(1) write
Storage                 N × precomputed view       Source tables only
Freshness               Eventual (depends on pipeline) Strong
Build complexity        High (pipeline, backfill)  Low
Failure blast radius    Pipeline stall = stale     Slow queries = sad users
─────────────────────────────────────────────────────────────────
Rule of thumb:
  if read:write > 100:1 AND query is expensive → precompute
  if read:write < 10:1 OR query is cheap        → lazy
  in between                                     → measure
```

---

## 9. Sizing for launch day (the 3 a.m. survival check)

Before any product launch, I run a "3 a.m. test": *can the system survive a 10x traffic spike with a cold cache?*

```
Launch day projection:
  Expected peak QPS         = 50,000
  Spike multiplier          = 10x
  Effective peak QPS        = 500,000

Pre-warm plan:
  At T-1h, load top-N keys:
    - Top 1% users by activity       → profile cache
    - Top 100 products               → product doc cache
    - Top 1000 trending items        → feed cache
    - All static asset URLs          → CDN pre-populate

CDN configuration:
  Cache-Control: public, max-age=300, stale-while-revalidate=86400
  Origin shield: enabled
  Geo-routing: enabled (closest region serves)

Redis configuration:
  Provisioned at 2x expected steady-state
  Eviction policy: allkeys-lfu
  Cluster mode: yes (sharded by user_id)
  Replication: 1 primary + 1 replica per shard

Database configuration:
  Read replicas: scaled to handle 50% of cache miss rate × spike QPS
  Connection pool: sized for spike, not steady state
  Slow query log: alert on > 100ms p99
```

If you can't write this down for your launch, you don't have a launch plan. You have a launch hope.

---

## 10. The cost-vs-freshness tradeoff curve

The decision is not binary. Different combinations of cache, replica, and precompute give you different points on the curve:

```
                                          Cost ($/month)
                                          │
   $100k ─────────────────────────────────●  All-primary, no caching
                                          │  • 100% fresh
                                          │  • slowest p99
                                          │
                                          │
    $50k ─────────────────────────●───────●  Cache + 2 replicas
                                          │  • 95% fresh
                                          │  • good p99
                              ●───────────●  Cache + replicas + precomputed feed
    $20k ──────────────────────●           │  • 90% fresh
                                          │  • fast p99
                              ●─────────────●  Aggressive precompute + CDN + cache
    $12k ──────────────────────●           │  • 80–95% fresh (depends on surface)
                                          │  • fast p99
                                          │  • complex pipeline
                                          │
     $5k ──────────────────────────●───────●  Minimal infra, manual ops
                                          │  • 100% fresh
                                          │  • doesn't scale
                                          │
                                          └────────────────────────────────
                                            Slow   ←————— p99 latency ———→   Fast

                                            High   ←————— freshness ———→    Low
```

The right point on this curve depends on:

- **Product SLA** (what p99 do users tolerate?)
- **Freshness requirements** per surface (which surfaces need strong consistency?)
- **Cost ceiling** (what does finance approve?)
- **Engineering capacity** (how much pipeline complexity can the team own?)

A staff engineer picks the **lowest point on the curve that meets the SLA**. A principal engineer picks the same point *and* documents why the other points are wrong.

---

## 11. The sizing exercise, end-to-end (worked example)

Let me size a "design Pinterest" from scratch, in one pass, on the whiteboard.

### Product description
- 200M MAU, 30M DAU
- Avg user pins 3 boards/day, views 50 pins/day
- 5B pins total, 2B boards, 500M users
- Goal: p99 < 200ms globally, daily snapshots for analytics

### The 5 numbers

```
DAU                         30,000,000
Reads / day                 1,500,000,000   (30M × 50)
Writes / day                90,000,000      (30M × 3)
Read : write ratio          ~17 : 1
Avg read payload            30 KB (pin + metadata + thumbnail URL)
Peak QPS (burst 5x)         ~87,000 reads/s, ~5,200 writes/s
```

### Architecture choices

```
CDN:            CloudFront, hashed URLs for all images
                Hit rate target: 70% on images
                Cost: ~$3k/month

App cache:      Redis, cluster mode, sharded by user_id
                Working set: top 5M users × 5 KB = 25 GB → 64 GB nodes
                TTL: 5 min for pins, 30 min for boards
                Cost: ~$1.5k/month

Read replicas:  3 replicas, cross-AZ
                Handle cache miss path (~26k reads/s sustained)
                Cost: ~$8k/month

Primary DB:     Postgres, write-optimized, single instance + failover
                5,200 writes/s sustained, well within capacity
                Cost: ~$4k/month

Precomputed:    Daily trending board via Spark job → Redis
                Cost: ~$500/month compute + $200 Redis

Total infra:    ~$17k/month
Per-DAU cost:   $0.00057 / DAU / month
```

vs. all-primary baseline (no caching, 12 large DB instances): **~$90k/month**.

That is **81% savings**, achieved entirely by the read-heavy pattern.

---

## 12. The sizing checklist (the artifact for design review)

Before any design review, I require this checklist filled out. If it's not filled out, the review is rescheduled.

```
┌─────────────────────────────────────────────────────────────────────┐
│                  READ-HEAVY SYSTEM SIZING CHECKLIST                  │
├─────────────────────────────────────────────────────────────────────┤
│ QPS                                                                  │
│ ☐ Avg QPS                = _____                                     │
│ ☐ Peak QPS (with burst)  = _____                                     │
│ ☐ Read QPS               = _____                                     │
│ ☐ Write QPS              = _____                                     │
│ ☐ Read:write ratio       = _____                                     │
│                                                                       │
│ STORAGE                                                               │
│ ☐ Working set size       = _____ GB                                  │
│ ☐ Cache allocation       = _____ GB (target hit rate: ____%)         │
│ ☐ Total DB size          = _____ TB                                  │
│ ☐ Precomputed model size = _____ GB                                  │
│                                                                       │
│ LAYER TARGETS                                                         │
│ ☐ CDN hit rate           = _____%                                     │
│ ☐ Cache hit rate         = _____%                                     │
│ ☐ Replica count          = _____                                      │
│ ☐ DB primary count       = _____                                      │
│                                                                       │
│ FRESHNESS                                                             │
│ ☐ Per-surface budget documented: yes / no                            │
│ ☐ Per-surface layer assigned:    yes / no                            │
│ ☐ Per-surface invalidation plan:  yes / no                            │
│                                                                       │
│ FAILURE MODES                                                         │
│ ☐ Cold-start plan:      _____                                        │
│ ☐ Stampede control:     _____                                        │
│ ☐ Hot-key strategy:     _____                                        │
│ ☐ Read-your-writes:     _____                                        │
│ ☐ Negative caching:     _____                                        │
│                                                                       │
│ COST                                                                  │
│ ☐ Per-layer infra $/month:    $_____                                 │
│ ☐ Per-DAU cost:               $_____                                 │
│ ☐ Compared to all-primary:    saved ____%                            │
│ ☐ Compared to launch-day:     sized for ____x                        │
│                                                                       │
│ SIGN-OFF                                                              │
│ ☐ Eng lead:    _____    ☐ SRE: _____    ☐ Finance: _____            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 13. The five questions a principal engineer asks before sizing anything

1. **What is the freshness budget for each surface?** (Not "what's the cache TTL" — what does the *product* tolerate?)
2. **What does the working set look like at peak?** (Not the average — the peak. 95th percentile.)
3. **Where is the binding constraint?** (Usually writes, sometimes bandwidth, rarely reads if you've layered correctly.)
4. **What is the cost of being wrong?** (Cache stampede takes down DB for 5 minutes = $X revenue loss.)
5. **Who owns the rebuild path?** (Denormalized models rot silently. If no one owns the rebuild, don't build the model.)

---

## 14. Closing thought

Part 1 was about the architecture.
Part 2 was about the cost.

A principal engineer is paid to make both decisions *together*, in the same design doc, with the same math, defended to both the engineering team and the finance partner. The engineer who designs the perfect five-layer system that costs $200k/month when the budget is $15k has failed just as surely as the one who proposes "just add Redis" for a $200M-launch product.

> **The right answer is always the cheapest point on the cost-freshness curve that meets the SLA, defended with the math.**

That is the difference between a senior engineer and a principal one. The architecture is the same. The math is the differentiator.

---

**If this helped:**

1. Repost Part 1 + Part 2 together (they're a set)
2. Drop a comment with the system you're sizing — I'll do the math with you
3. Follow for Part 3: *The launch-day playbook — what to break, what to keep, and the on-call rotation that survives the spike*

— *Principal Engineer. The diagrams are free. The math is what they pay me for.*
