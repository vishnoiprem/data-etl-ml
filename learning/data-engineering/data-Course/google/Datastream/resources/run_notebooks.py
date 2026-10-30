#!/usr/bin/env python3
"""
run_notebooks.py — execute every course notebook, headless.

The notebooks are the course's worked examples, so they must actually run.
This script executes each one in a fresh kernel with the course root as the
working directory, and reports the result.

Usage:
    python resources/run_notebooks.py
    python resources/run_notebooks.py --notebook 03-the-merge-and-bigquery.ipynb
    python resources/run_notebooks.py --timeout 900

Requires: ``jupyter``, ``nbclient`` and ``nbformat``.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = ROOT / "notebooks"


def execute(path: Path, timeout: int) -> tuple[bool, str]:
    """Execute one notebook and return whether it passed.

    Args:
        path: The notebook to execute.
        timeout: The per-notebook timeout, in seconds.

    Returns:
        A `(passed, message)` pair. The message is empty on success.
    """
    try:
        import nbformat
        from nbclient import NotebookClient
    except ImportError as exc:
        return False, (
            f"{exc} — install with: pip install jupyter nbclient nbformat"
        )

    try:
        notebook = nbformat.read(path, as_version=4)
    except Exception as exc:  # noqa: BLE001
        return False, f"could not read the notebook: {exc}"

    try:
        client = NotebookClient(
            notebook,
            timeout=timeout,
            kernel_name="python3",
            resources={"metadata": {"path": str(ROOT)}},
        )
        client.execute()
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {str(exc)[:2000]}"

    return True, ""


def main(argv: list[str] | None = None) -> int:
    """Execute the selected notebooks and report the result.

    Args:
        argv: The argument list, or None to read from `sys.argv`.

    Returns:
        0 when every notebook passes, 1 otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--notebook",
        action="append",
        default=None,
        help="Execute only this notebook (repeatable)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Per-notebook timeout in seconds (default: 600)",
    )
    args = parser.parse_args(argv)

    if args.notebook:
        paths = [NOTEBOOKS / name for name in args.notebook]
        missing = [p.name for p in paths if not p.exists()]
        if missing:
            print(f"no such notebook: {', '.join(missing)}")
            return 1
    else:
        paths = sorted(NOTEBOOKS.glob("*.ipynb"))

    if not paths:
        print(f"no notebooks found in {NOTEBOOKS}")
        return 1

    failures = 0
    for path in paths:
        passed, message = execute(path, args.timeout)
        if passed:
            print(f"  PASS  {path.name}")
        else:
            failures += 1
            print(f"  FAIL  {path.name}")
            print(f"        {message}")

    total = len(paths)
    print()
    print(f"{total - failures}/{total} notebooks executed successfully")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
