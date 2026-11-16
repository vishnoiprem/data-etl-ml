"""The planner — decides where each copy block goes, and why.

This is the decision layer, and it is deliberately *not* a model. A
language model asked to "improve this article" will happily rewrite
sentences the author was happy with. The planner instead:

1. reads the structural analysis of the draft;
2. matches the gaps against the framework library's declared resolvers;
3. places each chosen framework at a structural position where it is
   valid — and positions are ordered, so a framework that wants the
   opening loses to one that is a better fit for the opening;
4. emits a **plan**: an ordered list of insertions, each with the
   framework, the position, the block index it anchors to, and the
   reason it was chosen.

The reason matters as much as the choice. A plan that cannot explain
itself is a plan nobody can audit, and an unauditable copy insertion is
just a rewrite with extra steps.

**One framework per position.** Two frameworks stacked in the same
position produce mush. The planner keeps the highest-weight candidate
for each position and lets the rest go.

**The plan is idempotent by construction.** The writer marks inserted
blocks with an HTML comment carrying the framework slug, so a second run
over the same file detects the marker and skips the block. A draft that
has already been processed does not accumulate copies.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .frameworks import (
    AFTER_HOOK,
    AFTER_PROBLEM,
    BEFORE_CTA,
    BODY_ACTION,
    BODY_BRIDGE,
    BODY_EXAMPLE,
    BODY_POSITIONS,
    BODY_PROOF,
    CLOSING,
    LATE_MIDDLE,
    OPENING,
    POSITION_ORDER,
    Framework,
    get_framework,
    resolvers_for,
)
from .markdown import Analysis, Block, Document

#: The marker that identifies a block CopyForge inserted. Keeping the
#: slug in the marker means a second run can tell which framework
#: produced the block, and skip it.
MARKER_PREFIX = "<!-- copyforge:"
MARKER_SUFFIX = "-->"


@dataclass(slots=True)
class Insertion:
    """One planned copy block."""

    framework: str
    position: str
    #: The index of the document block this insertion is anchored *after*.
    #: `-1` means "at the very top", before everything.
    anchor: int = -1
    #: The heading the block gets, if any.
    heading: str = ""
    #: Why this framework was chosen for this position.
    reason: str = ""
    #: The gap this insertion resolves.
    resolves: str = ""
    #: The prompt handed to the writer for this block.
    prompt: str = ""
    #: The rendered markdown, filled in by the writer once the block has
    #: been generated.
    render_text: str = ""

    @property
    def slug(self) -> str:
        return self.framework


@dataclass(slots=True)
class Plan:
    """The full set of insertions for one draft."""

    insertions: list[Insertion] = field(default_factory=list)
    #: Gaps the planner could not fill with any framework.
    unresolved: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.insertions)

    def __len__(self) -> int:
        return len(self.insertions)

    def frameworks_used(self) -> list[str]:
        return [i.framework for i in self.insertions]


def _position_rank(position: str) -> int:
    try:
        return POSITION_ORDER.index(position)
    except ValueError:
        return len(POSITION_ORDER)


def _default_heading(framework: Framework) -> str:
    """The heading a framework's block gets.

    Most blocks do not need a heading — a PAS block that arrives with
    its own heading interrupts the flow it is meant to create. Only the
    list-shaped and example-shaped patterns want one, because they are
    self-contained units the reader might scan past.
    """
    if framework.slug in {"problem_list"}:
        return "The failure modes"
    if framework.slug in {"concrete_example"}:
        return "A concrete example"
    return ""


def _anchor_for(position: str, document: Document) -> int:
    """The document block index an insertion at this position anchors to.

    - `OPENING` anchors before the first block.
    - `AFTER_HOOK` anchors after the first prose paragraph.
    - `AFTER_PROBLEM` anchors after the first paragraph that reads as
      problem work.
    - The `BODY_*` positions each anchor after a different point in the
      prose, spread across the body in reading order. Two body blocks
      landing at the same spot would read as one long block.
    - `LATE_MIDDLE` anchors after the second third — the slot for the
      objection sandwich, which needs the reader to have seen the claim
      before it is challenged.
    - `BEFORE_CTA` anchors before the last prose paragraph.
    - `CLOSING` anchors after the last prose paragraph.
    """
    prose = document.prose_blocks()
    if not prose:
        return -1

    if position == OPENING:
        return -1

    if position == AFTER_HOOK:
        return _index_of(document, prose[0])

    if position == AFTER_PROBLEM:
        for block in prose:
            if _reads_as_problem(block):
                return _index_of(document, block)
        return _index_of(document, prose[0])

    if position in BODY_POSITIONS:
        # The body positions are spread across the middle of the prose,
        # in the order they appear in BODY_POSITIONS. Each one gets a
        # different fraction, so two body blocks never land together.
        slot = BODY_POSITIONS.index(position)
        fraction = (slot + 1) / (len(BODY_POSITIONS) + 1)
        target = prose[min(len(prose) - 1, int(len(prose) * fraction))]
        return _index_of(document, target)

    if position == LATE_MIDDLE:
        target = prose[min(len(prose) - 1, (len(prose) * 2) // 3)]
        return _index_of(document, target)

    if position == BEFORE_CTA:
        # The CTA goes before the article's final paragraph. It is
        # anchored *after* the block that precedes it, which is the
        # block before the last prose paragraph — so the CTA lands
        # between the second-to-last paragraph and the last one.
        if len(prose) < 2:
            return _index_of(document, prose[-1])
        return _index_of(document, prose[-2])

    if position == CLOSING:
        return _index_of(document, prose[-1])

    return -1


def _index_of(document: Document, block: Block) -> int:
    """The index of a block in the document's block list."""
    for index, candidate in enumerate(document.blocks):
        if candidate is block:
            return index
    return -1


