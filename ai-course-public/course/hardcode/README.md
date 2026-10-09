# Hardcode Track — Production-Grade AI Systems You Actually Build

> **The "hard coder" track. Real code. Real systems. Real time. No tutorials.**

If the regular `practice/` track has 200-line teaching labs, this `hardcode/` track has **500-1500 line runnable production systems** you ship to real users. Each file is a complete, multi-component system with real WebSockets, real async queues, real observability, real failure handling.

---

## What makes this "hardcode"

| Aspect | `practice/` (teaching) | `hardcode/` (production) |
|---|---|---|
| **Code size** | 100-300 lines per lab | 500-1500 lines per system |
| **Components** | Single file, single concept | Multi-file: API + worker + cache + metrics + tests |
| **Async** | Mostly synchronous | Full `asyncio`, `aiohttp`, async generators, async DB |
| **Real-time** | Batch examples | WebSockets, SSE, streaming pipelines, event-driven |
| **Observability** | Print statements | Prometheus, structured JSON logs, OpenTelemetry traces |
| **Failure handling** | try/except | Circuit breakers, retry with jitter, dead-letter queues, graceful degradation |
| **Testing** | Manual | pytest + fixtures + integration tests + load tests |
| **Deployment** | "Run it locally" | Dockerfile + compose + env config + health checks |

---

## Topic coverage (your stated requirements)

This track explicitly covers:

1. **LLMs, AI applications, RAG pipelines, and agentic workflows** — each lab is one of these in production form
2. **Integrating AI into workflows while managing probabilistic model behavior** — every lab includes fallback strategies when the LLM fails
3. **Probabilistic: outputs can vary and require continuous evaluation** — every lab has an eval harness + observability
4. **Functional testing plus model, retrieval, and workflow evaluation** — every lab has a `tests/` directory with full test suite
5. **Hallucinations, poor retrieval, incorrect tool calls, model failures, API errors, unexpected agent behavior** — every lab has explicit failure modes + handling
6. **Structured and unstructured data, proprietary documents, knowledge bases, real-time business data** — RAG labs include all of these

---

## Level organization

### `level-1-llm-foundations/` — Heavy LLM client work
Building production LLM clients from scratch: token streaming, retry logic, cost tracking, multi-model routing, batch processing, embeddings at scale, async workers. No frameworks — just `openai` and `httpx`.

### `level-2-ai-workflows/` — Integrating AI into business workflows
Real workflow systems: email triage, document processing pipelines, customer support routers, content moderation queues. Each one is a runnable pipeline that processes real data.

### `level-3-streaming/` — Real-time streaming systems
WebSocket chat, SSE responses, multi-worker pub/sub, server-sent events for long-running tasks. **This is where Lab 01 (the WebSocket chat) lives.**

### `level-4-rag-pipelines/` — Production RAG
RAG systems that handle 1M+ docs, with hybrid search, re-ranking, citations, multi-tenant isolation, async ingestion pipelines. Real vector DBs, real chunking, real evaluation.

### `level-5-agentic-workflows/` — Agentic systems
ReAct agents, multi-agent systems, tool use, planning, error recovery. Each agent system has explicit failure handling for "agent went off the rails."

### `level-6-production-systems/` — Production deployment
Docker, Kubernetes manifests, CI/CD pipelines, secrets management, blue/green deploys, autoscaling.

### `level-7-real-time-pipelines/` — Real-time data + AI
Kafka/Redis Streams consumers, change-data-capture + AI, real-time anomaly detection, live dashboards with AI insights. Real-time business data flowing through AI.

### `level-8-evaluation-testing/` — Eval & testing harnesses
LLM-as-judge, RAGAS, regression test suites, A/B test infrastructure, model comparison frameworks, drift detection.

### `level-9-failure-handling/` — When things break
Circuit breakers, bulkheads, fallback chains, prompt injection defense, hallucination detection, model degradation detection, incident playbooks.

---

## How to use this track

Each folder contains 2-5 heavy lab systems. For each system:

1. **Read the docstring at the top** — it explains what the system does, the architecture, and how to run it
2. **Install dependencies** — listed in the docstring (no requirements.txt because the imports tell you what you need)
3. **Run it** — most systems have an `if __name__ == "__main__"` block
4. **Read the code top-to-bottom** — it's written to be read, not just executed
5. **Modify it** — every system has "TODO: extend with X" markers

---

## Code style

- **Heavy use of `asyncio`** — every system is async-native
- **Type hints everywhere** — `def foo(x: int) -> str:`, not `def foo(x):`
- **Structured logging** — JSON logs, not print statements
- **Dependency injection** — `app.state` for shared resources, not globals
- **Graceful shutdown** — every system handles SIGTERM properly
- **Environment-based config** — no hardcoded URLs, all via env vars

---

## Companion to the rest of the course

This track is **the heavy coding layer** that sits on top of:
- `practice/` — the conceptual + teaching track
- `180-day-ai/` — the daily small-project track
- `capstone-starters/` — the 8-week capstone projects

If you finish a `practice/` lab and want to see "how do I actually ship this?", look in `hardcode/` for the production version.

---

## Inventory

