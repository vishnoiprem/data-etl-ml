# 16 · Quiz 2 — BigQuery Fundamentals & Core Concepts

> **Section 2 · BigQuery Fundamentals · Lectures 2.1–2.9**
>
> Twelve questions covering why BigQuery exists, what runs under the hood, and how to
> create and place tables. Answers and reasoning are at the bottom — try to answer first.

---

## 📝 Questions

**1. The problem being solved.** Name three concrete operational problems BigQuery was
designed to remove versus a traditional Hadoop/Spark warehouse. For each one, say what the
engineer used to do and what they do now.

**2. The two layers.** BigQuery's storage and compute are named subsystems with different
design goals. Name both, state what each one owns, and explain why the storage layer has
no NameNode while HDFS does.

**3. Tree vs Volcano.** BigQuery's execution engine does not use the classic Volcano
row-at-a-time iterator model. What does it use instead, and what practical benefit does
that give a query over a wide table?

**4. What is a slot?** Give the exact vCPU/RAM definition of one BigQuery slot, then
calculate the slot-hours and cost of a query that uses 500 slots for 20 minutes at the
Standard Edition rate.

**5. Serverless, precisely.** A stakeholder asks: *"So there's no cluster at all?"* Give
the accurate answer. What does BigQuery operate on your behalf, and what do you still
control?

**6. The table-type decision.** For each scenario, name the table type and justify:
   - (a) A 90 PB immutable archive in Parquet on Cloud Storage, queried twice a year
   - (b) A 2 TB daily fact table that dashboards hit 50×/day
   - (c) A 5 GB lookup table refreshed hourly
   - (d) A point-in-time safety copy of a table, created once a week

**7. Regional vs multi-region.** A team has EU-resident customer data and a separate
global reporting table queried from three continents. Which gets `EU` and which gets
`US`? State the cost and residency consequence of each choice.

**8. The 2× rule.** A chapter claims a multi-region dataset costs roughly twice a regional
one. Give the concrete monthly numbers for 10 TB of active data in each, and explain
what you give up by choosing multi-region.

**9. The two creation methods.** Distinguish `CREATE TABLE ... (schema)` from
`CREATE TABLE ... AS SELECT`. What do you get in each, and when is each the right choice?

**10. Money type.** A schema stores `total_amount FLOAT64`. Name the problem, the fix,
and the reason the fix is not optional.

**11. Timestamp semantics.** A table has an `event_ts TIMESTAMP` and a
`business_date DATE`. Why does the course insist these are different columns rather than
one derived from the other?

**12. Creating a table.** Write the `CREATE TABLE` statement for a table with:
`order_id STRING NOT NULL`, `order_date DATE NOT NULL`, `total_amount NUMERIC`,
partitioned by `order_date`, clustered by `customer_id`, with a description, labels, and a
730-day partition expiry.

---

## ✅ Answers

**1. The problem being solved.**
   - **Cluster sizing and operations.** You provisioned, sized, patched, and babysat a
     Spark/Hive cluster. Now you run a query and pay for the work it does — BigQuery
     operates the fleet.
   - **The NameNode / metadata bottleneck.** HDFS keeps the namespace in a single
     NameNode in RAM — one process to scale, patch, and keep alive. Colossus distributes
     metadata with the data, so there is no such chokepoint.
   - **Storage-compute coupling and the provisioning lag.** A Spark cluster's storage was
     tied to its nodes; scaling meant buying machines and waiting. BigQuery separates
     storage from compute and scales them independently, immediately.

**2. The two layers.**
   - **Colossus** owns storage: a distributed, columnar, replicated store. No NameNode,
     because the metadata is distributed across the service rather than held in one
     process's RAM — so there is nothing to bottleneck or fail as a single point.
   - **Dremel** owns compute: the distributed query engine that schedules a query as a
     tree of operators across slots.
   - The split is what makes BigQuery serverless — you never touch either layer directly.

**3. Tree vs Volcano.** Dremel uses **tree execution**: each operator is a stage that
takes a batch of rows, processes it, and passes it on, with stages running in parallel.
The benefit is throughput on wide tables — a Volcano iterator would shuffle rows one at a
time between operators; tree execution streams batches, so a query touching a
thousand-column table moves data in parallel blocks instead of row-by-row handoffs.

**4. Slot arithmetic.** One slot = **1 vCPU + 4 GB RAM**.
   500 slots × (20 min ÷ 60) = 500 × 0.3333 = **166.67 slot-hours**.
   At $0.04 per slot-hour (Standard Edition): 166.67 × $0.04 = **$6.67**.
   Note how small this is: on-demand pricing would bill the *bytes scanned* instead, and
   for a wide table that is often far more than $6.67.

