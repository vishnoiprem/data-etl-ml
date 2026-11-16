#!/usr/bin/env python3
"""The offline end-to-end demo.

Runs the whole pipeline on the synthetic corpus — no AWS account, no
network, no credentials — and writes the report to ``reports/``.

    python scripts/run_demo.py
    python scripts/run_demo.py --report-only
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from aws_cost_analyzer.config import load_settings  # noqa: E402
from aws_cost_analyzer.detectors.registry import run_all  # noqa: E402
from aws_cost_analyzer.evaluation import build_corpus, evaluate  # noqa: E402
from aws_cost_analyzer.narrative import apply_narratives, get_default_router  # noqa: E402
from aws_cost_analyzer.pricing import default_card  # noqa: E402
from aws_cost_analyzer.report import (  # noqa: E402
    ReportContext,
    render_text,
    write_json_report,
    write_text_report,
)

REPORTS = ROOT / "reports"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the offline end-to-end demo.")
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Write the reports without printing the analysis.",
    )
    parser.add_argument("--provider", help="stub or ollama.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    settings = load_settings()
    card = default_card()
    corpus = build_corpus()

    findings = run_all(corpus.input, settings, card)

    router = get_default_router(provider=args.provider or "")
    apply_narratives(router, findings)

    context = ReportContext(
        region=settings.region,
        start=settings.start,
        end=settings.end,
        rate_card_region=card.region,
        rate_card_checked_on=card.checked_on,
        total_spend=corpus.measured_spend,
        records_analyzed=len(corpus.input.records),
        excluded_periods=[],
        notes=list(corpus.input.notes),
        router_name=router.name,
    )

    if not args.report_only:
        print(render_text(findings, context))

    REPORTS.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS / "cost_analyzer_report.json"
    text_path = REPORTS / "cost_analyzer_report.txt"

    write_json_report(findings, context, json_path)
    write_text_report(findings, context, text_path)

    if not args.report_only:
        print(f"\nWrote {json_path}")
        print(f"Wrote {text_path}")

        # --- the eval harness -------------------------------------------- #
        from aws_cost_analyzer.evaluation import render

        result = evaluate()
        print()
        print(render(result))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
