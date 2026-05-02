# Procedural vs. Declarative Data Processing in Databricks: Which One Should You Choose?

*A practical breakdown of two fundamental paradigms — with real code, decision frameworks, and when to use each*

---

By **Prem Vishnoi** · Head of Data & AI · 10 min read

---

Every data pipeline you've ever written sits somewhere on a spectrum. At one end, you're telling the system *exactly* what to do and in what order. At the other, you're describing *what you want* and letting the engine figure out how to get there.

That's the procedural vs. declarative divide — and in Databricks, this choice has real consequences for pipeline complexity, team velocity, operational overhead, and cost.

This article breaks down both paradigms clearly, maps them to the Databricks ecosystem, gives you working code for each, and ends with a decision framework you can actually use.

---

## The Core Difference, in One Sentence

**Procedural:** *"Read this table. Filter these rows. Cache the result. If the count exceeds 1M, repartition. Write it here."*

**Declarative:** *"This table should exist, derived from that table, containing only valid records."*

One tells the engine how. The other tells the engine what. Everything else flows from that distinction.

---

## Procedural Data Processing

### What It Is

Procedural processing follows a structured, step-by-step approach. You explicitly define the order of operations, manage memory and caching, handle errors, and control execution flow. It maps directly to imperative programming — you're writing instructions, not descriptions.

### Characteristics

- **Step-by-step execution** — you dictate the sequence
- **Control structures** — loops, conditionals, and branching are first-class citizens
- **Fine-grained resource control** — manual caching, repartitioning, custom checkpointing
- **Explicit error handling** — you decide what happens when something breaks

### In Databricks: PySpark + Lakeflow Jobs

On Databricks, procedural pipelines are built with PySpark notebooks or scripts, orchestrated via **Lakeflow Jobs**. Each step can be parameterized, retried independently, and monitored at the task level.

Here's a realistic example — an ETL pipeline with conditional branching based on data volume:

```python
from pyspark.sql import functions as F
from pyspark.sql.utils import AnalysisException
import logging

logger = logging.getLogger(__name__)

def process_sales_transactions(spark, env: str, batch_date: str):
    """
    Procedural ETL: explicit control flow, manual optimization,
    conditional branching based on runtime data characteristics.
    """

    # ── Step 1: Read source with explicit schema ──────────────────────────
    raw_df = (spark.read
        .format("delta")
        .option("versionAsOf", "latest")
        .table(f"{env}.bronze.sales_transactions")
        .filter(F.col("transaction_date") == batch_date))

    record_count = raw_df.count()
    logger.info(f"Loaded {record_count:,} records for {batch_date}")

    # ── Step 2: Conditional optimization based on data volume ─────────────
    if record_count > 1_000_000:
        logger.info("Large batch detected — repartitioning for skew mitigation")
        raw_df = raw_df.repartition(200, "store_id")
    else:
        raw_df = raw_df.repartition(20)

    # Cache for multi-step reuse — explicitly managed
    raw_df.cache()

    # ── Step 3: Apply business rules ──────────────────────────────────────
    cleaned_df = (raw_df
        .filter(F.col("transaction_amount") > 0)
        .filter(F.col("customer_id").isNotNull())
        .withColumn("transaction_date", F.to_date("raw_date", "yyyy-MM-dd"))
        .withColumn("margin_pct",
            F.round((F.col("revenue") - F.col("cost")) / F.col("revenue") * 100, 2))
        .drop("raw_date", "_corrupt_record"))

    # ── Step 4: Conditional routing based on data quality ─────────────────
    bad_records = cleaned_df.filter(F.col("margin_pct") < 0)
    bad_count = bad_records.count()

    if bad_count > 0:
        logger.warning(f"{bad_count} negative-margin records found — quarantining")
        (bad_records.write.format("delta")
            .mode("append")
            .option("mergeSchema", "true")
            .saveAsTable(f"{env}.quarantine.negative_margin"))
        cleaned_df = cleaned_df.filter(F.col("margin_pct") >= 0)

    # ── Step 5: Write to Silver ───────────────────────────────────────────
    (cleaned_df.write
        .format("delta")
        .mode("overwrite")
        .option("replaceWhere", f"transaction_date = '{batch_date}'")
        .option("optimizeWrite", "true")
        .saveAsTable(f"{env}.silver.sales_transactions"))

    # ── Step 6: Release memory ────────────────────────────────────────────
    raw_df.unpersist()
    logger.info(f"Pipeline complete — {cleaned_df.count():,} records written to Silver")
```

**Why this is procedural:** The developer controls everything — execution order, memory management (`cache`/`unpersist`), conditional branching on data volume and quality, and the explicit write action. The engine does what it's told.

When orchestrated via Lakeflow Jobs, each function call becomes a retryable, observable task with its own logs and alerts.

---

## Declarative Data Processing

### What It Is

Declarative processing abstracts the *how* entirely. You describe what tables should exist, how they relate to each other, and what quality rules they must satisfy. The engine resolves dependencies, builds an execution plan, manages compute, and handles retries — you don't touch any of that.

