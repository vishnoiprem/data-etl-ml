# Azure for Data Engineering — CTO / Principal Study Plan

**Source course:** Data Vidhya — *Azure Data Engineering* by Darshil Parmar.
**Course URL:** https://datavidhya.com/learn/azure-data-engineering/
**Coverage:** 4 modules • 22 lessons
**Audience:** Data engineers targeting **Staff → Principal → Director →
VP/CTO** track on Microsoft Azure.

> **How to use this file.** Each lesson is broken into four lenses:
>
> 1. **Theory** — mental model, the architecture primitive, why it exists.
> 2. **Practical Example** — concrete scenario with code, numbers, costs.
> 3. **AI Use Case** — where GenAI / ML slots in or on top of this lesson.
> 4. **CTO / Principal Motivation** — the *career reason* to invest; what
>    decisions you will be trusted with at senior levels.
>
> The Microsoft Azure data stack is functionally similar to AWS but the
> **strategic differentiators** are different: Entra ID (best-in-class
> identity), Synapse (tight SQL + Spark coupling), Fabric (the unified
> lakehouse play), and deep integration with Microsoft 365 + Power BI.
>
> The Azure CTO's pitch: "your data, your AI, your apps, all on one
> trusted platform, all governed by Entra ID, all queryable through Fabric."

---

# Module 1 · Azure Data Engineering Stack (6 lessons)

## Lesson 1 — Data Factory

### Theory

Azure Data Factory (ADF) is Microsoft's **data integration orchestrator** —
the Azure equivalent of AWS Glue + Step Functions combined. Mental model:

- **Pipelines** are the top-level workflows; each contains one or more
  **activities**.
- **Activities** are the unit of work: copy data, run a Databricks
  notebook, execute a stored proc, run an SSIS package, trigger a
  webhook, etc.
- **Datasets** define the shape of input/output data (table or file
  schema).
- **Linked Services** are connection strings to external systems
  (S3/Blob/SQL/Databricks/etc.).
- **Triggers** schedule pipelines: schedule (cron), tumbling window
  (event-time), event-based (storage event arrives), or manual.
- **Integration Runtime (IR)** is the compute: Azure-hosted, self-hosted,
  or SSIS.

The ADF visual canvas is its superpower (and its curse) — non-engineers
can drag-drop a pipeline, but scaling requires dropping into JSON ARM
templates.

### Practical Example

A 5-stage daily ETL:

```
[Blob trigger] → [Copy activity: SQL → Parquet on ADLS Gen2]
              → [Databricks activity: bronze → silver Iceberg]
              → [Stored proc: refresh materialized view in Synapse]
              → [Web activity: post status to Teams]
              → [If Condition: rowcount > 0 → success; else → alert]
```

Cost: ADF runs are billed per activity-run + DIU-hour. A 5-activity
daily run × 30 = ~$5/month for orchestration, plus actual compute cost
of each backing service.

### AI Use Case

**Copilot for Data Factory** (GA in 2024) is the headline AI feature:
describe a pipeline in natural language → ADF generates the canvas.

> *"Copy all tables from the sales SQL database to the gold container as
> Parquet, partitioned by date"*

generates the linked services, datasets, and pipeline. As a Principal,
your job: define the **Copilot guardrails** — which sources are
allowed, which sinks are approved, which transformations must remain
human-reviewed (PII, financial data).

### CTO / Principal Motivation

ADF is where Microsoft fights AWS Glue. The Principal-level call: "do we
use ADF or do we use Databricks Workflows?" They overlap by ~70%; the
remaining 30% is **your team's skills**. ADF for SQL-heavy teams, Databricks
Workflows for Spark-heavy teams. The CTO's question: "is our data
integration vendor concentrated on Microsoft, and is that the right call?"
That belongs in the multi-year platform strategy.

---

## Lesson 2 — Synapse Analytics

### Theory

Azure Synapse is Microsoft's **analytics convergence product** — a single
workspace bundling:

- **Serverless SQL pool** — pay-per-query Trino/Spark-like SQL over
  data lake files.
- **Dedicated SQL pool** — provisioned MPP warehouse (formerly SQL DW).
- **Apache Spark pool** — managed Spark with notebooks.
- **Data Explorer pool** — Kusto-style log analytics.
- **Synapse Pipelines** — embedded ADF.
- **Synapse Link** — direct querying of operational stores (Cosmos DB,
  SQL DB) without ETL.

**Synapse vs Databricks vs Fabric:** Synapse is "best when your analysts
speak SQL and your warehouse is in Azure." Databricks is "best when your
team speaks PySpark and you need ML." Fabric is "best when you want the
whole thing in one SaaS package."

### Practical Example

```sql
-- Serverless SQL: query a Parquet file directly from ADLS Gen2
SELECT count(*) AS rows_loaded,
       count(DISTINCT user_id) AS unique_users
FROM OPENROWSET(
    BULK 'https://lake.dfs.core.windows.net/silver/events/year=2026/month=09/*/*',
    FORMAT = 'PARQUET'
) AS rows;
```

