#!/usr/bin/env python3
"""Collect live data from every source into `data/snapshots/`.

This is the only script in the project that touches the network. It writes
a snapshot, which is what the demo, the tests and the evaluation harness
then read.

    python scripts/fetch_snapshots.py            # collect and save
    python scripts/fetch_snapshots.py --quiet    # only report the summary
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tech_trend_radar.collector import collect, save_snapshot  # noqa: E402
from tech_trend_radar.config import load_settings  # noqa: E402
from tech_trend_radar.ranking import build_trends  # noqa: E402
from tech_trend_radar.semantic import build_matcher  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect live snapshots.")
    parser.add_argument("--quiet", action="store_true", help="Only print the summary.")
    parser.add_argument(
        "--limit", type=int, default=10, help="How many trends to show."
    )
    args = parser.parse_args(argv)

    settings = load_settings()
    snapshot = collect(settings)

    if not args.quiet:
        print("Collecting from every source...")
        print()
        for result in snapshot.results:
            status = "ok" if result.ok else "FAILED"
            note = "" if result.ok else f"  ({result.error[:70]})"
            print(
                f"  {status:>6}  {result.platform:14} {len(result.posts):4} posts "
                f"{result.duration_ms:8.0f}ms{note}"
            )

    total = len(snapshot.posts)
    print(f"\nCollected {total} unique posts from {len(snapshot.ok_platforms)} sources.")

    if not total:
        print("Nothing was collected. The API is available but every source failed.",
              file=sys.stderr)
        return 1

    path = save_snapshot(snapshot, settings)
    print(f"Snapshot saved to {path}")

    # The same matcher the service uses, so the snapshot's ranking is the
    # ranking the API will serve. None when the model is unavailable, in
    # which case the radar runs on the lexical signals alone.
    matcher = build_matcher(settings)
    trends = build_trends(snapshot.posts, settings, limit=args.limit, semantic=matcher)
    print(f"Semantic matching: {'on' if matcher is not None else 'off (lexical only)'}")
    if trends:
        print(f"\nTop {len(trends)} trends:")
        for trend in trends:
            platforms = ", ".join(trend.platforms)
            print(
                f"  {trend.rank:>2}. {trend.topic:<22} {trend.score:>6.2f}  "
                f"({trend.recent_mentions} recent vs {trend.baseline_mentions} baseline)"
                f"  [{platforms}]"
            )
    else:
        print("\nNo topics met the trending threshold in this window.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
