"""Pytest fixtures shared across the Iceberg-with-Athena tests.

Each test gets a fresh Lakehouse instance in a fresh namespace, so they
don't bleed snapshots into one another.
"""
from __future__ import annotations

import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

from lakehouse import Lakehouse  # noqa: E402


@pytest.fixture
def lake(tmp_path) -> Lakehouse:
    """Fresh in-memory lakehouse, each test owns its own namespace."""
    db = "lakehouse_db_test"
    lake = Lakehouse.new(database=db)
    csv_path = os.path.join(_ROOT, "sample_data", "orders.csv")
    lake.create_hive_orders(
        name="orders_csv", csv_path=csv_path,
        bucket="athena-iceberg-lakehouse-bucket-test",
        prefix="raw/orders/",
    )
    lake.create_iceberg_from_select(
        iceberg_name="orders_iceberg", hive_name="orders_csv")
    return lake
