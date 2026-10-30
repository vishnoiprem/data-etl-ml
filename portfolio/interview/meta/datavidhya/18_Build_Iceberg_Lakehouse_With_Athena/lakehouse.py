"""Offline Iceberg-lakehouse simulator for the Q18 lab.

Wraps ``pyiceberg.catalog.memory.InMemoryCatalog`` so we can drive every
lab stage without an AWS account. Mirrors the Athena surface area used in
the lab:

  - ``CREATE TABLE ... STORED AS PARQUET`` (Hive external table backed by CSV)
  - ``CREATE TABLE AS SELECT`` (CTAS into an Iceberg table)
  - ``UPDATE`` (PyIceberg 0.12 has no row-level UPDATE; the lab uses the
    same copy-on-write pattern Athena uses -- delete then append)
  - ``DELETE``
  - ``FOR SYSTEM_TIME AS OF`` / ``FOR SYSTEM_VERSION AS OF`` (time travel)
  - Metadata tables: ``snapshots``, ``history``, ``files``

The whole thing is in-memory; PyIceberg does write a manifest layout to a
tempdir on disk for the metadata JSON, which we let it manage.
"""
from __future__ import annotations

import datetime as _dt
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pyarrow as pa
import pyiceberg.expressions as E
from pyiceberg.catalog.memory import InMemoryCatalog
from pyiceberg.schema import Schema
from pyiceberg.table import Table
from pyiceberg.types import LongType, NestedField, StringType

# PyIceberg ships its own tempdir for metadata.json; let it use a stable one
# under the project root so it's clear where artifacts land if you re-run.
_REPO_TMP = Path(__file__).resolve().parent / ".tmp"
_REPO_TMP.mkdir(exist_ok=True)
os.environ.setdefault("TMPDIR", str(_REPO_TMP))


# Schema used for both the source CSV-as-Hive table and the Iceberg table.
# Five columns mirrors the lab's "orders" domain. status is the field the
# lab's UPDATE touches (placed -> shipped).
ORDERS_SCHEMA = Schema(
    NestedField(1, "order_id",    LongType(),   required=True),
    NestedField(2, "customer_id", LongType(),   required=True),
    NestedField(3, "amount",      StringType(), required=False),
    NestedField(4, "currency",    StringType(), required=False),
    NestedField(5, "order_date",  StringType(), required=False),
    NestedField(6, "status",      StringType(), required=False),
)


# PyArrow schema mirror of ORDERS_SCHEMA -- the append/delete API wants this.
_ORDERS_PA_SCHEMA = pa.schema([
    ("order_id",    pa.int64(),  False),
    ("customer_id", pa.int64(),  False),
    ("amount",      pa.string(), True),
    ("currency",    pa.string(), True),
    ("order_date",  pa.string(), True),
    ("status",      pa.string(), True),
])


@dataclass
class HiveTable:
    """Lab's "stage 1" target: a Hive external table over the raw CSV.

    Hive tables are NOT managed by Iceberg -- they're the read-only landing
    pad the lab starts from. We model them as a plain in-memory list of rows
    (a SELECT scans them; no transactions).
    """
    name:     str
    location: str                          # "s3://<bucket>/<prefix>/"
    rows:     List[Dict[str, Any]] = field(default_factory=list)

    def scan(self) -> List[Dict[str, Any]]:
        return list(self.rows)