def _reads_as_problem(block: Block) -> bool:
    """Whether a paragraph is doing problem work.

    Kept local rather than imported from `markdown` because the planner
    only needs a coarse version of the same judgement — the analyzer's
    version drives gap detection, this one drives placement.
    """
    from .markdown import _looks_like_problem

    return _looks_like_problem(block.text)


def _prompt_for(framework: Framework, document: Document, analysis: Analysis) -> str:
    """The prompt handed to the writer for one block.

    It carries the framework's slots, the article's title, a short
    excerpt of the draft for context, and the constraints that keep the
    output on-voice. The draft excerpt matters: without it a model
    writes copy for a generic article, and the block ends up unrelated
    to what the author wrote.

    The title is passed separately because the excerpt is built from
    prose blocks only. A title names the *subject*; the opening
    sentence names the *situation*. A block written from the title is
    about the piece; a block written from the opening sentence tends to
    restate it.
    """
    context = _context_excerpt(document)
    lines = [
        f"Write one {framework.name} block for the article below.",
        "",
        f"Framework: {framework.name} — {framework.summary}",
        f"Why it works: {framework.rationale}",
        "",
        "Fill these slots, in order:",
        framework.slot_prompt(),
        "",
        "Constraints:",
        (
            "- Use only what the article itself supports. Invent no statistics, "
            "quotes, names, or results."
        ),
        "- Do not use first-person singular claims of personal experience.",
        "- Keep sentences short and concrete. Prefer a number to an adjective.",
        (
            "- Do not use filler phrases like 'in today's world', 'delve into', "
            "'furthermore', 'game-changer', 'unlock the power'."
        ),
        "- Return only the block body. No preamble, no explanation.",
    ]
    title = document.title
    if title:
        lines += ["", f"Article title: {title}"]
    if context:
        lines += ["", "Article context:", context]
    return "\n".join(lines)


def _context_excerpt(document: Document, limit: int = 1200) -> str:
    """A short excerpt of the draft, for context."""
    prose = document.prose_blocks()
    if not prose:
        return ""
    text = "\n\n".join(b.text for b in prose)
    if len(text) <= limit:
        return text
    return text[:limit].rsplit("\n\n", 1)[0] + "\n\n[...]"


