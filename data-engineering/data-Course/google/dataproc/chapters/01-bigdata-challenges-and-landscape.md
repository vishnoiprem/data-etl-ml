# 1.1 — Big Data Challenges: From Hadoop to Spark to Dataproc

> **Section 1 · Foundations · Lecture 1.1 · 4:11**

## 🎯 What you will learn

- What actually makes a dataset "big" — and why the usual database answer fails
- The four classic Big Data problems: volume, velocity, variety, veracity
- How Hadoop's MapReduce answered them — and where it became painful
- What Spark changed, and why it is now the default for batch and streaming
- Where Google Cloud Dataproc fits: a managed Spark service, not a Hadoop distro

---

## 🧠 Concept

A single PostgreSQL server can hold terabytes and serve millions of queries a second. So why does
the word "big data" exist at all?

The answer is not raw size. It is the **shape of the workload**.

A traditional database is optimized for: a well-understood schema, a query that touches a
bounded fraction of the data, and a user who can afford to wait seconds. Big Data workloads
break every one of those assumptions:

| Assumption | What breaks it |
|------------|---------------|
| Data fits on one machine's disk | 100 TB of clickstream logs, replayed daily |
| Queries touch a small fraction | Full scans are the norm — aggregation over everything |
| Schema is known ahead of time | JSON events with new fields every week |
| Queries are interactive | Batch jobs that run for hours, night after night |
| Scale is bought by buying a bigger box | Need 10× capacity for a month, then back to 10% |

That last row is the expensive one. Traditional scaling is **vertical** — buy a bigger server.
It works, but it's linear in cost and it means you own the hardware, the power, the cooling, and
the refresh cycle. For a workload that is spiky (batch overnight, idle during the day), you are
paying for peak capacity 24/7.

Distributed processing flips the model to **horizontal** scaling: add more ordinary machines,
run the job across all of them, then throw them away when the job is done.

---

## The Four Vs

**Volume** — the sheer amount of data. Petabytes to exabytes.

**Velocity** — the rate at which data arrives and must be processed. Clickstreams, IoT telemetry,
market ticks, application logs.

**Variety** — the number of shapes. Structured tables, semi-structured JSON, documents, images,
audio, binary blobs, graphs.

**Veracity** — the trustworthiness of it. Duplicate events, late-arriving records, schema drift,
malformed rows, missing values.

**Value** — the fifth V people add later: the actual business payoff. Most Big Data projects fail
not because the processing was wrong, but because nobody could turn it into a decision.

💡 **Veracity is the V engineers underestimate.** A pipeline that silently drops 3% of records
because of a malformed line will report confidently incorrect numbers for months. Design for
quarantine and counts from day one.

---

## Hadoop: the original answer

Hadoop (2006) made horizontal scale mainstream by moving computation to the data.

```
HDFS  ──  NameNode (metadata)
         DataNodes × N (store the actual blocks)

MapReduce ── Map tasks (parallel, near the data)
             Shuffle & Sort (network transfer — the bottleneck)
             Reduce tasks (aggregate)
```

The **NameNode** is a single point of failure (mitigated in Hadoop 3 by the Standby NameNode), and
the **shuffle** — moving intermediate results across the network between map and reduce — is
where most of the time goes.

Hadoop solved Volume and Variety acceptably. Velocity and Veracity less so.

---

## Spark: the modern answer

Apache Spark (2009, UC Berkeley) kept HDFS but replaced MapReduce with an in-memory,
general-purpose execution engine.

The critical insight: **MapReduce forces everything to disk between stages.** Spark keeps data in
memory (where it fits) and reuses the same process for multiple operations. A ten-operation
pipeline that would take ten MapReduce jobs — each paying startup cost and a disk write — becomes
one job with ten stages.

Spark's improvements over Hadoop MapReduce:

| Dimension | Hadoop MapReduce | Spark |
|-----------|-----------------|-------|
| Iteration (ML algorithms) | Terrible — each iteration = new job | Fast — one job, in-memory |
| Data processing | Disk between stages | Memory between stages (with disk spill) |
| Interactive SQL | Hive on top of MapReduce | Spark SQL with a cost-based optimizer (Catalyst) |
| Stream processing | Not built in | Structured Streaming (micro-batch or continuous) |
| Languages | Java only | Scala, Python, Java, R, SQL |
| Machine learning | Mahout, separate stack | MLlib, integrated with the DataFrame API |

