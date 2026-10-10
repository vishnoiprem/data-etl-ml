"""Run every section's test_*.py files in sequence with pytest.

This script is the AWS Lambda course's entry point for running all
in-section tests. It mirrors the convention used in
``../aws_glue_course/scripts/run_all_tests.py``: walk every section
folder, look for any ``test_*.py`` underneath ``code/``, run pytest on
each, and aggregate a pass/fail summary.

Tracks included (relative to the course root):

  - 04_lambda_with_aws_resources/code/         (boto3 mini-project)
  - 06_usecase1_s3_lambda_dynamodb/code/       (use case 1)
  - 08_usecase2_apigw_lambda_s3/code/          (use case 2)
  - 09_api_security_lambda_cognito_auth/code/  (lambda / cognito authorizers)
  - 10_generative_ai_bedrock/code/             (bedrock lambdas)
  - 11_lambda_advanced_concepts/code/          (VPC, env vars, versions, aliases)
  - 12_cdk_v2_serverless/code/                 (CDK v2 synth snapshots)
  - 13_cloudformation_serverless/code/         (CFN template linting)

Usage::

    python3 scripts/run_all_tests.py             # run every section
    python3 scripts/run_all_tests.py 04_lambda_with_aws_resources
    python3 scripts/run_all_tests.py -v          # verbose pytest output
    python3 scripts/run_all_tests.py -k use_case_1   # pass through to pytest -k

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
    "04_lambda_with_aws_resources": COURSE_ROOT / "04_lambda_with_aws_resources" / "code",
    "06_usecase1_s3_lambda_dynamodb": COURSE_ROOT / "06_usecase1_s3_lambda_dynamodb" / "code",
    "08_usecase2_apigw_lambda_s3": COURSE_ROOT / "08_usecase2_apigw_lambda_s3" / "code",
    "09_api_security_lambda_cognito_auth": COURSE_ROOT
    / "09_api_security_lambda_cognito_auth"
    / "code",
    "10_generative_ai_bedrock": COURSE_ROOT / "10_generative_ai_bedrock" / "code",
    "11_lambda_advanced_concepts": COURSE_ROOT / "11_lambda_advanced_concepts" / "code",
    "12_cdk_v2_serverless": COURSE_ROOT / "12_cdk_v2_serverless" / "code",
    "13_cloudformation_serverless": COURSE_ROOT
    / "13_cloudformation_serverless"
    / "code",
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
    cmd.extend(str(p) for p in test_files)

    print(f"\n{'=' * 72}\n[{section}]  ({len(test_files)} test files)\n{'=' * 72}")
    print("+", " ".join(cmd))

    proc = subprocess.run(cmd, capture_output=True, text=True)
    # Echo pytest's output so the user can see what happened even when
    # we're aggregating across many sections.
    if proc.stdout:
        print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)

    return SectionResult(
        name=section,
        path=code_dir,
        returncode=proc.returncode,
        test_files=test_files,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run every test_*.py file in every populated section of the "
            "AWS Lambda course and print a pass/fail summary."
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
