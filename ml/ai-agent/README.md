# AI Agent System — reference architecture & working examples

> **A learning repo that explores the agent-system
> design space: tool integrations, domain-specific
> agents, and a more complete `AdvancedAgenticSystem`
> build.** Six domain agents (Customer Service, HR
> Onboarding, Healthcare, Marketing, Developer, Travel),
> a base `AgenticTool` class with Slack/Email/Database
> examples, and a 600-line `AdvancedAgenticSystem` that
> wires them all together.

This directory is the *reference* — the place where the
agent patterns (tool integration, perception →
reasoning → action loop, multi-model routing) are
written down in code, even if the implementations are
intentionally small. The production-shaped builds live
in [`../ai-engineering/03-multi-agent-platform/`](../ai-engineering/03-multi-agent-platform/)
and the `agentic-ai/` projects.

---

## What's in this directory

| Path | What it is |
|------|------------|
| `AgenticTool.py` | The `AgenticTool` base class + Slack / Email / Database / API integrations (185 lines) |
| `CustomerServiceAgent.py` | A domain agent for customer-service inquiries (42 lines) |
| `DeveloperAgent.py` | A domain agent for code questions (40 lines) |
| `HROnboardingAgent.py` | A domain agent for HR / onboarding flows (38 lines) |
| `HealthcareAssistant.py` | A domain agent for healthcare Q&A (45 lines) |
| `MarketingAgent.py` | A domain agent for marketing copy (40 lines) |
| `Travel-Planner-Agent/` | Standalone travel-planner agent build |
| `core/` | The (stub) core engine: perception, reasoning, action executor, learning system |
| `agents/` | The (stub) agent implementations mirroring the top-level files |
| `api/` | The (stub) external API integrations: data sources, external APIs, mock services |
| `web/` | The (stub) FastAPI web interface |
| `AdvancedAgenticSystem/` | **The real build** — a working 600-line agent with perception/reasoning/action + mock API |
| `requirements.txt` | The dependency manifest |

The split is intentional. The **top-level files** are
small, single-purpose examples (one agent per file,
~40 lines each). The **`AdvancedAgenticSystem/`
subdirectory** is the more complete build that
exercises the full loop.

---

## The shape (AdvancedAgenticSystem)

```
   ┌─────────────────────────────────────────────┐
   │  web/  (FastAPI app)                         │
   │  POST /agent/chat  → runs the agent          │
   │  GET  /agent/state → returns current state   │
   └─────────────────────────┬───────────────────┘
                             │
                             ▼
   ┌─────────────────────────────────────────────┐
   │  core/agentic_agent.py  (the orchestrator)   │
   │  perception → reasoning → action loop        │
   │  state held in core/state.py                 │
   └──────────┬─────────────────────┬─────────────┘
              │                     │
              ▼                     ▼
   ┌──────────────────────┐  ┌─────────────────────┐
   │  core/ai_models.py   │  │  core/mock_api.py   │
   │  (model router:      │  │  (mock external     │
   │   OpenAI/Claude/     │  │   tools / APIs)     │
   │   Gemini)            │  │                     │
   └──────────────────────┘  └─────────────────────┘
```

The agent's loop is the standard
**perception → reasoning → action** pattern:

1. **Perception** — parse the user input into a
   structured intent.
2. **Reasoning** — pick the next action (call a tool,
   ask for clarification, or answer directly).
3. **Action** — invoke the chosen tool or model,
   update state, return the response.

`mock_api.py` is the testbed — it provides the tool
implementations (calendar, search, etc.) so the agent
can run end-to-end without external services.

---

## The six domain agents (top-level)

Each top-level `.py` file is a single-purpose agent
built on the same pattern: a system prompt, a model
binding, and a list of allowed tools.

