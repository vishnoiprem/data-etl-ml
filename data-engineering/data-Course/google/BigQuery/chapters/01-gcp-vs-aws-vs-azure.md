# 1.1 — GCP vs AWS vs Azure: Why Choose GCP

> **Section 1 · Introduction to Google Cloud Platform · Lecture 1.1 · 6:03**

## 🎯 What you will learn

- The three hyperscalers at a glance, and what actually differs between them
- GCP's core differentiators: network, data analytics, and AI
- When GCP is the right choice — and when it is not
- A concrete decision framework for platform selection

---

## 🧠 Concept

Every data engineering course eventually has to answer the uncomfortable question: **"Why are we on
this cloud, and not the other one?"**

The honest answer is that the three hyperscalers are more similar than their marketing suggests.
All three offer object storage, managed VMs, serverless compute, managed Kubernetes, serverless
queues, and a managed analytics warehouse. The differences are real, but they are differences of
*emphasis*, not of *capability*.

### The landscape at a glance

| Dimension | Google Cloud | AWS | Azure |
|-----------|-------------|-----|-------|
| **Core strength** | Data & AI at scale | Breadth & maturity | Enterprise hybrid |
| **Network** | Closest to users (private global backbone) | Largest backbone, 1st mover | Strong SD-WAN / enterprise footprint |
| **Managed warehouse** | BigQuery | Redshift + Athena | Synapse / Fabric |
| **Streaming** | Pub/Sub (global, at-least-once) | Kinesis | Event Hubs |
| **Batch** | Dataflow (Beam-based) | EMR / Glue | HDInsight / Fabric |
| **Orchestration** | Cloud Composer (Airflow) | MWAA (Airflow) | Data Factory (Airflow) |
| **Kubernetes** | GKE (autopilot) | EKS | AKS |
| **Serverless containers** | Cloud Run | Lambda / Fargate | Container Apps / Functions |
| **AI/ML platform** | Vertex AI — deep ML tooling | SageMaker | Azure ML |
| **Generative AI** | Gemini across the portfolio | Bedrock | Azure OpenAI |
| **Identity** | Cloud IAM | IAM | Entra ID (AD) |
| **Hybrid story** | Anthos, Config Connector | Outposts, EKS Anywhere | Arc, Stack HCI — strongest |
| **Enterprise legacy** | Newer / smaller installed base | Largest | Largest non-AWS |

### GCP's three real differentiators

**1. The network.** Google owns one of the largest private backbones in the world, and routes
traffic between its own data centers over it. This is not marketing — it is why GCP has historically
offered strong egress pricing and why traffic between GCP regions avoids the public internet. If
your workload is data movement at petabyte scale, the network is part of your bill and GCP is
genuinely competitive on it.

**2. BigQuery.** BigQuery is not "a warehouse in the way Redshift is a warehouse." It is a
**serverless, columnar, massively parallel, pay-per-scan** analytical engine that separates storage
from compute. That one design decision eliminates the two most expensive problems in traditional
warehousing: cluster sizing and data loading. It also means a query can scale to thousands of slots
in seconds, with no prior capacity planning.

**3. AI integration.** Because Google owns the models, the TPU hardware, and the research, Vertex AI
and Gemini are not bolt-ons. They are first-class services with tight integration into the data
platform — and Google was the first major cloud to publish a full set of management and governance
controls (Vertex AI Model Registry, Data Catalog, Data Governance) covering both data and models.

### Where GCP is *not* the right answer

Be honest about this in a design doc:

- **Deepest enterprise hybrid footprint** → Azure. If you run a large estate of on-premises
  Windows Server, SQL Server, and Active Directory, Entra ID integration and Arc are more mature
  than anything GCP offers.
- **Broadest service catalog and longest track record** → AWS. When you need the most exotic
  service, AWS usually has it.
- **Strongest compliance certification breadth for specific geographies** → varies; check the
  compliance list directly rather than assuming.

---

## 🛠️ Hands-On: Compare Pricing Models

Cost is usually the deciding factor, so let's compare a concrete workload.

### The workload

A monthly analytics workload:
- 2 TB of raw events landing in Cloud Storage
- 5 TB of raw events landing in BigQuery
- 50 TB of raw events **scanned** by BI dashboards and ad-hoc queries
- 200 GB of active data queried with a 30-day expiry

### GCP (BigQuery on-demand)

