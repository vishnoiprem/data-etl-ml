"""
T1 — Advanced retrieval and RAG (lesson-runnable shim).

This file exists so the lesson is runnable as `python3 technical/01-advanced-retrieval.py`.
It re-exports the service code and adds a small `main()` that demos the
hybrid retriever side-by-side against pure-BM25, pure-dense, and the RRF
fusion.

How to run:
    python3 technical/01-advanced-retrieval.py

What you should be able to explain after running it:
- Why hybrid (BM25 + dense + RRF) outscores either alone for paraphrase-y queries.
- Why RRF is parameter-free and empirically as good as tuned convex combinations.
- When to add a cross-encoder reranker (eval shows top-1 wrong on 5+ rows/week).

What to read next:
- ../service/retrieval_v2.py            — the HybridRetriever (250 lines)
- ../service/app.py                    — the 5 endpoints that use it
- ../../hardcode/level-4-rag-pipelines/07-hybrid-search-rag.py
                                       — the 1300-line production version
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _import_service_module():
    """Load ../service/retrieval_v2.py as an importable module.

    Adds the service dir to sys.path FIRST so retrieval_v2's relative
    `from rag import ...` resolves.
    """
    svc_dir = Path(__file__).parent.parent / "service"
    if str(svc_dir) not in sys.path:
        sys.path.insert(0, str(svc_dir))
    spec = importlib.util.spec_from_file_location(
        "pf_retrieval_v2", svc_dir / "retrieval_v2.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["pf_retrieval_v2"] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    rv2 = _import_service_module()

    print("=" * 70)
    print("T1 — Advanced retrieval: BM25 + dense + RRF side-by-side")
    print("=" * 70)

    hr = rv2.HybridRetriever()
    print(f"\nLoaded {hr.n_chunks} chunks ({hr.bm25.n_docs} in BM25, {hr.dense.n_docs} in dense)")

    queries = [
        "customs duty payment",        # PF-1003 expected — exact term match
        "stuck at customs in Vietnam",  # paraphrase + entity — BM25 wins
        "refund my money",              # policy-only
    ]
    for q in queries:
        print(f"\n--- query={q!r} ---")
        c = hr.compare(q, k=3)
        for label, hits in c.items():
            if not hits:
                print(f"  {label:8s}  (no hits)")
                continue
            for did, s in hits:
                print(f"  {label:8s}  {did:30s}  {s:.4f}")

    # The paraphrase test — flag the win.
    print("\n--- key takeaway ---")
    c = hr.compare("stuck at customs in Vietnam", k=1)
    bm25_top = c["bm25"][0][0] if c["bm25"] else None
    dense_top = c["dense"][0][0] if c["dense"] else None
    hybrid_top = c["hybrid"][0][0] if c["hybrid"] else None
    print(f"  BM25 top:    {bm25_top}    (Vietnam lane, caught 'Vietnam')")
    print(f"  Dense top:   {dense_top}    (Tokyo lane, paraphrased 'stuck')")
    print(f"  Hybrid top:  {hybrid_top}  ← RRF promotes the BM25 consensus")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
