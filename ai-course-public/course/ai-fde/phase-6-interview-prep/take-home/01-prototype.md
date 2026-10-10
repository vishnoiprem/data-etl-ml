# Take-Home Project 1 — The Prototype (build a working AI service in 4-8 hours)

> **The most common FDE take-home is "build a working AI service that calls an LLM API, handles failures, and processes real-ish data."** Timeboxed to 4-8 hours (or 1-2 weeks for the longer Loom-style take-homes at OpenAI / Anthropic). The signal: a candidate who ships a 70% solution with an eval set + a cost tracker + a circuit breaker + a rollback path is signaling they can do the FDE job. A candidate who ships a 100% solution with no eval set is signaling they can't.

---

## Why this module exists

The take-home is the centerpiece of the LangChain / Sierra AI / OpenAI loops. The 4-8 hr variant is also the centerpiece of Rippling, Anthropic, and most startup FDE loops. **The signal isn't the artifact; it's the choices.** The 4-criteria rubric below is the rubric every take-home is graded on.

The thesis: **the take-home is the FDE job in miniature.** A 4-8 hr take-home is a 4-8 hr FDE engagement. The same patterns apply: scope first, build second, evaluate third, hand off fourth. The candidate who treats it as a coding test fails. The candidate who treats it as a mini-engagement wins.

---

## The 4-criteria rubric (what the take-home is graded on)

Every FDE take-home is graded on the same 4 criteria. Memorize them.

### Criterion 1: Correctness (the artifact works end-to-end)

**What they test:** does the artifact actually run? Can the interviewer clone, install, and run it without help?

**The 5 sub-signals:**

1. **The README is correct** — `git clone` → `pip install` → `python main.py` works.
2. **The tests pass** — `pytest` runs and exits 0. Aim for 5-10 tests, not 50.
3. **The error handling is real** — when the API fails, the service degrades, not crashes.
4. **The artifact is reproducible** — random seeds are fixed, env vars are documented, dependencies are pinned.
5. **The artifact is small** — under 1000 lines of code. Bigger is worse for a take-home.

**The 3 most common failure modes:**

1. **The README is wrong** — `pip install -r requirements.txt` fails because of a missing package.
2. **The tests are flaky** — they pass on the candidate's machine but fail on the interviewer's.
3. **The artifact doesn't run** — the interviewer has to spend 30 minutes debugging the setup.

### Criterion 2: Observability (the artifact is measurable)

**What they test:** can the interviewer see what the artifact is doing? Are the metrics, logs, and traces exposed?

**The 5 sub-signals:**

1. **The metrics are exposed** — `/metrics` endpoint or `metrics.json` file with: request count, latency, error rate, cost.
2. **The logs are structured** — JSON logs with request_id, user_id, timestamp, latency, cost, model.
3. **The traces are correlated** — every log line has the same request_id; you can trace a request end-to-end.
4. **The eval set is checked in** — `eval/golden_set.jsonl` with 20-50 hand-labeled examples.
5. **The eval harness runs** — `python eval.py` prints the 4 metrics (faithfulness, ansrel, context_precision, context_recall).

**The 3 most common failure modes:**

1. **No metrics** — the artifact runs, but the interviewer can't see how it's doing.
2. **No eval set** — the artifact has no quality check; it might be hallucinating.
3. **Print-statement logging** — `print("got here")` is not a log; structured JSON is.

### Criterion 3: Cost ceiling (the artifact is sustainable)

**What they test:** does the artifact track its own cost? Is there a circuit breaker or rate limiter?

**The 5 sub-signals:**

1. **Cost is tracked per request** — tokens × $/token, summed in the response.
2. **A cost ceiling is enforced** — when the cost ceiling is hit, the service fails closed (returns a fallback response), not open.
3. **A rate limiter is in place** — no more than N requests per minute per user.
4. **A circuit breaker is in place** — when the API is failing, the service fails closed.
5. **The cost model is documented** — `COST_MODEL.md` explains: tokens per request, $/token, requests/day, $/day, $/month.

**The 3 most common failure modes:**

