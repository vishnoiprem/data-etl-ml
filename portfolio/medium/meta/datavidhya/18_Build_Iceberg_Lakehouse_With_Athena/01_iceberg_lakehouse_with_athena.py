"""
Q18: Build an Iceberg Lakehouse with Athena   [AWS | Iceberg, Athena, Lakehouse]

Offline driver: replay the 8 lab stages against a PyIceberg InMemoryCatalog
that mirrors Athena's Iceberg-on-S3 surface area. No AWS, no Glue, no S3 --
just the catalog and a Python dict.

How to Think:
- The "data lake" is just an S3 bucket. CSV and Parquet files sit inside it
  with no schema, no ACID, no rollback. Iceberg is a thin metadata layer
  written ON TOP of those files: a versioned set of JSON manifests pointing
  at the data files. Athena reads the manifests + the data files together.
- Every write -- INSERT, UPDATE, DELETE -- creates a NEW snapshot. Old
  snapshots still point at the old data files, so time travel reads the
  table "exactly as it was" at any earlier snapshot. This is the killer
  feature: a query is always either fully-the-old-version or fully-the-
  new-version, never half-and-half (ACID).
- Athena's CTAS (CREATE TABLE AS SELECT) writes the new Iceberg table as
  one or more Parquet data files + a metadata file pointing at them. It is
  NOT a Hive CREATE TABLE; it's an Iceberg table from birth.

The trap:
- PyIceberg 0.12 has no row-level UPDATE. Athena does (copy-on-write: it
  deletes the old row in one snapshot and inserts the replacement in the
  next). We mirror that here: UPDATE is implemented as
  ``delete + append`` in one logical transaction.
- The lab uses Athena FOR SYSTEM_VERSION AS OF for snapshot-based time
  travel and FOR SYSTEM_TIME AS OF for timestamp-based. The PyIceberg
  equivalents are ``scan(snapshot_id=...)`` and ``scan(timestamp=...)``.
- An Iceberg table's "schema" lives in the metadata file. You can evolve
  the schema (ADD COLUMN, RENAME) and the data files don't need rewriting
  -- only the metadata JSON is touched. This is the other half of the
  "warehouse on a lake" story.

AWS note:
- Athena engine version 3 is the version that supports Iceberg. Earlier
  Athena (engine 2) is Hive-only. The lab workgroup is pinned to engine 3.
- In production, Iceberg tables can be backed by Parquet OR ORC. The lab
  uses Parquet because that's Athena's default and the cheapest to read.
"""
from __future__ import annotations

import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import pyarrow as pa  # noqa: E402

from lakehouse import Lakehouse, ORDERS_SCHEMA  # noqa: E402


def expect(title: str, got, expected) -> None:
    if got != expected:
        print(f"[FAIL] {title}")
        print(f"   expected: {expected}")
        print(f"   got:      {got}")
        raise AssertionError(title)
    print(f"[PASS] {title}")


