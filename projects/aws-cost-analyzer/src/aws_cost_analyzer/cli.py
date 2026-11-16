"""The command line.

    python -m aws_cost_analyzer.cli analyze --snapshot data/snapshots/xxx.json
    python -m aws_cost_analyzer.cli analyze --demo
    python -m aws_cost_analyzer.cli fetch --tag-keys Data Data-Squad
    python -m aws_cost_analyzer.cli eval

The ``analyze`` command reads a snapshot. It never talks to AWS — the
fetch script does that, separately, so that an analysis is always
reproducible from something on disk.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import load_settings
from .detectors.registry import AnalysisInput, run_all
from .evaluation import evaluate, render
from .narrative import apply_narratives, get_default_router
from .pricing import default_card
from .report import ReportContext, render_text, to_json, write_json_report, write_text_report
from .snapshots import (
    DEFAULT_SNAPSHOT_DIR,
    KIND_COST_RECORDS,
    Snapshot,
    latest_snapshot,
    list_snapshots,
    read_snapshot,
)

SERVICE = "Amazon Simple Storage Service"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="aws-cost-analyzer", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="Analyze a snapshot and report the findings.")
    analyze.add_argument("--snapshot", help="Path to a snapshot file.")
    analyze.add_argument(
        "--latest", action="store_true", help="Use the most recent snapshot in the directory."
    )
    analyze.add_argument(
        "--snapshots-dir", default=str(DEFAULT_SNAPSHOT_DIR), help="Where the snapshots live."
    )
    analyze.add_argument("--demo", action="store_true", help="Analyze the synthetic demo corpus.")
    analyze.add_argument("--provider", help="stub or ollama.")
    analyze.add_argument("--out", help="Write the JSON report here.")
    analyze.add_argument("--out-text", help="Write the text report here.")
    analyze.add_argument("--json", action="store_true", help="Print the JSON report to stdout.")

    fetch = sub.add_parser("fetch", help="Pull live data from AWS into a snapshot.")
    fetch.add_argument("--start")
    fetch.add_argument("--end")
    fetch.add_argument("--region")
    fetch.add_argument("--profile")
    fetch.add_argument("--tag-keys", nargs="*")
    fetch.add_argument("--with-resources", action="store_true")
    fetch.add_argument("--out", default=str(DEFAULT_SNAPSHOT_DIR))
    fetch.add_argument("--dry-run", action="store_true")

    sub.add_parser("list", help="List the available snapshots.")
    sub.add_parser("eval", help="Run the eval harness.")

    return parser.parse_args(argv)


def _load_snapshot(args: argparse.Namespace) -> Snapshot | None:
    if args.snapshot:
        return read_snapshot(args.snapshot)
    if args.latest:
        snapshot = latest_snapshot(args.snapshots_dir, kind=KIND_COST_RECORDS)
        if snapshot is None:
            print(f"No snapshots found in {args.snapshots_dir}", file=sys.stderr)
            return None
        return snapshot
    return None


def _analysis_input(snapshot: Snapshot) -> AnalysisInput:
    """Build the detector input from a snapshot.

    A snapshot holds the service-level view — one group per service.
    The growth detector needs a *resource* dimension to name a bucket,
    so when the snapshot has only a service group the growth detector
    has nothing to attribute and says so rather than inventing a
    target.
    """
    records = list(snapshot.records)
    group_definitions = snapshot.group_definitions

    resource_index = 0
    if group_definitions and len(group_definitions) > 1:
        resource_index = len(group_definitions) - 1
    elif group_definitions and group_definitions[0].get("Key") == "SERVICE":
        # A service-only group: the group key IS the service, so there
        # is no resource dimension to attribute a growth to.
        resource_index = -1

    periods = sorted({r.period_label for r in records if not r.estimated})
    latest_period = periods[-1] if periods else ""

    return AnalysisInput(
        records=records,
        latest_period=latest_period,
        resource_group_index=resource_index,
        service=SERVICE,
        untagged_service_total=sum(r.amount for r in records),
    )


def command_analyze(args: argparse.Namespace) -> int:
    settings = load_settings()
    card = default_card()

    if args.demo:
        from .evaluation import build_corpus

        corpus = build_corpus()
        data = corpus.input
        findings = run_all(data, settings, card)
        context = ReportContext(
            region=settings.region,
            start=settings.start,
            end=settings.end,
            rate_card_region=card.region,
            rate_card_checked_on=card.checked_on,
            total_spend=corpus.measured_spend,
            records_analyzed=len(corpus.input.records),
            notes=list(data.notes),
        )
    else:
        snapshot = _load_snapshot(args)
        if snapshot is None:
            return 1
        data = _analysis_input(snapshot)
        findings = run_all(data, settings, card)
        context = ReportContext(
            region=snapshot.region or settings.region,
            start=snapshot.start,
            end=snapshot.end,
            rate_card_region=card.region,
            rate_card_checked_on=card.checked_on,
            total_spend=sum(r.amount for r in snapshot.complete_records),
            records_analyzed=len(snapshot.records),
            excluded_periods=snapshot.excluded_periods,
            notes=list(data.notes) + list(snapshot.errors),
        )

    router = get_default_router(provider=args.provider or "")
    apply_narratives(router, findings)
    context.router_name = router.name

    if args.json:
        print(json.dumps(to_json(findings, context), indent=2, sort_keys=True))
    else:
        print(render_text(findings, context))

    if args.out:
        write_json_report(findings, context, args.out)
        print(f"\nWrote {args.out}")
    if args.out_text:
        write_text_report(findings, context, args.out_text)
        print(f"Wrote {args.out_text}")

    return 0


def command_fetch(args: argparse.Namespace) -> int:
    script = Path(__file__).resolve().parent.parent.parent / "scripts" / "fetch_aws.py"
    if not script.exists():
        print("scripts/fetch_aws.py not found", file=sys.stderr)
        return 1

    forwarded = []
    if args.start:
        forwarded += ["--start", args.start]
    if args.end:
        forwarded += ["--end", args.end]
    if args.region:
        forwarded += ["--region", args.region]
    if args.profile:
        forwarded += ["--profile", args.profile]
    if args.tag_keys:
        forwarded += ["--tag-keys", *args.tag_keys]
    if args.with_resources:
        forwarded += ["--with-resources"]
    if args.dry_run:
        forwarded += ["--dry-run"]
    forwarded += ["--out", args.out]

    import subprocess

    return subprocess.call([sys.executable, str(script), *forwarded])


def command_list(args: argparse.Namespace) -> int:
    paths = list_snapshots(args.snapshots_dir)
    if not paths:
        print(f"No snapshots in {args.snapshots_dir}")
        return 0
    for path in paths:
        snapshot = read_snapshot(path)
        print(
            f"{path.name}\n"
            f"    {snapshot.region} {snapshot.start}..{snapshot.end} "
            f"({snapshot.granularity}, {len(snapshot.records)} records, "
            f"taken {snapshot.taken_at or 'unknown'})"
        )
    return 0


def command_eval(args: argparse.Namespace) -> int:
    result = evaluate()
    print(render(result))
    return 0 if result.passed else 1


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.command == "analyze":
        return command_analyze(args)
    if args.command == "fetch":
        return command_fetch(args)
    if args.command == "list":
        return command_list(args)
    if args.command == "eval":
        return command_eval(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
