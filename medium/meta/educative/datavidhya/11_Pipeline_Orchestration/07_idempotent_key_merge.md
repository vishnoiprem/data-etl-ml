# Idempotent Key-Based Merge

## Problem
Upsert data into a target table such that re-running the same input does
not duplicate rows.

## How to Think
1. **Stable key** – user_id, event_id, order_id.
2. **MERGE pattern** – match ON key, update vs insert.
3. **Conflict policy** – latest-wins via updated_at.
4. **Streaming** – `foreachBatch` + Delta/Iceberg merge.
5. **Batch** – `MERGE INTO ... USING ... ON key`.

## How to Remember
- **"MERGE ON key for idempotency."**
- **"Re-run same input -> same output."**

## Code (PySpark + Delta)
```python
from delta.tables import DeltaTable
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
target = DeltaTable.forName(spark, "prod.user_dim")

def merge_user_dim(micro_batch_df, batch_id):
    (target.alias("t")
     .merge(micro_batch_df.alias("s"), "t.user_id = s.user_id")
     .whenMatchedUpdateAll()
     .whenNotMatchedInsertAll()
     .execute())

(streaming_df
 .writeStream
 .foreachBatch(merge_user_dim)
 .option("checkpointLocation", "s3://checkpoints/user_dim/")
 .start())
```

## SQL (Iceberg / Hive MERGE)
```sql
MERGE INTO prod.user_dim t
USING staging.user_dim_updates s
   ON t.user_id = s.user_id
WHEN MATCHED AND s.updated_at > t.updated_at THEN
     UPDATE SET full_name = s.full_name,
                email     = s.email,
                updated_at = s.updated_at
WHEN NOT MATCHED THEN
     INSERT (user_id, full_name, email, updated_at)
     VALUES (s.user_id, s.full_name, s.email, s.updated_at);
```

## Common Mistakes
- Using INSERT-only mode on re-runs -> duplicate rows.
- No `updated_at` tie-breaker -> non-deterministic upserts.
- Missing streaming checkpoint -> replayed batches reprocess state.

## AI Use Cases
- Auto-detect natural keys from data lineage.
- Conflict-resolution strategies (latest-wins, source-priority).
- Schema-aware MERGE generation.
