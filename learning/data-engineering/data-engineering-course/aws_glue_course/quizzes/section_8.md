# Section 8 Quiz — Glue Streaming

> 5 questions, multi-choice, single answer. The answer key is at the bottom.

---

**Q1.** Which of the following are supported streaming sources for an AWS Glue Spark Streaming Job?

- A. Amazon Kinesis Data Streams only
- B. Amazon S3 PUT events (S3 Event Notifications)
- C. Amazon MSK (managed Apache Kafka) only
- D. Both Kinesis Data Streams and Amazon MSK (incl. self-managed Kafka)

---

**Q2.** Your Kinesis Data Stream has **10 shards** and your Glue Streaming Job is configured with **`NumberOfWorkers = 5`**. What is the effective parallelism, and how do you increase it?

- A. Parallelism is 5 (limited by workers). Resize the Job to more workers.
- B. Parallelism is 10 (limited by shards). To increase parallelism, re-shard (split) the stream.
- C. Parallelism is 50 (workers × shards). To increase it, add more workers.
- D. Parallelism is 15 (workers + shards). To increase it, add a DPU.

---

**Q3.** You monitor the Job's **p99 `batchProcessingTimeInMs`** in CloudWatch. Last week it averaged ~30 seconds; this week it averages **4 minutes (~8x higher)**. At the same time, **`numRecordsProcessedPerBatch` is only ~3x higher** than last week. What does this most likely indicate?

- A. The Job is keeping up — more upstream traffic, same per-record cost.
- B. The Job is falling behind — per-record latency has degraded ~3x and the Job will soon backpressure the stream.
- C. The Kinesis shard limit was reached; the Job is throwing `ProvisionedThroughputExceededException`.
- D. S3 write throughput is the bottleneck; switch the output format from Parquet to JSON.

---

**Q4.** You built a **Python Shell Job** (`glue_python_shell`) that synthesizes records and uses the Kinesis `PutRecord` API to push them into the stream. When you test the Job, it runs once, exits successfully, and the downstream Spark Streaming Glue Job stops receiving new data shortly after. What is the fix?

- A. Set the Job's `--job-language` to `scala` so it stays resident.
- B. Increase the Python Shell Job's `Max Capacity` (DPUs) so it doesn't terminate.
- C. Schedule the Python Shell Job to run on a recurring basis (e.g. an EventBridge schedule every 1 minute, or a Glue Trigger) so records are continuously produced.
- D. Move the generator logic into the Spark Streaming Job itself using `foreachBatch`.

---

**Q5.** After a planned restart of the Spark Streaming Glue Job, you notice that the most recent **~2 minutes of records are missing** from the Parquet output in S3, and on the next start the Job appears to re-read older Kinesis records. Which property is most likely misconfigured?

- A. `NumberOfWorkers` — set too low, so the Job cannot keep up.
- B. The S3 output path's partitioning (`partitionBy`) — records were written to a date prefix the consumer isn't reading.
- C. The streaming Job's `checkpointLocation` (or `jobBookmarkOn`) / checkpoint table — without checkpoints the Job can't resume from the last committed sequence number.
- D. The Kinesis stream's retention period — set to 24 hours instead of 7 days.

---

# Answer Key

1. **D** — Both Kinesis Data Streams and Amazon MSK (including self-managed Kafka) are supported streaming sources for Glue Spark Streaming Jobs. S3 PUT events are *not* a streaming source — they're a trigger pattern that fires on object creation, not a continuous record stream.

2. **B** — Parallelism is `min(NumberOfWorkers, Kinesis shards)` = `min(5, 10)` = **10**. The Kinesis shard count is the upper bound; a worker can consume multiple shards but a shard cannot be split across workers. To increase parallelism you must **re-shard (split) the stream** — adding more workers beyond the shard count gives no benefit until the stream also grows.

3. **A** — The Job is keeping up. `batchProcessingTimeInMs` is a p99 latency metric, and `numRecordsProcessedPerBatch` is up ~3x while per-batch time is up ~8x — both grew roughly in proportion, meaning per-record latency is roughly unchanged and the Job is simply processing more records per micro-batch. The textbook rule of thumb: if both metrics grow by the same factor (e.g. both ~3x), the Job is healthy.

4. **C** — A Python Shell Job runs to completion and then exits — it is **not a long-running process**. Once it terminates, no more synthetic records are written to Kinesis and the stream effectively "stops." The fix is to schedule the generator on a recurring cadence (EventBridge schedule every 1 minute, or a Glue Trigger) so it keeps producing records while the Spark Streaming Job consumes them.

5. **C** — Without **checkpoints** (stored in S3 or DynamoDB), the streaming Job cannot remember its last-committed Kinesis sequence number. On restart it re-seeks from the stream's beginning (or from `TRIM_HORIZON`) and any records that were in-flight in the previous micro-batch are lost — that's exactly the symptom described (recent ~2 minutes missing, older records re-read). The misconfigured property is the **`checkpointLocation`** / checkpoint table / `jobBookmarkOn` setting.
