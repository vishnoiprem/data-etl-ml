"""apex-rag-omni — FastAPI backend.

Endpoints (per staff-level spec):
  GET  /traces?day=YYYY-MM-DD&cursor=trace_NNNNNN&limit=50
       Cursor pagination, O(1) not OFFSET O(N). Uses (day, trace_id) index.
       Requires X-API-Key.
  POST /query
       hybrid_search() across 10 Qdrant shards -> rerank Top8 -> grounded
       answer with evidence_json (anti-hallucination contract).
       Requires X-API-Key. query body capped at APEX_MAX_QUERY_CHARS.
  POST /documents (multipart: collection + file), GET /documents, DELETE /documents/{id}
       Upload .txt/.md/.csv/.pdf into a collection; searchable immediately.
  POST /query/stream
       Same pipeline as /query, delivered as Server-Sent Events so the
       UI can render tokens as they are produced (ChatGPT-style):
       `meta` -> `sources` -> `token`* -> `done` (or `error`).
  POST /feedback
       Optimistic update. Adds to gold dataset for LLM-as-judge.
       Requires X-API-Key.
  GET  /eval
       Returns the latest eval report from the real harness run
       (Postgres if APEX_POSTGRES_URL is set, JSONL fallback otherwise).
       Requires X-API-Key.
  GET  /healthz
       Static liveness probe. K8s livenessProbe target. Open.
  GET  /readyz
       Async readiness probe — pings Qdrant and ES with a 500ms timeout.
       Returns 503 if any dep is unreachable. K8s readinessProbe target.
       Open.
  GET  /health
       Backward-compat alias for /healthz. Deprecated.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import (
    Depends, FastAPI, File, Form, HTTPException, Query, UploadFile, status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from . import audit_queue, document_store, explain as explain_mod, llm
from .local_index import invalidate as _invalidate_index
from .apex_answerer import (
    EvidenceJSON as AnswererEvidenceJSON, grounded_answer, stream_tokens,
)
from .apex_audit import recent_traces
from .apex_eval import empty_report
from .apex_retriever import (
    InvalidFilterKeys, hybrid_search, rerank_top_k, validate_filter_keys,
)
from .hallucination import check_answer
from .textproc import detect_lang
from .sanitize import redact_pii, sanitize_output, sanitize_query
from .auth import safe_key_for_log, verify_api_key
from .eval_store import PRODUCTION_TARGETS, latest_report
from .readyz import check_dependencies as _check_dependencies, is_ready as _is_ready
from .settings import Settings, get_settings

logger = logging.getLogger("apex")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init the audit queue and start the drain task.
    Shutdown: stop the drain and flush remaining items with a 5s deadline.
    """
    settings = get_settings()
    audit_queue.init_audit_queue(
        maxsize=settings.audit_queue_max,
    )
    await audit_queue.start_drain()
    logger.info(
        "apex startup: api_keys=%d qdrant=%s es=%s audit_queue_max=%d",
        len(settings.api_keys_list), settings.qdrant_url, settings.es_url,
        settings.audit_queue_max,
    )
    try:
        yield
    finally:
        await audit_queue.stop_drain()
        await audit_queue.flush_on_shutdown(timeout=5.0)
        logger.info("apex shutdown complete")


app = FastAPI(
    title="apex-rag-omni",
    version="0.2.0",
    description=(
        "Sovereign RAG platform. 1 API, 3 collections, 100M docs. "
        "Auth: X-API-Key. Production-grade."
    ),
    lifespan=lifespan,
)

# CORS is wired AFTER app creation so we can read settings. We never
# use `allow_origins=["*"]` — that would let any browser call us with
# the user's API key in the request body.
_settings_for_cors = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip() for o in _settings_for_cors.frontend_origin.split(",") if o.strip()
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["X-API-Key", "Content-Type"],
)


# ---------- Pydantic schemas ----------


Collection = Literal["hr_policies", "tech_docs", "product_docs"]


class QueryRequest(BaseModel):
    collection: Collection
    # Cap the query size. 10 MB queries are a 403 risk.
    query: str = Field(..., min_length=1, max_length=2_000)
    top_k: int = Field(default=8, ge=1, le=50)
    # Filters are validated against a per-collection allowlist in the
    # route layer before reaching Qdrant. The dict shape is preserved
    # here for OpenAPI clarity.
    filters: dict[str, str] = Field(default_factory=dict)
    # Ask the configured (free) model to re-explain the verified answer in
    # plain words. Only honoured by /query/stream.
    explain: bool = False


