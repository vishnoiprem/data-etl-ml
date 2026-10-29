# 100-POINT REVIEW: All 7 Mock Loops

**Purpose:** Cross-loop validation. 100 points, 1 per question, scored against L6 bar.
**How to use:** Open this on your phone, score yourself 1/0 per question, target 85+.

---

## SECTION A: Greet (all 7 loops) - 15 points

| # | Question | Pass | Why |
|---|----------|------|-----|
| 1 | Can you pitch APEX-RAG in 2 minutes flat? | ☐ | Includes: 100M docs, 10 shards, Recall@8 0.89, eval harness, 6 years DE |
| 2 | Do you say "I built" not "we built" 80%+ of the time? | ☐ | L6 owns, doesn't just contribute |
| 3 | Did you include at least 3 concrete metrics? | ☐ | Numbers > adjectives. 400ms, $130k, 0.89 |
| 4 | Did you avoid "um/uh" filler? | ☐ | Practice out loud 5x |
| 5 | Did you explain WHY AI-Native DE vs pure DE? | ☐ | Pipelines without eval = useless for AI |
| 6 | Did you say "cursor O(1) not OFFSET"? | ☐ | Once is enough, not 5x |
| 7 | Did you say "dual-write shadow"? | ☐ | Production pattern L6 knows |
| 8 | Did you ask 2 smart questions back? | ☐ | "How does team measure quality today?" |
| 9 | Did you thank the interviewer? | ☐ | Always do this |
| 10 | Did you NOT ask about salary? | ☐ | Wait for recruiter |
| 11 | Did you say "Staff scope" for next role? | ☐ | L6 wants L7 next |
| 12 | Did you mention weakness = over-own + how you fixed? | ☐ | Honest + growth |
| 13 | Did you describe hardest decision (Qdrant vs ES)? | ☐ | Real tradeoff, not just "I picked X" |
| 14 | Did you have a "Why Meta" answer with scale number? | ☐ | 1B traces/day real here, not toy |
| 15 | Did you avoid "I'm a hard worker" / generic? | ☐ | L6 = specific examples, not platitudes |

---

## SECTION B: AI-Native DE Full Stack (all 7 loops) - 20 points

### Data modeling (5 points)

| # | Question | Pass | Why |
|---|----------|------|-----|
| 16 | Did you draw tables with PK + FK visible? | ☐ | Schema is the first thing interviewers look at |
| 17 | Did you distinguish modalities (text/table/image/metadata)? | ☐ | Loop 3 differentiator |
| 18 | Did you include PII fields, audit fields, version fields? | ☐ | Production schema, not toy |
| 19 | Did you partition tables by date when relevant? | ☐ | Scale awareness |
| 20 | Did you explain WHY you chose each field? | ☐ | Not just "here's the schema" |

### Pipeline (5 points)

| # | Question | Pass | Why |
|---|----------|------|-----|
| 21 | Did you name the tools (PyMuPDF, Flink, Spark, Qdrant)? | ☐ | Specific > vague |
| 22 | Did you include cost numbers ($130k, $30k, etc.)? | ☐ | Engineering = tradeoffs |
| 23 | Did you mention failure handling (DLQ, retry, alert)? | ☐ | Production = handles failure |
| 24 | Did you mention observability (metrics, logs, traces)? | ☐ | You can't fix what you can't see |
| 25 | Did you distinguish online vs offline? | ☐ | L6 thinks about both |

### SQL (5 points)

| # | Question | Pass | Why |
|---|----------|------|-----|
| 26 | Did you write SQL with JOIN, GROUP BY, HAVING? | ☐ | Not just SELECT * |
| 27 | Did you use window functions when relevant (TUMBLE, ROW_NUMBER)? | ☐ | Streaming SQL is L6+ |
| 28 | Did you include cost/SLA alerting in query? | ☐ | Operational thinking |
| 29 | Did you use `EXPLAIN` or query plan if asked? | ☐ | Deep SQL knowledge |
| 30 | Did you handle NULL or empty cases? | ☐ | Edge case awareness |

### Coding (5 points)

| # | Question | Pass | Why |
|---|----------|------|-----|
| 31 | Did your code compile / run without syntax errors? | ☐ | First bar |
| 32 | Did you write type hints / docstrings? | ☐ | Production code quality |
| 33 | Did you handle edge cases (empty, None, large input)? | ☐ | Defensive coding |
| 34 | Did you include unit-testable functions? | ☐ | Testable design |
| 35 | Did you explain complexity (O(N), O(log N))? | ☐ | Algorithmic awareness |

---

## SECTION C: Sr Tech Design (all 7 loops) - 25 points

### Requirements & scope (5 points)

| # | Question | Pass | Why |
|---|----------|------|-----|
| 36 | Did you ask clarifying questions BEFORE designing? | ☐ | L6 defines problem first |
| 37 | Did you name scale (QPS, MAU, data size)? | ☐ | Can't design without numbers |
| 38 | Did you define SLO (p95 latency, freshness)? | ☐ | L6 thinks in SLOs |
| 39 | Did you ask about edge cases (cold start, ACL, GDPR)? | ☐ | Production = thinks about edges |
| 40 | Did you define success metrics (Recall@K, satisfaction, cost)? | ☐ | You can't measure success without metrics |

