# LinkedIn Carousel — Read-Heavy Systems

> Format guide: each slide is one image (1080x1350 px, 4:5 portrait).
> Suggested tool: Canva, Figma, or LinkedIn's native carousel creator.
> Style: dark background (#0A0A0A), white text, one accent color (#00D4FF cyan), large sans-serif (Inter / Helvetica).
> 14 slides total. One core idea per slide.

---

## SLIDE 1 — Hook

**Title:**
Read-Heavy Systems

**Subtitle:**
The pattern behind every app you've ever scrolled.

**Bottom-right (small):**
A 3-minute crash course from a principal engineer.

---

## SLIDE 2 — The asymmetry

**Title:**
The asymmetry that breaks naive designs

**Body:**
One viral post. One write.

Three hundred million reads.

**Bottom line:**
Read:write ratio is 100:1 to 10,000:1 in most products. If your system treats both the same, you will spend your weekends on call.

---

## SLIDE 3 — The one principle

**Title:**
The one principle

**Big quote, centered:**
Do more work at write time so every read does less work.

**Bottom line:**
Every caching, replication, and denormalization trick is a variation of this sentence.

---

## SLIDE 4 — Naive design dies

**Title:**
The naive design (and why it dies)

**Left column:**
Instagram feed, naive:
1. Find who you follow
2. Fetch last 50 posts per account
3. Merge, rank, hydrate
4. Return top 20

**Right column, big number:**
~1,000 queries
~50,000 rows shuffled

**Bottom line:**
Per single app open. Scale to 500M daily users and the database is structurally incapable.

---

## SLIDE 5 — The 5 layers

**Title:**
The 5 layers of read scaling

**Stacked list:**
```
1. CDN / Edge            cheapest read
2. App tier              stateless
3. Cache (Redis)         hot objects
4. Read replicas         multiplies QPS
5. Primary DB            source of truth
```

**Bottom line:**
Each layer catches what the one above missed.

---

## SLIDE 6 — Cache strategies

**Title:**
The 4 cache strategies (pick deliberately)

**List:**

- Cache-aside. The default. Most apps start here.
- Read-through. Cache library owns the lifecycle.
- Write-through. Stale reads are unacceptable.
- Write-behind. Rarely. You can lose acknowledged writes.

**Bottom line:**
Write-behind has caused more outages in my career than every other pattern combined.

---

## SLIDE 7 — The celebrity problem

**Title:**
The celebrity problem
Why Twitter isn't pure fan-out-on-write

**Body:**
A user with 100M followers posts.
Pure fan-out-on-write = 100M timeline writes.
That's 17 minutes at 100k writes/sec.

**Big quote:**
Hybrid: push for normal users, pull for celebrities.

---

## SLIDE 8 — Invalidation

**Title:**
Cache invalidation. 4 strategies.

**Numbered list:**

1. TTL + jitter. Simplest. Bounds staleness.
2. Explicit DEL. Precise, but miss one path = stale forever.
3. Event-driven. Write publishes event, consumer rebuilds.
4. Versioned keys. Bump version, old keys expire naturally.

**Bottom line:**
Versioned keys are the single biggest defensive technique I know.

---

## SLIDE 9 — Failure modes

**Title:**
4 failure modes that ruin weekends

**Grid:**

| Cache stampede | Cold start |
|---|---|
| Hot key expires, 50k concurrent recomputes | Empty cache floods DB |
| Fix: single-flight lock + jitter | Fix: pre-warm on deploy |

| Hot keys | Replication lag |
|---|---|
| Celebrity profile saturates one Redis shard | User posts, reloads, can't see it |
| Fix: replicate key + local LRU | Fix: read-your-own-writes |

---

## SLIDE 10 — Freshness budget

**Title:**
Assign a freshness budget per surface

**List:**

- Home feed. 30s eventual. Cache + replica.
- Like count. 60s. Redis TTL.
- Inventory at PDP. 30 to 60s. Redis TTL.
- Inventory at checkout. Strong. Primary DB.
- Account balance. Strong. Primary DB.

**Bottom line:**
Not everything belongs in a cache.

---

## SLIDE 11 — When NOT to use it

**Title:**
When NOT to use this pattern

**3 boxes:**

Write-heavy workloads. Precomputing is wasted work.

Strong consistency required. Payments, balances, ledgers.

No pressure yet. Caching adds an invalidation surface.

**Bottom line:**
Caching must earn its place.

---

## SLIDE 12 — The summary

**Title:**
The 5-layer read path

**Final diagram:**
```
  Client
    |
    v
  1. CDN / Edge           static, hashed URLs
    |
    v
  2. App tier             stateless, LB in front
    |
    v
  3. Cache (Redis)        TTL + jitter + versioned keys
    |
    v
  4. Read replicas        async replication, read-your-writes
    |
    v
  5. Primary DB           all writes, source of truth
```

**Bottom line:**
The request that reaches layer 5 should be rare, cheap, and intentional.

---

## SLIDE 13 — Closing CTA

**Title:**
Now the 12 questions to ask before "just add Redis"

**List:**

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
  What's the cost vs capacity?
  Who owns the rebuild path?
```

**Bottom line:**
If you can answer all 12, you design at the level this pattern deserves.

---

## SLIDE 14 — End card

**Title:**
If this helped

**3 lines:**

1. Repost to help another engineer.
2. Follow for more deep-dives.
3. Drop a comment with what you're designing.

**Bottom:**
Your name. Principal Engineer.
Link to full Medium article.

---

# PRODUCTION NOTES

**Visual style:**
- Background: #0A0A0A near-black
- Primary text: #FFFFFF white
- Accent: #00D4FF cyan for highlights, numbers, arrows
- Font: Inter or Helvetica Neue
- Title size: 60 to 80pt
- Body size: 28 to 36pt
- Code/values: JetBrains Mono or Fira Code

**Layout per slide:**
- 80 to 100px padding
- Title at top with accent underline
- One core idea per slide
- Brand mark in bottom-right

**Avoid:**
- Walls of text (split into two slides if it doesn't fit)
- Stock photos (kills credibility with engineers)
- Multiple competing colors

**Posting tips:**
- Tuesday to Thursday, 9 to 11am in audience timezone
- Caption below: 3 to 5 line hook + "Full deep-dive in comments + on Medium"
- Pin for 7 days
- Engage in the first 2 hours
