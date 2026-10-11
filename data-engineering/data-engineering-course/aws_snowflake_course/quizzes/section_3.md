# Section 3 Quiz — Snowflake Architecture

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** The hierarchy in Snowflake is:

- A. Account → Catalog → Schema → Table
- B. Account → Database → Schema → Table
- C. Region → Database → Table
- D. Cloud → Region → Account → Table

<details><summary>Show answer</summary>

**B — Account → Database → Schema → Table.** Schemas contain
tables, stages, file formats, pipes, tasks, streams, sequences,
and views.

</details>

---

**Q2.** Which system database contains the `ACCOUNT_USAGE`
metadata views?

- A. `DEMO`
- B. `SNOWFLAKE`
- C. `ACCOUNT_USAGE`
- D. `PUBLIC`

<details><summary>Show answer</summary>

**B — `SNOWFLAKE`.** The `ACCOUNT_USAGE` schema lives inside
the `SNOWFLAKE` database. By default only `ACCOUNTADMIN` can
query it.

</details>

---

**Q3.** Which command lists all warehouses in the account?

- A. `LIST WAREHOUSES;`
- B. `SHOW WAREHOUSES;`
- C. `SELECT * FROM WAREHOUSES;`
- D. `DESCRIBE WAREHOUSE;`

<details><summary>Show answer</summary>

**B — `SHOW WAREHOUSES;`** Snowflake's native way to list
objects. `SHOW` returns rich metadata; the SQL-standard
`INFORMATION_SCHEMA.WAREHOUSES` is a cross-database alternative.

</details>

---

**Q4.** Which Snowflake loading pattern is **serverless** and
billed per file (not per warehouse)?

- A. `COPY INTO`
- B. Snowpipe
- C. Snowsight "Load data" wizard
- D. Manual `INSERT`

<details><summary>Show answer</summary>

**B — Snowpipe.** It uses Snowflake-managed compute billed per
file processed. `COPY INTO` is batch and uses your warehouse.

</details>

---

**Q5.** Which is **not** a Snowflake edition?

- A. Standard
- B. Enterprise
- C. Business Critical
- D. Foundation

<details><summary>Show answer</summary>

**D — Foundation.** The five tiers are Standard, Enterprise,
Business Critical, Virtual Private Snowflake (VPS), and
Government / VPS for US Government.

</details>

---

**Q6.** Which edition is required for **HIPAA** support and
**Tri-Secret Secure**?

- A. Standard
- B. Enterprise
- C. Business Critical
- D. VPS

<details><summary>Show answer</summary>

**C — Business Critical.** It adds HIPAA / PCI compliance,
customer-managed keys, and database failover with no data
loss.

</details>

---

**Q7.** What is the **per-second billing minimum** when a
warehouse is running?

- A. 1 second
- B. 60 seconds
- C. 5 minutes
- D. 1 hour

<details><summary>Show answer</summary>

**B — 60 seconds.** After the first minute, billing is precisely
proportional to runtime. The minimum exists because spinning
up a cluster has fixed cost.

</details>

---

**Q8.** When are **cloud services** billed?

- A. Always, per credit
- B. Only when monthly services usage exceeds 10% of
  corresponding warehouse compute
- C. Only on weekends
- D. Never

<details><summary>Show answer</summary>

**B — Only when monthly services usage exceeds 10% of the
corresponding warehouse compute.** In practice this is rare;
services are usually free.

</details>

---

**Q9.** Is **Fail-safe storage** billed separately?

- A. Yes, at the standard rate
- B. Yes, at a 50% surcharge
- C. No — included in active storage
- D. Only on weekends

<details><summary>Show answer</summary>

**C — No.** Fail-safe is included in active storage. Only Time
Travel (beyond the default 1 day) is billed separately.

</details>

---

**Q10.** Which action does a resource monitor take at the
**100% threshold** by default?

- A. NOTIFY
- B. SUSPEND
- C. SUSPEND_IMMEDIATE
- D. DROP

<details><summary>Show answer</summary>

**B — SUSPEND (graceful).** SUSPEND lets in-flight queries
finish; SUSPEND_IMMEDIATE aborts them. Both are valid choices
depending on policy.

</details>