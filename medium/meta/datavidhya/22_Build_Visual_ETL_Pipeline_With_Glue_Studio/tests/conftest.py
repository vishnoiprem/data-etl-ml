"""Pytest fixtures for the Glue Studio visual-ETL lab.

Shared SparkSession + a fresh tempdir per test for the curated output.
The driver uses subprocess for end-to-end Glue Studio script execution;
tests use a similar approach with per-test args.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
LAB_DIR = os.path.abspath(os.path.join(HERE, ".."))


@pytest.fixture(scope="session")
def spark():
    from pyspark.sql import SparkSession
    s = (SparkSession.builder
            .appName("q22_pytest")
            .config("spark.sql.shuffle.partitions", "1")
            .config("spark.ui.showConsoleProgress", "false")
            .getOrCreate())
    s.sparkContext.setLogLevel("ERROR")
    yield s
    s.stop()


@pytest.fixture
def graph() -> Dict[str, Any]:
    with open(os.path.join(LAB_DIR, "graph", "customer_etl_graph.json"),
              "r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture
def script_text() -> str:
    path = os.path.join(LAB_DIR, "glue_jobs", "customer_etl_glue_studio.py")
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture
def catalog_schema() -> Dict[str, Any]:
    path = os.path.join(LAB_DIR, "awsglue", "_catalog",
                          "studio_db_local", "customers_raw", "_schema.json")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture
def run_script():
    """Run the Glue Studio script end-to-end against a fresh tempdir."""
    def _run(out_dir: str) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["PYTHONPATH"] = LAB_DIR
        return subprocess.run(
            [sys.executable,
             os.path.join(LAB_DIR, "glue_jobs", "customer_etl_glue_studio.py"),
             "/unused", out_dir],
            capture_output=True, text=True, env=env)
    return _run


@pytest.fixture
def curated_dir() -> str:
    d = tempfile.mkdtemp(prefix="q22_pytest_curated_")
    yield d
    import shutil
    shutil.rmtree(d, ignore_errors=True)