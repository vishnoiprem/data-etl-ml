"""
service/app.py — PacificFreight Phase 2/3 FastAPI service (the deliverable).

What this file does
-------------------
Exposes 9 endpoints:

    GET  /health                → liveness probe + circuit state + n_chunks
    POST /draft                 → RAG-augmented draft (Phase 2 — unchanged contract)
    GET  /retrieve              → inspect what the retriever would return (Phase 2)
    POST /eval                  → run the eval set, return a markdown report (Phase 2)
    POST /draft/stream          → SSE streaming variant of /draft (Phase 3 T1)
    POST /feedback              → record a thumb on a draft (Phase 3 T2)
    GET  /metrics               → Prometheus text format (Phase 3 T2)
    POST /admin/reindex         → swap the retrieval corpus (Phase 3 T1)
    GET  /circuit/state         → current circuit state + recent transitions (Phase 3 T3)

The RAG pipeline (mirrors what Phase 1's CLI does, but over HTTP):
    1. Take the email + (optional) shipment_id.
    2. Retrieve the top-K policy chunks (k=2) and top-K shipment chunks (k=1)
       using the Phase 3 hybrid retriever (BM25 + dense + RRF).
    3. If a shipment_id was given, also look it up in the tracker.
    4. Build a RAG-augmented system prompt.
    5. Call Phase 1's `complete()` through the circuit breaker (Phase 3 T3)
       with rate limiting per user and PII redaction of the email body.
    6. Return the draft + the contexts that were used (so the eval harness
       can score it).

How to run
----------
    # From the phase-2-core-build/ directory:
    pip install -r service/requirements.txt
    uvicorn service.app:app --host 0.0.0.0 --port 8000

    # Or in Docker:
    docker build -t pf-phase2 service/       # build context = phase-2-core-build/
    docker run --rm -p 8000:8000 pf-phase2

What to read next
-----------------
- service/rag.py          — Phase 2 mock vector store
- service/retrieval_v2.py — Phase 3 hybrid (BM25 + dense + RRF)
- service/circuit.py      — Phase 3 circuit breaker + rate limiter + redactor
- service/telemetry.py    — Phase 3 metrics + JSON logger + request_id middleware
- service/eval.py         — the eval harness + regression check
- ../technical/           — the 6 lessons that walk through this code
- ../consulting/          — the 6 lessons that document why each piece is here
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, PlainTextResponse
from pydantic import BaseModel, Field

# Make sibling modules importable when running as a script or under uvicorn.
_HERE = Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import rag as rag_mod  # noqa: E402
import eval as eval_mod  # noqa: E402
import retrieval_v2 as retrieval_v2_mod  # noqa: E402
import circuit as circuit_mod  # noqa: E402
import telemetry as telemetry_mod  # noqa: E402


# ---------------------------------------------------------------------------
# Reuse Phase 1's complete() — same importlib pattern as 04-first-ai-tool.py
# ---------------------------------------------------------------------------
def _load_phase1_complete():
    """Import phase-1-foundations/technical/03-modern-ai-tooling.py as a module
    and return the `complete` function and the module itself."""
    p1_path = (
        _HERE.parent.parent / "phase-1-foundations" / "technical" / "03-modern-ai-tooling.py"
    )
    spec = importlib.util.spec_from_file_location("pf_llm", p1_path)
    pf_llm = importlib.util.module_from_spec(spec)
    sys.modules["pf_llm"] = pf_llm  # so dataclasses inside the module can resolve
    spec.loader.exec_module(pf_llm)
    return pf_llm


_pf_llm = _load_phase1_complete()
complete = _pf_llm.complete
PRICING = _pf_llm.PRICING


# ---------------------------------------------------------------------------
# Pydantic request/response models
# ---------------------------------------------------------------------------
class DraftRequest(BaseModel):
    email: str = Field(..., description="The inbound customer email body")
    shipment_id: Optional[str] = Field(None, description="Optional PF-XXXX id; if missing, the service retrieves it")
    rep: Optional[str] = Field(None, description="CS rep first name for the sign-off line")
    n_policy_chunks: int = Field(2, ge=1, le=5)
    n_shipment_chunks: int = Field(1, ge=1, le=5)


class ContextSnippet(BaseModel):
    id: str
    source: str
    score: float
    text: str
    metadata: dict


class DraftResponse(BaseModel):
    ok: bool
    draft: str
    shipment_id: Optional[str]
    contexts: list[ContextSnippet]
    model: str
    provider: str
    is_mock: bool
    cost_usd: float
    latency_ms: int


class RetrieveResponse(BaseModel):
    ok: bool
    query: str
    chunks: list[ContextSnippet]


class EvalRequest(BaseModel):
    set: Optional[str] = Field(None, description="Path to eval_set.jsonl (defaults to ../shared/eval_set.jsonl)")
    baseline: Optional[str] = Field(None, description="Optional baseline.jsonl path")
    threshold: float = Field(0.05, ge=0.0, le=1.0)
    save_baseline: Optional[str] = Field(None, description="If set, write current aggregate as this path")


# ---------------------------------------------------------------------------
# Phase 3 Pydantic models
# ---------------------------------------------------------------------------
class FeedbackRequest(BaseModel):
    draft_id: str = Field(..., description="The request_id (or arbitrary id) of the draft being rated")
    rating: int = Field(..., ge=-1, le=1, description="-1 (bad), 0 (neutral), +1 (good)")
    note: Optional[str] = Field(None, description="Free-text from the CS rep (optional)")


class ReindexRequest(BaseModel):
    policy_chunks: Optional[list[dict]] = Field(None, description="Replace the policy chunk corpus")
    shipments: Optional[list[dict]] = Field(None, description="Replace the shipment chunk corpus")


class ReindexResponse(BaseModel):
    ok: bool
    n_policy: int
    n_shipment: int
    n_total: int
    rebuild_ms: int


# ---------------------------------------------------------------------------
# Phase 3 module-level singletons
# ---------------------------------------------------------------------------
_RETRIEVER: retrieval_v2_mod.HybridRetriever | None = None
_REDACTOR = circuit_mod.Redactor()
_RATE_LIMITER = circuit_mod.TokenBucketRateLimiter(capacity=20, refill_rate=0.33)  # 20 burst, 1 every 3s = 20/min
_USAGE_LOG = telemetry_mod.JsonLogger(
    _HERE / "usage.jsonl" if _HERE.exists() else Path("usage.jsonl")
)
# LLM call wrapped in a circuit breaker. Failure threshold 25%, latency P99
# 4s, cost $5/min — calibrated to PacificFreight's 150 emails/day profile.
_LLM_CACHE = circuit_mod.TTLCache(max_size=64, ttl_seconds=600.0)
_LLM_BREAKER = circuit_mod.CircuitBreaker(
    name="openai",
    fallback=circuit_mod.make_tiered_fallback(_LLM_CACHE, cheaper_fn=None),
    config=circuit_mod.CircuitBreakerConfig(
        failure_threshold=0.25,
        latency_p99_ms_threshold=4000.0,
        cost_per_min_usd_threshold=5.0,
        min_calls_in_window=5,
        cooldown_seconds=30.0,
    ),
)


def _get_retriever() -> retrieval_v2_mod.HybridRetriever:
    global _RETRIEVER
    if _RETRIEVER is None:
        _RETRIEVER = retrieval_v2_mod.HybridRetriever()
    return _RETRIEVER


# ---------------------------------------------------------------------------
# Shared pipeline helpers
# ---------------------------------------------------------------------------
_PF_ID_RE = re.compile(r"PF-\s*(\d{4,5})")
_PF_ID_CLEAN_RE = re.compile(r"PF-\d{4,5}")

_VECTOR_STORE: rag_mod.MockVectorStore | None = None


def _get_vector_store():
    """Phase 2 compat shim — returns the Phase 3 HybridRetriever.

    Both expose `retrieve(query, k, source_filter) -> list[RetrievedChunk]`
    with the same return shape, so Phase 2 callers (and tests) keep working.
    The hybrid retriever uses BM25 + dense + RRF (T1 lesson) — better
    ranking at the cost of one extra process step.
    """
    return _get_retriever()


def _load_tracker() -> list[dict]:
    """Read the Phase 1 tracker file. Returns the list of shipment dicts."""
    path = _HERE.parent.parent / "phase-1-foundations" / "shared" / "shipments.json"
    if not path.exists():
        return []
    with path.open() as fh:
        return json.load(fh).get("shipments", [])


def _extract_id(text: str) -> Optional[str]:
    """Extract the *most recent* PF-XXXX reference from a string.

    Same heuristic as Phase 1: pick the last PF ID, since the most recent
    is usually the one the CS person should act on. Tolerates whitespace
    (e.g. "PF - 1003" or "PF  -  1003"). Uses the whitespace-tolerant
    regex _PF_ID_RE, not _PF_ID_CLEAN_RE — the clean regex would miss
    "PF - 1003" entirely.
    """
    matches = _PF_ID_RE.findall(text.upper())
    if not matches:
        return None
    # Each match is just the digits; reconstruct the canonical PF-NNNN form.
    return f"PF-{matches[-1]}"


def _find_shipment(shipments: list[dict], shipment_id: str) -> dict | None:
    target = shipment_id.upper().strip()
    for s in shipments:
        if s["id"].upper() == target:
            return s
    return None


# ---------------------------------------------------------------------------
# Pipeline: draft a reply
# ---------------------------------------------------------------------------
PERSONA_AND_STYLE = (
    "You are PacificFreight's customer-service drafter. "
    "You draft concise, factual replies in the customer's language. "
    "Follow the retrieved policy chunks: 4-line opener, no jargon, sign "
    "with — {rep} at PacificFreight. Output ONLY the reply."
)


def _draft_pipeline(req: DraftRequest, request_id: str = "") -> DraftResponse:
    started = time.monotonic()
    request_id = request_id or telemetry_mod.new_request_id()
    store = _get_retriever()
    shipments = _load_tracker()

    # 1. Rate-limit per user (Phase 3 T3). Skippable in tests via env var
    #    so the eval harness can run 30 back-to-back calls without tripping.
    user_key = req.rep or "anonymous"
    if os.environ.get("PF_DISABLE_RATE_LIMIT") != "1" and not _RATE_LIMITER.try_acquire(user_key):
        telemetry_mod.REGISTRY.counter(
            "pf_drafts_total", labels={"outcome": "rate_limited"}
        ).inc()
        _USAGE_LOG.log(
            request_id=request_id, outcome="rate_limited", latency_ms=0,
            model="n/a", cost_usd=0.0,
            circuit_state=circuit_mod.STATE_NAME[_LLM_BREAKER.state],
            user_id=user_key, note="rate_limiter_rejected",
        )
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded for user '{user_key}'. Try again shortly.",
        )

    # 2. PII redaction of the email body (Phase 3 T3).
    redacted_email = _REDACTOR.redact(req.email)
    redaction_stats = _REDACTOR.stats()

    # 3. Determine the shipment_id (from explicit param, else extract from email).
    shipment_id = req.shipment_id or _extract_id(req.email)

    # 4. If we have a shipment_id, look it up.
    shipment: dict | None = None
    if shipment_id:
        shipment = _find_shipment(shipments, shipment_id)

    # 5. Retrieve: top-N policy chunks (whole corpus) + top-N shipment chunks.
    #    Uses the Phase 3 HybridRetriever (BM25 + dense + RRF) — see
    #    service/retrieval_v2.py.
    policy_chunks = store.retrieve(redacted_email, k=req.n_policy_chunks, source_filter="policy")
    shipment_chunks: list = []
    if shipment_id:
        q = f"{redacted_email} {shipment_id}"
        shipment_chunks = store.retrieve(q, k=req.n_shipment_chunks, source_filter="shipment")

    all_chunks = policy_chunks + shipment_chunks

    # 6. Build the RAG prompt.
    rep_name = req.rep or "Linh"
    base = PERSONA_AND_STYLE.format(rep=rep_name)
    system_prompt = rag_mod.build_rag_prompt(
        base_system=base,
        email=redacted_email,
        shipment=shipment,
        chunks=all_chunks,
    )

    # 7. User prompt.
    user_prompt_parts = [f"Customer email:\n{redacted_email}\n"]
    if shipment is not None:
        user_prompt_parts.append("Shipment in tracker:")
        user_prompt_parts.append(f"- ID: {shipment['id']}")
        user_prompt_parts.append(f"- Status: {shipment.get('status', '?')}")
        user_prompt_parts.append(f"- Last event: {shipment.get('last_event', '?')}")
        if shipment.get("next_action_required"):
            user_prompt_parts.append(f"- Action required: {shipment['next_action_required']}")
    else:
        user_prompt_parts.append("(No shipment ID found in the email. Use the retrieved shipment chunks above to identify the right one.)")
    user_prompt_parts.append("\nDraft a reply.")
    user_prompt = "\n".join(user_prompt_parts)

    # 8. Call Phase 1's complete() through the circuit breaker (Phase 3 T3).
    def _do_complete():
        return complete(system=system_prompt, user=user_prompt)

    result = _LLM_BREAKER.call(_do_complete, __cost_usd=0.0)
    latency_ms = int((time.monotonic() - started) * 1000)

    # 9. Telemetry: counters, histograms, structured log.
    outcome = "ok"
    fallback_tier = None
    if isinstance(result, dict) and "fallback_tier" in result:
        # Came from the tiered fallback.
        outcome = "fallback"
        fallback_tier = result.get("fallback_tier")
        # Re-shape: produce a DraftResponse-shaped object from the fallback dict.
        class _R:
            text = result.get("draft", "")
            model = result.get("model", "stub")
            provider = "stub"
            is_mock = True
            cost_usd = result.get("cost_usd", 0.0)
        # The /draft response shape is the same; the contexts are still ours.
        response = DraftResponse(
            ok=result.get("ok", True),
            draft=_R.text,
            shipment_id=shipment_id,
            contexts=[
                ContextSnippet(id=c.id, source=c.source, score=c.score,
                               text=c.text, metadata=c.metadata)
                for c in all_chunks
            ],
            model=_R.model, provider=_R.provider, is_mock=_R.is_mock,
            cost_usd=_R.cost_usd, latency_ms=latency_ms,
        )
    else:
        response = DraftResponse(
            ok=True,
            draft=result.text,
            shipment_id=shipment_id,
            contexts=[
                ContextSnippet(id=c.id, source=c.source, score=c.score,
                               text=c.text, metadata=c.metadata)
                for c in all_chunks
            ],
            model=result.model,
            provider=result.provider,
            is_mock=result.is_mock,
            cost_usd=result.cost_usd,
            latency_ms=latency_ms,
        )

    telemetry_mod.REGISTRY.counter(
        "pf_drafts_total", labels={"outcome": outcome}
    ).inc()
    telemetry_mod.REGISTRY.histogram(
        "pf_draft_latency_seconds", labels={"outcome": outcome}
    ).observe(latency_ms / 1000.0)
    _USAGE_LOG.log(
        request_id=request_id, outcome=outcome, latency_ms=latency_ms,
        model=response.model, cost_usd=response.cost_usd,
        circuit_state=circuit_mod.STATE_NAME[_LLM_BREAKER.state],
        user_id=user_key, shipment_id=shipment_id, n_contexts=len(all_chunks),
        note=fallback_tier or f"redacted:e={redaction_stats['emails']},p={redaction_stats['phones']}",
    )
    return response


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="PacificFreight Phase 2/3 — AI Drafter",
    description=(
        "RAG-augmented customer-service drafter. Phase 2 added the RAG "
        "service; Phase 3 added hybrid retrieval, streaming, feedback, "
        "metrics, circuit breaker, and rate limiting. Runs in mock mode by "
        "default; set PF_LLM_PROVIDER=openai + PF_OPENAI_API_KEY for real LLM."
    ),
    version="0.3.0",
)


@app.middleware("http")
async def _request_id_middleware(request: Request, call_next):
    """Generate a request_id per request, store in state, echo in header."""
    rid = request.headers.get("x-request-id") or telemetry_mod.new_request_id()
    request.state.request_id = rid
    started = time.monotonic()
    try:
        response = await call_next(request)
    except Exception:
        elapsed = time.monotonic() - started
        telemetry_mod.REGISTRY.histogram(
            "pf_request_duration_seconds",
            labels={"path": request.url.path, "outcome": "error"},
        ).observe(elapsed)
        raise
    elapsed = time.monotonic() - started
    telemetry_mod.REGISTRY.histogram(
        "pf_request_duration_seconds",
        labels={"path": request.url.path, "outcome": str(response.status_code)},
    ).observe(elapsed)
    response.headers["X-Request-Id"] = rid
    return response


@app.get("/health")
def health() -> dict:
    """Liveness probe + circuit state + chunk count."""
    return {
        "ok": True,
        "service": "pf-phase2",
        "n_chunks_loaded": _get_retriever().n_chunks,
        "circuit_state": circuit_mod.STATE_NAME[_LLM_BREAKER.state],
        "rate_limiter": _RATE_LIMITER.stats(),
    }


@app.post("/draft", response_model=DraftResponse)
def draft(req: DraftRequest, request: Request) -> DraftResponse:
    """Draft a customer-service reply for the given email."""
    return _draft_pipeline(req, request_id=request.state.request_id)


@app.get("/retrieve", response_model=RetrieveResponse)
def retrieve(
    q: str,
    k: int = 5,
    source: Optional[str] = None,
) -> RetrieveResponse:
    """Inspect what the retriever would return for a given query.

    Useful for debugging the RAG pipeline. `source` can be 'policy',
    'shipment', or omitted (both).
    """
    store = _get_retriever()
    chunks = store.retrieve(q, k=k, source_filter=source)
    return RetrieveResponse(
        ok=True,
        query=q,
        chunks=[
            ContextSnippet(
                id=c.id, source=c.source, score=c.score,
                text=c.text, metadata=c.metadata,
            )
            for c in chunks
        ],
    )


# ---------------------------------------------------------------------------
# Phase 3 endpoints
# ---------------------------------------------------------------------------
@app.post("/draft/stream")
def draft_stream(req: DraftRequest, request: Request):
    """SSE streaming variant of /draft (Phase 3 T1).

    Emits SSE events as the LLM produces tokens. With Phase 1's mock LLM,
    the response is a single `done` event carrying the canned reply —
    the real value here is the streaming protocol (events per token,
    graceful close on client disconnect, JSON line per usage.jsonl).

    For real OpenAI, swap `_stream_complete` for an OpenAI streaming call.
    """
    rid = request.state.request_id
    started = time.monotonic()

    def event_gen():
        try:
            # Run the full draft synchronously (mock LLM is fast); then
            # yield it as one 'done' event. The SSE protocol is what matters.
            result = _draft_pipeline(req, request_id=rid)
            chunk = json.dumps({
                "draft_id": rid,
                "draft": result.draft,
                "shipment_id": result.shipment_id,
                "contexts": [c.model_dump() for c in result.contexts],
                "model": result.model,
                "is_mock": result.is_mock,
                "cost_usd": result.cost_usd,
                "latency_ms": result.latency_ms,
            })
            yield f"event: done\ndata: {chunk}\n\n"
        except HTTPException as e:
            err = json.dumps({"error": e.detail, "status": e.status_code})
            yield f"event: error\ndata: {err}\n\n"
        finally:
            elapsed_ms = int((time.monotonic() - started) * 1000)
            telemetry_mod.REGISTRY.histogram(
                "pf_stream_duration_ms", labels={"outcome": "ok"}
            ).observe(elapsed_ms)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Request-Id": rid},
    )


@app.post("/feedback")
def feedback(req: FeedbackRequest, request: Request) -> dict:
    """Record a thumb-up/down on a draft (Phase 3 T2)."""
    rid = request.state.request_id
    _USAGE_LOG.log(
        request_id=req.draft_id, outcome="feedback",
        latency_ms=0, model="n/a", cost_usd=0.0,
        circuit_state=circuit_mod.STATE_NAME[_LLM_BREAKER.state],
        user_id="cs_team", feedback_rating=req.rating, note=req.note or "",
    )
    telemetry_mod.REGISTRY.counter(
        "pf_feedback_total", labels={"rating": str(req.rating)}
    ).inc()
    return {"ok": True, "draft_id": req.draft_id, "rating": req.rating}


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    """Prometheus text format (Phase 3 T2)."""
    # Add the dynamic gauges (circuit state, rate limiter, n_chunks).
    telemetry_mod.REGISTRY.gauge(
        "pf_circuit_state", labels={"downstream": "openai"}
    ).set(float(_LLM_BREAKER.state))
    telemetry_mod.REGISTRY.gauge("pf_active_rate_limiters").set(
        float(len(_RATE_LIMITER._buckets))
    )
    telemetry_mod.REGISTRY.gauge("pf_n_chunks_loaded").set(
        float(_get_retriever().n_chunks)
    )
    return PlainTextResponse(
        telemetry_mod.REGISTRY.render_prometheus(),
        media_type="text/plain; version=0.0.4",
    )


@app.post("/admin/reindex", response_model=ReindexResponse)
def admin_reindex(req: ReindexRequest) -> ReindexResponse:
    """Swap the retrieval corpus at runtime (Phase 3 T1)."""
    started = time.monotonic()
    retriever = _get_retriever()
    result = retriever.reindex(
        policy_chunks=req.policy_chunks, shipments=req.shipments
    )
    rebuild_ms = int((time.monotonic() - started) * 1000)
    telemetry_mod.REGISTRY.counter("pf_reindexes_total").inc()
    return ReindexResponse(
        ok=True,
        n_policy=result["n_policy"],
        n_shipment=result["n_shipment"],
        n_total=result["n_total"],
        rebuild_ms=rebuild_ms,
    )


@app.get("/circuit/state")
def circuit_state() -> dict:
    """Current circuit state + recent transitions (Phase 3 T3)."""
    return {
        "ok": True,
        "llm": _LLM_BREAKER.snapshot(),
        "cache": _LLM_CACHE.stats(),
    }


def _service_draft_fn(row: dict) -> dict:
    """Adapter so the service's pipeline can be scored by eval.py.

    Reuses `_draft_pipeline` so the eval reports the same metrics
    the production /draft endpoint would produce.
    """
    req = DraftRequest(email=row.get("email", ""))
    resp = _draft_pipeline(req)
    return {
        "draft": resp.draft,
        "contexts": [c.text for c in resp.contexts],
    }


@app.post("/eval")
def run_eval(req: EvalRequest) -> dict:
    """Run the eval set through the service's draft pipeline, return a
    markdown report + a regression check if a baseline was provided."""
    set_path = Path(req.set) if req.set else (
        _HERE.parent / "shared" / "eval_set.jsonl"
    )
    if not set_path.exists():
        raise HTTPException(status_code=404, detail=f"eval set not found at {set_path}")
    rows = [json.loads(l) for l in set_path.read_text().splitlines() if l.strip()]

    aggregate = eval_mod.run_eval(_service_draft_fn, rows, verbose=False)

    baseline_agg = None
    if req.baseline:
        baseline_path = Path(req.baseline)
        baseline_dict = eval_mod.load_baseline(baseline_path)
        if baseline_dict:
            baseline_agg = eval_mod.Aggregate(
                n_rows=0, n_errors=0,
                faithfulness=baseline_dict.get("faithfulness", 0.0),
                answer_relevance=baseline_dict.get("answer_relevance", 0.0),
                context_precision=baseline_dict.get("context_precision", 0.0),
                context_recall=baseline_dict.get("context_recall", 0.0),
            )

    regressions = eval_mod.run_regression_check(aggregate, baseline_agg, req.threshold)
    md = eval_mod.render_report(aggregate, regressions, req.threshold)

    if req.save_baseline:
        eval_mod.save_baseline(aggregate, Path(req.save_baseline))

    return {
        "ok": True,
        "n_rows": aggregate.n_rows,
        "n_errors": aggregate.n_errors,
        "faithfulness": aggregate.faithfulness,
        "answer_relevance": aggregate.answer_relevance,
        "context_precision": aggregate.context_precision,
        "context_recall": aggregate.context_recall,
        "regressions": [
            {
                "metric": r.metric, "current": r.current, "baseline": r.baseline,
                "delta": r.delta, "threshold": r.threshold, "regressed": r.regressed,
            }
            for r in regressions
        ],
        "any_regressed": any(r.regressed for r in regressions),
        "report_markdown": md,
    }


# ---------------------------------------------------------------------------
# CLI for local testing (uvicorn is the normal entry, but this lets
# `python3 app.py` boot the server in foreground).
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
