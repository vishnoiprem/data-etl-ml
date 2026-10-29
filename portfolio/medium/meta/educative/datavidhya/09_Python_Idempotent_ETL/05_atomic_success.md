# Idempotent file write with _SUCCESS marker + temp atomic rename

## Problem
A batch job must publish a partition of files so that downstream consumers
(e.g. Hive, Spark, BigQuery external tables) only see a consistent snapshot.
A crash mid-write must NOT leave half-written files visible to readers. The
`_SUCCESS` marker is the "I'm done" signal.

## How to Think
1. Write all data files into a staging directory.
2. Drop a `_SUCCESS` marker in the same staging directory.
3. Atomically rename the staging directory onto the final path.
4. If anything in step 1 or 2 fails, clean up the staging directory; the final
   path is untouched and continues to point at the previous good partition.
5. Re-running the job is safe: it overwrites the final path atomically.

## How to Remember
- **Pattern**: "stage -> success marker -> atomic rename"
- Idempotency = same input -> same output, regardless of run count.
- `_SUCCESS` is published LAST. Its presence == the whole partition is done.

## Code (Python)
```python
def write_partition(final_dir, rows):
    staging = Path(tempfile.mkdtemp(prefix=".staging_", dir=final_dir.parent))
    try:
        with (staging / "part-00000.jsonl").open("w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        (staging / "_SUCCESS").write_text("ok\n")
        os.rename(staging, final_dir)  # atomic on POSIX
        return final_dir
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
```

## Common Mistakes
- Writing `_SUCCESS` first -- readers pick up partial data files.
- Renaming each file individually -- half the rename can succeed.
- Skipping the temp directory and writing directly to the final path.
- Not handling "previous partition exists" -- first rename can fail or leave
  two competing versions.

## AI Use Cases
- Publishing daily aggregates into Hive-style partition directories at Meta.
- Snapshotting ad-account reports for downstream BI dashboards.
- Producing training-set shards for ranking models in a way that is safe for
  parallel readers.
