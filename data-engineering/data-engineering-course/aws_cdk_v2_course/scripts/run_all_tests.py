"""Run ``npm test`` in every populated TypeScript CDK project.

The AWS CDK v2 Crash Course uses Jest (TypeScript) for testing rather
than pytest, because CDK itself is JavaScript/TypeScript and the
`aws-cdk-lib/assertions` module is a TypeScript library.

This script mirrors the convention used in the other courses in this
repo (see ``../aws_lambda_course/scripts/run_all_tests.py``): walk
every section folder, look for any ``package.json`` underneath
``code/``, run ``npm test`` in each, and aggregate a pass/fail summary.

Tracks included (relative to the course root):

  - 02_app_stack_construct/code/hello-cdk/
  - 03_building_with_cdk/code/lambda-api/
  - 04_appsync_stepfunctions/code/app-sync-sfn/
  - 05_testing_cicd/code/ (if populated)

Usage::

    python3 scripts/run_all_tests.py             # run every project
    python3 scripts/run_all_tests.py hello-cdk   # restrict by name
    python3 scripts/run_all_tests.py -v          # verbose npm output
    python3 scripts/run_all_tests.py --skip-install   # skip npm install

The script returns exit code 0 if every project either passes its tests
or is skipped (no ``package.json`` or ``npm`` not available).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE_ROOT = HERE.parent

# Every section we know about. The keys are short labels used in status
# output; the values are absolute paths to the section's ``code/``
# directory. Sections without a populated ``code/`` are silently
# skipped.
SECTIONS: dict[str, Path] = {
    "02_app_stack_construct": COURSE_ROOT / "02_app_stack_construct" / "code",
    "03_building_with_cdk": COURSE_ROOT / "03_building_with_cdk" / "code",
    "04_appsync_stepfunctions": COURSE_ROOT / "04_appsync_stepfunctions" / "code",
    "05_testing_cicd": COURSE_ROOT / "05_testing_cicd" / "code",
    "06_real_world": COURSE_ROOT / "06_real_world" / "code",
}


@dataclass
class ProjectResult:
    """Outcome of running ``npm test`` against a single CDK project."""

    section: str
    name: str
    path: Path
    returncode: int
    skipped: bool = False
    skip_reason: str = ""
    stdout: str = ""
    stderr: str = ""

    @property
    def status(self) -> str:
        if self.skipped:
            return "SKIP"
        if self.returncode == 0:
            return "OK"
        return "FAIL"


def discover_projects(code_dir: Path) -> list[Path]:
    """Return every directory under ``code_dir`` containing a ``package.json``."""
    if not code_dir.exists():
        return []
    return sorted(p.parent for p in code_dir.rglob("package.json") if p.is_file())


def have_npm() -> bool:
    """Return True if ``npm`` is on the PATH."""
    return shutil.which("npm") is not None


def run_npm_test(
    section: str,
    project_dir: Path,
    *,
    verbose: bool,
    install: bool,
) -> ProjectResult:
    """Run ``npm test`` in ``project_dir`` and capture output."""
    name = project_dir.name

    if not have_npm():
        return ProjectResult(
            section=section,
            name=name,
            path=project_dir,
            returncode=0,
            skipped=True,
            skip_reason="npm not on PATH",
        )

    if install:
        install_cmd = ["npm", "install", "--no-audit", "--no-fund", "--silent"]
        print(f"\n[install] {name}: {' '.join(install_cmd)}")
        install_proc = subprocess.run(install_cmd, cwd=project_dir, capture_output=True, text=True)
        if install_proc.returncode != 0:
            return ProjectResult(
                section=section,
                name=name,
                path=project_dir,
                returncode=install_proc.returncode,
                stdout=install_proc.stdout,
                stderr=install_proc.stderr + "\n(npm install failed; skipping npm test)",
            )

    cmd = ["npm", "test", "--silent"]
    if verbose:
        cmd = ["npm", "test", "--", "--verbose"]
    print(f"\n{'=' * 72}\n[{section}/{name}]  {' '.join(cmd)}\n{'=' * 72}")
    proc = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)

    if proc.stdout:
        print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)

    return ProjectResult(
        section=section,
        name=name,
        path=project_dir,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run npm test in every populated TypeScript CDK project of the "
            "AWS CDK v2 course and print a pass/fail summary."
        ),
    )
    parser.add_argument(
        "filter",
        nargs="*",
        help="Restrict to projects whose name contains one of these substrings.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Pass --verbose to jest for verbose output.",
    )
    parser.add_argument(
        "--skip-install",
        dest="install",
        action="store_false",
        help="Skip the ``npm install`` step before running tests.",
    )
    parser.add_argument(
        "--install",
        dest="install",
        action="store_true",
        default=True,
        help="Run ``npm install`` before each test (default).",
    )
    args = parser.parse_args(argv)

    results: list[ProjectResult] = []
    for section, code_dir in SECTIONS.items():
        for project_dir in discover_projects(code_dir):
            if args.filter and not any(f in project_dir.name for f in args.filter):
                continue
            results.append(
                run_npm_test(
                    section,
                    project_dir,
                    verbose=args.verbose,
                    install=args.install,
                )
            )

    # ---- summary --------------------------------------------------------
    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    any_fail = False
    for r in results:
        marker = ""
        if r.status == "SKIP":
            marker = f"  ({r.skip_reason})"
        print(
            f"  {r.section}/{r.name:<25}  status={r.status:<4}  rc={r.returncode}{marker}"
        )
        if r.status == "FAIL":
            any_fail = True
    print("-" * 72)
    print(
        f"  TOTAL projects: {len(results):>3}    failures: "
        f"{sum(1 for r in results if r.status == 'FAIL'):>3}    "
        f"skipped: {sum(1 for r in results if r.status == 'SKIP'):>3}"
    )

    if not have_npm():
        print(
            "\nNote: ``npm`` was not found on the PATH. To run these tests "
            "locally, install Node 20+ and re-run this script."
        )

    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
