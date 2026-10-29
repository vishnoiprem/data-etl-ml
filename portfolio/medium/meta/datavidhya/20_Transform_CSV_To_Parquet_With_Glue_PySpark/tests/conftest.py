"""Pytest fixtures for the Glue PySpark ETL lab.

Each test gets a fresh SparkSession + a fresh curated-output tempdir. The
driver and tests share ``sales_etl_job.transform`` -- the lab's actual ETL
script -- so a single source of truth covers both runs.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from typing import Iterator

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "glue_jobs"))

from pyspark.sql import SparkSession  # noqa: E402

import sales_etl_job  # noqa: E402

CSV_PATH = os.path.join(_ROOT, "sample_data", "raw_sales_transactions.csv")


@pytest.fixture(scope="session")
def spark() -> Iterator[SparkSession]:
    """A single SparkSession per test session -- starting Spark is slow."""
    s = (SparkSession.builder
         .appName("q20_pytest")
         .config("spark.sql.shuffle.partitions", "1")
         .config("spark.ui.showConsoleProgress", "false")
         .getOrCreate())
    s.sparkContext.setLogLevel("ERROR")
    yield s
    s.stop()


@pytest.fixture
def curated_dir() -> Iterator[str]:
    """Fresh output directory per test -- partitions don't bleed across tests."""
    d = tempfile.mkdtemp(prefix="q20_pytest_curated_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def raw_df(spark: SparkSession):
    """The raw CSV as a DataFrame (all-string schema, mirroring the lab's
    Glue catalog table)."""
    return (spark.read
                 .option("header", True)
                 .option("inferSchema", False)
                 .csv(f"file://{CSV_PATH}"))


@pytest.fixture
def run_etl(spark: SparkSession, curated_dir: str):
    """Run sales_etl_job.main() against the seed CSV into the tempdir.

    Returns a callable so tests can pick ``file://`` or ``s3://`` paths.
    """
    def _run(input_uri: str | None = None) -> None:
        in_uri  = input_uri or f"file://{CSV_PATH}"
        out_uri = f"file://{curated_dir}/curated/sales/"
        subprocess.run(
            [sys.executable,
             os.path.join(_ROOT, "glue_jobs", "sales_etl_job.py"),
             "--input_path",  in_uri,
             "--output_path", out_uri],
            check=True, capture_output=True, text=True,
        )
    return _run
