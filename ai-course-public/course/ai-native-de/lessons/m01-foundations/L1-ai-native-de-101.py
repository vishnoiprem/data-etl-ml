"""
================================================================
M1 L1  --  AI-Native Data Engineering 101
================================================================

Run:    python3 lessons/m01-foundations/L1-ai-native-de-101.py
Keys:   none (pure stdlib + numpy)

This is the M1 / L1 entry point.  It teaches the differences
between traditional DE and AI-native DE using a single, runnable
example: a 10-row "documents" table is processed by a traditional
ETL pipeline AND by an AI-native pipeline.  The output shows the
extra metadata, the embedding drift signal, and the cost/latency
budget that an AI-native DE must own.

The 10 sections below are the teaching order.  Each section is a
function that prints a labeled block.  Run the file end-to-end
and read the output.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Callable

import numpy as np


# =================================================================
# CONFIG  --  All magic numbers live here
# =================================================================

LESSON_NUMBER = "M1.L1"
WEEKS_PER_MONTH = 4.33
EMBEDDING_DIM = 8            # tiny so the demo is hand-checkable
PRICE_PER_M_TOKENS_USD = 0.15  # assumed gpt-4o-mini-style; mark as assumption
N_DOCS = 10


# =================================================================
# SECTION 1  --  Traditional DE pipeline
# =================================================================

@dataclass
class TraditionalDoc:
    """What a traditional DE pipeline emits."""
    doc_id: str
    text: str
    source: str
    ingested_at: str


def traditional_pipeline(docs: list[dict]) -> list[TraditionalDoc]:
    """Schema-on-read, text only, no model."""
    out: list[TraditionalDoc] = []
    for d in docs:
        out.append(TraditionalDoc(
            doc_id=d["id"],
            text=d["text"],
            source=d["source"],
            ingested_at=datetime.now(timezone.utc).isoformat(),
        ))
    return out


# =================================================================
# SECTION 2  --  AI-native DE pipeline
# =================================================================

@dataclass
class AINativeDoc:
    """What an AI-native DE pipeline emits.

    Adds: model_id, model_version, embedding, embedding_norm,
    prompt_template_version, eval_set_id, content_hash, acl_tags.
    """
    doc_id: str
    text: str
    source: str
    ingested_at: str
    model_id: str
    model_version: str
    embedding: list[float]
    embedding_norm: float
    prompt_template_version: str
    eval_set_id: str
    content_hash: str
    acl_tags: list[str] = field(default_factory=list)


def fake_embed(text: str, dim: int = EMBEDDING_DIM) -> np.ndarray:
    """A deterministic, dependency-free 'embedding'.

    Maps each character to a number in [0,1) and uses the first
    `dim` characters.  This is NOT a real embedding -- it's a
    placeholder that lets us demo the rest of the pipeline
    without a model download.
    """
    rng = np.random.default_rng(seed=sum(ord(c) for c in text) % (2**32))
    return rng.random(dim).astype(np.float32)


def l2_norm(v: np.ndarray) -> float:
    return float(np.sqrt(np.sum(v * v)))


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = l2_norm(a), l2_norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def content_hash(text: str) -> str:
    """Stable 8-char hash (FNV-1a 32-bit, hex-truncated)."""
    h = 0x811c9dc5
    for ch in text.encode("utf-8"):
        h ^= ch
        h = (h * 0x01000193) & 0xFFFFFFFF
    return f"{h:08x}"


def ai_native_pipeline(
    docs: list[dict],
    model_id: str = "fake-embed-v1",
    model_version: str = "1.0.0",
    prompt_template_version: str = "rag-v3",
    eval_set_id: str = "golden-2026-q4",
) -> list[AINativeDoc]:
    """The AI-native version: same inputs, more metadata."""
    out: list[AINativeDoc] = []
    for d in docs:
        v = fake_embed(d["text"])
        out.append(AINativeDoc(
            doc_id=d["id"],
            text=d["text"],
            source=d["source"],
            ingested_at=datetime.now(timezone.utc).isoformat(),
            model_id=model_id,
            model_version=model_version,
            embedding=v.tolist(),
            embedding_norm=l2_norm(v),
            prompt_template_version=prompt_template_version,
            eval_set_id=eval_set_id,
            content_hash=content_hash(d["text"]),
            acl_tags=d.get("acl_tags", []),
        ))
    return out


# =================================================================
# SECTION 3  --  The 7 extra things AI-native DE owns
# =================================================================

SEVEN_EXTRA_THINGS = [
    ("1. Model identity",       "Every embedding has a model_id + version.  You cannot mix v1 and v2 vectors in the same index -- they live in different spaces."),
    ("2. Embedding drift",      "A model upgrade changes cosine distances.  Measure drift on a fixed eval set before rolling out."),
    ("3. Prompt versioning",    "The same retrieval can produce different answers with different prompt templates.  Pin the template version in the trace."),
    ("4. Eval set lineage",     "Every retrieval + generation is scored against a versioned golden set.  No golden set = no idea if you got better or worse."),
    ("5. Content hash",         "Same text from two sources should be deduped.  A stable hash is the dedupe key, not the URL."),
    ("6. ACL tags at ingest",   "If you don't tag at ingest, you'll re-process the corpus every time the permission model changes."),
    ("7. Cost / latency budget","An LLM call is a per-token cost + a per-call latency.  Both must be measured, budgeted, and alerted on."),
]


# =================================================================
# SECTION 4  --  Embedding drift detector
# =================================================================

def embedding_drift(
    old_vec: np.ndarray,
    new_vec: np.ndarray,
) -> dict[str, float]:
    """Quantify how much a single vector has changed between two models.

    Returns a dict with the cosine similarity (1.0 = same direction,
    0.0 = orthogonal, -1.0 = opposite) and the L2 distance.

    Rule of thumb (assumption, not measured): if cosine < 0.7 on
    a fixed eval set, the model upgrade is a meaningful shift and
    you should re-rank the golden set before rolling out.
    """
    return {
        "cosine": cosine_sim(old_vec, new_vec),
        "l2": float(np.sqrt(np.sum((old_vec - new_vec) ** 2))),
    }


# =================================================================
# SECTION 5  --  Cost / latency calculator
# =================================================================

def llm_cost(
    prompt_tokens: int,
    completion_tokens: int,
    price_per_m_tokens_usd: float = PRICE_PER_M_TOKENS_USD,
) -> float:
    """USD cost of a single LLM call.

    Assumes the same price for prompt and completion.  Real APIs
    price them differently (completion is usually 3-5x prompt).
    """
    total = prompt_tokens + completion_tokens
    return total / 1_000_000 * price_per_m_tokens_usd


def llm_latency(
    prompt_tokens: int,
    completion_tokens: int,
    prefill_tok_per_sec: float = 200.0,   # assumption: Apple Silicon M-series
    decode_tok_per_sec: float = 50.0,     # assumption
) -> float:
    """Estimated end-to-end latency in seconds.

    Prefill is the prompt -> KV cache step.  Decode is generating
    the completion one token at a time.  Real numbers depend on
    model, quantization, and batch size.
    """
    prefill = prompt_tokens / prefill_tok_per_sec
    decode = completion_tokens / decode_tok_per_sec
    return prefill + decode


# =================================================================
# SECTION 6  --  Sample documents (10 hand-written)
# =================================================================

SAMPLE_DOCS: list[dict] = [
    {"id": "d01", "text": "Vacation policy: 20 days per year, accrued monthly.", "source": "hr-handbook.md", "acl_tags": ["internal", "hr"]},
    {"id": "d02", "text": "401k match: 100% of the first 3% of salary, 50% of the next 2%.", "source": "hr-handbook.md", "acl_tags": ["internal", "hr"]},
    {"id": "d03", "text": "Onboarding checklist: laptop, badge, SSO, 1:1 with manager in week 1.", "source": "hr-handbook.md", "acl_tags": ["internal", "hr"]},
    {"id": "d04", "text": "Expense policy: submit within 30 days, manager approval required over $100.", "source": "finance-policy.md", "acl_tags": ["internal", "finance"]},
    {"id": "d05", "text": "Vendor onboarding: W-9, COI, NDA, payment terms net-30.", "source": "finance-policy.md", "acl_tags": ["internal", "finance", "vendors"]},
    {"id": "d06", "text": "Q4 supplier SLA: 95% on-time delivery, 48-hour RMA turnaround.", "source": "supplier-q4.md", "acl_tags": ["internal", "suppliers"]},
    {"id": "d07", "text": "Approved supplier list: 47 active, 12 in probation, 3 in remediation.", "source": "supplier-q4.md", "acl_tags": ["internal", "suppliers"]},
    {"id": "d08", "text": "Data retention: customer PII 7 years, financial records 10 years, audit logs 3 years.", "source": "legal-policy.md", "acl_tags": ["confidential", "legal"]},
    {"id": "d09", "text": "Incident response: P1 within 15 min, P2 within 1 hour, P3 within 1 business day.", "source": "ops-runbook.md", "acl_tags": ["internal", "ops"]},
    {"id": "d10", "text": "Quarterly business review: revenue, gross margin, NPS, employee attrition, supplier scorecard.", "source": "ops-runbook.md", "acl_tags": ["internal", "ops"]},
]


# =================================================================
# SECTION 7  --  Demo
# =================================================================

def demo() -> None:
    print("=" * 70)
    print(f"  {LESSON_NUMBER}  --  AI-Native Data Engineering 101")
    print("=" * 70)

    # --- Section 1: traditional pipeline ---
    print("\n  Section 1: Traditional DE pipeline  (text + source + timestamp)")
    print("  " + "-" * 66)
    trad = traditional_pipeline(SAMPLE_DOCS)
    print(f"    Emitted {len(trad)} records.  Each has 4 fields:")
    for k in asdict(trad[0]).keys():
        print(f"      - {k}")

    # --- Section 2: AI-native pipeline ---
    print("\n  Section 2: AI-native DE pipeline  (everything traditional + 7 more)")
    print("  " + "-" * 66)
    ai = ai_native_pipeline(SAMPLE_DOCS)
    print(f"    Emitted {len(ai)} records.  Each has {len(asdict(ai[0]))} fields:")
    for k in asdict(ai[0]).keys():
        print(f"      - {k}")

    # --- Section 3: the 7 extra things ---
    print("\n  Section 3: The 7 things AI-native DE owns that traditional DE doesn't")
    print("  " + "-" * 66)
    for label, desc in SEVEN_EXTRA_THINGS:
        print(f"    {label}")
        print(f"      {desc}")

    # --- Section 4: embedding drift demo ---
    print("\n  Section 4: Embedding drift  (single-doc cosine between v1 and v2)")
    print("  " + "-" * 66)
    v1 = fake_embed(SAMPLE_DOCS[0]["text"])
    # Simulate v2 by adding a fixed perturbation
    v2 = v1 + np.random.default_rng(seed=99).random(EMBEDDING_DIM).astype(np.float32) * 0.5
    d = embedding_drift(v1, v2)
    print(f"    v1 norm = {l2_norm(v1):.3f},  v2 norm = {l2_norm(v2):.3f}")
    print(f"    cosine(v1, v2) = {d['cosine']:.3f}   (1.0 = same, 0.0 = orthogonal)")
    print(f"    L2 distance    = {d['l2']:.3f}")
    print(f"    Threshold rule: cosine < 0.7 => meaningful drift; re-score the golden set.")

    # --- Section 5: cost / latency ---
    print("\n  Section 5: Cost + latency for one LLM call")
    print("  " + "-" * 66)
    p, c = 1200, 250
    cost = llm_cost(p, c)
    lat = llm_latency(p, c)
    print(f"    Prompt tokens     : {p}")
    print(f"    Completion tokens : {c}")
    print(f"    Cost              : ${cost:.5f} per call  (assumes ${PRICE_PER_M_TOKENS_USD}/M tokens)")
    print(f"    Latency (P50 est) : {lat:.2f}s  (prefill {p/200:.2f}s + decode {c/50:.2f}s)")
    print(f"    1000 calls/day    : ${cost*1000:.2f}/day  = ${cost*1000*30:.2f}/mo")

    # --- Section 6: a real retrieval example ---
    print("\n  Section 6: A 1-query retrieval over the 10 docs")
    print("  " + "-" * 66)
    query = "how much vacation do I get per year"
    qv = fake_embed(query)
    scored = [(cosine_sim(qv, np.asarray(d.embedding, dtype=np.float32)), d) for d in ai]
    scored.sort(key=lambda x: x[0], reverse=True)
    print(f"    Query : {query!r}")
    print(f"    Top 3 (by cosine):")
    for s, d in scored[:3]:
        print(f"      {s:.3f}  {d.doc_id}  {d.text[:60]!r}")

    # --- Section 7: the one-page architecture ---
    print("\n  Section 7: One-page architecture (text version, see the notebook for Mermaid)")
    print("  " + "-" * 66)
    print("""
    [Sources]                       [Ingest]                    [Index]
    PDF / HTML / API   -->   parse + chunk + embed  -->  BM25 + vector store
                                                       |
                                                       v
                                                  [Retrieval]
                                                  BM25 + dense + RRF
                                                  + ACL filter
                                                       |
                                                       v
                                                  [Generation]
                                                  prompt assembly + LLM
                                                  + citations + abstain
                                                       |
                                                       v
                                                  [Observability]
                                                  traces + metrics + cost
    """)

    print("=" * 70)
    print("  See L1-ai-native-de-101.ipynb for the runnable version with assertions.")
    print("=" * 70)


# =================================================================
# SECTION 8  --  Unit tests (run with pytest or python -m)
# =================================================================

def test_l2_norm_zero():
    assert l2_norm(np.zeros(EMBEDDING_DIM)) == 0.0

def test_l2_norm_known():
    v = np.array([3.0, 4.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
    assert abs(l2_norm(v) - 5.0) < 1e-5

def test_cosine_identical():
    v = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
    assert abs(cosine_sim(v, v) - 1.0) < 1e-5

def test_cosine_orthogonal():
    a = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
    b = np.array([0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
    assert abs(cosine_sim(a, b)) < 1e-5

def test_content_hash_stable():
    assert content_hash("hello") == content_hash("hello")
    assert content_hash("hello") != content_hash("world")

def test_traditional_pipeline_count():
    out = traditional_pipeline(SAMPLE_DOCS)
    assert len(out) == N_DOCS

def test_ai_native_pipeline_count_and_fields():
    out = ai_native_pipeline(SAMPLE_DOCS)
    assert len(out) == N_DOCS
    for d in out:
        d_dict = asdict(d)
        for required in ("model_id", "model_version", "embedding", "embedding_norm",
                          "prompt_template_version", "eval_set_id", "content_hash", "acl_tags"):
            assert required in d_dict, f"missing {required}"

def test_llm_cost_zero():
    assert llm_cost(0, 0) == 0.0

def test_llm_cost_simple():
    # 1M tokens at $0.15/M = $0.15
    assert abs(llm_cost(500_000, 500_000) - 0.15) < 1e-9

def test_embedding_drift_identical():
    v = np.ones(EMBEDDING_DIM, dtype=np.float32)
    d = embedding_drift(v, v)
    assert abs(d["cosine"] - 1.0) < 1e-5
    assert abs(d["l2"]) < 1e-5


# =================================================================
# ENTRY
# =================================================================

if __name__ == "__main__":
    demo()