Cost: serverless SQL is billed per TB scanned. ~$5/TB. Same price as
Athena with similar ergonomics.

### AI Use Case

**Copilot for Synapse** generates SQL from natural language, fixes T-SQL
bugs, and explains stored procedures. The Principal's call: "Copilot is
on for analysts in dev, off for production financial models until we
audit the generated queries."

### CTO / Principal Motivation

Synapse occupies the same strategic slot as Redshift + Athena on AWS.
The Principal owns the **Synapse instance sizing** and the **Dedicated
SQL Pool pause schedule** (always pause off-hours). The CTO's question:
"is Synapse the right data warehouse, or should we use Snowflake / Fabric
/ Databricks SQL?" The answer usually depends on existing Microsoft
contracts and SQL skill in the team.

---

## Lesson 3 — Azure Databricks

### Theory

Azure Databricks is Microsoft's **managed Spark + ML platform** — the
Databricks SaaS, deployed on Azure infrastructure, with deep integration
into Entra ID, ADLS Gen2, Synapse, and Power BI. Mental model:

- **Workspace** — top-level container (org → workspace).
- **Cluster** — Spark compute (all-purpose vs job, interactive vs
  automated).
- **Notebook** — interactive Spark/Python/SQL.
- **Job** — scheduled production workflow (orchestrated within
  Databricks Workflows).
- **Unity Catalog** — unified governance layer (table-level ACLs,
  lineage, PII tags).
- **Delta Lake / Delta Live Tables (DLT)** — managed Iceberg-compatible
  tables.
- **Databricks SQL** — serverless warehouse for analysts.
- **Mosaic AI** — managed ML training + serving.

### Practical Example

```python
# Databricks notebook: bronze → silver via DLT
import dlt
from pyspark.sql.functions import col

@dlt.table(comment="Cleaned click events")
@dlt.expect_or_drop("valid_user", "user_id IS NOT NULL")
def silver_events():
    return (
        dlt.read_stream("bronze.events")
        .withColumn("event_time", col("ts").cast("timestamp"))
        .dropDuplicates(["event_id"])
    )
```

DLT handles schema evolution, auto-loader, and expectations
(`expect_or_drop`) automatically. As a Principal, you set the
**expectations standard**: what counts as a row your pipeline guarantees.

### AI Use Case

**Mosaic AI + Foundation Model APIs** lets you fine-tune and serve
custom LLMs on Databricks compute, with the same governance as your
data. The 2026 frontier: **AI Functions** (`ai_classify`, `ai_extract`,
`ai_translate`) callable from SQL — no Python, no model deployment.

```sql
SELECT review_text,
       ai_classify(review_text, ['positive', 'neutral', 'negative']) AS sentiment
FROM reviews;
```

### CTO / Principal Motivation

Databricks on Azure is the **highest-skill** data engineering surface
on the platform. Principals who can architect a multi-job DLT pipeline
with Unity Catalog ACLs are scarce. The CTO's call: "do we go deeper on
Databricks (and pay the license) or does Synapse + ADF suffice?" The
answer determines whether your team can build ML or just analytics.

---

## Lesson 4 — Event Hubs

### Theory

Azure Event Hubs is the **Azure equivalent of Kinesis Data Streams +
Firehose + SQS** in one service. Mental model:

- **Event Hubs namespace** — DNS domain for multiple hubs.
- **Event Hub** — the actual stream (like a Kafka topic).
- **Partitions** — ordered shards within a hub (consumer parallelism).
- **Consumer groups** — independent read positions (like Kafka groups).
- **Capture** — automatic streaming archive to ADLS Gen2 (Firehose
  equivalent).
- **Throughput units / Processing units** — capacity (Standard: 1 MB/s
  ingress per TU; Premium: auto-scale).
- **Kafka protocol support** — Event Hubs accepts Kafka clients without
  code change.

### Practical Example

```python
# Producer (any language with AMQP/HTTPS/Kafka)
import asyncio
from azure.eventhub.aio import EventHubProducerClient

async def send(events):
    producer = EventHubProducerClient.from_connection_string(
        conn_str="Endpoint=sb://.../;SharedAccessKey=...;EntityPath=events",
        eventhub_name="events"
    )
    async with producer:
        batch = await producer.create_batch()
        for e in events:
            batch.add({"body": e})
        await producer.send_batch(batch)
```

Cost: 1 TU = $0.015/hr ≈ $11/mo per TU. Throughput: 1 MB/s ingress,
2 MB/s egress per TU.

### AI Use Case

**Event Hubs + Azure Stream Analytics + Azure OpenAI = real-time content
moderation.** Every chat message flows through Event Hubs → Stream
Analytics (window-aggregated) → Azure OpenAI (classify toxicity) → write
flagged message to Cosmos DB. Sub-second end-to-end, on a managed service.

### CTO / Principal Motivation

