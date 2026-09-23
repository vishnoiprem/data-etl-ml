"""
Problem 07: Idempotent key-based merge.

Meta flavor: UPSERT pattern - re-running the same partition must not
duplicate rows. Show the SQL MERGE / Delta / Iceberg pattern.

How to Think:
- Use a stable business key (e.g., user_id, event_id).
- MERGE INTO target USING source ON key.
- WHEN MATCHED THEN UPDATE; WHEN NOT MATCHED THEN INSERT.
- In Spark: foreachBatch + Delta `merge`.

How to Remember:
- "MERGE ON key for idempotency."
- "Re-run same input -> same output."

AI Use Cases:
- Auto-detect natural keys from data lineage.
- Conflict-resolution strategies (latest-wins, source-priority).
- Schema-aware MERGE generation.
"""
# PySpark + Delta Lake
from delta.tables import DeltaTable
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

target = DeltaTable.forName(spark, "prod.user_dim")

def merge_user_dim(micro_batch_df, batch_id):
    """foreachBatch entry point for streaming UPSERT."""
    (target.alias("t")
     .merge(micro_batch_df.alias("s"),
            "t.user_id = s.user_id")
     .whenMatchedUpdateAll()       # overwrite all cols
     .whenNotMatchedInsertAll()
     .execute())

# Streaming
(streaming_df
 .writeStream
 .foreachBatch(merge_user_dim)
 .option("checkpointLocation", "s3://checkpoints/user_dim/")
 .start())

# Batch equivalent (Presto on Hive / Iceberg)
SQL_MERGE = """
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
"""
