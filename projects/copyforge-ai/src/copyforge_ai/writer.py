"""The writer — generates each planned block and splices it into the draft.

The writer is the only part of the pipeline that changes the author's
text, so it is also the part with the most rules:

* **The author's blocks are never rewritten.** Only insertions are
  added. The original prose is copied through verbatim.
* **Insertions are marked.** Every block CopyForge adds is wrapped in an
  HTML comment naming the framework that produced it. That marker is
  what makes a second run idempotent, and it is what lets a reader (or
  an editor) see exactly what was added and by which pattern.
* **An empty generation is skipped.** If the model returns nothing, the
  insertion is dropped rather than leaving a hole in the article.
* **A block is never inserted where its framework is invalid.** The
  planner already guarantees that; the writer double-checks.

The output keeps the front matter intact and preserves the original
ordering of everything that was there.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .frameworks import Framework, get_framework
from .llm import LLMRouter
from .markdown import Document, analyze, parse
from .planner import MARKER_PREFIX, MARKER_SUFFIX, Insertion, Plan, plan_copy

#: Matches a marker CopyForge previously wrote.
MARKER_RE = re.compile(rf"{re.escape(MARKER_PREFIX)}(?P<slug>[\w-]+){re.escape(MARKER_SUFFIX)}")


@dataclass(slots=True)
class WrittenBlock:
    """A generated block and where it landed."""

    framework: str
    position: str
    anchor: int
    heading: str = ""
    body: str = ""
    resolves: str = ""
    reason: str = ""

    def render(self) -> str:
        """The block as markdown, including its marker."""
        parts = [f"{MARKER_PREFIX}{self.framework}{MARKER_SUFFIX}"]
        if self.heading:
            parts.append(f"### {self.heading}")
        if self.body:
            parts.append(self.body.strip())
        return "\n\n".join(parts)


@dataclass(slots=True)
class WriteResult:
    """The result of writing one draft."""

    document: str = ""
    blocks: list[WrittenBlock] = field(default_factory=list)
    plan: Plan | None = None
    #: Insertions the plan wanted but the writer skipped.
    skipped: list[str] = field(default_factory=list)
    #: The analysis of the *input* draft, before writing.
    before: object | None = None
    #: The analysis of the *output* draft, after writing.
    after: object | None = None

    @property
    def changed(self) -> bool:
        return bool(self.blocks)


def existing_slugs(text: str) -> set[str]:
    """The framework slugs already inserted in this document.

    This is what makes a second run idempotent: a draft that already
    carries a PAS block does not get a second one.
    """
    return set(MARKER_RE.findall(text))


def _blocks_between(document: Document, insertions: list[Insertion]) -> list[str]:
    """The document's blocks, with the insertions spliced in.

    Insertions are grouped by anchor. An anchor of `-1` goes at the very
    top; any other anchor goes immediately *after* the block with that
    index. Anchors past the end of the document go at the end.
    """
    by_anchor: dict[int, list[Insertion]] = {}
    for insertion in insertions:
        by_anchor.setdefault(insertion.anchor, []).append(insertion)

    output: list[str] = []
    for insertion in by_anchor.get(-1, []):
        output.append(insertion.render_text)

    for index, block in enumerate(document.blocks):
        output.append(block.text)
        for insertion in by_anchor.get(index, []):
            output.append(insertion.render_text)

    # Anything anchored past the end of the document goes at the end.
    last_index = len(document.blocks) - 1
    for anchor, group in by_anchor.items():
        if anchor > last_index:
            for insertion in group:
                output.append(insertion.render_text)

    return output


def _write_block(router: LLMRouter, insertion: Insertion, system: str) -> WrittenBlock:
    """Generate one block.

    Returns a block with an empty body when the model produced nothing —
    the caller drops it.
    """
    body = router.complete(insertion.prompt, system=system, max_tokens=400)
    body = (body or "").strip()

    # A model sometimes wraps its answer in a preamble. Strip the
    # obvious ones rather than shipping them into the article.
    body = re.sub(r"^(here(?:'s| is) (?:the|a)[^\n:]*:\s*\n+)", "", body, flags=re.IGNORECASE)
    body = re.sub(r"^(block body|answer|response)\s*:\s*\n+", "", body, flags=re.IGNORECASE)

    return WrittenBlock(
        framework=insertion.framework,
        position=insertion.position,
        anchor=insertion.anchor,
        heading=insertion.heading,
        body=body,
        resolves=insertion.resolves,
        reason=insertion.reason,
    )


SYSTEM_PROMPT = (
    "You write direct-response copy for practitioners. You are given a "
    "framework with named slots and an article's context. Fill each slot "
    "in one or two sentences, in that order, separated by a blank line. "
    "Be concrete, be short, and invent nothing."
)


def write_article(
    text: str,
    router: LLMRouter | None = None,
    system: str = SYSTEM_PROMPT,
) -> WriteResult:
    """Insert copy into a markdown draft.

    The draft is analysed, a plan is built, each planned block is
    generated, and the blocks are spliced in. The author's own text is
    never altered.
    """
    document = parse(text)
    before = analyze(document)

    already = existing_slugs(text)
    plan = plan_copy(document, before)

    # Drop insertions whose framework is already in the document — that
    # is the idempotence rule.
    live: list[Insertion] = []
    for insertion in plan.insertions:
        if insertion.framework in already:
            plan.unresolved.append(insertion.resolves)
            continue
        live.append(insertion)

    result = WriteResult(plan=plan, before=before)
    if not live:
        result.document = text
        result.after = analyze(parse(text))
        return result

    written: list[WrittenBlock] = []
    for insertion in live:
        try:
            framework: Framework = get_framework(insertion.framework)
        except KeyError:
            result.skipped.append(insertion.framework)
            continue
        if not framework.applies_to(insertion.position):
            result.skipped.append(insertion.framework)
            continue

        block = _write_block(router, insertion, system)
        if not block.body:
            result.skipped.append(insertion.framework)
            continue
        written.append(block)

    if not written:
        result.document = text
        result.after = analyze(parse(text))
        return result

    # Give each insertion its rendered text so the splicing step can use
    # one code path.
    rendered_by_framework = {b.framework: b.render() for b in written}
    for insertion in live:
        insertion.render_text = rendered_by_framework.get(insertion.framework, "")

    parts = _blocks_between(document, [i for i in live if i.render_text])
    body = "\n\n".join(part for part in parts if part.strip())

    output = ""
    if document.front_matter:
        output += document.front_matter.rstrip("\n") + "\n\n"
    output += body.rstrip("\n") + "\n"

    result.document = output
    result.blocks = written
    result.after = analyze(parse(output))
    return result
