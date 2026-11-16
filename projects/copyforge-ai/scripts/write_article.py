#!/usr/bin/env python3
"""Insert high-performing copy structures into a markdown draft.

    python scripts/write_article.py draft.md                    # print the result
    python scripts/write_article.py draft.md -o formatted.md    # write to a file
    python scripts/write_article.py draft.md --in-place         # rewrite the file
    python scripts/write_article.py draft.md --dry-run          # show the plan only
    python scripts/write_article.py draft.md --provider ollama  # use a local model

The author's own text is never rewritten. Only copy blocks are added,
and each one is marked with an HTML comment naming the framework that
produced it — so a second run over the same file adds nothing.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from copyforge_ai.llm import get_default_router
from copyforge_ai.markdown import analyze, parse
from copyforge_ai.planner import plan_copy
from copyforge_ai.scoring import score_document
from copyforge_ai.writer import write_article


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Insert copy structures into a draft.")
    parser.add_argument("draft", help="The markdown draft to work on.")
    parser.add_argument("-o", "--output", default="", help="Where to write the result.")
    parser.add_argument(
        "--in-place", action="store_true", help="Overwrite the draft with the result."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show the plan without writing anything."
    )
    parser.add_argument(
        "--provider",
        choices=["stub", "ollama"],
        default="",
        help="Which backend to write with. Defaults to the environment.",
    )
    args = parser.parse_args(argv)

    path = Path(args.draft)
    if not path.exists():
        print(f"No such file: {path}", file=sys.stderr)
        return 1

    original = path.read_text(encoding="utf-8")

    if args.provider:
        import os

        os.environ["COPYFORGE_LLM_PROVIDER"] = args.provider
    router = get_default_router()

    if args.dry_run:
        document = parse(original)
        analysis = analyze(document)
        plan = plan_copy(document, analysis)
        print(f"Plan for {path.name}  (writer: {router.name})")
        print("=" * 72)
        print()
        if not plan:
            print("Nothing to insert — the draft already carries the structures it needs.")
            return 0
        for index, insertion in enumerate(plan.insertions, 1):
            print(f"  {index}. {insertion.framework:<20} {insertion.position:<14} "
                  f"anchor {insertion.anchor:>3}  ← {insertion.resolves}")
            print(f"     {insertion.reason}")
        if plan.unresolved:
            print()
            print("  Unresolved gaps:", ", ".join(plan.unresolved))
        return 0

    result = write_article(original, router=router)

    before = score_document(original)
    after = score_document(result.document)

    print(f"Wrote {path.name}  (writer: {router.name})")
    print("=" * 72)
    print()
    if not result.blocks:
        print("Nothing was inserted — the draft already carries the structures it needs.")
    else:
        print(f"  {len(result.blocks)} copy block(s) inserted:")
        for block in result.blocks:
            print(f"    {block.framework:<20} {block.position:<14} "
                  f"({len(block.body.split())} words)")
        if result.skipped:
            print(f"  skipped: {', '.join(result.skipped)}")
    print()
    print(f"  rubric score: {before.total:.1f} → {after.total:.1f} "
          f"({after.total - before.total:+.1f}, {before.percent:.0f}% → {after.percent:.0f}%)")
    print()

    if args.in_place:
        path.write_text(result.document, encoding="utf-8")
        print(f"Saved in place: {path}")
    elif args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(result.document, encoding="utf-8")
        print(f"Saved: {out}")
    else:
        print()
        print(result.document)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
