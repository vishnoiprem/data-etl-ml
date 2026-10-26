#!/usr/bin/env python3
"""Run every test_*.py under the course, plus a `dbt parse` smoke test.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
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
    # Also pick up tests under dbt_project/tests/ (Python tests, not dbt tests)
    root_code = HERE / "code"
    if root_code.exists():
        for test in sorted(root_code.rglob("test_*.py")):
            files.append(test)
    return files


def _run_dbt_parse() -> int:
    print("\n=== dbt parse smoke test ===")
    # Try the global dbt first; fall back to the venv-relative dbt.
    dbt_bin = shutil.which("dbt") or str(HERE / ".venv" / "bin" / "dbt")
    if not pathlib.Path(dbt_bin).exists():
        print(f"SKIP: dbt not installed at {dbt_bin} (run scripts/bootstrap.sh first)")
        return 0
    rc = subprocess.call(
        [
            dbt_bin,
            "parse",
            "--project-dir", "dbt_project",
            "--profiles-dir", "dbt_project",
            "--no-version-check",
            "--target", "mock",
        ],
        cwd=str(HERE),
    )
    return rc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    files = _find_test_files()

    print(f"Discovered {len(files)} pytest file(s).\n")
    overall_rc = 0
    for f in files:
        rel = f.relative_to(HERE)
        print(f"=== {rel} ===")
        rc = subprocess.call(
            [
                sys.executable, "-m", "pytest", str(f),
                "-v" if not args.quiet else "-q",
            ],
            cwd=str(HERE),
        )
        if rc != 0:
            overall_rc = rc

    rc_dbt = _run_dbt_parse()
    if rc_dbt != 0:
        overall_rc = rc_dbt

    print()
    if overall_rc == 0:
        print("ALL PASS")
    else:
        print(f"FAIL (exit code {overall_rc})")
    return overall_rc


if __name__ == "__main__":
    sys.exit(main())
