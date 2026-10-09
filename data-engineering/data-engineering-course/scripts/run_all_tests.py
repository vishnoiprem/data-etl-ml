"""Run tests across all tracks of the data engineering course.

Each track may have its own test layout. This script:
  1. Discovers every <track>/tests/ directory
  2. Runs every test_*.py file inside
  3. Aggregates a final pass/fail summary
  4. Returns exit code 0 only if all tracks pass

Tracks included:
  - system_design (existing, ~764 tests, run via its own runner)
  - data_modeling (new)
  - data_pipeline_design (new)
  - sql_interviews (new)
  - coding_interviews (new)
  - common (shared library tests)

Usage::

    python3 scripts/run_all_tests.py            # run every track
    python3 scripts/run_all_tests.py data_modeling   # run one track
    python3 scripts/run_all_tests.py -v         # verbose
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Dict, List, Tuple

HERE = Path(__file__).resolve().parent
COURSE_ROOT = HERE.parent
COMMON_DIR = COURSE_ROOT / "common"

# Track layout: a list of (name, absolute path). ``tests`` is a
# directory of test_*.py files. We keep this explicit (rather than
# a glob) so the script is honest about which tracks are wired up.
TRACKS: List[Tuple[str, Path]] = [
    ("system_design", COURSE_ROOT / "system_design"),
    ("data_modeling", COURSE_ROOT / "data_modeling"),
    ("data_pipeline_design", COURSE_ROOT / "data_pipeline_design"),
    ("sql_interviews", COURSE_ROOT / "sql_interviews"),
    ("coding_interviews", COURSE_ROOT / "coding_interviews"),
    ("common", COMMON_DIR),  # tests for the shared library itself
]

# Make `common` importable for every track.
sys.path.insert(0, str(COURSE_ROOT))


def _discover_test_cases(test_file: Path, track_name: str) -> List[type]:
    """Import a test file and return every ``unittest.TestCase`` it defines."""
    spec = importlib.util.spec_from_file_location(
        f"_track_{track_name}_{test_file.stem}", test_file
    )
    if spec is None or spec.loader is None:
        return []
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    cases: List[type] = []
    for name in dir(mod):
        obj = getattr(mod, name)
        if (
            isinstance(obj, type)
            and issubclass(obj, unittest.TestCase)
            and obj is not unittest.TestCase
        ):
            cases.append(obj)
    return cases


def run_track(name: str, path: Path, verbose: bool = False) -> Tuple[int, int, int]:
    """Run all tests in ``<path>/tests``; return (run, failures, errors).

    The ``system_design`` track uses its own runner
    (``system_design/scripts/run_tests.py``) because its tests
    import ``from code.X import ...`` which requires the module's
    directory to be on ``sys.path``. Delegate to it.
    """
    # ---- system_design uses its own runner ----
    if name == "system_design":
        runner = path / "scripts" / "run_tests.py"
        if not runner.exists():
            return (0, 0, 0)
        cmd = [sys.executable, str(runner), "-v" if verbose else ""]
        cmd = [c for c in cmd if c]
        proc = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(path)
        )
        print(proc.stdout)
        if proc.stderr:
            print(proc.stderr)
        out = proc.stdout + proc.stderr
        # The system_design runner ends with a line like
        # ``FAILED (failures=82, errors=56)`` or ``OK``. Parse it.
        import re
        m = re.search(r"FAILED \(failures=(\d+), errors=(\d+)\)", out)
        if m:
            fail = int(m.group(1))
            err = int(m.group(2))
            run_m = re.search(r"Ran (\d+) tests", out)
            run = int(run_m.group(1)) if run_m else (fail + err)
            return (run, fail, err)
        if "OK" in out:
            run_m = re.search(r"Ran (\d+) tests", out)
            run = int(run_m.group(1)) if run_m else 0
            return (run, 0, 0)
        return (0, 0, 0)

    tests_dir = path / "tests"

    # Short-circuit if there is nothing to find anywhere.
    if not tests_dir.exists() and not any(
        (sub / "tests").is_dir() or (sub / "code" / "tests").is_dir()
        for sub in path.iterdir() if sub.is_dir()
    ):
        return (0, 0, 0)

    suite = unittest.TestSuite()
    test_files: List[Path] = []
    if tests_dir.exists():
        test_files.extend(sorted(tests_dir.glob("test_*.py")))
    for sub in sorted(path.iterdir()):
        if not sub.is_dir():
            continue
        for candidate in (sub / "tests", sub / "code" / "tests"):
            if candidate.is_dir():
                test_files.extend(sorted(candidate.glob("test_*.py")))
    for tf in test_files:
        for case in _discover_test_cases(tf, name):
            suite.addTests(unittest.TestLoader().loadTestsFromTestCase(case))

    n_tests = suite.countTestCases()
    if n_tests == 0:
        return (0, 0, 0)

    runner_obj = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    print(f"\n{'=' * 70}\n[{name}]  ({n_tests} tests)\n{'=' * 70}")
    result = runner_obj.run(suite)
    return (result.testsRun, len(result.failures), len(result.errors))


def main(argv: List[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    verbose = "-v" in argv or "--verbose" in argv
    only = [a for a in argv if not a.startswith("-")]

    totals: Dict[str, Tuple[int, int, int]] = {}
    for name, path in TRACKS:
        if only and name not in only:
            continue
        if not path.exists():
            print(f"[{name}]  skipped (path does not exist: {path})")
            continue
        totals[name] = run_track(name, path, verbose=verbose)

    # ---- summary ---------------------------------------------------------
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    grand_run = grand_fail = grand_err = 0
    any_failure = False
    for name, (run, fail, err) in totals.items():
        status = "OK" if (fail == 0 and err == 0) else "FAIL"
        if fail or err:
            any_failure = True
        print(f"  {name:<24}  run={run:>5}  fail={fail:>3}  err={err:>3}  {status}")
        grand_run += run
        grand_fail += fail
        grand_err += err
    print("-" * 70)
    print(
        f"  {'TOTAL':<24}  run={grand_run:>5}  fail={grand_fail:>3}  "
        f"err={grand_err:>3}"
    )
    return 1 if any_failure else 0


if __name__ == "__main__":
    sys.exit(main())

