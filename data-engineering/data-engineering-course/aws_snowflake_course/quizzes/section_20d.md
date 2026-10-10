# Section 20d Quiz — Best Practices & Bonus (L182–L187)

> 8 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Scope:** L182–L187 (Best Practices + Bonus)

---

**Q1.** The #1 cost-control lever for Snowflake is:

- A. Warehouse size
- B. Auto-suspend
- C. Scaling policy
- D. Edition

<details><summary>Show answer</summary>

**B — Auto-suspend.** A warehouse auto-suspended at 60
seconds typically cuts idle cost by 60%+ vs always-on.

</details>

---

**Q2.** A resource monitor with `TRIGGERS ON 90 PERCENT DO
SUSPEND_IMMEDIATE` will:

- A. Send a notification at 90%
- B. Suspend all warehouses at 90% credit usage
- C. Drop the largest warehouse
- D. Disable the account

<details><summary>Show answer</summary>

**B — Suspend all warehouses at 90%.** The hard cap stops
further credit consumption.

</details>

---

**Q3.** A "right-sized" warehouse is:

- A. The largest available
- B. The smallest that finishes the workload in an
  acceptable time
- C. Always X-Small
- D. Always 4XL

<details><summary>Show answer</summary>

**B — The smallest that finishes the workload in an
acceptable time.** Start with X-Small; scale up only if
the workload is slow.

</details>

---

**Q4.** A clustering key is most useful when:

- A. The table is < 1 GB
- B. The table is > 1 TB and queries filter or join on
  the clustering columns
- C. The table is read-only
- D. The table has no `PRIMARY KEY`

<details><summary>Show answer</summary>

**B — The table is > 1 TB and queries filter / join on the
clustering columns.** For smaller tables, full scans are
fast enough that clustering doesn't help.

</details>

---

**Q5.** Snowflake enforces `PRIMARY KEY` and `FOREIGN KEY`
constraints declared on tables.

- A. True
- B. False

<details><summary>Show answer</summary>

**B — False.** Snowflake accepts the declarations for
documentation but does not enforce them. Validation
happens in your ETL code.

</details>

---

**Q6.** `DATA_RETENTION_TIME_IN_DAYS` for a transient table
caps at:

- A. 0 days
- B. 1 day
- C. 7 days
- D. 90 days

<details><summary>Show answer</summary>

**B — 1 day.** Transient tables cap at 1 day on Enterprise
Edition. For longer retention, promote to permanent.

</details>

---

**Q7.** A typical retention policy by table type:

- A. Audit 90 days; production 7 days; staging 1 day
- B. All 90 days
- C. All 0 days
- D. All 1 day

<details><summary>Show answer</summary>

**A — Audit 90 days; production 7 days; staging 1 day.** A
common production layout.

</details>

---

**Q8.** The "first five steps" in a new Snowflake account are:

- A. Roles, monitor, auto-suspend, ops dashboard, daily
  dev clone
- B. ACCTADMIN, SYSADMIN, SECURITYADMIN, USERADMIN, PUBLIC
- C. Stage, file format, pipe, task, stream
- D. Warehouse, database, schema, table, view

<details><summary>Show answer</summary>

**A — Roles, monitor, auto-suspend, ops dashboard, daily
dev clone.** The first five steps to a well-governed
account.

</details>