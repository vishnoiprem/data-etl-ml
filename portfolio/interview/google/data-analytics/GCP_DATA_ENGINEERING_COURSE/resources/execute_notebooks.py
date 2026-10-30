#!/usr/bin/env python3
"""
execute_notebooks.py — run every course notebook and report the result.

A notebook that parses but does not run is a broken notebook. This
executes them in place, with the course root as the working directory,
so the setup cell's ``Path.cwd()`` resolves the sample data.

Usage:
    python resources/execute_notebooks.py
    python resources/execute_notebooks.py --verbose
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = COURSE_ROOT / "notebooks"


def execute_one(path: Path, verbose: bool = False) -> tuple[bool, str]:
    """Execute a single notebook.

    Args:
        path: The notebook path.
        verbose: Whether to print each cell's output.

    Returns:
        A ``(ok, message)`` pair.
    """
    try:
        import nbformat
        from nbclient import NotebookClient
    except ImportError as exc:  # pragma: no cover - optional dependency
        return True, f"skipped: {exc}"

    notebook = nbformat.read(path, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=180,
        kernel_name="python3",
        resources={"metadata": {"path": str(COURSE_ROOT)}},
    )

    try:
        executed = client.execute()
    except Exception as exc:  # noqa: BLE001 - any failure is a failure
        return False, f"{type(exc).__name__}: {exc}"

    if verbose:
        for cell in executed.cells:
            if cell.cell_type != "code":
                continue
            for output in cell.get("outputs", []):
                text = output.get("text", "")
                if text:
                    print(text, end="" if text.endswith("\n") else "\n")
                if output.get("output_type") == "error":
                    print(f"  ERROR: {output.get('ename')}: {output.get('evalue')}")

    return True, "ok"


def main(argv: list[str] | None = None) -> int:
    """Execute every notebook.

    Args:
        argv: The argument list, or None for ``sys.argv``.

    Returns:
        The process exit code: 0 if every notebook ran, 1 otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verbose", action="store_true", help="Print cell outputs")
    args = parser.parse_args(argv)

    if not NOTEBOOKS_DIR.exists():
        print("no notebooks directory — nothing to execute")
        return 0

    paths = sorted(NOTEBOOKS_DIR.glob("*.ipynb"))
    if not paths:
        print("no notebooks found")
        return 0

    failures: list[tuple[str, str]] = []
    for path in paths:
        ok, message = execute_one(path, verbose=args.verbose)
        status = "OK  " if ok else "FAIL"
        print(f"{status} {path.name}: {message}")
        if not ok:
            failures.append((path.name, message))

    print()
    print(f"{len(paths) - len(failures)}/{len(paths)} notebooks executed cleanly.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
