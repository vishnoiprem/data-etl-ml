# Section 14 Quiz — Time Travel

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** What is the default `DATA_RETENTION_TIME_IN_DAYS` for
a Snowflake table?

- A. 0
- B. 1
- C. 7
- D. 90

<details><summary>Show answer</summary>

**B — 1.** You can push it up to 90 on Enterprise and above;
Standard is locked at 1.

</details>

---

**Q2.** Which clause anchors a Time Travel query to a specific
UTC moment?

- A. `AT (TIMESTAMP => '<ts>'::TIMESTAMP_NTZ)`
- B. `AS OF '<ts>'`
- C. `BEFORE '<ts>'`
- D. `VERSION '<ts>'`

<details><summary>Show answer</summary>

**A — `AT (TIMESTAMP => '<ts>'::TIMESTAMP_NTZ)`.** The
`::TIMESTAMP_NTZ` cast disambiguates the literal; Snowflake
expects UTC, not your session timezone.

</details>

---

**Q3.** Which clause anchors a Time Travel query to the state
*just before* a specific statement ran?

- A. `AT (STATEMENT => '<id>')`
- B. `BEFORE (STATEMENT => '<id>'::STRING)`
- C. `PRIOR (QUERY => '<id>')`
- D. `PREVIOUS (STATEMENT => '<id>')`

<details><summary>Show answer</summary>

**B — `BEFORE (STATEMENT => '<id>'::STRING)`.** The query ID
is the handle; the state is the version *just before* that
statement.

</details>

---

**Q4.** Which is the recommended pattern to "undo" a bad
`UPDATE` with Time Travel?

- A. `INSERT INTO t SELECT * FROM t AT (OFFSET => -10 MINUTES);`
- B. `CREATE TABLE t_undo CLONE t AT (OFFSET => -10 MINUTES);
  ALTER TABLE t SWAP WITH t_undo;`
- C. `ROLLBACK;`
- D. `UPDATE t SET col = t_undo.col FROM t_undo;`

<details><summary>Show answer</summary>

**B — Clone + swap.** The clone is zero-copy (references the
same micro-partitions as the historical version). `INSERT
INTO ... SELECT ... AT | BEFORE` rewrites micro-partitions
and double-bills you on storage.

</details>

---

**Q5.** Which command recovers a dropped table within the Time
Travel window?

- A. `RESTORE TABLE <name>;`
- B. `UNDROP TABLE <name>;`
- C. `RECOVER TABLE <name>;`
- D. `CREATE TABLE <name> AS SELECT * FROM <name>;`

<details><summary>Show answer</summary>

**B — `UNDROP TABLE <name>;`** (also `UNDROP SCHEMA`,
`UNDROP DATABASE`). Works within the Time Travel retention
window.

</details>

---

**Q6.** If you `DROP TABLE prices` and then accidentally
`CREATE TABLE prices (...)` as a new empty table, what must
you do before `UNDROP TABLE prices` will work?

- A. Run `UNDROP DATABASE` instead
- B. Drop the empty stub `prices` table first
- C. Rename the new table
- D. Nothing — `UNDROP` always works

<details><summary>Show answer</summary>

**B — Drop the empty stub first.** A new object with the same
name occupies the slot; you must remove it before the original
can be restored.

</details>

---

**Q7.** What is the maximum value of
`DATA_RETENTION_TIME_IN_DAYS` on Standard edition?

- A. 1
- B. 7
- C. 30
- D. 90

<details><summary>Show answer</summary>

**A — 1.** Standard is locked at 1. Enterprise and above can
go up to 90.

</details>

---

**Q8.** Which scope of `DATA_RETENTION_TIME_IN_DAYS` wins when
multiple scopes are set?

- A. Account
- B. Database
- C. Most-specific (table > schema > database > account)
- D. Least-specific

<details><summary>Show answer</summary>

**C — Most-specific wins.** You can set a 1-day account
default and override a single audit table to 90 days.

</details>

---

**Q9.** Which view shows you the storage cost of Time Travel
history and Fail Safe on a table?

- A. `TABLE_STORAGE_METRICS` in `INFORMATION_SCHEMA`
- B. `STORAGE_USAGE` in `ACCOUNT_USAGE`
- C. `COPY_HISTORY`
- D. `PIPE_USAGE_HISTORY`

<details><summary>Show answer</summary>

**A — `TABLE_STORAGE_METRICS`.** Returns `active_bytes`,
`time_travel_bytes`, and `failsafe_bytes` per table. The
relevant columns for retention tuning are the latter two.

</details>

---

**Q10.** Which of the following does **not** apply to transient
tables?

- A. Default `DATA_RETENTION_TIME_IN_DAYS = 1`
- B. No Fail Safe
- C. Allowed in production with full retention
- D. Cheaper than permanent tables for short-lived data

<details><summary>Show answer</summary>

**C — Allowed in production with full retention.** Transient
tables are designed for staging and short-lived data; they
have no Fail Safe and a 1-day max retention. They are not
appropriate for production tables where you need long
recovery windows.

</details>
