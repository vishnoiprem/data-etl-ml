"""The curated copy framework library — the "top 1%" patterns.

Every framework in here is a documented piece of direct-response craft that
has survived a lot of A/B tests. They are hand-written, not learned, and
each one carries:

* a **name** and a **slug** (the slug is the stable id used everywhere
  else — in the plan, in the output markers, in the report);
* a **rationale** — *why* the pattern works, in one sentence, so a reader
  can disagree with it rather than just trusting it;
* **slots** — the structural pieces the pattern is made of. A slot has a
  role (`problem`, `promise`, `proof`...), a label, and a prompt
  instruction that tells a writer — or a model — what goes in it;
* a **worked example**, because a pattern you cannot see is a pattern you
  cannot use;
* **where it goes** — the positions in an article where the framework is
  structurally valid. This is what makes the insertion *planned* rather
  than random.

**The library is the point.** A model can write a hook, but it cannot be
*trusted* to know that a PAS block belongs before the thesis and that a
BAB block belongs in the middle. That placement is decided here, in
Python, and it is testable.

**Where "top 1%" comes from.** These are the frameworks that show up
repeatedly in the top-decile of high-performing long-form and LinkedIn
copy: PAS, AIDA, BAB, the curiosity gap, social proof, the objection
sandwich, the "so what" bridge, and a handful of section-level patterns
(the problem-agitate list, the contrarian take, the concrete example).
Nobody has published the actual distribution of top-1% articles — that
claim is not measurable — so this library encodes the *documented,
well-worn* patterns rather than pretending to encode a percentile.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

#: Where a copy block can be placed in an article. These are structural
#: positions, not stylistic ones.
OPENING = "opening"
AFTER_HOOK = "after_hook"
AFTER_PROBLEM = "after_problem"
#: The body, in the order the body reads. Each body framework gets its
#: own slot: the body of an article can carry a concrete example *and* a
#: before/after bridge *and* a so-what, and putting them all in one
#: "middle" would leave the article with a single block for a body that
#: has three jobs.
BODY_EXAMPLE = "body_example"
BODY_BRIDGE = "body_bridge"
BODY_ACTION = "body_action"
BODY_PROOF = "body_proof"
BODY_LIST = "body_list"
LATE_MIDDLE = "late_middle"
BEFORE_CTA = "before_cta"
CLOSING = "closing"

#: The order the positions are considered in. Earlier positions win when
#: two frameworks want the same slot.
POSITION_ORDER = (
    OPENING,
    AFTER_HOOK,
    AFTER_PROBLEM,
    BODY_EXAMPLE,
    BODY_BRIDGE,
    BODY_ACTION,
    BODY_PROOF,
    BODY_LIST,
    LATE_MIDDLE,
    BEFORE_CTA,
    CLOSING,
)

#: Every position in the body, in reading order.
BODY_POSITIONS = (
    BODY_EXAMPLE,
    BODY_BRIDGE,
    BODY_ACTION,
    BODY_PROOF,
    BODY_LIST,
)


@dataclass(frozen=True, slots=True)
class Slot:
    """One structural piece of a framework.

    A framework with slots is a *shape*; a framework without slots is a
    *move*. The writer fills the slots, in order, and the filled text is
    what gets inserted.
    """

    role: str
    label: str
    instruction: str

    def render(self) -> str:
        """The slot as a prompt fragment."""
        return f"{self.label}: {self.instruction}"


@dataclass(frozen=True, slots=True)
class Framework:
    """A documented copy pattern."""

    slug: str
    name: str
    summary: str
    rationale: str
    positions: tuple[str, ...]
    slots: tuple[Slot, ...] = ()
    example: str = ""
    #: The signal that says this framework is *needed*. The planner reads
    #: these off the structural analysis of the draft.
    resolves: tuple[str, ...] = ()
    #: True when the framework is a section-level rewrite rather than an
    #: inserted block. Those are applied in place, not appended.
    inline: bool = False
    weight: float = 1.0

    def applies_to(self, position: str) -> bool:
        """Whether this framework is structurally valid at `position`."""
        return position in self.positions

    def slot_prompt(self) -> str:
        """All slots, rendered as prompt fragments."""
        return "\n".join(f"- {slot.render()}" for slot in self.slots)

    def slot_roles(self) -> tuple[str, ...]:
        return tuple(slot.role for slot in self.slots)


# --------------------------------------------------------------------------- #
# Opening frameworks
# --------------------------------------------------------------------------- #


PAS = Framework(
    slug="pas",
    name="Problem–Agitate–Solve",
    summary="Name the pain, twist the knife, then hand over the fix.",
    rationale=(
        "A reader who recognises the problem in the first sentence stays "
        "for the solution; agitating the problem is what makes the "
        "solution feel like relief rather than another thing to learn."
    ),
    positions=(OPENING, AFTER_HOOK),
    slots=(
        Slot(
            role="problem",
            label="Problem",
            instruction=(
                "state the reader's concrete problem in their own vocabulary, "
                "in one sentence, without naming a tool yet"
            ),
        ),
        Slot(
            role="agitate",
            label="Agitate",
            instruction=(
                "show what the problem actually costs — the wasted time, the "
                "silent failure, the thing they cannot explain to their team"
            ),
        ),
        Slot(
            role="solution",
            label="Solution",
            instruction=(
                "bridge to the approach this article teaches, promising a "
                "specific outcome rather than a general benefit"
            ),
        ),
    ),
    example=(
        "Your pipeline works on every sample you have tested. Then it meets "
        "production traffic and the numbers are wrong in ways nobody "
        "reproduced. This guide is the checklist that catches the four "
        "failure modes that cause it."
    ),
    resolves=("missing_hook", "no_problem_established"),
)

CURIOSITY_GAP = Framework(
    slug="curiosity_gap",
    name="Curiosity Gap",
    summary="Open on a specific oddity the reader cannot yet explain.",
    rationale=(
        "An unexplained specific detail is the strongest open loop there "
        "is: the reader cannot stop reading until they can close it, and "
        "the loop stays open only if the payoff actually arrives."
    ),
    positions=(OPENING,),
    slots=(
        Slot(
            role="observation",
            label="Observation",
            instruction=(
                "open on one concrete, slightly surprising fact or scene from "
                "the article's subject"
            ),
        ),
        Slot(
            role="tension",
            label="Tension",
            instruction=(
                "raise the question the observation opens — phrased so the "
                "reader now has to read on for the answer"
            ),
        ),
    ),
    example=(
        "Two teams run the same model, on the same data, with the same "
        "accuracy. One of them is useless in production. The difference is "
        "a single line in a config file."
    ),
    resolves=("generic_hook", "missing_hook"),
)

CONTRARIAN = Framework(
    slug="contrarian",
    name="Contrarian Open",
    summary="Disagree with the consensus the reader already believes.",
    rationale=(
        "Agreeing with the reader costs nothing and earns nothing; "
        "contradicting them earns attention precisely because it costs "
        "something."
    ),
    positions=(OPENING, AFTER_HOOK),
    slots=(
        Slot(
            role="consensus",
            label="Consensus",
            instruction=(
                "state the thing the reader's field believes right now, "
                "accurately and without straw-manning"
            ),
        ),
        Slot(
            role="counter",
            label="Counter",
            instruction=(
                "say what you believe instead, and the reason it is more "
                "true — a reason, not a boast"
            ),
        ),
    ),
    example=(
        "Everyone says you need a vector database for RAG. For most teams "
        "you need a SQL table and a good query — and here is the threshold "
        "where the vector database starts paying for itself."
    ),
    resolves=("generic_hook", "no_thesis"),
)


# --------------------------------------------------------------------------- #
# Body frameworks
# --------------------------------------------------------------------------- #


BAB = Framework(
    slug="bab",
    name="Before–After–Bridge",
    summary="Show the before, show the after, then bridge to how.",
    rationale=(
        "A reader cannot evaluate a claim, only a contrast. The before state "
        "is the state they are in, so the after state lands as a change "
        "rather than an aspiration."
    ),
    positions=(BODY_BRIDGE, AFTER_PROBLEM),
    slots=(
        Slot(
            role="before",
            label="Before",
            instruction=(
                "describe the current state concretely — the workflow, the "
                "workaround, the manual step everyone does"
            ),
        ),
        Slot(
            role="after",
            label="After",
            instruction=(
                "describe the same situation after the change, in the same "
                "terms so the contrast is visible"
            ),
        ),
        Slot(
            role="bridge",
            label="Bridge",
            instruction=(
                "name the specific mechanism that gets them from before to "
                "after"
            ),
        ),
    ),
    example=(
        "Before: every schema change is a ticket, a review, and a two-day "
        "wait. After: the same change ships in one query. The bridge is "
        "moving the compatibility check into the migration itself."
    ),
    resolves=("no_transition", "abstract_section"),
)

SOCIAL_PROOF = Framework(
    slug="social_proof",
    name="Social Proof",
    summary="Borrow credibility from someone the reader already trusts.",
    rationale=(
        "A claim from a stranger is a claim; the same claim from a source "
        "the reader already weights is evidence. The specific named "
        "attribution is what does the work — unattributed proof reads as "
        "marketing."
    ),
    positions=(BODY_PROOF, AFTER_PROBLEM),
    slots=(
        Slot(
            role="attribution",
            label="Attribution",
            instruction=(
                "name who experienced it and the context they experienced it "
                "in — role, team size, or constraint"
            ),
        ),
        Slot(
            role="result",
            label="Result",
            instruction=(
                "give the specific outcome they got, in a number if one "
                "exists — never a vague 'big improvement'"
            ),
        ),
    ),
    example=(
        "A staff engineer on a nine-person data team moved their nightly "
        "batch from 41 minutes to under four, without touching the "
        "transform logic at all."
    ),
    resolves=("no_proof", "unbacked_claim"),
)

OBJECTION_SANDWICH = Framework(
    slug="objection_sandwich",
    name="Objection Sandwich",
    summary="Name the objection, answer it, then restate the claim.",
    rationale=(
        "A reader who has not said the objection out loud is still "
        "objecting in their head; surfacing it removes the reason to leave, "
        "and restating the claim after the answer puts the conclusion last "
        "where it sticks."
    ),
    positions=(LATE_MIDDLE, BEFORE_CTA),
    slots=(
        Slot(
            role="objection",
            label="Objection",
            instruction=(
                "state the strongest objection a skeptical reader would "
                "raise, in their words"
            ),
        ),
        Slot(
            role="answer",
            label="Answer",
            instruction=(
                "answer it directly and specifically — concede what is "
                "genuinely true about it"
            ),
        ),
        Slot(
            role="reaffirm",
            label="Reaffirm",
            instruction=(
                "restate the article's claim now that the objection is "
                "answered"
            ),
        ),
    ),
    example=(
        "This sounds like another layer of tooling. Fair — it is another "
        "thing to learn, and for a three-person team it is not worth it. "
        "Above ten pipelines it replaces a script that breaks monthly."
    ),
    resolves=("unaddressed_objection", "no_proof"),
)

SO_WHAT = Framework(
    slug="so_what",
    name="So-What Bridge",
    summary="Turn an abstraction into something the reader can act on.",
    rationale=(
        "Readers abandon a section the moment it stops being about them. "
        "The so-what bridge is the shortest path from 'this is how it "
        "works' to 'here is what you do with it'."
    ),
    positions=(BODY_ACTION, AFTER_PROBLEM),
    slots=(
        Slot(
            role="implication",
            label="Implication",
            instruction=(
                "state the practical consequence of what was just explained, "
                "for the reader's situation"
            ),
        ),
        Slot(
            role="action",
            label="Action",
            instruction=(
                "give the first concrete step they can take today — a "
                "command, a check, a page to read"
            ),
        ),
    ),
    example=(
        "So what does this mean for your setup? Check whether your "
        "connection pool timeout is longer than your longest transaction. "
        "If it is, the fix is one config value."
    ),
    resolves=("abstract_section", "no_actionable_step"),
)


# --------------------------------------------------------------------------- #
# Section-level patterns (applied in place)
# --------------------------------------------------------------------------- #


PROBLEM_LIST = Framework(
    slug="problem_list",
    name="Problem Agitation List",
    summary="Turn a vague worry into a countable list of specific failures.",
    rationale=(
        "A reader who can count their problems is a reader who believes "
        "the article is about them. The list converts anxiety into "
        "recognition, and recognition is what makes them keep reading."
    ),
    positions=(BODY_LIST, AFTER_PROBLEM),
    slots=(
        Slot(
            role="item",
            label="Item",
            instruction=(
                "one specific failure, each in its own line, each naming the "
                "symptom rather than the cause"
            ),
        ),
    ),
    example=(
        "- The dashboard shows yesterday's numbers and nobody notices\n"
        "- The alert fires on a Tuesday and the incident was on Monday\n"
        "- Two teams maintain two versions of the same table"
    ),
    resolves=("no_problem_established", "abstract_section"),
    inline=True,
)

CONCRETE_EXAMPLE = Framework(
    slug="concrete_example",
    name="Concrete Example",
    summary="Replace an abstraction with one real, specific instance.",
    rationale=(
        "General claims are cheap and forgettable; one specific instance is "
        "the unit readers actually remember and quote."
    ),
    positions=(BODY_EXAMPLE,),
    slots=(
        Slot(
            role="scenario",
            label="Scenario",
            instruction=(
                "one specific instance of the pattern: real numbers, real "
                "names or roles, a real decision that was made"
            ),
        ),
    ),
    example=(
        "A retailer was losing £4,000 a month to a job that re-shipped "
        "returned parcels. The fix was not a better carrier — it was "
        "suppressing the second label."
    ),
    resolves=("no_specifics", "abstract_section"),
    inline=True,
)


# --------------------------------------------------------------------------- #
# Closing frameworks
# --------------------------------------------------------------------------- #


CTA = Framework(
    slug="cta",
    name="Call to Action",
    summary="Ask for one specific, easy next action.",
    rationale=(
        "A vague call to action gets ignored because it costs the reader "
        "something they cannot price. One specific, low-cost, "
        "immediately-doable ask gets taken."
    ),
    positions=(BEFORE_CTA, CLOSING),
    slots=(
        Slot(
            role="ask",
            label="Ask",
            instruction=(
                "one specific action the reader can take in the next ten "
                "minutes — reading, running, or changing one thing"
            ),
        ),
        Slot(
            role="friction",
            label="Friction",
            instruction=(
                "say what it costs them and why it is worth it, in one line"
            ),
        ),
    ),
    example=(
        "Run your slowest query with the new plan enabled and compare the "
        "two numbers. It takes four minutes and tells you whether any of "
        "this applies to you."
    ),
    resolves=("missing_cta",),
)

CLOSING_QUESTION = Framework(
    slug="closing_question",
    name="Closing Question",
    summary="End on a question the reader cannot answer with 'yes'.",
    rationale=(
        "A question that can be answered 'yes' is not a question. A closing "
        "question that the reader has to think about keeps the thread open "
        "in the comment section, which is where the distribution of a post "
        "actually happens."
    ),
    positions=(CLOSING,),
    slots=(
        Slot(
            role="question",
            label="Question",
            instruction=(
                "one question about the reader's own situation that they "
                "cannot answer from the article alone"
            ),
        ),
    ),
    example=(
        "So: if you could delete one step from your pipeline this quarter, "
        "which one would you stop being afraid to touch?"
    ),
    resolves=("missing_closing_question",),
)


#: Every framework in the library, in the order they are considered.
FRAMEWORKS: tuple[Framework, ...] = (
    PAS,
    CURIOSITY_GAP,
    CONTRARIAN,
    BAB,
    SOCIAL_PROOF,
    OBJECTION_SANDWICH,
    SO_WHAT,
    PROBLEM_LIST,
    CONCRETE_EXAMPLE,
    CTA,
    CLOSING_QUESTION,
)

_BY_SLUG = {framework.slug: framework for framework in FRAMEWORKS}

#: The signals a framework resolves, mapped to the frameworks that resolve
#: them. Used by the planner to pick the best candidate for a gap.
RESOLVERS: dict[str, tuple[Framework, ...]] = {}
for _framework in FRAMEWORKS:
    for _signal in _framework.resolves:
        RESOLVERS.setdefault(_signal, ())
        RESOLVERS[_signal] += (_framework,)


def get_framework(slug: str) -> Framework:
    """The framework with this slug.

    Raises `KeyError` for an unknown slug — a typo in a plan should fail
    loudly, not silently insert nothing.
    """
    try:
        return _BY_SLUG[slug]
    except KeyError:
        raise KeyError(
            f"unknown framework {slug!r}; known: {', '.join(sorted(_BY_SLUG))}"
        ) from None


def frameworks_for(position: str) -> tuple[Framework, ...]:
    """Every framework valid at `position`, in library order."""
    return tuple(f for f in FRAMEWORKS if f.applies_to(position))


def resolvers_for(signal: str) -> tuple[Framework, ...]:
    """Every framework that resolves this signal, best-weighted first."""
    candidates = RESOLVERS.get(signal, ())
    return tuple(sorted(candidates, key=lambda f: -f.weight))


#: Phrases that make a piece of copy read as machine-generated. These are
#: not banned outright — the *scorer* penalises them, and the writer's
#: prompt instructs the model to avoid them. A hard ban would be simpler
#: but would also ban "in this article" from a piece that is in fact an
#: article.
AI_PHRASES: tuple[str, ...] = (
    "in today's fast-paced world",
    "in the ever-evolving landscape",
    "it's important to note that",
    "it's worth noting that",
    "delve into",
    "delve deeper",
    "navigate the complexities",
    "in conclusion",
    "furthermore",
    "moreover",
    "at the end of the day",
    "game-changer",
    "game changer",
    "unlock the power",
    "unleash the power",
    "revolutionize",
    "seamlessly",
    "leverage the power",
    "elevate your",
    "supercharge your",
    "the world of",
    "embark on a journey",
    "without further ado",
    "a testament to",
    "underscores the importance",
    "pave the way",
    "tailor-made",
    "cutting-edge solution",
    "robust solution",
    "seamlessly integrate",
)

#: Phrases that signal a *real* opening — a hook that names a specific
#: thing rather than a category.
SPECIFICITY_MARKERS: tuple[str, ...] = (
    "%",
    "$",
    "€",
    "£",
    "×",
    "ms",
    "seconds",
    "minutes",
    "hours",
    "days",
    "weeks",
    "lines",
    "times",
    "people",
    "users",
    "requests",
    "queries",
    "GB",
    "TB",
    "MB",
    "Q1",
    "Q2",
    "Q3",
    "Q4",
    "20",
)

#: Patterns that mark a question — used to detect a closing question.
QUESTION_MARKERS: tuple[str, ...] = (
    "?",
    "what if",
    "how would you",
    "which one",
    "have you",
    "would you",
    "what would",
)


def looks_like_question(text: str) -> bool:
    """Whether a line reads as a question."""
    lowered = text.strip().lower()
    if not lowered:
        return False
    return any(marker in lowered for marker in QUESTION_MARKERS)


def count_ai_phrases(text: str) -> int:
    """How many banned AI phrases the text contains."""
    lowered = text.lower()
    return sum(1 for phrase in AI_PHRASES if phrase in lowered)


def specificity_score(text: str) -> int:
    """How many distinct specificity markers the text carries.

    A hook with a number in it is a hook about a specific thing. A hook
    with three is a hook that names a number, a quantity and a unit —
    which is as close to "this is a real measurement" as prose gets.

    The markers are matched on **word boundaries**, not as substrings.
    That distinction is the whole function: "teams" contains "ms" and
    "pipelines" contains "lines", so a naive substring match rates the
    sentence *"Data teams are under increasing pressure to scale their
    pipelines"* as highly specific — when it is precisely the generic
    opener this check exists to catch.
    """
    lowered = text.lower()
    return sum(
        1
        for marker in SPECIFICITY_MARKERS
        if re.search(rf"(?<![a-z0-9]){re.escape(marker)}(?![a-z0-9])", lowered)
    )


#: Fields a framework's slots can be filled with. Kept as a dataclass so
#: the writer can carry them around without a dict.
@dataclass(slots=True)
class CopyBlock:
    """One generated block of copy, ready to be spliced into a draft."""

    framework: str
    position: str
    heading: str = ""
    body: str = ""
    slots: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        """The block as markdown."""
        parts: list[str] = []
        if self.heading:
            parts.append(f"### {self.heading}")
        if self.body:
            parts.append(self.body.strip())
        return "\n\n".join(parts)
