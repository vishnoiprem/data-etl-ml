# Section 11 Quiz — Snowpipe

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** Which Snowflake object is the unit of configuration for
auto-ingest Snowpipe?

- A. A scheduled Task
- B. A pipe
- C. A stage
- D. A stream

<details><summary>Show answer</summary>

**B — A pipe.** A pipe wraps a `COPY INTO` statement, points at
a stage, and (with `AUTO_INGEST = TRUE`) subscribes to cloud
events for that stage.

</details>

---

**Q2.** What does the `AUTO_INGEST = TRUE` flag on a pipe do?

- A. Tells Snowflake to use a managed warehouse to scan the
  bucket on a schedule
- B. Provisions a managed event channel (SQS / Pub/Sub / Event
  Grid) and wires the pipe to it
- C. Enables `COPY INTO` to retry automatically on transient
  errors
- D. Triggers `MERGE` whenever a new file lands

<details><summary>Show answer</summary>

**B — Provisions a managed event channel.** Snowflake creates
the SQS queue (S3), Pub/Sub topic (GCS), or Event Grid
subscription (Azure) for you, and `DESC PIPE` exposes the
channel name you wire to the cloud side.

</details>

---

**Q3.** Which command unloads a query result to a stage?

- A. `EXPORT TABLE <t> TO @<stage>/path`
- B. `COPY INTO @<stage>/path FROM (<query>)`
- C. `UNLOAD INTO @<stage>/path (<query>)`
- D. `INSERT INTO @<stage>/path SELECT ...`

<details><summary>Show answer</summary>

**B — `COPY INTO @<stage>/path FROM (<query>)`.** Same command
family as the loader, opposite direction. The `FROM (<query>)`
form is the source.

</details>

---

**Q4.** Which option on `COPY INTO ... LOCATION=` produces a
hive-style directory tree like `year=2024/month=01/`?

- A. `OVERWRITE = TRUE`
- B. `HEADER = TRUE`
- C. `PARTITION BY '<expr>'`
- D. `INCLUDE_QUERY_ID = TRUE`

<details><summary>Show answer</summary>

**C — `PARTITION BY '<expr>'`.** The expression becomes a
directory prefix per row group; downstream engines (Spark,
BigQuery, Athena) read it natively.

</details>

---

**Q5.** Which `LIST` command confirms a stage is wired up
correctly *before* you create a pipe?

- A. `LIST STAGES;`
- B. `LIST @<stage_name>;`
- C. `SHOW TABLES;`
- D. `SHOW INTEGRATIONS;`

<details><summary>Show answer</summary>

**B — `LIST @<stage_name>;`.** Returns one row per file the
service account / principal can see. Zero rows = bucket, IAM, or
prefix misconfiguration.

</details>

---

**Q6.** On GCS, which event type does a Snowpipe subscribe to in
the bucket notification?

- A. `OBJECT_DELETE`
- B. `OBJECT_FINALIZE`
- C. `OBJECT_ARCHIVE`
- D. `OBJECT_MOVE`

<details><summary>Show answer</summary>

**B — `OBJECT_FINALIZE`.** Fires when a write to the bucket
closes. This is the canonical "new file available" signal.

</details>

---

**Q7.** How does Snowpipe's pricing model differ from batch
`COPY INTO`?

- A. Snowpipe charges per file loaded; batch `COPY INTO`
  charges per warehouse-second
- B. Snowpipe charges per row; batch charges per file
- C. Snowpipe is free; batch is paid
- D. Both are billed the same way

<details><summary>Show answer</summary>

**A — Per file vs per warehouse-second.** Snowpipe is
serverless (Snowflake-managed compute) and bills per file
loaded. Batch `COPY INTO` runs on a warehouse you size and
suspend yourself, billed per second the warehouse is active.

</details>

---

**Q8.** Which pipe command re-scans the stage for files the pipe
should have loaded (e.g. after a missed notification)?

- A. `ALTER PIPE <p> RESUME;`
- B. `ALTER PIPE <p> REFRESH;`
- C. `ALTER PIPE <p> RETRY;`
- D. `ALTER PIPE <p> RESCAN;`

<details><summary>Show answer</summary>

**B — `ALTER PIPE <p> REFRESH;`.** Snowflake re-runs the
materialization query against the stage and loads any file
still within the file retention window that the pipe missed.

</details>

---

**Q9.** In `CREATE PIPE ... AS COPY INTO ...`, the pipe stores:

- A. A reference to the source file's content
- B. The `COPY INTO` statement itself
- C. A materialized view of the loaded rows
- D. The schema of the target table

<details><summary>Show answer</summary>

**B — The `COPY INTO` statement itself.** `DESC PIPE` shows
you the stored statement. Change the pipe, and you change what
runs on each event.

</details>

---

**Q10.** Which view shows you per-file load history for a
specific pipe?

- A. `PIPE_USAGE_HISTORY` in `INFORMATION_SCHEMA`
- B. `COPY_HISTORY` (filtered by pipe)
- C. `QUERY_HISTORY`
- D. `TASK_HISTORY`

<details><summary>Show answer</summary>

**A — `PIPE_USAGE_HISTORY`.** One row per file the pipe
attempted to load, with `file_name`, `status`, `row_count`,
`first_error_message`, and `last_loaded_time`. `COPY_HISTORY`
shows the underlying load history but isn't pipe-scoped.

</details>
