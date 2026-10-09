"""
slm/eval.py — Run the Phase 3 eval set against the SLM and check the
quality bar (≥ 90% of GPT-4o-mini's quality).

What this file does
-------------------
The eval set is the *spec*; the cost model is the *test*.

This script:
  1. Loads the Phase 3 eval set (JSONL)
  2. Runs each row through the SLM (via the serve endpoint, or directly
     via the mock back-end if `--offline` is set)
  3. Computes the 4 RAGAS-style metrics (faithfulness, ansrel,
     context_precision, context_recall) — REUSED from Phase 3's
     `service/eval.py`
  4. Compares the aggregate metrics against the adapter's
     `expected_metrics` (from `ADAPTER.json`) — that's the quality bar
  5. If the SLM meets ≥ 90% of GPT-4o-mini's quality on all 4 metrics,
     prints `✓ SLM meets 90% quality bar`. Otherwise prints `✗` and
     the gap on each metric.

The 90% threshold is encoded in `ADAPTER.json` so a re-trained adapter
with different expected metrics automatically gets a new bar.

Why a separate file
-------------------
The eval is the *test* for the SLM. It's the artifact that tells the
customer (Daniel) that the SLM is good enough to deploy. A separate
file makes the eval reproducible and CI-friendly.

How to run
----------
    # Offline (mock back-end) — the default
    python3 eval.py

    # Against a running serve.py (real SLM)
    python3 eval.py --serve-url http://localhost:8001

    # With a baseline (regression check vs a prior SLM run)
    python3 eval.py --baseline data/baseline_slm.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
import urllib.request
from pathlib import Path
from typing import Optional


_HERE = Path(__file__).parent
_ADAPTER_DIR = _HERE / "adapters" / "pf-drafter-lora"
_ADAPTER_META_PATH = _ADAPTER_DIR / "ADAPTER.json"

# Reuse Phase 3's eval module. _HERE = .../03-distilled-slm/slm/eval.py
# .parent = .../03-distilled-slm/slm
# .parent.parent = .../03-distilled-slm
# .parent.parent.parent = .../phase-4-capstone
# .parent.parent.parent.parent = .../ai-fde  <-- phase-3-deployment lives here
_PHASE3_EVAL_PATH = (
    _HERE.parent.parent.parent.parent
    / "phase-3-deployment" / "service" / "eval.py"
)
_spec = importlib.util.spec_from_file_location("phase3_eval_module", _PHASE3_EVAL_PATH)
phase3_eval = importlib.util.module_from_spec(_spec)  # type: ignore
sys.modules["phase3_eval_module"] = phase3_eval
_spec.loader.exec_module(phase3_eval)


# Default eval set path
DEFAULT_EVAL_SET = (
    _HERE.parent.parent.parent.parent / "phase-3-deployment" / "shared" / "eval_set.jsonl"
)


# ---------------------------------------------------------------------------
# Back-ends for the draft_fn
# ---------------------------------------------------------------------------
def _make_mock_draft_fn():
    """A draft_fn that uses the serve.py mock back-end directly (no HTTP).

    For the eval to produce meaningful context_precision/recall, the mock
    needs to RETRIEVE contexts (not just generate the draft). We reuse
    Phase 3's HybridRetriever via the same importlib trick as above.
    """
    from serve import MockBackend
    from dataset import build_prompt
    backend = MockBackend()

    # Lazy-load Phase 3's retriever (avoid hard dep at import time).
    _svc_path = (
        _HERE.parent.parent.parent.parent / "phase-3-deployment" / "service"
    )
    if str(_svc_path) not in sys.path:
        sys.path.insert(0, str(_svc_path))
    _retriever_path = _svc_path / "retrieval_v2.py"
    _r_spec = importlib.util.spec_from_file_location("phase3_retriever", _retriever_path)
    _retriever_mod = importlib.util.module_from_spec(_r_spec)  # type: ignore
    sys.modules["phase3_retriever"] = _retriever_mod
    _r_spec.loader.exec_module(_retriever_mod)
    retriever = _retriever_mod.HybridRetriever()

    def draft_fn(row: dict) -> dict:
        email = row.get("email", "")
        # Retrieve contexts the same way the drafter does. The retriever
        # takes `k` (not `top_k`) and doesn't have a separate shipment_id
        # arg — shipment_id is implied in the query text.
        try:
            retrieved = retriever.retrieve(email, k=3)
            contexts = [c.text for c in retrieved]
        except Exception as e:
            print(f"  [warn] retriever failed: {e}")
            contexts = row.get("contexts") or []
        prompt = build_prompt(email, contexts)
        text, _ = backend.complete(prompt)
        return {"draft": text, "contexts": contexts}

    return draft_fn


def _make_http_draft_fn(serve_url: str):
    """A draft_fn that calls the running serve.py over HTTP."""
    from dataset import build_prompt

    def draft_fn(row: dict) -> dict:
        prompt = build_prompt(row.get("email", ""), row.get("contexts") or [])
        req = urllib.request.Request(
            f"{serve_url.rstrip('/')}/draft",
            data=json.dumps({
                "email": row.get("email", ""),
                "shipment_id": row.get("expected_shipment_id"),
                "contexts": row.get("contexts") or [],
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        return {"draft": data.get("draft", ""), "contexts": row.get("contexts") or []}

    return draft_fn


# ---------------------------------------------------------------------------
# Eval runner
# ---------------------------------------------------------------------------
def _load_eval_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open() as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _load_adapter_meta() -> dict:
    if not _ADAPTER_META_PATH.exists():
        return {}
    try:
        return json.loads(_ADAPTER_META_PATH.read_text())
    except Exception:
        return {}


def run_slm_eval(
    *,
    serve_url: Optional[str] = None,
    eval_set_path: Optional[Path] = None,
    quality_threshold: float = 0.90,
) -> tuple[phase3_eval.Aggregate, dict]:
    """Run the eval set against the SLM. Returns (aggregate, summary_dict).

    `quality_threshold` is the floor: the SLM must score at least this
    fraction of the adapter's `expected_metrics` on every metric to pass.
    """
    eval_path = Path(eval_set_path) if eval_set_path else DEFAULT_EVAL_SET
    if not eval_path.exists():
        raise FileNotFoundError(f"eval set not found at {eval_path}")
    rows = _load_eval_rows(eval_path)
    print(f"  loaded {len(rows)} eval rows from {eval_path}")

    # Pick the back-end
    if serve_url:
        draft_fn = _make_http_draft_fn(serve_url)
        back_end_name = f"http:{serve_url}"
    else:
        draft_fn = _make_mock_draft_fn()
        back_end_name = "mock"

    print(f"  back-end: {back_end_name}")
    print(f"  running eval ...")
    t0 = time.time()
    agg = phase3_eval.run_eval(draft_fn, rows, verbose=False)
    elapsed = time.time() - t0
    print(f"  done in {elapsed:.1f}s")
    print()
    print(f"  faithfulness       = {agg.faithfulness:.4f}")
    print(f"  answer_relevance   = {agg.answer_relevance:.4f}")
    print(f"  context_precision  = {agg.context_precision:.4f}")
    print(f"  context_recall     = {agg.context_recall:.4f}")

    # Compare to the adapter's expected metrics
    meta = _load_adapter_meta()
    expected = meta.get("expected_metrics", {})
    # If no expected metrics, just report (no pass/fail)
    summary: dict = {
        "back_end": back_end_name,
        "n_rows": len(rows),
        "elapsed_s": round(elapsed, 2),
        "metrics": {
            "faithfulness": agg.faithfulness,
            "answer_relevance": agg.answer_relevance,
            "context_precision": agg.context_precision,
            "context_recall": agg.context_recall,
        },
    }
    if not expected:
        summary["quality_bar"] = None
        summary["pass"] = None
        print()
        print("  (no expected_metrics in ADAPTER.json — skipping quality bar check)")
        return agg, summary

    # The quality bar is the adapter's expected value, scaled by threshold.
    bar = {k: v * quality_threshold for k, v in expected.items() if isinstance(v, (int, float))}
    summary["quality_bar"] = bar
    summary["expected_metrics"] = expected
    summary["threshold"] = quality_threshold
    print()
    print(f"  quality bar (≥ {int(quality_threshold * 100)}% of expected):")
    for k, v in bar.items():
        actual = summary["metrics"].get(k, 0.0)
        ok = "✓" if actual >= v else "✗"
        print(f"    {ok} {k:22s} {actual:.4f}  (bar {v:.4f})")
    # Pass iff all 4 RAGAS-style metrics meet the bar. The
    # `quality_ratio_vs_gpt4o_mini` field is a derived ratio, not a
    # separate metric — we exclude it from the per-metric check.
    RAGAS_KEYS = {"faithfulness", "answer_relevance", "context_precision", "context_recall"}
    passes = all(
        summary["metrics"].get(k, 0.0) >= bar[k]
        for k in RAGAS_KEYS
        if k in bar
    )
    summary["pass"] = passes
    return agg, summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Run the SLM eval set and check the quality bar")
    p.add_argument("--serve-url", default=None,
                   help="URL of a running serve.py (default: use mock back-end directly)")
    p.add_argument("--eval-set", default=None, help="Path to the eval set (default: Phase 3's)")
    p.add_argument("--threshold", type=float, default=0.90,
                   help="Quality bar as a fraction of expected_metrics (default 0.90)")
    p.add_argument("--out", default=None, help="Path to write the eval summary JSON")
    args = p.parse_args(argv)

    print("=" * 60)
    print("SLM eval — PacificFreight drafter")
    print("=" * 60)
    agg, summary = run_slm_eval(
        serve_url=args.serve_url,
        eval_set_path=Path(args.eval_set) if args.eval_set else None,
        quality_threshold=args.threshold,
    )
    print()
    print("=" * 60)
    if summary.get("pass") is True:
        print("✓ SLM MEETS 90% QUALITY BAR")
    elif summary.get("pass") is False:
        print("✗ SLM DOES NOT MEET THE QUALITY BAR")
    else:
        print("(no quality bar configured — eval complete)")
    print("=" * 60)

    if args.out:
        Path(args.out).write_text(json.dumps(summary, indent=2))
        print(f"\n  summary written to {args.out}")
    return 0 if summary.get("pass") is not False else 1


if __name__ == "__main__":
    raise SystemExit(main())
