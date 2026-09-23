# Backfill-safe merge: read existing partition, merge new, write

## Problem
A partition (e.g. `dt=2026-01-05`) may have been written once with some rows,
and later you receive additional rows for the same day. Re-running the merge
must (1) keep all old rows that are not superseded, (2) overwrite duplicates
on the business key with the newer values, (3) produce a byte-identical file
on rerun with no new rows.

## How to Think
1. Read existing partition rows from disk.
2. Combine with the incoming rows in memory.
3. Reduce by business key, last write wins.
4. Write the result back atomically (temp + rename).
5. Sort deterministically so reruns are byte-equal even if input order varied.

## How to Remember
- **Pattern**: "read-modify-write by key, atomic replace"
- Idempotency = same input -> same output, regardless of run count.
- The partition is your transactional unit; do not cross partition boundaries.

## Code (Python)
```python
def merge(existing_path, new_rows, key_fields=("user_id", "event_id")):
    existing = read_jsonl(existing_path) if existing_path.exists() else []
    by_key = {}
    for r in existing + list(new_rows):
        k = tuple(r[f] for f in key_fields)
        by_key[k] = r  # last write wins
    sorted_rows = sorted(by_key.values(),
                         key=lambda r: [r[f] for f in key_fields])
    write_atomic(existing_path, sorted_rows)
```

## Common Mistakes
- Appending without deduping: duplicate rows accumulate on each rerun.
- Updating in place without atomic rename: a crashed run leaves a partial file.
- Using `ts` or `ingest_ts` in the key; keys must be identity, not arrival.
- Mixing partitions in one merge (writes cross-contaminate other days).

## AI Use Cases
- Daily event partitions for Meta's ad-measurement offline pipelines.
- Backfilling or "catching up" ranking model training datasets.
- Reconciling second-source sync logs into the same daily partition.
