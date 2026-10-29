"""Offline pytest for the Iceberg-lakehouse lab.

Drives the same eight stages the AWS Skill Builder lab covers, against a
PyIceberg InMemoryCatalog so the suite needs zero AWS credentials.
"""
from __future__ import annotations

import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

import pyiceberg.expressions as E  # noqa: E402

from lakehouse import Lakehouse  # noqa: E402


# ============================================================== stage 1
def test_stage1_hive_table_points_at_csv(lake: Lakehouse) -> None:
    """Stage 1: register the seed CSV as a Hive external table."""
    hive = lake.hive_tables["orders_csv"]
    assert hive.location == "s3://athena-iceberg-lakehouse-bucket-test/raw/orders/"
    assert len(hive.scan()) == 12


def test_stage1_hive_table_has_id_columns_as_int(lake: Lakehouse) -> None:
    """CSVs always parse as strings; the lab's glue schema wants int64."""
    sample = lake.hive_tables["orders_csv"].scan()[0]
    assert isinstance(sample["order_id"], int)
    assert isinstance(sample["customer_id"], int)


# ============================================================== stage 2
def test_stage2_ctas_creates_one_snapshot(lake: Lakehouse) -> None:
    """Stage 2: CTAS into Iceberg yields exactly one snapshot, 12 rows."""
    iceberg = lake.iceberg_tables["orders_iceberg"]
    assert iceberg.scan().to_arrow().num_rows == 12
    assert len(lake.history("orders_iceberg")) == 1


def test_stage2_iceberg_table_lives_in_namespace(lake: Lakehouse) -> None:
    """The Iceberg table is registered under the Glue database namespace."""
    assert lake.catalog.list_tables("lakehouse_db_test") == [
        ("lakehouse_db_test", "orders_iceberg")]


# ============================================================== stage 3
def test_stage3_update_rewrites_one_row(lake: Lakehouse) -> None:
    """Stage 3: UPDATE order_id=1001 SET status='shipped'."""
    n = lake.update(name="orders_iceberg",
                     where="order_id = 1001",
                     set_clauses={"status": "shipped"})
    assert n == 1
    rows = lake.iceberg_tables["orders_iceberg"].scan().to_arrow().to_pylist()
    row = next(r for r in rows if r["order_id"] == 1001)
    assert row["status"] == "shipped"
    assert len(rows) == 12


def test_stage3_update_creates_two_snapshots(lake: Lakehouse) -> None:
    """UPDATE is copy-on-write under the hood; we see +2 snapshots."""
    lake.update(name="orders_iceberg",
                 where="order_id = 1001",
                 set_clauses={"status": "shipped"})
    assert len(lake.history("orders_iceberg")) == 3   # CTAS + 2


# ============================================================== stage 4
def test_stage4_delete_drops_cancelled_row(lake: Lakehouse) -> None:
    """Stage 4: DELETE WHERE status = 'cancelled' -- only 1003 is cancelled."""
    n = lake.delete(name="orders_iceberg", where="status = 'cancelled'")
    assert n == 1
    after = lake.iceberg_tables["orders_iceberg"].scan().to_arrow().to_pylist()
    assert len(after) == 11
    assert not any(r["status"] == "cancelled" for r in after)


def test_stage4_delete_creates_one_more_snapshot(lake: Lakehouse) -> None:
    """DELETE produces one new snapshot."""
    lake.delete(name="orders_iceberg", where="status = 'cancelled'")
    assert len(lake.history("orders_iceberg")) == 2  # CTAS + DELETE


# ============================================================== stage 5
def test_stage5_time_travel_to_ctas_snapshot(lake: Lakehouse) -> None:
    """Stage 5: read snapshot 1 directly via scan(snapshot_id=...)."""
    snap1 = list(lake.history("orders_iceberg"))[0].snapshot_id
    old_rows = lake.scan_at_snapshot("orders_iceberg", snap1).to_pylist()
    assert len(old_rows) == 12
    # Row 1001 was 'placed' in the CSV; it stays 'placed' at snapshot 1
    # (the UPDATE that flips it to 'shipped' hasn't happened yet).
    row_1001 = next(r for r in old_rows if r["order_id"] == 1001)
    assert row_1001["status"] == "placed"


def test_stage5_time_travel_via_timestamp(lake: Lakehouse) -> None:
    """FOR SYSTEM_TIME AS OF: timestamp-based time travel resolves to the
    latest snapshot at-or-before the requested timestamp."""
    hist = list(lake.history("orders_iceberg"))
    ts = hist[0].timestamp_ms + 100   # safely after the CTAS, before delete
    at_ts = lake.scan_at_timestamp("orders_iceberg", ts).to_pylist()
    assert len(at_ts) == 12


# ============================================================== stage 6
def test_stage6_history_is_unique_and_ordered(lake: Lakehouse) -> None:
    """Stage 6: history metadata table -- unique IDs, timestamp-ascending."""
    lake.delete(name="orders_iceberg", where="status = 'cancelled'")
    hist = lake.history("orders_iceberg")
    ids = [h.snapshot_id for h in hist]
    ts  = [h.timestamp_ms for h in hist]
    assert len(set(ids)) == len(ids)
    assert ts == sorted(ts)


# ============================================================== stage 7
def test_stage7_insert_appends_two_rows(lake: Lakehouse) -> None:
    """Stage 7: INSERT INTO orders_iceberg VALUES (...) -- +2 rows, +1 snapshot."""
    new_rows = [
        {"order_id": 9001, "customer_id": 42, "amount": "1.00",
         "currency": "USD", "order_date": "2026-09-27", "status": "placed"},
        {"order_id": 9002, "customer_id": 88, "amount": "2.00",
         "currency": "EUR", "order_date": "2026-09-27", "status": "placed"},
    ]
    lake.append("orders_iceberg", new_rows)
    after = lake.iceberg_tables["orders_iceberg"].scan().to_arrow().to_pylist()
    assert len(after) == 14
    assert {9001, 9002} <= {r["order_id"] for r in after}
    assert len(lake.history("orders_iceberg")) == 2   # CTAS + INSERT


# ============================================================== stage 8
def test_stage8_old_snapshot_immutable(lake: Lakehouse) -> None:
    """Stage 8: ACID guarantee -- reading an old snapshot never sees later writes."""
    snap1 = list(lake.history("orders_iceberg"))[0].snapshot_id

    # Appending must not corrupt the older snapshot.
    lake.append("orders_iceberg", [
        {"order_id": 9100, "customer_id": 1, "amount": "0.01",
         "currency": "USD", "order_date": "2026-09-27", "status": "placed"},
    ])
    lake.delete(name="orders_iceberg", where="order_id = 1003")

    snap1_again = lake.scan_at_snapshot(
        "orders_iceberg", snap1).to_pylist()
    assert len(snap1_again) == 12
    assert not any(r["order_id"] >= 9000 for r in snap1_again)
    assert any(r["order_id"] == 1003 for r in snap1_again)   # still present