Event Hubs is Microsoft's strategic streaming play. The decision vs Kafka
on HDInsight / Confluent Cloud is a **vendor and skill** decision. The
Principal owns the **throughput sizing** and the **capture retention**.
The CTO's lever: "is our streaming spend consolidated, or does every team
spin up their own hub?" Hub sprawl is the silent cost driver.

---

## Lesson 5 — Azure Architecture

### Theory

The Azure reference architecture for a data engineer is:

```
Sources (App / IoT / SQL DB / Cosmos / SaaS)
    ↓
Ingestion (Event Hubs / ADF Copy / Synapse Link)
    ↓
Storage (ADLS Gen2 in Bronze / Silver / Gold layout)
    ↓
Processing (Databricks / Synapse Spark / Data Factory)
    ↓
Serving (Synapse SQL / Databricks SQL / Power BI)
    ↓
Consumption (Power BI / Fabric / custom apps / Copilot Studio)
```

The Fabric extension adds a **SaaS layer** over all of these — OneLake
is the unified storage, all compute surfaces read from it.

### Practical Example

A medallion architecture on ADLS Gen2 + Databricks:

```
bronze/events/        → raw JSON from Event Hubs Capture
silver/events/        → Delta Live Tables, dedupe + schema enforcement
gold/daily_kpi/       → aggregated KPIs for Power BI
gold/customer_360/    → feature store for ML
```

Power BI connects to Gold; Databricks jobs read Silver; ADF orchestrates
everything; Entra ID governs every access.

### AI Use Case

The AI tier adds: Azure OpenAI for RAG + NL→SQL, Azure ML for custom
model training, Document Intelligence for unstructured data, Copilot
Studio for chat UIs.

### CTO / Principal Motivation

The architecture diagram is **the first artifact** a CTO shows to a new
board member, customer, or hire. If you can't draw it on a whiteboard in
10 minutes, you don't know your own platform. Principals own the
architecture; CTOs own the **story** the architecture tells.

---

## Lesson 6 — Quiz: Azure DE Stack

### Theory

The quiz validates service-selection literacy on Azure. The Azure
decision tree for every data architecture:

- **Ingest:** Event Hubs (streaming), ADF Copy (batch), Synapse Link
  (operational-to-analytical).
- **Store:** ADLS Gen2 (lake), Cosmos DB (operational NoSQL), SQL DB
  (relational).
- **Process:** Databricks (Spark), Synapse Spark (one-off), ADF Mapping
  Data Flows (no-code).
- **Serve:** Synapse Dedicated SQL (warehouse), Databricks SQL (BI),
  Fabric (SaaS).
- **Orchestrate:** ADF Pipelines (visual), Databricks Workflows
  (Python), Synapse Pipelines (embedded).
- **Govern:** Unity Catalog (Databricks), Purview (Microsoft catalog),
  Entra ID (identity).

### Practical Example

For each service, write a one-sentence "use this when…" rule.

### AI Use Case

Encode the rules in an internal `copilot-instructions.md` so AI
assistants default to your team's conventions.

### CTO / Principal Motivation

Service-selection literacy is the difference between Senior and Staff.
Staff pick the right service for the problem; Principals pick the right
service for the **team and the trajectory**. "We use ADF because we
can't afford a Databricks workspace yet" is a Principal answer.

---

# Module 2 · Batch Pipelines on Azure (6 lessons)

## Lesson 1 — Ingesting Data

### Theory

Five canonical ingestion patterns on Azure:

| Pattern              | Tool                       | Use case |
|----------------------|----------------------------|----------|
| Change Data Capture  | ADF + SQL CDC, Debezium    | SQL DB → Synapse / ADLS |
| File transfer        | Azure Storage SFTP, AzCopy | SFTP/FTP → ADLS Gen2 |
| SaaS connector       | ADF + Logic Apps + Fivetran | SaaS → ADLS |
| Streaming ingest     | Event Hubs Capture         | Real-time → ADLS |
| Operational analytical | Synapse Link             | Cosmos / SQL → Synapse direct |

### Practical Example

Synapse Link for Cosmos DB → Synapse SQL:

```sql
-- Enable Synapse Link on the Cosmos DB account (one-time, in portal)
-- Enable the container link
-- Then from Synapse: query Cosmos directly
SELECT TOP 100 *
FROM CosmosDB.[database].products
WHERE category = 'electronics';
```

Cost: Synapse Link is included; queries are billed per Synapse SQL
(DWU-hour or serverless TB-scanned).

### AI Use Case

**AI-powered schema evolution detection.** A Logic App watches the
Cosmos DB schema, calls Azure OpenAI to detect drift, and alerts the
data platform team when a new field appears. Auto-documents the change.

### CTO / Principal Motivation

Ingestion is where data quality is born or killed. The Principal owns
the **freshness SLA** ("operational data < 15 min") and the **vendor
call** (Fivetran vs. ADF vs. custom Lambda-equivalent). The CTO's question:
"is our ingestion single-vendor (Fivetran) or multi-vendor (ADF +
Fivetran + custom)?" Both are valid; the answer is in the contract
review.

---

## Lesson 2 — Delta Lakehouse

### Theory

