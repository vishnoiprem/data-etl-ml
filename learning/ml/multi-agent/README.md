# Multi-Agent Travel Assistant (CrewAI + Delta Lake)

> **A single-file CrewAI build that turns a natural-language
> travel request into a flight research → booking →
> confirmation flow.** Three agents (Researcher, Booker,
> Notifier) coordinate through CrewAI's task chaining; the
> tool calls land in a Spark + Delta Lake sink for the
> downstream analytics team.

The whole thing fits in `multi_agent_travel.py` (~200
lines) — that's the point. The interesting design
questions are:

- How does CrewAI route context between agents?
- How do you swap the LLM provider (OpenAI ↔ local
  Ollama) without rewriting the agent logic?
- Where do agent outputs land so they're queryable
  later?

The build is intentionally small. The production-shaped
cousin with retries, cost controls, and shared memory
lives in
[`../../ai-engineering/03-multi-agent-platform/`](../../ai-engineering/03-multi-agent-platform/).

---

## What it does

```
   User: "Find me a flight from NYC to LHR under $500"
        │
        ▼
   ┌──────────────────────────────────────────────┐
   │  Researcher agent                             │
   │  - role: Flight Researcher                    │
   │  - tool: DummyTravelAPI.search_flights        │
   │  - writes flight options to Delta Lake        │
   └─────────────────────┬────────────────────────┘
                         │  (context passed by CrewAI)
                         ▼
   ┌──────────────────────────────────────────────┐
   │  Booker agent                                 │
   │  - role: Travel Booker                        │
   │  - tool: DummyTravelAPI.book_flight           │
   │  - writes booking confirmation to Delta Lake  │
   └─────────────────────┬────────────────────────┘
                         │
                         ▼
   ┌──────────────────────────────────────────────┐
   │  Notifier agent                               │
   │  - role: Customer Notifier                    │
   │  - tool: DummyTravelAPI.send_email            │
   │  - sends confirmation to customer             │
   └──────────────────────────────────────────────┘
```

Three agents, one direction, one output per step. The
"magic" is CrewAI's task chaining — each task's output
becomes the next task's context without any explicit
plumbing.

---

## The pieces

### The three agents

| Agent | Role | Tool |
|-------|------|------|
| `researcher` | Flight Researcher — finds the best flight deals | `DummyTravelAPI.search_flights` |
| `booker` | Travel Booker — securely books the chosen flight | `DummyTravelAPI.book_flight` |
| `notifier` | Customer Notifier — sends the confirmation email | `DummyTravelAPI.send_email` |

