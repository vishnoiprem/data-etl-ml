# LinkedIn Carousel — Read-Heavy Systems

> Format guide: each slide is one image (1080×1350 px, 4:5 portrait).
> Suggested tool: Canva, Figma, or LinkedIn's native carousel creator.
> Style: dark background (#0A0A0A), white text, one accent color (#00D4FF cyan), large sans-serif (Inter / Helvetica).

---

## SLIDE 1 — Hook

**Title:**
# Read-Heavy Systems
## The pattern behind every app you've ever scrolled.

**Subtitle:**
A 3-minute crash course from a principal engineer.

**Footer / branding (small, bottom-right):**
Your name · Principal Engineer

---

## SLIDE 2 — The asymmetry

**Title:**
## The asymmetry that breaks naive designs

**Body (large):**
> 1 viral post
> 1 write.

> 300,000,000 reads.

**Caption (small):**
Read:write ratio is 100:1 to 10,000:1 in most products. If your system treats both the same, you will spend weekends on-call.

---

## SLIDE 3 — The principle

**Title:**
## The one principle

**Big quote (centered):**

> "Do more work at write time so every read does less work."

**Caption:**
Every caching, replication, and denormalization trick is a variation of this sentence.

---

## SLIDE 4 — Naive design dies

**Title:**
## The naive design (and why it dies)

**Body (left column):**
Instagram feed, naive:
1. Find who you follow
2. Fetch last 50 posts per account
3. Merge, rank, hydrate
4. Return top 20

**Body (right column, big number):**
≈ 1,000 queries
≈ 50,000 rows shuffled
…per single app open

**Caption:**
Multiply by 500M daily users. Database is not slow. It is structurally incapable.

---

## SLIDE 5 — The 5 layers

**Title:**
## The 5 layers of read scaling

**Diagram (top half, stacked vertically):**
```
①  CDN / Edge            ← cheapest read
②  App tier              ← stateless
③  Cache (Redis)         ← hot objects
④  Read replicas         ← multiplies QPS
⑤  Primary DB            ← source of truth
```

**Caption:**
Each layer catches what the one above missed.

---

## SLIDE 6 — Cache strategies

**Title:**
## The 4 cache strategies (pick deliberately)

**Table format:**
| Strategy | When to use |
|---|---|
| **Cache-aside** | The default. Most apps start here. |
| **Read-through** | Cache library owns the lifecycle. |
| **Write-through** | Stale reads are unacceptable. |
| **Write-behind** | Rarely. You can lose acknowledged writes. |

**Footer note:**
Write-behind has caused more outages in my career than every other pattern combined.

---

## SLIDE 7 — The celebrity problem

**Title:**
## The celebrity problem
### (Why Twitter isn't pure fan-out-on-write)

**Body:**
A user with 100M followers posts.
Pure fan-out-on-write = 100M timeline writes.
That's 17 minutes at 100k writes/sec.

**Big quote:**
> Hybrid: push for normal users,
> pull for celebrities.

---

## SLIDE 8 — Invalidation

**Title:**
## Cache invalidation — 4 strategies

**Numbered list (large):**
1. **TTL + jitter** — simplest, bounds staleness
2. **Explicit DEL** — precise, but miss one path = stale forever
3. **Event-driven** — write publishes event, consumer rebuilds
4. **Versioned keys** — bump version, old keys expire naturally

**Highlighted bottom box:**
Versioned keys are the single biggest defensive technique I know.

---

## SLIDE 9 — Failure modes

**Title:**
## 4 failure modes that ruin weekends

**Grid (2×2):**
| **Cache stampede** | **Cold start** |
|---|---|
| Hot key expires → 50k concurrent recomputes | Empty cache floods DB |
| Fix: single-flight lock + jitter | Fix: pre-warm on deploy |

| **Hot keys** | **Replication lag** |
|---|---|
| Celebrity profile saturates one Redis shard | User posts, reloads, can't see it |
| Fix: replicate key + local LRU | Fix: read-your-own-writes |

---

## SLIDE 10 — Freshness budget

**Title:**
## Assign a freshness budget per surface

**List:**
- **Home feed** — 30s eventual → cache + replica
- **Like count** — 60s → Redis TTL
- **Inventory at PDP** — 30–60s → Redis TTL
- **Inventory at checkout** — strong → primary DB
- **Account balance** — strong → primary DB

**Big bottom quote:**
> Not everything belongs in a cache.

---

## SLIDE 11 — When NOT to use it

**Title:**
## When NOT to use this pattern

**3 boxes (stacked):**

**Write-heavy workloads** — precomputing is wasted work

**Strong consistency required** — payments, balances, ledgers

**No pressure yet** — caching adds an invalidation surface

**Footer:**
Caching must earn its place.

---

## SLIDE 12 — The summary

**Title:**
## The 5-layer read path

**Final diagram (large):**
```
Client
   │
   ▼
① CDN / Edge           (static, hashed URLs)
   │
   ▼
② App tier             (stateless, LB in front)
   │
   ▼
③ Cache (Redis)        (TTL + jitter + versioned keys)
   │
   ▼
④ Read replicas        (async replication, read-your-writes)
   │
   ▼
⑤ Primary DB           (all writes, source of truth)
```

**Caption:**
The request that reaches layer ⑤ should be rare, cheap, and intentional.

---

## SLIDE 13 — Closing CTA

**Title:**
## Now the 12 questions to ask before "just add Redis"

**Big quote:**
> Add Redis for *what*?
> With *what* TTL?
> With *what* jitter?
> Invalidated *how*?
> What's the freshness budget?
> What happens at cold start?
> What happens on stampede?
> What if the key is hot?
> What if it doesn't exist?
> What if the user just wrote?
> What's the cost vs. capacity?
> Who owns the rebuild path?

**Footer:**
If you can answer all 12 — you design at the level this pattern deserves.

---

## SLIDE 14 — End card

**Title (centered, large):**
# If this helped:
## 1. Repost to help another engineer
## 2. Follow for more deep-dives
## 3. Drop a comment with what you're designing

**Bottom:**
Your name · Principal Engineer
Link to full Medium article →

---

# PRODUCTION NOTES

**Visual style:**
- Background: `#0A0A0A` (near-black)
- Primary text: `#FFFFFF`
- Accent: `#00D4FF` (cyan) for highlights, numbers, and arrows
- Warning accent: `#FF6B6B` (red) for failure modes
- Font: Inter or Helvetica Neue, 60–80pt for titles, 28–36pt for body

**Layout per slide:**
- Generous padding (80–100px)
- Title at top with accent underline
- One core idea per slide
- Diagram/code block in code-mono font (JetBrains Mono / Fira Code)
- Brand mark in bottom-right

**What to avoid:**
- Walls of text (if it doesn't fit, split into two slides)
- Stock photos (kills credibility with engineers)
- Multiple colors competing for attention

**Posting tips:**
- Publish Tuesday–Thursday, 9–11am in your audience's timezone
- Caption below the carousel: a 3–5 line hook + "Full deep-dive in the comments + on Medium"
- Pin the post for 7 days
- Engage in the first 2 hours (LinkedIn algorithm rewards early comments)

---

# SLIDE FILES (optional outputs)

If you want me to generate these as actual PNG images, I can:
- Output a single PDF with all slides (1080×1350 each) using a tool like `pdfkit` or `playwright`
- Output individual PNGs ready for upload

Just say "generate the carousel as PNG/PDF" and I'll produce the binary artifacts.
