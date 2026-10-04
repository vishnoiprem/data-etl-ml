# Katalon — Head of Data: Interview Prep Guide

> One file. Deep but memorable. Every technology in the job description gets: **hook** (one line to remember) -> **cheat card** (the facts) -> **questions with model answers** -> **trap** (what weak candidates say).

Legend (CP AXTRA palette): 🔵 hook / remember this · 🟡 tip · 🟢 model answer · 🔴 trap / red flag

---

## 0. How to use this file

1. Day 1: read Sections 1-5 (mnemonic, company, frameworks, 100-day plan, strategy). That alone gets you through the strategy round.
2. Day 2-3: one technology section per sitting. Read the hook, say the cheat card out loud, then answer each question **without looking** and compare.
3. Day 4: Section 21 (stories) — fill every `[f]` with your own real numbers. Model answers below use **illustrative numbers**; never say a number in the interview that is not yours.
4. Last hour before: Section 23 (flashcards) and Section 22 (questions to ask).

🟡 The model answers are written to be spoken in 60-90 seconds. Practice them out loud; written answers sound different from spoken ones.

---

## 1. The memory spine: **K-A-T-A-L-O-N**

Every answer you give should land on one letter. If you blank, ask yourself "which letter is this question?"

| Letter | Meaning | Job-description line it covers |
|---|---|---|
| **K** | **K**now the business (strategy, KPIs, ROI) | "Define and execute enterprise data strategy" |
| **A** | **A**rchitecture (platform) | "Build and scale modern data platforms" |
| **T** | **T**ooling (Snowflake/Databricks, AWS, Airflow, Kafka, SQL, Python) | "Technical Expertise" |
| **A** | **A**I and ML (MLOps, GenAI, RAG, experimentation) | "Drive adoption of ML, GenAI" |
| **L** | **L**aw and governance (GDPR, CCPA, quality, security, Responsible AI) | "Establish data governance, quality, security, privacy" |
| **O** | **O**rganization (team, stakeholders, culture) | "Build, mentor, lead a Data team", "Partner with Product, Eng, Mktg, Sales, CS" |
| **N** | **N**umbers (measurable impact, cost, adoption) | "Measurable business impact" |

🔵 **One sentence that sums up the role:** *"A Head of Data turns raw product and customer events into trusted decisions and AI features, safely and cheaply, through a team people want to join."*

### The 3 things Katalon is really hiring for

1. **A builder-leader**, not a manager of managers: they say "scalable data pipelines, KPIs, executive dashboards" and "Airflow, Kafka, SQL, Python" — expect to be asked how you would do it yourself.
2. **An AI-readiness owner**: "AI-ready data", "RAG", "vector DB", "Responsible AI". Katalon sells AI-augmented testing, so data quality is literally part of their product.
3. **A cross-functional translator** who can talk to a CFO about cost, a lawyer about GDPR, and an engineer about partitions in the same afternoon.

---

## 2. Know the company in 2 minutes (say this back to them)

**Who they are:** Founded 2016, "category leader in AI-augmented software testing", 30,000+ teams, 80+ countries, many in the Fortune Global 500. Tagline: serving *hybrid testers* (manual + automation + AI).

**What data they almost certainly have** (state as a hypothesis, then ask them to correct you — that shows structure and humility):

| Domain | Likely sources | Questions the business asks |
|---|---|---|
| Product usage | Test runs, test case creation, execution results, IDE/plugin telemetry, CI/CD integrations | Which features drive retention? What does an "activated team" look like? |
| Commercial funnel | Website, free-trial/free-tier signups, CRM (e.g. Salesforce), marketing automation, billing | Which channels produce paying teams? Trial -> paid conversion by segment? |
| Customer success | Support tickets, NPS/CSAT, health scores, renewals | Which accounts churn and why? Where is expansion? |
| AI features | Prompts, suggestions accepted/rejected, latency, cost | Is the AI assistant improving productivity or just being clicked? |
| Corporate | Finance, HR, G2 reviews, community forums | ARR, NRR, CAC payback, cost of cloud |

🔵 **Hook: "Land, adopt, expand."** In B2B SaaS the data story is: *land* (signup/trial) -> *adopt* (running tests weekly) -> *expand* (more seats/modules) -> *renew*. Every KPI maps to one of these four words.

🟡 Tip: Do not claim to know their stack. Say: *"I'd expect a PLG-plus-sales motion with product telemetry plus CRM; before I recommend anything I'd want to confirm what's actually there."*

---

## 3. Answer frameworks (memorize two)

### 3.1 Technical / design questions: **C-C-T-M**

**C**ontext (clarify the goal + scale) -> **C**hoice (what I would pick) -> **T**rade-off (what I give up, what else I considered) -> **M**etric (how I know it worked).

> 🟢 Example, "Snowflake or Databricks?" — *"Depends on the workload mix [Context]. For BI-heavy analytics with a small team I'd lean to a SQL warehouse; for heavy ML and streaming, a lakehouse [Choice]. The trade-off is lock-in and cost model, which I'd soften with open table formats like Iceberg [Trade-off]. I'd judge it on query cost per dashboard, time-to-new-dataset, and analyst satisfaction [Metric]."*

### 3.2 Behavioral / leadership questions: **STAR-R**

