"""Pytest fixtures for the Athena lab -- DuckDB connection + sample CSV path.

Single shared DuckDB connection. The schema + table are created once
per session and torn down at the end; tests assert against the same
SQL the driver uses.
"""
from __future__ import annotations

import os

import duckdb
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
LAB_DIR = os.path.abspath(os.path.join(HERE, ".."))
SAMPLE_CSV = os.path.join(LAB_DIR, "sample_data", "yellow_taxi_sample.csv")
DATABASE = "taxi_db"
TABLE = "taxi_trips"


@pytest.fixture(scope="session")
def db():
    """One in-memory DuckDB connection shared by every test."""
    con = duckdb.connect()
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {DATABASE}")
    con.execute(f"DROP TABLE IF EXISTS {DATABASE}.{TABLE}")
    con.execute(f"""
        CREATE TABLE {DATABASE}.{TABLE} AS
        SELECT * FROM read_csv_auto('{SAMPLE_CSV}', header=true)
    """)
    yield con
    con.execute(f"DROP SCHEMA {DATABASE} CASCADE")
    con.close()


@pytest.fixture
def taxi_csv_path() -> str:
    return SAMPLE_CSV


@pytest.fixture
def database_name() -> str:
    return DATABASE


@pytest.fixture
def table_name() -> str:
    return TABLE


@pytest.fixture
def fully_qualified_table() -> str:
    return f"{DATABASE}.{TABLE}"