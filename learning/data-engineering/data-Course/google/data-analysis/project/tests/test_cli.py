"""End-to-end tests for the CLI and the shipped sample data.

These are the tests that prove the project *runs*. They execute the
real command line against the real generated dataset, so a broken
import, a wrong flag name or a mismatched output format fails here
rather than in a reader's terminal.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parent.parent
ROOT = PROJECT.parent
CLI = PROJECT / "local_bi.py"

CORE = PROJECT / "core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from model import build_explores, build_sales_model  # noqa: E402


def run(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the CLI as a subprocess.

    Args:
        args: The command-line arguments.

    Returns:
        The completed process.
    """
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )


@pytest.fixture(scope="module")
def sample_dir(tmp_path_factory):
    """Generate the sample dataset once for the module.

    Args:
        tmp_path_factory: The pytest fixture factory.

    Returns:
        The directory holding the generated files.
    """
    output = tmp_path_factory.mktemp("sample_data")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "resources" / "sample_data.py"),
            "--output-dir",
            str(output),
        ],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stderr
    return output


# --------------------------------------------------------------------------
# The CLI runs
# --------------------------------------------------------------------------


def test_the_cli_prints_its_help():
    """The CLI has a working help screen."""
    result = run("--help")
    assert result.returncode == 0
    assert "local_bi" in result.stdout


def test_describe_prints_the_semantic_layer(sample_dir):
    """`describe` prints the models, their grains and their measures."""
    result = run("describe")
    assert result.returncode == 0
    assert "one row per order line" in result.stdout
    assert "total_revenue" in result.stdout
    assert "gross_margin" in result.stdout


def test_explores_lists_the_fan_out_join(sample_dir):
    """`explores` names the fan-out join."""
    result = run("explores")
    assert result.returncode == 0
    assert "FAN-OUT" in result.stdout


def test_query_aggregates_the_fact_table(sample_dir):
    """`query` groups by a dimension and sums a measure."""
    result = run(
        "query",
        "--input",
        str(sample_dir / "orders.csv"),
        "--dimensions",
        "region",
        "--measures",
        "total_revenue",
    )
    assert result.returncode == 0, result.stderr
    assert "region" in result.stdout
    assert "total_revenue" in result.stdout
    for region in ("AMER", "EMEA", "APAC", "LATAM"):
        assert region in result.stdout


def test_query_writes_csv(sample_dir, tmp_path):
    """`query --format csv --output` writes a CSV file."""
    output = tmp_path / "out.csv"
    result = run(
        "query",
        "--input",
        str(sample_dir / "orders.csv"),
        "--dimensions",
        "region",
        "--measures",
        "total_revenue",
        "--format",
        "csv",
        "--output",
        str(output),
    )
    assert result.returncode == 0, result.stderr
    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert text.splitlines()[0] == "region,total_revenue"


