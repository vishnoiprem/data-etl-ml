# Assignment 04 — Glue Streaming Pipeline

> **Section:** 8 (Glue streaming)
> **Due:** End of week 4
> **Deliverable:** A working streaming pipeline: generator → Kinesis → loading job → transforming job → S3, with the transforming job running in real time.

## Objective

Build the full streaming pipeline (3 Glue Jobs):
1. **Generator job** (Python Shell) — writes synthetic records to a Kinesis stream.
2. **Loading job** (Glue Streaming) — reads from Kinesis, writes raw records to S3.
3. **Transforming job** (Glue Streaming) — reads from Kinesis, applies a transformation, writes to S3.

The deliverable proves you can:
- Use Python Shell jobs to write to Kinesis.
- Use Glue Streaming jobs to read from Kinesis, transform, and write to S3.
- Wire all 3 jobs together via Triggers or a schedule.

## Steps

1. **Create a Kinesis Data Stream** named `glue-course-stream` with 2 shards.
2. **Create 3 IAM roles** (or one role with all 3 policies):
   - `GlueGeneratorRole` — `kinesis:PutRecord` on the stream.
   - `GlueLoadingRole` — `kinesis:Get*` + `s3:PutObject` on the target.
   - `GlueTransformingRole` — `kinesis:Get*` + `s3:PutObject` on the target.
3. **Create the Generator Job** — a Python Shell job that writes 10 records/sec to the stream:
   ```python
   import boto3, json, time, random
   kinesis = boto3.client("kinesis", region_name="us-east-1")
   while True:
       record = {"user_id": random.randint(1, 1000), "event": "click", "ts": time.time()}
       kinesis.put_record(StreamName="glue-course-stream",
                          Data=json.dumps(record),
                          PartitionKey=str(record["user_id"]))
       time.sleep(0.1)
   ```
4. **Create the Loading Job** — reads from the stream, writes raw JSON to S3.
5. **Create the Transforming Job** — reads from the stream, applies a transformation (e.g., filter to `user_id < 500`), writes Parquet to S3.
6. **Run the Generator on a schedule** (every 1 min via EventBridge).
7. **Start the Loading and Transforming Jobs** — they should run continuously.

## Acceptance criteria

- Kinesis stream shows `IncomingBytes > 0` and `IncomingRecords > 0`.
- Loading job's S3 output prefix has new JSON files every 30 seconds.
- Transforming job's S3 output prefix has new Parquet files every 30 seconds.
- The transforming job's output has only `user_id < 500` records (the filter is applied).

## Stretch (optional, 1 hour)

- Add a Glue Data Quality rule on the transforming job's output: `IsComplete "user_id"`.
- Add a CloudWatch alarm on the job's `batchProcessingTimeInMs > 60000` (60s).
- Run `aws kinesis describe-stream-summary` to check the iterator age; verify it's < 1 minute (the job is keeping up).
