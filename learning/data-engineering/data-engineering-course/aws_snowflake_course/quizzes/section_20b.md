# Section 20b Quiz — Materialized Views + Data Masking (L155–L165)

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Scope:** L155–L165 (Materialized Views + Data Masking)

---

**Q1.** A materialized view differs from a standard view in that:

- A. It runs on read
- B. It precomputes the result and stores it on disk
- C. It can join multiple tables
- D. It supports `LIMIT`

<details><summary>Show answer</summary>

**B — It precomputes the result and stores it on disk.**
Reads are O(1) against the precomputed result; the cost is
maintenance on every source change.

</details>

---

**Q2.** Which of the following is a hard limit of a Snowflake
materialized view?

- A. Cannot have more than 10 columns
- B. Cannot join multiple tables
- C. Cannot be refreshed automatically
- D. Cannot be queried

<details><summary>Show answer</summary>

**B — Cannot join multiple tables.** MVs are limited to
single-table aggregations. For multi-table, use a dynamic
table or a task-driven pipeline.

</details>

---

**Q3.** What does `ALTER MATERIALIZED VIEW mv REFRESH` do?

- A. Drops the MV
- B. Forces a synchronous refresh
- C. Suspends the MV
- D. Renames the MV

<details><summary>Show answer</summary>

**B — Forces a synchronous refresh.** The statement blocks
until the refresh is complete. Useful after bulk loads.

</details>

---

**Q4.** The cost of a materialized view includes:

- A. Maintenance compute, storage, minus read savings
- B. Only maintenance compute
- C. Only storage
- D. Only read savings

<details><summary>Show answer</summary>

**A — Maintenance compute + storage − read savings.** The
net is what hits your credit balance.

</details>

---

**Q5.** A masking policy is a:

- A. A role that masks data
- B. A SQL function attached to a column
- C. A warehouse setting
- D. A stream type

<details><summary>Show answer</summary>

**B — A SQL function attached to a column.** It takes the
column value and returns either the value or a masked version,
based on the role of the querying user.

</details>

---

**Q6.** Which role can see the raw value through a masking
policy that returns `***-**-****` for `CURRENT_ROLE() !=
'ACCOUNTADMIN'`?

- A. Every role
- B. Only `ACCOUNTADMIN`
- C. Only `SYSADMIN`
- D. No one

<details><summary>Show answer</summary>

**B — Only `ACCOUNTADMIN`.** The policy's `CASE` returns
`val` for `ACCOUNTADMIN` and the mask for everyone else.

</details>

---

**Q7.** To attach a masking policy to a column you use:

- A. `ALTER TABLE ... SET MASKING POLICY ...`
- B. `CREATE MASKING POLICY ...`
- C. `GRANT MASKING POLICY TO TABLE ...`
- D. `ATTACH POLICY ... TO COLUMN ...`

<details><summary>Show answer</summary>

**A — `ALTER TABLE ... MODIFY COLUMN ... SET MASKING
POLICY ...`.** The full syntax:
`ALTER TABLE t MODIFY COLUMN c SET MASKING POLICY p;`

</details>

---

**Q8.** What is the safest pattern for column-level PII
protection?

- A. A view that omits the column
- B. A masking policy attached to the column
- C. Renaming the column
- D. Granting `USAGE` to a private role

<details><summary>Show answer</summary>

**B — A masking policy attached to the column.** It's
audit-friendly (the role check is logged) and survives view
replacements.

</details>

---

**Q9.** `CREATE OR REPLACE MASKING POLICY` is:

- A. Not allowed; you must `DROP` and `CREATE`
- B. Atomic; existing columns using the policy see the new
  body instantly
- C. Slow; it takes hours
- D. Permission-restricted to `ACCOUNTADMIN`

<details><summary>Show answer</summary>

**B — Atomic; existing columns see the new body instantly.**
No partial state.

</details>

---

**Q10.** `SHA2(val, 256)` is used in a masking policy to:

- A. Encrypt the value
- B. Produce a deterministic hash that's joinable across
  masked users
- C. Compress the value
- D. Time-stamp the value

<details><summary>Show answer</summary>

**B — A deterministic hash.** The same value always hashes
to the same SHA-256, so two masked users can still join on
the column.

</details>