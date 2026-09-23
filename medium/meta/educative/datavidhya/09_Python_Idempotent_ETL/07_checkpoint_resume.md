# State checkpoint (save progress, resume on failure)

## Problem
A long-running ETL iterates over thousands of items (ad accounts, files,
URLs). Crashing forces a re-run from the top, wasting hours. Persisting a
small "where am I?" marker after each unit of work lets the next run pick up
where the previous one left off.

## How to Think
1. Define the unit of work. Choose a checkpoint granularity: per item, per
   batch, or per partition.
2. After each unit, atomically write the next checkpoint value to durable
   storage (file, S3, Redis).
3. On startup, read the checkpoint and skip ahead.
4. Each unit must be idempotent on its own: if a crash happens between the
   side effect and the checkpoint write, the unit must be safe to redo.
5. Do NOT checkpoint inside a partially-completed unit. Atomic per unit.

## How to Remember
- **Pattern**: "checkpoint after each safe unit; unit must be idempotent"
- Idempotency = same input -> same output, regardless of run count.
- Checkpoint is a forward marker, not a transaction log.

## Code (Python)
```python
def run_with_checkpoint(items, process, checkpoint_path):
    start = int(checkpoint_path.read_text() or 0) if checkpoint_path.exists() else 0
    for idx, item in enumerate(items):
        if idx < start:
            continue
        process(item)
        tmp = checkpoint_path.with_suffix(".tmp")
        tmp.write_text(str(idx + 1))
        tmp.replace(checkpoint_path)  # atomic
```

## Common Mistakes
- Checkpointing before the work, so a crash leaves you double-processing.
- Using a non-atomic write (no temp + rename) -- the file can end up empty.
- Coupling the checkpoint to a non-idempotent unit -- resumes double-write.
- Forgetting to clear the checkpoint on a manual data reset.

## AI Use Cases
- Long-running Meta Ads data pulls (Insights sync, creative sync).
- Crawling large URL/edge graphs for content features.
- Iterating Spark partitions in driver-side loops for fine-grained control.
