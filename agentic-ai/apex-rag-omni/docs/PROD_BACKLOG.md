# Production Hardening — Backlog

Status (updated on branch `feature/apex-rag-omni-chatgpt-review`). Items 1-7 shipped in v0.2.0; 8-11 shipped here:

| # | Gap | Status |
|---|---|---|
| 1 | Auth (APIKeyHeader) on /traces, /query, /feedback, /eval | **DONE** |
| 2 | Async audit writes (off the event loop) | **DONE** |
| 3 | /healthz (liveness) + /readyz (readiness, pings Qdrant+ES) split | **DONE** |
| 4 | CORS middleware with explicit `allow_origins` from env | **DONE** |
| 5 | `Settings(BaseSettings)` + `.env.example`, env-driven config | **DONE** |
| 6 | `QueryRequest.query` max_length=2000 + per-collection filter allowlist | **DONE** |
| 7 | Real eval harness (Postgres + JSONL fallback, no more hardcoded targets) | **DONE** |
| 8 | Streaming `/query/stream` (SSE) + measured per-stage timings | **DONE** (feature/apex-rag-omni-chatgpt-review) |
| 9 | Working local retriever + extractive grounded answerer (replaces stubs) | **DONE** |
| 10 | Hallucination gate + input/output sanitization + PII redaction in audit | **DONE** |
| 11 | Time-ordered trace ids (keyset-pagination correctness), constant-time auth | **DONE** |

9 gaps remain. Listed in execution order. Each is a separate PR.

## Backlog

### B1. Global exception handler + structured JSON logs (gap #10 + part of #2)
- **Why:** Unhandled exceptions return FastAPI's default 500 with stack traces in dev mode. Nothing correlates to a request ID. Debugging a 5xx in prod is impossible today.
- **Files:** `backend/app/main.py` (new `@app.exception_handler(Exception)`), new `backend/app/middleware.py` (request-id + structlog JSON).
- **Plan:** Add `X-Request-ID` middleware that generates a UUID per request (or accepts an inbound one), wires it to structlog's contextvars, and echoes it in the response header. Replace `logging.basicConfig` with `structlog.configure(...)` for JSON output. Global exception handler logs the exception with the request ID and returns `{"error": "...", "request_id": "..."}` without a traceback.
- **Estimate:** 4 hours.

### B2. Real LLM call (gap #11)
- **Why:** `apex_answerer.grounded_answer()` simulates the gateway (zero latency, perfect output). The current `/query` is a deterministic mock. Real model integration is the single biggest correctness risk.
- **Files:** `backend/app/apex_answerer.py` (replace simulation with httpx call to `settings.model_gateway_url`), add `tenacity` retry decorator with `wait_exponential`, add circuit breaker state.
- **Note:** the streaming seam is `stream_tokens()`; the hallucination gate and sanitizers already run on whatever answer is produced, so a model's output is checked before it reaches the user.
- **Plan:** `httpx.AsyncClient(timeout=httpx.Timeout(connect=2, read=8, write=10, pool=2))` against the gateway. On 5xx or timeout: retry with exponential backoff (max 3). If still failing: return `refused=True, refusal_reason="model gateway unavailable"` — never hang. Track in-flight calls; if > 50 concurrent, refuse new ones (circuit open).
- **Estimate:** 1 day.

### B3. Rate limit + per-key cost ceiling (gap #13)
- **Why:** No per-IP or per-key rate limit. No daily token budget on `/query`. One misconfigured client can drive unbounded LLM cost.
- **Files:** `backend/app/rate_limit.py` (new, slowapi or hand-rolled Redis token bucket), modify `backend/app/main.py` to apply the dep.
- **Plan:** Per-API-key: 60 RPS, 100K tokens/day, 1M tokens/month hard cap (returns 429 with `Retry-After`). Per-IP: 10 RPS (backstop for unauthenticated traffic, even though we 403 them). Use Redis if `APEX_REDIS_URL` is set; in-memory dict fallback for dev. Log every 429 for cost reconciliation.
- **Estimate:** 1 day.

### B4. Prometheus `/metrics` + OpenTelemetry tracing (rest of gap #2)
- **Why:** No standardized observability. K8s Prometheus scraper, Datadog, etc. can't ingest custom metrics. Distributed traces (across the LLM call, Qdrant fan-out, ES) need OTel.
- **Files:** `backend/app/main.py` (add `prometheus-fastapi-instrumentator` + `/metrics` route), `backend/app/otel.py` (new, OTel auto-instrumentation for httpx + FastAPI).
- **Plan:** `/metrics` exposes `http_requests_total`, `http_request_duration_seconds`, `apex_query_refused_total`, `apex_audit_queue_size`, `apex_audit_dropped_total`. OTel exports to a configurable OTLP endpoint (`APEX_OTLP_ENDPOINT`). Trace every `/query` end-to-end including the (future) LLM call.
- **Estimate:** 1 day.

