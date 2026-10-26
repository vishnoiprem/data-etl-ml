# Lesson 9.6: Production Agent Patterns

> **Observability, debugging, cost control, safety, guardrails. A production agent with safety.**
> 20 min. Code: Production agent with guardrails + cost control.

## 🎯 Architect Level

- [ ] 🟢 **Junior (1-2 yrs)** — implement and run
- [ ] 🟡 **Mid (3-5 yrs)** — extend with monitoring
- [ ] 🟠 **Senior (6-10 yrs)** — add multi-tenancy
- [ ] 🔴 **Staff (10+ yrs)** — design the SLA, capacity model, incident playbook

> *Picking the right level is a one-time decision per lab. Pick the highest level you can honestly complete. Move up next time.*

---

## 🧠 Concept (5 min)

A prototype agent that runs in a notebook is not a production agent. The five properties a shipping agent must satisfy, each enforced in code rather than prompted: **(1) observability** — every step is a structured log row (turn, event, tool, args, result, cost, tokens); the audit log is the artifact the on-call reads at 3am. LangSmith, Helicone, and OpenLLMetry are the standard instrumentations. **(2) cost control** — hard caps on turns, tokens, and USD per run; the agent aborts on the first breach, not on the average. **(3) safety** — forbidden tools are blocked at the registry, returning a structured 403, not a soft prompt-level "please don't." NeMo Guardrails, Guardrails AI, or a custom policy file. **(4) determinism** — temperature=0, fixed seeds, structured outputs, where the task allows. **(5) error recovery** — retries with exponential backoff for transient failures; a loop detector that aborts on N identical tool calls in a row and surfaces the question to the user. **Architect rule:** no agent ships without `MAX_TURNS` and `MAX_COST_USD`. The default behavior of a confused agent is to spend the entire budget; the guardrails are the only thing that prevents that.

---

## 🛠️ Build It (45 min)

### Spec

Build a production-grade agent with the five guardrails wired in: (1) `MAX_TURNS=10`, `MAX_TOKENS=50_000`, `MAX_COST_USD=$0.50` — enforced at the orchestrator, not the LLM; (2) `FORBIDDEN_TOOLS = {delete_user, wipe_database, send_to_all_customers, export_pii}` — registry-enforced, returns a structured `403`; (3) a `CostTracker` that meters input/output tokens and the running USD total; (4) a `StepLog` audit row per step, emitted as a dataclass; (5) a loop detector that aborts when the same tool fires 3 times in a row. Mock the LLM and the tools. Demo: three scenarios — (a) normal task terminates cleanly, (b) a forbidden tool is blocked and the agent recovers on a safe tool, (c) the loop detector trips on 3 identical tool calls.

### Acceptance Criteria

**Functional:**
- [ ] Program runs without errors (mocked APIs so no key required)
- [ ] All TODO functions have a working implementation
- [ ] Demo function exercises the full flow
- [ ] At least one structured output (dict, dataclass, or Pydantic model)

**Quality:**
- [ ] All functions have docstrings
- [ ] Code is readable in <5 minutes
- [ ] No magic numbers — use named constants
- [ ] Type hints on all public functions

**Observability (Mid+):**
- [ ] Logs every significant operation
- [ ] Tracks token usage and cost where applicable
- [ ] For Senior+: handles concurrency / multi-tenant isolation

### Starter Code

Open `lesson-9-6-production-agents.py` in the same folder. It has a `TODO` per step.

### Solution

The same `.py` file has the complete solution after the `# === SOLUTION ===` divider. Run the file; the starter section runs first and demonstrates the concept, then the solution section shows a production-grade version.

---

## 🏛️ Architect Notes

### Trade-offs

| Choice | Pros | Cons | Pick when |
|---|---|---|---|
| Mock everything (this lab) | Runs anywhere, no API key, no cost | Doesn't catch real-API issues | Learning, CI, demos |
| Real API (gpt-4o-mini) | Real quality, real latency, real cost | Needs key, costs money, flakes in CI | Final integration testing |
| Hybrid (mock + real) | Best of both — fast iteration, real validation | More code to maintain | Production codebases |
| Snapshot tests (vcr.py) | Deterministic, replay real API responses | Stale recordings | CI for LLM apps |

**Architect insight:** The mock-first approach lets you iterate 10x faster in the design phase. Move to real API only when the design is stable.

### Capacity Model

| Volume | Latency p50 | Latency p99 | Cost/day | Notes |
|---|---|---|---|---|
| 1 req | <100ms | <500ms | $0 | Single-threaded mock |
| 100 req/min | <200ms | <1s | ~$0.10 | Async I/O, in-memory state |
| 10K req/min | <500ms | <3s | ~$10 | Connection pool, rate limiting |
| 100K req/min | <1s | <5s | ~$100 | Distributed, queue, monitoring |

**Rule of thumb:** Mock-based systems are CPU-bound; real LLM calls are network-bound. Plan for the network bound case from day one.

### Cost Model (per 1M tokens, 2026)

