#!/usr/bin/env python3
"""
run_factory.py — Run the 3 revenue streams end-to-end.

Usage:
  python scripts/run_factory.py                 # all 3 streams
  python scripts/run_factory.py --stream seo    # one stream only
  python scripts/run_factory.py --stream saas
  python scripts/run_factory.py --stream product
  python scripts/run_factory.py --seed "ai agents" --topic "soc2" --niche "indie devs"
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dashboard import print_dashboard  # noqa: E402
from ledger import Ledger  # noqa: E402
from router import get_default_router  # noqa: E402
from stream_product import run as run_product  # noqa: E402
from stream_saas import run as run_saas  # noqa: E402
from stream_seo import run as run_seo  # noqa: E402


STREAMS = {"seo": run_seo, "saas": run_saas, "product": run_product}


def main() -> int:
    ap = argparse.ArgumentParser(description="AI side-hustle factory")
    ap.add_argument("--db", default="ledger.db")
    ap.add_argument("--output", default=str(ROOT / "output"),
                    help="where to write generated articles/saas/products")
    ap.add_argument("--stream", choices=["all", "seo", "saas", "product"],
                    default="all")
    ap.add_argument("--seed", default="ai agents",
                    help="SEO seed keyword")
    ap.add_argument("--niche", default="indie developers",
                    help="target SaaS niche")
    ap.add_argument("--topic", default="soc2 for solo founders",
                    help="digital product topic")
    ap.add_argument("--no-record", action="store_true",
                    help="don't record projected revenue to the ledger (dry run)")
    ap.add_argument("--loop", action="store_true",
                    help="run all streams once per hour forever")
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

        if verbose:
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