### High-level architecture (10 points)

| # | Question | Pass | Why |
|---|----------|------|-----|
| 41 | Did you draw the system with components named? | ☐ | Whiteboard = visual |
| 42 | Did you distinguish offline / online / hybrid paths? | ☐ | Different tradeoffs |
| 43 | Did you name the storage layer (Qdrant, ES, TAO)? | ☐ | Specific > generic |
| 44 | Did you include feedback loop (gold dataset, retrain)? | ☐ | L6 = closed loop |
| 45 | Did you include monitoring/alerting in design? | ☐ | Observability is not optional |
| 46 | Did you name the embedding model? | ☐ | text-embedding-3-large, CLIP, etc. |
| 47 | Did you describe the rerank step? | ☐ | Search ≠ just retrieval |
| 48 | Did you describe the LLM prompt with evidence_json? | ☐ | Grounded generation pattern |
| 49 | Did you explain how ACL is enforced? | ☐ | Loop 6 critical |
| 50 | Did you mention cost per query? | ☐ | Engineering = economics |

### Deep dive (5 points)

| # | Question | Pass | Why |
|---|----------|------|-----|
| 51 | Did you compute scale math (1B chunks, 50M/shard)? | ☐ | L6 = numbers |
| 52 | Did you name bottleneck and how to mitigate? | ☐ | Identify the hardest problem |
| 53 | Did you propose alternatives considered? | ☐ | L7 = tradeoffs |
| 54 | Did you describe 2-3 ways to scale further? | ☐ | L6 = scale thinking |
| 55 | Did you identify what you'd cut for v1? | ☐ | Scope discipline |

### Wrap-up (5 points)

| # | Question | Pass | Why |
|---|----------|------|-----|
| 56 | Did you name 2-3 things deliberately out of scope? | ☐ | L6 = scope |
| 57 | Did you describe what you'd build next? | ☐ | Forward thinking |
| 58 | Did you mention the failure mode and mitigation? | ☐ | Production = anticipates failure |
| 59 | Did you describe observability for the system? | ☐ | Can't operate blind |
| 60 | Did you close with "any questions?" | ☐ | L6 invites pushback |

---

## SECTION D: Sr Ownership (all 7 loops) - 20 points

### STAR structure (10 points)

| # | Question | Pass | Why |
|---|----------|------|-----|
| 61 | Did you start with S - situation (30 sec, with metric)? | ☐ | Sets the stakes |
| 62 | Did you state T - task (15 sec, your ownership)? | ☐ | "I owned" not "we were asked" |
| 63 | Did you describe A - action in 4+ steps? | ☐ | Detailed, not vague |
| 64 | Did you name specific tools/tech (Kafka, Flink, Spark)? | ☐ | Concreteness = senior |
| 65 | Did you describe a specific bug or root cause? | ☐ | Engineering = debugging |
| 66 | Did you include numbers (400ms → 420ms)? | ☐ | Quantified impact |
| 67 | Did you say "owned without being asked" at least once? | ☐ | L6 keyword |
| 68 | Did you end with R - result (30 sec, with metric + adoption)? | ☐ | Impact |
| 69 | Did you mention runbook / dashboard / system left behind? | ☐ | L6 = systems not just code |
| 70 | Did you answer "what would you do differently" probe? | ☐ | Growth mindset |

### Story quality (5 points)

| # | Question | Pass | Why |
|---|----------|------|-----|
| 71 | Did you have a latency story (400 → 2500 → 420ms)? | ☐ | Always have this |
| 72 | Did you have a cost story ($130k → $30k)? | ☐ | Shows business thinking |
| 73 | Did you have a conflict story (chunks vs embeddings)? | ☐ | Influence without authority |
| 74 | Did you have an ambiguity story (defined metrics first)? | ☐ | L6 = defines problem |
| 75 | Did you have a failure story (OFFSET → cursor)? | ☐ | Self-aware |

### Depth (5 points)

| # | Question | Pass | Why |
|---|----------|------|-----|
| 76 | Did you describe the rollback plan in detail? | ☐ | 5-min rollback is the bar |
| 77 | Did you describe the prevention step? | ☐ | Runbook, alert, dashboard |
| 78 | Did you describe cross-team adoption? | ☐ | L6 = scales via others |
| 79 | Did you describe the data-driven decision? | ☐ | Showed PM the cost model |
| 80 | Did you describe scaling via delegation? | ☐ | L6 = multiplies team |

---

## SECTION E: Full Stack (all 7 loops) - 20 points

### API design (5 points)

