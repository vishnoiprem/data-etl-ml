"""The Beam workbench — run, list and verify the labs in this suite.

    python beam_workbench.py env                 # what the workbench can see
    python beam_workbench.py list                # the labs, with descriptions
    python beam_workbench.py run labs/01-beam-basics.py
    python beam_workbench.py verify              # check every Expected output
    python beam_workbench.py clean               # remove lab output files

The workbench resolves its Python interpreter by searching, in order:

  1. the ``BEAM_PYTHON`` environment variable,
  2. the shared course virtualenv at ``<repo>/.env/bin/python``,
  3. a project-local ``practice/.beam-venv/bin/python``.

Whichever is found must have ``apache_beam`` importable.  This is checked up
front so a missing dependency produces a clear message rather than a
``ModuleNotFoundError`` halfway through a lab.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
COURSE = HERE.parent.parent
REPO = COURSE.parent.parent.parent

# Candidate interpreters, most specific first.
CANDIDATES = [
    os.environ.get("BEAM_PYTHON"),
    str(REPO / ".env" / "bin" / "python"),
    str(COURSE / "practice" / ".beam-venv" / "bin" / "python"),
    str(HERE / ".beam-venv" / "bin" / "python"),
]

# The labs, and the one-line idea each one teaches.
LABS = {
    "labs/01-beam-basics.py": "Build your first pipeline: Create -> Map -> Write",
    "labs/02-extract.py": "Extract: reading a source into a PCollection",
    "labs/03-transform.py": "Transform: Map, FlatMap, Filter, GroupByKey, CombinePerKey",
    "labs/04-load.py": "Load: writing results, and the BigQuery row shape",
    "labs/05-pipeline-creation.py": "Pipeline creation: template method vs custom code",
    "labs/06-case-study-batch.py": "Case study 1 (batch): the full ETL pipeline",
    "labs/07-case-study-streaming.py": "Case study 2 (streaming): windowed aggregation",
}


def find_interpreter() -> str | None:
    """Return the first candidate interpreter that has apache_beam."""
    for candidate in CANDIDATES:
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


def require_interpreter() -> str:
    """Return the Beam interpreter, or exit with an actionable message."""
    interpreter = find_interpreter()
    if interpreter:
        return interpreter

    print("No Python interpreter with apache_beam was found.", file=sys.stderr)
    print("", file=sys.stderr)
    print("Tried:", file=sys.stderr)
    for candidate in CANDIDATES:
        if candidate:
            print(f"  {candidate}", file=sys.stderr)
    print("", file=sys.stderr)
    print("Install Beam into the shared course environment:", file=sys.stderr)
    print(f"  {REPO / '.env' / 'bin' / 'python'} -m pip install apache-beam", file=sys.stderr)
    print("", file=sys.stderr)
    print("Or create a project-local environment:", file=sys.stderr)
    print(f"  python3 -m venv {COURSE / 'practice' / '.beam-venv'}", file=sys.stderr)
    print(
        f"  {COURSE / 'practice' / '.beam-venv' / 'bin' / 'python'} -m pip install apache-beam",
        file=sys.stderr,
    )
    print("", file=sys.stderr)
    print("Or point the workbench at any other interpreter:", file=sys.stderr)
    print("  export BEAM_PYTHON=/path/to/python", file=sys.stderr)
    sys.exit(2)


def cmd_env(_args: argparse.Namespace) -> int:
    """Report what the workbench can see."""
    print("Beam workbench")
    print("==============")
    print(f"course root : {COURSE}")
    print(f"suites      : {HERE}")

    interpreter = find_interpreter()
    if interpreter:
        version = subprocess.run(
            [interpreter, "-c", "import apache_beam; print(apache_beam.__version__)"],
            capture_output=True,
            text=True,
        )
        print(f"interpreter : {interpreter}")
        print(f"beam        : {version.stdout.strip()}")
    else:
        print("interpreter : NONE FOUND (run `beam_workbench.py env` after installing Beam)")

    sample = COURSE / "sample_data" / "events.csv"
    if sample.exists():
        rows = len(
            [
                line
                for line in sample.read_text().splitlines()
                if line.strip() and not line.lower().startswith("event_id,")
            ]
        )
        print(f"sample data : {rows} events")
    else:
        print("sample data : MISSING — run `python resources/sample_data.py --output-dir ./sample_data`")

    print()
    print("labs:")
    for name, description in LABS.items():
        marker = "ok " if (HERE / name).exists() else "MISSING"
        print(f"  [{marker}] {name} — {description}")
    return 0


def cmd_list(_args: argparse.Namespace) -> int:
    """List the labs."""
    print("Labs")
    print("----")
    for name, description in LABS.items():
        print(f"  {name}")
        print(f"      {description}")
    print()
    print(f"  {len(LABS)} labs")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Run one lab with the Beam interpreter."""
    interpreter = require_interpreter()
    target = (HERE / args.lab).resolve()
    if not target.exists():
        print(f"no such lab: {args.lab}", file=sys.stderr)
        print(f"known labs: {', '.join(LABS)}", file=sys.stderr)
        return 1

    result = subprocess.run([interpreter, str(target)], cwd=str(HERE))
    return result.returncode


def cmd_verify(args: argparse.Namespace) -> int:
    """Verify every lab's Expected output against a real run."""
    verifier = HERE / "_verify_beam_labs.py"
    if not verifier.exists():
        print(f"missing {verifier}", file=sys.stderr)
        return 1
    extra = ["--repeats", str(args.repeats)] if args.repeats else []
    result = subprocess.run(
        [require_interpreter(), str(verifier), *extra],
        cwd=str(HERE),
    )
    return result.returncode


def cmd_clean(_args: argparse.Namespace) -> int:
    """Remove the output files the labs write."""
    removed = 0
    patterns = ["_out/*", "_out_*/*", "labs/_out/*", "labs/_out_*/*"]
    for pattern in patterns:
        for path in HERE.glob(pattern):
            if path.is_dir():
                for child in sorted(path.rglob("*"), reverse=True):
                    if child.is_file():
                        child.unlink()
                        removed += 1
                path.rmdir()
            else:
                path.unlink()
                removed += 1
    print(f"removed {removed} output file(s)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="beam_workbench",
        description="Run and verify the Apache Beam labs.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("env", help="report what the workbench can see").set_defaults(
        func=cmd_env
    )
    sub.add_parser("list", help="list the labs").set_defaults(func=cmd_list)

    run_parser = sub.add_parser("run", help="run one lab")
    run_parser.add_argument("lab", help="path relative to the beam/ directory")
    run_parser.set_defaults(func=cmd_run)

    verify_parser = sub.add_parser("verify", help="verify every Expected output")
    verify_parser.add_argument(
        "--repeats",
        type=int,
        default=0,
        help="also re-run each block N times and require identical output",
    )
    verify_parser.set_defaults(func=cmd_verify)

    sub.add_parser("clean", help="remove lab output files").set_defaults(func=cmd_clean)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
