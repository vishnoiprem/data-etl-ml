#!/usr/bin/env python3
"""
nb_assemble.py — assemble notebooks from content files.

The notebook *content* lives in plain files under
``resources/notebook_src/<slug>/``, numbered in order:

    00_header.md     the title block and "in this notebook you will" bullets
    01.md            a markdown cell
    02.py            a code cell
    03.md            ...
    99_exercises.md  the exercise prompts
    99_solution.md   the collapsed solution

The generator reads them in numeric order and emits a valid nbformat 4.5
notebook. Keeping the content in files rather than in Python string
literals means no amount of quoting, backticks or docstrings inside a
cell can break the generator.

A file may also carry a directive on its first line:

    #! title: My Title
    #! module: Module 1 · Composer Fundamentals & Model
    #! lecture: Lecture 1.1–1.2

Usage:
    python resources/nb_assemble.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nb_builder import Notebook

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(__file__).resolve().parent / "notebook_src"
OUT = ROOT / "notebooks"

DIRECTIVE = re.compile(r"^#!\s*(\w+)\s*:\s*(.*)$")


def read_directives(text: str) -> tuple[dict[str, str], str]:
    """Split leading ``#!`` directives off the top of a content file.

    Args:
        text: The file's content.

    Returns:
        A ``(directives, body)`` tuple.
    """
    directives: dict[str, str] = {}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        match = DIRECTIVE.match(lines[index])
        if not match:
            break
        directives[match.group(1)] = match.group(2).strip()
        index += 1
    return directives, "\n".join(lines[index:]).lstrip("\n")


def build(slug: str) -> Notebook:
    """Build one notebook from its content directory.

    Args:
        slug: The notebook's slug, e.g. ``01-setup-and-environment``.

    Returns:
        The assembled notebook.

    Raises:
        FileNotFoundError: When the content directory does not exist.
        ValueError: When the header file is missing or malformed.
    """
    directory = SRC / slug
    if not directory.exists():
        raise FileNotFoundError(f"no content directory for {slug!r}: {directory}")

    header_path = directory / "00_header.md"
    if not header_path.exists():
        raise ValueError(f"{slug}: missing 00_header.md")

    header_directives, header_body = read_directives(
        header_path.read_text(encoding="utf-8")
    )
    title = header_directives.get("title", slug)
    nb = Notebook(title, slug)

    # The header file's body holds the bullets; the title/module/lecture
    # come from the directives.
    bullets = [
        line.strip()[2:].strip()
        for line in header_body.splitlines()
        if line.strip().startswith("- ")
    ]
    nb.markdown(
        _header(
            header_directives.get("number", "00"),
            title,
            header_directives.get("module", ""),
            header_directives.get("lecture", ""),
            bullets,
        )
    )

    files = sorted(
        path
        for path in directory.iterdir()
        if path.suffix in (".md", ".py") and path.name != "00_header.md"
    )

    exercises_body = ""
    solution_body = ""
    for path in files:
        text = path.read_text(encoding="utf-8")
        if path.name.startswith("99_exercises"):
            exercises_body = text
            continue
        if path.name.startswith("99_solution"):
            solution_body = text
            continue
        if path.suffix == ".md":
            nb.markdown(text.strip("\n"))
        else:
            nb.code(text.strip("\n"))

    if exercises_body:
        nb.markdown(exercises_body.strip("\n"))
    if solution_body:
        nb.markdown(
            "<details>\n"
            "<summary><b>Solution (click to reveal)</b></summary>\n\n"
            + solution_body.strip("\n")
            + "\n\n</details>"
        )

    return nb


def _header(number: str, title: str, module: str, lecture: str, bullets: list[str]) -> str:
    """Build the standard opening markdown block.

    Args:
        number: The notebook number.
        title: The notebook title.
        module: The module name.
        lecture: The lecture range.
        bullets: The "In this notebook you will" bullets.

    Returns:
        The markdown text.
    """
    lines = [
        f"# {number} · {title}",
        "",
        f"> **{module} · {lecture}**",
        "",
        "In this notebook you will:",
        "",
    ]
    lines.extend(f"- {item}" for item in bullets)
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    """Build every notebook that has a content directory.

    Returns:
        0 when all notebooks built, 1 otherwise.
    """
    slugs = sorted(path.name for path in SRC.iterdir() if path.is_dir())
    if not slugs:
        print(f"no content directories under {SRC}")
        return 1

    failures = 0
    for slug in slugs:
        try:
            nb = build(slug)
        except Exception as exc:  # noqa: BLE001
            print(f"  FAIL  {slug}: {type(exc).__name__}: {exc}")
            failures += 1
            continue
        path = nb.write(OUT)
        code_cells = sum(1 for c in nb.cells if c["cell_type"] == "code")
        print(f"  BUILT {path.name:<44} {len(nb.cells)} cells ({code_cells} code)")

    print()
    print(f"{len(slugs) - failures}/{len(slugs)} notebooks built")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
