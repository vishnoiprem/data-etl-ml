"""Shared helpers for the Beam labs.

Every lab in this suite imports from here, so the labs stay short and focused
on the Beam concept they are teaching.  This module deliberately contains no
Beam logic of its own — it is setup, data loading, and output formatting.

Import it from a lab with::

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from beam_lib import ...

or simply run the lab through the workbench::

    python beam_workbench.py run labs/01-beam-basics.py
"""

from __future__ import annotations

import json
import pathlib
import sys

# --------------------------------------------------------------------------
# Paths — resolve the course root so labs work from any working directory.
# --------------------------------------------------------------------------

HERE = pathlib.Path(__file__).resolve().parent
COURSE = HERE.parent.parent
CORE = COURSE / "project" / "core"
SAMPLE_DATA = COURSE / "sample_data"

# The course's own pure-Python core: validation, currency normalisation,
# windowing, dedup, and the BigQuery row shape.
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))


# --------------------------------------------------------------------------
# Data access
# --------------------------------------------------------------------------

def read_events(path: pathlib.Path | None = None) -> list[str]:
    """Return the raw lines of the sample event file, header excluded.

    The course's generator writes ``sample_data/events.csv`` with a header
    row.  Beam's ``ReadFromText`` reads the header like any other line, so
    the labs strip it deliberately rather than letting it become an event.
    """
    target = path or (SAMPLE_DATA / "events.csv")
    if not target.exists():
        raise FileNotFoundError(
            f"{target} not found. Generate it first:\n"
            "    python resources/sample_data.py --output-dir ./sample_data"
        )
    lines = target.read_text().splitlines()
    if lines and lines[0].lower().startswith("event_id,"):
        lines = lines[1:]
    return lines


def read_malformed(path: pathlib.Path | None = None) -> list[str]:
    """Return the raw lines of the malformed event file (no header)."""
    target = path or (SAMPLE_DATA / "malformed_events.csv")
    if not target.exists():
        raise FileNotFoundError(
            f"{target} not found. Generate it first:\n"
            "    python resources/sample_data.py --output-dir ./sample_data"
        )
    return target.read_text().splitlines()


# --------------------------------------------------------------------------
# Beam plumbing
# --------------------------------------------------------------------------

def pipeline_options(runner: str = "DirectRunner", extra: list[str] | None = None):
    """Return the ``PipelineOptions`` every lab uses.

    The legacy Direct Runner is requested explicitly with a LOOPBACK
    environment.  Beam 2.77 otherwise defaults to the Prism runner, which
    does not support every transform the labs use (windowed
    ``CombinePerKey`` and ``ParDo`` reading ``DoFn.WindowParam`` both fail on
    it with a gRPC worker-pool error).
    """
    import apache_beam as beam
    from apache_beam.options.pipeline_options import PipelineOptions

    args = ["--runner=" + runner]
    if runner == "DirectRunner":
        args.append("--environment_type=LOOPBACK")
    if extra:
        args.extend(extra)
    return PipelineOptions(args)


def read_output(pattern: str) -> list[str]:
    """Read back what ``WriteToText`` produced, newest file last.

    ``WriteToText`` writes shard files named ``<prefix>-00000-of-00001`` and
    friends, so the labs need to glob for them.  The lines are returned with
    trailing newlines stripped, ready to print.
    """
    import glob

    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"no output files matching {pattern}")
    lines: list[str] = []
    for name in files:
        lines.extend(
            line.rstrip("\n")
            for line in pathlib.Path(name).read_text().splitlines()
            if line.strip()
        )
    return lines


def as_json(rows: list[dict]) -> list[str]:
    """Render dict rows as sorted-key JSON, one per line."""
    return [json.dumps(row, sort_keys=True) for row in rows]


def show(title: str, lines: list[str], limit: int | None = None) -> None:
    """Print a titled block of output lines."""
    print(title)
    shown = lines if limit is None else lines[:limit]
    for line in shown:
        print(f"  {line}")
    if limit is not None and len(lines) > limit:
        print(f"  ... and {len(lines) - limit} more")


def banner(title: str) -> None:
    """Print a section header."""
    print()
    print(title)
    print("-" * len(title))