class EvidenceSpan(BaseModel):
    doc_id: str
    offset: int
    text: str
    score: float


class EvidenceJSON(BaseModel):
    query: str
    collection: Collection
    answer: str
    spans: list[EvidenceSpan]
    refused: bool = False
    refusal_reason: str | None = None


class QueryResponse(BaseModel):
    trace_id: str
    evidence: AnswererEvidenceJSON
    timing_ms: dict[str, float]


class FeedbackRequest(BaseModel):
    trace_id: str = Field(..., min_length=1, max_length=64)
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2_000)


class TraceSummary(BaseModel):
    trace_id: str
    day: str
    ts: str
    collection: Collection
    query: str
    latency_ms: float
    refused: bool
    rating: int | None = None


class TracesResponse(BaseModel):
    traces: list[TraceSummary]
    next_cursor: str | None
    has_more: bool


# ---------- Endpoints ----------


@app.get("/healthz", include_in_schema=False)
async def healthz() -> dict:
    """Liveness probe. Static, no I/O. Open to K8s."""
    return {"status": "ok"}


@app.get("/readyz", include_in_schema=False)
async def readyz(settings: Settings = Depends(get_settings)) -> dict:
    """Readiness probe. Pings Qdrant + ES concurrently with a 500ms timeout.

    Returns 503 if any dependency is unreachable. The body always
    includes per-dep status so K8s logs and the operator can see which
    one is red.
    """
    statuses = await _check_dependencies(settings)
    ready = _is_ready(statuses)
    if not ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "deps": statuses},
        )
    return {"status": "ready", "deps": statuses}


@app.get("/health", include_in_schema=False, deprecated=True)
async def health_deprecated() -> dict:
    """Deprecated alias for /healthz. Kept for backward compatibility
    with the frontend if it's already wired. Will be removed in v0.4.
    """
    return {"status": "ok"}


@app.get("/traces", response_model=TracesResponse)
async def get_traces(
    day: str = Query(..., description="Day in YYYY-MM-DD format"),
    cursor: str | None = Query(None, description="Last trace_id from prev page"),
    limit: int = Query(50, ge=1, le=500),
    api_key: str = Depends(verify_api_key),
    settings: Settings = Depends(get_settings),
) -> TracesResponse:
    """Cursor-paginated trace log. O(1) per page (not OFFSET O(N)).

    Uses an index on (day, trace_id) so the query is a range scan with
    keyset pagination. Works at 100M traces without skipping or
    duplicating — no OFFSET, no page-N.
    """
    after_id = cursor or ""
    rows = recent_traces(day=day, after_id=after_id, limit=limit + 1)
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = rows[-1].trace_id if has_more and rows else None
    await audit_queue.enqueue_audit(
        trace_id=f"trace-list-{uuid.uuid4().hex[:8]}",
        kind="trace_list",
        payload={
            "day": day, "limit": limit, "n_returned": len(rows),
            "actor_prefix": safe_key_for_log(api_key),
        },
    )
    return TracesResponse(
        traces=[TraceSummary(**r) for r in rows],
        next_cursor=next_cursor,
        has_more=has_more,
    )


def new_trace_id() -> str:
    """Time-ordered UUIDv7-style id: 48-bit ms timestamp + random.

    Keyset pagination on trace_id is only correct if ids sort by creation
    time; random uuid4s let new traces land *before* an existing cursor and
    be skipped forever.
    """
    ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand = uuid.uuid4().int & ((1 << 74) - 1)
    n = (ms << 80) | (0x7 << 76) | ((rand >> 62) << 64) | (0b10 << 62) | (rand & ((1 << 62) - 1))
    return str(uuid.UUID(int=n))