1. **No cost tracking** — the artifact uses the API but doesn't know how much it costs.
2. **No rate limiter** — the artifact can be DDoS'd by a single user.
3. **No circuit breaker** — when the API is down, the artifact crashes.

### Criterion 4: Handoff (the artifact is operable)

**What they test:** can the interviewer (or the customer) operate the artifact? Is the runbook + the on-call rotation documented?

**The 5 sub-signals:**

1. **A runbook is checked in** — `RUNBOOK.md` explains: how to deploy, how to roll back, what to do when X breaks.
2. **The deployment is one command** — `make deploy` or `./deploy.sh` does it all.
3. **The rollback is one command** — `make rollback` reverts to the previous version.
4. **The "FDE has left" test passes** — a colleague can pick up the artifact and operate it without help.
5. **The handoff checklist is documented** — `HANDOFF.md` lists: open issues, known limitations, next steps.

**The 3 most common failure modes:**

1. **No runbook** — the artifact is code, not a service.
2. **No rollback path** — the artifact is one-shot; if it breaks, you redeploy from scratch.
3. **No handoff checklist** — the candidate vanishes after the take-home, leaving the interviewer to figure it out.

---

## The 4-hour build plan (the timeboxed FDE)

Here's the 4-hour plan that hits all 4 criteria. Adapt to 8 hours or 1-2 weeks as needed.

### Hour 0-1: Scope (the most important hour)

**Goal:** lock scope. One workflow, one "wow" moment, 5 minutes. Don't build 5 workflows at 1 minute each.

**The 4 sub-tasks:**

1. **Read the prompt carefully.** Note: (a) the customer scenario, (b) the data format, (c) the time budget, (d) the deliverables.
2. **Pick the "wow" moment.** The one thing that, if it works, makes the customer say "I need this." Resist the urge to ship 5 things.
3. **List the cuts.** Auth/SSO, evals, edge cases, scale, agentic write actions, multi-tenancy. Cut ruthlessly.
4. **Sketch the architecture.** 1-page diagram: input → processing → output. Don't write code yet.

### Hour 1-2: Build the happy path

**Goal:** get the "wow" moment working with real data.

**The 4 sub-tasks:**

1. **Set up the repo.** `git init`, `README.md`, `requirements.txt`, `.env.example`, `Makefile`.
2. **Write the prompt.** 1 file, 50-100 lines. Include: system prompt, user prompt, JSON schema for output.
3. **Wire the LLM call.** OpenAI / Anthropic / open-source. Streaming if the artifact benefits from streaming.
4. **Test on 1-2 examples.** Manually run the artifact; verify the output is what you want.

### Hour 2-3: Add the 4 criteria

**Goal:** hit the 4-criteria rubric.

**The 8 sub-tasks:**

1. **Correctness:** write 5 pytest tests. Aim for the happy path + 1-2 edge cases.
2. **Observability:** add a `metrics.json` file or `/metrics` endpoint. Track: request count, latency, error rate, cost.
3. **Cost ceiling:** add a token counter + a circuit breaker (3-strike breaker). When the breaker is open, return a fallback.
4. **Rate limiter:** add a token-bucket rate limiter. 10 req/min per user.
5. **Structured logging:** replace print() with `logger.info({request_id, latency, cost})`. JSON format.
6. **Eval set:** write 20-50 hand-labeled examples. `eval/golden_set.jsonl` with input + expected output.
7. **Eval harness:** `eval.py` runs the golden set, prints the 4 metrics.
8. **Cost model:** `COST_MODEL.md` with: tokens/req, $/token, req/day, $/day, $/month.

### Hour 3-4: Operability + handoff

**Goal:** make the artifact operable by someone who isn't you.

**The 6 sub-tasks:**

