# Synapse — Daily Intelligence Brief (multi-agent system)

> **A small, complete multi-agent system that produces a daily
> intelligence brief.** Three agents (Scout → Contextualist →
> Publisher), four MCP servers (finance, media, weather,
> world_data), an in-process A2A messaging bus, and a Streamlit
> UI. Runs on a laptop, deployable as-is to a container.

This project is the reference for "show me a working
multi-agent system in 600 lines." The pattern is intentionally
small so the agent boundaries are the only thing you have to
read. Larger systems follow the same shape with a real
message bus (Kafka / NATS) and real transports (HTTP / gRPC).

---

## The shape

```
   ┌───────────────────────────────────────────────────────┐
   │  Streamlit UI (ui/app.py)                             │
   │  User clicks "Generate today's brief"                 │
   └──────────────────────────┬────────────────────────────┘
                              │
                              ▼  (in-process A2A bus)
   ┌───────────────────────────────────────────────────────┐
   │  Scout agent — finds today's signal sources            │
   │  - reads MCP servers: finance, media, weather, world   │
   │  - emits: List[Signal]                                 │
   └──────────────────────────┬────────────────────────────┘
                              │
                              ▼
   ┌───────────────────────────────────────────────────────┐
   │  Contextualist agent — explains what each signal       │
   │                       means in context                 │
   │  - inputs: List[Signal]                                │
   │  - emits: List[ContextualizedSignal]                   │
   └──────────────────────────┬────────────────────────────┘
                              │
                              ▼
   ┌───────────────────────────────────────────────────────┐
   │  Publisher agent — composes the daily brief           │
   │  - inputs: List[ContextualizedSignal]                 │
   │  - emits: Brief (Markdown, ready to send)             │
   └──────────────────────────┬────────────────────────────┘
                              │
                              ▼
   Streamlit renders the Markdown
```

Three agents, one direction, no back-edges. Each agent has
one job; the bus carries typed messages between them. The
Streamlit UI just kicks off the run and renders the output.

---

## The four MCP servers

| Server | What it exposes |
|--------|-----------------|
| `mcp-servers/finance/` | Stock prices, FX rates, market indices (via `yfinance`) |
| `mcp-servers/media/` | Trending topics, news headlines (via a small RSS aggregator) |
| `mcp-servers/weather/` | Current and forecast weather for a list of cities (via a public weather API) |
| `mcp-servers/world_data/` | Country / region metadata, holidays, public-holiday calendar |

Each server is a small Python module that exposes its tools
over MCP. The Scout agent binds to all four servers at
startup. The pattern is identical for any other server
you'd want — sports scores, GitHub activity, calendar,
CRM, etc.

---

## The A2A bus

`protocol/a2a.py` is a tiny in-process message bus with
typed envelopes (`Message` dataclass). It's enough for a
single-machine run; for a multi-machine run you'd swap it
for Kafka / NATS and the message schema stays the same.

The bus routes messages by agent name. Each agent
subscribes to its own queue; the producer writes to it.
There's no fan-out, no broadcast, no topic-based routing —
the producer knows who's consuming. This is the simplest
correct multi-agent pattern; everything else is
optimization.

---

## How to run it

```bash
# Local
pip install -r requirements.txt
cp .env.example .env  # set ANTHROPIC_API_KEY
streamlit run ui/app.py

# Or in Docker
docker build -t synapse .
docker run --rm -p 8501:8501 --env-file .env synapse
```

The Streamlit UI runs at `http://localhost:8501`. Click
"Generate today's brief" and you'll get a Markdown brief
in 15-30 seconds (one model call per agent, plus the MCP
tool calls the Scout makes).

---

## What this is NOT

- **Not a production multi-agent platform.** The bus is
  in-process, the agents are single-machine, the model
  calls are unbounded. For production, see
  [`../../agentic-ai/16-autonomous-loop/`](../../agentic-ai/16-autonomous-loop/)
  for the bounded-loop + budget + retry pattern, and
  [`../../agentic-ai/15-multi-agent-debate/`](../../agentic-ai/15-multi-agent-debate/)
  for the verifier pattern.
- **Not a research project on agent collaboration.** The
  three agents have fixed roles; there's no negotiation,
  no debate, no plan revision. The bigger patterns live
  elsewhere in this repo.
- **Not a chat product.** No streaming UI, no memory
  across briefs, no user accounts. The brief is one-shot;
  click the button, get the brief, read it.

---

## The 5 things this project teaches

1. **Agent boundaries are the design.** Scout / Contextualist /
   Publisher are the only thing you have to read to
   understand the system. The bus is one method
   (`bus.send(agent_name, message)`).
2. **MCP is the right protocol for tool use.** Each server
   is a small Python module; the agent binds to all of
   them at startup. Adding a fifth server is a 5-line
   change.
3. **A2A messages are typed.** The bus doesn't know what
   they're carrying; the consumer does. Same pattern as
   Kafka — schema in the producer, deserialization in the
   consumer.
4. **The "show me the brief" button is the only UI.** A
   Streamlit button + a Markdown render is enough to
   demonstrate the whole system. Don't over-UI a demo.
5. **Eval is the next project.** This project ships
   without a formal eval harness. The right next step is
   RAGAS / DeepEval scoring the briefs against a held-out
   set of "good brief" examples. That's the pattern in
   [`../../ai-engineering/04-fm-evaluation/`](../../ai-engineering/04-fm-evaluation/).

---

## Related directories

- [`../../agentic-ai/`](../../agentic-ai/) — the broader
  agentic-AI half of the portfolio (18 agents). Synapse
  fits here as the "small working reference" example.
- [`../../ai-engineering/03-multi-agent-platform/`](../../ai-engineering/03-multi-agent-platform/) —
  the production-shaped cousin with LangGraph, Bedrock,
  and shared memory.
- [`../../ai-engineering/01-enterprise-rag-platform/`](../../ai-engineering/01-enterprise-rag-platform/) —
  the RAG layer that the Contextualist agent would benefit
  from (today it does a single model call per signal;
  with RAG it would cite sources).