It's closer to writing a specification than writing a program.

### Characteristics

- **Abstraction of execution details** — no explicit reads, writes, or loops
- **Automatic optimization** — query planning, predicate pushdown, AQE, and dynamic partitioning applied automatically
- **Dependency resolution** — the engine builds the DAG from your table references
- **Reduced surface area** — less code, fewer places for bugs to hide

### In Databricks: Lakeflow Declarative Pipelines (formerly Delta Live Tables)

Databricks' declarative engine is **Lakeflow Declarative Pipelines**. You declare tables and expectations; the system handles everything else — including unifying batch and streaming under one syntax.

```sql
-- ── Bronze: Auto Loader ingestion, declared as a streaming table ──────────
CREATE OR REFRESH STREAMING TABLE bronze_sales_transactions
COMMENT "Raw sales transactions from ADLS landing zone"
AS SELECT
    *,
    current_timestamp() AS _ingested_at,
    'pos_system'        AS _source_system
FROM STREAM read_files(
    'abfss://landing@storage.dfs.core.windows.net/sales/',
    format         => 'json',
    inferSchema    => true,
    schemaHints    => 'transaction_amount DECIMAL(18,2)'
);


-- ── Silver: Declarative quality rules + transformations ───────────────────
CREATE OR REFRESH STREAMING TABLE silver_sales_transactions (
    CONSTRAINT valid_amount   EXPECT (transaction_amount > 0)        ON VIOLATION QUARANTINE,
    CONSTRAINT valid_customer EXPECT (customer_id IS NOT NULL)        ON VIOLATION DROP ROW,
    CONSTRAINT valid_date     EXPECT (transaction_date IS NOT NULL)   ON VIOLATION FAIL UPDATE
)
COMMENT "Cleansed, validated sales transactions"
TBLPROPERTIES (
    'pipelines.autoOptimize.zOrderCols' = 'transaction_date,store_id',
    'delta.enableChangeDataFeed'        = 'true'
)
AS SELECT
    transaction_id,
    customer_id,
    store_id,
    TO_DATE(raw_date, 'yyyy-MM-dd')                                AS transaction_date,
    CAST(transaction_amount AS DECIMAL(18,2))                      AS transaction_amount,
    ROUND((revenue - cost) / revenue * 100, 2)                     AS margin_pct,
    current_timestamp()                                            AS _silver_processed_at
FROM STREAM(LIVE.bronze_sales_transactions);


-- ── Gold: Business metric, auto-refreshed when Silver updates ─────────────
CREATE OR REFRESH MATERIALIZED VIEW gold_daily_store_revenue
COMMENT "Daily revenue by store — primary KPI table for BI"
AS SELECT
    transaction_date,
    store_id,
    COUNT(*)                       AS transaction_count,
    SUM(transaction_amount)        AS total_revenue,
    AVG(margin_pct)                AS avg_margin_pct,
    current_timestamp()            AS _gold_refreshed_at
FROM LIVE.silver_sales_transactions
GROUP BY transaction_date, store_id;
```

**Why this is declarative:** There are no `read`, `write`, `cache`, or `repartition` calls anywhere. The pipeline declares what three tables should look like and what rules they must satisfy. Lakeflow handles everything else automatically:

- Builds the dependency DAG (`bronze → silver → gold`)
- Unifies batch and streaming execution under one syntax
- Enforces data quality and routes quarantined records
- Applies Auto Optimizer (file compaction, Z-ordering, AQE)
- Manages retries, checkpointing, and schema evolution
- Publishes lineage, quality metrics, and pipeline observability

---

## Side-by-Side Comparison

| Aspect | Procedural (PySpark + Lakeflow Jobs) | Declarative (Lakeflow Declarative Pipelines) |
|---|---|---|
| **Control** | Full control over execution flow & resources | Execution handled and optimized by the system |
| **Complexity** | Can become verbose; harder to maintain at scale | Concise, self-documenting, readable by non-engineers |
| **Optimization** | Manual — caching, repartition, skew handling | Automatic — AQE, Auto Optimize, predicate pushdown |
| **Flexibility** | Very high, but requires deep Spark expertise | Lower explicit control; easier to scale and govern |
| **Error handling** | Custom try/catch, conditional branching | Declarative expectations with quarantine/drop/fail modes |
| **Lineage** | Manual instrumentation required | Automatic column-level lineage, published by default |
| **Streaming** | Structured Streaming with explicit state management | Unified batch/streaming, same syntax, auto-checkpointing |
| **Team accessibility** | Requires Python/Scala engineers | Accessible to SQL practitioners and analytics engineers |

---

## When to Choose Each

The decision isn't about which paradigm is better. It's about matching the tool to the problem.

### Choose Procedural When...

**You need fine-grained execution control.** If your pipeline's correct behavior depends on doing things in a specific order — read, validate, decide, branch, write to one of three places based on a runtime condition — procedural is the right model. Declarative engines abstract away that control.

