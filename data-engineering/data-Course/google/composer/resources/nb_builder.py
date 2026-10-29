#!/usr/bin/env python3
"""
nb_builder.py — a tiny helper for emitting nbformat 4.5 notebooks.

The Composer course notebooks are generated rather than hand-written so
that the structural rules hold everywhere:

  * ``nbformat`` 4.5 with ``nbformat_minor`` 5
  * the exact ``metadata.kernelspec`` and ``metadata.language_info``
    the course requires
  * every cell carries a unique 8-character hex ``id``
  * ``source`` is a list of strings, each ending with ``\\n`` except the
    last — the canonical nbformat encoding
  * code cells start with ``execution_count: null`` and ``outputs: []``

The builder never executes anything; ``verify_notebooks.py`` does that.

Usage:
    from nb_builder import Notebook

    nb = Notebook("01 · Setup & Environment")
    nb.markdown("# Hello")
    nb.code("print('hi')")
    nb.write(Path("notebooks/01-demo.ipynb"))
"""
from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any

KERNELSPEC: dict[str, Any] = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}

LANGUAGE_INFO: dict[str, Any] = {
    "name": "python",
    "version": "3.13.0",
    "mimetype": "text/x-python",
    "codemirror_mode": {"name": "ipython", "version": 3},
    "pygments_lexer": "ipython3",
    "nbconvert_exporter": "python",
    "file_extension": ".py",
}


def _split_source(text: str) -> list[str]:
    """Split source text into the canonical nbformat list-of-lines form.

    Every line keeps its trailing newline except the very last one.

    Args:
        text: The full source text.

    Returns:
        A list of strings.
    """
    if not text:
        return []
    lines = text.splitlines(keepends=True)
    if lines and lines[-1].endswith("\n"):
        lines[-1] = lines[-1][:-1]
    return lines


class Notebook:
    """Accumulate cells and write a valid nbformat 4.5 notebook.

    Attributes:
        title: The notebook's title, used in the file name.
        cells: The cell list, in order.
        ids: The set of cell ids already handed out.
    """

    def __init__(self, title: str, slug: str) -> None:
        """Create a notebook.

        Args:
            title: A human-readable title.
            slug: The file-name stem, without the ``.ipynb`` extension.
        """
        self.title = title
        self.slug = slug
        self.cells: list[dict[str, Any]] = []
        self.ids: set[str] = set()

    # -- internals ----------------------------------------------------

    def _new_id(self) -> str:
        """Return a fresh 8-character hex cell id.

        Returns:
            An id that has not been used in this notebook.
        """
        while True:
            candidate = secrets.token_hex(4)
            if candidate not in self.ids:
                self.ids.add(candidate)
                return candidate

    # -- cell constructors --------------------------------------------

    def markdown(self, text: str) -> "Notebook":
        """Append a markdown cell.

        Args:
            text: The markdown body.

        Returns:
            self, for chaining.
        """
        self.cells.append(
            {
                "cell_type": "markdown",
                "id": self._new_id(),
                "metadata": {},
                "source": _split_source(text.strip("\n") + "\n"),
            }
        )
        return self

    def code(self, text: str) -> "Notebook":
        """Append a code cell with no outputs.

        The source is compiled before it is added, so a typo or a
        prematurely-closed string literal is caught at generation time
        rather than at execution time.

        Args:
            text: The Python body.

        Returns:
            self, for chaining.

        Raises:
            SyntaxError: When the source does not parse.
        """
        compile(text.strip("\n") + "\n", f"<cell:{len(self.cells)}>", "exec")
        self.cells.append(
            {
                "cell_type": "code",
                "execution_count": None,
                "id": self._new_id(),
                "metadata": {},
                "outputs": [],
                "source": _split_source(text.strip("\n") + "\n"),
            }
        )
        return self

    # -- output --------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return the notebook as a plain dict.

        Returns:
            The nbformat 4.5 structure.
        """
        return {
            "cells": self.cells,
            "metadata": {
                "kernelspec": dict(KERNELSPEC),
                "language_info": dict(LANGUAGE_INFO),
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }

    def write(self, directory: Path) -> Path:
        """Write the notebook to ``directory/<slug>.ipynb``.

        Args:
            directory: The target directory.

        Returns:
            The path written.
        """
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.slug}.ipynb"
        path.write_text(
            json.dumps(self.to_dict(), indent=1, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return path


# --------------------------------------------------------------------------
# Reusable code fragments
# --------------------------------------------------------------------------

#: The path-resolution preamble every notebook that touches the project uses.
PREAMBLE = '''from pathlib import Path
import sys

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent.parent
sys.path.insert(0, str(COURSE_ROOT / "project" / "core"))
sys.path.insert(0, str(COURSE_ROOT / "project"))

print("COURSE_ROOT =", COURSE_ROOT)
print("project/ present:", (COURSE_ROOT / "project").exists())
print("core/ present:", (COURSE_ROOT / "project" / "core").exists())'''

#: A preamble variant that also imports the local runner.
PREAMBLE_WITH_RUNNER = PREAMBLE + '''

import local_runner
print("local_runner loaded from:", local_runner.__file__)'''


def header(number: str, title: str, module: str, lecture: str, bullets: list[str]) -> str:
    """Build the standard opening markdown block.

    Args:
        number: The notebook number, e.g. ``"01"``.
        title: The notebook title.
        module: The module line, e.g. ``"Module 1 · Composer Fundamentals & Model"``.
        lecture: The lecture line, e.g. ``"Lecture 1.1–1.2"``.
        bullets: The "In this notebook you will:" bullets.

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


def exercises(prompts: list[str], solution: str) -> tuple[str, str]:
    """Build the exercises section and its collapsed solution.

    Args:
        prompts: The exercise prompts, as markdown bullets.
        solution: The solution markdown.

    Returns:
        A ``(exercises_markdown, solution_markdown)`` tuple.
    """
    body = ["## Exercises", ""]
    body.extend(prompts)
    body.append("")
    sol = [
        "<details>",
        "<summary><b>Solution (click to reveal)</b></summary>",
        "",
        solution.strip("\n"),
        "",
        "</details>",
    ]
    return "\n".join(body), "\n".join(sol)
