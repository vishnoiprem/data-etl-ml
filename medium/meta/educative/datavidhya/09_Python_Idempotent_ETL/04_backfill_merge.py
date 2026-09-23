"""
Problem 04: Backfill-safe merge: read existing partition, merge new, write
Meta flavor: "We may receive another batch for `dt=2026-01-05` a week later.
Re-running that day's partition must NOT double-count existing rows and must
NOT lose any older rows that arrived first."

How to Think:
- Treat each partition directory as the source of truth. On re-run, read it
  back, dedupe against incoming rows on the same business key, and rewrite the
  whole partition.
- This is "read-modify-write" within a partition. Across partitions, nothing
  touches anything else -- so each partition's idempotency is local.
- Use a temp file + atomic rename to avoid leaving a half-written partition.

How to Remember:
- Partition = transaction boundary. Inside it, last-write-wins by business key.

AI Use Cases
- Per-day event partitions for Meta's offline pipelines (HDFS / S3 prefixes).
- Backfilling ranking model training data when ingestion was delayed.
"""
from __future__ import annotations
from pathlib import Path
import json
import tempfile
import shutil
from typing import Iterable


def _read_existing(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def _atomic_write(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent,
                                    delete=False, suffix=".tmp") as tmp:
        for r in rows:
            tmp.write(json.dumps(r) + "\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)  # atomic on POSIX


def transform(existing_path: Path, new_rows: Iterable[dict],
              key_fields: tuple[str, ...] = ("user_id", "event_id")) -> Path:
    existing = _read_existing(existing_path)
    by_key: dict[tuple, dict] = {}
    for r in existing + list(new_rows):
        k = tuple(r.get(f) for f in key_fields)
        by_key[k] = r  # last write wins on key
    merged = sorted(by_key.values(),
                    key=lambda r: [r.get(f) for f in key_fields])
    out = existing_path.parent / "merged.jsonl"
    _atomic_write(out, merged)
    return out


if __name__ == "__main__":
    p = Path("/tmp/_etl_demo_partition.jsonl")
    if p.exists():
        p.unlink()
    p.write_text('{"user_id":1,"event_id":"e1","v":1}\n'
                 '{"user_id":1,"event_id":"e2","v":2}\n')
    new = [{"user_id": 1, "event_id": "e1", "v": 999},  # update
           {"user_id": 2, "event_id": "e3", "v": 3}]   # insert
    out = transform(p, new)
    print("wrote:", out)
    print(out.read_text())
    # second run with same inputs => same file (idempotent)
    out2 = transform(out, new)
    assert out.read_text() == out2.read_text(), "NOT IDEMPOTENT"
    print("MERGE_IDEMPOTENT_OK")