**Transformation logic is genuinely complex.** Complex state management, non-standard windowing, custom aggregation functions, or ML inference mid-pipeline — these are hard or impossible to express declaratively. PySpark gives you the full Spark API and Python ecosystem.

**You're doing low-level performance tuning.** If you know your data has a hot key causing skew, or you need a very specific partition strategy for downstream read patterns, manual `repartition`, `salting`, and `cache` give you control the declarative engine can't match.

**You're integrating with external systems.** REST API calls, writing to message queues, conditional alerts, custom encryption — these live outside the declarative model. Procedural notebooks with Lakeflow Jobs handle them naturally.

**You're migrating legacy ETL code.** Porting an existing PySpark or SQL Server SSIS pipeline to Databricks procedurally is faster and lower risk than rewriting it declaratively from scratch.

### Choose Declarative When...

**SQL-based transformations cover your use case.** If your pipeline is fundamentally "read from here, join these tables, apply these rules, write there" — and that's the majority of enterprise analytics — declarative is faster to build, easier to maintain, and better governed out of the box.

**You need automatic data quality enforcement.** Declarative pipelines let you define expectations once at the table level. They're enforced at every run, violations are logged, and bad records are quarantined or dropped automatically. Procedural pipelines need this logic written and maintained manually.

**Cross-functional teams own the pipelines.** Analytics engineers, SQL practitioners, and domain data owners can read and modify declarative pipelines without Spark expertise. Procedural pipelines require Python/Scala engineers in the loop for every change.

**You need lineage and observability without instrumentation.** Lakeflow Declarative Pipelines publish column-level lineage automatically. With procedural pipelines, lineage requires manual instrumentation or third-party tools.

**You're building the Silver/Gold layers of a Medallion architecture.** The medallion pattern — Bronze, Silver, Gold — is a near-perfect fit for declarative pipelines. Each layer is a set of tables with defined inputs, transformations, and quality rules. That's exactly what declarative engines are designed to express.

---

## The Practical Reality: Hybrid Is Normal

In production, most mature data platforms use both paradigms — in different parts of the same pipeline.

A common pattern at enterprise scale:

```
[Source Systems]
      │
      ▼
[Lakeflow Jobs: Procedural]          ← Custom connectors, API ingestion,
      │   PySpark notebooks            legacy system extraction
      │
      ▼
[Bronze Delta Tables]
      │
      ▼
[Lakeflow Declarative Pipelines]    ← Bronze → Silver → Gold
      │   SQL + DLT expectations       Medallion transformations
      │                                Data quality enforcement
      ▼
[Gold Delta Tables]
      │
      ├──▶ [SQL Warehouses: BI tools]
      │
      └──▶ [Lakeflow Jobs: Procedural] ← ML feature engineering,
                PySpark notebooks         custom model scoring,
                                          external API callbacks
```

The ingestion layer is procedural because source systems are messy and require custom handling. The core Medallion transformations are declarative because they're well-structured and benefit from automatic optimization and lineage. The ML layer dips back into procedural because feature engineering and inference require the full Python ecosystem.

**Starting point recommendation:** Default to declarative. Lakeflow Declarative Pipelines cover roughly 80% of modern data engineering use cases. Add procedural components only where the declarative model genuinely can't express what you need — not because procedural feels more familiar.

---

## Quick Decision Reference

> **"Is my transformation expressible as a SQL SELECT or a table dependency?"**
> → Declarative. Use Lakeflow Declarative Pipelines.

> **"Do I need to branch based on runtime data conditions, call external APIs, or apply custom state logic?"**
> → Procedural. Use PySpark notebooks with Lakeflow Jobs.

> **"Do I need both?"**
> → Build the stable, well-defined transformations declaratively. Wrap the edge cases in procedural jobs that feed into or read from the declarative pipeline.

---

## Closing Thoughts

The procedural vs. declarative debate in data engineering often gets framed as old-school vs. modern, or control vs. simplicity. Neither framing is right.

Procedural processing gives you a programming language — expressive, flexible, powerful, and appropriately complex for the problems it solves well. Declarative processing gives you a specification language — concise, self-documenting, and optimized for the 80% of analytics engineering that is fundamentally about table relationships and data quality.

The right answer for most teams: start declarative, stay declarative as long as you can, and reach for procedural only when the declarative model runs out of expressiveness. On Databricks, both paradigms are first-class — PySpark + Lakeflow Jobs on one side, Lakeflow Declarative Pipelines + SQL on the other — and they're designed to be composed, not chosen between.

---

*Prem Vishnoi is Head of Data & AI, building multi-market data platforms on Azure Databricks. He writes about data engineering architecture, distributed systems, and practical AI.*

---

*Tags: #DataEngineering #Databricks #PySpark #DeltaLake #DeltaLiveTables #LakeflowPipelines #DataArchitecture #ETL #BigData #Analytics*
