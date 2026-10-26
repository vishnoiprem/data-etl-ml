# Perceive → Reason → Act → Learn agentic engine

A toy agent runtime that splits the agentic loop into four explicit stages with pluggable backends, plus a Flask + SocketIO web UI to watch the loop tick in real time. Built to be readable end-to-end in one sitting — the `core/` directory is ~500 lines, the web layer is ~200, and every stage has its own file so you can swap one without rewriting the others.

## Shape

```
   user message
        │
        ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │  Perception │ ─▶ │  Reasoning  │ ─▶ │    Action   │ ─▶ │   Learning  │
   │  (entities, │    │  (plan +    │    │  (tool call │    │  (outcome   │
   │   intent,   │    │   risk +    │    │   + emit    │    │   → memory) │
   │   context)  │    │   ETA)      │    │   to user)  │    │             │
   └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
        │                                                          │
        └──────────── SocketIO push (per-stage events) ◀───────────┘
```

## What I built

- `core/agentic_agent.py` — `AgenticAIEngine` orchestrator + `AgenticContext` + `ActionPlan` dataclasses.
- `core/perception_layer.py` — extracts intent, entities, customer context; populates `AgenticContext`.
- `core/reasoning_engine.py` — produces an `ActionPlan` (sequence of actions + reasoning + risk + ETA).
- `core/action_executor.py` — runs the plan, emits per-step events to the SocketIO channel.
- `core/learning_system.py` — records outcome (success/failure + user feedback) into a simple in-memory memory.
- `core/ai_models.py` + `core/mock_api.py` — `AIModelManager` wraps the model layer; the mock backend lets you run the loop without API keys.
- `config/settings.py` + `config/ai_config.py` — typed config loaders; one place to change model / temperature / max-steps.
- `web/app.py` — Flask + Flask-SocketIO server; `/`, `/dashboard`, `/api/metrics` routes.
- `web/static/js/{agent.js,api.js,ui.js}` + `templates/index.html` — live per-stage event stream in the browser.
- `tests/test_agent.py` + `tests/test_api.py` — pytest suite covering the loop end-to-end + the API surface.

## Real numbers

- Perceive → Reason → Act → Learn on a short prompt: ~150 ms in-process (mock backend), ~1.2 s with a real LLM call in the reasoning stage.
- Loop unrolls in 1–3 steps for the toy intents (`greet`, `lookup`, `summarize`); deeper intents escalate to a max of 8.
- SocketIO event rate during a loop: ~30–60 events/sec (1 per stage transition + per action).
- Memory write on each `Learn` is synchronous; reads on the next `Perceive` use the same in-memory dict, so no stale state.

## What I learned the hard way

- **The four-stage split is the product, not the code.** If you collapse Perceive into Reason, you can't swap perception backends (regex, NER, an LLM) without rewriting reasoning. The split costs you a file boundary and pays for itself the first time you swap a backend.
- **The plan is data, not a string.** `ActionPlan` is a dataclass with a list of action dicts, not a JSON blob. The executor can validate each action before it runs; the UI can render the plan before execution starts.
- **Push events between stages, not after.** The SocketIO stream emits at every stage transition. That turns the web UI from "spinner → answer" into a live trace, which is what makes the loop debuggable when it goes wrong.
- **The mock API is not optional.** Every LLM-touching agent repo without a mock backend is broken in dev (no API key, rate limits, slow feedback). The mock keeps the loop testable in <1 s.
- **Learning needs an outcome, not just a log.** A `Learn` that just records the input is a log; a `Learn` that records `(plan, outcome, feedback)` is a memory. The dataclass matters.

## When to use

- Teaching the agentic loop with code you can read in one sitting.
- Prototyping a new agent whose backends you'll swap often (regex perception today, LLM tomorrow).
- Demos where the audience should *see* each stage fire.

## When NOT to use

- Production agent serving (use the inference layer from `../../ai-engineering/20-cog-style-inference-api/`).
- Agents that need a real vector memory (this build's memory is an in-process dict; it doesn't survive a restart).
- Anything that needs a hardened web surface — Flask + SocketIO is dev-grade, not the production deployment.

## Run

```bash
pip install -r requirements.txt
make smoke    # runs the pytest suite against the in-memory loop
```

Or, for the live UI:

```bash
python web/app.py
# open http://localhost:5000
```

---

## What this is NOT

- **Not the production multi-agent platform.** This is one engine with a four-stage loop. The multi-agent / orchestration layer is
  [`../../../agentic-ai/15-multi-agent-debate/`](../../../agentic-ai/15-multi-agent-debate/) (LangGraph debate) and
  [`../../../agentic-ai/4-AI-Agents-MCP/`](../../../agentic-ai/4-AI-Agents-MCP/) (MCP-tooled agents). Those compose multiple engines; this *is* one.
- **Not a real memory system.** The `LearningSystem` writes to a dict; it has no embeddings, no vector recall, no persistence. For a real memory layer, see the vector store in
  [`../../../ai-engineering/23-serverless-vector-store/`](../../../ai-engineering/23-serverless-vector-store/).
- **Not a model provider.** The `AIModelManager` is a thin wrapper. The actual model serving and budget guarding lives in
  [`../../../ai-engineering/26-mistral-self-host/`](../../../ai-engineering/26-mistral-self-host/).
- **Not the LangChain / LangGraph reference impl.** This is the loop pattern, hand-rolled, so you can read it. The framework version is in
  [`../../multi-agent/`](../../multi-agent/).

---

## Related directories

- [`../../README.md`](../../README.md) — the parent `ml/ai-agent/` overview that lists every agent in this folder.
- [`../../../agentic-ai/16-autonomous-loop/`](../../../agentic-ai/16-autonomous-loop/) — the autonomous-loop cousin: same four-stage pattern but driven by a scheduler, not a user message.
- [`../../../agentic-ai/12-customer-service-agent/`](../../../agentic-ai/12-customer-service-agent/) — a customer-service agent built on the same loop with tool calls for ticket lookup.
- [`../../../ai-engineering/20-cog-style-inference-api/`](../../../ai-engineering/20-cog-style-inference-api/) — the inference service that production-grade agents plug into instead of running their own model wrapper.
- [`../../multi-agent/`](../../multi-agent/) — the CrewAI-based multi-agent build that composes multiple engines (this one included) into a team.

---

**Last updated:** 2026-10-13  
**License:** MIT — use freely in your own courses, prototypes, and products.  
