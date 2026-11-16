"""Environment check for the Data Engineering on GCP course.

Verifies every assumption made in
"03 Setup Local Environment using VS Code.md":
Python version, virtualenv, dependencies, gcloud install/auth/project,
repository layout, and sample data.

Run from the course root:

    python tools/check_environment.py

Exits 0 when every check passes, 1 otherwise. Each check reports its own
failure reason so the output tells you what to fix, not just that
something is wrong.
"""

import os
import shutil
import subprocess
import sys

failures = []


def check(name, fn):
    """Run a check, print its result, and record any failure."""
    try:
        result = fn()
    except Exception as exc:  # noqa: BLE001 - a failed check must not stop the rest
        print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
        failures.append(f"{name}: {type(exc).__name__}: {exc}")
        return

    if result is True:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}: {result}")
        failures.append(f"{name}: {result}")


def python_version():
    v = sys.version_info
    if v < (3, 9):
        return f"Python {v.major}.{v.minor} is too old; need 3.9 or newer"
    return True


def in_venv():
    if hasattr(sys, "real_prefix") or sys.base_prefix != sys.prefix:
        return True
    return "not in a virtualenv - activate .venv first"


def deps_installed():
    missing = []
    for mod in ("pandas", "google.cloud.bigquery", "google.cloud.secretmanager"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    return True if not missing else f"missing modules: {', '.join(missing)}"


def gcloud_present():
    path = shutil.which("gcloud")
    return True if path else "gcloud is not on PATH in this terminal"


def _gcloud(args):
    return subprocess.run(
        ["gcloud", *args], capture_output=True, text=True, check=False
    )


def gcloud_authed():
    if not shutil.which("gcloud"):
        return "gcloud is not installed"
    proc = _gcloud(["auth", "list", "--filter=status:ACTIVE", "--format=value(account)"])
    if proc.returncode != 0:
        return f"gcloud auth list failed: {proc.stderr.strip()}"
    if not proc.stdout.strip():
        return "no active gcloud account - run `gcloud init`"
    return True


def project_set():
    if not shutil.which("gcloud"):
        return "gcloud is not installed"
    proc = _gcloud(["config", "get-value", "project"])
    value = proc.stdout.strip()
    if proc.returncode != 0 or not value or value == "(unset)":
        return "no default project - run `gcloud config set project YOUR_PROJECT_ID`"
    return True


def repo_layout():
    """Resolve the course root from the script location, not the cwd."""
    course_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    expected = ["apps", "data", "notebooks", "scripts"]
    missing = [
        d for d in expected if not os.path.isdir(os.path.join(course_dir, d))
    ]
    return True if not missing else f"missing folders: {', '.join(missing)}"


def sample_data_present():
    """Sample data lives in the refactored course directory, one level up."""
    here = os.path.dirname(os.path.abspath(__file__))
    course_dir = os.path.dirname(here)
    candidates = [
        os.path.join(course_dir, "sample_data"),
        os.path.join(os.path.dirname(course_dir), "sample_data"),
    ]
    if any(os.path.isdir(path) for path in candidates):
        return True
    return (
        "sample_data/ not generated - run "
        "`python resources/sample_data.py --output-dir ./sample_data` from the course root"
    )


def main():
    print("Environment check\n")
    check("Python >= 3.9", python_version)
    check("Virtualenv active", in_venv)
    check("Dependencies installed", deps_installed)
    check("gcloud on PATH", gcloud_present)
    check("gcloud authenticated", gcloud_authed)
    check("Default project set", project_set)
    check("Repository layout", repo_layout)
    check("Sample data generated", sample_data_present)

    print()
    if failures:
        print(f"{len(failures)} check(s) failed:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("All checks passed. You are ready for chapter 2.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