| Agent | Tools | Use case |
|-------|-------|----------|
| `CustomerServiceAgent` | Ticket lookup, KB search, refund API | Tier-1 support deflection |
| `DeveloperAgent` | Code search, file read, shell | Engineer Q&A |
| `HROnboardingAgent` | Calendar, document templates, provisioning | New-hire workflow |
| `HealthcareAssistant` | Symptom lookup, appointment booking | Triage pre-screen |
| `MarketingAgent` | Asset library, brand guidelines, copy tools | Campaign drafting |
| `TravelPlannerAgent` | Flight search, hotel search, itinerary | Trip planning |

They're intentionally short (~40 lines each). The
*interesting* design questions — what tools to expose,
how the agent decides between them, how to scope each
agent's authority — are the same questions at any
scale; the small files make the patterns legible.

---

## How to run the AdvancedAgenticSystem

```bash
cd ml/ai-agent/AdvancedAgenticSystem
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start the agent
uvicorn web.app:app --reload --port 8000

# In another terminal, chat
curl -X POST http://localhost:8000/agent/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "What meetings do I have tomorrow?"}'
```

The mock API will respond with synthetic data; the
real shape of the response matches what a production
build would return.

---

## How to run the top-level agents

Each top-level file is a standalone example. Pick one:

```bash
cd ml/ai-agent
python CustomerServiceAgent.py
# -> prints a sample customer-service conversation
```

These are *not* deployable; they illustrate the
per-agent code shape.

---

## What this is NOT

- **Not production-ready.** The `core/` and `agents/`
  subdirectories are stubs (`__init__.py` only). The
  top-level agent files are illustrative skeletons.
  The `AdvancedAgenticSystem/` is the one build in
  this directory that runs end-to-end, and even that
  uses a `mock_api.py` for tools.
- **Not a complete agent framework.** The
  `AgenticTool` base class is a small, opinionated
  example — it shows the *pattern* (named tool,
  description, async `execute(action, params)`), not
  a production framework. For frameworks, see
  [Agno](https://github.com/agno-agi/agno) (the
  library this code uses), LangChain, or LangGraph.
- **Not a multi-agent system.** The six domain
  agents are independent examples. There's no
  orchestrator that routes between them, no shared
  memory, no agent-to-agent messaging. For
  multi-agent patterns, see the `agentic-ai/`
  directory.

---

## The 5 things this directory teaches

1. **Tools are a class.** The `AgenticTool` pattern
   (name + description + async `execute(action, params)`)
   is the smallest possible tool abstraction. Once
   you have it, the model does the routing.
2. **One agent per domain.** Each of the six top-level
   files is one agent with one job. The system prompt
   scopes the agent; the tools scope its authority.
3. **The perceive-reason-act loop is the agent.** The
   `AdvancedAgenticSystem/core/agentic_agent.py`
   file is the orchestrator; everything else is
   implementation. The loop is the same at any
   complexity.
4. **Mock APIs are a forcing function for tool
   design.** Writing the mock first (`mock_api.py`)
   forces you to define the tool contract before the
   real implementation. It's the same trick the
   `AdvancedAgenticSystem` uses to be runnable
   without external services.
5. **Small examples beat large frameworks for
   learning.** 40 lines per agent, one file each, is
   enough to see the pattern. Production frameworks
   bury the same pattern under configuration.

---

## Related directories

- [`../ai-engineering/03-multi-agent-platform/`](../ai-engineering/03-multi-agent-platform/) —
  the production-shaped multi-agent platform (LangGraph,
  Bedrock, shared memory).
- [`../../agentic-ai/`](../../agentic-ai/) — 18
  production agents with A2A messaging, MCP servers,
  bounded loops, and debate patterns.
- [`../multi-agent/`](../multi-agent/) — the
  multi-agent reference (28L README, the next lift
  target).
- [`../../ai-engineering/04-fm-evaluation/`](../../ai-engineering/04-fm-evaluation/) —
  the eval framework you'd use to compare the six
  domain agents on the same task.