Delta Lake (Lakehouse) is the **default storage format** on Databricks
and increasingly on Synapse + Fabric. Mental model:

- **Delta table** — Parquet files + a transaction log (`_delta_log/`).
- **ACID transactions** — every write is committed atomically.
- **Time travel** — query a snapshot from any version or timestamp.
- **Schema enforcement** — writes fail if schema doesn't match.
- **Schema evolution** — add columns without rewriting data.
- **Liquid clustering** (replacing partitioning) — auto-clustering based
  on query patterns.
- **UniForm** — read Delta tables as Iceberg, no copy needed.
- **Deletion vectors** — efficient row-level deletes.

### Practical Example

```sql
-- Create a Delta table from Synapse serverless SQL
CREATE EXTERNAL TABLE gold.daily_kpi
WITH (LOCATION = 'abfss://gold@lake.dfs.core.windows.net/daily_kpi/',
      DATA_SOURCE = LakeStorage,
      FILE_FORMAT = Delta)
AS
SELECT event_date, count(*) AS events
FROM silver.events
GROUP BY event_date;
```

```sql
-- Time travel
SELECT * FROM gold.daily_kpi VERSION AS OF 42;
SELECT * FROM gold.daily_kpi TIMESTAMP AS OF '2026-09-15 00:00:00';
```

### AI Use Case

**Delta + Unity Catalog = AI feature store.** Point-in-time correctness
is built in. The Principal's deliverable: "ML features live as versioned
Delta tables, queried by both training jobs and online serving." This is
the 2026 lakehouse-on-Azure value-prop.

### CTO / Principal Motivation

Lakehouse is the **strategic bet** Microsoft made (via Fabric) to
counter Databricks + Snowflake. Principals who can stand up a Delta
lakehouse on ADLS Gen2 with Unity Catalog ACLs become the most
valuable person in the room when the company asks "why are we paying
$X to Databricks?" Answer: "we can run the same workloads on Fabric for
half the cost." $500k/year win.

---

## Lesson 3 — Transformation & dbt

### Theory

dbt (data build tool) sits **on top of** the warehouse. On Azure, dbt
can target Synapse Dedicated SQL, Synapse Serverless, Databricks SQL,
or Snowflake (via cross-cloud). Mental model:

- **Models** are SELECT statements; dbt builds them as tables or views.
- **Materializations** — view, table, incremental, ephemeral.
- **Sources** define incoming tables (with freshness tests).
- **Tests** — not_null, unique, accepted_values, custom SQL.
- **Snapshots** — SCD Type 2 history.
- **dbt Cloud** — managed orchestrator + CI/CD + docs.

### Practical Example

```sql
-- models/gold/daily_kpi.sql
{{ config(materialized='table') }}

WITH events AS (
    SELECT * FROM {{ ref('silver_events') }}
    WHERE event_date >= dateadd('day', -30, current_date())
)
SELECT event_date,
       count(*) AS events,
       count(DISTINCT user_id) AS users
FROM events
GROUP BY event_date
```

```yaml
# models/sources.yml
sources:
  - name: silver
    database: lakehouse
    schema: silver
    tables:
      - name: events
        freshness:
          error_after: {count: 6, period: hour}
        loaded_at_field: event_loaded_at
```

When `silver.events` is older than 6 hours, dbt's `source freshness`
fails → CI pipeline fails → on-call alerted.

### AI Use Case

**dbt + Copilot.** Copilot generates dbt models from natural language,
writes tests, and suggests column descriptions. The Principal's call:
"Copilot is on for skeleton generation, off for production transforms
until reviewed."

### CTO / Principal Motivation

dbt is **the** transformation tool for analytics engineers. The Principal
delivers a **dbt project standard** (folder layout, naming, test coverage).
The CTO's lever: dbt is the cheapest productivity multiplier you can
adopt — every model is documentation, test, and lineage for free.

---

## Lesson 4 — Batch Orchestration

### Theory

Three orchestrators on Azure:

| Tool                | Type              | When to use |
|---------------------|-------------------|-------------|
| ADF Pipelines       | Visual / JSON     | ADF-heavy shops, large teams |
| Databricks Workflows| Python / JSON     | Databricks-heavy shops |
| Azure Data Factory + Airflow | Self-managed Airflow on AKS | When you need full Airflow |

### Practical Example

A Databricks Workflow with task dependencies:

```python
# Python SDK for Databricks Workflows
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

job = w.jobs.create(
    name="nightly_events",
    tasks=[
        {"task_key": "bronze", "notebook_task": {"notebook_path": "/etl/bronze"}},
        {"task_key": "silver",
         "depends_on": [{"task_key": "bronze"}],
         "notebook_task": {"notebook_path": "/etl/silver"}},
        {"task_key": "gold",
         "depends_on": [{"task_key": "silver"}],
         "notebook_task": {"notebook_path": "/etl/gold"}},
        {"task_key": "notify",
         "depends_on": [{"task_key": "gold"}],
         "email_task": {"to": "data-platform@example.com",
                        "subject": "Nightly ETL Complete"}},
    ],
    schedule={"quartz_cron_expression": "0 0 6 * * ?",
              "timezone_id": "UTC"},
)
```