1. **Runbook:** `RUNBOOK.md` with: how to deploy, how to roll back, what to do when X breaks.
2. **Deployment:** `make deploy` does it all. Use a free tier (Vercel, Railway, Modal, Fly.io).
3. **Rollback:** `make rollback` reverts to the previous version.
4. **Handoff checklist:** `HANDOFF.md` with: open issues, known limitations, next steps.
5. **Final test run:** run all 5 tests + the eval harness. Verify everything passes.
6. **README polish:** the README should be readable in 60 seconds. 1-sentence pitch, 1-command install, 1-command run, 1-command eval.

---

## The 5 most common take-home prompts (by company)

These 5 prompts appear in at least 3 of the major FDE take-homes. Practice each one.

### Prompt 1: "Build a semantic search system over [data]"

**Source:** OpenAI FDE take-home (the canonical prompt), Anthropic FDE take-home, LangChain take-home.

**What the customer actually wants:** a deployed, working search system that returns relevant results for natural-language queries.

**The minimum viable artifact:**

1. A simple RAG pipeline (chunk → embed → store → retrieve → generate)
2. 50-100 docs in the test set
3. A `/search` endpoint that returns the top-5 chunks
4. An eval set of 20-30 queries with hand-labeled ground truth
5. A `/metrics` endpoint with latency, error rate, cost

**The 3 over-engineering traps:**

1. **Adding auth/SSO** — not needed for a take-home. Cut.
2. **Adding a fancy UI** — a curl command is fine. Cut.
3. **Fine-tuning the embedding model** — the default OpenAI embedding is fine. Cut.

### Prompt 2: "Build a customer-support agent for [company]"

**Source:** Sierra AI, LangChain, OpenAI, Anthropic.

**What the customer actually wants:** a working agent that can handle 80% of customer queries without human intervention.

**The minimum viable artifact:**

1. A LangGraph / hand-rolled orchestrator
2. 3-5 tools (lookup, refund, escalate, recommend)
3. A 20-30 customer query eval set with hand-labeled ground truth
4. An eval harness that measures: tool selection accuracy, response faithfulness, hallucination rate
5. A `/chat` endpoint + a Gradio UI

**The 3 over-engineering traps:**

1. **Adding 20 tools** — 3-5 is enough. Cut the rest.
2. **Building a multi-agent orchestrator** — a single agent with 3-5 tools is fine for a take-home. Cut.
3. **Adding auth/SSO** — not needed. Cut.

### Prompt 3: "Build a knowledge worker that answers questions about [company]"

**Source:** Ed Donner's RAG project, Anthropic, Sierra AI, LangChain.

**What the customer actually wants:** a Q&A system that answers questions about the company's documents.

**The minimum viable artifact:**

1. A RAG pipeline (chunk → embed → store → retrieve → generate)
2. 50-100 company docs
3. An eval set of 20-30 questions with hand-labeled ground truth
4. An eval harness that measures: faithfulness, ansrel, context_precision, context_recall
5. A `/ask` endpoint + a Gradio UI

**The 3 over-engineering traps:**

1. **Adding advanced RAG techniques** (re-ranking, query rewriting, GraphRAG) — the basic RAG is fine. Cut.
2. **Adding multi-tenancy** — not needed. Cut.
3. **Adding a custom embedding model** — the default is fine. Cut.

### Prompt 4: "Build a Python → C++ converter with cost-quality comparison"

**Source:** Ed Donner's Python → C++ project, Anthropic, OpenAI.

**What the customer actually wants:** a tool that takes Python code and returns optimized C++ code, with a cost-quality comparison across 4 frontier models.

**The minimum viable artifact:**

1. A CLI that takes a Python file + a model name, returns the C++ output
2. A test set of 5-10 Python functions with expected C++ outputs
3. A cost-quality-latency table across 4 models
4. A recommendation engine ("use model X because Y")
5. A README that explains the trade-offs

**The 3 over-engineering traps:**

1. **Adding a Gradio UI** — a CLI is fine. Cut.
2. **Adding 10 models** — 4 is enough. Cut the rest.
3. **Adding Rust as a third language** — stretch goal. Cut for the take-home.

### Prompt 5: "Build a price-prediction system for [product]"

**Source:** Ed Donner's Capstone A, Anthropic, OpenAI.

