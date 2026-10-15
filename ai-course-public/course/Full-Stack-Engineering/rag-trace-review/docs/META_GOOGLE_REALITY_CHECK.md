# Meta L6 / Google L5 Interview — Reality Check
## What this course gives you vs. what you still need

---

## Short answer

**This course gets you to ~60–70% of what Meta L6 / Google L5 full-stack interviews test.** The remaining 30–40% is **system design**, **behavioral**, and **execution speed under pressure** that no reading material can give you.

If you do only this course, you will likely **fail** the system design round and **struggle** in coding. If you do this + 8 weeks of LeetCode + 2 mock system designs per week, you have a real shot.

---

## What this course DOES give you (the 60–70%)

✅ **Cursor pagination** — you can explain keyset vs OFFSET, write the WHERE clause cold, debug the tie-breaker.
✅ **Optimistic UI with rollback** — you can write the canonical `onMutate`/`onError`/`onSettled` pattern from memory.
✅ **Virtualization** — you can explain why it reduces DOM cost (not API cost) and write `useVirtualizer`.
✅ **FastAPI + Pydantic** — you can write a route, validate with `Field(pattern=...)`, and explain why 422 vs 400.
✅ **SQL + indexes** — you can read `EXPLAIN QUERY PLAN`, write a composite index, and explain ACID.
✅ **React + TypeScript** — you can write a component, hooks, controlled input, and debug a stale closure.
✅ **Debugging + tests** — you can write 14 pytest tests, mock with msw, use Playwright.
✅ **Packaging** — you can explain Dockerfile layers, 12-factor, and health checks.

These are the things the **coding round** tests for an L5/L6 full-stack role. If the interviewer asks "implement a virtualized list with optimistic feedback", you can ship it.

---

## What you do NOT have yet (the 30–40%)

### 1. System design (Meta L6: 45 min, Google L5: 45 min)

This is the **biggest gap**. The course doesn't cover:

- **"Design YouTube" / "Design a chat app" / "Design a rate limiter"** — you need to draw boxes and arrows.
- **Sharding, replication, consistency models** — the course only touches SQLite.
- **Caches (Redis, Memcached), CDNs, queues (Kafka, SQS)** — not covered.
- **Capacity estimation** — "this gets 100k QPS, so I need X shards and Y GB of RAM."
- **CAP theorem, eventual consistency, leader election** — the course is single-node.

**Resources to add:**
- *Designing Data-Intensive Applications* (Kleppmann) — chapters 5, 6, 7, 9.
- *System Design Interview* (Alex Xu) — Vol 1 + Vol 2.
- Hello Interview (youtube) — 50+ system design walkthroughs.
- Do 2 mock system designs per week with a friend.

### 2. Coding round (Meta: 45 min, Google: 45 min)

This course teaches **building features**, not **solving algorithmic puzzles under pressure**.

Meta L6 full-stack coding is closer to LeetCode Medium than to building a CRUD app. You need:

- **Arrays, hash maps, sliding window, two pointers** — Medium level.
- **Trees, graphs, BFS/DFS** — sometimes asked.
- **Dynamic programming** — rarely for full-stack, but happens.
- **Big-O analysis cold** — you should be able to say "this is O(n log n) because we sort and then walk" in 5 seconds.

**Resources to add:**
- LeetCode: 150 problems, Medium, in your weak areas. Time-box 30 min each.
- NeetCode 150 roadmap.
- For Meta: focus on arrays, strings, hash maps. For Google: add graphs and DP.

### 3. Behavioral (Meta: 30 min, Google: 30 min)

The course is technical. Behavioral is a separate muscle.

You need 5–7 STAR stories ready:
- A project you led end-to-end (this course counts).
- A conflict you resolved.
- A time you disagreed with your manager.
- A failure and what you learned.
- A time you influenced without authority.
- A time you shipped under pressure.
- A time you mentored someone.

**Resources to add:**
- Read the company's leadership principles (Meta: "Move Fast", "Be Bold"; Google: "Googliness", "Leadership").
- Practice out loud. Time yourself at 3 minutes per story.

### 4. Domain knowledge (AI-native roles)

You said this is for an **AI-native** role. The course has:
- RAG traces ✅
- Prompt versions ✅
- Token usage ✅
- Latency ✅

But it does NOT have:
- **Vector databases** (Pinecone, Weaviate, pgvector).
- **LLM APIs** (streaming, function calling, JSON mode).
- **Eval frameworks** (LangSmith, Phoenix, Ragas).
- **Cost optimization** (caching, batching, model cascading).

**Resources to add:**
- Build a side project that uses the OpenAI API end-to-end.
- Read the *Designing Machine Learning Systems* book (Huyen) — chapters on inference, evals, monitoring.

---

## Honest scorecard (what this course is worth)

| Area | Course coverage | What you still need |
|---|---|---|
| React + TS | 9/10 | Real-time practice (no substitute) |
| FastAPI + SQL | 9/10 | Same |
| Cursor pagination | 10/10 | None — you can teach this |
| Optimistic UI | 9/10 | Edge cases under flaky networks |
| Virtualization | 9/10 | Variable row heights, scroll restoration |
| System design | 4/10 | **Months of study** (Days 22–26 cover the framework; needs depth) |
| Algorithms | 4/10 | **100+ LeetCode** (Days 27–32 cover 12 patterns + 50 problems) |
| Behavioral | 0/10 | **Separate prep** |
| AI domain | 4/10 | Vector DBs, evals, cost |

---

## Recommended 8-week plan ON TOP of this course

| Week | Focus | Daily time |
|---|---|---|
| 1 | LeetCode NeetCode 75 (arrays, strings) | 60 min |
| 2 | LeetCode (hash maps, sliding window) | 60 min |
| 3 | LeetCode (trees, graphs) | 60 min |
| 4 | LeetCode (DP, backtracking) | 60 min |
| 5 | System design: read *DDIA* ch 5–7 | 60 min |
| 6 | System design: do 2 mocks/week | 90 min |
| 7 | AI domain: build a vector RAG app | 120 min |
| 8 | Behavioral: write 7 STAR stories | 45 min |

**Total: ~50 hours.** That's realistic.

---

## The brutal truth

For Meta L6 / Google L5 full-stack:

- **This course alone:** ~30% chance of passing. The system design round will sink you.
- **This course + 8 weeks of supplemental prep:** ~60–70% chance. The coding is solid; the system design and behavioral are still the wild cards.
- **This course + 8 weeks + 2 mock interviews per week:** ~75–85% chance.

No course can replace **doing real system designs out loud** and **solving real LeetCode under time pressure**.

---

## What to do right now

1. **Finish this course** (you have 21 days at 90 min = ~32 hours).
2. **Start LeetCode** — 1 problem per day, 30 min time-boxed, focus on Mediums.
3. **Read one system design per week** — Hello Interview or Alex Xu.
4. **Practice out loud** — every time you finish a LeetCode problem, explain it to a rubber duck for 2 minutes.
5. **Find a mock interview buddy** — 1 hour per week, alternating system design and coding.

---

## The good news

The parts of this course that exist are **really good**. Cursor pagination, optimistic UI, virtualization — these are exactly the patterns Meta and Google full-stack interviewers love to ask about because they're hard to do well and easy to do poorly. If you can whiteboard these, write them clean, and explain tradeoffs, you're ahead of 70% of candidates.

What you have is a **strong base for the coding round**. What's missing is the **system design**, **algorithms**, and **behavioral** muscles.

---

**Bottom line:** Treat this course as 30% of your total interview prep. The other 70% is LeetCode, system design, and behavioral. Do all three, and you have a real shot.
