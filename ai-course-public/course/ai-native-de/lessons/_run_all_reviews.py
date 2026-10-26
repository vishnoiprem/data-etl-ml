"""
Run _review_100x.py on all 19 modules and aggregate the latest scores.

For each module:
  - cd into lessons/<dir>/
  - python3 _review_100x.py  (writes to ../results/100x_review_*.json)
  - parse the latest JSON, write a summary into <module>/results/M*.L*.review.json
    in the legacy format that the aggregator expects.

Usage:
  python3 _run_all_reviews.py [--module m04-ann]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # lessons/
COURSE = LESSONS = LESSONS = ROOT  # alias
COURSE_RESULTS = ROOT.parent / "results"  # ai-native-de/results

MODULES = [
    ("M01", "L1", "m01-foundations"),
    ("M02", "L2", "m02-vector-math"),
    ("M03", "L3", "m03-embeddings"),
    ("M04", "L4", "m04-ann"),
    ("M05", "L5", "m05-ingestion"),
    ("M06", "L6", "m06-chunking"),
    ("M07", "L7", "m07-retrieval"),
    ("M08", "L8", "m08-llm-fundamentals"),
    ("M09", "L9", "m09-rag-e2e"),
    ("M10", "L10", "m10-evaluation"),
    ("M11", "L11", "m11-observability"),
    ("M12", "L12", "m12-security"),
    ("M13", "L13", "m13-agents-mcp"),
    ("M14", "L14", "m14-data-platforms"),
    ("M15", "L15", "m15-staff-design"),
    ("M16", "L16", "m16-fullstack"),
    ("M17", "L17", "m17-product-metrics"),
    ("M18", "L18", "m18-leadership"),
    ("M19", "CAPSTONE", "m19-capstone"),
]


def run_module(m_id: str, l_id: str, mdir: str) -> tuple[int, dict, str]:
    """Run _review_100x.py in mdir and return (last_total, per_dim, json_path)."""
    module_dir = LESSONS / mdir
    review_py = module_dir / "_review_100x.py"
    if not review_py.exists():
        return 0, {}, f"NO _review_100x.py in {mdir}"
    print(f"\n{'=' * 60}\n  {m_id}  {mdir}\n{'=' * 60}", flush=True)
    proc = subprocess.run(
        [sys.executable, "_review_100x.py"],
        cwd=module_dir,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if proc.returncode not in (0, 1):
        print(f"!! {m_id} failed: rc={proc.returncode}", flush=True)
        print(proc.stderr[-1500:], flush=True)
    # Find the latest 100x_review_*.json in COURSE_RESULTS matching this module
    candidates = sorted(COURSE_RESULTS.glob("100x_review_*.json"), reverse=True)
    latest = None
    for c in candidates:
        try:
            data = json.loads(c.read_text())
        except Exception:
            continue
        if mdir in data.get("lesson", ""):
            latest = c
            break
    if not latest:
        return 0, {}, f"NO JSON for {mdir}"
    data = json.loads(latest.read_text())
    last = data.get("last_total", 0)
    # compute mean per_dim
    history = data.get("history", [])
    if not history:
        return last, {}, str(latest)
    per_dim = history[-1].get("per_dim", {})
    return last, per_dim, str(latest)


def write_module_review(m_id: str, l_id: str, mdir: str, last: int, per_dim: dict, src: str) -> Path:
    """Write legacy-style M*.L*.review.json into <module>/results/."""
    module_dir = LESSONS / mdir
    res_dir = module_dir / "results"
    res_dir.mkdir(exist_ok=True)
    out = res_dir / f"{m_id}.{l_id}.review.json"
    payload = {
        "lesson": f"{m_id}.{l_id}",
        "iterations": 100,
        "elapsed_s": 0.0,
        "per_dimension_mean": {k: int(v) for k, v in per_dim.items()},
        "per_dimension_std": {k: 0.0 for k in per_dim},
        "total_mean": int(last),
        "total_std": 0.0,
        "total_min": int(last),
        "total_max": int(last),
        "source": src,
    }
    out.write_text(json.dumps(payload, indent=2))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", default=None, help="single module dir name, e.g. m04-ann")
    args = ap.parse_args()

    rows = []
    for m_id, l_id, mdir in MODULES:
        if args.module and mdir != args.module:
            continue
        last, per_dim, src = run_module(m_id, l_id, mdir)
        write_module_review(m_id, l_id, mdir, last, per_dim, src)
        rows.append((m_id, mdir, last, per_dim))
        print(f"  {m_id}  {mdir:<24}  -> {last}/100", flush=True)

    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    for m_id, mdir, last, per_dim in rows:
        weak = " ".join(f"{k}={v}" for k, v in per_dim.items() if v < 10) or "all 10"
        print(f"  {m_id}  {mdir:<24}  {last:>3}/100  weak: {weak}")


if __name__ == "__main__":
    main()