| # | Question | Pass | Why |
|---|----------|------|-----|
| 81 | Did you write actual API contract (path, method, body)? | ☐ | Not just "REST endpoint" |
| 82 | Did you include error cases (400, 401, 429)? | ☐ | Production = handles errors |
| 83 | Did you include response shape with examples? | ☐ | Concrete |
| 84 | Did you describe auth (JWT, OAuth, API key)? | ☐ | Security awareness |
| 85 | Did you describe pagination if relevant? | ☐ | Scale = pagination |

### UI/UX (10 points)

| # | Question | Pass | Why |
|---|----------|------|-----|
| 86 | Did you draw the UI with components? | ☐ | Visual, not just code |
| 87 | Did you use state management (useState, Redux)? | ☐ | React fundamentals |
| 88 | Did you handle loading and error states? | ☐ | Production UX |
| 89 | Did you include feedback mechanism (thumbs, rating)? | ☐ | Closed loop |
| 90 | Did you include accessibility (aria, keyboard nav)? | ☐ | L6 = inclusive |
| 91 | Did you include optimistic UI updates? | ☐ | Performance UX |
| 92 | Did you include copy-to-clipboard or share? | ☐ | Common feature |
| 93 | Did you include empty states ("No results")? | ☐ | Edge case UX |
| 94 | Did you include mobile-responsive design? | ☐ | Modern web |
| 95 | Did you describe the testing approach? | ☐ | Component, integration, E2E |

### Polish (5 points)

| # | Question | Pass | Why |
|---|----------|------|-----|
| 96 | Did you add diff view / side-by-side comparison? | ☐ | L6 differentiates UI |
| 97 | Did you add stats footer / aggregate metrics? | ☐ | Data-driven UI |
| 98 | Did you include the cross-round integration (gold dataset)? | ☐ | Shows system thinking |
| 99 | Did you describe performance optimization (memo, lazy)? | ☐ | Production code |
| 100 | Did you describe the deploy strategy (Vercel, Docker)? | ☐ | End-to-end ownership |

---

## SCORING INTERPRETATION

| Score | Verdict | Action |
|-------|---------|--------|
| 90-100 | **Strong hire + bar-raiser** | You're ready. Do a final mock. |
| 80-89 | **Strong hire** | You're ready. Polish weak spots. |
| 70-79 | **Hire (L5→L6)** | Practice 2-3 more loops, focus on weak areas. |
| 60-69 | **Lean hire** | Need more STAR stories, more SQL/coding reps. |
| 50-59 | **No hire** | 1 week of focused practice, redo weak areas. |
| < 50 | **Strong no hire** | Reset, restart with Loop 1-2 first. |

---

## WEAK AREA DIAGNOSIS

**If you scored low in Section A (Greet):**
- Practice pitch 10x out loud with timer
- Record yourself, count "um/uh"
- Memorize 3 stories (latency, cost, conflict)

**If you scored low in Section B (AI-Native DE):**
- Code 5 SQL queries a day for a week
- Code 5 Python functions (rate limiter, PII scrubber, Recall@K, etc.)
- Draw 5 data models from real systems (Twitter, Uber, Airbnb)

**If you scored low in Section C (Tech Design):**
- Whiteboard 1 system per day (Uber, Twitter, Dropbox, Notion, Slack)
- Practice asking 5 clarifying questions first
- Compute scale math (QPS, shards, cost)

**If you scored low in Section D (Ownership):**
- Write 5 STAR stories: latency, cost, conflict, ambiguity, failure
- Practice each story 3x out loud
- Get a friend to probe you with "what would you do differently"

**If you scored low in Section E (Full Stack):**
- Build 1 React component per day (focus on state, errors, loading)
- Practice drawing UI before coding
- Add feedback mechanism to every UI

---

## FINAL CHECKLIST BEFORE REAL INTERVIEW

### Day Before

- [ ] Sleep 8+ hours
- [ ] Re-read this 100-point review
- [ ] Tell 3 STAR stories out loud, 5x each
- [ ] Practice 2-min pitch 5x with timer
- [ ] Code from memory: rate limiter, PII scrubber, Recall@K, nDCG@K
- [ ] Draw 1 system design from memory (e.g., YouTube)

### Day Of (Morning)

- [ ] Eat protein breakfast
- [ ] 30 min light review (skim, don't cram)
- [ ] 10 min breathing exercises
- [ ] Remind yourself: "I define the problem, then I solve it"

### During Interview

- [ ] 2-min pitch under time
- [ ] 3+ concrete metrics per answer
- [ ] "I" 80%+ of the time
- [ ] "I owned without being asked" at least once
- [ ] End with prevention: runbook + dashboard + gold dataset
- [ ] Ask 2 smart questions back

### After Each Round

- [ ] Thank interviewer
- [ ] Note 1 thing you did well
- [ ] Note 1 thing to improve
- [ ] Reset, breathe, next round

---

**You've prepared 7 loops × 5 rounds = 35 round scripts.**
**You've coded 30+ functions from memory.**
**You have 100 review points to grade yourself.**
**You're ready. The bar is high. You can hit it.**

**Good luck. 🚀**
