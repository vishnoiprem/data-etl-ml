# 07 · Quiz 1 — GCP and the Big Data Ecosystem

> **Section 1 · Introduction to Google Cloud Platform · Lectures 1–6**

Ten questions covering the GCP services, the BigQuery ecosystem, and where BigQuery
sits. Answers and reasoning are at the bottom — try to answer first.

---

## 📝 Questions

**1. Service mapping.** For each workload, name the GCP service you would reach for
and one you would explicitly avoid:

   - (a) Petabyte-scale object storage for a data lake
   - (b) Serverless SQL analytics over that lake
   - (c) Streaming event ingestion from thousands of producers
   - (d) Long-running batch transformations written in Python

**2. The BigQuery architecture.** BigQuery is described as serverless. Name the two
internal subsystems that replace the components a traditional warehouse runs itself,
and what each one is responsible for.

**3. Compute equivalence.** BigQuery bills work in *slots*, where one slot is one vCPU
and 4 GB of RAM. A query touches 1,000 slots for 6 hours. How many slot-hours is that,
and at the Standard Edition rate of $0.04 per slot-hour, what does it cost?

**4. Region vs multi-region.** Give one workload that belongs in a **regional**
dataset and one that belongs in a **multi-region** dataset, and state the trade-off
you are making in each case.

**5. The serverless bargain.** What does "serverless" actually give you in BigQuery —
and what does it *not* give you?

**6. Dataflow vs BigQuery.** A team has a complex transformation: fuzzy matching,
sessionization, and custom windowing. A second team has simple aggregations over a
2 TB table. Which goes to Dataflow, which goes to BigQuery, and why?

**7. Pub/Sub's role.** Why would you put Pub/Sub in front of BigQuery rather than
loading directly into BigQuery's streaming API?

**8. Cloud Composer.** What is Composer, and what does it cost you beyond the Airflow
DAG itself?

**9. Slot sharing.** Two teams in the same organisation each run queries. Explain how
capacity pricing (slots) can cost both teams *less* than on-demand pricing, using the
concept of a slot baseline.

**10. One more service.** Name a GCP service you would use to track data quality,
and one you would use to serve a BI dashboard on top of BigQuery.

---

## ✅ Answers

**1. Service mapping.**

   - (a) **Cloud Storage** — the cheap, durable object store a data lake sits on.
     Avoid: Cloud SQL, which is relational and priced per-instance.
   - (b) **BigQuery** — for managed SQL over object storage, or **BigLake** for open
     tables on GCS. Avoid: running raw Spark for a simple aggregate.
   - (c) **Pub/Sub** — the managed ingestion backbone. Avoid: pushing directly into
     BigQuery if you need fan-out to multiple consumers.
   - (d) **Dataflow** — managed Apache Beam for unbounded, non-SQL transformations.
     Avoid: Dataflow for a query BigQuery can express in SQL.

**2. The BigQuery architecture.**
   - **Colossus** — the distributed, columnar storage layer. It replaces the
     traditional shared-nothing storage cluster, so there is no NameNode to
     bottleneck or fail.
   - **Dremel** — the execution engine. It breaks a query into a tree of operators
     scheduled across slots, replacing the query-planning and execution machinery
     a warehouse runs itself.

**3. Slot arithmetic.** 1,000 slots × 6 hours = **6,000 slot-hours**.
   At $0.04 per slot-hour: 6,000 × $0.04 = **$240.00**.

**4. Region vs multi-region.**
   - **Regional** — a table with EU-resident personal data that must stay in the EU.
     You trade away the ability to run one query across two regions, but you get
     lower latency and keep data residency.
   - **Multi-region** — a global reporting table queried by users on three
     continents. You trade a small amount of extra latency for a single copy that
     any region can serve.

**5. The serverless bargain.** You get **no cluster to size, provision, patch, or
   babysit** — capacity scales to the query automatically, and you pay only for the
   work done. What you *do not* get: control over the physical layout, guaranteed
   dedicated resources (that is what capacity pricing buys), or the ability to run
   a long-lived cluster you tune yourself. "Serverless" means someone else operates
   the cluster — not that there isn't one.

**6. Dataflow vs BigQuery.**
   - **Dataflow** for the first team. Fuzzy matching and sessionization have no
     clean SQL expression; Beam gives you per-element transforms, stateful
     processing, and windowing triggers.
   - **BigQuery SQL** for the second. A 2 TB aggregation is exactly what BigQuery is
     built for — it will be faster, simpler, and cheaper than a Beam pipeline.

**7. Pub/Sub's role.** Pub/Sub decouples producers from consumers. It gives you
   **fan-out** (many independent consumers of one event stream), **buffering** (a
   slow consumer does not block the producer), **retry and dead-letter handling**
   for free, and **ordering keys** for per-entity ordering. BigQuery's streaming API
   gives you none of those — it is a direct write path.

**8. Cloud Composer.** Composer is a **managed Apache Airflow** environment. Beyond
   the Airflow control plane it costs you the Cloud SQL instance behind it, the
   GCS bucket for DAGs, the worker(s) that run your tasks, and the networking and
   logging around them. You trade infrastructure management for a smaller bill.

**9. Slot sharing.** With on-demand, each team pays for the bytes *it* scans, so two
   teams scanning the same table twice pay twice. With capacity pricing you commit
   to a slot baseline and provision it **once per organisation**; teams share that
   baseline and consume from it. If your combined stable utilisation exceeds the
   committed slot cost, you win — and you also get predictable bills and reserved
   capacity.

**10. One more service.**
   - **Data quality** — Dataplex (catalog, lineage, data quality monitoring) or
     BigQuery-native DQ checks in your pipeline.
   - **BI dashboard** — Looker Studio (Looker), optionally with a **BI Engine
     reservation** so dashboard queries run against a dedicated copy instead of
     your on-demand slot pool.

---

## 🔑 Key Takeaways

- BigQuery = **Colossus** (storage) + **Dremel** (execution). No NameNode.
- One slot = 1 vCPU + 4 GB. 1,000 slots × 6 h = 6,000 slot-hours = $240.
- **Serverless** removes cluster operations — not resource control.
- **Pub/Sub** decouples and buffers; **Dataflow** transforms; **BigQuery** queries.
- **Composer** is managed Airflow — and it is not free.
- Capacity pricing wins when *shared* stable utilisation beats the commitment.

---

## 📚 Next

[08 · What is BigQuery](./08-what-is-bigquery.md)
