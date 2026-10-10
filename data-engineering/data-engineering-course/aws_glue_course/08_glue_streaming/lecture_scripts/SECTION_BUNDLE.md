# Section 8 — Glue Streaming (Lectures L60-L70)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> This file bundles 11 lecture scripts (L60-L70) for Section 8. Note: L60 is the role play from Section 11 — included here per the original syllabus.

---

## L60 — Diagnose Glue Job Failure: Role/Trust Misconfig (Role Play) (2:22)

> "This is the first of the 3 role plays. The full script is in `11_role_plays/RP1_trust_misconfig.md`. The scenario: a junior DE has deployed the pipeline stack; the Job fails with `AccessDeniedException` on `sts:AssumeRole`. You (the senior DE) walk the junior through the diagnosis: read the error message, check the trust policy, attach the right trust policy, re-run the Job. The teaching points: trust policy vs identity policy, IaC discipline (fix the template, not the console), and the read-the-error-message habit."

---

## L61 — Section Overview (Streaming) (1:43)

> "Section 8 covers Glue Streaming — running ETL on a stream of records, not a batch. The 3 sources Glue Streaming supports: Kinesis Data Streams, Apache Kafka (including Amazon MSK), and a custom connector (Spark Streaming's generic source). The 2 sink types: S3 (Parquet, JSON, or CSV), and a JDBC database. The 3-Job pattern we'll build: a Python Shell *generator* that writes synthetic events to Kinesis, a *loading* job that reads from Kinesis and writes raw records to S3, and a *transforming* job that reads from Kinesis, applies a transformation, and writes Parquet to S3."

---

## L62 — Getting Ready For Glue Streaming Pipeline (2:05)

> "Pre-flight for the streaming pipeline. 1) Create a Kinesis Data Stream named `glue-course-stream` with 2 shards. 2) Create 3 IAM roles: `GlueGeneratorRole` (Kinesis write), `GlueLoadingRole` (Kinesis read + S3 write), `GlueTransformingRole` (Kinesis read + S3 write). Or use one role with all 3 policies. 3) Verify the source S3 bucket has the `city_temperature.csv` (or, for streaming, a separate synthetic-data script)."

---

## L63 — Deploying Glue Streaming Job Infrastructure (4:04)

> "Deploy the streaming infrastructure. Two options: by hand in the console (create the 3 Jobs one at a time) or via CloudFormation (a single stack). For this course, we deploy by hand to make the resource creation explicit. The 3 Jobs to create: `GlueGeneratorJob` (Python Shell, 1 worker, 0.0625 DPU), `GlueLoadingJob` (Spark Streaming, 2 workers, G.025X), `GlueTransformingJob` (Spark Streaming, 2 workers, G.025X)."

---

## L64 — Lab: Creating Python Shell Glue Job For Stream Generation (2:13)

> "Create the Python Shell job. Glue → Jobs → Add job. Name: `GlueGeneratorJob`. Type: Python Shell. Glue version: 4.0. IAM role: `GlueGeneratorRole`. Script location: `s3://<source-bucket>/scripts/glue_generator.py`. The script (in `downloads/`): `import boto3, json, time, random; kinesis = boto3.client('kinesis'); while True: record = {...}; kinesis.put_record(StreamName='glue-course-stream', Data=json.dumps(record), PartitionKey=str(record['user_id'])); time.sleep(0.1)`. Configure a schedule: every 1 minute via EventBridge."

---

## L65 — Lab: Creating Glue Streaming Loading Job (3:14)

> "Create the loading job. Name: `GlueLoadingJob`. Type: Spark Streaming. Glue version: 4.0. IAM role: `GlueLoadingRole`. Script: `s3://<source-bucket>/scripts/glue_loading_job.py`. The script reads from the Kinesis stream (`glue-course-stream`), parses each record as JSON, and writes the raw JSON to S3 at `s3://<target-bucket>/streaming/raw/`. The job runs continuously (no end condition)."

---

## L66 — Lab: Creating Glue Streaming Transforming Job (3:30)

> "Create the transforming job. Same as L65 but with a transformation: filter to `user_id < 500`, compute a running mean of `avg_temperature` per country, and write Parquet to `s3://<target-bucket>/streaming/transformed/`. The job is stateful — it maintains a per-country mean across the stream. The state is stored in a Spark Structured Streaming state store (backed by S3 or RocksDB)."

---

## L67 — Recap Before Running All Three Glue Streaming Jobs (2:25)

> "Quick recap: 3 Jobs, 1 Kinesis stream, 2 S3 prefixes (raw + transformed). Verify: Kinesis stream is `ACTIVE`; 3 IAM roles exist with the right policies; 3 Jobs are in `READY` state; the generator's schedule is configured. Now run them in order: generator first (wait 30s for records to appear in the stream), then loading + transforming (start them in parallel)."

---

## L68 — Running Glue Streaming Generator Job (1:35)

> "Run the generator. The job is a Python Shell that runs for up to 60 minutes, writes 10 records/sec to the Kinesis stream. To verify: open the Kinesis console, click the stream, watch the `IncomingBytes` and `IncomingRecords` metrics. They should tick up by ~10 records/sec."

---

## L69 — Running Glue Streaming Transformation Job (3:49)

> "Run the transforming job. Glue → Jobs → GlueTransformingJob → Run. The job starts and runs continuously. To verify: open the S3 console, navigate to `s3://<target-bucket>/streaming/transformed/`. New Parquet files appear every ~30 seconds (the micro-batch interval). Each file has 1-2 minutes of data. To check the throughput: CloudWatch → Metrics → Glue → `glue.streaming.numRecordsProcessedPerBatch` and `glue.driver.streaming.batchProcessingTimeInMs`."

---

## L70 — Section Recap (2:25)

> "Section 8 takeaways. One: Glue Streaming runs ETL on a stream of records, not a batch. Two: the 3 sources are Kinesis, Kafka (MSK), and a custom connector. Three: the 3-Job pattern (generator + loading + transforming) is the canonical streaming pipeline. Four: the 3 CloudWatch metrics that matter are `numRecordsProcessedPerBatch`, `batchProcessingTimeInMs`, and `iteratorAge` (the age of the oldest unprocessed record). Five: the streaming job's state can be checkpointed to S3 or DynamoDB for exactly-once semantics."

---

## Section 8 Quiz

5 questions, see `quizzes/section_8.md`.
