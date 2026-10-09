# Module 6 — Take-Home Assignments

> **Take-homes test whether you can ship, not just whiteboard.** A 4-8 hour build + a 1-hour presentation. The interviewer wants to see code you actually wrote, decisions you actually made, and tradeoffs you can defend. **The signal: a candidate who delivers a working system, with a runbook, an eval set, and a cost model, is showing they can do the FDE work.**

---

## The 3 take-home patterns

### Pattern 1: Prototype (e.g., OpenAI semantic search)

**The OpenAI take-home:** "Build a semantic search system over a corpus of 10k documents. The system should return the top-5 most relevant documents for a natural-language query. You have 4 hours. Use any tools you want."

**The 4-step build:**

1. **Hour 1: spec + eval set.** Build a 30-row eval set (10 queries, 3 relevant docs each). The eval set is the spec.
2. **Hour 2: retrieval.** BM25 + dense embeddings + RRF. The simplest hybrid retriever.
3. **Hour 3: API + UI.** A FastAPI endpoint + a simple HTML page. The API takes a query, returns top-5 docs with relevance scores.
4. **Hour 4: cost model + runbook.** The $/month calculation, the cost ceiling, the 1-page runbook.

**The 5 deliverables:**

1. **The eval set** (30 rows, with the queries + the relevant doc IDs + the relevance scores).
2. **The retrieval code** (Python file, ~100 lines, with the BM25 + dense + RRF).
3. **The API** (FastAPI, ~50 lines, with the GET /search endpoint).
4. **The UI** (HTML + JS, ~50 lines, with the search box + the results).
5. **The README** (1 page: how to run, the cost model, the runbook).

**The signal:** the eval set is the differentiator. Most candidates skip it. The eval set is the FDE signal.

### Pattern 2: Pipeline (e.g., Labelbox RLHF data pipeline)

**The Labelbox take-home:** "Build a data pipeline that takes a stream of model outputs, samples them for human review, and produces a labeled dataset for RLHF. You have 6 hours. Use any tools you want."

**The 4-step build:**

1. **Hour 1: spec + sampling strategy.** Define the sampling strategy (random, stratified, active learning). The spec is the strategy.
2. **Hour 2: pipeline + queue.** A producer (model outputs) + a queue (Redis) + a consumer (human review UI).
3. **Hour 3: labeling UI + storage.** A simple HTML form + Postgres for the labeled data.
4. **Hour 4: cost model + runbook.** The $/month calculation, the cost ceiling, the 1-page runbook.
5. **Hour 5-6: polish + tests.** Tests, error handling, edge cases.

**The 5 deliverables:**

1. **The sampling strategy** (1 page: random vs stratified vs active learning, with the tradeoff).
2. **The pipeline code** (Python file, ~150 lines, with the producer + queue + consumer).
3. **The labeling UI** (HTML + JS, ~100 lines, with the form + the Postgres write).
4. **The cost model** (1 page: $/month for 1k, 10k, 100k labels).
5. **The README** (1 page: how to run, the cost model, the runbook).

### Pattern 3: The "ship + defend" take-home (e.g., a full FDE engagement)

**The most common take-home at senior FDE roles:** "Here's a customer brief. Build a system that satisfies the brief. You have 8 hours. Use any tools you want. You'll present it for 1 hour."

**The 4-step build:**

1. **Hour 1: spec + eval set.** Build the eval set. The eval set is the spec.
2. **Hour 2: architecture + retrieval.** The 4 services, the 3 data stores, the 2 LLM calls.
3. **Hour 3-4: implementation.** The retrieval service + the inference service + the API.
4. **Hour 5: feedback + metrics.** The thumbs-up/down endpoint + the Prometheus counter.
5. **Hour 6: cost model + runbook.** The $/month calculation + the 1-page runbook.
6. **Hour 7: tests.** 5-10 tests, including the eval set, the API, the cost calculation.
7. **Hour 8: README + presentation.** The 1-page README + the 10-slide deck.

**The 7 deliverables:**

1. **The eval set** (30 rows, with the 4 metrics).
2. **The retrieval code** (~100 lines).
3. **The inference code** (~100 lines, with the LLM call + the circuit breaker).
4. **The API** (~50 lines, with the POST /draft + POST /feedback).
5. **The cost model** (1 page).
6. **The runbook** (1 page).
7. **The README + presentation** (1 page + 10 slides).

**The signal:** the 7 deliverables are the FDE signal. Most candidates deliver 1-2 (the code, maybe a README). The senior FDE delivers all 7.

---

## The 5 take-home anti-patterns

1. **Spending 6 hours on the code, 0 on the eval set.** The eval set is the spec. Without it, the code is ungrounded.
2. **Skipping the cost model.** "It would cost $X/month" without the math is hand-waving. The math is the signal.
3. **Skipping the runbook.** The runbook is the artifact that survives your exit. Without it, the system is a prototype, not a product.
4. **Using a fancy framework (LangChain, LlamaIndex) when simple code would do.** The interviewer is testing your judgment, not your framework knowledge. Simple code + clear comments > fancy framework + opaque behavior.
5. **Skipping the tests.** 5-10 tests, including the eval set, the API, and the cost calculation. The tests are the proof that the code works.

---

## The 3 take-home presentation patterns

### Pattern 1: "Here's what I built" (default for Pattern 1 + 2)

- 5 min: the problem + the spec
- 10 min: the live demo (show the system working)
- 10 min: the architecture + the eval set + the cost model
- 10 min: the tradeoffs + the "what I'd do differently"
- 5 min: Q&A

**Total: 40 minutes.** The live demo is the signal.

### Pattern 2: "Here's what I built + here's the customer narrative" (for Pattern 3)

- 5 min: the customer + the problem + the constraint
- 10 min: the live demo
- 10 min: the architecture + the eval set + the cost model + the runbook
- 10 min: the tradeoffs + the "what I'd do differently"
- 5 min: Q&A

**Total: 40 minutes.** The customer narrative is the FDE signal.

### Pattern 3: "Here's the take-home, evaluated as if you were the customer" (for senior FDE roles)

- 5 min: the customer's perspective ("if I were the customer, here's what I'd want to see")
- 10 min: the live demo
- 10 min: the architecture + the eval set + the cost model + the runbook + the handoff
- 10 min: the tradeoffs + the "what I'd do differently + what I'd ask the next FDE to do"
- 5 min: Q&A

**Total: 40 minutes.** The handoff is the principal FDE signal.

---

## How to use this module

1. **Pick a target company.** OpenAI = Pattern 1; Labelbox = Pattern 2; Anthropic / Palantir = Pattern 3.
2. **Build the take-home in 4-8 hours.** Time yourself. The 4-hour time pressure is real.
3. **Deliver all 7 deliverables.** The 7 are the FDE signal.
4. **Rehearse the 40-minute presentation.** The live demo is the highest-leverage 10 minutes.
5. **Rehearse with an AI assistant.** Have it score you on the 5 anti-patterns.
6. **Use the cost model + runbook as the closing line.** "Total cost: $X/month at Y QPS, under the $Z/month ceiling. The runbook is 1 page; the handoff is the 5-question test." That's the FDE answer.
