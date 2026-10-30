#!/usr/bin/env python3
"""
build_notebooks.py — generate the course notebooks.

The notebooks are generated from Python rather than hand-written as JSON,
because a notebook is mostly prose and the JSON quoting is error-prone.
This script is the source of truth; run it after editing a notebook.

Usage:
    python resources/build_notebooks.py
    python resources/build_notebooks.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = ROOT / "notebooks"

#: Notebook sources, keyed by output filename. Each entry is a builder
#: module exposing a `build()` function returning the notebook dict.
NOTEBOOK_SOURCES: dict[str, str] = {
    "01-the-semantic-layer.ipynb": "notebook_01",
    "02-measures-and-dimensions.ipynb": "notebook_02",
    "03-joins-and-grain.ipynb": "notebook_03",
    "04-the-date-spine.ipynb": "notebook_04",
    "05-looker-studio-and-looker.ipynb": "notebook_05",
    "06-end-to-end-project.ipynb": "notebook_06",
}


def _cell_id(prefix: str, source: str) -> str:
    """Return a stable cell id derived from the cell's source.

    Python's built-in ``hash()`` for strings is randomised per process
    (PYTHONHASHSEED), so using it here would make ``--check`` report every
    notebook as stale on every run. A SHA-256 digest is stable across
    processes, machines and Python versions.

    Args:
        prefix: The cell-type prefix, ``md`` or ``cd``.
        source: The cell source.

    Returns:
        A cell id of the form ``md1a2b3c4d``.
    """
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    return f"{prefix}{digest[:8]}"


def md(source: str) -> dict:
    """Build a markdown cell.

    Args:
        source: The markdown text.

    Returns:
        The cell dict.
    """
    return {
        "cell_type": "markdown",
        "id": _cell_id("md", source),
        "metadata": {},
        "source": source.strip("\n").splitlines(keepends=True),
    }


def code(source: str) -> dict:
    """Build a code cell.

    Args:
        source: The Python source.

    Returns:
        The cell dict.
    """
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": _cell_id("cd", source),
        "metadata": {},
        "outputs": [],
        "source": source.strip("\n").splitlines(keepends=True),
    }


def notebook(cells: list[dict]) -> dict:
    """Build a notebook from a list of cells.

    Args:
        cells: The cells.

    Returns:
        The notebook dict.
    """
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python (data analysis course)",
                "language": "python",
                "name": "data-analysis-course",
            },
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main(argv: list[str] | None = None) -> int:
    """Build every notebook from its builder module.

    Args:
        argv: The argument list, or None to read from `sys.argv`.

    Returns:
        The process exit code.
    """
    import importlib

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="Verify without writing")
    args = parser.parse_args(argv)

    sys.path.insert(0, str(Path(__file__).resolve().parent))

    failures = 0
    for filename, module_name in NOTEBOOK_SOURCES.items():
        module = importlib.import_module(module_name)
        payload = json.dumps(module.build(), indent=1) + "\n"
        target = NOTEBOOKS / filename

        if args.check:
            current = target.read_text(encoding="utf-8") if target.exists() else ""
            status = "ok" if current == payload else "STALE"
            if current != payload:
                failures += 1
            print(f"{status:<6} {filename}")
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload, encoding="utf-8")
        print(f"wrote {target.relative_to(ROOT)}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
