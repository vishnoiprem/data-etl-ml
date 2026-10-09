"""
service/app.py — PacificFreight Phase 2 FastAPI service (the deliverable).

What this file does
-------------------
Exposes 4 endpoints:

    GET  /health                → liveness probe (returns {"ok": true})
    POST /draft                 → RAG-augmented draft of a customer reply
    GET  /retrieve              → inspect what the retriever would return
    POST /eval                  → run the eval set, return a markdown report

The RAG pipeline (mirrors what Phase 1's CLI does, but over HTTP):
    1. Take the email + (optional) shipment_id.
    2. Retrieve the top-K policy chunks (k=2) and top-K shipment chunks (k=1).
    3. If a shipment_id was given, also look it up in the tracker.
    4. Build a RAG-augmented system prompt.
    5. Call Phase 1's `complete()` (mock by default; real OpenAI if keys set).
    6. Return the draft + the contexts that were used (so the eval harness
       can score it).

How to run
----------
    # From the phase-2-applications/ directory:
    pip install -r service/requirements.txt
    uvicorn service.app:app --host 0.0.0.0 --port 8000

    # Or in Docker:
    docker build -t pf-phase2 service/
    docker run --rm -p 8000:8000 pf-phase2

What to read next
-----------------
- service/rag.py   — the mock vector store + retrieval
- service/eval.py  — the eval harness + regression check
- ../technical/    — the 3 lessons that walk through this code line by line
- ../consulting/   — the 3 lessons that document why each piece is here
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Make sibling modules importable when running as a script or under uvicorn.
_HERE = Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import rag as rag_mod  # noqa: E402
import eval as eval_mod  # noqa: E402


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
# Shared pipeline helpers
# ---------------------------------------------------------------------------
_PF_ID_RE = re.compile(r"PF-\s*(\d{4,5})")
_PF_ID_CLEAN_RE = re.compile(r"PF-\d{4,5}")

_VECTOR_STORE: rag_mod.MockVectorStore | None = None


def _get_vector_store() -> rag_mod.MockVectorStore:
    global _VECTOR_STORE
    if _VECTOR_STORE is None:
        _VECTOR_STORE = rag_mod.MockVectorStore()
    return _VECTOR_STORE


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
    (e.g. "PF - 1003" or "PF  -  1003").
    """
    matches = _PF_ID_CLEAN_RE.findall(text.upper())
    if not matches:
        return None
    # The match already includes the "PF-" prefix; normalize whitespace.
    return re.sub(r"\s+", "", matches[-1])


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


def _draft_pipeline(req: DraftRequest) -> DraftResponse:
    started = time.monotonic()
    store = _get_vector_store()
    shipments = _load_tracker()

    # 1. Determine the shipment_id.
    shipment_id = req.shipment_id or _extract_id(req.email)

    # 2. If we have a shipment_id, look it up.
    shipment: dict | None = None
    if shipment_id:
        shipment = _find_shipment(shipments, shipment_id)

    # 3. Retrieve: top-N policy chunks (whole corpus) + top-N shipment chunks.
    policy_chunks = store.retrieve(req.email, k=req.n_policy_chunks, source_filter="policy")
    shipment_chunks: list[rag_mod.RetrievedChunk] = []
    if shipment_id:
        # Use both the email AND the shipment id as the query so we find
        # the right one even if the email is short.
        q = f"{req.email} {shipment_id}"
        shipment_chunks = store.retrieve(q, k=req.n_shipment_chunks, source_filter="shipment")

    all_chunks = policy_chunks + shipment_chunks

    # 4. Build the RAG prompt.
    # System: persona + retrieved policy chunks (the "what to write like" context)
    rep_name = req.rep or "Linh"
    base = PERSONA_AND_STYLE.format(rep=rep_name)
    system_prompt = rag_mod.build_rag_prompt(
        base_system=base,
        email=req.email,
        shipment=shipment,  # shipment summary goes in the system prompt as retrieved shipment context
        chunks=all_chunks,
    )

    # 5. User prompt: the customer email + a "Shipment in tracker" line.
    #    The "Shipment in tracker: - ID: PF-XXXX" line is the contract
    #    Phase 1's mock backend looks for to return a canned reply. With
    #    a real LLM (PF_LLM_PROVIDER=openai), the line just gives the
    #    model the explicit ID for grounding.
    user_prompt_parts = [f"Customer email:\n{req.email}\n"]
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

    # 6. Call Phase 1's complete().
    result = complete(system=system_prompt, user=user_prompt)
    latency_ms = int((time.monotonic() - started) * 1000)

    return DraftResponse(
        ok=True,
        draft=result.text,
        shipment_id=shipment_id,
        contexts=[
            ContextSnippet(
                id=c.id, source=c.source, score=c.score,
                text=c.text, metadata=c.metadata,
            )
            for c in all_chunks
        ],
        model=result.model,
        provider=result.provider,
        is_mock=result.is_mock,
        cost_usd=result.cost_usd,
        latency_ms=latency_ms,
    )


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="PacificFreight Phase 2 — AI Drafter",
    description=(
        "RAG-augmented customer-service drafter. Wraps Phase 1's CLI "
        "in an HTTP service with retrieval over the style guide and "
        "the shipment tracker. Runs in mock mode by default; set "
        "PF_LLM_PROVIDER=openai + PF_OPENAI_API_KEY to use real OpenAI."
    ),
    version="0.2.0",
)


@app.get("/health")
def health() -> dict:
    """Liveness probe. Returns 200 if the service is up."""
    return {
        "ok": True,
        "service": "pf-phase2",
        "n_chunks_loaded": len(_get_vector_store().chunks),
    }


@app.post("/draft", response_model=DraftResponse)
def draft(req: DraftRequest) -> DraftResponse:
    """Draft a customer-service reply for the given email."""
    return _draft_pipeline(req)


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
    store = _get_vector_store()
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
