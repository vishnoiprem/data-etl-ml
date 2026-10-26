# Section 2 Quiz — Getting Started

> 10 questions, multi-choice, single answer. Answers are hidden in
> collapsible blocks; expand only after you've attempted the question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** What is the duration and credit budget of the Snowflake
free trial?

- A. 7 days, $100 credits
- B. 30 days, $400 credits
- C. 60 days, $1000 credits
- D. 90 days, unlimited

<details><summary>Show answer</summary>

**B — 30 days, $400 credits.** That's enough for ~200 hours of
an X-Small warehouse running flat-out, or ~20 hours of a Large.

</details>

---

**Q2.** Which edition does the free trial start on?

- A. Standard
- B. Enterprise
- C. Business Critical
- D. Virtual Private Snowflake (VPS)

<details><summary>Show answer</summary>

**B — Enterprise.** The trial unlocks most features including
multi-cluster warehouses, 90-day Time Travel, and materialized
views. Higher editions (Business Critical, VPS) require
upgrading.

</details>

---

**Q3.** What are the three layers of Snowflake's architecture?

- A. Application, presentation, data
- B. Storage, compute, cloud services
- C. CPU, RAM, disk
- D. Primary, secondary, tertiary

<details><summary>Show answer</summary>

**B — Storage, compute, cloud services.** Each layer scales
independently. Storage holds micro-partitions in S3/ADLS/GCS;
compute is virtual warehouses; cloud services is the always-on
metadata + query planner.

</details>

---

**Q4.** A **micro-partition** is best described as:

- A. A row in a table
- B. An immutable columnar file of 50–500 MB compressed with
  min/max metadata per column
- C. A type of virtual warehouse
- D. A Snowflake system role

<details><summary>Show answer</summary>

**B — An immutable columnar file of 50–500 MB compressed with
min/max metadata per column.** The metadata enables partition
pruning.

</details>

---

**Q5.** How long does Snowflake's **result cache** keep query
results?

- A. 1 minute
- B. 1 hour
- C. 24 hours
- D. 7 days

<details><summary>Show answer</summary>

**C — 24 hours.** Identical queries within that window return
instantly from the cache with no warehouse compute billed.

</details>

---

**Q6.** What is the **default** value for `AUTO_SUSPEND` on a
newly created warehouse?

- A. 0 (never suspend)
- B. 60 seconds
- C. 600 seconds
- D. 3600 seconds (1 hour)

<details><summary>Show answer</summary>

**B — 60 seconds.** That's a sensible default for most
workloads. Heavy ETL may want 300–600s; BI dashboards often
benefit from 60s.

</details>

---

**Q7.** Which `CREATE WAREHOUSE` parameter creates the
warehouse in a paused state so no credits are billed until a
query is submitted?

- A. `AUTO_SUSPEND = TRUE`
- B. `INITIALLY_SUSPENDED = TRUE`
- C. `AUTO_RESUME = FALSE`
- D. `PAUSED = TRUE`

<details><summary>Show answer</summary>

**B — `INITIALLY_SUSPENDED = TRUE`.** Without it, the warehouse
starts in the running state and bills for the first minute
immediately.

</details>

---

**Q8.** Which account_usage view shows **per-warehouse credit
usage** over time?

- A. `QUERY_HISTORY`
- B. `WAREHOUSE_METERING_HISTORY`
- C. `STORAGE_USAGE`
- D. `TASK_HISTORY`

<details><summary>Show answer</summary>

**B — `WAREHOUSE_METERING_HISTORY`.** Query it with
`SUM(credits_used) GROUP BY warehouse_name` to build a
cost dashboard.

</details>

---

**Q9.** Multi-cluster warehouses are available on which Snowflake
edition?

- A. Standard
- B. Enterprise and above
- C. Free trial only
- D. All editions

<details><summary>Show answer</summary>

**B — Enterprise and above.** The free trial starts on
Enterprise, so it has multi-cluster, but production Standard
editions do not.

</details>

---

**Q10.** The difference between `STANDARD` and `ECONOMY` scaling
policy is:

- A. STANDARD bills more credits per query
- B. STANDARD spins up clusters faster; ECONOMY waits longer to
  save cost
- C. ECONOMY is for ETL only
- D. They are synonyms

<details><summary>Show answer</summary>

**B — STANDARD spins up clusters faster; ECONOMY is more
conservative.** Use STANDARD for interactive BI; ECONOMY for
batch or budget-sensitive workloads.

</details>