Spark's developer API is far friendlier than MapReduce's. The equivalent of a 40-line MapReduce
job is roughly 4 lines of PySpark.

### The unified DataFrame API

This is the single most important thing to internalize for this course:

```
RDD (2011)  →  DataFrame (2014)  →  Dataset (2016)
  low-level       structured         typed
```

Spark 2.x unified DataFrame and Dataset; Spark 3.x made the DataFrame API the default way to
write everything. **Everything in this course uses DataFrames unless we are explicitly teaching
RDDs**, because DataFrames give you:

- A **schema** — Catalyst knows your column types and can plan around them
- A **Catalyst optimizer** — predicate pushdown, constant folding, join reordering
- **Tungsten** — a columnar, code-generation-aware execution engine

💡 **You will still need to understand RDDs.** The interview question "when would you use an RDD
instead of a DataFrame?" has a real answer, and chapter 3 covers it properly. But if you write
new PySpark code today and reach for RDDs by default, you are writing 2012 code.

---

## Dataproc: managed Spark on Google Cloud

Apache Spark is open source and runs anywhere: on your laptop, on Kubernetes, on a VM, on
Dataproc. The question is who operates it.

**Self-managed Spark** means you own:
- Cluster provisioning and teardown
- OS and JDK patching
- Python and dependency packaging for every worker
- Autoscaling logic
- YARN/Kubernetes configuration
- Monitoring, logging, and incident response

**Dataproc** is Google's managed Spark. You describe the cluster you want — master/worker counts,
machine types, optional Hadoop/Hive/Spark components, initialization scripts — and Google runs it.
It bills per-second for running workers, and it is deeply integrated with the rest of GCP:

| Integration | What it means |
|-------------|---------------|
| **Cloud Storage** | Read/write HDFS-equivalent data natively; no NameNode to operate |
| **BigQuery** | Bulk read via Storage Write API, bulk load via Storage Write API, and direct table I/O from Spark |
| **Cloud Storage as the metastore** | Hive metadata without a Hive Metastore server to run |
| **Cloud Monitoring** | Cluster metrics, Spark executor metrics, custom metrics from Spark |
| **Cloud Logging** | Driver and executor logs, searchable |
| **IAM + VPC** | Private clusters, service accounts, CMEK encryption |
| **Workflows / Cloud Composer** | Submit and orchestrate Dataproc jobs from Airflow |
| **Vertex AI** | Spark ML models served on Vertex endpoints |

Dataproc image versions track Apache Spark releases. As of the 2.2 LTS image family, Spark 3.5
is the default runtime. The image version matters more than anything else in Dataproc — it
determines your Spark version, your Python version, and which Hadoop ecosystem components are
included.

⚠️ **Dataproc 2.x is the current family. Dataproc 1.x reached end of support.** Always specify
`--image-version` explicitly; never rely on the default, because the default changes and your
job may silently change behavior.

---

## Why Dataproc specifically

The core economic argument is **ephemeral clusters**.

A traditional Hadoop cluster is sized for peak load and runs forever. Dataproc clusters are
designed to be created for a job and destroyed when it finishes:

```
        Job arrives
             │
    ┌────────▼─────────┐
    │  Create cluster   │  ← ~60-90 seconds
    │  (3 workers)      │
    └────────┬─────────┘
             │
    ┌────────▼─────────┐
    │  Run Spark job    │
    └────────┬─────────┘
             │
    ┌────────▼─────────┐
    │  Delete cluster   │  ← seconds
    └──────────────────┘
```

You pay only for the minutes the cluster existed. For batch ETL — which is most ETL — this is a
large win compared to a permanently warm cluster.

Dataproc also gives you **two cluster modes**, and choosing between them is one of the most
important operational decisions:

| Mode | Lifecycle | Best for |
|------|-----------|----------|
| **Temporary** | Created per job, deleted after | Batch ETL, scheduled pipelines, one-off analysis |
| **Persistent** | Long-running, manually or auto-scaled | Interactive development, streaming jobs, shared clusters |

And two ways to run code on a cluster:

| Method | How it works | Best for |
|--------|--------------|----------|
| **Job submission** (`gcloud dataproc clusters submit`) | Package code, upload, run on the cluster, fetch logs | Production pipelines, repeatable jobs |
| **Interactive sessions** (Jupyter, SSH, Spark Connect) | Attach a live session to a running cluster | Development, exploration, teaching |

This course uses **job submission** for all pipeline work and **interactive sessions** for the
learning labs, which is exactly how you should structure your own work.

