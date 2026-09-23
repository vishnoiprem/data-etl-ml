# Pandas groupby -> parquet write partitioned by date

## Problem
Compute a daily aggregate (e.g. revenue per user) and write it to disk in a
partitioned, query-friendly layout. Re-running the job must overwrite the
same partitions deterministically -- not duplicate them, not drift them.

## How to Think
1. Pick the partition column from the data (e.g. `dt` from `event_date`).
2. Group + aggregate deterministically. `groupby().agg()` is a pure function
   of the input frame.
3. Sort the frame by the partition key and any tie-breaker keys. Parquet
   blocks become byte-stable.
4. Write one parquet file per partition with `df.to_parquet(..., partition_cols=["dt"])`.
   On rerun, each partition file is replaced in place (idempotent at file
   scope).
5. Combine with `_SUCCESS` markers and atomic renames for full hive-like
   semantics.

## How to Remember
- **Pattern**: "groupby on business keys, partition by date, write parquet"
- Idempotency = same input -> same output, regardless of run count.
- Sort before you write. The byte-stable result makes diffing reruns trivial.

## Code (Python)
```python
import pandas as pd

def run(rows, out_dir):
    df = pd.DataFrame(rows)
    df["dt"] = pd.to_datetime(df["event_date"]).dt.strftime("%Y-%m-%d")
    agg = (df.groupby(["dt", "user_id"], as_index=False)["value"]
             .sum().rename(columns={"value": "revenue"}))
    agg = agg.sort_values(["dt", "user_id"])  # deterministic byte layout
    agg.to_parquet(out_dir, partition_cols=["dt"], index=False)
```

## Common Mistakes
- Forgetting to sort before writing -- parquet block ordering varies by
  groupby hash.
- Picking a partition column with high cardinality (e.g. `user_id`) and
  creating thousands of tiny files.
- Writing multiple files per partition without deterministic naming; reruns
  create `part-000`, `part-001`, ... drift.
- Including unstable fields (`ingest_ts`) in the sort key.

## AI Use Cases
- Daily per-user revenue aggregates for Meta Insights sync.
- Snapshot tables for offline BI tools reading partitioned parquet.
- Feature-store snapshots for ranking/recommendation models.
