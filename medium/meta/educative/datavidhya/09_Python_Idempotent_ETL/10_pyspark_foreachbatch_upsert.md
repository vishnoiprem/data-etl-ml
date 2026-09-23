# PySpark foreachBatch upsert into Delta/Iceberg table

## Problem
A streaming pipeline (Kafka -> Spark Structured Streaming) must land each
event into a Delta or Iceberg table keyed by `(user_id, event_id)`. Micro-batches
overlap on retries and replays; the sink must dedupe via MERGE so that any
given batch, replayed N times, leaves the table in the same state.

## How to Think
1. Use `foreachBatch` to wrap each micro-batch in a Python function.
2. Inside the function, dedup the batch itself (last-write-wins on a tie-breaker
   like `ts`).
3. Issue a `MERGE INTO target USING source ON (...)` (Delta) or
   `upsert` (Iceberg) keyed on the business identity.
4. Pick a stable trigger: `availableNow` for replays, `processingTime` for live
   streams.
5. Treat each micro-batch as the unit of idempotency; the table itself is just
   the merge target.

## How to Remember
- **Pattern**: "foreachBatch + MERGE on business key"
- Idempotency = same input -> same output, regardless of run count.
- Dedup twice: inside the batch and again in the merge.

## Code (PySpark)
```python
def upsert_to_delta(batch_df, batch_id):
    from delta.tables import DeltaTable
    dt = DeltaTable.forName(spark, "conversions")
    (dt.alias("t")
      .merge(batch_df.alias("s"),
             "t.user_id = s.user_id AND t.event_id = s.event_id")
      .whenMatchedUpdateAll()
      .whenNotMatchedInsertAll()
      .execute())

stream.writeStream.foreachBatch(upsert_to_delta) \
    .option("checkpointLocation", "s3://.../chk") \
    .trigger(availableNow=True) \
    .start()
```

## Common Mistakes
- Using `append` mode -- retries create duplicates.
- Keying the merge on `event_date` instead of `(user_id, event_id)` -- two
  events for the same user get merged into one row.
- Forgetting `checkpointLocation` -- restart replays every batch from scratch
  with no dedup.
- Skipping intra-batch dedup -- the merge runs once per row, slowing the job.

## AI Use Cases
- Streaming Meta ad conversions into a Delta table for near-real-time
  dashboards.
- Online feature-store writes from a Kafka stream with replay-safe semantics.
- Joining click stream + action stream into a single fact table.
