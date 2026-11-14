"""Verify every "Expected output" in the Beam suite against a real execution.

Every ``💻 Runs locally`` code block in the modules and labs is paired with a
verbatim ``Expected output:`` block.  Those blocks are pasted from real runs;
this script is what keeps them honest.

Unlike ``practice/_verify_modules.py``, this verifier runs the blocks with an
interpreter that actually has **apache_beam** installed.  It resolves one the
same way ``beam_workbench.py`` does.

Run from ``practice/beam/``::

    python beam_workbench.py verify
    python beam_workbench.py verify --repeats 3     # require identical output

or directly, with an explicit interpreter::

    <python-with-beam> _verify_beam_labs.py
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent

# A python block followed by its expected output.
BLOCK = re.compile(
    r"```python\n(.*?)```\n\nExpected output:\n\n```text\n(.*?)```",
    re.S,
)

# Only these files are scanned; the assignments are graded exercises and are
# checked by their own solution scripts.
SCAN_GLOBS = ["*.md", "labs/*.md", "assignments/*.md"]


def candidate_interpreters() -> list[str]:
    """Interpreters that might have apache_beam, most specific first."""
    course = HERE.parent.parent
    repo = course.parent.parent.parent
    return [
        os.environ.get("BEAM_PYTHON"),
        str(repo / ".env" / "bin" / "python"),
        str(course / "practice" / ".beam-venv" / "bin" / "python"),
        str(HERE / ".beam-venv" / "bin" / "python"),
    ]


def find_interpreter() -> str | None:
    for candidate in candidate_interpreters():
        if not candidate:
            continue
        path = pathlib.Path(candidate)
        if not path.exists():
            continue
        probe = subprocess.run(
            [str(path), "-c", "import apache_beam"],
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0:
            return str(path)
    return None


def scan_files() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for pattern in SCAN_GLOBS:
        files.extend(sorted(HERE.glob(pattern)))
    # The top-level README and the workbench reference are not module prose.
    return [f for f in files if f.name not in {"README.md"}]


def run_block(interpreter: str, code: str, cwd: pathlib.Path) -> subprocess.CompletedProcess:
    """Execute one code block and return the completed process."""
    script = cwd / "_beam_block.py"
    script.write_text(code)
    try:
        return subprocess.run(
            [interpreter, str(script)],
            capture_output=True,
            text=True,
            cwd=str(cwd),
        )
    finally:
        script.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repeats",
        type=int,
        default=0,
        help="re-run each block N times and require identical output",
    )
    args = parser.parse_args()

    interpreter = find_interpreter()
    if not interpreter:
        print("No Python interpreter with apache_beam was found.", file=sys.stderr)
        print("Tried:", file=sys.stderr)
        for candidate in candidate_interpreters():
            if candidate:
                print(f"  {candidate}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Install Beam:", file=sys.stderr)
        course = HERE.parent.parent
        repo = course.parent.parent.parent
        print(
            f"  {repo / '.env' / 'bin' / 'python'} -m pip install apache-beam",
            file=sys.stderr,
        )
        return 2

    print(f"interpreter: {interpreter}")
    print()

    mismatches = 0
    checked = 0
    unstable = 0

    # Labs write their output under the beam/ directory, so run them there.
    workdir = HERE

    for path in scan_files():
        text = path.read_text(encoding="utf-8")
        for index, match in enumerate(BLOCK.finditer(text), start=1):
            code, expected = match.group(1), match.group(2)
            checked += 1

            result = run_block(interpreter, code, workdir)
            actual = result.stdout.rstrip("\n")
            want = expected.rstrip("\n")

            if result.returncode != 0:
                mismatches += 1
                print(f"ERROR {path.name} block {index}")
                print(result.stderr.strip()[-1500:])
                continue

            if actual != want:
                mismatches += 1
                print(f"MISMATCH {path.name} block {index}")
                print("--- expected ---")
                print(want)
                print("--- actual ---")
                print(actual)
                if result.stderr:
                    print("--- stderr ---")
                    print(result.stderr.strip()[-800:])
                continue

            if args.repeats > 1:
                first = actual
                for _ in range(args.repeats - 1):
                    again = run_block(interpreter, code, workdir)
                    if again.stdout.rstrip("\n") != first:
                        unstable += 1
                        print(f"UNSTABLE {path.name} block {index}")
                        print(f"  run 1: {first[:200]!r}")
                        print(f"  run N: {again.stdout.rstrip(chr(10))[:200]!r}")
                        break

    print()
    print(
        f"blocks checked: {checked}   mismatches: {mismatches}   unstable: {unstable}"
    )
    return 1 if (mismatches or unstable) else 0


if __name__ == "__main__":
    sys.exit(main())
