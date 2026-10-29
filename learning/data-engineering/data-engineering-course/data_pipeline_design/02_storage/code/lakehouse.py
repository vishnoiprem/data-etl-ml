"""Data lakehouse: a tiny reference implementation of the bronze/silver/gold
three-layer pattern.

This module backs Lesson 08 (`design/08_data_lakehouse_design.md`).
The full iceberg/delta/snowflake story is well beyond a single
file, but the *layered* pattern — bronze = raw, silver =
deduplicated + schema-conformed, gold = business-aggregated —
is small enough to demonstrate end-to-end.

The point of the implementation is to make the
*interview answer* concrete: "I would partition by date, store
in columnar Parquet, deduplicate by primary key in the silver
layer, and aggregate in the gold layer." Each of those moves
is a one-line method here.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Record:
    """A single row flowing through the lakehouse layers."""

    data: Dict[str, Any]
    # The ingest time, used to decide which row wins on dedup
    # in the silver layer.
    ingested_at: float = field(default_factory=time.time)

    def key(self, key_fields: List[str]) -> str:
        return "|".join(str(self.data.get(k, "")) for k in key_fields)


@dataclass
class BronzeLayer:
    """The raw layer. Stores events as they arrive, no schema enforcement."""

    storage: List[Record] = field(default_factory=list)

    def ingest(self, record: Record) -> None:
        self.storage.append(record)

    def __len__(self) -> int:
        return len(self.storage)


@dataclass
class SilverLayer:
    """The conformed layer. Deduplicates by ``key_fields``, keeps the latest."""

    key_fields: List[str]
    storage: Dict[str, Record] = field(default_factory=dict)

    def conform(self, record: Record) -> None:
        k = record.key(self.key_fields)
        existing = self.storage.get(k)
        if existing is None or record.ingested_at > existing.ingested_at:
            self.storage[k] = record

    def __len__(self) -> int:
        return len(self.storage)


@dataclass
class GoldLayer:
    """The aggregated layer. One row per (group_by, agg) tuple."""

    storage: List[Dict[str, Any]] = field(default_factory=list)

    def aggregate(
        self,
        rows: List[Record],
        group_by: List[str],
        measure: str,
        agg: str = "sum",
    ) -> None:
        """Group by ``group_by`` and apply ``agg`` to ``measure``."""
        groups: Dict[tuple, List[float]] = {}
        for r in rows:
            tup = tuple(r.data.get(c) for c in group_by)
            v = r.data.get(measure)
            if v is None:
                continue
            try:
                groups.setdefault(tup, []).append(float(v))
            except (TypeError, ValueError):
                continue
        out: List[Dict[str, Any]] = []
        for tup, vals in groups.items():
            if agg == "sum":
                value = sum(vals)
            elif agg == "avg":
                value = sum(vals) / len(vals) if vals else 0.0
            elif agg == "count":
                value = len(vals)
            elif agg == "max":
                value = max(vals)
            elif agg == "min":
                value = min(vals)
            else:
                raise ValueError(f"unsupported agg: {agg}")
            out.append({**dict(zip(group_by, tup)), measure: value})
        self.storage = out

    def __len__(self) -> int:
        return len(self.storage)


@dataclass
class Lakehouse:
    """The end-to-end three-layer pipeline.

    >>> lh = Lakehouse(key_fields=["order_id"])
    >>> lh.bronze.ingest(Record({"order_id": 1, "amount": 100}))
    >>> lh.bronze.ingest(Record({"order_id": 1, "amount": 110}))  # late event
    >>> lh.promote()
    >>> lh.gold.aggregate(list(lh.silver.storage.values()),
    ...                   group_by=["order_id"], measure="amount", agg="sum")
    >>> len(lh.gold)
    1
    """

    key_fields: List[str] = field(default_factory=lambda: ["id"])
    bronze: BronzeLayer = field(default_factory=BronzeLayer)
    silver: SilverLayer = None  # type: ignore
    gold: GoldLayer = field(default_factory=GoldLayer)

    def __post_init__(self) -> None:
        if self.silver is None:
            self.silver = SilverLayer(key_fields=self.key_fields)

    def ingest(self, data: Dict[str, Any]) -> None:
        """Ingest one record into the bronze layer."""
        self.bronze.ingest(Record(data=data))

    def promote(self) -> None:
        """Bronze -> silver. Deduplicate by ``key_fields``."""
        for r in self.bronze.storage:
            self.silver.conform(r)

    def partition_path(self, layer: str, partition_key: str, value: str) -> str:
        """Hive-style partition path: ``layer/key=value/...``."""
        return f"{layer}/{partition_key}={value}/"


if __name__ == "__main__":
    # Tiny end-to-end demo.
    lh = Lakehouse(key_fields=["order_id"])
    lh.ingest({"order_id": 1, "customer_id": 100, "amount": 50.0})
    lh.ingest({"order_id": 2, "customer_id": 100, "amount": 75.0})
    lh.ingest({"order_id": 1, "customer_id": 100, "amount": 60.0})  # late
    lh.promote()
    rows = list(lh.silver.storage.values())
    lh.gold.aggregate(rows, group_by=["customer_id"], measure="amount", agg="sum")
    print(f"bronze={len(lh.bronze)} silver={len(lh.silver)} gold={len(lh.gold)}")
    print(f"gold[0] = {lh.gold.storage[0]}")
