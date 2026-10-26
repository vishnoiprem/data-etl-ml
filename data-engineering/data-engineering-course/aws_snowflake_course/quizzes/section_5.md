# Section 5 Quiz — Copy Options

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** A **named file format object** is best described as:

- A. A one-off inline `FILE_FORMAT = (...)` in a single
  `COPY INTO`
- B. A reusable, named set of file format options scoped to
  a schema
- C. A type of stage
- D. A type of warehouse

<details><summary>Show answer</summary>

**B — A reusable, named set of file format options scoped to
a schema.** Created with `CREATE FILE FORMAT`; used with
`FILE_FORMAT = (FORMAT_NAME = '<name>')`.

</details>

---

**Q2.** How do you reference a named file format object in
`COPY INTO`?

- A. `FILE_FORMAT = <name>`
- B. `FILE_FORMAT = (FORMAT_NAME = '<name>')`
- C. `FILE_FORMAT = (USE = '<name>')`
- D. `USE_FILE_FORMAT = '<name>'`

<details><summary>Show answer</summary>

**B — `FILE_FORMAT = (FORMAT_NAME = '<name>')`.** You can
also attach a default file format to a stage via
`STAGE_FILE_FORMAT = <name>`.

</details>

---

**Q3.** What is the difference between named and inline
file formats?

- A. Named formats support more types
- B. Named formats are reusable across statements and stages;
  inline are one-off
- C. Inline formats are faster
- D. There is no difference

<details><summary>Show answer</summary>

**B — Named formats are reusable across statements and
stages; inline are one-off.** Use named for production
pipelines, inline for ad-hoc.

</details>

---

**Q4.** What does `VALIDATION_MODE = 'RETURN_ALL_ERRORS'`
do?

- A. Loads all rows and reports errors
- B. Validates the load without inserting any rows and
  returns all errors
- C. Drops the table
- D. Truncates the table

<details><summary>Show answer</summary>

**B — Validates the load without inserting any rows and
returns all errors.** Use it as a pre-flight check before
the real load.

</details>

---

**Q5.** How do you retrieve the detailed list of rejected
records after a `COPY INTO`?

- A. `SELECT * FROM TABLE(VALIDATE(<table>, JOB_ID =>
  '<query_id>'))`
- B. `SHOW REJECTIONS FOR <table>`
- C. `DESC TABLE <table>`
- D. `LIST REJECTIONS`

<details><summary>Show answer</summary>

**A — `SELECT * FROM TABLE(VALIDATE(<table>, JOB_ID =>
'<query_id>'))`.** Returns one row per rejected record with
the reason, source line, and column.

</details>

---

**Q6.** What does `SIZE_LIMIT = 50000000` do?

- A. Caps the file size to 50 MB
- B. Caps the total bytes loaded by a single `COPY INTO` to
  50 MB
- C. Caps the number of rows
- D. Caps the number of files

<details><summary>Show answer</summary>

**B — Caps the total bytes loaded by a single `COPY INTO`
to 50 MB.** Useful for cost guards and throttling.

</details>

---

**Q7.** What does `RETURN_FAILED_ONLY = TRUE` do?

- A. Loads only failed files
- B. Returns only failed files in the result set
- C. Drops failed files
- D. Skips the load if any file fails

<details><summary>Show answer</summary>

**B — Returns only failed files in the result set.** It
filters the result, not the load itself.

</details>

---

**Q8.** What does `TRUNCATECOLUMNS = TRUE` do?

- A. Truncates the table before loading
- B. Silently truncates strings that exceed the column width
- C. Drops columns not in the source
- D. Adds new columns

<details><summary>Show answer</summary>

**B — Silently truncates strings that exceed the column
width.** Use it carefully — truncation is silent and may
lose data.

</details>

---

**Q9.** What is the **default retention period** of load
history?

- A. 7 days
- B. 30 days
- C. 64 days
- D. 1 year

<details><summary>Show answer</summary>

**C — 64 days.** After that, a re-load of the same file is
treated as new unless you archive the history.

</details>

---

**Q10.** When using `FORCE = TRUE`, what is the recommended
companion step to avoid duplicates?

- A. `DROP TABLE`
- B. `TRUNCATE` or `MERGE` first
- C. `SHOW TABLES`
- D. Nothing; `FORCE` handles it

<details><summary>Show answer</summary>

**B — `TRUNCATE` or `MERGE` first.** `FORCE = TRUE` bypasses
load history but doesn't deduplicate. Without a truncate or
merge, you may double-count rows.

</details>