def main() -> None:
    bucket     = "athena-iceberg-lakehouse-bucket-test"
    db         = "lakehouse_db_test"
    hive_name  = "orders_csv"
    iceberg    = "orders_iceberg"
    csv_path   = os.path.join(_HERE, "sample_data", "orders.csv")

    lake = Lakehouse.new(database=db)

    print("\n=== Q18 Build an Iceberg Lakehouse with Athena ===\n")

    # ------ stage 1: register the seed CSV as a Hive external table
    hive = lake.create_hive_orders(
        name=hive_name, csv_path=csv_path,
        bucket=bucket, prefix="raw/orders/")
    expect("Q18 stage 1 Hive table points at the CSV location",
           hive.location, f"s3://{bucket}/raw/orders/")
    expect("Q18 stage 1 Hive table loaded the seed CSV rows",
           len(hive.scan()), 12)

    # ------ stage 2: CREATE TABLE AS SELECT (CTAS) into an Iceberg table
    iceberg_tbl = lake.create_iceberg_from_select(
        iceberg_name=iceberg, hive_name=hive_name)
    expect("Q18 stage 2 Iceberg table exists in the Glue database namespace",
           lake.catalog.list_tables(db), [(db, iceberg)])
    snap1 = lake.current_snapshot_id(iceberg)
    rows1 = iceberg_tbl.scan().to_arrow()
    expect("Q18 stage 2 CTAS copied 12 rows into the Iceberg table",
           rows1.num_rows, 12)
    expect("Q18 stage 2 Iceberg table has exactly one snapshot after CTAS",
           len(lake.history(iceberg)), 1)

    # ------ stage 3: UPDATE one row -- copy-on-write via delete+append
    # Athena's UPDATE on an Iceberg table is implemented internally as a
    # delete of the old row + append of the replacement. PyIceberg exposes
    # only the primitives, so the lab mirrors the same two-snapshot chain.
    n_updated = lake.update(
        name=iceberg,
        where="order_id = 1001",
        set_clauses={"status": "shipped"},
    )
    expect("Q18 stage 3 UPDATE statement rewrote exactly one row",
           n_updated, 1)
    after_update = iceberg_tbl.scan().to_arrow()
    updated_row = [r for r in after_update.to_pylist()
                   if r["order_id"] == 1001][0]
    expect("Q18 stage 3 row 1001 now has status='shipped'",
           updated_row["status"], "shipped")
    expect("Q18 stage 3 UPDATE creates 2 snapshots (delete + append) "
           "=> CTAS + UPDATE = 3",
           len(lake.history(iceberg)), 3)
    expect("Q18 stage 3 row count is unchanged after UPDATE",
           after_update.num_rows, 12)

    # ------ stage 4: DELETE rows in bulk -- all 'cancelled' orders
    n_deleted = lake.delete(
        name=iceberg, where="status = 'cancelled'")
    expect("Q18 stage 4 DELETE removed exactly one row (only 1003 is cancelled)",
           n_deleted, 1)
    after_delete = iceberg_tbl.scan().to_arrow()
    expect("Q18 stage 4 row count is now 11 after DELETE",
           after_delete.num_rows, 11)
    expect("Q18 stage 4 no cancelled rows remain",
           [r for r in after_delete.to_pylist() if r["status"] == "cancelled"],
           [])
    expect("Q18 stage 4 DELETE created one more snapshot => total 4",
           len(lake.history(iceberg)), 4)

    # ------ stage 5: time travel -- snapshot-based FOR SYSTEM_VERSION AS OF
    at_snap1 = lake.scan_at_snapshot(iceberg, snap1)
    expect("Q18 stage 5 time travel to snapshot 1 returns the CTAS row count",
           at_snap1.num_rows, 12)
    expect("Q18 stage 5 time-travel snapshot 1 still has status='placed' for 1001",
           [r for r in at_snap1.to_pylist() if r["order_id"] == 1001][0]["status"],
           "placed")

    # Time travel via timestamp: pick the timestamp of the SECOND snapshot
    # (i.e. just after the first UPDATE). Anything at-or-before that timestamp
    # still resolves to the CTAS state.
    snap2_ts = lake.history(iceberg)[1].timestamp_ms - 1
    at_ts = lake.scan_at_timestamp(iceberg, snap2_ts)
    expect("Q18 stage 5 timestamp-based time travel returns the original row count",
           at_ts.num_rows, 12)

    # ------ stage 6: inspect the snapshots metadata table
    hist = lake.history(iceberg)
    expect("Q18 stage 6 history table has 4 entries "
           "(CTAS, UPDATE x 2, DELETE)",
           len(hist), 4)
    snap_ids = [h.snapshot_id for h in hist]
    expect("Q18 stage 6 every snapshot has a unique ID",
           len(set(snap_ids)) == len(snap_ids), True)
    expect("Q18 stage 6 snapshots are ordered by timestamp ascending",
           [h.timestamp_ms for h in hist] == sorted(h.timestamp_ms for h in hist),
           True)
    expect("Q18 stage 6 the head snapshot is not the original CTAS snapshot",
           lake.current_snapshot_id(iceberg) != snap1, True)

    # ------ stage 7: INSERT INTO ... append a fresh row
    new_rows = [
        {"order_id":    2001, "customer_id": 42, "amount": "500.00",
         "currency": "USD", "order_date": "2026-09-27", "status": "placed"},
        {"order_id":    2002, "customer_id": 88, "amount": "75.00",
         "currency": "EUR", "order_date": "2026-09-27", "status": "placed"},
    ]
    n_appended = lake.append(iceberg, new_rows)
    expect("Q18 stage 7 INSERT INTO appends two rows",
           n_appended, 2)
    after_append = iceberg_tbl.scan().to_arrow()
    expect("Q18 stage 7 row count after INSERT is 13 (11 + 2)",
           after_append.num_rows, 13)
    expect("Q18 stage 7 INSERT created a fifth snapshot",
           len(lake.history(iceberg)), 5)
    appended_ids = sorted([r["order_id"] for r in after_append.to_pylist()
                           if r["order_id"] >= 2000])
    expect("Q18 stage 7 the two new rows are visible at the head snapshot",
           appended_ids, [2001, 2002])

    # ------ stage 8: re-read the original snapshot -- the INSERT must not leak
    snap1_after_inserts = lake.scan_at_snapshot(iceberg, snap1)
    expect("Q18 stage 8 reading snapshot 1 after the INSERT still shows 12 rows",
           snap1_after_inserts.num_rows, 12)
    expect("Q18 stage 8 snapshot 1 has no order_id >= 2000 (immutable history)",
           [r for r in snap1_after_inserts.to_pylist()
            if r["order_id"] >= 2000], [])
    print("[PASS] Q18 stage 8 snapshot isolation: ACID reads are stable")

    print("\n=== All Q18 stages pass ===\n")


if __name__ == "__main__":
    main()