### AI Use Case

**Workflow debugging assistant.** A Logic App watches failed tasks,
calls Azure OpenAI with the error logs, posts a Teams message: "the
silver task failed because column X has nulls — likely cause is upstream
parquet drift." 70% MTTR reduction.

### CTO / Principal Motivation

Orchestration choice is **sticky** — moving from ADF to Databricks
Workflows (or vice versa) is a 6-month project. The Principal's job:
pick right the first time. The CTO's question: "if Azure has an outage,
can we still run our pipelines?" Multi-region, multi-cloud orchestration
becomes a board topic at certain company sizes.

---

## Lesson 5 — Batch Architecture

### Theory

The Azure reference architecture mirrors the AWS one:

```
Sources → Ingest (ADF/Event Hubs/Databricks Auto Loader)
       → Storage (ADLS Gen2 in bronze/silver/gold)
       → Process (Databricks DLT / Synapse Spark / dbt)
       → Serve (Synapse SQL / Databricks SQL / Fabric)
       → Consume (Power BI / custom apps / Copilot)
```

Each layer is **idempotent** (re-runnable, same output) and **observable**
(freshness, error rate, latency).

### Practical Example

End-to-end:

```sql
-- ADF copies from SQL DB to ADLS bronze (Parquet, daily)
-- Databricks DLT reads bronze → silver (Delta, schema enforced, dedup)
-- Databricks SQL materializes gold (Delta, with dbt tests)
-- Power BI connects to Gold
-- Microsoft Fabric mirrors Gold to OneLake for SaaS BI
```

### AI Use Case

The AI tier: Azure OpenAI for RAG + NL→SQL, AI Search for vector search,
Document Intelligence for PDFs, Copilot Studio for chat UIs.

### CTO / Principal Motivation

The medallion architecture is **the** data architecture pattern in 2026.
Every Principal can defend it; every CTO can read it. The board-level
value: a clear separation of "what we collect" (bronze) from "what we
trust" (gold). This is the data-governance story.

---

## Lesson 6 — Quiz: Batch Pipelines on Azure

### Theory

The quiz validates architecture decisions. The principle: **every batch
pipeline is a DAG with three layers** (ingest → process → serve) and
**two characteristics** (idempotent, observable).

### Practical Example

For each pattern, write a one-sentence rule:
- *Bronze storage format:* "Parquet in ADLS Gen2, partitioned by date."
- *Orchestrator choice:* "ADF for visual shops, Databricks Workflows for
  Spark shops, Airflow for hybrid."

### AI Use Case

Encode the rules in `copilot-instructions.md` so AI assistants default
to your team's conventions.

### CTO / Principal Motivation

Quiz yourself on **failure modes**, not happy paths. "What happens if
Synapse pauses mid-job?" "What happens if ADF fails on day 30 of 30?"
Principal-level engineers think in failure modes; CTOs think in incident
simulations.

---

# Module 3 · Streaming on Azure (5 lessons)

## Lesson 1 — Event Hubs Deep Dive

### Theory

Event Hubs in depth. Mental model:

- **Partitions** — units of ordered throughput. Choose partition count
  at creation (can scale up, not down).
- **Throughput units (TU)** — Standard tier: 1 MB/s ingress, 2 MB/s
  egress per TU. Billed per hour.
- **Processing units (PU)** — Premium tier: auto-scale clusters.
- **Capture** — automatic streaming archive to ADLS Gen2 in Avro/Parquet.
- **Schema Registry** — enforced schema for events (Avro/JSON/Protobuf).
- **Geo-disaster recovery** — pairs of hubs in different regions.
- **Kafka protocol** — same client code as Kafka.

### Practical Example

Capacity math for 10K events/sec × 1 KB:

- 10 MB/s ingress. Standard tier: 10 TU.
- Cost: 10 TU × $0.015/hr × 730 hr = **$110/mo** for the hub itself.
- Event ingestion: 10K × 86400 × 30 × 1 KB = ~25 TB. Capture to ADLS
  included.
- Compared to Event Hubs Premium: ~$650/mo for the cluster, but no TU
  math, simpler ops.

### AI Use Case

**Schema Registry + Schema Evolution AI** — Azure Schema Registry is
already useful; the AI layer watches for breaking changes and generates
backward-compatible schemas automatically. Principal's call: enable
strict mode in prod, backward-compat mode in dev.

### CTO / Principal Motivation

Streaming capacity math is where over-provisioning happens. The
Principal's deliverable: a **TU auto-scaling script** based on
throughput metrics. The CTO's question: "what's our streaming cost per
million events?" That unit-economics answer shapes product decisions.

---

## Lesson 2 — Stream Processing

### Theory

Three stream processing options on Azure:

