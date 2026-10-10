# Section 8 Quiz — Glue Streaming

> 5 questions, multi-choice, single answer. The answer key is at the bottom.

---

**Q1.** Which AWS service is the most common source of a Glue Streaming ETL job?

- A. S3 PUT events
- B. Kinesis Data Streams
- C. Amazon MSK (Kafka)
- D. Both B and C

---

**Q2.** A Glue Streaming job reads from a Kinesis stream with 10 shards. The job is configured with `NumberOfWorkers=5`. What is the effective parallelism?

- A. 5 (limited by the workers)
- B. 10 (limited by the shards)
- C. 50 (5 workers × 10 shards)
- D. 1 (Kinesis shards cannot be parallelized)

---

**Q3.** A Glue Streaming job's `batchProcessingTimeInMs` p99 is 4 minutes, up from 30 seconds 2 weeks ago. The `numRecordsProcessedPerBatch` is also up 3x. What is the most likely cause?

- A. The job is failing
- B. Upstream traffic increase — the job is keeping up but processing more data
- C. Worker count is too low
- D. Kinesis is throttling

---

**Q4.** A Glue Streaming job uses a Python Shell job to generate synthetic data and write it to Kinesis. The job runs once and exits. What is the most likely issue?

- A. The Python Shell job is not configured to run on a schedule
- B. Python Shell jobs cannot write to Kinesis
- C. The IAM role is wrong
- D. The script is buggy

---

**Q5.** A Glue Streaming job reads from Kinesis, transforms, and writes to S3. The S3 output is missing some recent records. What is the most likely cause?

- A. The job is not checkpointing
- B. The S3 bucket policy is wrong
- C. The IAM role is wrong
- D. The Glue version is too old

---

# Answer Key

1. **D** — Both B and C. Glue Streaming supports Kinesis Data Streams and Kafka (including MSK) as sources. (Direct S3 PUT events are processed differently — typically via EventBridge → Glue Job, not a streaming ETL job.)
2. **B** — 10. The parallelism is the minimum of workers and shards. With 10 shards and 5 workers, each worker processes 2 shards. To increase parallelism beyond 10, you must re-shard the Kinesis stream.
3. **B** — Upstream traffic increase. If both metrics are up proportionally, the job is processing more data per batch; the question is whether the rate of *drain* is keeping up. If `batchProcessingTimeInMs` is also up 3x, the job is keeping up. If it's up 12x, the job is falling behind.
4. **A** — Schedule. Python Shell jobs can write to Kinesis, but a one-shot job exits. To generate a *stream* of data, the job must run on a schedule (e.g., every 1 minute via EventBridge schedule or Glue Trigger).
5. **A** — Not checkpointing. Glue Streaming uses checkpoints (stored in S3 or DynamoDB) to track which records have been processed. Without checkpointing, a job restart re-reads from the beginning, but in-flight records are lost.
