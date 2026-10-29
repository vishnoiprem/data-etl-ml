# 2.1 — Conventional Data Warehouse Problems

> **Section 2 · BigQuery Fundamentals · Lecture 2.1 · 3:41**

## 🎯 What you will learn

- Why traditional Hadoop/Spark data warehouses are hard and expensive
- The five specific problems BigQuery was designed to eliminate
- How to articulate this to a non-technical stakeholder

---

## 🧠 Concept

To understand BigQuery, you need to understand what it replaced. The pre-BigQuery enterprise data
warehouse had a well-known set of problems, and BigQuery is a direct answer to each.

### The pre-2010 stack

```
Raw data ──▶ HDFS (NameNode) ──▶ Hive (MetaStore) ──▶ Spark (YARN) ──▶ Hive/SQL
                 ▲                     ▲                    ▲
             single SPOF           single SPOF         capacity planning
             RAM bottleneck        metadata bottleneck   cluster sizing
```

### The five problems

**1. Cluster sizing and capacity planning.**
Spark on YARN needed a fixed cluster. Under-provision and queries queue for hours; over-provision
and you pay for idle nodes all month. Worse, the cluster was optimized for *one* workload — batch
ETL or interactive queries — and you often needed two clusters.

> 💰 *The cost of over-provisioning an underused 100-node Spark cluster: roughly $30,000/month in
> wasted node time, with an 8–12% average utilization.*

**2. Data loading time ("ETL hell").**
To make data queryable you had to convert formats, rewrite into columnar layout, and `LOAD` it into
a table. This was often 60–80% of the pipeline's wall-clock time, and it was pure waiting.

**3. Metadata and schema management.**
Hive's Metastore was a single MySQL database — a hard SPOF and a nightly-painful operation. Schema
evolution meant `ALTER TABLE` on huge tables with no transactional safety.

**4. NameNode as a single point of failure.**
HDFS stored all metadata in RAM on one machine. It needed a warm standby, manual failover, and it
imposed a hard limit on the number of files (tens of millions) and total namespace size. Small files
were a chronic performance problem.

**5. Storage/compute coupling.**
You couldn't store data cheaply and query it expensively. Storage was on spinning disks in the
same nodes that ran the query. Choosing to keep 3 years of history meant keeping 3 years of
expensive compute nodes alive.

### What BigQuery changed

| Traditional problem | BigQuery answer |
|---------------------|----------------|
| Cluster sizing | **Serverless** — no cluster exists. Resources scale per query. |
| Load time | **Columnar storage** — no load needed for external files; managed tables write directly. |
| Metadata SPOF | **Managed catalog** — Google operates it; INFORMATION_SCHEMA for you. |
| NameNode SPOF | **No NameNode** — storage is a distributed, replicated service (Colossus). |
| Coupled storage/compute | **Separated** — store once, compute per query, priced independently. |

### The deeper point

The old stack's real cost was not compute — it was **human cost**. Someone had to size clusters,
watch HDFS, tune Hive, manage Metastore, and keep everything running. BigQuery's pitch is not
"faster queries"; it is **"fewer things to break."**

That said, BigQuery is not automatically cheaper. A badly designed BigQuery implementation — no
partitioning, on-demand pricing, a dashboard that scans 40 TB daily — can cost more than the Spark
cluster it replaced. BigQuery moves the cost from **infrastructure** to **design**, which is
usually a better trade, but only if you do the design work. That is the subject of Module 4.

---

## 🛠️ Hands-On: Quantify the Traditional Cost

### The old model (Spark on EMR/YARN)

```
Cluster: 10 × m5.2xlarge (8 vCPU, 32 GB)
  Node cost:      $0.384 / hour
  Utilization:    10% average (nightly batch + occasional ad-hoc)
  Hours/month:    730
  Monthly cost:   10 × $0.384 × 730 = $2,803

Cluster #2 (interactive BI, always on, 5 nodes): $1,401
Data engineer time: 1 FTE maintaining HDFS, Hive, Spark tuning
  Loaded cost:     ~$12,000 / month

TOTAL: ~$16,200 / month
```

### The BigQuery model

```
Storage:      20 TB active, $0.02/GB-mo        = $419 / month
Queries:      5 TB scanned/mo @ $6.25/TiB       = $ 31 / month
              (plus heavy ad-hoc usage, say 50 TB)= $313 / month
Data engineer time: ~1/4 FTE (no cluster admin) = $3,000 / month

TOTAL: ~$3,700 / month
```

> Savings: **~$12,500/month, ~$150,000/year**, plus the elimination of on-call pages at 3am.

### A caveat worth stating

The comparison is only fair if BigQuery is used *well*. Here is what the same company would pay
with a poorly designed BigQuery platform:

```
Storage:      20 TB                          = $ 419
Queries:      500 TB scanned/mo @ $6.25/TiB  = $3,125   ← unpartitioned tables
Engineer time:                              = $3,000
TOTAL: ~$6,544 / month
```

**Still cheaper than $16,200** — but you have left ~$10,000/month on the table. Partitioning,
clustering, and materialized views are not optional extras; they are where the savings live.

---

## 💡 Production Notes

- **"Serverless" does not mean "free" or "infinitely fast."** A query that scans 40 TB still costs
  $250 and still takes minutes.
- **BigQuery's concurrency advantage is real.** A thousand analysts hitting the same dashboard do
  not queue behind each other the way they would on a shared Hive/Hive-on-Spark cluster.
- **Migration is rarely a pure lift-and-shift.** Parquet in GCS + BigQuery external tables often
  beats a full load into managed tables — you trade query speed for near-zero ingestion cost.

---

## 🔑 Key Takeaways

- Traditional warehouses suffered from cluster sizing, load time, metadata SPOFs, NameNode SPOFs,
  and coupled storage/compute.
- BigQuery eliminates all five via serverless execution, columnar storage, and separated
  storage/compute.
- The biggest saving is **engineering time**, not infrastructure spend.
- BigQuery shifts cost from infrastructure to **design** — do the design work or you will pay for
  it in query bills.
- Serverless still means pay-per-scan. An unpartitioned dashboard can burn thousands a month.

---

## 📚 Practice Exercises

1. **Cost model.** Recompute both models for 100 TB of data and 10 TB scanned/month. At what point
   does BigQuery's cost model flip against a fixed Spark cluster?

2. **Migration strategy.** A company has 500 TB of Parquet on S3. Design a migration to GCP in
   three phases, with the decision criteria for each phase (external table vs managed table).

3. **Stakeholder pitch.** Write a 150-word explanation for a CFO: why move from a Spark cluster to
   BigQuery? Focus on risk, not just cost.

4. **NameNode limits.** Research the HDFS NameNode limits (file count, namespace size) and explain
   concretely how "many small files" becomes a BigQuery design problem (partitioning strategy).

---

## 📖 Further Reading

- HDFS Architecture — https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-hdfs/HdfsDesign.html
- BigQuery architecture — https://cloud.google.com/bigquery/docs/introduction
- Cloud Architecture Framework: Data Analytics — https://cloud.google.com/architecture/data-analytics