| Option               | What it is                | When to use |
|----------------------|---------------------------|-------------|
| Azure Stream Analytics | SQL-like query language  | Simple transforms, low-code |
| Spark Structured Streaming (Databricks) | Streaming Spark | Complex transforms, ML |
| Azure Functions on Event Hubs | Event-driven code | Per-message logic |

### Practical Example

Stream Analytics query — a 5-minute tumbling window count:

```sql
SELECT
    System.Timestamp AS window_end,
    event_type,
    COUNT(*) AS event_count
INTO
    outputBlob
FROM
    inputEventHub TIMESTAMP BY event_time
GROUP BY
    event_type,
    TumblingWindow(minute, 5)
```

This writes per-5-minute aggregates to ADLS Gen2, queryable from
Synapse Serverless SQL.

### AI Use Case

**Stream Analytics + Azure OpenAI for real-time content moderation.**
Every chat message → Event Hubs → Stream Analytics (windowing) →
Azure OpenAI (classify toxicity) → write flagged message to Cosmos DB.
Sub-second end-to-end on a managed service.

### CTO / Principal Motivation

Stream processing choice is often over-engineered. Most teams don't
need Spark Structured Streaming — they need Functions + Cosmos. The
Principal's call: "don't reach for Spark until you can articulate why
Functions + Cosmos isn't enough." CTOs approve the **streaming spend**
and the **operational complexity** trade-off.

---

## Lesson 3 — Event-Driven Patterns (Service Bus / Event Grid)

### Theory

Three messaging primitives on Azure:

| Service       | Pattern    | Delivery      | Use case |
|---------------|------------|---------------|----------|
| Service Bus   | Queue + Topic | At-least-once, ordered | Decouple producer/consumer |
| Event Grid    | Event bus  | At-least-once, push | Reactive cloud events |
| Storage Queues| Queue      | At-least-once | Cheap decouple |

**Decision rule:** "One consumer, want to buffer?" → Service Bus Queue.
"Many consumers, want fan-out?" → Service Bus Topic or Event Grid.
"Want cloud-events for resource changes?" → Event Grid.

### Practical Example

Event Grid for reactive Blob events:

```json
{
  "destination": {
    "endpointType": "WebHook",
    "properties": {
      "endpointUrl": "https://func-app.azurewebsites.net/runtime/webhooks/EventGridTrigger"
    }
  },
  "filter": {
    "subjectBeginsWith": "/blobServices/default/containers/raw",
    "and": [
      {"isSubjectCaseSensitive": false,
       "subjectEndsWith": ".csv"}
    ]
  }
}
```

When a CSV lands in `raw`, a Function runs to validate the schema →
moves to `bronze` if valid, alerts if invalid.

### AI Use Case

**Event Grid + Azure OpenAI = document processing.** A PDF uploaded to
Blob → Event Grid → Function → Document Intelligence → AI enrichment
via OpenAI → write summary to Cosmos DB. The Principal's deliverable:
"this is the document RAG pipeline."

### CTO / Principal Motivation

Event-driven is the **architectural style** that scales without adding
people. Principals who default to events ship 10× faster than teams
stuck on request-response. CTOs fund this style because every
event-driven service saves headcount.

---

## Lesson 4 — Streaming Architecture

### Theory

The Azure reference streaming architecture:

```
Source (App/IoT/CDC)
    ↓ Event Hubs (or Kafka)
    ├──→ Stream Analytics → ADLS Gen2 (aggregates)
    ├──→ Azure Function → Cosmos DB (real-time state)
    └──→ Databricks (Spark) → Delta Lake (historical + ML features)
```

Each arrow is a separate consumer; Event Hubs supports multiple
consumer groups.

### Practical Example

A driver-position streaming system:
- Mobile SDK → Event Hubs (10K events/s).
- Consumer 1: Functions → Cosmos DB (live positions, <100 ms).
- Consumer 2: Stream Analytics → ADLS (per-zone aggregates).
- Consumer 3: Databricks Structured Streaming → Delta Lake (ML features
  for surge prediction).

### AI Use Case

**AI at every layer.** Azure OpenAI classifies support messages in real
time. Azure ML endpoints score churn risk per session. Document
Intelligence processes uploaded forms. The Principal's deliverable:
"our streaming layer has AI hooks at every consumer."

### CTO / Principal Motivation

Streaming architecture is the **most expensive** and **most
differentiating** data work a company does. Principals who can stand up
this stack on Azure are scarce and well-compensated. CTOs approve it
because it unlocks product features that batch-only competitors can't
ship.

---

## Lesson 5 — Quiz: Streaming on Azure

### Theory

The quiz validates stream-selection literacy. The principle: **start
with the simplest primitive** (Storage Queue, Service Bus Queue) and
only reach for Event Hubs / Stream Analytics / Databricks when simpler
options don't suffice.

### Practical Example

The "streaming decision tree":
1. "Do I need real-time?" → If no, use a nightly ADF pipeline.
2. "Do I need event-time windows?" → If no, use Functions.
3. "Do I need fan-out?" → If yes, use Event Hubs or Service Bus Topic.
4. "Do I need stateful stream processing?" → If yes, use Spark
   Structured Streaming.

