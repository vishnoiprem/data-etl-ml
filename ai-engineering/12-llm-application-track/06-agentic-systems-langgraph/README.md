# Course 6 — Agentic Systems with LangGraph

> Source: Data Vidhya — Agentic Systems with LangGraph
> Level: Advanced | Prereqs: Courses 1–5 (especially tool use)

---

## Course Promise

> "Build agents that reason, plan, recover from errors, ask for human help, and persist state — the systems that go beyond the demo."

LangGraph is the **stateful orchestration** framework. Where LangChain gives you chains, LangGraph gives you **graphs**: cycles, branches, conditional edges, human-in-the-loop, and persistence. This is where LLM applications stop being toys and start being systems.

---

## Lesson Index

| # | Lesson | Type | Theme |
|---|--------|------|-------|
| 1 | [The agent loop, beyond ReAct](./01-beyond-react-agent.md) | Article + Worked Example | Why ReAct isn't enough, cycles, persistence, HIL |
| 2 | State & persistence | Article | `StateGraph`, checkpointing, memory, replay |
| 3 | Nodes & edges | Article | Functions as nodes, conditional routing, parallel branches |
| 4 | Cycles & termination | Article | `max_iterations`, `should_continue`, error paths |
| 5 | Human-in-the-loop | Article | `interrupt`, approval gates, feedback integration |
| 6 | Multi-agent orchestration | Article | Supervisor pattern, peer-to-peer, handoffs |
| 7 | Streaming & observability | Article | `astream_events`, LangSmith traces, debugging |
| 8 | Production deployment | Article | Long-running, async, queue-backed, idempotent |

---

## What "good" looks like after this course

1. You can model an LLM system as a **graph**, not a chain.
2. You understand when an agent is needed vs a chain.
4. You can implement human-in-the-loop approval gates.
3. You can persist and resume agent state (long-running workflows).
5. You can coordinate multiple agents via supervisor or peer patterns.

---

## The Lead Lesson

> **Lesson 1 — [The agent loop, beyond ReAct](./01-beyond-react-agent.md)** — why ReAct (Course 5's pattern) is the wrong abstraction for production agents. Includes a complete LangGraph implementation of a research-agent with cycles, human approval, persistence, and the eval harness that gates it.