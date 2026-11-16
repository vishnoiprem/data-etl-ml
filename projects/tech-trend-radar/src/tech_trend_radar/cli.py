"""The command-line interface.

`python -m tech_trend_radar` is the one command that does everything the
API does, without needing a server:

    python -m tech_trend_radar trends --limit 10
    python -m tech_trend_radar topics rust
    python -m tech_trend_radar sources
    python -m tech_trend_radar report --out reports/trend_report.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .collector import collect, load_latest_snapshot, save_snapshot
from .config import load_settings
from .ranking import build_trends, explain
from .semantic import build_matcher


def _load_posts(offline: bool, settings) -> tuple[list, str] | None:
    """The posts to analyse, and where they came from.

    Returns None when there is nothing to analyse, so the caller can exit
    with a message rather than raising.
    """
    if not offline:
        snapshot = collect(settings)
        if snapshot.posts:
            try:
                save_snapshot(snapshot, settings)
            except OSError:
                pass
            return snapshot.posts, "live"

    snapshot = load_latest_snapshot(settings)
    if snapshot is None:
        print(
            "No snapshot available. Run `make fetch` first, or drop --offline "
            "to collect live.",
            file=sys.stderr,
        )
        return None
    return snapshot.posts, f"snapshot {snapshot.fetched_at.isoformat()}"


def cmd_trends(args: argparse.Namespace) -> int:
    settings = load_settings()
    loaded = _load_posts(args.offline, settings)
    if loaded is None:
        return 1
    posts, origin = loaded
    matcher = build_matcher(settings)
    trends = build_trends(posts, settings, limit=args.limit, semantic=matcher)

    print(f"Tech Trend Radar — {len(posts)} posts from {origin}")
    print(f"Windows: {settings.recent_window_hours}h recent vs "
          f"{settings.baseline_window_hours}h baseline")
    print(f"Semantic matching: {'on' if matcher is not None else 'off (lexical only)'}")
    print()
    if not trends:
        print("No topics met the trending threshold in this window.")
        return 0
    for trend in trends:
        print(explain(trend))
        print()
    return 0


def cmd_topics(args: argparse.Namespace) -> int:
    settings = load_settings()
    loaded = _load_posts(args.offline, settings)
    if loaded is None:
        return 1
    posts, origin = loaded
    matcher = build_matcher(settings)
    trends = build_trends(posts, settings, limit=200, semantic=matcher)

    for trend in trends:
        if trend.topic.lower() == args.topic.lower():
            print(explain(trend))
            print()
            for headline in trend.headlines:
                url = headline["url"]
                print(f"  - {headline['title']}")
                if url:
                    print(f"    {url}")
            return 0

    print(f"No topic named {args.topic!r} in the current trends.", file=sys.stderr)
    return 1


def cmd_sources(args: argparse.Namespace) -> int:
    settings = load_settings()
    snapshot = load_latest_snapshot(settings)
    if snapshot is None:
        print("No snapshot available.", file=sys.stderr)
        return 1

    print("Source coverage:")
    for result in snapshot.results:
        status = "ok  " if result.ok else "FAIL"
        print(
            f"  [{status}] {result.platform:14} {len(result.posts):4} posts "
            f"{result.duration_ms:8.0f}ms  {result.error[:60]}"
        )
    print(f"\nTotal: {len(snapshot.posts)} unique posts")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    settings = load_settings()
    loaded = _load_posts(args.offline, settings)
    if loaded is None:
        return 1
    posts, origin = loaded
    matcher = build_matcher(settings)
    trends = build_trends(posts, settings, limit=args.limit, semantic=matcher)

    lines = [
        "# Tech Trend Radar",
        "",
        f"- **Collected:** {origin}",
        f"- **Posts:** {len(posts)}",
        f"- **Windows:** {settings.recent_window_hours}h recent vs "
        f"{settings.baseline_window_hours}h baseline",
        f"- **Semantic matching:** {'on' if matcher is not None else 'off (lexical only)'}",
        "",
    ]

    if trends:
        lines += [
            "## Ranked trends",
            "",
            "| # | Topic | Score | Recent | Baseline | Platforms | Confirmed |",
            "|---|-------|-------|--------|----------|----------|-----------|",
        ]
        for trend in trends:
            platforms = ", ".join(trend.platforms)
            lines.append(
                f"| {trend.rank} | {trend.topic} | {trend.score:.2f} | "
                f"{trend.recent_mentions} | {trend.baseline_mentions} | "
                f"{platforms} | {'yes' if trend.corroborated else 'no'} |"
            )
        lines.append("")
        lines += ["## Why", ""]
        for trend in trends:
            lines.append(f"### {trend.rank}. {trend.topic}")
            lines.append("")
            lines.append(trend.summary)
            lines.append("")
            for reason in trend.rationale:
                lines.append(f"- {reason}")
            lines.append("")
    else:
        lines += ["No topics met the trending threshold in this window.", ""]

    output = "\n".join(lines)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output, encoding="utf-8")
        print(f"Wrote {path}")
    else:
        print(output)
    return 0


def cmd_json(args: argparse.Namespace) -> int:
    settings = load_settings()
    loaded = _load_posts(args.offline, settings)
    if loaded is None:
        return 1
    posts, origin = loaded
    matcher = build_matcher(settings)
    trends = build_trends(posts, settings, limit=args.limit, semantic=matcher)
    payload = {
        "origin": origin,
        "post_count": len(posts),
        "semantic_enabled": matcher is not None,
        "trends": [t.to_dict() for t in trends],
    }
    print(json.dumps(payload, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tech_trend_radar",
        description="Find trending technology topics across developer communities.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use the last saved snapshot instead of collecting live.",
    )
    sub = parser.add_subparsers(dest="command")

    trends = sub.add_parser("trends", help="Show the ranked trends.")
    trends.add_argument("--limit", type=int, default=10)
    trends.set_defaults(func=cmd_trends)

    topics = sub.add_parser("topics", help="Show one topic in detail.")
    topics.add_argument("topic")
    topics.set_defaults(func=cmd_topics)

    sources = sub.add_parser("sources", help="Show source coverage.")
    sources.set_defaults(func=cmd_sources)

    report = sub.add_parser("report", help="Write the trend report.")
    report.add_argument("--limit", type=int, default=15)
    report.add_argument("--out", default="")
    report.set_defaults(func=cmd_report)

    as_json = sub.add_parser("json", help="Emit the trends as JSON.")
    as_json.add_argument("--limit", type=int, default=20)
    as_json.set_defaults(func=cmd_json)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