| Model | Input ($/1M tokens) | Output ($/1M tokens) |
|---|---|---|
| GPT-4o | $5.00 | $15.00 |
| GPT-4o-mini | $0.15 | $0.60 |
| Claude 3.5 Sonnet | $3.00 | $15.00 |
| Claude 3.5 Haiku | $0.80 | $4.00 |
| Gemini 1.5 Pro | $1.25 | $5.00 |
| Gemini 1.5 Flash | $0.075 | $0.30 |
| Llama 3 70B (self-hosted) | $0.10 | $0.10 |

### When NOT to use this lab's content

**Don't ship a mock to production.** The mock is for learning. The patterns and architecture translate, but the actual LLM calls need real keys, real rate limits, real error handling.

**Don't over-engineer the abstraction.** A wrapper class is good. Five levels of inheritance is bad. Start simple.

**Don't skip observability.** Even in a lab, log every step. The habit matters.

### Production Checklist

- [ ] All LLM calls wrapped with retry + timeout
- [ ] Token usage and cost logged on every call
- [ ] Errors categorized (transient, permanent, degraded)
- [ ] Rate limits respected (per-user and per-org)
- [ ] PII handling: never log user data
- [ ] Observability: traces, metrics, logs all flowing
- [ ] Tests: unit, integration, and eval suite
- [ ] Cost dashboard updated daily

---

## 🏗️ FDE Production Hardening (the patterns beyond this lab)

The lab above covers the 5 guardrails every prototype needs. A **Forward Deployed Engineer** adds 5 more on top — the patterns that make the agent survive the customer's first quarter in production:

1. **The cost ceiling as a score, not a number.** Tie `MAX_COST_USD` to the customer's LLM line item in their monthly budget, not to a per-task limit. Mei's $0.50/week is `MAX_COST_USD` divided by the expected throughput. The dashboard shows "agent spend / LLM budget" as a single ratio; the circuit breaker trips at 80% to give the customer 20% headroom.

2. **The circuit breaker, not just a max-turns counter.** A confused agent that hits `MAX_TURNS` is a *symptom*. The breaker watches the failure rate across many concurrent runs: if > 5% of runs in the last 5 minutes hit `MAX_TURNS` or the loop detector, the breaker opens and the agent returns a fallback response ("I'm having trouble; a human will follow up") instead of spending the whole budget on retries.

3. **Per-tenant rate limits, not a global one.** The `MAX_COST_USD` should be per `user_id`, not per process. A noisy customer who triggers 5 loops in a minute shouldn't be able to spend another customer's budget. Production: a token bucket per `(user_id, tool_name)` pair; the policy file (lesson 9.1) is the manifest.

4. **The audit log is the artifact.** Every `StepLog` row in the lab demo is a real row in `usage.jsonl` in production. The customer reads it on a Monday morning to see what their agent did over the weekend. The FDE hands the customer a Grafana dashboard pointed at this log on day 1, not day 30.

5. **The "FDE has left" test.** Before exiting, the FDE asks 5 questions of the customer's team: (1) "Show me the last agent run that hit `MAX_TURNS`." (2) "Show me the last guardrail block." (3) "What happens when the cost ceiling is breached at 3am?" (4) "Who gets paged when the breaker opens?" (5) "Show me the eval set the agent must pass before each deploy." 5/5 must be answerable from the dashboard + runbook without the FDE.

**The pattern:** the lab teaches the 5 in-process guardrails. The FDE adds the 5 cross-process guardrails (cost ceiling as score, circuit breaker, per-tenant limits, audit log, "FDE has left" test). The 5 + 5 = the 10 things every production agent needs.

---

## 🌙 Reflect (10 min)

Answer these in your own notes (or a comment at the bottom of the `.py` file):

1. **What did I build?**
   Production Agent Patterns. What did you learn that you didn't expect?

2. **What was hard?**
   Was it the API design? The cost math? The trade-off thinking?

3. **What would I change at 10× scale?**
   If this code had to handle 10x the load or 10x the users, what would break first?

4. **What's tomorrow's lab?**
   Lesson 10.1: Fine-Tuning vs RAG vs Prompting.

---

## References

- [`openai` Python SDK](https://github.com/openai/openai-python) — the OpenAI client library
- [`anthropic` Python SDK](https://github.com/anthropics/anthropic-sdk-python) — the Anthropic client library
- [`pydantic` v2 docs](https://docs.pydantic.dev/) — data validation
- [`tenacity` docs](https://tenacity.readthedocs.io/) — retries
- [Codebook § 5.0](../../workbooks/ai-engineer-codebook.md) — the chapter for this level
- [Paired codebook exercises](../../workbooks/exercises/) — extend what you learned here
- [Capstone starter](../../capstone-starters/) — relevant starter code

### Reference implementation

- [`../../hardcode/level-5-agentic-workflows/10-multi-agent-orchestrator.py`](../../hardcode/level-5-agentic-workflows/10-multi-agent-orchestrator.py) — production-grade multi-agent with approval checkpoints, per-run timeouts, and the full execution trace pattern that backs the observability section above. The HITL checkpoint in the reviewer agent is the same pattern as `interrupt_before=[...]` in LangGraph.