---

## The cost model

Dataproc bills:

- **Workers** — per-second, based on machine type
- **Master** — per-second, based on machine type
- **Managed worker** — an optional always-on worker pool sized to zero when idle (billed for
  scaling up, plus the idle floor)
- **Storage** — Cloud Storage for data, Persistent Disk for the cluster

⚠️ **Two Dataproc cost traps:**

1. **A forgotten cluster bills 24/7.** The single most common surprise for newcomers. Always
   enable **Cluster Deletion Scheduled** (auto-delete after N minutes of inactivity) or set
   `--max-idle` and use temporary clusters.

2. **Big data means big bills.** The `standard` machine type is 4× the price of `preemptible`
   for roughly 1/4 the throughput. Use preemptible workers for fault-tolerant batch work (Spark
   is designed to retry failed tasks), and standard workers only where you need guaranteed
   capacity.

💡 **Rule of thumb:** if the job takes longer than a few minutes, you want a preemptible-tolerant
cluster with more workers. The cluster lifecycle should be automated — a cluster that is running
while no job is running is pure waste.

---

## 🛠️ Hands-On: Your first look at the landscape

### Verify your tools

```bash
# gcloud
gcloud --version

# Which account / project are you actually using?
gcloud auth list
gcloud config get-value project

# Is Dataproc enabled?
gcloud services list --enabled --filter="config.name:dataproc.googleapis.com"
```

### Check the available images

```bash
# List image versions — note the newest 2.x and its Spark version
gcloud dataproc clusters describe-versions \
  --project=YOUR_PROJECT_ID 2>/dev/null || \
gcloud dataproc image list --project=YOUR_PROJECT_ID
```

The output shows image versions like `2.2-debian12` (Spark 3.5) alongside older families. Pin
the version in every command you write.

### Estimate before you create

```bash
# A quick cost sanity check for a 3-worker n1-standard-4 cluster
# Master n1-standard-4: ~$0.19/hr; Worker n1-standard-4: ~$0.19/hr each
# 4 nodes × $0.19 × 24h ≈ $18/day if left running
echo "Reminder: delete the cluster when done, or set a deletion schedule."
```

---

## 🔑 Key Takeaways

- Big Data is about workload shape, not just size: unbounded data, full scans, unknown schemas,
  long-running jobs, spiky capacity.
- Hadoop MapReduce solved volume through horizontal scale, but its disk-between-stages model and
  single MapReduce programming model made it slow and rigid.
- Spark replaced MapReduce with an in-memory, multi-stage, multi-language engine and the
  Catalyst-optimized DataFrame API.
- Dataproc is Google’s managed Spark: it removes cluster operations and integrates natively with
  GCS, BigQuery, IAM, Monitoring, Logging, and Composer.
- **Temporary clusters are the default choice for batch ETL** — pay only while the job runs.
- **Always pin `--image-version`.** It controls your Spark and Python versions.
- **Always set a cluster deletion schedule.** Forgotten clusters are the #1 surprise bill.
- Learn RDDs to understand them; write DataFrames in production.

---

## 📚 Practice Exercises

1. **Vertical vs horizontal.** Describe a workload from your own job that would be painful on a
   single server. Identify the specific assumption it breaks (volume, velocity, variety,
   veracity) and what the distributed design would look like.

2. **MapReduce vs Spark.** Write the equivalent of: given a directory of JSON event logs, count
   events per user per day and sum the `amount` field. Write it as (a) a MapReduce job in
   pseudocode, (b) a PySpark DataFrame script. Count the lines. Explain where the 10× comes from.

3. **Cost modeling.** Price a Dataproc cluster with 1 master (`n1-standard-4`) and 4 workers
   (`n1-standard-4`) running 24 hours/day vs. 8 hours/day. What changes if you switch workers to
   `preemptible`? What is the risk, and how does Spark mitigate it?

4. **Image version audit.** List the Dataproc image versions available to you. For the newest 2.x
   version, find its Spark version and Python version. Explain what would break if your team
   silently moved to a newer image.

---

## 📖 Further Reading

- Apache Spark architecture — https://spark.apache.org/docs/latest/architecture.html
- Dataproc overview — https://cloud.google.com/dataproc/docs/overview
- Dataproc image versions — https://cloud.google.com/dataproc/docs/concepts/versioning/dataproc-image-versions
- Dataproc pricing — https://cloud.google.com/dataproc/pricing
