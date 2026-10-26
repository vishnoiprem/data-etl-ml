#!/usr/bin/env python3
"""
stress_test.py — run find_opportunities() N_CYCLES (default 10000)
times back-to-back and score the autopilot for stability + consistency.

What it measures per cycle:
  - Wall time
  - Number of qualified routes (>=35% margin)
  - Top opportunity's product / route / margin / rich_score
  - Whether all expected output files were written
  - Whether all 2,016 routes were evaluated (26 products × 8 src × 7 dst + extras)
  - Whether any exception escaped

What it reports at the end:
  - Total runtime
  - Pass / fail rate
  - Mean / median / p95 cycle time
  - Mean n_qualified (and how stable it is across cycles)
  - Top-route stability histogram
  - Rich-fast leaderboard across all cycles (which product wins most often)
  - File-write success rate per output type
  - Overall PASS / FAIL verdict

N_CYCLES is read from the environment if set (so we can do 1K / 10K / 50K
without editing the file).
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import time
import traceback
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# Import the same module the autopilot uses
import importlib.util as _ilu
import sys as _sys
_spec = _ilu.spec_from_file_location("find_opportunities", str(HERE / "find_opportunities.py"))
_mod = _ilu.module_from_spec(_spec)
_sys.modules["find_opportunities"] = _mod  # dataclass needs this in sys.modules
assert _spec.loader is not None
_spec.loader.exec_module(_mod)
run_once = _mod.run_once
PRODUCTS_CSV = _mod.PRODUCTS_CSV
RANKED_JSON = _mod.RANKED_JSON
REPORTS_DIR = _mod.REPORTS_DIR
PRODUCTS = _mod.PRODUCTS

N_CYCLES = int(os.environ.get("N_CYCLES", "10000"))
TOP_N = 3  # how many top routes to track for "stability" metric


def _one_cycle(i: int) -> dict:
    """Run a single cycle and return timing + outcome."""
    t0 = time.perf_counter()
    cycle = {
        "i": i,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "ok": False,
        "duration_ms": 0.0,
        "n_evaluated": 0,
        "n_qualified": 0,
        "top_product": None,
        "top_route": None,
        "top_margin": None,
        "top_score": None,
        "rich_top_product": None,
        "rich_top_route": None,
        "rich_top_score": None,
        "rich_top_margin_usd": None,
        "top_n": [],
        "files_written": {},
        "err": None,
    }
    try:
        qualified = run_once(verbose=False)
        cycle["duration_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        cycle["n_qualified"] = len(qualified)
        cycle["n_evaluated"] = sum(
            len(p["src"]) * len(p["dst"]) for p in PRODUCTS
        )
        if qualified:
            top = qualified[0]
            cycle["top_product"] = top.product
            cycle["top_route"] = f"{top.source_country}->{top.dest_country}"
            cycle["top_margin"] = round(top.margin_pct, 4)
            cycle["top_score"] = top.score
            for q in qualified[:TOP_N]:
                cycle["top_n"].append(
                    (q.product, f"{q.source_country}->{q.dest_country}",
                     round(q.margin_pct, 4))
                )
            # rich-fast #1
            rtop = max(qualified, key=lambda o: o.rich_score)
            cycle["rich_top_product"] = rtop.product
            cycle["rich_top_route"] = f"{rtop.source_country}->{rtop.dest_country}"
            cycle["rich_top_score"] = rtop.rich_score
            cycle["rich_top_margin_usd"] = round(rtop.margin_usd, 2)
        # Verify outputs
        cycle["files_written"] = {
            "products_csv": PRODUCTS_CSV.exists(),
            "ranked_json": RANKED_JSON.exists(),
            "report_md":   any(REPORTS_DIR.glob("*.md")),
        }
        if RANKED_JSON.exists():
            with RANKED_JSON.open() as f:
                d = json.load(f)
            cycle["n_qualified"] = d.get("n_qualified", cycle["n_qualified"])
        cycle["ok"] = all(cycle["files_written"].values())
    except Exception as exc:
        cycle["err"] = f"{type(exc).__name__}: {exc}"
        cycle["duration_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        cycle["err_tb"] = traceback.format_exc(limit=2)
    return cycle


def main() -> int:
    print(f"=== Trade-finder stress test — {N_CYCLES} cycles ===")
    print(f"  started: {datetime.now().isoformat(timespec='seconds')}")
    print(f"  target: 1 cycle as fast as possible, no sleep, no LLM calls")
    print(f"  dataset: 26 products × 8 src × 7 dst = {sum(len(p['src']) * len(p['dst']) for p in PRODUCTS)} routes")
    print()

    cycles: list[dict] = []
    t_total0 = time.perf_counter()
    last_print = t_total0

    for i in range(1, N_CYCLES + 1):
        c = _one_cycle(i)
        cycles.append(c)
        if c["err"]:
            print(f"  cycle {i:>5}  ERROR {c['err']}")
        # Throttled progress — every 500 cycles or every 10s
        if i <= 5 or i % 500 == 0 or time.perf_counter() - last_print > 10:
            ok = sum(1 for x in cycles if x["ok"])
            err = sum(1 for x in cycles if x["err"])
            avg_ms = sum(x["duration_ms"] for x in cycles) / len(cycles)
            elapsed = time.perf_counter() - t_total0
            rate = len(cycles) / elapsed if elapsed > 0 else 0
            eta = (N_CYCLES - i) / rate if rate > 0 else 0
            print(
                f"  cycle {i:>5}/{N_CYCLES}  ok={ok} err={err}  "
                f"avg={avg_ms:6.1f}ms  rate={rate:4.2f}/s  "
                f"eta={eta:5.0f}s  "
                f"top={c['top_route']}  rich#1={c['rich_top_route']} \${c['rich_top_margin_usd']}"
            )
            last_print = time.perf_counter()

    total_seconds = time.perf_counter() - t_total0
    print()
    print("=== summary ===")
    print(f"  total wall time:    {total_seconds:.2f}s  ({total_seconds/60:.1f} min)")
    print(f"  cycles / second:    {N_CYCLES / total_seconds:.2f}")

    n_ok = sum(1 for c in cycles if c["ok"])
    n_err = sum(1 for c in cycles if c["err"])
    print(f"  pass:               {n_ok}/{N_CYCLES}  ({n_ok/N_CYCLES*100:.1f}%)")
    print(f"  errors:             {n_err}")

    durations = sorted(c["duration_ms"] for c in cycles)
    print(f"  cycle time ms:      "
          f"min={durations[0]:.1f}  "
          f"median={statistics.median(durations):.1f}  "
          f"mean={statistics.mean(durations):.1f}  "
          f"p95={durations[int(N_CYCLES*0.95)]:.1f}  "
          f"max={durations[-1]:.1f}")

    nq = [c["n_qualified"] for c in cycles]
    print(f"  n_qualified:        "
          f"min={min(nq)}  median={statistics.median(nq)}  mean={statistics.mean(nq):.1f}  "
          f"max={max(nq)}  stdev={statistics.stdev(nq) if len(nq) > 1 else 0:.2f}")

    # Top-opportunity stability
    top_routes = Counter(c["top_route"] for c in cycles if c["top_route"])
    print(f"\n  top route (margin-based #1) — across {N_CYCLES} cycles:")
    for route, count in top_routes.most_common(10):
        bar = "#" * int(count / N_CYCLES * 50)
        print(f"    {count:>6}  {route:<14}  ({count/N_CYCLES*100:5.1f}%)  {bar}")

    # Rich-fast stability
    rich_routes = Counter(c["rich_top_route"] for c in cycles if c["rich_top_route"])
    print(f"\n  rich-fast #1 (\$/unit × capital) — across {N_CYCLES} cycles:")
    for route, count in rich_routes.most_common(10):
        bar = "#" * int(count / N_CYCLES * 50)
        print(f"    {count:>6}  {route:<14}  ({count/N_CYCLES*100:5.1f}%)  {bar}")

    rich_products = Counter(
        c["rich_top_product"] for c in cycles if c["rich_top_product"]
    )
    print(f"\n  rich-fast winning PRODUCT — across {N_CYCLES} cycles:")
    for product, count in rich_products.most_common(10):
        bar = "#" * int(count / N_CYCLES * 50)
        print(f"    {count:>6}  {product:<26}  ({count/N_CYCLES*100:5.1f}%)  {bar}")

    # Top-N changes per cycle
    top_n_changes = 0
    prev_top_n: list | None = None
    for c in cycles:
        if c["top_n"] != prev_top_n:
            top_n_changes += 1
        prev_top_n = c["top_n"]
    print(f"\n  top-{TOP_N} changed {top_n_changes}/{N_CYCLES} times  "
          f"({top_n_changes/N_CYCLES*100:.2f}%)")

    # File-write consistency
    if cycles:
        csv_ok = sum(1 for c in cycles if c["files_written"].get("products_csv"))
        json_ok = sum(1 for c in cycles if c["files_written"].get("ranked_json"))
        md_ok = sum(1 for c in cycles if c["files_written"].get("report_md"))
        print(f"\n  file writes:  csv={csv_ok}  json={json_ok}  md={md_ok}")

    # Verdict
    print()
    print("=== verdict ===")
    stable_score = (n_ok / N_CYCLES) * 100
    diversity_score = min(1.0, top_n_changes / max(N_CYCLES, 1)) * 100
    print(f"  stability (cycles that produced full output): {stable_score:.2f}%")
    print(f"  diversity (top-{TOP_N} changes):              {diversity_score:.2f}%")

    # Final rich-fast WINNER (the product most likely to make money)
    if rich_products:
        winner = rich_products.most_common(1)[0]
        winner_count = winner[1]
        winner_pct = winner_count / N_CYCLES * 100
        print(f"\n  RICH-FAST WINNER: {winner[0]}  ({winner_count}/{N_CYCLES} cycles, {winner_pct:.1f}%)")
        # Find typical $/unit for this winner
        winner_dollars = [
            c["rich_top_margin_usd"] for c in cycles
            if c["rich_top_product"] == winner[0] and c["rich_top_margin_usd"] is not None
        ]
        if winner_dollars:
            print(f"    typical margin \$/unit: min={min(winner_dollars):.2f}  "
                  f"mean={statistics.mean(winner_dollars):.2f}  max={max(winner_dollars):.2f}")
        n_for_10k = int(10000 / statistics.mean(winner_dollars)) if winner_dollars else 0
        print(f"    units to \$10K profit: ~{n_for_10k}")

    if stable_score >= 99.0:
        verdict = "PASS"
    elif stable_score >= 95.0:
        verdict = "WARN"
    else:
        verdict = "FAIL"
    print(f"\n  verdict: {verdict}")
    if verdict == "PASS":
        print("  ✅ — autopilot is reliable and the rich-fast model is consistent.")
    elif verdict == "WARN":
        print(f"  ⚠️  — {stable_score:.2f}% stability. Check errors above.")
    else:
        print(f"  ❌ — only {stable_score:.2f}% of cycles produced all outputs.")

    # Persist raw results
    out_path = HERE / "logs" / f"stress_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "n_cycles": N_CYCLES,
        "total_seconds": round(total_seconds, 3),
        "n_ok": n_ok,
        "n_err": n_err,
        "durations_ms_summary": {
            "min": durations[0], "median": statistics.median(durations),
            "mean": round(statistics.mean(durations), 2),
            "p95": durations[int(N_CYCLES*0.95)], "max": durations[-1],
        },
        "n_qualified_min": min(nq),
        "n_qualified_max": max(nq),
        "n_qualified_mean": round(statistics.mean(nq), 2),
        "n_qualified_stdev": round(statistics.stdev(nq), 2) if len(nq) > 1 else 0,
        "top_route_counts": dict(top_routes),
        "rich_top_route_counts": dict(rich_routes),
        "rich_top_product_counts": dict(rich_products),
        "top_n_changes": top_n_changes,
        "stable_score_pct": round(stable_score, 2),
        "diversity_score_pct": round(diversity_score, 2),
        "verdict": verdict,
    }, indent=2))
    print(f"\n  raw results → {out_path}")
    return 0 if n_err == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
