"""
test_pipeline.py — integration tests for the runnable pipelines.

These tests drive `cdc_pipeline.py` and `kafka_to_gcp.py` end to end over
the generated sample data. They need no cloud account and no bill.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent
COURSE_ROOT = PROJECT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

import cdc_pipeline  # noqa: E402


@pytest.fixture(scope="module")
def sample_data(tmp_path_factory) -> Path:
    """Generate the sample dataset once for the whole module."""
    out_dir = tmp_path_factory.mktemp("sample_data")
    result = subprocess.run(
        [
            sys.executable,
            str(COURSE_ROOT / "resources" / "sample_data.py"),
            "--output-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(f"sample_data.py failed:\n{result.stdout}\n{result.stderr}")
    return out_dir


# --------------------------------------------------------------------------
# The CDC pipeline
# --------------------------------------------------------------------------


class TestCdcPipeline:
    """The end-to-end CDC replay."""

    def test_replays_the_sample_data(self, sample_data, tmp_path):
        output = tmp_path / "customers"
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_DIR / "cdc_pipeline.py"),
                "--input",
                str(sample_data / "changes.ndjson"),
                "--output",
                str(output),
                "--merge-keys",
                "customer_id",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "CDC replay summary" in result.stdout

    def test_writes_csv_and_json_outputs(self, sample_data, tmp_path):
        output = tmp_path / "customers"
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_DIR / "cdc_pipeline.py"),
                "--input",
                str(sample_data / "changes.ndjson"),
                "--output",
                str(output),
                "--merge-keys",
                "customer_id",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert output.with_suffix(".csv").exists()
        assert output.with_suffix(".json").exists()

    def test_the_json_output_is_valid_and_non_empty(self, sample_data, tmp_path):
        output = tmp_path / "customers"
        subprocess.run(
            [
                sys.executable,
                str(PROJECT_DIR / "cdc_pipeline.py"),
                "--input",
                str(sample_data / "changes.ndjson"),
                "--output",
                str(output),
                "--merge-keys",
                "customer_id",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        rows = json.loads(output.with_suffix(".json").read_text())
        assert len(rows) > 0
        assert "customer_id" in rows[0]

    def test_the_csv_output_has_a_header(self, sample_data, tmp_path):
        output = tmp_path / "customers"
        subprocess.run(
            [
                sys.executable,
                str(PROJECT_DIR / "cdc_pipeline.py"),
                "--input",
                str(sample_data / "changes.ndjson"),
                "--output",
                str(output),
                "--merge-keys",
                "customer_id",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        first_line = output.with_suffix(".csv").read_text().splitlines()[0]
        assert first_line.startswith("customer_id,")

    def test_the_run_is_reproducible(self, sample_data, tmp_path):
        """Two runs over the same input give the same output."""
        outputs = []
        for name in ("run_a", "run_b"):
            output = tmp_path / name
            subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_DIR / "cdc_pipeline.py"),
                    "--input",
                    str(sample_data / "changes.ndjson"),
                    "--output",
                    str(output),
                    "--merge-keys",
                    "customer_id",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            outputs.append(output.with_suffix(".json").read_text())
        assert outputs[0] == outputs[1]

    def test_the_deleted_rows_are_absent_from_the_output(self, sample_data, tmp_path):
        """The end-to-end proof that the DELETE was applied."""
        output = tmp_path / "customers"
        subprocess.run(
            [
                sys.executable,
                str(PROJECT_DIR / "cdc_pipeline.py"),
                "--input",
                str(sample_data / "changes.ndjson"),
                "--output",
                str(output),
                "--merge-keys",
                "customer_id",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        rows = json.loads(output.with_suffix(".json").read_text())

        events = [
            json.loads(line)
            for line in (sample_data / "changes.ndjson").read_text().splitlines()
            if line.strip()
        ]
        deleted = {
            event["before"]["customer_id"]
            for event in events
            if event.get("op") == "DELETE" and event.get("before")
        }
        present = {row["customer_id"] for row in rows}
        assert deleted.isdisjoint(present)

    def test_a_missing_input_file_fails_cleanly(self, tmp_path):
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_DIR / "cdc_pipeline.py"),
                "--input",
                str(tmp_path / "does_not_exist.ndjson"),
                "--output",
                str(tmp_path / "out"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 2

    def test_the_audit_file_is_written(self, sample_data, tmp_path):
        output = tmp_path / "customers"
        audit = tmp_path / "audit.json"
        subprocess.run(
            [
                sys.executable,
                str(PROJECT_DIR / "cdc_pipeline.py"),
                "--input",
                str(sample_data / "changes.ndjson"),
                "--output",
                str(output),
                "--merge-keys",
                "customer_id",
                "--audit",
                str(audit),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        audit_data = json.loads(audit.read_text())
        assert audit_data["rows"] > 0
        assert audit_data["events_read"] > 0


# --------------------------------------------------------------------------
# The Kafka pipeline
# --------------------------------------------------------------------------


class TestKafkaPipeline:
    """The end-to-end Kafka replay."""

    def test_replays_the_sample_messages(self, sample_data, tmp_path):
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_DIR / "kafka_to_gcp.py"),
                "--messages",
                str(sample_data / "transactions.ndjson"),
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "Kafka → GCP replay summary" in result.stdout

    def test_ingests_every_valid_message(self, sample_data, tmp_path):
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_DIR / "kafka_to_gcp.py"),
                "--messages",
                str(sample_data / "transactions.ndjson"),
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        assert "rejected         : 0" in result.stdout

    def test_a_missing_messages_file_fails_cleanly(self, tmp_path):
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_DIR / "kafka_to_gcp.py"),
                "--messages",
                str(tmp_path / "nope.ndjson"),
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 2


# --------------------------------------------------------------------------
# The sample data generator
# --------------------------------------------------------------------------


class TestSampleData:
    """The generator itself."""

    def test_the_generated_files_all_exist(self, sample_data):
        for name in (
            "customers.csv",
            "customers.ndjson",
            "changes.ndjson",
            "transactions.ndjson",
            "summary.json",
        ):
            assert (sample_data / name).exists(), name

    def test_the_change_events_cover_all_three_operations(self, sample_data):
        events = [
            json.loads(line)
            for line in (sample_data / "changes.ndjson").read_text().splitlines()
            if line.strip()
        ]
        ops = {event.get("op") for event in events}
        assert {"INSERT", "UPDATE", "DELETE"} <= ops

    def test_the_generation_is_deterministic(self, tmp_path):
        first = tmp_path / "a"
        second = tmp_path / "b"
        for target in (first, second):
            subprocess.run(
                [
                    sys.executable,
                    str(COURSE_ROOT / "resources" / "sample_data.py"),
                    "--output-dir",
                    str(target),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
        assert (first / "changes.ndjson").read_bytes() == (
            second / "changes.ndjson"
        ).read_bytes()
