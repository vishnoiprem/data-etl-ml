#!/usr/bin/env python3
"""The offline end-to-end demo.

Runs the whole radar against the recorded snapshot in `data/snapshots/` —
no network, no API key, no Docker. This is what `make demo` runs, and it
is what proves the pipeline works end to end.

The demo walks the story in the order a reader would want it:
1. Where the data came from.
2. The topics that are accelerating, and why.
3. One topic in detail, with its sources.
4. What the ranking is actually made of.
5. The report that gets written.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tech_trend_radar.collector import load_latest_snapshot  # noqa: E402
from tech_trend_radar.config import load_settings  # noqa: E402
from tech_trend_radar.ranking import build_trends, explain  # noqa: E402
from tech_trend_radar.semantic import build_matcher  # noqa: E402


def rule(title: str = "") -> None:
    if title:
        print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")
    else:
        print("=" * 72)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the offline Tech Trend Radar demo.")
    parser.add_argument(
        "--limit", type=int, default=8, help="How many trends to show."
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Just write the report, without the walkthrough.",
    )
    parser.add_argument(
        "--out",
        default=str(PROJECT_ROOT / "reports" / "trend_report.md"),
        help="Where to write the report.",
    )
    args = parser.parse_args(argv)

    settings = load_settings()
    snapshot = load_latest_snapshot(settings)
    if snapshot is None:
        print(
            "No snapshot found in data/snapshots/.\n"
            "Run `make fetch` to collect live data first.",
            file=sys.stderr,
        )
        return 1

    posts = snapshot.posts
    # The semantic matcher is built here too, so the demo shows the same
    # ranking the service serves. When the model is unavailable this is
    # None and the demo runs on the lexical signals alone.
    matcher = build_matcher(settings)
    trends = build_trends(posts, settings, limit=args.limit, semantic=matcher)

    if not args.report_only:
        rule("Tech Trend Radar — offline demo")
        print(f"Snapshot:  {snapshot.fetched_at.isoformat()}")
        print(f"Posts:     {len(posts)}")
        print(
            f"Windows:   {settings.recent_window_hours}h recent vs "
            f"{settings.baseline_window_hours}h baseline"
        )
        print(
            f"Semantic:  {'on' if matcher is not None else 'off (lexical only)'}"
        )

        rule("1. Where the data came from")
        for result in snapshot.results:
            status = "ok" if result.ok else "FAILED"
            note = "" if result.ok else f"  ({result.error[:60]})"
            print(
                f"  {status:>6}  {result.platform:14} {len(result.posts):4} posts "
                f"{result.duration_ms:8.0f}ms{note}"
            )
        live = snapshot.ok_platforms
        failed = snapshot.failed_platforms
        print(f"\n  {len(live)} source(s) contributed, {len(failed)} failed.")

        rule("2. What is accelerating")
        if not trends:
            print("  No topics met the trending threshold in this window.")
        for trend in trends:
            print()
            print(explain(trend))

        rule("3. One topic in detail")
        corroborated = [t for t in trends if t.corroborated]
        if corroborated:
            topic = corroborated[0]
            print(f"  {topic.topic}")
            print()
            for headline in topic.headlines:
                print(f"    - {headline['title']}")
                if headline["url"]:
                    print(f"      {headline['url']}")
            print()
            print("  Evidence:")
            for item in topic.evidence:
                print(f"    [{item.kind}] {item.text}")

        rule("4. What the ranking is made of")
        print(f"  {'topic':<22} {'score':>7} {'accel':>7} {'vol':>7} {'corrob':>7}  platforms")
        for trend in trends:
            b = trend.breakdown
            print(
                f"  {trend.topic:<22} {trend.score:>7.2f} {b['acceleration']:>7.2f} "
                f"{b['volume']:>7.2f} {b['corroboration']:>7.2f}  "
                f"{', '.join(trend.platforms)}"
            )

    # The report.
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Tech Trend Radar",
        "",
        f"- **Snapshot:** {snapshot.fetched_at.isoformat()}",
        f"- **Posts:** {len(posts)}",
        f"- **Windows:** {settings.recent_window_hours}h recent vs "
        f"{settings.baseline_window_hours}h baseline",
        f"- **Semantic matching:** {'on' if matcher is not None else 'off (lexical only)'}",
        "",
        "## Ranked trends",
        "",
        "| # | Topic | Score | Recent | Baseline | Platforms | Confirmed |",
        "|---|-------|-------|--------|----------|----------|-----------|",
    ]
    for trend in trends:
        lines.append(
            f"| {trend.rank} | {trend.topic} | {trend.score:.2f} | "
            f"{trend.recent_mentions} | {trend.baseline_mentions} | "
            f"{', '.join(trend.platforms)} | {'yes' if trend.corroborated else 'no'} |"
        )
    lines += ["", "## Why", ""]
    for trend in trends:
        lines += [f"### {trend.rank}. {trend.topic}", "", trend.summary, ""]
        lines += [f"- {reason}" for reason in trend.rationale]
        lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
