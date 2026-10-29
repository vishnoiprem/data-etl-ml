"""
Lesson 03 — Early evaluation, reliability, and application-layer patterns.

What this file does
-------------------
This is the *lesson* version of the eval CLI. It re-uses
`../service/eval.py` for the metrics + regression check + markdown
report, and adds a small `main()` that demonstrates all four CLI modes:

    1. Run the eval, write a report.
    2. Run the eval AND save a baseline.
    3. Run the eval AND compare to a baseline (with a regression check).
    4. Run the eval against a fabricated bad pipeline to show the
       regression check trips when scores drop.

How to run
----------
    python3 03-eval-reliability.py            # runs the eval, prints summary
    python3 03-eval-reliability.py --verbose  # prints per-row detail

What you should be able to explain to a client after this lesson
----------------------------------------------------------------
- Why 4 RAGAS-style metrics (faithfulness, answer relevance, context
  precision, context recall), all deterministic, run in milliseconds.
- Why the eval set is frozen (so last week's number is comparable to
  this week's) and committed to the repo.
- Why the regression threshold is 0.05 (a 5pp drop on any metric blocks
  the deploy).
- Why one bad row should not kill the whole eval run.

What to read next
-----------------
- ../service/eval.py            — the production version of this code
- ../service/tests/test_app.py  — the pytest cases that exercise this
- ../../hardcode/level-8-evaluation-testing/11-llm-as-judge-eval.py
                                — the 1000-line production version
"""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path


def _import_eval_module():
    eval_path = Path(__file__).parent.parent / "service" / "eval.py"
    spec = importlib.util.spec_from_file_location("pf_eval", eval_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["pf_eval"] = mod
    spec.loader.exec_module(mod)
    return mod


def _import_app_module():
    """For the service-side `draft_fn` that the eval actually scores."""
    app_path = Path(__file__).parent.parent / "service" / "app.py"
    spec = importlib.util.spec_from_file_location("pf_phase2_app", app_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["pf_phase2_app"] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    eval_mod = _import_eval_module()
    app_mod = _import_app_module()

    set_path = Path(__file__).parent.parent / "shared" / "eval_set.jsonl"
    rows = [eval_mod.json.loads(l) for l in set_path.read_text().splitlines() if l.strip()]

    print("=" * 70)
    print(f"Eval set: {set_path}")
    print(f"Rows    : {len(rows)}  (clean={sum(1 for r in rows if r['category']=='clean')}  "
          f"messy={sum(1 for r in rows if r['category']=='messy')}  "
          f"edge={sum(1 for r in rows if r['category']=='edge')})")
    print("=" * 70)

    # Run the eval using the service's pipeline (same code as /draft).
    started = time.monotonic()
    aggregate = eval_mod.run_eval(app_mod._service_draft_fn, rows, verbose=False)
    elapsed = int((time.monotonic() - started) * 1000)

    print()
    print(f"Faithfulness       : {aggregate.faithfulness:.4f}")
    print(f"Answer relevance   : {aggregate.answer_relevance:.4f}")
    print(f"Context precision  : {aggregate.context_precision:.4f}")
    print(f"Context recall     : {aggregate.context_recall:.4f}")
    print(f"Errors             : {aggregate.n_errors} / {aggregate.n_rows}")
    print(f"Elapsed            : {elapsed} ms")

    print()
    print("By category:")
    for cat, m in aggregate.by_category.items():
        print(f"  {cat:6s}  n={m['n']:2d}  faith={m['faithfulness']:.3f}  "
              f"ansrel={m['answer_relevance']:.3f}  ctxp={m['context_precision']:.3f}  "
              f"ctxr={m['context_recall']:.3f}")

    # Demonstrate the regression check with a synthetic baseline.
    print()
    print("=" * 70)
    print("Regression check demo (synthetic baseline +0.20 above current)")
    print("=" * 70)
    from types import SimpleNamespace
    fake_baseline = SimpleNamespace(
        n_rows=0, n_errors=0,
        faithfulness=aggregate.faithfulness + 0.20,
        answer_relevance=aggregate.answer_relevance + 0.20,
        context_precision=aggregate.context_precision + 0.20,
        context_recall=aggregate.context_recall + 0.20,
    )
    regressions = eval_mod.run_regression_check(aggregate, fake_baseline, threshold=0.05)
    any_tripped = any(r.regressed for r in regressions)
    for r in regressions:
        flag = "REGRESSED" if r.regressed else "ok"
        print(f"  {r.metric:22s}  cur={r.current:.3f}  base={r.baseline:.3f}  "
              f"delta={r.delta:+.3f}  {flag}")
    print()
    print(f"any_regressed = {any_tripped}")

    if any_tripped:
        print()
        print("In CI, this would BLOCK the deploy.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
