"""Run every section's test_*.py files in sequence with pytest.

This script is the AWS Cognito Authorizers course's entry point for
running all in-section tests. It mirrors the convention used in
``../aws_lambda_course/scripts/run_all_tests.py``: walk every section
folder, look for any ``test_*.py`` underneath ``code/``, run pytest on
each, and aggregate a pass/fail summary.

Tracks included (relative to the course root):

  - 02_user_pools/code/      (idempotent create_user_pool.py + 6 moto tests)
  - 03_identity_pools/code/  (idempotent identity_pool_demo.py + 4 moto tests)

Usage::

    python3 scripts/run_all_tests.py             # run every section
    python3 scripts/run_all_tests.py 02_user_pools
    python3 scripts/run_all_tests.py -v          # verbose pytest output
    python3 scripts/run_all_tests.py -k dry_run  # pass through to pytest -k

The script returns exit code 0 only if every section's tests pass.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE_ROOT = HERE.parent

# Every section we run tests for. The keys are the short names used in
# status output; the values are the absolute paths to the section's
# ``code/`` directory. Sections without a populated ``code/`` are
# silently skipped.
SECTIONS: dict[str, Path] = {
    "02_user_pools": COURSE_ROOT / "02_user_pools" / "code",
    "03_identity_pools": COURSE_ROOT / "03_identity_pools" / "code",
}


@dataclass
class SectionResult:
    """Outcome of running pytest on a single section."""

    name: str
    path: Path
    returncode: int
    test_files: list[Path] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""

    @property
    def status(self) -> str:
        if not self.test_files:
            return "SKIP"
        if self.returncode == 0:
            return "OK"
        if self.returncode == 5:
            # pytest returns 5 when no tests were collected
            return "SKIP"
        return "FAIL"


def discover_test_files(code_dir: Path) -> list[Path]:
    """Return every ``test_*.py`` file under ``code_dir``, recursively."""
    if not code_dir.exists():
        return []
    return sorted(p for p in code_dir.rglob("test_*.py") if p.is_file())


def run_pytest(
    section: str,
    code_dir: Path,
    *,
    verbose: bool,
    extra_args: list[str],
) -> SectionResult:
    """Run pytest against the section's test files; return a SectionResult."""
    test_files = discover_test_files(code_dir)
    if not test_files:
        return SectionResult(name=section, path=code_dir, returncode=0, test_files=[])

    cmd: list[str] = [sys.executable, "-m", "pytest"]
    if verbose:
        cmd.append("-v")
    cmd.extend(extra_args)

    print(f"\n{'=' * 72}\n[{section}]  ({len(test_files)} test files)\n{'=' * 72}")

    worst_rc = 0
    combined_stdout: list[str] = []
    combined_stderr: list[str] = []
    for tf in test_files:
        single_cmd = cmd + [str(tf)]
        print("+", " ".join(single_cmd))
        proc = subprocess.run(single_cmd, capture_output=True, text=True)
        if proc.stdout:
            print(proc.stdout)
            combined_stdout.append(proc.stdout)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
            combined_stderr.append(proc.stderr)
        if proc.returncode > worst_rc:
            worst_rc = proc.returncode

    return SectionResult(
        name=section,
        path=code_dir,
        returncode=worst_rc,
        test_files=test_files,
        stdout="\n".join(combined_stdout),
        stderr="\n".join(combined_stderr),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run every test_*.py file in every populated section of the "
            "AWS Cognito Authorizers course and print a pass/fail summary."
        ),
    )
    parser.add_argument(
        "section",
        nargs="*",
        help="Restrict to one or more section short names (see SECTIONS).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Pass -v to pytest for verbose output.",
    )
    args, passthrough = parser.parse_known_args(argv)

    selected = dict(SECTIONS)
    if args.section:
        unknown = [s for s in args.section if s not in SECTIONS]
        if unknown:
            print(
                f"Unknown section(s): {', '.join(unknown)}. Known: {', '.join(SECTIONS)}",
                file=sys.stderr,
            )
            return 2
        selected = {k: v for k, v in SECTIONS.items() if k in args.section}

    results: list[SectionResult] = []
    for name, path in selected.items():
        results.append(run_pytest(name, path, verbose=args.verbose, extra_args=passthrough))

    # ---- summary --------------------------------------------------------
    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    any_fail = False
    for r in results:
        print(
            f"  {r.name:<40}  status={r.status:<4}  tests={len(r.test_files):>3}  "
            f"rc={r.returncode}"
        )
        if r.status == "FAIL":
            any_fail = True
    print("-" * 72)
    print("  TOTAL sections: {:>3}    failures: {:>3}".format(
        len(results), sum(1 for r in results if r.status == "FAIL")
    ))
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