### AI Use Case

Encode the decision tree in an internal tool so AI assistants can guide
new engineers.

### CTO / Principal Motivation

The cost of over-engineering streaming is 10× the cost of under-
engineering it. Principals who default to "the simplest queue" save
their company from $500k/year in unnecessary Event Hubs spend.

---

# Module 4 · Running Azure Pipelines in Production (5 lessons)

## Lesson 1 — Monitoring & Alerts

### Theory

Azure Monitor is the **observability layer** of Azure. Mental model:

- **Metrics** — numeric time series (CPU, latency, error rate).
- **Logs** — structured text (Function logs, ADF logs, Synapse logs).
- **Alerts** — thresholds on metrics/logs; trigger Action Group
  (email/SMS/webhook/Logic App/Function/ITSM).
- **Dashboards** — visualizations.
- **Log Analytics** — query logs with KQL (Kusto Query Language).
- **Application Insights** — APM for custom apps.
- **Smart Detection** — ML-based anomaly detection.

### Practical Example

A pipeline-freshness alert — the most important alert in data
engineering:

```kql
// Log Analytics: alert when last ETL success was over 1 hour ago
Heartbeat_CL
| summarize LastHeartbeat = max(TimeGenerated) by PipelineName_s
| where LastHeartbeat < ago(1h)
```

Trigger: Action Group → email on-call + Teams webhook + ITSM ticket.

### AI Use Case

**AIOps with Azure Monitor + OpenAI.** A Function watches Log Analytics
queries, calls OpenAI to interpret anomaly patterns, posts to Teams
"the nightly silver job has been failing for 3 days — pattern suggests
upstream API change." AI-on-AI observability.

### CTO / Principal Motivation

