# Section 20a Quiz — Tasks + Streams (L136–L154)

> 12 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Scope:** L136–L154 (Tasks + Streams)

---

**Q1.** What is a Snowflake task?

- A. A scheduled SQL statement that runs inside Snowflake
- B. A third-party scheduler like Airflow
- C. A Snowpipe trigger
- D. A `CREATE TASK` is a stored procedure

<details><summary>Show answer</summary>

**A — A scheduled SQL statement that runs inside Snowflake.**
Tasks are managed by Snowflake; no external scheduler.

</details>

---

**Q2.** Tasks are created in which state by default?

- A. Running
- B. Suspended
- C. Failed
- D. Pending

<details><summary>Show answer</summary>

**B — Suspended.** You must `ALTER TASK ... RESUME` to start it.

</details>

---

**Q3.** Which clause makes a child task depend on a predecessor?

- A. `AFTER`
- B. `BEFORE`
- C. `WHEN`
- D. `SCHEDULE`

<details><summary>Show answer</summary>

**A — `AFTER`.** The child task waits for the predecessor to
succeed before running.

</details>

---

**Q4.** In what order should you resume a 3-task chain?

- A. Top-down (root first)
- B. Bottom-up (leaves first)
- C. Alphabetical
- D. Order does not matter

<details><summary>Show answer</summary>

**B — Bottom-up.** Snowflake rejects resuming a child whose
parent is still suspended.

</details>

---

**Q5.** A task body must be:

- A. A single SQL statement
- B. A stored procedure
- C. A JavaScript function
- D. A Python file

<details><summary>Show answer</summary>

**A — A single SQL statement.** For multi-statement logic,
wrap in a stored procedure and `CALL` it from the task.

</details>

---

**Q6.** What does a stream track?

- A. Real-time streaming data from Kafka
- B. Row-level changes (CDC) to a table
- C. Snowpipe events
- D. `INSERT` statements only

<details><summary>Show answer</summary>

**B — Row-level changes (CDC) to a table.** A stream records
the `INSERT`, `UPDATE`, and `DELETE` operations on the source.

</details>

---

**Q7.** Which metadata column identifies a row as a "real"
insert (not the new image of an update)?

- A. `METADATA$ACTION = 'INSERT'` and `METADATA$ISUPDATE = FALSE`
- B. `METADATA$ISINSERT = TRUE`
- C. `METADATA$ROW_ID = 0`
- D. `METADATA$ACTION = 'NEW'`

<details><summary>Show answer</summary>

**A — `ACTION = 'INSERT' AND ISUPDATE = FALSE`.** The
`ISUPDATE` flag distinguishes fresh inserts from the new
image of an update.

</details>

---

**Q8.** What does a stream's offset do?

- A. Orders updates by timestamp
- B. Records the order in which changes were captured
- C. Specifies the retention period
- D. Names the stream

<details><summary>Show answer</summary>

**B — Records the order in which changes were captured.** The
offset is a 64-bit integer, monotonically increasing per stream.

</details>

---

**Q9.** When does a stream become "stale"?

- A. After 7 days
- B. When its offset is older than the source table's Time Travel
  retention
- C. When the consumer task stops
- D. Never; streams don't go stale

<details><summary>Show answer</summary>

**B — When its offset is older than the source table's Time
Travel retention.** A stale stream cannot be queried; recreate
it.

</details>

---

**Q10.** The "minimal set of changes" pattern handles which DML
operations in one `MERGE`?

- A. `INSERT` only
- B. `INSERT` and `UPDATE` only
- C. `INSERT`, `UPDATE`, and `DELETE`
- D. All four including truncate

<details><summary>Show answer</summary>

**C — `INSERT`, `UPDATE`, and `DELETE`.** The `MERGE` has three
`WHEN` branches; the `ISUPDATE` filter keeps the set minimal.

</details>

---

**Q11.** What is an append-only stream?

- A. A stream that tracks only `INSERT` operations
- B. A stream that includes `DELETE`s
- C. A stream on an external table
- D. A stream on a temporary table

<details><summary>Show answer</summary>

**A — A stream that tracks only `INSERT` operations.**
Created with `APPEND_ONLY = TRUE`; cheaper and simpler than a
default stream.

</details>

---

**Q12.** `SYSTEM$STREAM_HAS_DATA` is used in which clause?

- A. The `WHEN` clause of a task
- B. The `WHERE` clause of a query
- C. The `AFTER` clause of a child task
- D. The `APPEND_ONLY` parameter

<details><summary>Show answer</summary>

**A — The `WHEN` clause of a task.** It's the canonical
predicate for "skip the task if the stream is empty".

</details>