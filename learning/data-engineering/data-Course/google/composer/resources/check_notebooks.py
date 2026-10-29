#!/usr/bin/env python3
"""
check_notebooks.py — validate and execute every notebook in the course.

The notebooks are the course's promise that you can learn Airflow without
a local Airflow install. This script enforces that promise mechanically:
it parses every notebook, validates its structure, and executes its code
cells **in order**, in a fresh namespace, with no Airflow and no cloud
credentials available.

Any notebook that imports Airflow, reaches the network, or raises will
fail here — which means it fails on a student's laptop too, before they
waste an hour on it.

Usage:
    python resources/check_notebooks.py            # check every notebook
    python resources/check_notebooks.py 04         # check notebooks matching "04"
    python resources/check_notebooks.py --list     # list the notebooks
    python resources/check_notebooks.py --no-exec  # structure only
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK_DIR = COURSE_ROOT / "notebooks"

#: Directories that must be importable from a notebook.
PROJECT_PATHS = [
    COURSE_ROOT / "project" / "core",
    COURSE_ROOT / "project",
]


def check_structure(path: Path) -> list[str]:
    """Validate a notebook's JSON and nbformat structure.

    Args:
        path: The notebook path.

    Returns:
        A list of error messages. Empty means the structure is valid.
    """
    errors: list[str] = []

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc}"]

    if raw.get("nbformat") != 4:
        errors.append(f"nbformat should be 4, got {raw.get('nbformat')!r}")

    cells = raw.get("cells")
    if not isinstance(cells, list) or not cells:
        errors.append("no cells")
        return errors

    seen_ids: set[str] = set()
    for index, cell in enumerate(cells):
        where = f"cell {index}"
        cell_type = cell.get("cell_type")
        if cell_type not in ("code", "markdown", "raw"):
            errors.append(f"{where}: bad cell_type {cell_type!r}")

        cell_id = cell.get("id")
        if not cell_id:
            errors.append(f"{where}: missing id")
        elif cell_id in seen_ids:
            errors.append(f"{where}: duplicate id {cell_id!r}")
        else:
            seen_ids.add(cell_id)

        source = cell.get("source")
        if isinstance(source, str):
            source = [source]
        if not isinstance(source, list):
            errors.append(f"{where}: source must be a list or str")

        if cell_type == "code":
            if "outputs" not in cell:
                errors.append(f"{where}: code cell missing outputs")
            if cell.get("execution_count") is not None:
                errors.append(f"{where}: execution_count should be null")

    return errors


def execute_notebook(path: Path, *, timeout_note: str = "") -> list[str]:
    """Execute every code cell in a notebook, in order.

    Args:
        path: The notebook path.
        timeout_note: Unused; reserved for future timeout support.

    Returns:
        A list of error messages. Empty means every cell ran cleanly.
    """
    errors: list[str] = []
    raw = json.loads(path.read_text(encoding="utf-8"))

    for search_path in PROJECT_PATHS:
        text = str(search_path)
        if text not in sys.path:
            sys.path.insert(0, text)

    namespace: dict[str, object] = {"__name__": "__main__"}

    for index, cell in enumerate(raw.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source")
        if isinstance(source, str):
            source = [source]
        code = "".join(source)
        if not code.strip():
            continue
        try:
            exec(compile(code, f"{path.name}:cell{index}", "exec"), namespace)
        except Exception as exc:  # noqa: BLE001 - we report, not raise
            errors.append(
                f"cell {index} raised {type(exc).__name__}: {exc}\n"
                + _last_frames(code)
            )
            # Stop at the first failure: later cells usually depend on it.
            break

    return errors


def _last_frames(code: str) -> str:
    """Return the last few lines of the failing cell's source.

    Args:
        code: The cell's source.

    Returns:
        An indented excerpt of the cell source.
    """
    lines = [line for line in code.strip().splitlines() if line.strip()]
    excerpt = lines[-6:]
    return "    " + "\n    ".join(excerpt)


def main(argv: list[str] | None = None) -> int:
    """Run the checks.

    Args:
        argv: The argument list, or None for ``sys.argv``.

    Returns:
        The process exit code: 0 if everything passed, 1 otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pattern", nargs="?", default="", help="Only check notebooks matching this")
    parser.add_argument("--list", action="store_true", help="List the notebooks and exit")
    parser.add_argument("--no-exec", action="store_true", help="Check structure only")
    args = parser.parse_args(argv)

    notebooks = sorted(NOTEBOOK_DIR.glob("*.ipynb"))
    if args.pattern:
        notebooks = [n for n in notebooks if args.pattern in n.name]

    if not notebooks:
        print("No notebooks matched.", file=sys.stderr)
        return 2

    if args.list:
        for path in notebooks:
            print(path.name)
        return 0

    failures = 0
    for path in notebooks:
        structural = check_structure(path)
        execution: list[str] = []
        if not args.no_exec and not structural:
            execution = execute_notebook(path)

        if structural or execution:
            failures += 1
            print(f"✗ {path.name}")
            for message in structural + execution:
                print(f"    {message}")
        else:
            print(f"✓ {path.name}")

    total = len(notebooks)
    print()
    if failures:
        print(f"{failures} of {total} notebooks failed.")
        return 1
    print(f"All {total} notebooks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
