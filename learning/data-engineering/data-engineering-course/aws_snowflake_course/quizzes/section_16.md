# Section 16 Quiz — Types of tables

> 8 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** How long does Fail Safe hold data after Time Travel expires?

- A. 1 day
- B. 7 days
- C. 30 days
- D. Until manually deleted

<details><summary>Show answer</summary>

**B — 7 days.** Fail Safe is a non-configurable 7-day window that
kicks in only after the table's `DATA_RETENTION_TIME_IN_DAYS`
expires.

</details>

---

**Q2.** Which role can read Fail Safe data?

- A. SYSADMIN
- B. The table owner
- C. ACCOUNTADMIN, and only by opening a Support case
- D. Any role with SELECT privilege on the table

<details><summary>Show answer</summary>

**C — Only ACCOUNTADMIN / Snowflake Support can read Fail Safe data
through a Support case.** It is invisible to all user queries.

</details>

---

**Q3.** Which table types exist?

- A. Permanent and transient
- B. Permanent, transient, temporary
- C. Permanent, ephemeral, temporary
- D. Durable, ephemeral, virtual

<details><summary>Show answer</summary>

**B — Permanent, transient, temporary.** The three Snowflake table
types covered in L113.

</details>

---

**Q4.** Which table type supports Fail Safe?

- A. Permanent
- B. Transient
- C. Temporary
- D. Both B and C

<details><summary>Show answer</summary>

**A — Only permanent.** Transient and temporary tables skip Fail Safe
entirely; their data is deleted after Time Travel expires.

</details>

---

**Q5.** What is the maximum Time Travel retention for a transient
table on Enterprise Edition?

- A. 0 days
- B. 1 day
- C. 7 days
- D. 90 days

<details><summary>Show answer</summary>

**B — 1 day on Enterprise.** Transient tables cap at 1 day
regardless of account-level settings; the typical pattern is to set
them to 0.

</details>

---

**Q6.** When is a temporary table dropped?

- A. After 1 day
- B. When the schema is dropped
- C. When the session that created it ends
- D. When the warehouse is suspended

<details><summary>Show answer</summary>

**C — When the creating session ends.** Temporary tables are
session-scoped; they are invisible to other sessions and disappear
on disconnect.

</details>

---

**Q7.** Which keyword creates a database whose tables inherit a
type with no Fail Safe?

- A. `CREATE DATABASE staging;`
- B. `CREATE TRANSIENT DATABASE staging;`
- C. `CREATE EPHEMERAL DATABASE staging;`
- D. `CREATE TEMPORARY DATABASE staging;`

<details><summary>Show answer</summary>

**B — `CREATE TRANSIENT DATABASE staging;`** A transient database
makes all its child schemas/tables transient by default.

</details>

---

**Q8.** You have a multi-TB staging table that is dropped and
recreated every 10 minutes. Which type is the cheapest?

- A. Permanent with `DATA_RETENTION_TIME_IN_DAYS = 0`
- B. Transient with `DATA_RETENTION_TIME_IN_DAYS = 0`
- C. Temporary
- D. It does not matter

<details><summary>Show answer</summary>

**B — Transient with retention = 0.** Transient skips Fail Safe
(which would otherwise consume memory bytes for churned data), and
the 0-day retention disables Time Travel. Permanent with 0 days
*looks* similar but still incurs Fail Safe overhead on mutations.
Temporary won't survive across recreations in different sessions.

</details>