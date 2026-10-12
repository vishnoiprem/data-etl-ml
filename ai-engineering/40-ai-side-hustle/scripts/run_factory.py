#!/usr/bin/env python3
"""
run_factory.py — Run the 4 revenue streams end-to-end.

Usage:
  python scripts/run_factory.py                    # all 4 streams
  python scripts/run_factory.py --stream seo       # one stream
  python scripts/run_factory.py --stream merch
  python scripts/run_factory.py --simulate-days 30 # inject 30 days of synthetic sales
  python scripts/run_factory.py --simulate-ramp    # 14-day ramp scenario
  python scripts/run_factory.py --loop             # cron every hour
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dashboard import print_dashboard  # noqa: E402
from indexer import build_index  # noqa: E402
from ledger import Ledger  # noqa: E402
from router import get_default_router  # noqa: E402
from simulator import simulate_days, simulate_ramp  # noqa: E402
from stream_merch import run as run_merch  # noqa: E402
from stream_product import run as run_product  # noqa: E402
from stream_saas import run as run_saas  # noqa: E402
from stream_seo import run as run_seo  # noqa: E402


STREAMS = {
    "seo": run_seo,
    "saas": run_saas,
    "product": run_product,
    "merch": run_merch,
}


def main() -> int:
    ap = argparse.ArgumentParser(description="AI side-hustle factory")
    ap.add_argument("--db", default="ledger.db")
    ap.add_argument("--output", default=str(ROOT / "output"))
    ap.add_argument("--stream", choices=["all", "seo", "saas", "product", "merch"],
                    default="all")
    ap.add_argument("--seed", default="ai agents")
    ap.add_argument("--niche", default="indie developers")
    ap.add_argument("--topic", default="soc2 for solo founders")
    ap.add_argument("--merch-topic", default="ai engineers")
    ap.add_argument("--no-record", action="store_true",
                    help="don't record projected revenue (dry run)")
    ap.add_argument("--simulate-days", type=int, default=0, metavar="N",
                    help="inject N days of synthetic sales events after running streams")
    ap.add_argument("--simulate-ramp", action="store_true",
                    help="inject a 14-day ramp scenario (zero → a few events/day)")
    ap.add_argument("--simulate-seed", type=int, default=42,
                    help="seed for the simulator (default 42 = reproducible)")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=3600)
    args = ap.parse_args()

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    def one_pass(verbose: bool = True) -> dict:
        router = get_default_router()
        if verbose:
            print(f"→ router: {getattr(router, 'name', type(router).__name__)}")
        ledger = Ledger(db_path=args.db)
        record = not args.no_record

        results: dict = {}
        if args.stream in ("all", "seo"):
            if verbose:
                print("→ Stream 1: SEO content engine")
            results["seo"] = run_seo(args.seed, router, ledger, output,
                                     top=3, record_projected=record)
        if args.stream in ("all", "saas"):
            if verbose:
                print("→ Stream 2: Micro-SaaS scaffolder")
            results["saas"] = run_saas(args.niche, router, ledger, output,
                                       top=1, record_projected=record)
        if args.stream in ("all", "product"):
            if verbose:
                print("→ Stream 3: Digital product factory")
            results["product"] = run_product(args.topic, router, ledger, output,
                                             record_projected=record)
        if args.stream in ("all", "merch"):
            if verbose:
                print("→ Stream 4: Print-on-demand merch")
            results["merch"] = run_merch(args.merch_topic, router, ledger, output,
                                         record_projected=record)

        if args.simulate_ramp:
            n = simulate_ramp(ledger, days=14)
            if verbose:
                print(f"→ Simulated 14-day ramp: injected {n} events")
        elif args.simulate_days > 0:
            n = simulate_days(ledger, days=args.simulate_days, seed=args.simulate_seed)
            if verbose:
                print(f"→ Simulated {args.simulate_days} days: injected {n} events")

        if verbose:
            idx = build_index(output)
            print(f"→ Wrote {idx}")
            print()
            print_dashboard(db_path=args.db)

        return results

    if args.loop:
        while True:
            try:
                one_pass()
            except KeyboardInterrupt:
                print("\nstopped.")
                return 0
            except Exception as e:
                print(f"[loop] pass failed: {e}", file=sys.stderr)
            print(f"\n[loop] sleeping {args.interval}s... (Ctrl-C to stop)\n")
            time.sleep(args.interval)
    else:
        one_pass()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
