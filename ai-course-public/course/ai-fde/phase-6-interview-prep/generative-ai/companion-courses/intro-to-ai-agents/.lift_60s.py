#!/usr/bin/env python3
"""Lift the 60-second script from each lecture's Production addendum to the top.

For each lecture .md file:
1. Find the blockquote that immediately follows "The 60-second script:"
2. Insert a new `## In 60 seconds` blockquote block between the FDE-framing
   line and `## The 3 things you'll learn`
3. The lifted content is the blockquote verbatim, prefixed with the section
   heading and a 1-line context line.

The original 60-second script in the Production addendum is LEFT IN PLACE
because the section structure (interview question framing) belongs there.
This is a non-destructive lift.
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Marker that appears in the FDE-framing line (the line just above `## The 3
# things you'll learn`). It's a `>` blockquote ending in a period or similar.
FDE_LINE = re.compile(r"^> \*\*FDE framing in one line:\*\*.*$", re.MULTILINE)
# Marker for the start of "3 things" — the anchor for insertion.
THREE_THINGS = re.compile(r"^## The 3 things you'll learn\s*$", re.MULTILINE)

# Pattern that finds the 60-second blockquote. We look for a paragraph that
# ends with "The 60-second script:" or similar, then capture the blockquote
# that follows until the next blank-line-separated paragraph.
SEC60_LEAD = re.compile(
    r"^.*?60[- ]second script:\s*\n\n> \"[^\n]+",
    re.MULTILINE,
)


def extract_60s_block(body: str) -> str | None:
    """Return the multi-line blockquote that constitutes the 60-second script.

    Walks the body line-by-line from the first occurrence of
    "60[- ]second script:" forward, capturing consecutive `>`-prefixed lines
    (with or without an opening `"`).
    """
    lines = body.splitlines()
    # Find the first line that introduces the 60-second script.
    start = None
    for i, line in enumerate(lines):
        if "60-second script:" in line or "60 second script:" in line:
            start = i
            break
    if start is None:
        return None

    # Walk forward: skip the empty line, then collect blockquote lines.
    i = start + 1
    # Allow one or two blank lines before the blockquote.
    while i < len(lines) and lines[i].strip() == "":
        i += 1

    quote_lines: list[str] = []
    while i < len(lines) and (lines[i].startswith(">") or lines[i].strip() == ""):
        if lines[i].startswith(">"):
            quote_lines.append(lines[i])
        i += 1
        # A blank line in the middle of a blockquote is fine; continue.
        if i < len(lines) and lines[i].strip() == "":
            # peek ahead: if the next non-blank line is also `>`, keep going.
            j = i
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and lines[j].startswith(">"):
                i = j
                continue
            break

    if not quote_lines:
        return None
    return "\n".join(quote_lines).strip()


def lift_to_top(body: str) -> tuple[str, str | None]:
    """Return (new_body, lifted_block_or_None).

    Inserts a `## In 60 seconds` block between the FDE framing blockquote and
    `## The 3 things you'll learn`. The block is the verbatim blockquote of
    the existing 60-second script.
    """
    quote = extract_60s_block(body)
    if quote is None:
        return body, None

    # Build the inserted block.
    # The first line of `quote` already starts with `>`. We keep it as a
    # blockquote with no extra wrapping. Add 2-3 leading lines for context.
    insert = (
        "## In 60 seconds\n\n"
        f"{quote}\n\n"
        "**The wrong choice is to read past this block.** "
        "The right choice is to recite the 60-second script before you read "
        "any other content. The rest of the lecture is the receipt; this is the punchline.\n"
    )

    # Find the FDE framing line and the `## The 3 things` heading, and
    # insert the block in between.
    m_framing = FDE_LINE.search(body)
    m_three = THREE_THINGS.search(body)
    if not m_framing or not m_three:
        return body, None
    if m_framing.end() > m_three.start():
        # Malformed file: FDE line appears after `## The 3 things`. Skip.
        return body, None

    # The FDE framing line is followed by a blank line and then `## The 3
    # things`. Insert AFTER the blank line, BEFORE `## The 3 things`.
    # Easiest: split at `## The 3 things`, prepend the FDE framing block,
    # then the insert, then continue.
    before = body[: m_three.start()]
    after = body[m_three.start():]
    new_body = before.rstrip() + "\n\n" + insert + "\n" + after
    return new_body, quote


def process(file: Path) -> tuple[bool, str]:
    text = file.read_text()
    if "## In 60 seconds" in text:
        return False, "already lifted"
    new_text, lifted = lift_to_top(text)
    if lifted is None:
        return False, "no 60-second script found"
    file.write_text(new_text)
    return True, f"lifted {len(lifted)} chars"


def main() -> None:
    files = sorted(ROOT.glob("s*/L*.md"))
    lifted, skipped = 0, 0
    for f in files:
        ok, msg = process(f)
        if ok:
            lifted += 1
        else:
            skipped += 1
        print(f"  {f.relative_to(ROOT)}: {msg}")
    print(f"\nLifted: {lifted} | Skipped: {skipped} | Total: {len(files)}")


if __name__ == "__main__":
    main()
