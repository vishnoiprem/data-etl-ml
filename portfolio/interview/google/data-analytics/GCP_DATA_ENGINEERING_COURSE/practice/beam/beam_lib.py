"""Shared helpers for the Beam practice modules and labs.

Every module and lab imports from here, so the teaching material stays short
and focused on the Beam concept it is teaching.  This module contains setup
and output formatting only — no Beam logic of its own.

Import it from a module or lab with::

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from beam_lib import ...

or run a lab through the workbench::

    python beam_workbench.py run labs/01-beam-basics.py
"""

from __future__ import annotations

import glob
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
COURSE = HERE.parent.parent
REPO = COURSE.parent.parent.parent.parent

# The user's own lab material: notebooks, sample data, template method.
LAB_DIR = COURSE / "practice" / "Lab-sessions-beam-dataflow"
SAMPLE_DATA = LAB_DIR / "sample_data"
TEMPLATE_METHOD = LAB_DIR / "Template Method"

# The course's generated sample data: 4800 events, 12 malformed.
COURSE_SAMPLE_DATA = COURSE / "sample_data"

# Where the labs write their output.
OUT_DIR = HERE / "_out"


# --------------------------------------------------------------------------
# Pipeline options
# --------------------------------------------------------------------------

def pipeline_options(runner: str = "DirectRunner", extra: list[str] | None = None):
    """Return the ``PipelineOptions`` every module and lab uses.

    The legacy Direct Runner is requested explicitly with a LOOPBACK
    environment.  Beam 2.77 otherwise defaults to the Prism runner, which
    does not support every transform the material uses.
    """
    from apache_beam.options.pipeline_options import PipelineOptions

    args = ["--runner=" + runner]
    if runner == "DirectRunner":
        args.append("--environment_type=LOOPBACK")
    if extra:
        args.extend(extra)
    return PipelineOptions(args)


# --------------------------------------------------------------------------
# Data access
# --------------------------------------------------------------------------

def read_rows(path: pathlib.Path, *, skip_header: bool = True) -> list[str]:
    """Return the lines of a local data file, header optionally stripped."""
    lines = path.read_text().splitlines()
    if skip_header and lines:
        lines = lines[1:]
    return lines


def sample_file(name: str) -> pathlib.Path:
    """Return the path of a file in the lab sample data folder."""
    path = SAMPLE_DATA / name
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    return path


def read_sample(name: str, *, skip_header: bool = True) -> list[str]:
    """Return the lines of a sample data file, header optionally stripped."""
    return read_rows(sample_file(name), skip_header=skip_header)


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def read_output(pattern: str) -> list[str]:
    """Read back what ``WriteToText`` produced.

    ``WriteToText`` writes shard files named ``<prefix>-00000-of-00001`` and
    friends, so the labs glob for them.  Lines come back with trailing
    newlines stripped, ready to print.
    """
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
