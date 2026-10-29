"""Assert the pipeline reproduces the documented reference output."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

apache_beam = pytest.importorskip("apache_beam", reason="apache-beam is not installed")

from apache_beam.testing.test_pipeline import TestPipeline  # noqa: E402

from conftest import beam_test_options  # noqa: E402

#: The documented reference output. Four regions, 1,245 counted orders.
EXPECTED = {
    "AMER": (318, 113592.19),
    "APAC": (285, 108194.92),
    "EMEA": (322, 118423.22),
    "LATAM": (320, 110646.18),
}


def _parse(output_file):
    """Parse a summary CSV into a dict of region -> (count, revenue)."""
    rows = {}
    for line in output_file.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("region,"):
            continue
        region, count, revenue = line.split(",")
        rows[region] = (int(count), float(revenue))
    return rows


def test_matches_documented_reference_output(tmp_path):
    """The pipeline reproduces the numbers in the course material."""
    from batch_pipeline import build_pipeline

    sample = Path(__file__).resolve().parents[2] / "sample_data" / "orders.csv"
    if not sample.is_file():
        # `sample_data/` is gitignored — it is generated, not checked in.
        # Generate it so this test passes on a fresh clone.
        import subprocess

        course_root = Path(__file__).resolve().parents[2]
        subprocess.run(
            [
                sys.executable,
                str(course_root / "resources" / "sample_data.py"),
                "--output-dir",
                str(course_root / "sample_data"),
            ],
            check=True,
            capture_output=True,
        )

    assert sample.is_file(), f"sample data missing: {sample}"

    output_prefix = tmp_path / "summary"

    with TestPipeline(options=beam_test_options()) as pipeline:
        build_pipeline(
            pipeline,
            input_path=str(sample),
            output_path=str(output_prefix),
        )

    output_files = sorted(tmp_path.glob("summary*"))
    assert output_files, "the pipeline produced no output file"

    actual = _parse(output_files[0])
    assert actual == EXPECTED
