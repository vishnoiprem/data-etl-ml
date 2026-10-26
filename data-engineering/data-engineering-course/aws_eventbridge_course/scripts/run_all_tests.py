#!/usr/bin/env python3
"""Run every test_*.py under each section's code/ directory."""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent


def _find_test_files() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for section in sorted(HERE.iterdir()):
        if not section.is_dir() or not section.name[:2].isdigit():
            continue
        code_dir = section / "code"
        if not code_dir.exists():
            continue
        for test in sorted(code_dir.rglob("test_*.py")):
            files.append(test)
    return files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    files = _find_test_files()
    if not files:
        print("No test files found.")
        return 0

    print(f"Discovered {len(files)} test file(s).\n")
    overall_rc = 0
    for f in files:
        rel = f.relative_to(HERE)
        print(f"=== {rel} ===")
        rc = subprocess.call(
            [sys.executable, "-m", "pytest", str(f), "-v" if not args.quiet else "-q"],
            cwd=str(HERE),
        )
        if rc != 0:
            overall_rc = rc

    print()
    if overall_rc == 0:
        print("ALL PASS")
    else:
        print(f"FAIL (exit code {overall_rc})")
    return overall_rc


if __name__ == "__main__":
    sys.exit(main())
