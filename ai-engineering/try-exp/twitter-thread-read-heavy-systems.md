# Twitter/X Thread — Read-Heavy Systems

> Format: 14-tweet thread. Each tweet ≤ 280 chars (most well under). Designed for hooks, reshares, and bookmarking. Author handle + reply-to thread structure implied.

---

## TWEET 1 / 14 — Hook (the one that decides if anyone reads the rest)

**Post:**
A viral post is written once and read millions of times.

If your system treats both numbers the same, you will spend your weekends on-call.

Here's how principal engineers actually design read-heavy systems 🧵

---

## TWEET 2 / 14 — The asymmetry

**Post:**
Read:write ratios in real products:

• Instagram feed       → ~10,000 : 1
• Amazon product page  → ~1,000 : 1
• Twitter timeline      → ~500 : 1
• Bank ledger           → ~1 : 1

The first three need different architecture than the last one.

---

## TWEET 3 / 14 — The principle

**Post:**
The one principle that decides every design decision:

"Do more work at write time so every read does less work."

Every caching, replication, and denormalization trick is a variation of that sentence.

---

## TWEET 4 / 14 — The naive design dies

**Post:**
Naive Instagram feed, per app open:

• 1 query for follows
• 500 queries for posts
• 500 joins for authors
• 1 ranking pass

≈ 1,000 queries
≈ 50,000 rows shuffled

…for ONE user opening the app. Scale to 500M DAU and the DB doesn't have a chance.

---

## TWEET 5 / 14 — The 5 layers

**Post:**
The 5-layer read path every read-heavy system has:

① CDN/edge       (cheapest read, may never hit you)
② App tier       (stateless, behind a load balancer)
③ Cache (Redis)  (hot objects, TTL+jitter)
④ Read replicas  (async replication)
⑤ Primary DB     (writes only, most protected node)

---

## TWEET 6 / 14 — Cache strategies (the part interviewers test)

**Post:**
4 cache strategies. Pick deliberately:

• Cache-aside    → default. App checks cache, falls through to DB.
• Read-through   → same, but cache library calls DB.
• Write-through  → slow writes, never stale.
• Write-behind   → async flushes. Has caused more outages in my career than every other pattern combined.

---

## TWEET 7 / 14 — Fan-out on write vs read (the celebrity problem)

**Post:**
Fan-out on write: post → push into every follower's timeline.
✓ Reads dirt cheap
✗ Writes cost O(followers)

Fan-out on read: store nothing, merge at read time.
✗ Reads expensive

A user with 100M followers breaks fan-out-on-write (17 min of writes per tweet).

Solution: hybrid. Push for normal users, pull for celebrities.

---

## TWEET 8 / 14 — Invalidation

**Post:**
4 invalidation strategies (least → most effort):

1. TTL + jitter
2. Explicit DEL
3. Event-driven (write publishes, consumer rebuilds)
4. Versioned keys (bump version, old keys expire naturally)

Versioned keys are the single biggest defensive technique I know. No DEL to forget.

---

## TWEET 9 / 14 — Cache stampede

**Post:**
Hot key expires → 50k concurrent requests all recompute at once → database melts.

Fixes:
• TTL jitter (spread expirations)
• Per-key locking (one wins, others wait)
• Stale-while-revalidate (serve old, refresh in background)

If you cache anything popular, you owe it stampede protection.

---

## TWEET 10 / 14 — The cold start trap

**Post:**
Cold start: deploy/flush/cache failure → every request hits DB at once.

Rule I tattoo on every design doc:

"Before you add caching, prove your database can survive an empty cache. THEN add caching."

If it can't, caching is a required dependency, not an optimization.

---

## TWEET 11 / 14 — Replication lag

**Post:**
Classic bug:

1. User posts a comment
2. Reloads feed
3. Replica hasn't caught up
4. User: "my comment disappeared!"

Fixes (collectively: read-your-own-writes):
• Pin writer's reads to primary briefly
• Monotonic reads (sticky replica per user)
• Version tokens (replica waits until caught up)
• Optimistic UI (render pending, reconcile later)

---

## TWEET 12 / 14 — Freshness budgets

**Post:**
Different surfaces, different staleness budgets:

Home feed         → 30s OK
Like count        → 60s OK
Inventory (PDP)   → 30–60s OK
Inventory (checkout) → strong
Account balance   → strong

"Not everything belongs in a cache."

Caching a bank balance is how you invent money.

---

## TWEET 13 / 14 — When NOT to use it

**Post:**
Skip this pattern when:

✗ Workload is write-heavy or balanced
✗ You need strong consistency (payments, ledgers)
✗ System isn't under pressure yet

Caching adds an invalidation surface and a new failure mode. It needs to earn its place.

---

## TWEET 14 / 14 — The 12 questions (close + CTA)

**Post:**
Before anyone says "just add Redis," ask:

1. For what?
2. With what TTL?
3. With what jitter?
4. Invalidated how?
5. Freshness budget?
6. Cold start plan?
7. Stampede control?
8. Hot-key strategy?
9. Negative cache?
10. Read-your-writes?
11. Cost vs capacity?
12. Who owns the rebuild path?

Answer all 12 → you design at the level this pattern deserves.

Full deep-dive in the next reply and on Medium.
[link to Medium article]

---

# THREAD POSTING STRATEGY

**Format:**
- Post tweet 1, immediately reply with tweet 2, etc.
- Wait 60–90 seconds between posts (avoids spam flags, gives each tweet oxygen)
- Or batch 2–3 at a time if you have a small following

**Timing:**
- Tuesday/Wednesday/Thursday, 9–11am or 7–9pm in audience TZ
- Tech Twitter peaks: Tue–Thu, 10am PT

**Engagement hooks:**
- End with a question ("What are you designing right now?")
- Quote-tweet your own thread 24 hours later with a "Part 2 coming" tease
- Pin the thread for 7 days

**Repurposing:**
- Same thread → LinkedIn (longer form, add 1 paragraph per tweet)
- Same thread → Substack (each tweet = a section)
- Best tweet → standalone quote-tweet 1 week later

**Visual variants (boost engagement 2–3x):**
- Tweets 4, 5, 7, 11, 14 → attach a diagram image (same ASCII art from the article, screenshot to PNG)
- Use the dark background + cyan accent style from the carousel

**Hashtags (sparingly):**
- #systemdesign (broad reach)
- #backend (targeted)
- Avoid more than 2 per tweet

---

# ENGAGEMENT-FIRST VARIANTS

If you want maximum reshare velocity, swap these tweets in:

**Alt hook (Tweet 1):**
Your database isn't slow.
It's structurally incapable of doing what you're asking of it.

Here's what I mean 🧵

**Alt principle (Tweet 3):**
The cheapest read you can serve is the one that never reaches your infrastructure.

That's the whole game.

**Alt close (Tweet 14):**
Hot take: "just add Redis" is the most expensive sentence in system design.

Reply with the system you're currently building — I'll tell you the 3 questions to ask before you cache anything.
