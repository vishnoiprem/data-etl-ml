#!/usr/bin/env python3
"""
verify_notebooks.py — validate the Composer course notebooks.

For every notebook in ``notebooks/`` this checks:

  1. the file parses as JSON;
  2. ``nbformat`` considers the structure valid (nbformat 4.5);
  3. every cell has a unique 8-character hex ``id``;
  4. the metadata matches the course's required ``kernelspec`` and
     ``language_info`` exactly;
  5. ``source`` is a list of strings whose last element has no trailing
     newline and whose others do;
  6. code cells carry ``execution_count: null`` and ``outputs: []`` —
     no faked results;
  7. **every code cell executes**, in order, in a fresh namespace, with
     the working directory set to the course root.

The execution check is the important one: it proves the notebook runs
top-to-bottom with no Airflow, no GCP credentials and no network.

Usage:
    python resources/verify_notebooks.py
    python resources/verify_notebooks.py --notebook 03-templates-and-variables
    python resources/verify_notebooks.py --no-exec
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import textwrap
import traceback
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = ROOT / "notebooks"

ID_RE = re.compile(r"^[0-9a-f]{8}$")

REQUIRED_KERNELSPEC = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}

REQUIRED_LANGUAGE_INFO = {
    "name": "python",
    "version": "3.11.0",
    "mimetype": "text/x-python",
    "codemirror_mode": {"name": "ipython", "version": 3},
    "pygments_lexer": "ipython3",
    "nbconvert_exporter": "python",
    "file_extension": ".py",
}


class Failure(Exception):
    """One verification failure."""


def check_json(path: Path) -> dict[str, Any]:
    """Parse the notebook as JSON.

    Args:
        path: The notebook path.

    Returns:
        The parsed notebook.

    Raises:
        Failure: When the file is not valid JSON.
    """
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Failure(f"not valid JSON: {exc}") from exc


def check_nbformat(path: Path, nb: dict[str, Any]) -> None:
    """Validate the notebook with the ``nbformat`` library.

    Args:
        path: The notebook path.
        nb: The parsed notebook.

    Raises:
        Failure: When nbformat rejects the notebook.
    """
    try:
        import nbformat
    except ImportError:
        print("    (nbformat not installed — structural validation skipped)")
        return

    try:
        parsed = nbformat.read(path, as_version=4)
        nbformat.validate(parsed)
    except Exception as exc:  # noqa: BLE001
        raise Failure(f"nbformat validation failed: {exc}") from exc

    if nb.get("nbformat") != 4:
        raise Failure(f"nbformat must be 4, got {nb.get('nbformat')!r}")
    if nb.get("nbformat_minor") != 5:
        raise Failure(f"nbformat_minor must be 5, got {nb.get('nbformat_minor')!r}")


def check_metadata(nb: dict[str, Any]) -> None:
    """Check the kernelspec and language_info against the course spec.

    Args:
        nb: The parsed notebook.

    Raises:
        Failure: When the metadata does not match.
    """
    metadata = nb.get("metadata", {})
    if metadata.get("kernelspec") != REQUIRED_KERNELSPEC:
        raise Failure(
            f"metadata.kernelspec mismatch: {metadata.get('kernelspec')!r}"
        )
    if metadata.get("language_info") != REQUIRED_LANGUAGE_INFO:
        raise Failure(
            f"metadata.language_info mismatch: {metadata.get('language_info')!r}"
        )


def check_cells(nb: dict[str, Any]) -> None:
    """Check cell ids, source encoding and code-cell shape.

    Args:
        nb: The parsed notebook.

    Raises:
        Failure: When a cell violates the format rules.
    """
    cells = nb.get("cells", [])
    if not cells:
        raise Failure("notebook has no cells")

    seen: set[str] = set()
    for index, cell in enumerate(cells):
        cell_id = cell.get("id")
        if not isinstance(cell_id, str) or not ID_RE.match(cell_id):
            raise Failure(
                f"cell {index}: id must be 8 hex chars, got {cell_id!r}"
            )
        if cell_id in seen:
            raise Failure(f"cell {index}: duplicate id {cell_id!r}")
        seen.add(cell_id)

        source = cell.get("source")
        if not isinstance(source, list):
            raise Failure(f"cell {index}: source must be a list, got {type(source).__name__}")
        for line in source:
            if not isinstance(line, str):
                raise Failure(f"cell {index}: source entries must be strings")
        if source:
            if source[-1].endswith("\n"):
                raise Failure(f"cell {index}: last source line must not end with \\n")
            for line in source[:-1]:
                if not line.endswith("\n"):
                    raise Failure(f"cell {index}: source lines must end with \\n")

        cell_type = cell.get("cell_type")
        if cell_type == "code":
            if cell.get("execution_count") is not None:
                raise Failure(f"cell {index}: execution_count must be null")
            if cell.get("outputs") != []:
                raise Failure(f"cell {index}: outputs must be an empty list")
            for key in ("metadata",):
                if key not in cell:
                    raise Failure(f"cell {index}: missing {key}")
        elif cell_type == "markdown":
            if "outputs" in cell:
                raise Failure(f"cell {index}: markdown cell must not have outputs")
        else:
            raise Failure(f"cell {index}: unknown cell_type {cell_type!r}")


def check_execution(path: Path, nb: dict[str, Any]) -> None:
    """Execute every code cell in order, in a fresh namespace.

    The cells run in a subprocess rooted at the course directory, so the
    path-resolution preamble in each notebook resolves the same way a
    student would see it.

    Args:
        path: The notebook path.
        nb: The parsed notebook.

    Raises:
        Failure: When a cell raises.
    """
    blocks: list[str] = []
    for index, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        # Indent the whole source as a block so that multi-line statements
        # (a string literal spanning lines, a bracketed call) stay intact.
        indented = textwrap.indent(source, "    ")
        blocks.append(
            f"# ---- cell {index} ----\n"
            "try:\n"
            f"{indented}\n"
            "except Exception:\n"
            "    import traceback; traceback.print_exc(); raise\n"
        )

    script = "\n".join(blocks)
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        tail = (result.stderr or result.stdout).strip().splitlines()
        detail = "\n".join(tail[-25:])
        raise Failure(f"execution failed:\n{detail}")


def verify(path: Path, execute: bool = True) -> list[str]:
    """Run every check against one notebook.

    Args:
        path: The notebook path.
        execute: Whether to execute the code cells.

    Returns:
        A list of failure messages — empty when the notebook passes.
    """
    problems: list[str] = []
    try:
        nb = check_json(path)
    except Failure as exc:
        return [str(exc)]

    for label, check in (
        ("nbformat", lambda: check_nbformat(path, nb)),
        ("metadata", lambda: check_metadata(nb)),
        ("cells", lambda: check_cells(nb)),
    ):
        try:
            check()
        except Failure as exc:
            problems.append(f"[{label}] {exc}")

    if execute and not problems:
        try:
            check_execution(path, nb)
        except Failure as exc:
            problems.append(f"[execution] {exc}")

    return problems


def main(argv: list[str] | None = None) -> int:
    """Verify the notebooks.

    Args:
        argv: The command-line arguments.

    Returns:
        0 when every notebook passes, 1 otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--notebook", default=None, help="Verify one notebook by slug")
    parser.add_argument("--no-exec", action="store_true", help="Skip the execution check")
    args = parser.parse_args(argv)

    if args.notebook:
        paths = [NOTEBOOKS / f"{args.notebook}.ipynb"]
    else:
        paths = sorted(NOTEBOOKS.glob("*.ipynb"))

    if not paths:
        print("no notebooks found")
        return 1

    failures = 0
    print("=" * 78)
    print("COMPOSER NOTEBOOK VERIFICATION")
    print("=" * 78)
    for path in paths:
        if not path.exists():
            print(f"  MISSING  {path.name}")
            failures += 1
            continue
        problems = verify(path, execute=not args.no_exec)
        if problems:
            failures += 1
            print(f"  FAIL     {path.name}")
            for problem in problems:
                print(f"             {problem}")
        else:
            print(f"  PASS     {path.name}")

    print("-" * 78)
    total = len(paths)
    print(f"{total - failures}/{total} notebooks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
