"""The eval harness — measures whether the copy insertion actually helped.

The harness runs the full pipeline over every sample draft and reports:

* **rubric improvement** — the score before and after, on the same
  rubric. This is the headline number.
* **framework coverage** — how many copy structures each draft ended up
  carrying.
* **idempotence** — running the pipeline twice must not change the
  article a second time. A writer that keeps adding copy is not a
  writer.
* **author-text preservation** — the author's original paragraphs must
  survive the write untouched. This is the check that stops the whole
  thing being a stealth rewrite.

The acceptance gate is a set of thresholds. Missing an input is a
*skipped* result, not a failed one — the same rule the tech-trend-radar
harness uses.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .config import Settings, load_settings
from .llm import LLMRouter, get_default_router
from .scoring import score_document
from .writer import existing_slugs, write_article

#: The thresholds the run must clear.
ACCEPTANCE = {
    "min_mean_score_delta": 5.0,
    "min_idempotent_drafts": 1.0,
    "min_preserved_paragraphs": 1.0,
    "min_coverage": 2.0,
}


@dataclass(slots=True)
class DraftResult:
    """The result for one draft."""

    name: str
    before: float = 0.0
    after: float = 0.0
    delta: float = 0.0
    frameworks: list[str] = field(default_factory=list)
    coverage: int = 0
    idempotent: bool = True
    preserved: bool = True
    skipped: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "before": round(self.before, 2),
            "after": round(self.after, 2),
            "delta": round(self.delta, 2),
            "frameworks": list(self.frameworks),
            "coverage": self.coverage,
            "idempotent": self.idempotent,
            "preserved": self.preserved,
            "skipped": list(self.skipped),
        }


@dataclass(slots=True)
class EvalResult:
    """The whole run."""

    drafts: list[DraftResult] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    router: str = "stub"
    acceptance: dict = field(default_factory=dict)
    passed: bool = False

    def mean_delta(self) -> float:
        if not self.drafts:
            return 0.0
        return sum(d.delta for d in self.drafts) / len(self.drafts)

    def mean_coverage(self) -> float:
        if not self.drafts:
            return 0.0
        return sum(d.coverage for d in self.drafts) / len(self.drafts)

    def idempotent_ratio(self) -> float:
        if not self.drafts:
            return 0.0
        return sum(1 for d in self.drafts if d.idempotent) / len(self.drafts)

    def preserved_ratio(self) -> float:
        if not self.drafts:
            return 0.0
        return sum(1 for d in self.drafts if d.preserved) / len(self.drafts)

    def as_dict(self) -> dict:
        return {
            "router": self.router,
            "drafts": [d.as_dict() for d in self.drafts],
            "skipped": list(self.skipped),
            "mean_score_delta": round(self.mean_delta(), 2),
            "mean_coverage": round(self.mean_coverage(), 2),
            "idempotent_ratio": self.idempotent_ratio(),
            "preserved_ratio": self.preserved_ratio(),
            "acceptance": dict(self.acceptance),
            "passed": self.passed,
        }


def _author_paragraphs(text: str) -> list[str]:
    """The draft's prose paragraphs, used for the preservation check."""
    from .markdown import parse

    return [b.text.strip() for b in parse(text).prose_blocks() if b.text.strip()]


def run_eval(
    drafts: list[Path],
    settings: Settings | None = None,
    router: LLMRouter | None = None,
) -> EvalResult:
    """Run the pipeline over every draft and measure the result."""
    settings = settings or load_settings()
    router = router or get_default_router()

    result = EvalResult(router=router.name)

    for path in drafts:
        if not path.exists():
            result.skipped.append(path.name)
            continue

        original = path.read_text(encoding="utf-8")
        if not original.strip():
            result.skipped.append(path.name)
            continue

        before = score_document(original)
        written = write_article(original, router=router)
        after = score_document(written.document)

        # Idempotence: a second run must not change the article.
        second = write_article(written.document, router=router)
        idempotent = second.document == written.document

        # Preservation: every original paragraph must still be there.
        after_paragraphs = _author_paragraphs(written.document)
        missing = [
            p for p in _author_paragraphs(original) if p not in after_paragraphs
        ]
        preserved = not missing

        result.drafts.append(
            DraftResult(
                name=path.name,
                before=before.total,
                after=after.total,
                delta=after.total - before.total,
                frameworks=sorted(existing_slugs(written.document)),
                coverage=len(existing_slugs(written.document)),
                idempotent=idempotent,
                preserved=preserved,
                skipped=list(written.skipped),
            )
        )

    checks = {
        "min_mean_score_delta": result.mean_delta() >= ACCEPTANCE["min_mean_score_delta"],
        "min_idempotent_drafts": result.idempotent_ratio() >= ACCEPTANCE["min_idempotent_drafts"],
        "min_preserved_paragraphs": result.preserved_ratio() >= ACCEPTANCE["min_preserved_paragraphs"],
        "min_coverage": result.mean_coverage() >= ACCEPTANCE["min_coverage"],
    }
    result.acceptance = {
        name: {"passed": bool(ok), "threshold": ACCEPTANCE[name]} for name, ok in checks.items()
    }
    result.passed = all(checks.values())
    return result


def _sample_drafts(settings: Settings) -> list[Path]:
    """The sample drafts in the data directory."""
    if not settings.data_dir.exists():
        return []
    return sorted(settings.data_dir.glob("*.md"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate the copy insertion pipeline.")
    parser.add_argument("--out", type=str, default="", help="Where to write the JSON report.")
    parser.add_argument("--drafts", type=str, default="", help="A directory of drafts to evaluate.")
    args = parser.parse_args(argv)

    settings = load_settings()

    if args.drafts:
        drafts = sorted(Path(args.drafts).glob("*.md"))
    else:
        drafts = _sample_drafts(settings)

    if not drafts:
        print("No drafts to evaluate. Nothing was measured.", file=sys.stderr)
        return 1

    result = run_eval(drafts, settings)

    print("CopyForge AI — evaluation")
    print("=" * 72)
    print()
    for draft in result.drafts:
        status = "ok " if draft.delta > 0 else "-- "
        print(
            f"[{status}] {draft.name:<28} {draft.before:6.1f} → {draft.after:6.1f} "
            f"({draft.delta:+5.1f})  {draft.coverage} frameworks"
        )
    print()
    print(f"  mean score delta: {result.mean_delta():+.2f}")
    print(f"  mean coverage:    {result.mean_coverage():.2f} frameworks")
    print(f"  idempotent:       {result.idempotent_ratio() * 100:.0f}%")
    print(f"  author text kept: {result.preserved_ratio() * 100:.0f}%")
    print()
    for name, check in result.acceptance.items():
        flag = "PASS" if check["passed"] else "FAIL"
        print(f"[{flag}] {name}: {check['threshold']}")
    print()
    print(f"Acceptance: {'PASS' if result.passed else 'FAIL'}")

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result.as_dict(), indent=2), encoding="utf-8")
        print(f"Wrote {out}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
