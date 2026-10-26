# Section 7 Quiz — Performance Optimization

> 10 questions, multi-choice, single answer. Answers are hidden
> in collapsible blocks; expand only after you've attempted the
> question.

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;

---

**Q1.** What is the typical speedup of switching from JSON to
Parquet for analytics queries?

- A. None — they're equivalent
- B. 2–3× (Parquet is slightly faster)
- C. 5–10× (Parquet is meaningfully faster for selective queries)
- D. 100× (Parquet is always orders of magnitude faster)

<details><summary>Show answer</summary>

**C — 5–10× for selective queries.** Parquet is columnar, so a
query that references 3 of 30 columns reads only those 3 from
disk. JSON has to parse the whole line. The exact speedup
depends on how selective the query is — for full-table scans
the gap is smaller.

</details>

---

**Q2.** Which Parquet file-format option tells Snowflake to
infer the column types from the file's schema?

- A. `TYPE = PARQUET`
- B. `INFER_SCHEMA = TRUE`
- C. `COMPRESSION = SNAPPY`
- D. There is no such option — Snowflake infers automatically

<details><summary>Show answer</summary>

**A — `TYPE = PARQUET`.** Once the file format type is
`PARQUET`, Snowflake reads the embedded schema header and
infers each column's type. `COMPRESSION = SNAPPY` is the
default compression. There is no `INFER_SCHEMA` option for
file formats — `INFER_SCHEMA` is a separate table function.

</details>

---

**Q3.** What is the single biggest cost-saving setting on a
Snowflake warehouse?

- A. `AUTO_SUSPEND = 60`
- B. `WAREHOUSE_SIZE = XSMALL`
- C. `SCALING_POLICY = ECONOMY`
- D. `RESOURCE_MONITOR = 100`

<details><summary>Show answer</summary>

**A — `AUTO_SUSPEND = 60`.** Idle warehouses bill credits.
Dropping `AUTO_SUSPEND` from 600 s (the default) to 60 s
typically saves 80% of idle cost for a 5-person BI team. A
smaller warehouse is useful too, but the suspending behaviour
is the dominant lever.

</details>

---

**Q4.** What is the difference between scale up and scale out?

- A. Scale up = bigger warehouse (more CPUs per cluster); scale
  out = more clusters (more concurrent queries)
- B. Scale up = bigger warehouse; scale out = smaller warehouse
- C. Scale up = Snowflake-managed; scale out = user-managed
- D. They are synonyms

<details><summary>Show answer</summary>

**A — Scale up is bigger; scale out is more clusters.** Scale
up helps **one slow query** finish faster. Scale out helps
**many concurrent queries** run in parallel without queuing.
They're complementary, not alternatives.

</details>

---

**Q5.** Which scaling policy adds a cluster as soon as the
queue grows by one query?

- A. `STANDARD`
- B. `ECONOMY`
- C. `AGGRESSIVE`
- D. `IMMEDIATE`

<details><summary>Show answer</summary>

**C — `AGGRESSIVE`.** `STANDARD` waits ~20 s before adding;
`ECONOMY` waits longer to save money; `AGGRESSIVE` adds a
cluster as soon as the queue grows. Use `AGGRESSIVE` for
user-facing apps where latency dominates cost.

</details>

---

**Q6.** A query's `Total_elapsed_time` drops from 60 s to 80 ms
on the second identical run, with no warehouse resize. Which
cache served it?

- A. Local disk cache
- B. Query history cache
- C. Result cache
- D. Materialised view

<details><summary>Show answer</summary>

**C — Result cache.** The result cache returns exact-match
queries in milliseconds, with no compute and no warehouse
resume. The local disk cache is per-warehouse file-level data
and still incurs some compute cost. A drop from 60 s to 80 ms
is the signature of a result-cache hit.

</details>

---

**Q7.** The local disk cache is scoped to which scope?

- A. The account
- B. The database
- C. The warehouse
- D. The user

<details><summary>Show answer</summary>

**C — The warehouse.** Each warehouse has its own SSD cache.
A query on `bi_wh` does not benefit from a prior `loading_wh`
read of the same table. That's why pinning dashboards to one
warehouse is so important.

</details>

---

**Q8.** Which SQL pattern enables the query history cache to
prune the most micro-partitions?

- A. `WHERE YEAR(order_ts) = 2026`
- B. `WHERE order_ts >= '2026-01-01' AND order_ts < '2027-01-01'`
- C. `WHERE order_ts = '2026-06-15'`
- D. `WHERE order_ts IS NOT NULL`

<details><summary>Show answer</summary>

**B — `WHERE order_ts >= '2026-01-01' AND order_ts < '2027-01-01'`.**
Range predicates on a single column prune micro-partitions
effectively. `YEAR(order_ts) = 2026` wraps the column in a
function, which prevents pruning. `=` on a high-cardinality
column only prunes if the value lands in a single partition.

</details>

---

**Q9.** What does `ALTER SESSION SET USE_CACHED_RESULT = FALSE`
do?

- A. Disables the local disk cache
- B. Forces the next query to bypass the result cache
- C. Turns off the warehouse
- D. Clears the query history cache

<details><summary>Show answer</summary>

**B — Bypasses the result cache.** Set this when an analyst
asks "is this up to date?" — the result cache is 24 h stale,
so a brand-new row won't appear in cached results. The local
disk cache and query history cache are unaffected.

</details>

---

**Q10.** Why should you keep SQL text **byte-for-byte
identical** for repeated queries?

- A. It is a Snowflake linting requirement
- B. The result cache is keyed on the exact SQL text; whitespace
  differences break the cache
- C. Snowflake charges more for non-canonical SQL
- D. It speeds up the query history cache

<details><summary>Show answer</summary>

**B — The result cache is keyed on exact text.** `SELECT
COUNT(*) FROM orders` and `select count(*) from orders` are
two different cache entries. Parameterised SQL — same text,
different bind values — gives you one cache entry that serves
many users. This is how BI tools get high cache hit ratios.

</details>