### B5. Dockerfile + graceful shutdown (gap #12)
- **Why:** No production image. `uvicorn --reload` is a dev tool. SIGTERM in K8s terminates the pod mid-request without draining the audit queue.
- **Files:** New `Dockerfile` (multi-stage, `python:3.12-slim`, non-root user, healthcheck), new `.dockerignore`, modify `backend/app/main.py` to handle SIGTERM via `signal.signal()` (drain audit queue, close httpx clients).
- **Plan:** Multi-stage: builder installs `requirements.txt` into a venv, runtime copies the venv only. Final image: non-root `apex` user, `uvicorn backend.app.main:app --workers $CPU --timeout 30`. Healthcheck uses `/healthz` (liveness) and `/readyz` (readiness, but compose uses the new `HEALTHCHECK` directive). Graceful shutdown: register a `signal.signal(SIGTERM, _shutdown)` that calls `audit_queue.flush_on_shutdown(timeout=10)` and `httpx.AsyncClient().aclose()` on all open clients.
- **Estimate:** 1 day.

### B6. CI / CD (gap #14)
- **Why:** No GitHub Actions. PRs don't run tests or lint. A 2000-line refactor can land with broken tests.
- **Files:** New `.github/workflows/ci.yml` (matrix: lint + test + type-check + contract), new `.pre-commit-config.yaml` (ruff + mypy).
- **Plan:** Workflow: `on: [push, pull_request]`, jobs run on Python 3.10 + 3.12. Steps: checkout, `pip install -r requirements.txt pytest pytest-asyncio pytest-cov`, `ruff check backend/ tests/`, `mypy backend/`, `pytest tests/ -v --cov=backend --cov-report=term-missing`. Pre-commit runs ruff + mypy locally on commit. Required status check on the `APEX-RAG-Omni` branch.
- **Estimate:** 4 hours.

### B7. ADRs + documentation honesty (gap #15)
- **Why:** README claims "Not a demo" but `apex_retriever.py` returns synthetic data, `apex_answerer.py` simulates the gateway. The deception undermines every other claim in the README.
- **Files:** New `docs/adr/0001-eval-store-choice.md` (Postgres + JSONL fallback), `docs/adr/0002-async-audit-queue.md` (asyncio.Queue + drain task), `docs/adr/0003-filter-key-allowlist.md`, `docs/adr/0004-auth-api-key.md`. Update `README.md` with a "Status" section listing live vs. simulated per surface.
- **Plan:** Each ADR follows the standard format (Context / Decision / Consequences). README "Status" section: 1 table per major surface (retriever, answerer, eval store, audit store, gateway), with column "Status" = `live | simulated | stubbed` and a sentence explaining what's needed to move to `live`. Retriever is now a working in-process index (`local_index.py`) over a demo corpus; the answerer is extractive (no LLM). B2 adds the LLM, B8 swaps in Qdrant/ES. The hallucination gate (`hallucination.py`) already sits in front of any generator.
- **Estimate:** 4 hours.

### B8. Replace dummy retriever with real Qdrant client (gap #11, separate from B2)
- **Why:** `apex_retriever.hybrid_search()` returns fake `RetrievedDoc` objects. The RRF + shard routing is real, but the data is mocked. Without a real client, the production eval numbers are meaningless.
- **Files:** `backend/app/apex_retriever.py` (replace stub fan-out with `qdrant_client.AsyncQdrantClient.search` per shard, then RRF), `backend/app/elasticsearch_client.py` (new, async ES BM25 client).
- **Plan:** Async fan-out via `asyncio.gather` against 10 Qdrant shards. Each shard returns Top-K candidates. RRF fuses with ES BM25 results. Single-tenant Qdrant first; multi-tenant routing as a follow-up. The dummy retriever stays for unit tests via a `USE_DUMMY_RETRIEVER=1` env var.
- **Estimate:** 2-3 days.

### B9. Frontend X-API-Key wiring (no audit gap; out-of-scope for backend hardening)
- **Why:** The API now requires `X-API-Key`. The Next.js frontend at `frontend/app/components/ApexRagOmni.tsx` doesn't send it. Every call from the UI will 403.
- **Files:** `frontend/app/components/ApexRagOmni.tsx` (add a `fetch` wrapper that reads `NEXT_PUBLIC_APEX_API_KEY` and attaches it), `frontend/.env.local` (new).
- **Plan:** Single `apexFetch(path, init)` helper that wraps `fetch()` and adds the `X-API-Key` header. Replace all direct `fetch` calls in the component. Document the env var in `frontend/README.md` (or a new file). Dev key from `.env`; prod key from K8s secret. Optional: add a UI prompt for the user to paste a key, stored in `localStorage`.
- **Estimate:** 2 hours.

## Cumulative cost

| Backlog item | Estimate |
|---|---|
| B1. Exception handler + JSON logs | 4 h |
| B2. Real LLM call | 1 d |
| B3. Rate limit + cost ceiling | 1 d |
| B4. Prometheus + OTel | 1 d |
| B5. Dockerfile + graceful shutdown | 1 d |
| B6. CI / CD | 4 h |
| B7. ADRs + README honesty | 4 h |
| B8. Real Qdrant + ES clients | 2-3 d |
| B9. Frontend X-API-Key | 2 h |
| **Total** | **~2 weeks** |

## Definition of "production-ready"

When all 9 backlog items are complete, the system is deployable to a regulated environment (SOC2 / HIPAA / FedRAMP baseline). At that point:

- The README's "Not a demo" claim is honest
- Every endpoint has auth + audit + metrics + tracing
- LLM calls have timeouts, retries, circuit breakers
- The pod survives SIGTERM without dropping audit events
- Eval reports are real numbers from a real harness on real data
- Every change passes CI before merging

Until then, the system is "prototype with prod bones" — deployable behind an auth wall with mock retrieval, which is the bar for the v0.2.0 ship.