def test_query_writes_json(sample_dir, tmp_path):
    """`query --format json --output` writes valid JSON."""
    import json

    output = tmp_path / "out.json"
    result = run(
        "query",
        "--input",
        str(sample_dir / "orders.csv"),
        "--dimensions",
        "channel",
        "--measures",
        "total_revenue",
        "--format",
        "json",
        "--output",
        str(output),
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert payload
    assert "channel" in payload[0]


def test_query_rejects_an_unknown_measure(sample_dir):
    """A query for a measure that does not exist fails loudly."""
    result = run(
        "query",
        "--input",
        str(sample_dir / "orders.csv"),
        "--measures",
        "nonexistent",
    )
    assert result.returncode == 2
    assert "unknown field" in result.stderr


def test_query_requires_a_measure(sample_dir):
    """A query with no measure fails."""
    result = run(
        "query",
        "--input",
        str(sample_dir / "orders.csv"),
        "--dimensions",
        "region",
    )
    assert result.returncode == 2
    assert "at least one measure" in result.stderr


def test_validate_fails_on_the_sample_data(sample_dir):
    """The planted duplicate makes the validation fail.

    This is the point: the sample data is deliberately imperfect, so the
    gate has something real to catch, and the exit code is non-zero.
    """
    result = run("validate", "--input", str(sample_dir / "orders.csv"))
    assert result.returncode == 1
    assert "grain.not_unique" in result.stdout
    assert "FAIL" in result.stdout


def test_validate_reports_the_stale_extract(sample_dir):
    """The stale extract is caught too."""
    result = run("validate", "--input", str(sample_dir / "orders.csv"))
    assert "freshness.stale" in result.stdout


def test_validate_accepts_the_negative_revenue_as_a_warning(sample_dir):
    """A refund is a warning, not a failure — on its own."""
    result = run("validate", "--input", str(sample_dir / "orders.csv"))
    assert "value.negative" in result.stdout


def test_spine_finds_the_empty_days(sample_dir):
    """`spine` finds the days with no orders."""
    result = run(
        "spine",
        "--input",
        str(sample_dir / "orders.csv"),
        "--timeframe",
        "day",
    )
    assert result.returncode == 0
    assert "empty buckets" in result.stdout
    assert "The empty buckets" in result.stdout


def test_spine_writes_a_filled_csv(sample_dir, tmp_path):
    """`spine --output` writes every bucket, empty or not."""
    import csv

    output = tmp_path / "spine.csv"
    result = run(
        "spine",
        "--input",
        str(sample_dir / "orders.csv"),
        "--timeframe",
        "day",
        "--output",
        str(output),
    )
    assert result.returncode == 0, result.stderr
    rows = list(csv.DictReader(output.open(encoding="utf-8")))
    assert len(rows) > 100
    assert "order_lines" in rows[0]
    assert "revenue" in rows[0]


def test_spine_range_prints_a_calendar():
    """`spine-range` prints one line per day."""
    result = run(
        "spine-range", "--start", "2026-03-01", "--end", "2026-03-07"
    )
    assert result.returncode == 0
    assert "2026-03-01" in result.stdout
    assert "7 days" in result.stdout


def test_lookml_renders_the_semantic_layer():
    """`lookml` renders LookML with the relationship types."""
    result = run("lookml", "--with-explores")
    assert result.returncode == 0
    assert "view: orders {" in result.stdout
    assert "measure: total_revenue {" in result.stdout
    assert "relationship: many_to_one" in result.stdout
    assert "relationship: one_to_many" in result.stdout
    assert "explore: orders {" in result.stdout


def test_lookml_writes_a_file(tmp_path):
    """`lookml --output` writes the file."""
    output = tmp_path / "out.lookml"
    result = run("lookml", "--with-explores", "--output", str(output))
    assert result.returncode == 0
    assert output.exists()
    assert "view: orders {" in output.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# The shipped LookML file is current
# --------------------------------------------------------------------------


def test_the_shipped_lookml_matches_the_generator():
    """The committed LookML is what the generator produces.

    If the semantic layer changes and the LookML file is not
    regenerated, the two drift apart and a Looker developer gets a file
    that does not match the model the course teaches.
    """
    shipped = PROJECT / "lookml" / "ecommerce.model.lookml"
    assert shipped.exists()

    result = run("lookml", "--with-explores")
    assert result.returncode == 0
    assert shipped.read_text(encoding="utf-8") == result.stdout


# --------------------------------------------------------------------------
# The shipped sample data is current
# --------------------------------------------------------------------------


def test_the_sample_data_generator_is_deterministic():
    """Two runs produce byte-identical files."""
    import tempfile

    outputs = []
    for _ in range(2):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "resources" / "sample_data.py"),
                    "--output-dir",
                    tmp,
                ],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            )
            assert result.returncode == 0, result.stderr
            outputs.append(
                (Path(tmp) / "orders.csv").read_text(encoding="utf-8")
            )
    assert outputs[0] == outputs[1]
