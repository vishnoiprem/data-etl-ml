# How to Answer a System Design Interview Question

> Companion to **Module 00** — read this alongside the design docs.

This is the playbook. Every module in this course was written to give
you the *output* of this playbook for one specific system. Practice
applying the playbook yourself — that's how you internalize it.

---

## The 4-step framework

### Step 1: Clarify requirements (5 min)

Start every answer with questions. **Never start drawing boxes.** Good
questions:

- **Functional**: "What are the must-have features? What about nice-to-have?"
- **Users**: "How many daily active users? What devices?"
- **Scale**: "What's the read:write ratio? QPS? Storage?"
- **Latency**: "What's an acceptable p99 for the critical action?"
- **Consistency**: "Is the user OK if their follower count is 30 seconds
  stale? What about payment state?"
- **Existing infra**: "Are we on AWS? Any constraints on managed services?"

A clarifying question buys you 30 seconds of structured thinking, and
the interviewer *likes* it. It also signals that you know what
matters.

### Step 2: Back-of-envelope estimation (5 min)

Pick numbers. Round aggressively. The point is **ballpark**, not
precision.

Useful constants:
- 1 day = 86,400 s ≈ 10⁵ s
- 1 month = 2.5 × 10⁶ s
- 1 KB = 10³ B; 1 MB = 10⁶; 1 GB = 10⁹; 1 TB = 10¹²; 1 PB = 10¹⁵
- 1 byte per char of text
- 1 photo ≈ 200 KB
- 1 SD video minute ≈ 10 MB

Example: "100M users, 10% DAU = 10M DAU. Average user writes 1 post
and reads 20 feeds per day. So 10M writes/day ≈ 100 writes/sec and
200M reads/day ≈ 2,500 reads/sec."

Do the math out loud. Show your work.

### Step 3: High-level design (10 min)

Draw boxes. Label arrows.

```
[client]
   │
   ▼
[CDN / LB]
   │
   ▼
[App tier] ──► [Cache] ──► [Primary DB]
                  │              │
                  └─miss─────────┘
                                  │
                                  ▼
                            [Read replicas]
```

**Order of boxes to mention**:
1. Client (web/mobile)
2. Edge / CDN
3. Load balancer
4. App tier (stateless, horizontal)
5. Cache (Redis)
6. Primary DB
7. Read replicas
8. Async workers / queue
9. Object storage / blob
10. Search index / analytics

Don't draw all 10 every time. Draw the 4-6 that matter for the system.

### Step 4: Deep dive on hot path (15-20 min)

**This is where you win.** Pick the single most performance-critical
path and go deep. Examples:

| System | Hot path |
|---|---|
| URL Shortener | `GET /<key>` — cache → DB → 302 |
| Typeahead | Trie walk + top-K slice |
| Instagram | Home feed read (fanout-on-write) |
| Twitter | Timeline merge (write fanout + celeb pull) |
| YouTube | Video metadata read, CDN edge |
| Uber Eats | Order state machine, dispatch |

For your chosen hot path, draw:
- The exact API call.
- The data model (tables / collections / keys).
- The algorithm in plain English.
- The failure modes (what if cache is down? what if DB is slow?).
- The tradeoffs (what we picked, and what we gave up).

Then **stop and ask the interviewer** "want me to go deeper here, or
move on to a different area?" That gives them control and signals
maturity.

---

## Common interview anti-patterns

- **Starting with the database**: "we'll have a Postgres with a
  users table" — wrong. Start with the user; the data is an
  implementation detail.
- **Listing every technology you know**: "we'll use Kafka, Cassandra,
  Redis, ElasticSearch, Spark, Flink…" — name a technology only when
  it solves a specific problem.
- **Skipping failure modes**: every design you draw has a
  single point of failure. Identify it, then propose how to mitigate.
- **Not going deep**: "we'll cache things" — *how*, *where*,
  *eviction policy*, *cache stampede protection*? That's the
  interview.
- **Refusing to pick**: "we could do A or B, it depends" — *pick*,
  then say "the alternative would be X, with these tradeoffs." That
  shows you can decide.

---

## How to practice

1. Open any module's `design/README.md`.
2. Read only the Requirements + Capacity sections.
3. Close the doc.
4. Set a 45-min timer.
5. Re-derive the design on paper, applying the 4-step framework.
6. Open the doc. Compare. Where did you diverge? Why?
7. Repeat for the next module.

After 3 passes through all 39 systems, you'll find that the
differences are smaller than you think. The 8 patterns cover most of
it.