**5. Serverless, precisely.** There *is* a cluster — Google operates it, you do not.
   BigQuery manages provisioning, patching, load balancing, and failover of the compute
   fleet; you get elastic capacity sized to each query and billing for actual work done.
   What you still control: the SQL, the schema, the partition and cluster layout, the
   query settings, and — with capacity pricing — a reserved baseline of capacity.

**6. The table-type decision.**
   - (a) **External table** over the Parquet files. It never copies 90 PB; you pay to
     scan what you query, twice a year. A managed table would copy and then bill storage
     on all of it.
   - (b) **Managed (permanent) table** — probably partitioned by date and clustered.
     50 dashboard hits a day justify keeping the data resident and query-ready rather
     than re-scanning the lake.
   - (c) **Managed table**, refreshed by a scheduled query or a load job. Small enough
     that keeping it materialized is trivial, and hourly freshness needs a materialized
     copy to query.
   - (d) **Snapshot table** — `CREATE SNAPSHOT TABLE ... FOR SYSTEM_TIME AS OF ...`. It
     copies the data at a point in time and is then independent of the original.

**7. Regional vs multi-region.**
   - **EU-resident customer data → `EU` (regional).** The data physically stays in the
     EU; a multi-region `EU` dataset is also confined to the EU, but a *regional* dataset
     gives you the cheaper price and lower latency, and it is unambiguous on residency.
   - **Global reporting table → `US` (multi-region).** One copy serves users on three
     continents with lower latency than any single region.
   - The trade-off is explicit: multi-region costs roughly **2×** the storage of regional
     and buys global reach; regional costs less and pins the data to one place.

**8. The 2× rule.** Active logical storage is $0.02/GiB/month.
   - **Regional, 10 TB:** 10,240 GiB × $0.02 ≈ **$205/month**
   - **Multi-region, 10 TB:** 10,240 GiB × $0.02 × 2 ≈ **$410/month** (the chapter quotes
     ~$419 for 10 TB against a slightly different TB basis)
   You give up: half your storage budget, and the stronger residency guarantee a single
   region gives you. In exchange you get one dataset served from the nearest region to
   every user.

**9. The two creation methods.**
   - `CREATE TABLE t (col TYPE, ...)` creates an **empty** table with exactly the schema
     you declare. You then load data into it with `bq load`, a streaming insert, or the
     Storage Write API. Schema is flexible until the first data lands.
   - `CREATE TABLE t AS SELECT ...` creates the table *and* writes the query's results
     into it in one step. The schema is whatever the query produces — you do not get to
     tweak it afterwards without an `ALTER`.
   - Use the first for a load pipeline where you control the contract; the second when
     building a model table straight from a transformation.

**10. Money type.** `FLOAT64` is binary floating point — it cannot represent decimal
    fractions exactly, so money values drift (0.1 + 0.2 ≠ 0.3). The fix is **`NUMERIC`**,
    which stores an exact fixed-point decimal. It is not optional: a ledger that
    disagrees with itself is unusable, and reconciling the drift later costs far more
    than the storage difference.

**11. Timestamp semantics.** They answer different business questions.
    `event_ts TIMESTAMP` is an **absolute instant in UTC** — when the event actually
    happened, independent of timezone, and the only correct type for cross-system
    event ordering. `business_date DATE` is the **local calendar date** a business
    reports on — "yesterday's revenue" means yesterday in *the business's* timezone, not
    in UTC. Deriving one from the other forces you to pick a timezone permanently and
    hard-codes it; keeping both lets the report follow the business calendar. `DATE` is
    also what you partition on.

**12. Creating a table.**

```sql
CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.curated.orders` (
  order_id     STRING    NOT NULL,
  customer_id  STRING,
  order_date   DATE      NOT NULL,
  total_amount NUMERIC
)
PARTITION BY order_date
CLUSTER BY customer_id
OPTIONS(
  description = "Curated order facts",
  partition_expiration_days = 730,
  labels = [("tier", "curated"), ("owner", "data-eng")]
);
```

Note the placement: `PARTITION BY` and `CLUSTER BY` follow the column list, and
`description`, `partition_expiration_days`, and `labels` all live inside `OPTIONS(...)`.

---

## 🔑 Key Takeaways

- BigQuery = **Colossus** (storage, no NameNode) + **Dremel** (compute, tree execution).
- One slot = 1 vCPU + 4 GB. 500 slots × 20 min = 166.67 slot-hours = $6.67.
- "Serverless" means *you* don't run the cluster — not that there isn't one.
- External vs managed vs snapshot: **don't copy what you'll barely read**.
- Regional vs multi-region is a **cost-vs-reach** decision with residency implications.
- `NUMERIC` for money, `TIMESTAMP` for events, `DATE` for business partitions — each
  answers a different question, so each gets its own column.

---

## 📚 Next

[17 · Query Settings & Caching](./17-query-settings-and-caching.md)
