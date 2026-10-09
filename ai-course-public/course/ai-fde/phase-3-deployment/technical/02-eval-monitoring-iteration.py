"""
T2 — Evaluation, monitoring, and iteration (lesson-runnable shim).

This file exists so the lesson is runnable as
`python3 technical/02-eval-monitoring-iteration.py`. It writes a small fake
`usage.jsonl` (so the iteration report has something to read), then calls
`service.eval.render_iteration_report(...)` and prints the result to stdout.

How to run:
    python3 technical/02-eval-monitoring-iteration.py

What you should be able to explain after running it:
- How the 3-loop iteration cadence (online metrics + offline eval + user
  feedback) shows up in a single one-screen markdown report.
- Why the thumbs-up rate is the one number you cannot fake from the eval
  set alone.
- How to read the per-day breakdown to spot a quiet quality drop.

What to read next:
- ../service/eval.py::render_iteration_report    — the report builder (~140 lines)
- ../service/app.py::POST /feedback              — the endpoint that appends to usage.jsonl
- ../service/app.py::GET /metrics                — the Prometheus text exporter
- 02-eval-monitoring-iteration.md                — the lesson itself
"""
from __future__ import annotations

import importlib.util
import json
import random
import sys
import time
from pathlib import Path


def _import_eval_module():
    """Load ../service/eval.py as an importable module so the lesson is
    runnable without installing anything."""
    svc_dir = Path(__file__).parent.parent / "service"
    if str(svc_dir) not in sys.path:
        sys.path.insert(0, str(svc_dir))
    spec = importlib.util.spec_from_file_location("pf_eval", svc_dir / "eval.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["pf_eval"] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_fake_usage_log(path: Path, *, n_days: int = 7) -> int:
    """Write a deterministic fake `usage.jsonl` to disk.

    Mei sends ~150 emails/day. We model 7 days of activity: drafts (mostly
    ok, occasional fallback + error), 8% thumbs-down, 12% thumbs-neutral,
    and 80% thumbs-up. Latency has a long tail: p95 ~ 4s.

    The number we don't fudge is the cost: $0.0005 per draft is what the
    Phase 1 mock LLM reports.
    """
    rng = random.Random(42)  # deterministic output
    now = time.time()
    n_lines = 0

    with path.open("w") as fh:
        for d in range(n_days):
            day_start = now - (n_days - d) * 86400
            n_drafts = rng.randint(120, 175)
            for _ in range(n_drafts):
                ts = day_start + rng.uniform(0, 86400)
                outcome = "ok"
                if rng.random() < 0.005:        # 0.5% error
                    outcome = "error"
                elif rng.random() < 0.01:        # ~1% fallback
                    outcome = "fallback"
                latency_ms = int(rng.gauss(1800, 600))
                latency_ms = max(120, latency_ms)
                if rng.random() < 0.05:          # long tail → p95 ~ 4s
                    latency_ms = int(rng.uniform(3500, 5500))
                e = {
                    "ts": ts,
                    "request_id": f"d{n_lines:04d}",
                    "outcome": outcome,
                    "latency_ms": latency_ms,
                    "model": "mock-deterministic-v1",
                    "cost_usd": 0.0005,
                    "circuit_state": "closed",
                    "user_id": "cs_team",
                }
                fh.write(json.dumps(e) + "\n")
                n_lines += 1

            # Feedback: roughly 30% of drafts get a thumb.
            n_thumbs = int(n_drafts * 0.30)
            for _ in range(n_thumbs):
                ts = day_start + rng.uniform(0, 86400)
                roll = rng.random()
                if roll < 0.798:
                    rating = 1
                    note = "great draft, no changes"
                elif roll < 0.881:
                    rating = -1
                    note = rng.choice([
                        "wrong address",
                        "should mention refund policy",
                        "drafted a refund response — should have escalated",
                        "tone too formal",
                    ])
                else:
                    rating = 0
                    note = "ok, no changes"
                e = {
                    "ts": ts,
                    "request_id": f"fb{n_lines:04d}",
                    "outcome": "feedback",
                    "latency_ms": 0,
                    "model": "n/a",
                    "cost_usd": 0.0,
                    "circuit_state": "closed",
                    "user_id": "cs_team",
                    "feedback_rating": rating,
                    "note": note,
                }
                fh.write(json.dumps(e) + "\n")
                n_lines += 1

    return n_lines


def main() -> int:
    eval_mod = _import_eval_module()

    # 1. Build a fake usage.jsonl next to the lesson.
    out_dir = Path(__file__).parent / "_demo"
    out_dir.mkdir(exist_ok=True)
    usage_path = out_dir / "usage.jsonl"
    n = _write_fake_usage_log(usage_path)
    print("=" * 70)
    print("T2 — 3-loop iteration cadence (online + offline + feedback)")
    print("=" * 70)
    print(f"\nWrote {n} lines of fake activity to {usage_path}")
    print("(Mei: ~150 drafts/day × 7 days, 30% thumbs coverage, ~80% thumbs-up)")

    # 2. Render the iteration report.
    print("\n" + "-" * 70)
    print("render_iteration_report() output:")
    print("-" * 70 + "\n")
    md = eval_mod.render_iteration_report(
        usage_log_path=usage_path,
        since_seconds=7 * 86400.0,
    )
    print(md)

    # 3. Key takeaways.
    print("-" * 70)
    print("Key takeaways:")
    print("-" * 70)
    print(
        "1. The 3 loops (online metrics, offline eval, user feedback) are\n"
        "   joined into a single one-screen markdown report. The FDE reads\n"
        "   this on Monday morning in 60 seconds.\n"
        "2. The thumbs-up rate (79.8%) is the ONE number you cannot derive\n"
        "   from the eval set alone — it comes from /feedback events only.\n"
        "3. The per-day breakdown makes a quiet quality drop visible: a day\n"
        "   with 0 errors but 1 fallback is still a bad day if Mei sent 3\n"
        "   thumbs-down notes about refund policy.\n"
        "4. To re-run on real data, point --usage-log at the service's\n"
        "   actual usage.jsonl (default: ./usage.jsonl next to app.py).\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
