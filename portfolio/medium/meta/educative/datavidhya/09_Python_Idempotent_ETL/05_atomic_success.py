"""
Problem 05: Idempotent file write with _SUCCESS marker + temp atomic rename
Meta flavor: "Downstream consumers (Hive, Spark) read partitions only if a
`_SUCCESS` marker exists. If a job dies mid-write, downstream must keep
serving the previous good partition. Atomicity around the marker is the
contract."

How to Think:
- Two-phase commit on a directory:
  (1) write all data files into a staging path
  (2) on full success, rename staging -> final and drop `_SUCCESS`
- A `_SUCCESS` marker is the visible "I am done" signal. Without it, downstream
  assumes the partition is incomplete.
- Atomic rename is the only way to make the final state all-or-nothing on POSIX.

How to Remember:
- Atomic rename = the unit of success for batch jobs.

AI Use Cases
- Publishing daily aggregates into Hive-style partition directories at Meta.
- Snapshotting ad-account reports for downstream BI dashboards.
"""
from __future__ import annotations
from pathlib import Path
import json
import os
import tempfile
from typing import Iterable


def write_partition(final_dir: Path, rows: Iterable[dict],
                    name: str = "part-00000.jsonl") -> Path:
    final_dir.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".staging_", dir=final_dir.parent))
    try:
        # Phase 1: write data into staging only.
        data_file = staging / name
        with data_file.open("w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        # Phase 2: drop _SUCCESS marker in staging.
        (staging / "_SUCCESS").write_text("ok\n")
        # Atomic: rename staging -> final. Replace if prior attempt left one.
        if final_dir.exists():
            # remove then rename for cross-fs portability
            backup = final_dir.with_suffix(final_dir.suffix + ".old")
            if backup.exists():
                shutil.rmtree(backup)
            os.rename(final_dir, backup)
        os.rename(staging, final_dir)
        return final_dir
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


if __name__ == "__main__":
    import shutil
    base = Path("/tmp/_etl_atomic_demo")
    if base.exists():
        shutil.rmtree(base)
    target = base / "dt=2026-01-05"
    rows = [{"user_id": i, "v": i * 10} for i in range(3)]
    print("wrote:", write_partition(target, rows))
    for p in sorted(target.iterdir()):
        print(" ", p.name, "->", p.read_text()[:40])
    print("SUCCESS_PRESENT:", (target / "_SUCCESS").exists())
