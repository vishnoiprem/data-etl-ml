"""Partition writer for the bulk_loader.

A partition writer takes rows and routes them to per-partition
sub-tables, then optionally combines them into a final union
view. The pattern matches the warehouse pattern of "partition
overwrite" for date-partitioned tables.

The three strategies are exposed:

  * ``DatePartitioner``   — partition by date column
  * ``KeyPartitioner``    — partition by a high-cardinality key
  * ``HashPartitioner``   — bucket by hash of a key

Each partitioner has the same interface:
  ``partition_key(row) -> str`` returns the partition name
  ``partition_name(row) -> str`` returns the partition name
  (often derived from the key)

The writer is a thin wrapper over ``bulk_loader`` that creates
per-partition tables and inserts accordingly.

Author: Prem Vishnoi <prem.vishnoi.example.com>
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from typing import Any, Callable, Dict, List, Sequence

from common import QueryRunner

# bulk_loader is loaded by the test runner via the same trick we
# use for the other modules; we just import the function here.
try:
    from .bulk_loader import bulk_load  # type: ignore
except ImportError:  # pragma: no cover - fallback for direct import
    import importlib.util as _ilu
    import sys as _sys
    from pathlib import Path as _Path
    _here = _Path(__file__).resolve().parent
    _spec = _ilu.spec_from_file_location(
        "_data_pipeline_design_loading_bulk_loader", _here / "bulk_loader.py"
    )
    _mod = _ilu.module_from_spec(_spec)
    _sys.modules["_data_pipeline_design_loading_bulk_loader"] = _mod
    _spec.loader.exec_module(_mod)  # type: ignore[union-attr]
    bulk_load = _mod.bulk_load


# ---- partitioners -----------------------------------------------------


def _to_date(v: Any) -> str:
    """Coerce a value to an ISO-8601 date string."""
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, str):
        # Accept either 'YYYY-MM-DD' or full ISO 8601.
        return v[:10]
    raise ValueError(f"cannot derive date from {v!r}")


class DatePartitioner:
    """Partition by a date column. Partition name: ``YYYY-MM-DD``."""

    def __init__(self, date_column: str) -> None:
        self.date_column = date_column

    def partition_name(self, row: Dict[str, Any]) -> str:
        return _to_date(row.get(self.date_column))


class KeyPartitioner:
    """Partition by a high-cardinality key. Partition name: the key."""

    def __init__(self, key_column: str) -> None:
        self.key_column = key_column

    def partition_name(self, row: Dict[str, Any]) -> str:
        v = row.get(self.key_column)
        if v is None:
            raise ValueError(f"missing partition key {self.key_column!r}")
        return str(v)


class HashPartitioner:
    """Bucket by hash of a key. Partition name: ``bucket_NN``."""

    def __init__(self, key_column: str, n_buckets: int = 16) -> None:
        if n_buckets < 1:
            raise ValueError("n_buckets must be >= 1")
        self.key_column = key_column
        self.n_buckets = n_buckets

    def partition_name(self, row: Dict[str, Any]) -> str:
        v = str(row.get(self.key_column, ""))
        h = int(hashlib.sha256(v.encode("utf-8")).hexdigest(), 16)
        return f"bucket_{h % self.n_buckets:02d}"


# ---- the writer -------------------------------------------------------


def partitioned_load(
    q: QueryRunner,
    target: str,
    rows: Sequence[Dict[str, Any]],
    partitioner: Any,
    *,
    source: str = "",
) -> Dict[str, Any]:
    """Bulk-load ``rows`` into per-partition sub-tables of ``target``.

    Returns a dict with the total row count and the per-partition
    counts.

    The pattern:
      1. Group rows by partition name.
      2. For each partition, create a per-partition table
         ``{target}__part_{partition_name}`` and bulk-load.
      3. (Optional) Create a union view that reads from all
         partitions. We skip the view here; the caller can
         ``UNION ALL`` at query time, or replace the target
         with a view in their warehouse.
    """
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        name = partitioner.partition_name(row)
        groups.setdefault(name, []).append(row)

    total = 0
    per_partition: Dict[str, int] = {}
    for part_name, part_rows in groups.items():
        # SQL identifiers can't contain '-' or '.' — replace
        # with '_' for the per-partition table name.
        safe_name = part_name.replace("-", "_").replace(".", "_")
        part_table = f"{target}__part_{safe_name}"
        result = bulk_load(
            q, part_table, part_rows, source=source, create_table=True
        )
        per_partition[part_name] = result["row_count"]
        total += result["row_count"]

    return {
        "target": target,
        "row_count": total,
        "partitions": per_partition,
    }
