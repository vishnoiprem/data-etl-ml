# Section 17 Quiz — Zero-Copy Cloning

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** A zero-copy clone of a 5 TB table takes how much storage at
the moment of creation?

- A. 5 TB (a full copy)
- B. 0 (metadata only)
- C. 50 GB (metadata + 1% overhead)
- D. 5 TB / number of micro-partitions

<details><summary>Show answer</summary>

**B — 0.** The clone is a metadata operation. Storage accrues only
when the source and clone diverge.

</details>

---

**Q2.** Which statement creates a zero-copy clone of a table?

- A. `CREATE TABLE x AS SELECT * FROM y;`
- B. `CREATE TABLE x CLONE y;`
- C. `INSERT INTO x SELECT * FROM y;`
- D. `COPY INTO x FROM y;`

<details><summary>Show answer</summary>

**B — `CREATE TABLE x CLONE y;`** The `CLONE` keyword triggers the
zero-copy path.

</details>

---

**Q3.** Which of the following is **not** inherited by a clone?

- A. Column definitions
- B. Clustering keys
- C. Grants on the source table
- D. Masking policies

<details><summary>Show answer</summary>

**C — Grants.** The clone is a brand-new object; it does not
inherit the source's privileges. Re-grant explicitly.

</details>

---

**Q4.** You can clone a clone.

- A. True
- B. False

<details><summary>Show answer</summary>

**A — True.** Cloning a clone is fully supported and remains
zero-copy at the moment of creation.

</details>

---

**Q5.** Which clause forks a clone from a specific point in time?

- A. `WHERE`
- B. `AS OF`
- C. `AT (TIMESTAMP => ...)`
- D. `VERSION`

<details><summary>Show answer</summary>

**C — `AT (TIMESTAMP => ...)`.** Same syntax as a Time Travel
`SELECT`, applied to the source of a `CLONE`.

</details>

---

**Q6.** A 1-day retention permanent table can be cloned at most
how far into the past?

- A. 1 day
- B. 7 days
- C. 90 days
- D. 365 days

<details><summary>Show answer</summary>

**A — 1 day.** The source's `DATA_RETENTION_TIME_IN_DAYS` is the
maximum depth for both Time Travel `SELECT` and historical clones.

</details>

---

**Q7.** Tasks in a clone are created in which state?

- A. Running
- B. Suspended
- C. Failed
- D. The same as the source

<details><summary>Show answer</summary>

**B — Suspended.** Snowflake pauses cloned tasks to prevent both
source and clone from running the same workload.

</details>

---

**Q8.** What does `ALTER TABLE prod.orders SWAP WITH staging.orders_v2` do?

- A. Renames the staging table; leaves prod alone
- B. Atomic rename of both tables
- C. Copies data from staging to prod
- D. Drops both tables

<details><summary>Show answer</summary>

**B — Atomic rename of both tables.** Either session sees the old
`prod.orders` or the new one — never an empty intermediate state.

</details>

---

**Q9.** Which constraint is true for `SWAP WITH`?

- A. The two tables must be in different databases
- B. The two tables must be the same type
- C. The two tables must be in the same schema
- D. Both B and C

<details><summary>Show answer</summary>

**D — Both B and C.** Both tables must be the same type
(permanent, transient, or temporary) and in the same database.

</details>

---

**Q10.** Which pattern is the canonical "ELT swap-and-drop"?

- A. Truncate-and-insert directly in prod
- B. Clone prod → transform clone → swap → drop
- C. Recreate prod from scratch every run
- D. Use an `UPSERT` to merge in place

<details><summary>Show answer</summary>

**B — Clone prod → transform clone → swap → drop.** Atomic, cheap,
reversible, and invisible to concurrent readers.

</details>