def _run_pipeline(req: QueryRequest):
    """sanitize -> hybrid_search -> rerank -> grounded answer -> hallucination
    gate -> output sanitization, with REAL per-stage timings.

    Returns (candidates, top, evidence, timing_ms, audit_flags). Raises
    HTTPException(400) on an invalid filter key, before any expensive work.
    """
    try:
        validate_filter_keys(req.collection, req.filters)
    except InvalidFilterKeys as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    t0 = time.perf_counter()
    sq = sanitize_query(req.query)
    flags = list(sq.flags)
    if sq.injection:
        # Never let a suspected injection steer retrieval or generation.
        ej = AnswererEvidenceJSON(
            query=sq.text, collection=req.collection, answer="", spans=[],
            refused=True,
            refusal_reason="Request looks like a prompt-injection attempt",
            flags=flags,
        )
        t = (time.perf_counter() - t0) * 1000
        return [], [], ej, {"hybrid_ms": 0.0, "rerank_ms": 0.0,
                            "answer_ms": 0.0, "total_ms": t}, flags
    if not sq.text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Query is empty after sanitization.")
    # hybrid_search across 10 shards (BM25 + dense vector, RRF fusion)
    candidates = hybrid_search(
        collection=req.collection, query=sq.text,
        top_k=req.top_k * 4,  # over-fetch for reranker
        filters=req.filters,
    )
    t1 = time.perf_counter()
    top = rerank_top_k(candidates, k=req.top_k)
    t2 = time.perf_counter()
    ej, _ = grounded_answer(sq.text, req.collection, top)
    if not ej.refused:
        rep = check_answer(ej.answer, [s.text for s in ej.spans])
        ej.groundedness = rep.groundedness
        if rep.verdict == "fail":
            flags.append("hallucination_blocked")
            ej = AnswererEvidenceJSON(
                query=sq.text, collection=req.collection, answer="", spans=[],
                refused=True,
                refusal_reason="Answer failed the hallucination check: "
                               + "; ".join(rep.problems[:2] or ["low evidence support"]),
                groundedness=rep.groundedness,
            )
        elif rep.verdict == "warn":
            flags.append("low_groundedness")
    # Defence in depth: nothing markup-like leaves the API.
    ej.answer = sanitize_output(ej.answer)
    for sp in ej.spans:
        sp.text = sanitize_output(sp.text)
        sp.title = sanitize_output(sp.title)
    ej.flags = flags
    t3 = time.perf_counter()
    timing = {
        "hybrid_ms": (t1 - t0) * 1000,
        "rerank_ms": (t2 - t1) * 1000,
        "answer_ms": (t3 - t2) * 1000,
        "total_ms": (t3 - t0) * 1000,
    }
    return candidates, top, ej, timing, flags


async def _run_pipeline_i18n(req, settings):
    """_run_pipeline plus cross-language rescue: if a non-English question finds
    nothing, translate it to English with the configured model and retry, so a
    Thai/Vietnamese/Chinese/Hindi question can still reach English documents.
    The answer text is then the (English) source sentences; the plain-words
    explanation can be written in the user's own language."""
    result = _run_pipeline(req)
    _, _, ej, timing, flags = result
    lang = detect_lang(ej.query or req.query)
    if not ej.refused or "prompt_injection" in flags or lang == "en" or not llm.is_configured(settings):
        return result
    t0 = time.perf_counter()
    alt = await explain_mod.translate_query(ej.query, settings)
    translate_ms = (time.perf_counter() - t0) * 1000
    if not alt:
        return result
    cands2, top2, ej2, timing2, flags2 = _run_pipeline(req.model_copy(update={"query": alt}))
    if ej2.refused:
        return result
    ej2.query = ej.query  # keep the user's own words
    flags2 = list(flags2) + ["translated_query"]
    ej2.flags = flags2
    timing2["translate_ms"] = translate_ms
    timing2["total_ms"] += translate_ms + timing["total_ms"]
    return cands2, top2, ej2, timing2, flags2


async def _audit_query(trace_id, req, candidates, top, ej, timing, api_key, flags=()):
    safe_q, pii = redact_pii(ej.query or "")
    await audit_queue.enqueue_audit(
        trace_id=trace_id, kind="query", payload={
            "collection": req.collection, "query": safe_q,
            "pii_redacted": pii, "flags": list(flags),
            "groundedness": ej.groundedness,
            "n_candidates": len(candidates), "n_returned": len(top),
            "refused": ej.refused, "elapsed_ms": timing["total_ms"],
            "actor_prefix": safe_key_for_log(api_key),
        },
    )


@app.post("/query", response_model=QueryResponse)
async def post_query(
    req: QueryRequest,
    api_key: str = Depends(verify_api_key),
    settings: Settings = Depends(get_settings),
) -> QueryResponse:
    """Grounded RAG query. hybrid_search -> rerank -> grounded answer.

    Body limits: query <= 2000 chars, filters keys are validated against
    a per-collection allowlist. Timings are measured, not estimated.
    """
    trace_id = new_trace_id()
    candidates, top, ej, timing, flags = await _run_pipeline_i18n(req, settings)
    await _audit_query(trace_id, req, candidates, top, ej, timing, api_key, flags)
    return QueryResponse(trace_id=trace_id, evidence=ej, timing_ms=timing)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.get("/capabilities")