**What the customer actually wants:** a system that predicts product prices from short descriptions, with a cost-quality comparison across frontier models.

**The minimum viable artifact:**

1. A RAG-augmented LLM pipeline (description → similar products → price)
2. A test set of 20-30 products with known prices
3. A cost-quality-latency table across 4 models
4. An error distribution analysis (where does the model fail?)
5. A recommendation engine ("use model X because Y")

**The 3 over-engineering traps:**

1. **Adding 10 models** — 4 is enough. Cut.
2. **Adding a custom UI** — a CLI is fine. Cut.
3. **Adding an LLM-as-judge eval** — a simple MAE is fine. Cut.

---

## The 5 take-home anti-patterns (the disqualifiers)

These 5 anti-patterns are instant-fail signals in every take-home. Memorize them.

1. **The README is wrong.** `pip install -r requirements.txt` fails. (Correctness anti-pattern)
2. **The artifact has no eval set.** The candidate ships a system that might be hallucinating. (Observability anti-pattern)
3. **The artifact has no cost tracking.** The candidate uses the API but doesn't know how much it costs. (Cost anti-pattern)
4. **The artifact has no circuit breaker.** When the API is down, the artifact crashes. (Cost anti-pattern)
5. **The artifact has no runbook.** The candidate ships code, not a service. (Handoff anti-pattern)

**The pattern:** every anti-pattern is a missing FDE layer. The take-home is graded on the 4 criteria; the candidate who omits any one of them fails.

---

## The 5-question "what would the candidate do differently" recap

1. **Scope before committing.** Spend 1 hour on scope, not 5 hours on code. Lock the "wow" moment.
2. **Add the 4 criteria, not 40 features.** Correctness + Observability + Cost + Handoff. Not auth + UI + multi-tenancy + 10 tools.
3. **Ship a 70% solution with a great README.** A well-documented 70% beats an undocumented 100%.
4. **Test on the interviewer's machine.** Run `git clone` → `pip install` → `python main.py` from scratch. Time it.
5. **Document the handoff.** A 1-page HANDOFF.md with: open issues, known limitations, next steps.

**The signal:** the candidate who can do all 5 in a 4-hour take-home is signaling they can do the FDE job. The candidate who can do 3 of 5 is signaling they need coaching. The candidate who can do 1 of 5 is signaling they're not ready.

---

## The cross-reference: how this maps to the 6 FDE company loops

| Company | Take-home length | Cross-reference |
|---|---|---|
| **LangChain** | 1 week (no time limit on prep, 20-min presentation) | `../company-experiences/langchain-deployed-engineer.md` § 2 + 3 |
| **Sierra AI** | 1 week + 60-min demo + customer simulation | `../company-experiences/sierra-ai-agent-engineer.md` § 2 + 3 + 4 |
| **OpenAI** | 1 week + 60-min team discussion + AI-enabled LeetCode | `../company-experiences/openai-semantic-search.md` § 2 + 3 |
| **Anthropic** | 1 week + 60-min system design + customer simulation | `../company-experiences/anthropic-fde-customer-simulation.md` § 3 |
| **AWS FDE** | 4-8 hours + 60-min coding + 60-min system design + 60-min customer scenario | `../company-experiences/aws-fde-customer-simulation.md` § 3 |
| **Palantir** | No take-home (decomposition round instead) | `../company-experiences/palantir-fde-decomposition.md` § 2 |

---

## The thesis

**The take-home is the FDE job in miniature.** A 4-8 hr take-home is a 4-8 hr FDE engagement. The 4-criteria rubric (correctness / observability / cost / handoff) is the rubric every take-home is graded on. The 5 prompts (semantic search / customer support / knowledge worker / Python-to-C++ / price prediction) are the most common take-home scenarios.

**The candidate who can ship a 70% solution with a great README, an eval set, a cost tracker, a circuit breaker, and a runbook is signaling they can do the FDE job.** All other signals are noise.

**General prep gets you past the resume screen. Take-home prep gets you past the centerpiece round at LangChain / Sierra AI / OpenAI / Anthropic / AWS FDE.**