```
Storage (BigQuery, active):   5 TB  × $0.02 / GB-month  = $102.40 / month
Storage (BigQuery, long-term): 0 TB  (under 1 TB free tier)
Storage (GCS, Standard):       2 TB  × $0.020 / GB-month = $ 41.94 / month
Query on-demand:              50 TB  × $6.25 / TiB       = $312.50 / month
                                     (1 TiB free each month → −$6.25)
Total ≈ $450 / month
```

### AWS (Redshift Serverless + Athena)

```
Redshift Serverless:   200 GB × $0.05 / GB-month = $10.00 / month
Athena queries:         50 TB × $5.00 / TiB       = $250.00 / month
S3 Standard:            2 TB  × $0.023 / GB-month = $ 47.09 / month
Total ≈ $307 / month
```

### Azure (Fabric / Synapse)

```
Fabric OneLake storage:  2 TB  × $0.023 / GB-month = $47.09 / month
Warehouse compute:      200 GB, ~$30-60 / month (capacity tier dependent)
Warehouse storage:      200 GB × $0.021 / GB-month = $ 4.20 / month
Query on-demand share:  charged via capacity, not directly comparable
Total ≈ $95-150 / month
```

> ⚠️ **Do not treat this as a verdict.** The comparison is apples-to-oranges in one important way:
> AWS and Azure numbers here reflect **capacity-based** or **pre-bought** pricing, while BigQuery is
> purely **usage-based**. On a workload that spikes, BigQuery wins decisively. On a steady,
> always-on workload, reserved capacity can beat on-demand BigQuery — which is why BigQuery also
> offers **slot commitments** (1-year and 3-year) and **capacity editions**.

💡 **The real lesson:** price the *query pattern*, not the storage. Storage is cheap and roughly
comparable everywhere. Querying is where the bills diverge, and query cost is a function of
**bytes scanned** — a number you control directly through partitioning, clustering, and table
design.

---

## 💡 The decision framework

Ask these five questions in order:

1. **Is this workload analytical (OLAP) or operational (OLTP)?**
   BigQuery is OLAP. If you need sub-10ms row-level updates and transactional integrity, you want
   Cloud SQL / AlloyDB, not BigQuery.

2. **How much data, and how often is it scanned?**
   Scanned-bytes cost dominates. Highly repetitive scans of the same data reward materialized views
   and slot commitments.

3. **What is your latency tolerance?**
   BigQuery query latency is seconds. Sub-100ms serving → Bigtable / Spanner / Cloud SQL.

4. **What is the organizational context?**
   Existing Azure estate, existing AWS skills, existing on-prem — the platform your team already
   operates well is usually cheaper than a nominally better one.

5. **Do you need real-time streaming ingestion at volume?**
   GCP's Pub/Sub + Dataflow combination is genuinely excellent. So is Kinesis + Flink on AWS.

---

## 🔑 Key Takeaways

- GCP's edge is **data + AI + network**; AWS's is **breadth + maturity**; Azure's is **enterprise hybrid**.
- BigQuery's serverless, pay-per-scan model removes cluster sizing and data loading entirely.
- Storage pricing is broadly comparable; **query pricing is where the differences live**.
- Always compare **capacity-based vs on-demand** fairly, and price the *scan pattern*.
- Choose the platform your team can operate well — "best cloud" is a false frame.

---

## 📚 Practice Exercises

1. **Cost model.** Take the workload above, change it to 500 TB scanned/month, and recompute for all
   three platforms. At what scan volume does BigQuery on-demand exceed a 1-year slot commitment?

2. **Service mapping.** Produce a table mapping each of these GCP services to its AWS and Azure
   equivalent, and note any *capability gap*:
   `BigQuery`, `Dataflow`, `Pub/Sub`, `Composer`, `Dataplex`, `Dataform`, `Bigtable`, `Spanner`,
   `Filestore`, `Cloud Run`, `GKE Autopilot`, `Vertex AI`.

3. **Hybrid reality check.** Your company has 400 on-prem SQL Servers and Active Directory. Write a
   200-word argument for and against choosing GCP for a new analytics platform, and give a verdict.

4. **Migration scenario.** Outline what changes if you migrate a Redshift workload to BigQuery:
   cluster sizing disappears, but what new *design* obligations appear (partitioning, clustering,
   table formats)?

---

## 📖 Further Reading

- Google Cloud Architecture Framework — https://cloud.google.com/architecture
- BigQuery Pricing — https://cloud.google.com/bigquery/pricing
- AWS vs GCP vs Azure comparisons — https://cloud.google.com/architecture/compare
