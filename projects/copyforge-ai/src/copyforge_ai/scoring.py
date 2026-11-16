"""The scoring rubric — how good is this article, on a 100-point scale?

The scorer exists for two reasons:

1. **The writer needs a target.** "Write better copy" is not a
   specification. "The hook must contain a number, the closing must
   contain a question, no paragraph may exceed 120 words" is.
2. **The eval harness needs a measurement.** Without a number, "the
   output improved" is a claim; with one, it is a measurement.

The rubric is a *structural* score, not a taste score. Every criterion
is checkable from the text alone — no model judges it, no human has to
disagree about it. That is a deliberate limit: the rubric can tell you
the article has no hook, but it cannot tell you the hook is good. The
first is a fact; the second is a conversation.

**The score is comparable within a draft.** The interesting number is
not "92/100" but "68 → 92": what the copy insertion bought. That is
what the eval harness reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .markdown import analyze, parse
from .writer import existing_slugs

#: The maximum score per criterion, and the criteria themselves.
CRITERIA: tuple[tuple[str, str, int], ...] = (
    ("hook_present", "The article opens with prose, not with a heading or a preamble.", 10),
    ("hook_specific", "The opening contains something concrete — a number, a name, a quantity.", 15),
    ("problem_established", "The reader's problem is named early.", 10),
    ("framework_coverage", "The copy structures a strong piece has are present.", 15),
    ("proof_present", "At least one passage offers evidence rather than assertion.", 10),
    ("objection_addressed", "The strongest counter-argument is surfaced and answered.", 5),
    ("actionable_step", "The reader is told something they can do.", 10),
    ("cta_present", "There is a call to action.", 10),
    ("closing_question", "The article ends on a question.", 5),
    ("readability", "Paragraphs are short; no paragraph is a wall of text.", 5),
    ("no_ai_filler", "No machine-filler phrases.", 5),
)

MAX_SCORE = sum(maximum for _, _, maximum in CRITERIA)


@dataclass(slots=True)
class Score:
    """A scored article."""

    total: float = 0.0
    maximum: float = float(MAX_SCORE)
    #: criterion name → points earned
    per_criterion: dict[str, float] = field(default_factory=dict)
    #: criterion name → the maximum for that criterion
    maxima: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @property
    def percent(self) -> float:
        if not self.maximum:
            return 0.0
        return round(100.0 * self.total / self.maximum, 1)

    def as_dict(self) -> dict:
        return {
            "total": round(self.total, 2),
            "maximum": self.maximum,
            "percent": self.percent,
            "per_criterion": {k: round(v, 2) for k, v in self.per_criterion.items()},
            "notes": list(self.notes),
        }


#: How many distinct frameworks a well-formed piece should carry.
TARGET_FRAMEWORKS = 4

#: The paragraph length above which a paragraph is a wall of text.
MAX_PARAGRAPH_WORDS = 120


def score_document(text: str) -> Score:
    """Score a markdown document against the rubric."""
    document = parse(text)
    analysis = analyze(document)
    score = Score()

    for name, _description, maximum in CRITERIA:
        score.maxima[name] = maximum
        score.per_criterion[name] = 0.0

    # 1. The hook is present.
    if analysis.hook_text:
        score.per_criterion["hook_present"] = score.maxima["hook_present"]

    # 2. The hook is specific.
    if analysis.hook_specificity >= 2:
        score.per_criterion["hook_specific"] = score.maxima["hook_specific"]
    elif analysis.hook_specificity == 1:
        score.per_criterion["hook_specific"] = score.maxima["hook_specific"] / 2
        score.notes.append("The opening names one concrete thing, not two.")

    # 3. The problem is established.
    if not analysis.has("no_problem_established"):
        score.per_criterion["problem_established"] = score.maxima["problem_established"]

    # 4. Framework coverage.
    used = existing_slugs(text)
    coverage = min(len(used), TARGET_FRAMEWORKS) / TARGET_FRAMEWORKS
    score.per_criterion["framework_coverage"] = score.maxima["framework_coverage"] * coverage
    if len(used) < TARGET_FRAMEWORKS:
        score.notes.append(
            f"{len(used)} of {TARGET_FRAMEWORKS} target copy structures present."
        )

    # 5. Proof.
    if analysis.has_proof:
        score.per_criterion["proof_present"] = score.maxima["proof_present"]

    # 6. Objection addressed.
    if not analysis.has("unaddressed_objection"):
        score.per_criterion["objection_addressed"] = score.maxima["objection_addressed"]

    # 7. Actionable step.
    if not analysis.has("no_actionable_step"):
        score.per_criterion["actionable_step"] = score.maxima["actionable_step"]

    # 8. CTA.
    if analysis.has_cta:
        score.per_criterion["cta_present"] = score.maxima["cta_present"]

    # 9. Closing question.
    if analysis.has_closing_question:
        score.per_criterion["closing_question"] = score.maxima["closing_question"]

    # 10. Readability — every paragraph under the ceiling.
    long_paragraphs = [
        b for b in document.prose_blocks() if b.word_count() > MAX_PARAGRAPH_WORDS
    ]
    if not long_paragraphs:
        score.per_criterion["readability"] = score.maxima["readability"]
    else:
        worst = max(b.word_count() for b in long_paragraphs)
        penalty = min(1.0, len(long_paragraphs) / 4) * 0.5 + min(1.0, worst / 300) * 0.5
        score.per_criterion["readability"] = score.maxima["readability"] * (1 - penalty)
        score.notes.append(
            f"{len(long_paragraphs)} paragraph(s) over {MAX_PARAGRAPH_WORDS} words "
            f"(longest: {worst})."
        )

    # 11. No AI filler.
    if analysis.ai_phrase_count == 0:
        score.per_criterion["no_ai_filler"] = score.maxima["no_ai_filler"]
    else:
        ratio = min(1.0, analysis.ai_phrase_count / 4)
        score.per_criterion["no_ai_filler"] = score.maxima["no_ai_filler"] * (1 - ratio)
        score.notes.append(f"{analysis.ai_phrase_count} machine-filler phrase(s) found.")

    score.total = sum(score.per_criterion.values())
    return score


def compare(before_text: str, after_text: str) -> dict:
    """Score both drafts and report the difference.

    This is the number the eval harness gates on: did the insertion
    actually make the article better, measured on the same rubric?
    """
    before = score_document(before_text)
    after = score_document(after_text)
    delta = after.total - before.total

    return {
        "before": before.as_dict(),
        "after": after.as_dict(),
        "delta": round(delta, 2),
        "delta_percent": round(after.percent - before.percent, 1),
        "improved": delta > 0,
    }
