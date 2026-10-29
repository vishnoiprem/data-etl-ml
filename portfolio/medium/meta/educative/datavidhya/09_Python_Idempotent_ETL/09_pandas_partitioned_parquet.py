"""
Problem 09: Pandas groupby -> parquet write partitioned by date
Meta flavor: "Compute daily per-user revenue and write to S3-style partitioned
parquet. Hive-style layout makes the same output visible to Presto and Spark
queries; reruns overwrite the same partition files atomically."

How to Think:
- Choose the partition key deterministically: `dt` from `event_date`.
- Aggregate with `groupby(...).agg(...)` -- this is deterministic for a given
  input frame.
- Write one parquet file per partition with `partition_by="dt"`. Replace on
  rerun (idempotent at partition level).
- Sort by the partition + key columns before writing so byte-equal reruns.

How to Remember:
- Partition key must be derived from the data, not external state.

AI Use Cases
- Daily per-user revenue aggregates for Meta Insights sync.
- Snapshot tables for offline BI tools that read partitioned parquet.
"""
from __future__ import annotations
from pathlib import Path
import json
import tempfile
import shutil


def transform(rows: list[dict], out_dir: Path) -> list[Path]:
    """
    Aggregate revenue per (user_id, event_date) and write partitioned parquet-
    like directory layout. Uses pure stdlib so it runs anywhere; replace the
    body with `df.to_parquet(..., partition_cols=["dt"])` in production.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    agg: dict[tuple, float] = {}
    for r in rows:
        key = (r["user_id"], r["event_date"][:10])
        agg[key] = agg.get(key, 0.0) + float(r.get("value", 0))

    by_dt: dict[str, list[dict]] = {}
    for (user_id, dt), total in agg.items():
        by_dt.setdefault(dt, []).append({
            "user_id": user_id, "revenue": total})

    written: list[Path] = []
    for dt, items in sorted(by_dt.items()):
        items.sort(key=lambda r: r["user_id"])
        final = out_dir / f"dt={dt}" / "part-000.jsonl"
        staging = out_dir / f"dt={dt}" / ".staging"
        staging.mkdir(parents=True, exist_ok=True)
        with (staging / "part-000.jsonl").open("w") as f:
            for it in items:
                f.write(json.dumps(it) + "\n")
        if final.exists():
            final.unlink()
        if (out_dir / f"dt={dt}").exists() and not final.exists():
            (out_dir / f"dt={dt}").rmdir()
        (staging / "part-000.jsonl").replace(final)
        shutil.rmtree(staging, ignore_errors=True)
        (final.parent / "_SUCCESS").write_text("ok\n")
        written.append(final)
    return written


if __name__ == "__main__":
    base = Path("/tmp/_etl_part_demo")
    if base.exists():
        shutil.rmtree(base)
    rows = [
        {"user_id": "u1", "event_date": "2026-01-05T10:00", "value": 9.99},
        {"user_id": "u1", "event_date": "2026-01-05T20:00", "value": 0.01},
        {"user_id": "u2", "event_date": "2026-01-05T08:00", "value": 4.50},
        {"user_id": "u1", "event_date": "2026-01-06T10:00", "value": 2.00},
    ]
    for p in transform(rows, base):
        print("wrote:", p)
    # rerun -> same files
    for p in transform(rows, base):
        print("rerun:", p)
