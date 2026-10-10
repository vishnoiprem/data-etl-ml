# Section 4 Quiz — Loading Data

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** Which system-defined role has full control over a
Snowflake account?

- A. `SYSADMIN`
- B. `USERADMIN`
- C. `SECURITYADMIN`
- D. `ACCOUNTADMIN`

<details><summary>Show answer</summary>

**D — `ACCOUNTADMIN`.** It can see billing, drop accounts,
manage resource monitors. Use it sparingly; create other
roles for day-to-day work.

</details>

---

**Q2.** What does `GRANT SELECT, INSERT ON FUTURE TABLES IN
SCHEMA demo.raw` do?

- A. Grants on currently existing tables only
- B. Grants on all tables, past and future
- C. Grants on tables that will be created later in the
  schema
- D. Drops all future tables

<details><summary>Show answer</summary>

**C — Grants on tables that will be created later.** Without
`FUTURE`, you'd need to re-grant on every new table. Use
`FUTURE` grants in production pipelines.

</details>

---

**Q3.** A **stage** in Snowflake is:

- A. A SQL view
- B. A named reference to a storage location for files
- C. A type of virtual warehouse
- D. A Snowflake system database

<details><summary>Show answer</summary>

**B — A named reference to a storage location for files.**
Stages can be internal (Snowflake-managed) or external
(S3/ADLS/GCS). Referenced with `@<stage>`.

</details>

---

**Q4.** The recommended pattern for **production bulk loads**
is:

- A. `INSERT INTO ... VALUES`
- B. `COPY INTO <table> FROM @<stage>`
- C. Snowsight "Load data" wizard
- D. Snowpipe

<details><summary>Show answer</summary>

**B — `COPY INTO <table> FROM @<stage>`.** It's idempotent
via load history, parallelizes across files, and supports
column-level transforms. The UI wizard is for one-offs;
Snowpipe is for continuous auto-ingest.

</details>

---

**Q5.** What is the SQL syntax to access a field in a
**VARIANT** column?

- A. `column.field`
- B. `column->field`
- C. `column:field`
- D. `column[field]`

<details><summary>Show answer</summary>

**C — `column:field`.** Snowflake's colon-notation
(`payload:email`, `payload:user:id`) returns the value at
the path. For nested, use `:` repeatedly.

</details>

---

**Q6.** What does `METADATA$FILENAME` provide?

- A. The Snowflake account name
- B. The source file name for the row being loaded
- C. The MD5 hash of the row
- D. The warehouse name

<details><summary>Show answer</summary>

**B — The source file name for the row.** Use
`METADATA$FILENAME` and `METADATA$FILE_ROW_NUMBER` to build
an audit trail during loads.

</details>

---

**Q7.** What is the difference between `CAST` and `TRY_CAST`?

- A. `CAST` raises an error on bad data; `TRY_CAST` returns
  NULL
- B. They are identical
- C. `TRY_CAST` only works for numbers
- D. `CAST` only works for dates

<details><summary>Show answer</summary>

**A — `CAST` raises an error on bad data; `TRY_CAST` returns
NULL.** Use `TRY_CAST` for untrusted source data.

</details>

---

**Q8.** What does `LATERAL FLATTEN` do?

- A. Compresses a table
- B. Turns nested arrays/objects into rows
- C. Aggregates a column
- D. Drops a table

<details><summary>Show answer</summary>

**B — Turns nested arrays/objects into rows.** It's the
standard pattern for unnesting JSON arrays into a relational
table.

</details>

---

**Q9.** What is the default `ON_ERROR` behavior in `COPY
INTO`?

- A. `CONTINUE`
- B. `SKIP_FILE`
- C. `ABORT_STATEMENT`
- D. `DROP`

<details><summary>Show answer</summary>

**C — `ABORT_STATEMENT`.** If any row fails, the load is
rolled back. The safest default for data integrity.

</details>

---

**Q10.** `VALIDATE_TABLE_FUNCTION` returns:

- A. A summary of credit usage
- B. Detailed error information for a failed or validated
  load
- C. The list of all warehouses
- D. The list of all stages

<details><summary>Show answer</summary>

**B — Detailed error information for a failed or validated
load.** Use it after `VALIDATION_MODE` or `CONTINUE` loads
to see exactly which rows failed and why.

</details>