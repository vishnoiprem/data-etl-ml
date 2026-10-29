# Lesson 3.4: ReAct Prompting

> **Reasoning + Acting. The agent loop. Build a ReAct agent from scratch.**
> 20 min. Code: ReAct agent loop + tool execution.

## 🎯 Architect Level

- [ ] 🟢 **Junior (1-2 yrs)** — implement and run
- [ ] 🟡 **Mid (3-5 yrs)** — extend with monitoring
- [ ] 🟠 **Senior (6-10 yrs)** — add multi-tenancy
- [ ] 🔴 **Staff (10+ yrs)** — design the SLA, capacity model, incident playbook

> *Picking the right level is a one-time decision per lab. Pick the highest level you can honestly complete. Move up next time.*

---

## 🧠 Concept (5 min)

ReAct (Reasoning + Acting) is the pattern behind every modern agent. The loop: (1) **Thought**: the model thinks about what to do next. (2) **Action**: it picks a tool and arguments. (3) **Observation**: the tool result comes back. (4) **Repeat** until the model decides to output a final answer. The prompt format is strict: `Thought: ...\nAction: tool_name(arg1=value1)\nObservation: ...` The model is trained on this pattern in the system prompt. The **architect decisions** are: how many turns before forcing a final answer (default 10), what to do if the model gets stuck in a loop (detect repetition, force a different action), how to handle tool errors (retry once, then escalate). ReAct is the foundation for LangChain agents, OpenAI Assistants, and Claude tool use.

---

## 🛠️ Build It (45 min)

### Spec

Build a ReAct agent from scratch: (1) define 3 tools (search, calculator, wikipedia), (2) parse the model's text output into (thought, action), (3) execute the action, (4) feed observation back, (5) loop until final answer. No frameworks, just the openai SDK and a loop.

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

Open `lesson-3-4-react.py` in the same folder. It has a `TODO` per step.

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

## 🌙 Reflect (10 min)

Answer these in your own notes (or a comment at the bottom of the `.py` file):

1. **What did I build?**
   ReAct Prompting. What did you learn that you didn't expect?

2. **What was hard?**
   Was it the API design? The cost math? The trade-off thinking?

3. **What would I change at 10× scale?**
   If this code had to handle 10x the load or 10x the users, what would break first?

4. **What's tomorrow's lab?**
   Lesson 3.5: System Prompts That Work.

---

## References

- [`openai` Python SDK](https://github.com/openai/openai-python) — the OpenAI client library
- [`anthropic` Python SDK](https://github.com/anthropics/anthropic-sdk-python) — the Anthropic client library
- [`pydantic` v2 docs](https://docs.pydantic.dev/) — data validation
- [`tenacity` docs](https://tenacity.readthedocs.io/) — retries
- [Codebook § 2.0](../../workbooks/ai-engineer-codebook.md) — the chapter for this level
- [Paired codebook exercises](../../workbooks/exercises/) — extend what you learned here
- [Capstone starter](../../capstone-starters/) — relevant starter code
