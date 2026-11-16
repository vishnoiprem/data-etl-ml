#!/usr/bin/env python3
"""The offline end-to-end demo.

No API key, no network, no Ollama required. The demo takes the sample
draft, shows what the planner decided and why, runs the writer, and
reports the rubric score before and after.

    python scripts/run_demo.py
    python scripts/run_demo.py --report-only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from copyforge_ai.config import load_settings
from copyforge_ai.llm import get_default_router
from copyforge_ai.markdown import analyze, parse
from copyforge_ai.planner import plan_copy
from copyforge_ai.scoring import compare
from copyforge_ai.writer import write_article

RULE = "=" * 72


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the offline demo.")
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Write the JSON report and print nothing else.",
    )
    parser.add_argument(
        "--draft",
        default="",
        help="Which draft to use. Defaults to the first sample.",
    )
    args = parser.parse_args(argv)

    settings = load_settings()
    router = get_default_router()

    if args.draft:
        draft_path = Path(args.draft)
    else:
        drafts = sorted(settings.data_dir.glob("*.md"))
        if not drafts:
            print(f"No sample drafts in {settings.data_dir}", file=sys.stderr)
            return 1
        draft_path = drafts[0]

    original = draft_path.read_text(encoding="utf-8")
    document = parse(original)
    analysis = analyze(document)
    plan = plan_copy(document, analysis)

    if not args.report_only:
        print(RULE)
        print("CopyForge AI — offline demo")
        print(RULE)
        print()
        print(f"Draft:   {draft_path.name}")
        print(f"Writer:  {router.name}")
        print(f"Words:   {analysis.word_count}")
        print()

        print("── The gaps ──────────────────────────────────────────────────────────")
        if analysis.gaps:
            for gap in analysis.gaps:
                print(f"  • {gap}")
        else:
            print("  (none — the draft already carries the structures it needs)")
        print()

        print("── The plan ─────────────────────────────────────────────────────────")
        if plan:
            for index, insertion in enumerate(plan.insertions, 1):
                print(f"  {index}. {insertion.framework:<20} {insertion.position:<14} "
                      f"← {insertion.resolves}")
                print(f"     {insertion.reason}")
        else:
            print("  (nothing to insert)")
        if plan.unresolved:
            print()
            print(f"  Unresolved: {', '.join(plan.unresolved)}")
        print()

        result = write_article(original, router=router)

        print("── The blocks ───────────────────────────────────────────────────────")
        for block in result.blocks:
            print(f"  {block.framework}  ({block.position})")
            for line in block.render().splitlines():
                if line.strip():
                    print(f"    {line}")
            print()

        comparison = compare(original, result.document)
        print("── The score ────────────────────────────────────────────────────────")
        print(f"  before: {comparison['before']['total']:.1f} / "
              f"{comparison['before']['maximum']}  ({comparison['before']['percent']:.0f}%)")
        print(f"  after:  {comparison['after']['total']:.1f} / "
              f"{comparison['after']['maximum']}  ({comparison['after']['percent']:.0f}%)")
        print(f"  delta:  {comparison['delta']:+.1f}")
        if comparison["after"]["notes"]:
            print()
            print("  Remaining notes:")
            for note in comparison["after"]["notes"]:
                print(f"    - {note}")
        print()

    # Always write the report.
    result = write_article(original, router=router)
    comparison = compare(original, result.document)
    report = {
        "draft": draft_path.name,
        "router": router.name,
        "gaps": list(analysis.gaps),
        "plan": [
            {
                "framework": i.framework,
                "position": i.position,
                "resolves": i.resolves,
                "reason": i.reason,
            }
            for i in plan.insertions
        ],
        "blocks": [
            {"framework": b.framework, "position": b.position, "body": b.body}
            for b in result.blocks
        ],
        "score": comparison,
    }
    settings.report_dir.mkdir(parents=True, exist_ok=True)
    report_path = settings.report_dir / "copyforge_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if not args.report_only:
        print(f"Report written to {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