Alerts are the **insurance policy** that pays for itself the first time
they fire. Principals own the **alert standard** ("every production
pipeline has 5 alerts"). CTOs see the **MTTR dashboard** — that's a
board metric.

---

## Lesson 2 — Cost Optimization

### Theory

The five cost levers on Azure, ranked by impact:

1. **Right-sizing** — bigger savings than Reserved Instances in most
   cases. Stop paying for a Synapse Dedicated Pool that's 80% idle.
2. **Pause / auto-pause** — Synapse Dedicated Pools can auto-pause after
   N minutes idle.
3. **Reserved Instances / Savings Plans** — 30-60% discount for 1-yr or
   3-yr commitments.
4. **Storage tiering** — ADLS Gen2 lifecycle (hot/cool/archive/cold).
5. **Cleanup orphaned resources** — unused disks, idle IPs, abandoned
   Synapse pools.

The principle: **cost optimization is a continuous practice, not a
quarterly project.**

### Practical Example

```powershell
# Find Synapse Dedicated Pools that are running but idle
Get-AzSynapseSqlPool -WorkspaceName "synapse-prod" |
  Where-Object {$_.Status -eq "Online" -and $_.Sku.Name -match "DW300"} |
  Select Name, Sku, LastActivityTime
```

A DW300c pool costs $5/hr → $3,600/mo. Pause it 12 hours/day → save
$1,800/mo. **$22k/year from one knob.**

### AI Use Case

**AI cost optimizers.** Azure Cost Management has built-in Advisor
recommendations. Third-party tools (CloudHealth, Spot.io) use LLMs to
recommend right-sizing. The Principal's call: which tool, and what's
the human review process.

### CTO / Principal Motivation

Cost optimization is the **most quantifiable** Principal contribution.
"$500k/year saved by pausing idle Synapse pools" is a promotion packet
bullet. CTOs fund cost-engineering roles because the ROI is obvious to
the CFO.

---

## Lesson 3 — Pipeline Security

### Theory

Three pillars on Azure:

1. **Identity** — Entra ID (formerly Azure AD), Managed Identity,
   least-privilege RBAC.
2. **Encryption** — at rest (CMK with Key Vault) and in transit (TLS).
3. **Network** — private endpoints, VNet integration, Service Endpoints.

**Defense in depth:** never rely on a single layer. Even if ADLS is
public, the CMK should reject unauthorized decryption.

### Practical Example

A secure ADF pipeline:
- Runs with a **System-Assigned Managed Identity** (no secrets in code).
- RBAC: `Storage Blob Data Contributor` on the specific container,
  nothing else.
- Storage account: **private endpoint** in the VNet, public access
  disabled.
- Encryption: customer-managed key in Key Vault, auto-rotation enabled.
- Logs: every ADF run + every Storage operation logged to Log Analytics.

### AI Use Case

**AI agents with Managed Identity.** As agents proliferate, "machine
identity" becomes the dominant security concern. The Principal's
deliverable: "every AI agent gets a Managed Identity scoped to one
purpose, with conditional access policy applied."

### CTO / Principal Motivation

Security is the **non-negotiable**. Principals who ship insecure
pipelines get fired. CTOs who ignore security get breached. The
Principal's deliverable: a **security review checklist** that every
pipeline must pass before production.

---

## Lesson 4 — CI/CD for Pipelines

### Theory

CI/CD for Azure pipelines means:

1. **Version control** — code, IaC (Bicep / Terraform), configs in Git.
2. **Automated tests** — unit (functions), integration (small data),
   schema (column-level diffs).
3. **Staging environment** — mirror of production, isolated data.
4. **Deployment** — blue/green or canary on production pipelines.
5. **Observability** — same alerts in dev as in prod.

The tools: **Azure DevOps**, **GitHub Actions**, **Terraform Cloud**.

### Practical Example

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include: [main]
  paths:
    include: [pipelines/**]

stages:
  - stage: test
    jobs:
      - job: unit_tests
        steps:
          - script: pytest tests/unit/
          - script: pytest tests/integration/ --env=staging
  - stage: deploy_prod
    dependsOn: test
    condition: succeeded()
    jobs:
      - job: deploy_adf
        steps:
          - task: AzureResourceManagerTemplateDeployment@3
            inputs:
              deploymentScope: 'Resource Group'
              azureSubscription: 'prod-spn'
              action: 'Create Or Update Resource Group'
              resourceGroupName: 'rg-data-prod'
              templateFile: 'infra/adf-pipelines.json'
```

### AI Use Case

**AI code review on Bicep / Terraform.** Use Azure OpenAI or GitHub
Copilot to review PRs for: missing encryption, public storage accounts,
hard-coded secrets, untagged resources. The Principal's deliverable:
"every PR to `data-platform/` is reviewed by AI + a human."

### CTO / Principal Motivation

CI/CD maturity is the **leading indicator** of platform reliability.
Teams with mature CI/CD have 5× fewer incidents than teams without.
Principals own the **pipeline-of-pipelines** (the meta-pipeline that
deploys pipelines). CTOs see the **deployment frequency** dashboard —
that's a DORA metric that the board understands.

---

## Lesson 5 — Quiz: Running Azure Pipelines in Production

### Theory

The production-readiness checklist for Azure:

| Aspect        | Question |
|---------------|----------|
| Monitoring    | Do we have alerts on freshness, error rate, latency, cost? |
| Security      | Least-privilege RBAC? Entra ID + Managed Identity? Customer-managed keys? |
| Cost          | Right-sized? Paused when idle? Reserved Instances? |
| Reliability   | Multi-region? Geo-DR enabled? Backup and restore tested? |
| CI/CD         | Every change reviewed, tested, deployable in <30 min? |
| Documentation | Runbook for every alert? Architecture diagram current? |

### Practical Example

For each pipeline, maintain a **production-readiness scorecard**. The
goal: 100% green before declaring GA.

### AI Use Case

Use AI to auto-generate runbooks from Azure Monitor alerts. "When this
alert fires, here's the investigation checklist" — generated from the
last 5 incident retrospectives.

### CTO / Principal Motivation

Production readiness is a **cultural standard**. The Principal's
contribution: "no pipeline ships without 100% on the scorecard." CTOs
enforce this at the platform level. The board sees the **reliability
metric** — uptime, MTTR, incident count — and that's the data-platform
brand.

---

# Closing Notes

## The Promotion Path from this Course

| Level        | Skill unlocked by this course | Compensation signal |
|--------------|-------------------------------|---------------------|
| Senior DE    | Hands-on Azure data pipeline build/deploy | $150-200k |
| Staff DE     | Architecture decisions across the Azure stack | $200-280k |
| Principal DE | Platform-level decisions; Purview + Fabric + Entra governance | $280-400k |
| Director / VP | Org-level platform strategy; EA cost & headcount ownership | $350-500k+ |
| CTO          | Azure vs AWS vs GCP strategy; EA negotiation; board communication | $400-700k+ |

## The Azure-Specific Differentiator

Unlike AWS, Azure has **three P's** the Principal must master:

1. **Purview** — Microsoft Purview is the unified governance catalog
   (think Glue Catalog + Lake Formation + DataHub combined). Owners of
   Purview own the company's **data map**.
2. **Power BI + Fabric** — the SaaS analytics layer. Power BI Premium
   per-user + Fabric capacity is the third-largest line item after
   compute and storage. The Principal's lever is right-sizing Fabric
   SKUs.
3. **Entra ID** — best-in-class identity. The Principal's edge is
   understanding Entra ID conditional access, Managed Identity, and
   service principals deeply — most Azure security incidents trace
   back to misconfigured identities.

## The Single Most Important Habit

After each lesson, write a **1-page memo**: "If asked about this topic
in an executive review, here's what I would say." That habit — turning
technical knowledge into **defensible artifacts** — is what separates
engineers who plateau at Staff from engineers who make Principal and
beyond.

## Cross-References

- **AWS DE CTO plan** — `aws_de_cto_learning_plan.md` in this folder
  (parallel structure).
- **Azure DE full article bodies** — to be added as the data-vidhya
  extraction continues.
- **DE Foundations track** — `01_de_foundations_track.md`.
- **Snowflake course** — see Snowflake full-detail curriculum.