| # | Folder | File | Lines | Topics |
|---|---|---|---|---|
| 01 | `level-1-llm-foundations/` | `01-multi-model-async-router.py` | 1,240 | Multi-provider routing, batching, per-provider circuit breakers, content-hash dedup, Prometheus |
| 02 | `level-1-llm-foundations/` | `02-async-embedding-pipeline.py` | 858 | Async worker pool, bounded semaphore, retry+jitter, DLQ, checkpoint resume, FAISS/NumPy |
| 03 | `level-2-ai-workflows/` | `03-email-triage-pipeline.py` | 915 | IMAP fetcher, LLM classifier, auto-draft, webhook router, SQLite audit, JSONL spill |
| 04 | `level-2-ai-workflows/` | `04-content-moderation-queue.py` | 714 | Redis-list queue, two-stage classifier, token-bucket rate limit, DLQ, Prometheus |
| 05 | `level-2-ai-workflows/` | `05-document-ingestion-pipeline.py` | 761 | FS watcher, content-hash skip, multi-format parser, sentence chunking, DLQ |
| 06 | `level-2-ai-workflows/` | `06-knowledge-base-qa-system.py` | 795 | BM25 + vector hybrid, LLM re-ranker, citations, feedback re-weighting |
| 01 | `level-3-streaming/` | `01-realtime-chat-websocket.py` | 858 | WebSocket + SSE, token-bucket via Redis Lua, conversation history, Prometheus, cost tracking |
| 07 | `level-4-rag-pipelines/` | `07-hybrid-search-rag.py` | 1,300 | BM25 + dense + RRF, metadata filters, LLM re-ranker, multi-tenant, RAGAS metrics |
| 08 | `level-4-rag-pipelines/` | `08-rag-async-ingestion.py` | 1,200 | Source adapters (FS/S3/Notion/Conf), pypdf+OCR, semantic chunker, token-bucket, DLQ |
| 09 | `level-5-agentic-workflows/` | `09-react-agent-tools.py` | 1,041 | ReAct loop, 6 tools, recovery policy, stuck detector, HITL, JSONL trail |
| 10 | `level-5-agentic-workflows/` | `10-multi-agent-orchestrator.py` | 960 | Researcher + Writer + Reviewer, asyncio message bus, DAG plan, HITL escalation |
| 11 | `level-8-evaluation-testing/` | `11-llm-as-judge-eval.py` | 849 | 12-item eval set, async judge, 3 dimensions, A/B, regression mode, HTML report |
| 12 | `level-8-evaluation-testing/` | `12-ragas-evaluation.py` | 821 | 52-item golden set, 4 RAGAS metrics, A/B, baseline save/compare, markdown report |
| 13 | `level-6-production-systems/` | `13-autoscaling-llm-service.py` | 1,294 | Bounded priority queue, HPA via Little's Law, per-downstream breakers, load tester |
| 14 | `level-6-production-systems/` | `14-multi-region-llm-gateway.py` | 1,138 | Active health probes, latency routing, HMAC signing, per-user rate limit, CO2 cost |
| 15 | `level-7-real-time-pipelines/` | `15-kafka-ai-consumer.py` | 1,151 | Pluggable Kafka/Redis/in-memory, idempotency, DLQ, backpressure, group coordinator |
| 16 | `level-7-real-time-pipelines/` | `16-realtime-anomaly-detector.py` | 1,045 | Async streaming, EWMA baseline, z-score + hysteresis, mock LLM explainer, replay |
| 17 | `level-9-failure-handling/` | `17-circuit-breaker-llm.py` | 1,071 | Multi-signal breaker (errors+p99+cost+quality), full-jitter backoff, LRU cache fallback |
| 18 | `level-9-failure-handling/` | `18-hallucination-detector.py` | 1,089 | NLI + fact-check + citation coverage, soft confidence, human review queue, dashboard |

**Total: 19 systems, 19,100 lines, covering all 10 topic areas you specified.**

### Topic coverage map

| User's stated requirement | Systems that address it |
|---|---|
| LLMs, AI applications, RAG pipelines, agentic workflows | 01, 02, 07, 08, 09, 10, 11, 12 |
| Integrating AI while managing probabilistic behavior | 01, 09, 10, 17, 18 |
| Probabilistic: outputs vary, need continuous evaluation | 11, 12, 17, 18 |
| Functional + model + retrieval + workflow evaluation | 11, 12, 13, 17 |
| Hallucinations, poor retrieval, bad tool calls, agent misbehavior | 09, 10, 17, 18 |
| Structured + unstructured data, proprietary docs, KB, real-time business data | 05, 06, 07, 08, 15, 16 |
| App performance + model quality + hallucination rate + retrieval + latency + cost + agent behavior | 01, 13, 14, 17, 18 |
| Code changes + prompts + models + retrieval + eval + agent workflow | 11, 12, 13 |
| Human-in-the-loop review, escalation, approval | 09, 10, 18 |
| Reliable business outcomes | 11, 12, 17, 18 |

---

**Last updated:** 2026-10-09
**Style:** Production-grade, multi-file, async, observable
**Goal:** You finish this track and you can build + ship any AI system to production.