def plan_copy(document: Document, analysis: Analysis) -> Plan:
    """The plan for this draft.

    Every insertion is justified by a gap the analysis found and a
    framework that resolves it. If nothing matches, the plan is empty
    and the draft is left alone — an article that already has everything
    does not need more copy poured into it.
    """
    plan = Plan()

    # Gap → position. The order of this mapping is the priority order:
    # the earliest gap that can be filled wins the earliest position.
    #
    # The *gaps* list is the authority here, not the signals set. The
    # analyzer credits a gap as closed when an already-inserted
    # framework resolves it — so a gap that is still in `gaps` is still
    # open, and one that has been credited is not. Reading `signals`
    # instead would re-plan every insertion on a second run.
    gap_positions: list[tuple[str, str]] = []

    open_gaps = set(analysis.gaps)

    if "missing_hook" in open_gaps:
        gap_positions.append(("missing_hook", OPENING))
    elif "generic_hook" in open_gaps:
        gap_positions.append(("generic_hook", OPENING))

    if "no_thesis" in open_gaps:
        gap_positions.append(("no_thesis", AFTER_HOOK))

    if "no_problem_established" in open_gaps:
        gap_positions.append(("no_problem_established", AFTER_PROBLEM))

    # Specificity before abstraction. `no_specifics` is the narrower
    # gap — the article names no concrete instance — and a concrete
    # example is the better answer to it than a before/after bridge.
    # Ordering these the other way round would fill the bridge slot
    # and leave the narrower gap open, which the next run would then
    # try to fill — and the article would grow a second block for a gap
    # the first block had already covered.
    if "no_specifics" in open_gaps:
        gap_positions.append(("no_specifics", BODY_EXAMPLE))

    if "abstract_section" in open_gaps:
        gap_positions.append(("abstract_section", BODY_BRIDGE))

    if "no_transition" in open_gaps:
        gap_positions.append(("no_transition", BODY_BRIDGE))

    if "no_proof" in open_gaps:
        gap_positions.append(("no_proof", BODY_PROOF))

    if "unaddressed_objection" in open_gaps:
        gap_positions.append(("unaddressed_objection", LATE_MIDDLE))

    if "no_actionable_step" in open_gaps:
        gap_positions.append(("no_actionable_step", BODY_ACTION))

    if "missing_cta" in open_gaps:
        gap_positions.append(("missing_cta", BEFORE_CTA))

    if "missing_closing_question" in open_gaps:
        gap_positions.append(("missing_closing_question", CLOSING))

    # Candidate frameworks per gap, ranked by weight then by how early
    # they fit the position.
    taken_positions: dict[str, str] = {}
    used_frameworks: set[str] = set()
    #: Which gap each framework was chosen for — needed when a framework
    #: is displaced to a different position.
    gap_for_framework: dict[str, str] = {}

    for gap, preferred_position in gap_positions:
        candidates = [
            framework
            for framework in resolvers_for(gap)
            if framework.slug not in used_frameworks
            and framework.applies_to(preferred_position)
        ]
        if not candidates:
            # The preferred position does not work for any resolver of
            # this gap. Try the position's neighbours rather than
            # dropping the gap on the floor.
            candidates = [
                framework
                for framework in resolvers_for(gap)
                if framework.slug not in used_frameworks
            ]
            if not candidates:
                plan.unresolved.append(gap)
                continue
            candidates = sorted(
                candidates,
                key=lambda f: (
                    _position_rank(min(f.positions, key=_position_rank)),
                    -f.weight,
                ),
            )
            position = min(candidates[0].positions, key=_position_rank)
        else:
            candidates = sorted(candidates, key=lambda f: (-f.weight, _position_rank(min(f.positions, key=_position_rank))))
            position = preferred_position

        framework = candidates[0]

        # One framework per position. When the slot is already taken,
        # the *later* gap gives way — but a CTA is a structural
        # requirement, so it takes the slot and displaces the softer
        # framework into a position it also fits.
        if position in taken_positions:
            displaced = taken_positions[position]
            displaced_framework = get_framework(displaced)
            alternate = next(
                (
                    p
                    for p in displaced_framework.positions
                    if p != position and p not in taken_positions
                ),
                None,
            )
            if gap == "missing_cta" and alternate:
                taken_positions[position] = framework.slug
                used_frameworks.add(framework.slug)
                used_frameworks.discard(displaced_framework.slug)
                plan.insertions.append(
                    Insertion(
                        framework=framework.slug,
                        position=position,
                        anchor=_anchor_for(position, document),
                        heading=_default_heading(framework),
                        reason=framework.rationale,
                        resolves=gap,
                        prompt=_prompt_for(framework, document, analysis),
                    )
                )
                # Re-insert the displaced framework at its alternate.
                plan.insertions.append(
                    Insertion(
                        framework=displaced_framework.slug,
                        position=alternate,
                        anchor=_anchor_for(alternate, document),
                        heading=_default_heading(displaced_framework),
                        reason=displaced_framework.rationale,
                        resolves=gap_for_framework.get(displaced_framework.slug, ""),
                        prompt=_prompt_for(displaced_framework, document, analysis),
                    )
                )
                continue
            plan.unresolved.append(gap)
            continue

        taken_positions[position] = framework.slug
        used_frameworks.add(framework.slug)
        gap_for_framework[framework.slug] = gap

        plan.insertions.append(
            Insertion(
                framework=framework.slug,
                position=position,
                anchor=_anchor_for(position, document),
                heading=_default_heading(framework),
                reason=framework.rationale,
                resolves=gap,
                prompt=_prompt_for(framework, document, analysis),
            )
        )

    # Stable ordering: by position, then by anchor.
    plan.insertions.sort(key=lambda i: (_position_rank(i.position), i.anchor))
    return plan
