"""Markdown parsing and the structural analysis that drives insertion.

The writer needs to know two things about a draft before it can do
anything useful:

1. **What is in it** — the headings, the paragraphs, the lists, the code
   blocks, the blockquotes, in order, with the original text preserved
   exactly so the output can be reconstructed byte-for-byte outside the
   edited regions.
2. **What is missing** — the copy structures a top-1% piece has and this
   draft does not.

Both live here. The parser is deliberately small and line-oriented: it
does not build a tree, because a flat list of blocks in document order is
all the planner needs, and a flat list is trivial to render back out.

**The parser never rewrites what it did not touch.** Every block keeps
its original source text, so a round trip through `parse` → `render` is
the identity. That property is what lets the writer insert copy into a
draft without silently reflowing the author's prose.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

#: A front-matter fence, at the very top of the file.
FRONT_MATTER_RE = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.DOTALL)

#: An ATX heading.
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")

#: A fenced code block.
FENCE_RE = re.compile(r"^\s*(```|~~~)")

#: A list item.
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")

#: A blockquote.
BLOCKQUOTE_RE = re.compile(r"^\s*>")


@dataclass(slots=True)
class Block:
    """One block of the document, with its original source text."""

    kind: str
    text: str
    level: int = 0
    #: The index of the line the block starts on, in the original file.
    start_line: int = 0
    #: The heading this block sits under, if any.
    section: str = ""

    @property
    def is_heading(self) -> bool:
        return self.kind == "heading"

    @property
    def is_prose(self) -> bool:
        return self.kind == "paragraph"

    def word_count(self) -> int:
        return len(self.text.split())


@dataclass(slots=True)
class Document:
    """A parsed markdown document."""

    blocks: list[Block] = field(default_factory=list)
    front_matter: str = ""
    #: The heading of each section, in order.
    sections: list[str] = field(default_factory=list)

    def render(self) -> str:
        """The document back to markdown.

        For a parsed document this is the identity — the parser keeps
        every block's original text.
        """
        parts: list[str] = []
        if self.front_matter:
            parts.append(self.front_matter.rstrip("\n"))
        for block in self.blocks:
            parts.append(block.text)
        return "\n\n".join(parts).rstrip("\n") + "\n"

    def prose_blocks(self) -> list[Block]:
        return [b for b in self.blocks if b.is_prose]

    def headings(self) -> list[Block]:
        return [b for b in self.blocks if b.is_heading]

    @property
    def title(self) -> str:
        """The article's title.

        From the front matter's ``title:`` if present, otherwise the
        first H1. The title names the *subject* of the piece, which is
        what a copy block should be about — the opening sentence names
        the *situation* instead.
        """
        if self.front_matter:
            match = re.search(r"^title:\s*(.+?)\s*$", self.front_matter, re.MULTILINE)
            if match:
                value = match.group(1).strip().strip("\"'")
                if value:
                    return value
        for block in self.blocks:
            if block.level == 1 and block.is_heading:
                return block.text.lstrip("#").strip()
        return ""

    def word_count(self) -> int:
        return sum(b.word_count() for b in self.prose_blocks())

    def first_prose(self) -> Block | None:
        for block in self.blocks:
            if block.is_prose:
                return block
        return None


def split_front_matter(text: str) -> tuple[str, str]:
    """Split front matter from the body.

    Returns `(front_matter, body)`. Front matter is the YAML fence at the
    very top of the file, if there is one.
    """
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return "", text
    return match.group(0), text[match.end() :]


def parse(text: str) -> Document:
    """Parse a markdown document into blocks.

    Blocks keep their original text verbatim. Paragraphs are separated by
    blank lines; a list, a code fence and a blockquote each stay whole.
    """
    front_matter, body = split_front_matter(text)

    blocks: list[Block] = []
    lines = body.split("\n")
    index = 0
    line_no = 0
    section = ""

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        # Blank line — skip, blocks are separated by blank lines anyway.
        if not stripped:
            index += 1
            line_no += 1
            continue

        # Fenced code block — keep the whole fence verbatim.
        if FENCE_RE.match(line):
            fence = FENCE_RE.match(line).group(1)  # type: ignore[union-attr]
            chunk = [line]
            index += 1
            line_no += 1
            while index < len(lines):
                chunk.append(lines[index])
                line_no += 1
                if FENCE_RE.match(lines[index]) and lines[index].strip().startswith(fence):
                    index += 1
                    break
                index += 1
            blocks.append(
                Block(
                    kind="code",
                    text="\n".join(chunk),
                    start_line=line_no - len(chunk) + 1,
                    section=section,
                )
            )
            continue

        # Heading.
        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            if level <= 2:
                section = title
            blocks.append(
                Block(
                    kind="heading",
                    text=line.rstrip(),
                    level=level,
                    start_line=line_no + 1,
                    section=section,
                )
            )
            index += 1
            line_no += 1
            continue

        # Blockquote — consecutive quote lines are one block.
        if BLOCKQUOTE_RE.match(line):
            chunk = []
            while index < len(lines) and BLOCKQUOTE_RE.match(lines[index]):
                chunk.append(lines[index].rstrip())
                index += 1
                line_no += 1
            blocks.append(
                Block(
                    kind="quote",
                    text="\n".join(chunk),
                    start_line=line_no - len(chunk) + 1,
                    section=section,
                )
            )
            continue

        # List — consecutive list items are one block.
        if LIST_ITEM_RE.match(line):
            chunk = []
            while index < len(lines) and (
                LIST_ITEM_RE.match(lines[index])
                or (lines[index].startswith(("  ", "\t")) and lines[index].strip())
            ):
                chunk.append(lines[index].rstrip())
                index += 1
                line_no += 1
            blocks.append(
                Block(
                    kind="list",
                    text="\n".join(chunk),
                    start_line=line_no - len(chunk) + 1,
                    section=section,
                )
            )
            continue

        # Paragraph — consecutive non-blank, non-special lines.
        chunk = []
        while index < len(lines):
            current = lines[index]
            if not current.strip():
                break
            if (
                HEADING_RE.match(current)
                or FENCE_RE.match(current)
                or LIST_ITEM_RE.match(current)
                or BLOCKQUOTE_RE.match(current)
            ):
                break
            chunk.append(current.rstrip())
            index += 1
            line_no += 1
        blocks.append(
            Block(
                kind="paragraph",
                text="\n".join(chunk),
                start_line=line_no - len(chunk) + 1,
                section=section,
            )
        )

    sections: list[str] = []
    for block in blocks:
        if block.is_heading and block.level <= 2 and block.text not in sections:
            sections.append(block.text)

    return Document(blocks=blocks, front_matter=front_matter, sections=sections)


# --------------------------------------------------------------------------- #
# Structural analysis
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Analysis:
    """What the draft already has, and what it is missing."""

    signals: set[str] = field(default_factory=set)
    #: The signals that are missing — the gaps the planner fills.
    gaps: list[str] = field(default_factory=list)
    hook_text: str = ""
    hook_specificity: int = 0
    word_count: int = 0
    paragraph_count: int = 0
    longest_paragraph: int = 0
    ai_phrase_count: int = 0
    has_cta: bool = False
    has_closing_question: bool = False
    has_proof: bool = False
    sections: list[str] = field(default_factory=list)

    def has(self, signal: str) -> bool:
        return signal in self.signals


#: Signals the analyzer can detect. These are the vocabulary the planner
#: and the frameworks share.
SIGNAL_MISSING_HOOK = "missing_hook"
SIGNAL_GENERIC_HOOK = "generic_hook"
SIGNAL_NO_THESIS = "no_thesis"
SIGNAL_NO_PROBLEM = "no_problem_established"
SIGNAL_NO_TRANSITION = "no_transition"
SIGNAL_NO_PROOF = "no_proof"
SIGNAL_NO_OBJECTION = "unaddressed_objection"
SIGNAL_NO_ACTION = "no_actionable_step"
SIGNAL_NO_SPECIFICS = "no_specifics"
SIGNAL_MISSING_CTA = "missing_cta"
SIGNAL_MISSING_CLOSING_QUESTION = "missing_closing_question"
SIGNAL_ABSTRACT_SECTION = "abstract_section"


def _looks_like_problem(text: str) -> bool:
    """Whether a passage is doing problem work.

    Problem language is about a *state of affairs*, not about a solution:
    "your pipeline breaks", "the results are wrong", "nobody knows which
    one is right". Solution language names a tool, a technique or a
    configuration.
    """
    lowered = text.lower()
    problem_markers = (
        "your ",
        "you're ",
        "the problem",
        "breaks",
        "broke",
        "fails",
        "failed",
        "wrong",
        "silently",
        "nobody",
        "no one",
        "everyone",
        "manual",
        "spreadsheet",
        "tickets",
        "stuck",
        "waiting",
        "guess",
        "guesswork",
        "waste",
        "wasted",
        "cost",
        "slow",
        "painful",
        "pain",
        "confus",
        "hard to",
        "difficult",
        "impossible",
        "afraid",
        "scared",
        "stuck on",
    )
    return any(marker in lowered for marker in problem_markers)


def _looks_like_proof(text: str) -> bool:
    """Whether a passage offers evidence rather than assertion."""
    lowered = text.lower()
    proof_markers = (
        "we measured",
        "we ran",
        "i measured",
        "i ran",
        "benchmark",
        "measured",
        "in production",
        "at ",
        "reported",
        "case study",
        "a team",
        "one team",
        "engineer",
        "studio",
        "startup",
        "the result",
        "results showed",
        "our test",
        "the test",
        "accuracy",
        "p99",
        "latency",
        "throughput",
        "cpu",
        "memory",
    )
    return any(marker in lowered for marker in proof_markers)


def _looks_like_action(text: str) -> bool:
    """Whether a passage gives the reader something to do."""
    lowered = text.lower()
    action_markers = (
        "run ",
        "check ",
        "try ",
        "open ",
        "install ",
        "configure",
        "set ",
        "add ",
        "start by",
        "first, ",
        "step 1",
        "you can ",
        "you should",
        "the fix",
        "the command",
        "```",
    )
    return any(marker in lowered for marker in action_markers)


def _looks_like_objection(text: str) -> bool:
    """Whether a passage addresses a counter-argument."""
    lowered = text.lower()
    objection_markers = (
        "but ",
        "however",
        "that said",
        "the objection",
        "fair enough",
        "fair point",
        "yes, but",
        "unless",
        "the catch",
        "the downside",
        "the trade-off",
        "the tradeoff",
        "you might think",
        "you may think",
        "counter",
    )
    return any(marker in lowered for marker in objection_markers)


def _looks_like_specific(text: str) -> bool:
    """Whether a passage names a concrete instance."""
    from .frameworks import specificity_score

    return specificity_score(text) >= 2


#: The marker CopyForge writes above each block it inserts. It is
#: defined here rather than imported from `planner` because `planner`
#: imports from this module, and a cycle would be the result.
INSERT_MARKER = "<!-- copyforge:"


def _inserted_block_indices(blocks: list[Block]) -> set[int]:
    """The indices of the blocks CopyForge inserted.

    A marker is its own block, and everything between it and the next
    marker — or the next heading — belongs to it. Those blocks are
    excluded from gap detection, because the planner already chose them
    to answer a gap and must not be told the gap is still open.
    """
    indices: set[int] = set()
    in_inserted = False
    for index, block in enumerate(blocks):
        if block.text.strip().startswith(INSERT_MARKER):
            in_inserted = True
            indices.add(index)
            continue
        if in_inserted:
            if block.is_heading:
                in_inserted = False
                continue
            indices.add(index)
    return indices


def _signals_resolved_by_inserted(document: Document, inserted: set[int]) -> set[str]:
    """The signals that an already-inserted framework has resolved.

    The marker names the framework; the framework declares the signals it
    resolves. So the credit for a gap is derived from the library rather
    than guessed, and a gap that has been answered does not re-open.
    """
    from .frameworks import FRAMEWORKS

    resolved: set[str] = set()
    by_slug = {f.slug: f for f in FRAMEWORKS}
    for index in inserted:
        text = document.blocks[index].text.strip()
        if not text.startswith(INSERT_MARKER):
            continue
        slug = text[len(INSERT_MARKER) :].rstrip("->").strip()
        framework = by_slug.get(slug)
        if framework is not None:
            resolved.update(framework.resolves)
    return resolved


def analyze(document: Document) -> Analysis:
    """Work out what the draft has and what it is missing.

    The signals here are the shared vocabulary between the analyzer and
    the framework library: a framework declares which signals it
    resolves, and the planner matches the two.
    """
    analysis = Analysis()
    analysis.sections = list(document.sections)

    prose = document.prose_blocks()
    analysis.paragraph_count = len(prose)
    analysis.word_count = sum(b.word_count() for b in prose)
    analysis.longest_paragraph = max((b.word_count() for b in prose), default=0)

    # Gap detection looks only at the *author's* prose. CopyForge's own
    # blocks are excluded: they were chosen to answer a gap, so seeing
    # them would make the pipeline think the gap is still open — and a
    # second run would insert a second block for it.
    inserted = _inserted_block_indices(document.blocks)
    author_prose = [b for b in prose if not any(b is document.blocks[i] for i in inserted)]

    # ...but a gap that an already-inserted framework resolves is not
    # open. The marker names the framework, and the framework declares
    # which signals it resolves, so the credit is derived rather than
    # guessed.
    resolved_by_inserted = _signals_resolved_by_inserted(document, inserted)

    all_text = "\n".join(b.text for b in document.blocks)
    from .frameworks import count_ai_phrases, looks_like_question, specificity_score

    analysis.ai_phrase_count = count_ai_phrases(all_text)

    # -- the hook ------------------------------------------------------
    hook = document.first_prose()
    if hook is None:
        analysis.gaps.append(SIGNAL_MISSING_HOOK)
        analysis.signals.add(SIGNAL_MISSING_HOOK)
        analysis.signals.add(SIGNAL_GENERIC_HOOK)
    else:
        analysis.hook_text = hook.text.strip()
        analysis.hook_specificity = specificity_score(analysis.hook_text)
        if analysis.hook_specificity == 0:
            analysis.signals.add(SIGNAL_GENERIC_HOOK)
            analysis.gaps.append(SIGNAL_GENERIC_HOOK)
        if analysis.hook_text.lower().startswith(
            ("in this article", "this article", "today", "have you ever")
        ):
            analysis.signals.add(SIGNAL_GENERIC_HOOK)
            if SIGNAL_GENERIC_HOOK not in analysis.gaps:
                analysis.gaps.append(SIGNAL_GENERIC_HOOK)

    # -- problem / thesis ----------------------------------------------
    problem_blocks = [b for b in author_prose if _looks_like_problem(b.text)]
    if not problem_blocks:
        analysis.signals.add(SIGNAL_NO_PROBLEM)
        analysis.gaps.append(SIGNAL_NO_PROBLEM)

    thesis_blocks = [
        b
        for b in author_prose
        if any(
            marker in b.text.lower()
            for marker in (
                "the point is",
                "the trick is",
                "the difference is",
                "the difference was",
                "the answer is",
                "the reason is",
                "the cause is",
                "the problem is",
                "this guide",
                "this article is",
                "the fix is",
                "the real issue",
                "what matters is",
            )
        )
    ]
    if not thesis_blocks:
        analysis.signals.add(SIGNAL_NO_THESIS)
        analysis.gaps.append(SIGNAL_NO_THESIS)

    # -- proof ---------------------------------------------------------
    proof_blocks = [b for b in author_prose if _looks_like_proof(b.text)]
    if proof_blocks:
        analysis.signals.add("has_proof")
        analysis.has_proof = True
    else:
        analysis.signals.add(SIGNAL_NO_PROOF)
        analysis.gaps.append(SIGNAL_NO_PROOF)

    # -- objection / action / specifics --------------------------------
    if not any(_looks_like_objection(b.text) for b in author_prose):
        analysis.signals.add(SIGNAL_NO_OBJECTION)
        analysis.gaps.append(SIGNAL_NO_OBJECTION)

    if not any(_looks_like_action(b.text) for b in author_prose):
        analysis.signals.add(SIGNAL_NO_ACTION)
        analysis.gaps.append(SIGNAL_NO_ACTION)

    if not any(_looks_like_specific(b.text) for b in author_prose):
        analysis.signals.add(SIGNAL_NO_SPECIFICS)
        analysis.gaps.append(SIGNAL_NO_SPECIFICS)

    # -- transitions ----------------------------------------------------
    # A transition is a connective that carries the reader from one
    # claim to the next. The marker list is deliberately broad: a
    # paragraph that opens with "But", "So", "That said" or "The
    # difference" is doing transitional work, and detecting that
    # reliably matters more than classifying the exact kind.
    transition_markers = (
        "but ",
        "so ",
        "now ",
        "which means",
        "and that",
        "therefore",
        "that said",
        "the difference",
        "this means",
        "as a result",
        "because ",
        "instead",
        "yet ",
        "then ",
        "however",
        "in practice",
    )
    if not any(
        any(marker in b.text.lower() for marker in transition_markers) for b in author_prose[1:]
    ):
        analysis.signals.add(SIGNAL_NO_TRANSITION)
        analysis.gaps.append(SIGNAL_NO_TRANSITION)

    # -- abstract sections ----------------------------------------------
    abstract_sections = [
        b
        for b in author_prose
        if b.word_count() >= 25
        and not _looks_like_specific(b.text)
        and not _looks_like_action(b.text)
    ]
    if abstract_sections:
        analysis.signals.add(SIGNAL_ABSTRACT_SECTION)
        analysis.gaps.append(SIGNAL_ABSTRACT_SECTION)

    # -- CTA / closing question ----------------------------------------
    cta_blocks = [
        b
        for b in author_prose
        if any(
            marker in b.text.lower()
            for marker in ("try it", "give it a", "go ahead", "start with", "run it", "download", "sign up")
        )
    ]
    if cta_blocks:
        analysis.has_cta = True
    else:
        analysis.signals.add(SIGNAL_MISSING_CTA)
        analysis.gaps.append(SIGNAL_MISSING_CTA)

    tail = author_prose[-3:] if author_prose else []
    if any(looks_like_question(b.text) for b in tail):
        analysis.has_closing_question = True
    else:
        analysis.signals.add(SIGNAL_MISSING_CLOSING_QUESTION)
        analysis.gaps.append(SIGNAL_MISSING_CLOSING_QUESTION)

    # Credit the gaps an already-inserted framework has answered.
    for gap in list(analysis.gaps):
        if gap in resolved_by_inserted:
            analysis.gaps.remove(gap)

    return analysis