Each agent is a `crewai.Agent` with a `role`, `goal`,
`backstory`, and `verbose=True` for the demo. The
*backstory* matters: it's what the model uses to scope
its behavior. A vague backstory produces vague output;
a specific one (e.g. "Specialist in handling
reservations for seamless travel") is what makes the
agent stay in its lane.

### The three tools (`DummyTravelAPI`)

A static-method class that mocks a real travel API.
Three endpoints, all writing to Delta Lake:

| Method | What it does | Delta Lake sink |
|--------|--------------|-----------------|
| `search_flights(origin, destination, budget, date)` | Returns 2 mock flights (Delta, United) | `s3://lakehouse/songkran_flights` |
| `book_flight(flight)` | Returns a confirmation number | `s3://lakehouse/songkran_bookings` |
| `send_email(email, message)` | "Sends" the confirmation (mock) | (no sink — fire-and-forget) |

The Delta Lake sinks are the interesting bit. The
agent's tool calls double as an event log: every
search, every booking, every notification is
queryable downstream by the analytics team.

### The Spark session

```python
spark = SparkSession.builder.appName("SongkranTravelETL").getOrCreate()
```

One Spark session, shared across all tool calls. In a
Databricks deployment this is auto-provided; locally
you'd need `pyspark` installed and a Delta Lake runtime
(`delta-spark`).

### The LLM provider

The README mentions "Works with both OpenAI API and
local Ollama models." The actual provider is picked by
CrewAI's `LLM` config — typically:

```python
# OpenAI
import os
os.environ["OPENAI_API_KEY"] = "..."

# Or local Ollama
# (set OLLAMA_HOST and use ollama/llama3 as the model)
```

The same agent code runs against either. The model
abstraction is what makes this swappable.

---

## How to run it

```bash
cd ml/multi-agent
python -m venv .venv && source .venv/bin/activate
pip install crewai pyspark delta-spark python-dotenv

# Set up auth
echo "OPENAI_API_KEY=sk-..." > .env
# or
echo "OLLAMA_HOST=http://localhost:11434" >> .env

# Run the demo
python multi_agent_travel.py
```

The script runs end-to-end: researcher finds flights,
booker books one, notifier sends the confirmation.
With `verbose=True` you see the agent's reasoning
between tool calls.

---

## What this is NOT

- **Not a real travel agent.** The `DummyTravelAPI` is
  hardcoded mock data (Delta + United, $450 + $420).
  No real flight search, no real booking, no real
  email. It's a *demo of the multi-agent pattern*,
  not a product.
- **Not production-shaped.** There's no retry on
  tool failure, no budget cap on the LLM calls, no
  per-tenant isolation, no audit log of the agent's
  decisions. The pattern is right; the engineering
  isn't. For production, see
  [`../../ai-engineering/03-multi-agent-platform/`](../../ai-engineering/03-multi-agent-platform/).
- **Not the only multi-agent pattern.** CrewAI's
  task-chaining is one shape. The other patterns in
  this repo:
  - **Synapse** ([`../../agentic-ai/ai-agent/`](../../agentic-ai/ai-agent/)) —
    3 agents (Scout → Contextualist → Publisher) with
    MCP servers and an A2A bus.
  - **Debate** ([`../../agentic-ai/15-multi-agent-debate/`](../../agentic-ai/15-multi-agent-debate/)) —
    two agents argue, a verifier picks.
  - **Autonomous loop** ([`../../agentic-ai/16-autonomous-loop/`](../../agentic-ai/16-autonomous-loop/)) —
    bounded loop with a budget and a retry policy.
- **Not a Spark/Databricks tutorial.** The Spark +
  Delta Lake integration is the *output sink* for the
  agent's tool calls. The Spark patterns themselves
  live in
  [`../../data-engineering/activity-volume-olap/`](../../data-engineering/activity-volume-olap/).

---

## The 5 things this directory teaches

1. **Three agents with three roles is enough to see
   the pattern.** Researcher / Booker / Notifier is
   the smallest multi-agent build that exercises
   CrewAI's task chaining.
2. **Backstories are behavior prompts.** A specific
   backstory ("Specialist in handling reservations for
   seamless travel") is what keeps the agent in its
   lane. Vague backstories produce vague output.
3. **Tool outputs can be data events.** Writing every
   search/booking/notification to Delta Lake turns the
   agent's tool calls into a queryable log for the
   analytics team. Same pattern as the
   `event-sourced-audit/` build in
   [`../../data-engineering/event-sourced-audit/`](../../data-engineering/event-sourced-audit/).
4. **LLM providers are swappable.** The same agent
   code runs against OpenAI or local Ollama. The
   abstraction is what makes this work; pick the
   provider that matches your cost / privacy /
   latency budget.
5. **One file is the right size for a demo.** ~200
   lines is enough to demonstrate the whole
   pattern. Production builds are 10–100x this size,
   but the *shape* doesn't change.

---

## Related directories

- [`../ai-engineering/03-multi-agent-platform/`](../../ai-engineering/03-multi-agent-platform/) —
  the production-shaped multi-agent platform (LangGraph
  orchestrator, Bedrock, shared memory store).
- [`../../agentic-ai/ai-agent/`](../../agentic-ai/ai-agent/) —
  Synapse: a working multi-agent system with 4 MCP
  servers and an A2A bus.
- [`../../agentic-ai/15-multi-agent-debate/`](../../agentic-ai/15-multi-agent-debate/) —
  the debate pattern (two agents argue, verifier picks).
- [`../../data-engineering/activity-volume-olap/`](../../data-engineering/activity-volume-olap/) —
  the OLAP-on-clickstream pattern that the Delta Lake
  sink is a stripped-down version of.
- [`../ai-agent/`](../ai-agent/) — the per-agent
  reference (six domain agents, `AgenticTool` base
  class).