**S**ituation (1 sentence) -> **T**ask (what was mine) -> **A**ction (what *I* did, 3 specific steps) -> **R**esult (number) -> **R**eflection (what I'd change).

🔴 Trap: "we" for ten minutes. Interviewers score the "I".

### 3.3 Strategy questions: **W-N-N**

**W**hat is true today -> **N**ear-term wins (0-90 days) -> **N**orth-star (12-24 months). Always show a quick win *and* a long bet.

---

## 4. The 30-60-90 / 100-day plan (have this ready; they will ask)

| Window | Theme | Concrete deliverables |
|---|---|---|
| **Days 1-30: Listen** | Learn, don't change | 1:1 with every function head; inventory of sources, pipelines, dashboards, cost, access; list "top 10 decisions this company makes weekly and what data they use"; pick the 5 KPIs everyone argues about |
| **Days 31-60: Fix & prove** | One visible win | Single trusted definition for 3-5 exec KPIs (e.g. ARR, activation, NRR); data-quality SLOs on Tier-1 tables; cost baseline for the platform; 1 quick-win dashboard replacing a spreadsheet |
| **Days 61-100: Plan & hire** | Strategy and team | 12-month data and AI roadmap (now/next/later) with cost and ROI; governance charter (owners, stewards, PII classification); hiring plan; one AI pilot with a measurable success metric |

🔵 **Hook: "Listen, Fix, Plan."** Never propose a platform re-architecture in the first 30 days.

### Q: "What would you do in your first 90 days?"

🟢 *"First 30 days I listen: every function head, plus an inventory of sources, pipelines, dashboards, and spend. I ask what are the ten decisions made every week and what data backs them. Days 30-60 I fix what hurts most and prove value: one agreed definition for the executive KPIs, quality checks on the Tier-1 tables, and a cost baseline. By day 100 I present a now-next-later roadmap for data and AI with cost and ROI, a governance charter, a hiring plan, and one AI pilot with a measurable success metric. I avoid big migrations early because trust is built by small, visible wins."*

🔴 Trap: "I'd migrate everything to X" in the first answer.

---

## 5. 🟦 K — Strategy & business impact

🔵 **Hook: "Decisions, not dashboards."** A data strategy is the list of decisions the company needs to make better, and the minimum data/AI capability to make them.

### Cheat card — the 5-layer data strategy

```
5. VALUE      -> use cases with owners and $ targets (churn, activation, pricing, AI features)
4. ENABLE     -> self-service, semantic layer, experimentation, ML platform
3. GOVERN     -> quality, security, privacy, AI governance
2. PLATFORM   -> ingest, store, transform, serve (cloud, orchestration, streaming)
1. PEOPLE     -> team shape, skills, operating model
```
Build bottom-up, **prioritise top-down**: choose the value use case first, then the thinnest platform slice that supports it.

### Q1. "How do you define a data strategy for a company like Katalon?"

🟢 *"I start from the business goals — growth, retention, product differentiation with AI — and translate each into decisions that data should improve. For a testing-software company, examples are: which trial teams will convert, which accounts are at risk, which AI features customers actually use, and what we can safely learn from usage to improve the product. For each decision I define an owner, a metric, and the minimum data needed. That produces a prioritised use-case list. Then I size the platform and governance work needed for the top five, not for everything. I review it quarterly against outcomes: revenue influenced, hours saved, cost to serve."*

🔴 Trap: starting with technology ("we need a lakehouse").

### Q2. "How do you prove data is delivering ROI?"

🟢 *"Three buckets. Revenue: conversion lift, expansion, churn reduction attributed with a control group where possible. Efficiency: analyst hours saved, report requests deflected by self-service, infrastructure cost per query. Risk: audit findings, privacy incidents, data-quality incidents avoided. I agree the baseline with Finance before the project starts, so the number is credible. Example: if a churn model gives CS a ranked list and the contacted group retains 3 points better than a holdout, with average ARR of [X], I can compute the dollars."*

### Q3. "How do you prioritise competing requests from Sales, Marketing and Product?"

🟢 *"One intake, one scoring model. I use impact × confidence ÷ effort (RICE-style), with a mandatory field: 'what decision changes if we have this?'. Anything that is a one-off question goes to self-service; anything strategic goes to the roadmap. I publish the ranked backlog so trade-offs are transparent, and I reserve about 20% capacity for platform health so the team isn't only firefighting."*

### Q4. "What is your North Star metric for a testing platform?"

🟢 *"I'd propose something like 'weekly active teams executing automated tests', because it captures both adoption and real value — people only run tests regularly if the product works for them. Supporting metrics: activation (first successful test run within 7 days), depth (tests per team, CI integrations), and retention (4-, 8-, 12-week). Commercial layer: trial-to-paid, NRR, expansion. I would validate by checking that this metric predicts renewal."*

🟡 Tip: always say "I'd validate that it predicts the outcome" — shows scientific mindset.

### Q5. "Build vs buy for data tools?"

🟢 *"Buy commodity, build differentiators. Ingestion connectors, orchestration hosting, observability are usually buy — unless cost at scale flips it. Build where the data is the product edge: AI features, domain-specific models, key metrics logic. Decision rubric: strategic differentiation, total cost over 3 years including people, time to value, lock-in/exit cost, security fit. I document it in a one-page decision record."*

---
## 6. 🟦 A/T — Modern data platform (Snowflake / Databricks / BigQuery / Redshift)

🔵 **Hook: "Ingest -> Store -> Transform -> Serve -> Observe."** Five verbs; every architecture question is one of them.

### Cheat card — reference architecture for a SaaS company this size

```
SOURCES            INGEST              STORE (raw -> clean -> mart)        SERVE
product events --> Kafka/Kinesis -----> S3 / warehouse  [bronze]            BI (dashboards)
SaaS apps (CRM,  > Fivetran/Airbyte --> clean, conformed [silver]           reverse ETL -> CRM
 billing, support)  CDC (Debezium)      business marts    [gold]            feature store -> ML
app DBs ---------> CDC / snapshots      + semantic layer                    vector DB -> RAG/AI
                         \                   |                              APIs / notebooks
                          ORCHESTRATION (Airflow)  ·  TRANSFORM (dbt/SQL/Spark)  ·  CATALOG + LINEAGE
                          QUALITY  ·  SECURITY (RBAC, masking)  ·  COST (FinOps)  ·  OBSERVABILITY
```

**Medallion layers:** bronze = raw, immutable, replayable · silver = cleaned, deduped, typed, conformed keys · gold = business-ready marts with agreed metric definitions.

### Cheat card — the four platforms in one table

| | Snowflake | Databricks | BigQuery | Redshift |
|---|---|---|---|---|
| **Sweet spot** | SQL analytics, easy ops, data sharing | Lakehouse: ML, streaming, big ETL, open formats | Serverless analytics on GCP | Analytics deep in AWS |
| **Compute model** | Virtual warehouses (credits), per-second | Clusters / SQL warehouses (DBUs) | On-demand per TB scanned or slot reservations | RA3 nodes or Serverless (RPUs) |
| **Storage** | Managed (or Iceberg tables) | Open: Delta/Iceberg on your object store | Managed | Managed (RA3 managed storage), Spectrum for S3 |
| **Cost levers** | auto-suspend, right-size, resource monitors, query tags | job clusters not all-purpose, spot, Photon, autoscaling | partition + cluster, require partition filter, slots | RA3 + concurrency scaling, WLM, Spectrum |
| **Watch out** | cost creep from always-on / big warehouses | ops complexity, cluster sprawl | scan-cost surprises | tuning (sort/dist keys) and concurrency |

🔵 **Hook: "SQL-first -> Snowflake; ML-first -> Databricks; GCP -> BigQuery; AWS-only simple -> Redshift."**

### Q1. "Snowflake vs Databricks — which would you choose for Katalon and why?"

🟢 *"I'd want three facts first: the team's skill mix, the workload mix (BI vs ML vs streaming), and where the data already lives. Katalon likely has a lot of product telemetry plus CRM/billing data and AI ambitions. If most consumers are analysts and the AI work is mostly applied — RAG, scoring models — a SQL-centric warehouse with dbt gets value fastest and is simpler to operate. If there's heavy streaming, large-scale feature engineering, or model training on raw events, a lakehouse is more natural. The two are converging anyway — both support Iceberg, both have vector search and LLM functions — so I'd reduce lock-in by storing data in open table formats and keeping transformation logic in dbt/SQL rather than in proprietary procedures. I'd decide with a two-week proof of concept on three real queries and judge cost per query, time-to-first-dashboard, and developer experience."*

🔴 Trap: picking by brand. 🟡 Say "what is already there? migration is rarely worth it."

### Q2. "How do you control cloud data cost?"

🟢 *"Make cost visible, then make it somebody's job. Tag every query and pipeline by team and use case so we can show cost per domain and per dashboard. Quick wins: auto-suspend warehouses after 60 seconds idle, right-size, move heavy jobs to scheduled windows, cluster or partition large tables, kill unused tables and dashboards (find them from query history), use incremental models instead of full refreshes, and set budgets and alerts with resource monitors. Longer term: storage lifecycle policies on S3, tiering cold data, reserved capacity once usage is predictable. I report unit cost — dollars per 1,000 queries or per active user — because absolute cost grows with success."*

### Q3. "Walk me through designing the platform from scratch."

🟢 *"Use C-C-T-M. Context: sources, volumes, latency needs, and consumers. Choice: land raw data in object storage and the warehouse (bronze), standardise in silver, publish business marts in gold, orchestrated by Airflow, transformed with dbt, with a semantic layer on top so metrics are defined once. Streaming only where latency matters — product events for in-app features or alerting — everything else is batch. Governance is built in, not bolted on: a catalog with lineage, PII tags that drive masking policies, role-based access, and quality tests on every model. Trade-off: I deliberately don't build real-time everywhere because it costs ~3-5x in complexity. Metrics of success: data freshness SLA met, % of queries on certified models, cost per query, and time to onboard a new source (target under a week)."*

### Q4. "Data lake vs warehouse vs lakehouse?"

🟢 *"Lake = cheap object storage, flexible, any format, but weak governance and performance unless you add structure. Warehouse = structured, fast SQL, strong governance, costlier for unstructured or ML-heavy data. Lakehouse = lake storage with table formats (Delta, Iceberg, Hudi) adding ACID transactions, schema evolution, time travel — so one copy serves BI and ML. Practical answer: structured business analytics in a warehouse, plus open table formats so ML/AI can read the same data without copies."*

### Q5. "How do you do schema changes without breaking everything?"

🟢 *"Data contracts at the producer boundary: a versioned schema, owner, and SLA. Additive changes are backward compatible; breaking changes need a new version and a deprecation window. Schema registry for events, CI checks on dbt models that fail the build if a downstream column vanishes, and lineage to see who's impacted. Producers get an alert before they ship, not consumers after."*

---

## 7. 🟦 T — AWS (preferred cloud)

🔵 **Hook: "S3 is the lake, Glue is the catalog, IAM is the gatekeeper, KMS is the lock."**

### Cheat card — the AWS data map

| Need | AWS service | One-line use |
|---|---|---|
| Object storage / lake | **S3** (+ Intelligent-Tiering, lifecycle) | Raw + curated, parquet/iceberg |
| Catalog / ETL | **Glue** (Data Catalog, crawlers, Spark jobs) | Table metadata; serverless Spark |
| Governance | **Lake Formation** | Column/row-level permissions, LF-tags |
| Warehouse | **Redshift** (RA3 / Serverless) | Analytics; Spectrum queries S3 |
| Ad-hoc query | **Athena** | Serverless SQL on S3, pay per TB scanned |
| Streaming | **Kinesis** / **MSK** (managed Kafka) | Events in; Firehose to S3 |
| Orchestration | **MWAA** (managed Airflow) / Step Functions | Schedules and dependencies |
| CDC from DBs | **DMS** | Replicate RDS/Aurora into lake |
| ML | **SageMaker** (+ Feature Store, Model Registry) | Train, deploy, monitor |
| GenAI | **Bedrock** (+ Knowledge Bases), OpenSearch / pgvector | Managed LLMs + RAG |
| Security | **IAM, KMS, Secrets Manager, CloudTrail, Macie, VPC endpoints** | Access, encryption, audit, PII discovery |

### Security checklist (speak it as a list)
Least-privilege IAM roles (no long-lived keys) · S3 block public access · encryption at rest (KMS, per-domain keys) and in transit (TLS) · VPC endpoints so data never traverses public internet · CloudTrail + S3 access logs for audit · Macie for PII discovery · separate accounts for prod/dev (AWS Organizations) · tag-based access control.

### Q1. "Design a lake on AWS for product event data."

🟢 *"Events arrive via Kinesis or MSK and Firehose writes partitioned parquet to S3 raw (partitioned by event_date and maybe event_type — never by high-cardinality user_id). Glue Data Catalog registers tables; Lake Formation applies tags such as pii=true to restrict columns. A Glue or dbt job produces silver (deduped on event_id, typed, bad-record quarantine) and gold marts loaded to Redshift or queried through Athena. Orchestrated by MWAA. S3 lifecycle moves raw older than 90 days to Intelligent-Tiering or Glacier Instant. Files compacted to ~128-512 MB to avoid the small-file problem."*

### Q2. "Redshift vs Athena vs Snowflake on AWS?"

🟢 *"Athena for occasional ad-hoc queries on S3 — no cluster, pay per scan, great with partitioned parquet. Redshift when you have steady, concurrent BI load and want predictable performance and tight AWS integration. Snowflake runs on AWS too and wins on operational simplicity, workload isolation, and data sharing, at a premium. I'd choose by concurrency, team skills, and total cost of ownership, not by whether it carries the AWS logo."*

### Q3. "How do you secure PII in an AWS data platform?"

🟢 *"Defence in depth. Discover: Macie scans S3 and I classify columns. Minimise: don't ingest PII we don't need; hash or tokenise at ingestion. Protect: KMS encryption with separate keys per domain, columns tagged pii and exposed only through masked views to analysts. Control: Lake Formation tag-based access, roles per job function, no direct S3 access for humans. Audit: CloudTrail plus access reviews every quarter. Respond: a tested runbook for deletion requests and incidents."*

### Q4. "S3 small files problem?"

🟢 *"Millions of tiny files kill query planning and increase S3 request cost. Fix upstream by batching writes (Firehose buffer by size/time), and downstream by scheduled compaction to 128-512 MB parquet or by using table formats like Iceberg/Delta with compaction. Also avoid over-partitioning: partitioning by hour and user results in many small partitions."*

---

## 8. 🟦 T — Airflow (orchestration)

🔵 **Hook: "Airflow orchestrates — it does not compute."** Schedule, order, retry, alert. Heavy work runs in the warehouse/Spark.

### Cheat card

- **DAG** = tasks + dependencies, scheduled by `data_interval` (a run for a *period*, not "now").
- **Idempotent task** = running it twice for the same interval gives the same result (use `MERGE`/overwrite partition, not blind `INSERT`).
- **Backfill** = rerun history; works safely only if tasks are idempotent and parameterised by the interval.
- **Sensors** wait for something; use **deferrable operators** so they don't hog worker slots.
- **XCom** = tiny metadata only (IDs, paths), never data frames.
- **Pools** limit concurrency against a fragile system; **retries with backoff** for transient failures; **SLAs/alerts** for lateness.
- **Datasets (data-aware scheduling)**: run downstream when upstream data updates, instead of guessing times.
- **Dynamic task mapping**: fan out one task per file/tenant at runtime.
- Alternatives: Dagster (asset-centric, strong testing), Prefect (Pythonic, simpler). Managed: MWAA, Astronomer, Cloud Composer.

### A tidy DAG skeleton (know how to write this)

```python
from airflow.decorators import dag, task
from pendulum import datetime

@dag(
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,                      # don't auto-run all missed intervals
    max_active_runs=1,
    default_args={"retries": 3, "retry_delay": 300, "retry_exponential_backoff": True},
    tags=["product", "tier1"],
)
def product_events_daily():
    @task
    def extract(data_interval_start=None, data_interval_end=None):
        # pull exactly one interval, write to s3://.../dt={ds}/ (overwrite = idempotent)
        ...

    @task
    def load_to_warehouse(path):
        # MERGE INTO silver USING staging ON event_id  (idempotent)
        ...

    @task
    def run_quality_checks():
        # row-count, null, uniqueness, freshness -> fail the run if breached
        ...

    run_quality_checks() << load_to_warehouse(extract())

product_events_daily()
```

### Q1. "How do you make pipelines reliable?"

🟢 *"Five habits. Idempotency — every load is a MERGE or partition overwrite, so retries and backfills are safe. Small, single-purpose tasks so a failure is easy to locate. Data-quality gates between layers: if the check fails the run stops and alerts rather than publishing bad data. Retries with exponential backoff for transient errors only; failures page the owner, with a runbook. Monitoring on freshness and row-count anomalies, not just 'task succeeded', because a green DAG can still produce wrong data."*

### Q2. "How do you backfill two years of data?"

🟢 *"Make sure the DAG uses the logical `data_interval` rather than `now()`, confirm tasks are idempotent, then run in controlled batches with `max_active_runs` and pools capped so I don't overload the source or warehouse. I backfill into a shadow table first, reconcile row counts and checksums against the source, then swap. I communicate to downstream owners the time window and any metric restatement."*

### Q3. "Airflow vs dbt vs Dagster?"

🟢 *"Different jobs. dbt transforms data inside the warehouse and tracks lineage and tests; Airflow orchestrates across systems — ingestion, dbt runs, ML jobs, notifications. Dagster models 'assets' rather than tasks, which makes lineage and testing more natural, but Airflow's ecosystem and hiring pool are larger. I'd stay on Airflow if it's already there and use cosmos or dbt-run tasks to integrate dbt."*

### Q4. "A DAG that used to take 30 minutes now takes 3 hours. What do you do?"

🟢 *"Find which task regressed from the Gantt view, then ask what changed: data volume, a skewed key, a warehouse resized or suspended, a new upstream dependency, or resource contention from a pool. Check the query profile for the slow task — scan volume, spilling, join explosion. Fix the cause, add an alert on duration versus a rolling baseline so we catch it earlier next time."*

🔴 Trap: "I'd add more workers" without diagnosing.

---

## 9. 🟦 T — Kafka & streaming

🔵 **Hook: "Kafka is a durable, ordered, replayable log."** Producers append; consumers read at their own pace using an offset.

### Cheat card

- **Topic** -> split into **partitions** (unit of parallelism and ordering). Order is guaranteed **only within a partition**; choose the **key** (e.g. `account_id`) so related events land together.
- **Replication factor 3**, `min.insync.replicas=2`, producer `acks=all` -> survive a broker loss without data loss.
- **Consumer group**: each partition is read by one consumer in the group; max parallelism = number of partitions.
- **Delivery semantics:** at-most-once · at-least-once (default, may duplicate) · exactly-once (idempotent producer + transactions + idempotent sinks).
- **Schema Registry** (Avro/Protobuf) enforces compatibility.
- **Compacted topics** keep the latest value per key (good for "current state").
- **Kafka Connect / Debezium** = CDC from databases. **DLQ** (dead-letter queue) for poison messages.
- **Lag** (offset behind head) is the key health metric.
- **Stream processing:** Flink / Spark Structured Streaming / ksqlDB; **watermarks** handle late events.
- Managed: **MSK**, **Confluent Cloud**, Kinesis (AWS-native alternative).

### Q1. "When do you actually need streaming?"

🟢 *"Only when the decision's value decays in minutes: in-app personalization, fraud or abuse detection, operational alerting, live usage-based billing. For daily executive KPIs, batch is cheaper, simpler, and easier to debug. I ask: 'what would you do differently with data that is 5 minutes old instead of 24 hours old?' If nobody can answer, it's batch. Streaming also forces you to handle ordering, duplicates, and late data — that complexity needs a business reason."*

### Q2. "How do you guarantee no data loss and no duplicates?"

🟢 *"Loss: replication factor 3, min ISR 2, acks=all, and consumers that commit offsets only after successfully processing. Duplicates: Kafka gives at-least-once by default, so I make the sink idempotent — upsert keyed on a unique event_id — rather than chase true exactly-once end to end. Where we need exactly-once inside Kafka (read-process-write), use the idempotent producer and transactions. Then monitor with end-to-end reconciliation: count at source vs count in the lake per hour."*

### Q3. "Consumer lag is growing. What do you check?"

🟢 *"First, is it the consumer or the producer: did the produce rate spike? If consumers are slow: processing time per message (slow downstream call, DB lock), rebalances happening repeatedly, under-provisioned consumers, or a hot partition from a skewed key. Fixes: scale consumers up to the partition count, add partitions (mind the key mapping), batch writes to the sink, move slow work async, or fix the key distribution. Alert on lag trend, not just threshold."*

### Q4. "Handle late and out-of-order events?"

🟢 *"Process by event time, not arrival time. Use watermarks with an allowed lateness (say 10 minutes). Late-but-within-window events update the result; later ones go to a late-data side output and are reconciled by the nightly batch job. The batch layer is the source of truth; streaming gives fast approximate numbers — the lambda-style compromise — or I use a single streaming pipeline writing to Iceberg/Delta when the team can operate it."*

### Q5. "Kafka vs Kinesis vs a managed queue?"

🟢 *"Kafka: richest ecosystem (Connect, Streams, Flink), replay, portability. Kinesis: lower ops on AWS, tighter integration, limits per shard. SQS/SNS: simple task queues without replay or ordering at scale. For analytics events and CDC with many consumers, a log (Kafka/Kinesis) fits; for 'do this job once', a queue fits."*

---

## 10. 🟦 T — SQL (they will test this; practise writing, not reading)

🔵 **Hook: "Grain first, then join, then window."** Say the grain of every table out loud before writing a join. Most wrong answers are fan-out from a join at the wrong grain.

### Cheat card

- Order of evaluation: `FROM/JOIN -> WHERE -> GROUP BY -> HAVING -> WINDOW -> SELECT -> DISTINCT -> ORDER BY -> LIMIT`.
- `ROW_NUMBER` (unique rank) · `RANK` (ties skip) · `DENSE_RANK` (ties no skip) · `LAG/LEAD` (neighbour rows) · `SUM() OVER (ORDER BY ...)` (running total).
- `QUALIFY` (Snowflake/BigQuery/Databricks) filters on window results; elsewhere wrap in a CTE.
- Anti-join: `LEFT JOIN ... WHERE b.id IS NULL`, or `NOT EXISTS`. Avoid `NOT IN` with nullable columns.
- `COUNT(*)` counts rows, `COUNT(col)` skips NULLs, `COUNT(DISTINCT col)` unique.

Assume tables: `users(user_id, signup_at, plan, account_id)`, `events(event_id, user_id, event_name, event_ts)`, `subscriptions(account_id, month, mrr)`.

### SQL 1 — Activation: % of new users who ran a first test within 7 days of signup

```sql
WITH first_test AS (
  SELECT user_id, MIN(event_ts) AS first_test_ts
  FROM events
  WHERE event_name = 'test_run'
  GROUP BY user_id
)
SELECT
  DATE_TRUNC('week', u.signup_at)                                   AS signup_week,
  COUNT(*)                                                           AS new_users,
  COUNT_IF(f.first_test_ts <= DATEADD('day', 7, u.signup_at))        AS activated_7d,
  ROUND(100.0 * COUNT_IF(f.first_test_ts <= DATEADD('day', 7, u.signup_at))
        / COUNT(*), 1)                                               AS activation_pct
FROM users u
LEFT JOIN first_test f USING (user_id)       -- LEFT: keep users who never ran a test
GROUP BY 1
ORDER BY 1;
```
🟢 *Say:* "Grain is one row per user after the `first_test` CTE, so the join cannot fan out. LEFT JOIN so non-activators stay in the denominator. I'd also exclude users whose 7-day window hasn't elapsed yet, otherwise recent weeks look artificially low (right-censoring)."

### SQL 2 — Weekly retention cohort

```sql
WITH activity AS (
  SELECT DISTINCT user_id, DATE_TRUNC('week', event_ts) AS active_week
  FROM events WHERE event_name = 'test_run'
),
cohort AS (
  SELECT user_id, DATE_TRUNC('week', signup_at) AS cohort_week FROM users
)
SELECT
  c.cohort_week,
  DATEDIFF('week', c.cohort_week, a.active_week) AS weeks_since_signup,
  COUNT(DISTINCT a.user_id)                       AS active_users
FROM cohort c
JOIN activity a USING (user_id)
GROUP BY 1, 2
ORDER BY 1, 2;
```
🟢 *Say:* "Divide `active_users` by the week-0 cohort size for the retention curve. Dedupe activity to user-week first so heavy users don't inflate counts."

### SQL 3 — Latest row per key (dedupe)

```sql
SELECT *
FROM subscriptions_raw
QUALIFY ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY updated_at DESC) = 1;
```
(No `QUALIFY`? `SELECT * FROM (SELECT *, ROW_NUMBER() OVER (...) rn FROM t) WHERE rn = 1`.)

### SQL 4 — Sessionization (new session after 30 minutes idle)

```sql
WITH flagged AS (
  SELECT user_id, event_ts,
         CASE WHEN DATEDIFF('minute',
                LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts),
                event_ts) > 30
              OR LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts) IS NULL
              THEN 1 ELSE 0 END AS new_session
  FROM events
)
SELECT user_id, event_ts,
       SUM(new_session) OVER (PARTITION BY user_id ORDER BY event_ts) AS session_id
FROM flagged;
```
🔵 Hook: "Flag the break, then running-sum the flags."

### SQL 5 — Net Revenue Retention (NRR) for a month

```sql
WITH cur AS  (SELECT account_id, mrr FROM subscriptions WHERE month = '2026-09-01'),
     prev AS (SELECT account_id, mrr FROM subscriptions WHERE month = '2025-09-01')
SELECT 100.0 * SUM(cur.mrr) / SUM(prev.mrr) AS nrr_pct
FROM prev
LEFT JOIN cur USING (account_id);   -- start from last year's customers only
```
🟢 *Say:* "NRR looks at the cohort of customers that existed 12 months ago: their MRR now (including expansion, contraction and churn at 0) divided by their MRR then. New customers are excluded — starting from `prev` guarantees that."
🔴 Trap: dividing total MRR now by total MRR then — that is growth, not retention.

### SQL 6 — SCD Type 2 with MERGE (concept; know the shape)

```sql
-- 1) close current rows whose tracked attributes changed
MERGE INTO dim_account d
USING stg_account s ON d.account_id = s.account_id AND d.is_current
WHEN MATCHED AND (d.plan <> s.plan OR d.segment <> s.segment)
  THEN UPDATE SET d.is_current = FALSE, d.valid_to = CURRENT_TIMESTAMP;
-- 2) insert new current versions (new accounts + changed accounts)
INSERT INTO dim_account (account_id, plan, segment, valid_from, valid_to, is_current)
SELECT s.account_id, s.plan, s.segment, CURRENT_TIMESTAMP, NULL, TRUE
FROM stg_account s
LEFT JOIN dim_account d ON d.account_id = s.account_id AND d.is_current
WHERE d.account_id IS NULL;     -- none current = new, or just closed above
```

### Q1. "How do you debug a query that is slow?"

🟢 *"Look at the query profile before touching SQL. Check bytes scanned versus returned (missing partition/cluster pruning), join order and join explosion (wrong grain), data skew on a hot key, spilling to disk, and repeated expensive subqueries. Fixes in order: filter early on partition columns, select only needed columns, pre-aggregate before joining, replace correlated subqueries with joins/windows, materialise a reused CTE or build an incremental model, cluster on the common filter column. Then validate that results are identical and cost fell."*

### Q2. "Two dashboards show different revenue. What do you do?"

🟢 *"Reconcile from the top: same definition? (booked vs recognised vs billed; gross vs net of refunds; currency). Same grain and filters? Same time zone and cutoff? Same source (CRM versus billing)? I bisect by slicing both numbers by month and segment until the gap localises, then trace lineage. The long-term fix is organisational: one certified revenue model in the semantic layer, and the competing dashboards point to it."*

---

## 11. 🟦 T — Python

🔵 **Hook: "Python is glue and guardrails."** SQL does the heavy transformation; Python orchestrates, validates, calls APIs, and does ML.

### Cheat card

- Idempotent loads · retries with backoff · structured logging · type hints · tests with `pytest` · config via env vars (never hard-coded secrets).
- `pandas` for small/medium; `polars`/`duckdb` for fast single-node; `PySpark` for large.
- Generators/chunking for memory; `requests.Session` with timeouts; never `except Exception: pass`.

### Code to know cold — incremental, idempotent API ingestion

```python
import os, time, logging, requests
log = logging.getLogger(__name__)

def fetch_page(session, url, params, retries=5):
    for attempt in range(retries):
        resp = session.get(url, params=params, timeout=30)
        if resp.status_code == 429 or resp.status_code >= 500:   # transient
            time.sleep(min(2 ** attempt, 60))
            continue
        resp.raise_for_status()                                  # permanent errors fail loudly
        return resp.json()
    raise RuntimeError(f"gave up after {retries} tries: {url}")

def load_incremental(conn, since):
    """Pull records updated since `since`; upsert on id -> safe to re-run."""
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {os.environ['API_TOKEN']}"
    page, rows = 1, 0
    while True:
        data = fetch_page(session, "https://api.example.com/tickets",
                          {"updated_since": since, "page": page})
        if not data["items"]:
            break
        conn.execute_many(UPSERT_SQL, data["items"])   # MERGE on primary key
        rows += len(data["items"]); page += 1
    log.info("loaded %d rows since %s", rows, since)
    return rows
```
🟢 *Say:* "Three production ideas in 20 lines: retry only transient errors with exponential backoff, a high-water-mark (`since`) for incremental loads, and an upsert so re-running doesn't duplicate."

### Code to know cold — a data-quality check

```python
def check_not_null_unique(df, key, required):
    problems = []
    if df[key].duplicated().any():
        problems.append(f"duplicate {key}: {df[key].duplicated().sum()}")
    for col in required:
        n = df[col].isna().sum()
        if n: problems.append(f"{col} has {n} nulls")
    if problems:
        raise ValueError("; ".join(problems))   # fail the pipeline, don't publish bad data
```

### Q1. "How do you write production-grade pipeline code?"

🟢 *"Small pure functions that I can unit test; configuration through environment and parameters; idempotent writes; clear separation of extract, transform, load; structured logs and metrics; retries only for transient failures; and CI that runs tests and linting on every PR. Anything that touches data gets a validation step. Code review is mandatory, including for analysts' SQL and notebooks that become production."*

### Q2. "pandas runs out of memory on a 50 GB file. Options?"

🟢 *"Do not load it all. Stream in chunks, or switch engines: DuckDB or Polars for fast single-node, columnar and lazy; Spark if it's growing beyond one machine. Convert CSV to partitioned parquet once — columnar format and column pruning typically cut size and time dramatically — and push filters down. Choose by growth: if 50 GB is the ceiling, DuckDB on a big instance is far cheaper than a cluster."*

---

## 12. 🟦 Data modeling & SaaS metrics (the language of the CFO)

🔵 **Hook: "Facts are verbs, dimensions are nouns."** A fact = something that happened (test_run, invoice). A dimension = who/what/where (account, plan, date).

### Cheat card — modeling

- **Grain**: what one row means. Decide it first, write it down.
- **Star schema**: fact in the middle, denormalised dimensions around it. Best for BI.
- **Fact types**: transaction (event), periodic snapshot (daily MRR per account), accumulating snapshot (funnel with milestone dates).
- **SCD**: Type 1 overwrite · Type 2 history rows (valid_from/valid_to) · Type 3 previous-value column.
- **Surrogate keys** insulate from source-key changes. **Conformed dimensions** (one `dim_account` shared by all facts) let you slice anything by anything.
- Alternatives: **Data Vault** (auditable, many sources) and **One Big Table** (fast for BI, hard to govern). Pick star for analytics, vault only for heavy audit/integration needs.

### Cheat card — SaaS metrics (know the formulas, they WILL ask)

| Metric | Formula / meaning |
|---|---|
| **MRR / ARR** | Monthly recurring revenue; ARR = MRR × 12 |
| **New / Expansion / Contraction / Churned MRR** | The four movements that explain MRR change |
| **Gross Revenue Retention (GRR)** | (Start MRR − contraction − churn) / Start MRR (max 100%) |
| **Net Revenue Retention (NRR)** | (Start MRR + expansion − contraction − churn) / Start MRR (can exceed 100%) |
| **Logo churn** | % customers lost in period |
| **CAC / payback** | Sales + marketing spend / new customers; payback months = CAC / (new MRR × gross margin) |
| **LTV** | ARPA × gross margin / churn rate (rule of thumb LTV:CAC ≥ 3) |
| **Activation rate** | % signups reaching the "aha" action in N days |
| **PQL** | Product-qualified lead: usage pattern that predicts purchase |
| **Quick ratio** | (New + Expansion MRR) / (Contraction + Churn MRR); healthy > 4 |

🔵 **Hook: "GRR = floor, NRR = growth."** GRR can't beat 100%; NRR above 100% means the existing base grows by itself.

### Q1. "Model product-usage data for Katalon."

🟢 *"Grain first. Core fact: `fact_test_execution`, one row per test run, with keys to account, user, project, product/module, environment, date, plus measures: duration, pass/fail counts. A daily snapshot fact `fact_account_daily_usage` aggregates active users, executions, and integrations, because most analytics and ML features are account-day. Dimensions: `dim_account` (SCD2 for plan and segment so history is right), `dim_user`, `dim_product`, `dim_date`. Events are raw in bronze with an `event_id`, deduped in silver. The semantic layer defines 'active team' once. I'd confirm the real hierarchy — user -> team/project -> account/organisation — since B2B analysis nearly always needs the account level, not just the user."*

### Q2. "Attribute revenue to marketing channels?"

🟢 *"First-touch, last-touch, and multi-touch tell different stories; no model is 'true'. I'd keep a touchpoint fact table and compute position-based and data-driven attribution as views, then validate with experiments (geo or holdout tests) because attribution is observational. In B2B, attribute at the account level over a long cycle — one opportunity has many contacts and touches over months."*

### Q3. "How do you handle changing definitions (e.g. 'active user')?"

🟢 *"Version them. Metric definitions live in code in the semantic layer with an owner and effective date; changes go through review; historical values are either restated or the break is annotated. I announce definition changes in the data channel and keep the old metric for a deprecation window so trends don't silently jump."*

---
## 13. 🟦 L — Governance, quality, security, privacy (GDPR, CCPA/CPRA)

🔵 **Hook: "Govern to enable, not to block."** Good governance makes the *right* data easy to find and safe to use. Bad governance is a ticket queue.

### Cheat card — the 6 pillars: **C-O-Q-S-P-L**

| Pillar | What it means | Concrete mechanism |
|---|---|---|
| **C**atalog | Everyone can find and understand data | Catalog, business glossary, owners, lineage |
| **O**wnership | Every dataset has an owner and steward | Domain owners; data contracts |
| **Q**uality | Fit for use, measured | Tests, SLOs, anomaly monitors, incident process |
| **S**ecurity | Only the right people access | RBAC/ABAC, encryption, masking, audit |
| **P**rivacy | Lawful, minimal, deletable | Classification, consent, DSAR process, retention |
| **L**ifecycle | Keep only what is needed | Retention + deletion policies, archival |

### Cheat card — GDPR vs CCPA/CPRA (quick contrast)

| | **GDPR (EU/UK)** | **CCPA/CPRA (California)** |
|---|---|---|
| Model | **Opt-in**: need a lawful basis (consent, contract, legitimate interest...) | **Opt-out**: notice + right to opt out of "sale/sharing" |
| Key principles | Lawfulness, purpose limitation, **data minimisation**, accuracy, storage limitation, integrity/confidentiality, accountability | Notice at collection, purpose limitation, data minimisation (CPRA), reasonable security |
| Rights | Access, rectification, **erasure**, restriction, portability, objection, rights on automated decisions | Know, delete, **correct**, opt-out of sale/sharing, limit use of **sensitive PI**, non-discrimination |
| Response time | 1 month (extendable by 2) | 45 days (extendable by 45) |
| Other | **DPIA** for high-risk processing; **DPA** with processors; transfer mechanisms (SCCs) for non-EU transfers; breach notice to authority within **72h** | Honour **Global Privacy Control** opt-out signal; service-provider contracts; "Do Not Sell or Share" link |

🔵 **Hook: "GDPR = permission first; CCPA = notice and opt-out."**

🟡 You are not the lawyer. Say: "I translate legal requirements into controls and evidence; Legal confirms the interpretation." Verify the current thresholds with counsel before quoting them as fact.

### Cheat card — data quality dimensions (**C-V-U-T-C-A**)

**C**ompleteness · **V**alidity · **U**niqueness · **T**imeliness · **C**onsistency · **A**ccuracy. Tool options: dbt tests, Great Expectations, Soda, Monte Carlo/observability. Tier datasets: **Tier 1** (exec KPIs, finance, customer-facing) get SLOs, on-call, and incident review; Tier 3 (exploratory) gets best-effort.

### Q1. "How would you build a governance programme without slowing teams down?"

🟢 *"Start with the 20% of data that carries 80% of the risk and value — customer PII, revenue, and the executive KPIs — and put real controls there first. Name an owner for each critical dataset, publish a glossary and lineage so people can self-serve, and automate: PII tags drive masking policies, quality tests run in CI, access requests go through a workflow with auto-expiry. A governance council meets monthly to resolve conflicts and approve policy, not to approve every request. I measure it: percentage of Tier-1 data with an owner, test coverage, access-request turnaround, and number of incidents."*

### Q2. "A user asks to be deleted under GDPR. How does it work in a data lake?"

🟢 *"Three steps: find, delete, prove. Find all of the person's data through a subject identifier mapped in a PII registry or through lineage-tagged columns. Delete from operational stores immediately. In the lake: tables with ACID formats (Delta/Iceberg) support row-level deletes followed by compaction/VACUUM to physically remove old files; for immutable raw files I either rewrite affected partitions or use crypto-shredding — encrypt each person's PII with a per-person key and delete the key. Backups roll off on their retention schedule, which we document. Derived data like aggregates and model features need review; truly anonymised aggregates are out of scope, but features keyed on the user are not. Log the request and completion for audit, within the legal deadline."*

### Q3. "How do you protect PII for analytics while still enabling analysis?"

🟢 *"Minimise, then pseudonymise, then restrict. Don't ingest what we don't need. Replace direct identifiers with a keyed hash/token so analysts can still join and count distinct users. Role-based dynamic masking: emails show as `a***@domain.com` for most roles, clear only for the few roles with justification. Row-level policies for region restrictions. Sensitive free text — like support tickets — gets PII redaction before it reaches the lake and before it is used for any LLM. Everything audited."*

### Q4. "How do you measure and improve data quality?"

🟢 *"Define quality from the consumer's view: for each Tier-1 dataset write a short SLO — freshness by 7am, completeness above 99.5%, no duplicates on the key. Tests run at ingestion, after transformation, and before publish; failures block publishing and alert the owner. I track incidents with time-to-detect and time-to-resolve, and run a blameless review for each Tier-1 incident. Trend line for the board: percentage of days SLOs were met. Detection should come from us, not from an executive spotting a wrong number."*

### Q5. "What is a data contract?"

🟢 *"A formal agreement between a data producer and its consumers about schema, semantics, quality expectations, and freshness — versioned, owned, and enforced in CI. It moves quality upstream: the team that emits the event is accountable for it. Example: the product team's `test_run` event has required fields, a stable ID, and a documented meaning; a breaking change must be versioned and announced."*

### Q6. "Security of customer data — Katalon customers are Fortune-500 companies."

🟢 *"For a testing vendor, customer test artefacts and logs may contain sensitive information, so the default is to treat them as confidential: least-privilege access, encryption, segregation by tenant, strict retention, and no use for analytics or model training beyond what contracts and consent allow. Compliance evidence — SOC 2 and ISO 27001-style controls — is a sales asset, so I'd make access logs, lineage, and retention automatically auditable, not a scramble before audits."*

🔴 Traps: "we'll just anonymise it" (hashing an email is pseudonymisation, not anonymisation) · "governance is Legal's job".

---

## 14. 🟦 A — Machine learning & MLOps

🔵 **Hook: "Data -> Features -> Train -> Register -> Deploy -> Monitor -> Retrain."** ML is a loop, not a project. Most failures happen after the model is "done".

### Cheat card

- **Use cases for a SaaS company:** churn/expansion prediction · lead and PQL scoring · usage forecasting and capacity · anomaly detection · support-ticket routing · recommendations / next-best-action · flaky-test and test-failure classification (product).
- **Feature store:** one definition of each feature used offline (training) and online (serving) -> prevents **training-serving skew**. Needs **point-in-time correctness** to avoid **leakage** (using data from after the prediction moment).
- **MLOps pipeline:** versioned data + code + model (MLflow / SageMaker Model Registry) · CI tests for data and model · staged rollout (shadow -> canary -> full) · monitoring.
- **Monitoring:** data drift (PSI, KS test) · concept drift (performance decay) · latency/error · business KPI. Define **retrain triggers** in advance.
- **Metrics:** imbalanced classes -> PR-AUC, recall@k, precision@k — not accuracy. Business metric: **uplift** vs a control group.
- **Batch vs real-time:** batch scoring (daily churn list) is 10x simpler than online serving. Start with batch.

### Q1. "Walk me through building a churn model."

🟢 *"Start with the decision: CS wants a weekly list of accounts to contact. That defines prediction horizon (say 90 days), unit (account), and the cost trade-off — a missed churner is expensive, a wasted call is cheap, so I'd optimise recall at a fixed list size. Features: usage trend (week-over-week change in test executions), breadth (modules used, integrations), seat utilisation, support tickets and sentiment, contract data, and champion changes. Careful with leakage — features must be computed as of the prediction date. Start with a gradient-boosted tree and a simple baseline; evaluate on a time-based split, not random. Explainability (SHAP) matters because CS needs reasons, not just scores. Then batch scoring into the CRM via reverse ETL. The real test is an uplift measurement: contacted vs holdout accounts. Monitor drift and retrain quarterly or on trigger."*

### Q2. "What is training-serving skew and how do you prevent it?"

🟢 *"The model sees different feature values in production than in training — different code, different time windows, different null handling. Prevent it by defining each feature once in a feature store or shared transformation library used by both paths, testing feature distributions between offline and online, and logging served features so they can be replayed for debugging."*

### Q3. "Model accuracy dropped in production. What do you do?"

🟢 *"Diagnose in order: is the pipeline healthy (missing or stale features)? Has the input distribution drifted (PSI)? Has the world changed (concept drift — e.g. a pricing change altered churn behaviour)? Is the label delayed so the dashboard is lagging? Roll back to the previous model if the business is exposed, retrain on recent data if drift is confirmed, and add an alert so we catch it earlier."*

### Q4. "How do you decide whether an ML solution is worth it vs rules?"

🟢 *"Start with the simplest thing that could work: rules or a heuristic baseline. ML earns its place if it beats the baseline by enough to cover its extra cost — training, monitoring, on-call, explainability. For many B2B problems with small data (a few thousand accounts), a good rules-and-scoring approach beats a complex model."*

---

## 15. 🟦 A — Generative AI, LLMs, agents, vector DBs, RAG

🔵 **Hook: "RAG = Retrieve, then Generate — with receipts."** Give the model the right facts at question time, and make it cite them.

### Cheat card — RAG pipeline (**I-C-E-S-R-R-G-E**, say it as a flow)

```
Ingest  -> Chunk  -> Embed  -> Store(vector DB)  -> Retrieve -> Rerank -> Generate -> Evaluate
docs,     300-800   turn text  pgvector/OpenSearch  hybrid:     cross-    LLM with   offline golden set
tickets,  tokens,   into       /Pinecone/Weaviate/  BM25 +      encoder   retrieved  + online feedback
wiki,     overlap,  vectors    Snowflake Cortex/    dense,      re-scores context +   (faithfulness,
code      by heading           Databricks Vector    top-k       top-k     citations   relevance)
                               Search
```

- **Embedding**: text -> vector; similar meaning -> nearby vectors (cosine similarity). **ANN indexes** (HNSW, IVF) trade a little recall for big speed.
- **Hybrid search** (keyword + vector) beats pure vector for product names, error codes, and acronyms — very relevant for a testing tool.
- **Metadata filters** (product version, language, tenant) are essential. **Access control must be enforced at retrieval time**, not just in the UI.
- **Evaluation:** Retrieval — recall@k, MRR. Generation — faithfulness (grounded in retrieved text), answer relevance, citation accuracy. Use a **golden set** of 100-300 real questions with reference answers; **LLM-as-judge** calibrated against human labels; online thumbs-up/down and escalation rate.
- **Hallucination controls:** retrieve-then-answer, "say you don't know" instruction and thresholds, citations, constrained output schemas, human review for high-stakes actions.
- **Agents** = LLM + tools + loop (plan -> act -> observe). Control with: bounded tools, least privilege, step/time/cost limits, human-in-the-loop for irreversible actions, full trace logging.
- **Fine-tuning vs RAG vs prompting:** prompting first, RAG for fresh/private knowledge, fine-tune for style/format/latency or specialised behaviour. RAG is the default for enterprise knowledge.
- **Cost/latency levers:** smaller models for simple routing, caching, shorter context, batching, streaming responses.
- **Security:** prompt injection (instructions hidden in retrieved content), data exfiltration, PII in prompts, vendor retention terms (zero-retention endpoints), customer-data training opt-in.

### Q1. "Design a RAG assistant for Katalon's documentation and support."

🟢 *"Goal first: deflect common support questions and speed up engineers; success is ticket-deflection rate with no drop in CSAT, plus answer faithfulness. Ingest docs, release notes, community posts, and resolved tickets (PII redacted). Chunk by heading with ~500 tokens and some overlap, attach metadata: product, version, language, source URL. Embed and store in a vector index; retrieve with hybrid search, because error codes and API names need exact matches, then rerank. The prompt passes the top chunks, requires citations, and instructs the model to say 'I don't know' when evidence is weak. Evaluation: a golden set from real tickets, tracked in CI so a prompt or model change can't silently regress quality. Guardrails: filter by user entitlement and tenant, block prompt-injection from retrieved content, log everything. Rollout: internal support agents first as co-pilot, then customers."*

### Q2. "How do you evaluate an LLM feature?"

🟢 *"Three layers. Offline: golden dataset, metrics for retrieval (recall@k) and generation (faithfulness, relevance), LLM-as-judge validated against human ratings on a sample. Pre-release: red-team for safety, injection, and PII leakage. Online: acceptance rate, edit distance of AI suggestions, escalation rate, latency, cost per request, and A/B against the baseline. Treat the eval set as a living asset reviewed every release."*

### Q3. "RAG gives wrong answers. How do you debug?"

🟢 *"Separate retrieval from generation. Check if the right chunk was in the top-k: if not, it's retrieval — fix chunking, add hybrid search, tune embeddings, add metadata filters, add a reranker. If the right chunk was there and the answer was still wrong, it's generation — tighten the prompt, reduce irrelevant context, add citation requirements, or use a stronger model. Most failures are retrieval, so I look there first."*

### Q4. "Where would Generative AI add measurable value at Katalon?"

🟢 *"Hypotheses to validate with the product team, each with a metric: (1) AI-assisted test authoring — natural language to test steps; metric is time to first working test and suggestion acceptance rate. (2) Failure triage — cluster test failures and propose root causes, flag flaky tests; metric is mean time to diagnose. (3) Test-impact analysis — predict which tests to run for a code change; metric is CI time saved at equal defect detection. (4) Support deflection via RAG. (5) Internal text-to-SQL on top of a semantic layer to widen self-service; metric is analyst request volume. I'd rank by value, data readiness, and risk, and run two as pilots."*

### Q5. "What is a vector database? When do you NOT need one?"

🟢 *"A store optimised for nearest-neighbour search over embeddings. You don't need a separate one if your volume is modest and Postgres with pgvector, your warehouse's vector features, or OpenSearch already fit the scale and ops model — one fewer system to secure. Pick a dedicated vector DB when you need very large scale, low latency, or advanced filtering/hybrid features. Decision drivers are scale, filtering needs, ops burden, and where the source data and access controls already live."*

### Q6. "How would you approach AI agents safely?"

🟢 *"Start with narrow, reversible tasks, give the agent least-privilege tools, cap steps and spend, require human approval before irreversible actions, log full traces, and evaluate on realistic task suites before release. Treat tool outputs and retrieved text as untrusted input — that's where injection comes from."*

---

## 16. 🟦 L — AI governance & Responsible AI

🔵 **Hook: "Know it, test it, explain it, own it."** Know every AI system you run (inventory), test for harm, explain decisions, and name an owner.

### Cheat card

- **Frameworks to name:** **NIST AI RMF** (Govern, Map, Measure, Manage) · **EU AI Act** (risk tiers: unacceptable, high, limited, minimal; transparency duties for generative AI) · **ISO/IEC 42001** (AI management system).
- **Controls:** AI/model inventory · use-case risk tiering · model cards and data sheets · bias and robustness testing · human oversight · incident process · vendor and third-party model review · audit logs.
- **Customer-data principle:** customer content is not training data unless contract/consent says so; document opt-in/opt-out; keep tenant isolation.
- **Transparency:** tell users when they interact with AI and when content is AI-generated.

### Q1. "How do you set up AI governance in a fast-moving company?"

🟢 *"Lightweight and risk-tiered. A one-page intake for any AI use case: purpose, data used, owner, customer impact. Low risk (internal productivity) is approved quickly by checklist; higher risk (customer-facing, uses customer data, automated decisions) goes through review with Security, Legal and Product, and needs evaluation evidence and a rollback plan. Maintain a model inventory, model cards, and monitoring. Align with NIST AI RMF so we speak a common language with enterprise customers' procurement teams."*

### Q2. "A customer asks if you train on their data. What's our answer?"

🟢 *"It must be a crisp, truthful, contract-backed answer: by default no, unless they opt in; their data is isolated by tenant; and we can show where it flows. If the data team can't prove it from lineage and access logs, we fix that first. For Fortune-500 buyers this is a sales blocker if vague."*

---

## 17. 🟦 N — Experimentation, recommendations, personalization

🔵 **Hook: "Randomise, size, check, decide."**

### Cheat card — A/B testing

- **Hypothesis -> metric (primary + guardrails) -> randomisation unit -> sample size -> run -> analyse -> decide.**
- **Sample size (per group, two-sided α = 5%, power 80%):** `n ≈ 16 σ² / Δ²` where Δ = smallest effect worth detecting (MDE). Halving Δ quadruples n.
- **SRM (Sample Ratio Mismatch)**: assignment ratio differs from design (chi-square test) -> the experiment is broken; fix before reading results.
- **CUPED**: use pre-experiment data as a covariate to cut variance (often 20-50%).
- **Pitfalls:** peeking (use sequential testing or fixed horizon), multiple comparisons, novelty/primacy effects, Simpson's paradox, interference between users.
- **B2B twist:** users in the same account influence each other and accounts are few -> randomise at **account level** (cluster), expect low power, run longer, use more sensitive proxy metrics, and combine with quasi-experiments (diff-in-diff, holdouts, staged rollouts).
- **Platform pieces:** feature flags + assignment service + event logging + stats engine + guardrail dashboards + experiment registry.

### Cheat card — recommenders / personalization

- Types: **collaborative filtering** (users like you), **content-based** (similar items), **hybrid**, **two-tower** retrieval + ranker (large scale). **Cold-start** -> use content/metadata and popularity.
- Offline metrics: precision/recall@k, NDCG, coverage/diversity. **Online A/B decides.**
- B2B examples at a testing company: recommend test templates/keywords, suggest integrations, next-best-action in onboarding, personalised in-app guides by role (manual tester vs automation engineer).

### Q1. "Design an experimentation platform for a B2B SaaS."

🟢 *"Core: a feature-flag service for stable assignment (hash of account_id + experiment salt), event logging with exposure events, a stats service computing the primary and guardrail metrics with CUPED and SRM checks, and a registry so every experiment has a hypothesis, owner, and decision log. Because teams are the natural unit in B2B, assignment is at account level; I'd include power calculators that show realistic durations. Governance: pre-registration of metrics and no peeking without sequential methods. Culture: celebrate learning from null results."*

### Q2. "Your test shows +2% conversion, p = 0.04, but you ran it for 3 days. Ship?"

🟢 *"Not yet. Three days misses weekly seasonality, and if we peeked daily the p-value is inflated. Check SRM, check that the test reached its planned sample size, look at guardrails, and see if the effect holds across segments. If still positive at the pre-agreed horizon, ship, ideally with a holdout to confirm long-term effect."*

### Q3. "Fewer than 200 accounts per month. How do you experiment?"

🟢 *"Standard A/B won't have the power. Options: bigger effect sizes only, user-level randomisation where interference is low, more sensitive intermediate metrics (activation steps rather than annual revenue), variance reduction, staged rollouts with diff-in-diff, and Bayesian methods to express uncertainty. Also pair with qualitative research. And be honest with stakeholders: some questions can't be answered with a single test."*

---

## 18. 🟦 O/N — KPIs, dashboards, self-service analytics, data culture

🔵 **Hook: "One metric, one definition, one place."**

### Cheat card

- **Metric tree**: North Star -> L1 drivers -> L2 levers. Example: Weekly active teams = new teams × activation × retention.
- **Executive dashboard rules:** 5-7 numbers, trend + target + owner, drill-down, freshness timestamp, link to definition. If it needs explaining, it's too complex.
- **Self-service tiers:** Gold (certified, governed, exec-ready) · Silver (team-owned, documented) · Bronze (sandbox). Label them in the BI tool.
- **Semantic layer** (dbt Semantic Layer, Cube, LookML, AtScale, Snowflake semantic views): metric logic defined once, consumed by BI, notebooks, APIs, and LLM text-to-SQL.
- **Adoption metrics for the data team:** weekly active users of certified dashboards · % decisions citing data · request turnaround · trust score survey · cost per active user.
- **Culture levers:** data literacy training · office hours · embedded analysts · public glossary · celebrating decisions made with data (and decisions reversed because of data).

### Q1. "How do you create a data-driven culture?"

🟢 *"Make good data easy and bad data visible. Easy: certified datasets, a semantic layer so definitions agree, dashboards people actually open, and embedded analysts who sit with each function. Visible: freshness and quality badges on dashboards, a public glossary, a regular 'metrics review' where leadership uses the same numbers. Then teach: office hours and short trainings. And lead by example — my own recommendations always show the data, the assumption, and what would change my mind."*

### Q2. "Executives distrust the numbers. What do you do?"

🟢 *"Trust is rebuilt with consistency and transparency. I'd find the three most-argued metrics, document a single definition for each with Finance and the business owner, publish it in one certified place, and retire the rival versions. Add freshness and quality indicators on the dashboard, and a visible changelog. When a number is wrong I tell people first, explain, and fix the root cause."*

### Q3. "How do you prevent the data team from becoming a report factory?"

🟢 *"Deflect repeatable questions to self-service, publish certified datasets and a semantic layer, and use an intake that asks which decision it supports. The team's time goes to roughly 60% roadmap (platform, models, AI), 20% enablement, 20% ad-hoc. Review the request log monthly; every repeated question becomes a dashboard or a metric."*

---

## 19. 🟦 O — Stakeholders: Product, Engineering, Marketing, Sales, Customer Success

🔵 **Hook: "Give each function its one number and its one question."**

| Function | Their question | Your offer | First deliverable |
|---|---|---|---|
| **Product** | What do users do? What drives retention? | Event taxonomy, funnels, cohort and feature adoption, experimentation | Activation definition + feature-adoption dashboard |
| **Engineering** | Can you stop breaking our events? Can I use your data in the product? | Data contracts, shared schemas, ML/feature platform, AI-ready data | Event schema review + contract for top 10 events |
| **Marketing** | Which channels create paying teams? | Funnel, attribution, audience building, CAC by channel | Single source for lead->opportunity->revenue |
| **Sales** | Whom should I call, and what's the health of my accounts? | PQL scoring, account 360, territory analytics | PQL list inside the CRM |
| **Customer Success** | Who will churn / expand? | Health score, churn model, usage alerts | Weekly at-risk list with reasons |
| **Finance/Execs** | What's ARR, NRR, burn, forecast? | Certified revenue model, forecasts, unit economics | Monthly KPI pack from one model |
| **Legal/Security** | Are we compliant? | PII map, retention, DSAR automation, audit logs | Data inventory + DSAR runbook |

### Q1. "Engineering won't instrument events properly. What do you do?"

🟢 *"Make it their win. I don't ask for 'more tracking'; I show them what's broken in the data and what it blocks — e.g. 'we can't tell if the new feature works'. Provide a tracking plan template, SDK helpers, and automated schema checks in CI so instrumenting is minutes, not days. Agree the top ten events first. Escalate through the product lead with the business cost of not having the data."*

### Q2. "Sales wants a lead score by Friday; the data isn't ready."

🟢 *"Offer a thin, honest version: a rules-based PQL score from three signals we trust (e.g. team size, test runs in first 14 days, number of integrations), clearly labelled v0, with a plan to move to a model once data quality allows. Deliver value fast without overpromising, and agree how we'll measure whether it helps (conversion of scored vs unscored)."*

### Q3. "How do you say no?"

🟢 *"I say 'yes, and here's the trade-off.' I show the ranked backlog, what would be delayed by this request, and what the requester would gain. If it's still the top priority for the business, I'll reprioritise openly. Silent over-commitment is worse than a clear no."*

---

## 20. 🟦 O — Leadership: building and leading the Data team

🔵 **Hook: "Hire for range, build for trust, review for growth."**

### Cheat card — team shape (a typical first 12 months)

```
Head of Data
 ├── Data Platform / Engineering   (ingest, orchestration, cost, security)      <- hire first
 ├── Analytics Engineering         (dbt models, semantic layer, quality)       <- hire early
 ├── Analytics / BI (embedded)     (Product, GTM, CS partners)
 ├── Data Science / ML / AI        (churn, PQL, recommendations, GenAI)        <- after foundations
 └── Governance & Privacy (shared with Security/Legal)                         <- part-time lead first
```
- **Sequence:** foundations (platform + analytics engineering) before advanced science. A data scientist without clean data produces slides.
- **Operating model:** hub-and-spoke — central platform and standards, embedded analysts for domain speed.
- **Hiring bar:** technical depth + business curiosity + communication. Work-sample over trivia. Diverse panels.
- **Growth:** career ladders (IC and manager tracks), quarterly 1:1 growth conversations, stretch projects, internal talks, blameless post-mortems.
- **Rhythm:** weekly planning, monthly stakeholder review, quarterly OKRs, yearly strategy refresh.

### Q1. "How do you build and mentor a high-performing team?"

🟢 *"Clarity, trust and growth. Clarity: every person knows the 2-3 outcomes they own and how they're measured. Trust: blameless post-mortems, I take accountability upward and give credit downward, and I keep my promises on priorities. Growth: a development plan per person, regular stretch work, sponsorship for promotions, and I mentor by pairing on real problems — design reviews and code reviews are my main teaching tools. I hire people stronger than me in specific areas and make sure decisions are made at the lowest competent level."*

### Q2. "Whom do you hire first?"

🟢 *"It depends on what I find, but typically a strong analytics engineer or senior data engineer first — to stabilise the foundations and gain trust through reliable numbers — and an embedded product analyst second. ML/AI roles come after the data is trustworthy. If a critical gap exists, like privacy, I'd use a contractor or partner with Security while hiring."*

### Q3. "How do you handle an underperformer?"

🟢 *"Early, specific and kind. First check whether expectations were clear and whether I gave the right support. Then a direct conversation with concrete examples, an agreed 30-60 day plan with measurable goals and weekly check-ins, and help (pairing, training, scope change). If it's not working, I act fairly and promptly with HR — leaving it unresolved hurts the team more than the individual."*

### Q4. "How do you manage the data budget?"

🟢 *"Three buckets: platform and tools, people, and cloud consumption. I forecast consumption from unit costs (cost per 1,000 queries, per pipeline run) and growth drivers, review the bill monthly with owners, and keep a 10-15% buffer for experiments. For vendors I negotiate commit discounts only after a few quarters of stable usage, and maintain exit plans. I present the budget to Finance as investment cases tied to outcomes, not as a list of tools."*

### Q5. "Tell me about leading a change across business functions."

🟢 *Use a story from Section 21 (S5). Structure:* the burning problem -> stakeholder map -> small pilot with a champion -> data to show results -> scale + training -> embed in process (so it survives you).

---

## 21. Behavioural story bank (fill the blanks with YOUR real numbers)

🔵 **Hook: "8 stories cover 80% of questions."** Prepare each one as STAR-R. Write one line per slot, then compress to 90 seconds.

| # | Story | Typical prompts it answers |
|---|---|---|
| **S1** | Built or scaled a data platform | "Biggest technical achievement", "how did you choose tools" |
| **S2** | Fixed trust in numbers / data-quality crisis | "Tell me about a failure", "conflict about metrics" |
| **S3** | Influenced executives with data | "Persuade a sceptical stakeholder", "disagree and commit" |
| **S4** | Delivered ML/AI value with measurable impact | "AI initiative", "ROI" |
| **S5** | Led cross-functional transformation | "Change management", "lead without authority" |
| **S6** | Built / grew / turned around a team | "Hiring", "mentoring", "underperformer" |
| **S7** | Privacy / security / compliance event | "Risk", "ethical dilemma" |
| **S8** | Cut cost or said no to a bad idea | "Prioritisation", "trade-offs" |

🟡 Personal version of this section lives in `Katalon_Stories_PRIVATE.md` (gitignored; not in this public file).

### Template (copy per story)

```
S_ : <title>
Situation (1 line):  [BLANK: company, scale, why it mattered]
Task (my role):      [BLANK: what I owned]
Action (3 verbs):    1) [BLANK]  2) [BLANK]  3) [BLANK]
Result (numbers):    [BLANK: % / $ / hours / latency / adoption]
Reflection:          [BLANK: what I'd do differently]
Link to Katalon:     [BLANK: how this applies to their JD line]
```

### Example (shape only — replace with your own facts)

> **S2: Metric trust.** *Situation:* Sales and Finance reported ARR numbers 8% apart, which delayed a board pack. *Task:* I owned the data and was asked to resolve it within a month. *Action:* (1) I traced both numbers to different definitions — booked vs billed — and different sources; (2) I ran a workshop with Finance, Sales Ops and Product to agree one definition and owner; (3) I built a certified revenue model with tests and put it in the semantic layer, retiring the two spreadsheets. *Result:* the gap fell to under 0.5%, month-end close shortened by two days, and dashboard usage on the certified model reached [X]. *Reflection:* I should have involved Finance sooner; now I pair metric changes with a named business owner from day one.

### Common behavioural questions (practise each in 90 seconds)

1. Tell me about a time you built a data strategy that changed the business.
2. Tell me about a time a pipeline or dashboard gave wrong numbers to executives.
3. Describe a time you disagreed with a senior stakeholder.
4. Describe an AI/ML project that did not deliver. What did you learn?
5. How did you handle a privacy or security incident or near-miss?
6. Tell me about the hardest hire or the hardest termination.
7. Describe a time you had to deliver with limited budget or headcount.
8. Tell me about influencing a team that didn't report to you.
9. Describe a decision you made with incomplete data.
10. What's the most important thing you've done to grow someone's career?

---

## 22. Questions YOU should ask (shows seniority)

**Strategy**
1. "What are the 3 business outcomes you expect data and AI to move in the first year?"
2. "Where does the company make decisions today with the least data support?"

**Platform & people**
3. "What is the current stack, and which part causes the most pain? Who owns it today?"
4. "How big is the data team today, how is it structured, and where are the biggest skill gaps?"
5. "What do monthly cloud and tooling spend look like, and who approves changes?"

**AI**
6. "Which AI features are in the product now, and how do you measure whether they work?"
7. "What is the policy on using customer data for model training and analytics?"

**Governance**
8. "What compliance obligations are you actively audited against (SOC 2, ISO 27001, GDPR)? Where are gaps?"

**Culture & success**
9. "Which metric do executives argue about most?"
10. "What would make you say in 12 months: this hire was a great decision?"
11. "What is the biggest risk you see in this role?"

🟡 Ask 3-4, not 11. Choose by who is interviewing: CEO/CPO -> 1, 2, 10; Engineering lead -> 3, 6; Legal/Security -> 7, 8; HR -> 4, 11.

---

## 23. Flashcards (cover the right side and answer)

| Q | A |
|---|---|
| What is a data strategy in one sentence? | Decisions to improve + minimum capability + owners + ROI. |
| Medallion layers? | Bronze raw, silver cleaned, gold business marts. |
| ETL vs ELT? | ELT loads raw into the warehouse then transforms there; cheaper compute elasticity, replayable. |
| Idempotent pipeline? | Running twice for the same interval gives the same result (MERGE / overwrite partition). |
| Airflow's job? | Orchestrate (order, retry, alert) — not compute. |
| Kafka ordering guarantee? | Only within a partition; use the right key. |
| Kafka no-loss config? | RF 3, min ISR 2, acks=all, commit offsets after processing. |
| Exactly-once in practice? | At-least-once delivery + idempotent sink (upsert on unique ID). |
| Snowflake cost levers? | Auto-suspend, right-size, resource monitors, query tags, clustering. |
| BigQuery cost levers? | Partition + cluster, require partition filter, slots vs on-demand. |
| Redshift cost levers? | RA3, concurrency scaling, WLM, Spectrum. |
| Lakehouse in one line? | Lake storage + table format (Delta/Iceberg) giving ACID and one copy for BI and ML. |
| Star schema? | Fact table at a declared grain surrounded by denormalised dimensions. |
| SCD2? | New row per change with valid_from/valid_to/is_current. |
| NRR formula? | (Start + expansion − contraction − churn) / Start MRR, same cohort. |
| GRR vs NRR? | GRR ≤ 100% (no expansion); NRR can exceed 100%. |
| LTV:CAC target? | ≥ 3:1; CAC payback ideally < 12-18 months. |
| GDPR vs CCPA? | GDPR opt-in/lawful basis; CCPA notice + opt-out of sale/sharing. |
| GDPR deadlines? | Respond 1 month; breach notice to authority 72h. |
| CCPA response? | 45 days (+45). |
| Erasure in a lake? | ACID row delete + vacuum, rewrite partitions, or crypto-shredding. |
| Hash vs anonymise? | Hashing identifiers = pseudonymisation, still personal data. |
| Data quality dimensions? | Completeness, validity, uniqueness, timeliness, consistency, accuracy. |
| Data contract? | Versioned producer-consumer agreement on schema, semantics, quality, SLA. |
| Training-serving skew? | Features differ between training and production; fix with a feature store. |
| Leakage? | Using information not available at prediction time. |
| Imbalanced classification metric? | PR-AUC, recall/precision@k — not accuracy. |
| Drift types? | Data drift (inputs) vs concept drift (relationship). |
| RAG in one line? | Retrieve relevant private context, then generate a grounded, cited answer. |
| Hybrid search? | BM25 keyword + vector search; better for codes and names. |
| Reduce hallucination? | Grounding, citations, abstain threshold, schema-constrained output, evals. |
| Retrieval vs generation failure? | Right chunk missing = retrieval; chunk present but wrong answer = generation. |
| Agent safeguards? | Least-privilege tools, step/cost caps, human approval, traces. |
| Prompt injection? | Malicious instructions in untrusted content; treat retrieved text as untrusted. |
| Sample size rule of thumb? | n ≈ 16σ²/Δ² per group (α 5%, power 80%). |
| SRM? | Sample ratio mismatch — assignment bug; invalidates the test. |
| CUPED? | Variance reduction using pre-experiment covariates. |
| B2B experiment unit? | Account level (cluster) because users interact. |
| NIST AI RMF functions? | Govern, Map, Measure, Manage. |
| EU AI Act tiers? | Unacceptable, high, limited, minimal risk. |
| North Star for Katalon (hypothesis)? | Weekly active teams executing automated tests. |
| Team build order? | Platform/AE -> embedded analysts -> DS/ML/AI -> governance depth. |
| 100-day plan? | Listen, Fix, Plan. |
| Core framework (technical)? | Context, Choice, Trade-off, Metric. |
| Core framework (behavioural)? | STAR-R (+ Reflection). |

---

## 24. Last-hour checklist

- [ ] Say the **K-A-T-A-L-O-N** spine from memory.
- [ ] 100-day plan in 60 seconds (Listen, Fix, Plan).
- [ ] Two SQL queries written without looking (activation, NRR).
- [ ] One Kafka answer and one Airflow answer with a trade-off each.
- [ ] RAG pipeline drawn on paper in 90 seconds.
- [ ] GDPR vs CCPA in 30 seconds; erasure-in-a-lake answer.
- [ ] Four stories with real numbers (S1, S2, S4, S6).
- [ ] Three questions to ask.
- [ ] Never claim a number or tool you haven't used — say "I haven't run X in production; here's how I'd evaluate it."

🟡 **Final mindset:** they are hiring a leader who is hands-on enough to be credible and strategic enough to be trusted. Anchor every answer on a *business outcome*, show the *trade-off*, and finish with the *metric*.

---

*Illustrative numbers and examples in this guide are for practice only. Regulatory details (deadlines, thresholds, applicability) should be confirmed with counsel; Katalon product and stack details are hypotheses to verify with the interviewers.*