@dataclass
class Lakehouse:
    """Stateful in-memory replica of one lab session.

    Owns:
      - a PyIceberg InMemoryCatalog (the Iceberg-managed tables)
      - a dict of HiveTable objects (the non-Iceberg read-only tables)

    The driver's stages call methods in the same order the lab does them.
    """
    catalog:        InMemoryCatalog
    database:       str
    hive_tables:    Dict[str, HiveTable] = field(default_factory=dict)
    iceberg_tables: Dict[str, Table]     = field(default_factory=dict)

    @classmethod
    def new(cls, database: str) -> "Lakehouse":
        """Provision the Glue database equivalent (Iceberg namespace)."""
        cat = InMemoryCatalog("athena-iceberg-lakehouse")
        cat.create_namespace(database)
        return cls(catalog=cat, database=database)

    # --------------------------------------------------------------- Hive
    def create_hive_orders(self, name: str, csv_path: str,
                            bucket: str, prefix: str) -> HiveTable:
        """CREATE EXTERNAL TABLE ... STORED AS PARQUET LOCATION 's3://...'

        The lab uses Athena's Hive syntax, which reads ANY file format Athena
        can SerDe; CSV is fine for the source CSV. We just load the CSV
        rows into a HiveTable.
        """
        import csv
        with open(csv_path, encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        # CSV gives us strings; the orders schema needs long for id cols.
        for row in rows:
            row["order_id"]    = int(row["order_id"])
            row["customer_id"] = int(row["customer_id"])
        tbl = HiveTable(name=name, location=f"s3://{bucket}/{prefix}",
                        rows=rows)
        self.hive_tables[name] = tbl
        return tbl

    # ----------------------------------------------------------- Iceberg
    def create_iceberg_from_select(self, iceberg_name: str,
                                    hive_name: str,
                                    where: Optional[str] = None) -> Table:
        """CREATE TABLE iceberg_name AS SELECT * FROM hive_name [WHERE ...]

        PyIceberg has no CTAS API; we copy the Hive rows into a freshly-
        created Iceberg table -- the same shape Athena CTAS produces
        (one Parquet data file + one snapshot).
        """
        tbl = self.catalog.create_table(
            identifier=(self.database, iceberg_name),
            schema=ORDERS_SCHEMA,
        )
        rows = self.hive_tables[hive_name].scan()
        if where:
            rows = _apply_where(rows, where)
        self.iceberg_tables[iceberg_name] = tbl
        if rows:
            tbl.append(_rows_to_pa(rows))
        return tbl

    def delete(self, name: str, where: str) -> int:
        """DELETE FROM name WHERE ... -> number of rows deleted."""
        tbl = self.iceberg_tables[name]
        expr = _compile_where(where)
        before = tbl.scan().to_arrow().num_rows
        tbl.delete(delete_filter=expr)
        after = tbl.scan().to_arrow().num_rows
        return before - after

    def update(self, name: str, where: str, set_clauses: Dict[str, str]) -> int:
        """UPDATE name SET col=val WHERE ...

        PyIceberg 0.12 lacks row-level UPDATE; the lab itself uses Athena's
        copy-on-write rewrite (DELETE old row, INSERT new row in one
        transaction). We replicate that by issuing two operations: a delete
        on the filter, then an append of the replacement rows.
        """
        tbl = self.iceberg_tables[name]
        rows_to_replace = tbl.scan(
            row_filter=_compile_where(where)).to_arrow().to_pylist()
        for row in rows_to_replace:
            row.update(set_clauses)

        tbl.delete(delete_filter=_compile_where(where))
        if rows_to_replace:
            tbl.append(pa.Table.from_pylist(rows_to_replace,
                                            schema=_ORDERS_PA_SCHEMA))
        return len(rows_to_replace)

    def append(self, name: str, rows: List[Dict[str, Any]]) -> int:
        """INSERT INTO name VALUES (...) -- lab stage 7."""
        tbl = self.iceberg_tables[name]
        tbl.append(_rows_to_pa(rows))
        return len(rows)

    # ----------------------------------------------------- time travel
    def scan_at_snapshot(self, name: str, snapshot_id: int) -> pa.Table:
        """FOR SYSTEM_VERSION AS OF <snapshot_id>."""
        return self.iceberg_tables[name].scan(
            snapshot_id=snapshot_id).to_arrow()

    def scan_at_timestamp(self, name: str, ts_ms: int) -> pa.Table:
        """FOR SYSTEM_TIME AS OF '<iso8601>'.

        PyIceberg 0.12 has no native ``scan(timestamp=...)`` API. We find
        the latest snapshot whose ``timestamp_ms`` is <= ``ts_ms`` and
        delegate to ``scan(snapshot_id=...)``. Athena's timestamp-based
        time travel uses the same fallback semantics.
        """
        matching = [h for h in self.history(name) if h.timestamp_ms <= ts_ms]
        if not matching:
            raise ValueError(f"no snapshot at or before timestamp {ts_ms}")
        snap_id = max(matching, key=lambda h: h.timestamp_ms).snapshot_id
        return self.scan_at_snapshot(name, snap_id)

    def history(self, name: str) -> List[Any]:
        """Return snapshots metadata, oldest-first."""
        return list(self.iceberg_tables[name].history())

    def current_snapshot_id(self, name: str) -> int:
        snap = self.iceberg_tables[name].current_snapshot()
        return snap.snapshot_id if snap else -1


# ============================================================ helpers
def _rows_to_pa(rows: List[Dict[str, Any]]) -> pa.Table:
    """Materialise a list of dicts into a typed PyArrow table.

    PyIceberg refuses to append when the PyArrow types don't match the
    Iceberg schema, so we go via from_pylist with the explicit schema.
    """
    return pa.Table.from_pylist(rows, schema=_ORDERS_PA_SCHEMA)


def _apply_where(rows: List[Dict[str, Any]], where: str) -> List[Dict[str, Any]]:
    """Filter rows using a tiny WHERE-subset DSL the lab's CTAS exercises.

    The lab's CTAS is `CREATE TABLE orders_iceberg AS SELECT * FROM
    orders_csv WHERE status = 'placed'`, so we only need ``col = 'val'``.
    """
    col, val = [t.strip() for t in where.split("=", 1)]
    val = val.strip("'\"")
    return [r for r in rows if str(r.get(col)) == val]


def _compile_where(where: str) -> Any:
    """Translate a single-clause WHERE into a PyIceberg BooleanExpression.

    Supports: ``col = 'val'`` and ``col = <int>``. Anything else raises --
    the lab only uses these two shapes.
    """
    col, val = [t.strip() for t in where.split("=", 1)]
    if val.startswith("'") and val.endswith("'"):
        return E.EqualTo(col, val[1:-1])
    if val.isdigit():
        return E.EqualTo(col, int(val))
    return E.EqualTo(col, val)