async def capabilities(
    api_key: str = Depends(verify_api_key),
    settings: Settings = Depends(get_settings),
) -> dict:
    """What the UI may offer. `explain` is true only when a model endpoint is configured."""
    ok = llm.is_configured(settings)
    local = settings.model_gateway_url.startswith(
        ("http://localhost", "http://127.", "http://host.docker.internal", "http://ollama"))
    return {"explain": ok, "model": settings.model_name if ok else None,
            "model_is_local": ok and local}


@app.post("/query/stream")
async def post_query_stream(
    req: QueryRequest,
    api_key: str = Depends(verify_api_key),
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    """SSE variant of /query. Event order:

      meta    {trace_id}
      sources {spans, refused, refusal_reason}   (citations land first so
                                                  chips are clickable while
                                                  the answer types out)
      token   {delta}                            (0..n)
      done    {trace_id, evidence, timing_ms}    (final, authoritative)
      error   {message}                          (instead of done on failure)

    The filter-key check runs before the stream opens so a bad request is
    a real HTTP 400, not an in-band error event.
    """
    trace_id = new_trace_id()
    candidates, top, ej, timing, flags = await _run_pipeline_i18n(req, settings)

    async def gen():
        try:
            yield _sse("meta", {"trace_id": trace_id})
            yield _sse("sources", {
                "spans": [s.model_dump() for s in ej.spans],
                "refused": ej.refused,
                "refusal_reason": ej.refusal_reason,
                "flags": ej.flags,
            })
            for delta in stream_tokens(ej.answer):
                yield _sse("token", {"delta": delta})
            await _audit_query(trace_id, req, candidates, top, ej, timing, api_key, flags)
            yield _sse("done", {
                "trace_id": trace_id,
                "evidence": ej.model_dump(),
                "timing_ms": timing,
            })
            if req.explain and not ej.refused:
                async for chunk in _explain_events(trace_id, req, ej, settings, api_key):
                    yield chunk
        except Exception as exc:  # noqa: BLE001 — surfaced to the client
            logger.exception("stream failed trace_id=%s", trace_id)
            yield _sse("error", {"message": str(exc)})

    return StreamingResponse(
        gen(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _explain_events(trace_id, req, ej, settings, api_key):
    """Stream a plain-language explanation of a verified answer, then verify it.

    Events: explain_start | explain_token* | explain_end{verdict,text,...} |
            explain_skipped{reason} | explain_error{message}
    The UI shows tokens as they arrive but treats `explain_end` as the
    authority: on verdict=fail the text is discarded.
    """
    if not llm.is_configured(settings):
        yield _sse("explain_skipped", {"reason": "no_model_configured"})
        return
    spans = [s.model_dump() for s in ej.spans]
    lang = detect_lang(ej.query)
    msgs = explain_mod.build_messages(ej.query, ej.answer, spans, lang)
    yield _sse("explain_start", {"model": settings.model_name})
    buf = ""
    try:
        async for delta in llm.stream_chat(msgs, settings):
            buf += delta
            if len(buf) > explain_mod.MAX_CHARS * 2:
                break  # runaway generation; verification below will fail it
            yield _sse("explain_token", {"delta": delta})
    except llm.LLMError as exc:
        logger.warning("explain failed trace_id=%s: %s", trace_id, exc)
        yield _sse("explain_error", {"message": str(exc)})
        return
    spans_text = [s["text"] for s in spans]
    text = explain_mod.clean_explanation(buf)
    text = explain_mod.repair_citations(text, spans_text)
    cross = explain_mod.is_cross_lingual(text, spans_text)
    verdict, rep, reason = explain_mod.verify_explanation(text, spans_text, cross)
    if cross and verdict != "fail":
        # Wording can't be compared across languages directly, so translate the
        # explanation back to English and check THAT against the sources. A
        # garbled or invented explanation does not survive the round trip.
        back = await explain_mod.back_translate(text, settings)
        if back:
            v2, rep2, why2 = explain_mod.verify_explanation(back, spans_text, cross_lingual=False)
            if v2 == "fail":
                verdict, reason = "fail", f"back-translation does not match the sources ({why2})"
            else:
                verdict = v2
                reason = "translated: verified by back-translation"
                rep = rep2 or rep
    await audit_queue.enqueue_audit(
        trace_id=trace_id, kind="explain", payload={
            "verdict": verdict, "reason": reason, "model": settings.model_name,
            "groundedness": rep.groundedness if rep else None,
            "actor_prefix": safe_key_for_log(api_key),
        },
    )
    yield _sse("explain_end", {
        "verdict": verdict, "reason": reason, "model": settings.model_name,
        "groundedness": rep.groundedness if rep else None,
        "translated": cross, "lang": lang,
        "text": text if verdict != "fail" else "",
    })


@app.post("/documents", status_code=status.HTTP_201_CREATED)
async def upload_document(
    collection: Collection = Form(...),
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Upload a .txt/.md/.csv/.pdf into a collection. It is extracted,
    cleaned, chunked into citable passages, de-duplicated by SHA-256, and
    searchable immediately. Returns PII / injection-like warnings so the
    uploader can decide whether to keep it."""
    data = await file.read(settings.max_upload_bytes + 1)
    try:
        info = document_store.add_document(collection, file.filename or "document", data)
    except document_store.UploadError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc))
    _invalidate_index(collection)
    await audit_queue.enqueue_audit(
        trace_id=f"upload-{info['doc_id']}", kind="upload", payload={
            "collection": collection, "filename": info["filename"],
            "chunks": info["chunks"], "pii_detected": info["pii_detected"],
            "injection_like": info["injection_like"],
            "actor_prefix": safe_key_for_log(api_key),
        },
    )
    return info


@app.get("/documents")
async def list_documents(
    collection: Collection = Query(...),
    api_key: str = Depends(verify_api_key),
) -> dict:
    from .corpus import CORPUS
    return {
        "collection": collection,
        "builtin_passages": len(CORPUS[collection]),
        "documents": document_store.list_documents(collection),
    }


@app.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    collection: Collection = Query(...),
    api_key: str = Depends(verify_api_key),
) -> dict:
    if not document_store.delete_document(collection, doc_id):
        raise HTTPException(status_code=404, detail="No such uploaded document.")
    _invalidate_index(collection)
    await audit_queue.enqueue_audit(
        trace_id=f"delete-{doc_id}", kind="delete_document",
        payload={"collection": collection, "actor_prefix": safe_key_for_log(api_key)},
    )
    return {"ok": True, "doc_id": doc_id}


@app.post("/feedback")
async def post_feedback(
    req: FeedbackRequest,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Optimistic feedback. Land instantly, reconcile in background.

    Adds the (query, evidence, rating) tuple to the gold dataset for
    LLM-as-judge calibration. The user rating is the ground truth for
    whether the answer was actually useful.
    """
    await audit_queue.enqueue_audit(
        trace_id=req.trace_id, kind="feedback", payload={
            "rating": req.rating,
            "comment": redact_pii(req.comment)[0] if req.comment else None,
            "actor_prefix": safe_key_for_log(api_key),
        },
    )
    return {"ok": True, "trace_id": req.trace_id}


@app.get("/eval")
async def get_eval(
    api_key: str = Depends(verify_api_key),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Latest eval report from the real harness run.

    Returns 200 with the most recent report from Postgres (if configured)
    or the JSONL fallback in `eval/reports/`. If no reports exist yet,
    returns an empty report with `n_samples: 0` so the operator can
    distinguish "no runs" from "system is broken".

    Production targets are returned as a sibling field, not as the
    report itself — the previous version of this endpoint returned
    the targets as the data, which was theater.
    """
    report = latest_report(settings)
    if report is None:
        report = empty_report()
    return {
        "report": report.to_dict(),
        "production_targets": PRODUCTION_TARGETS,
        "meets_targets": _meets_targets(report),
    }


def _meets_targets(report) -> dict[str, bool]:
    """Per-metric pass/fail against the production targets."""
    if report.n_samples == 0:
        return {}
    return {
        "recall_at_8": report.recall_at_8 >= PRODUCTION_TARGETS["recall_at_8"],
        "ndcg_at_8": report.ndcg_at_8 >= PRODUCTION_TARGETS["ndcg_at_8"],
        "p95_latency_ms": report.p95_latency_ms <= PRODUCTION_TARGETS["p95_latency_ms"],
        "judge_groundedness": report.judge_groundedness >= PRODUCTION_TARGETS["judge_groundedness"],
        "judge_hallucination": report.judge_hallucination <= PRODUCTION_TARGETS["judge_hallucination"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
