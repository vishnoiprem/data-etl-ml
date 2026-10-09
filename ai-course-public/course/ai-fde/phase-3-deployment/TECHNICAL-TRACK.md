# Technical Track — AI FDE Phase 3

> **From a working service to a production system.** Three lessons, ~2.5 hours total. Builds on the Phase 2 service in `../phase-2-core-build/`.

This track teaches the **production engineering craft** of taking an AI service out of "works on Daniel's laptop" and into "runs 24/7 for Mei and Sarah." Every lesson ends with runnable code + a pytest case that passes against the hardened Phase 2 service.

---

## Lesson map

| # | Lesson | What you build | Time |
|---|---|---|---|
| 01 | [Advanced retrieval and RAG](./technical/01-advanced-retrieval.md) | A hybrid retriever (BM25 + dense + RRF) in `../phase-2-core-build/service/retrieval_v2.py` (~250 lines). Replaces the Phase 2 token-overlap mock store. | 45 min |
| 02 | [Evaluation, monitoring, and iteration](./technical/02-eval-monitoring-iteration.md) | Adds `/draft/stream` (SSE), `/feedback` (thumbs up/down), `/metrics` (Prometheus), and `render_iteration_report.py` to the Phase 2 service. | 45 min |
| 03 | [Scale, reliability, and security failure handling](./technical/03-scale-reliability-security.md) | A `circuit.py` (~400 lines) with `CircuitBreaker` + `TokenBucketRateLimiter` + `Redactor` + `TTLCache` + `make_tiered_fallback`. Plus `telemetry.py` and a `Caddyfile`. | 45 min |

After lesson 03, the service is **production-grade**: 13/13 pytest cases pass, the circuit breaker trips on simulated outages, the rate limiter caps LLM calls per user, the redactor strips PII from logs, the metrics endpoint exposes Prometheus counters, and a Caddy reverse proxy terminates TLS.

---

## How the track builds on Phase 2

```
Phase 2 service (in ../phase-2-core-build/service/)
    │
    ├── app.py           ← T2 adds /draft/stream, /feedback, /metrics
    ├── circuit.py       ← T3 ADDS this file (new)
    ├── retrieval_v2.py  ← T1 ADDS this file (replaces the mock store)
    ├── eval.py          ← T2 adds render_iteration_report
    ├── telemetry.py     ← T3 ADDS this file (new)
    ├── Caddyfile        ← T3 ADDS this file (new)
    └── tests/           ← 13/13 cases pass (the regression suite)
```

The Phase 2 service is **not copied** into Phase 3. The Phase 3 lessons edit it in place via `importlib` indirection. The Phase 2 service stays the "single source of truth" for the drafter.

---

## What "Phase 3 technical" is NOT

- It is **not** Kubernetes. One container, one process, one port, Caddy in front.
- It is **not** a multi-region deployment. One VM, one Caddy, one service.
- It is **not** framework-heavy. No LangChain, no LlamaIndex. Plain Python.
- It is **not** async-everywhere. Only the streaming endpoint is async; the rest stay sync.

---

## Run the hardened service

```bash
cd ../phase-2-core-build/service
pip install -r requirements.txt
PF_LLM_PROVIDER=openai PF_OPENAI_API_KEY=sk-... uvicorn app:app --host 0.0.0.0 --port 8000
```

Or with the mock LLM backend (no API key needed):

```bash
cd ../phase-2-core-build/service
uvicorn app:app --host 0.0.0.0 --port 8000
```

Then:

```bash
# Health
curl localhost:8000/health

# Draft (with hybrid retrieval)
curl -X POST localhost:8000/draft -H 'Content-Type: application/json' \
     -d '{"email":"Where is PF-1003?", "shipment_id":"PF-1003"}'

# Stream
curl -X POST localhost:8000/draft/stream -H 'Content-Type: application/json' \
     -d '{"email":"Where is PF-1003?", "shipment_id":"PF-1003"}'

# Feedback
curl -X POST localhost:8000/feedback -H 'Content-Type: application/json' \
     -d '{"draft_id":"abc-123", "rating":"up"}'

# Metrics
curl localhost:8000/metrics

# Circuit state
curl localhost:8000/circuit/state

# Run the 13-test regression suite
pytest tests/ -v
```

---

## Run in Docker (with Caddy)

```bash
cd ../phase-2-core-build/service
docker compose up
```

The `docker-compose.yml` brings up the FastAPI service behind a Caddy reverse proxy on port 443. Caddy handles TLS termination (Let's Encrypt) and per-IP rate limiting at the edge.

---

## What's next

- The **Consulting Track** — the stakeholder map, iteration cadence, runbook, RACI, and on-call rotation that go with this service.
- **Phase 4 (Capstone)** — `../phase-4-capstone/` — where the Phase 3 service is lifted into a platform: MCP, multi-agent, distilled SLM, fresh engagement.
- **`course/practice/level-5-agents/`** — when you want LangGraph, ReAct, and multi-agent patterns (Phase 4 Project 2 builds on these).
- **`course/practice/level-6-production/`** — when you want FT + deploy + observability patterns (Phase 4 Project 3 builds on these).
- **`course/hardcode/level-9-failure-handling/`** — when you want more sandbox patterns and policy files (Phase 4 Projects 1 and 4 build on these).

---

**Last updated:** 2026-10-09
**Phase:** 3 of 4 (Deployment & Reliability)
**Prerequisite:** [Phase 2 — Core Build](../phase-2-core-build/)
