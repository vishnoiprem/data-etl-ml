# 04 — ETL Pipeline Tools & Technologies

> **Lesson 4 of 5 — Overview**

The tool landscape changes every two years. Hadoop was the answer in
2014. Spark in 2018. dbt + lakehouse in 2022. Agentic pipelines in
2026. This lesson is the *map* — not the territory. The interview
asks "what would you use?" and you need to know what the options are
and when each is right.

---

## 1. The five categories of tools

Every pipeline tool fits into one of five categories. Memorize the
shape, not the brand:

| Category | What it does | 2026 examples |
|---|---|---|
| **Orchestration** | Schedules + sequences tasks | Airflow, Dagster, Prefect, K8s CronJobs |
| **Ingestion** | Pulls data from sources | Debezium (CDC), Fivetran, Airbyte, custom Python |
| **Storage** | Stores data at rest | S3/GCS, Delta Lake, Iceberg, Hudi |
| **Transformation** | Runs business logic | dbt, Spark, Flink, Beam, custom Python |
| **Serving** | Exposes data to consumers | Snowflake, BigQuery, Redshift, ClickHouse, Druid |

The categories map onto the boxes you draw. A senior design names
*one* tool per category and says "given the requirements, this is
the right call."

---

## 2. Orchestration: Airflow, Dagster, Prefect

**Airflow** is the default. DAGs in Python, huge ecosystem, mature.
The downside: DAGs become unmaintainable around 100+ tasks. The
senior framing: "Airflow is fine until your DAG is unmaintainable.
At that point you migrate to Dagster or Prefect for better
observability."

**Dagster** treats the pipeline as a typed asset graph. Strong
lineage, great for data quality, but newer ecosystem. Good for
medium-sized teams that want strong typing.

**Prefect** is the most Pythonic of the three. Good DX, good
observability, hybrid execution model. The senior framing:
"Prefect is the choice when your team is small and Python-first."

**The senior move** is to know one of the three deeply and to know
the *tradeoffs* of the other two. The interview rarely tests tool
specifics; it tests your judgment about which tool fits which scenario.

---

## 3. Ingestion: CDC, Fivetran, Airbyte

**CDC (Change Data Capture)** is the source-of-truth pattern. You
read the database's binlog (Postgres, MySQL) or transaction log
(Oracle, SQL Server) and emit INSERT/UPDATE/DELETE events. Debezium
is the open-source default; AWS DMS, Fivetran, and Airbyte are
managed alternatives.

**Why CDC wins**: it's complete, low-latency, and doesn't burden the
source database. The downside: the source must expose a binlog. Old
Oracle versions and some SaaS APIs don't.

**Fivetran / Airbyte** are managed ingestion services. They do CDC
where possible, polling otherwise. The trade-off: monthly cost vs
engineering time. A small team with 50 sources is better off with
Fivetran than building it themselves.

**The senior move**: "For the Postgres source I'd use Debezium for
the CDC stream. For the SaaS APIs I'd use Airbyte for the managed
connectors. The homegrown poller is only worth it if you have 1-2
sources and very specific latency requirements."

---

## 4. Storage: warehouses, lakes, lakehouses

**Warehouses** (Snowflake, BigQuery, Redshift) are columnar SQL
engines optimized for analytics. Schema-on-write. Strong consistency.
The downside: cost per TB is high, schema changes are painful.

**Lakes** (S3 + Parquet) are cheap, flexible, schema-on-read. The
downside: no ACID, no schema enforcement, no time travel. Without
discipline they become data swamps.

**Lakehouses** (Delta Lake, Iceberg, Hudi) are the bridge. They
add ACID transactions, schema enforcement, and time travel to a
parquet-on-S3 lake. The 2026 default for new architectures.

**The senior move** is to know which layer of the medallion
(bronze/silver/gold) lives in which tool. Bronze in Delta on S3.
Silver in Delta on S3. Gold in Snowflake or BigQuery. The
lakehouse feeds the warehouse; the warehouse is the serving layer.

---

## 5. Transformation: dbt, Spark, Flink

**dbt** is the SQL transformation layer. You write `SELECT`
statements, dbt builds them into a DAG, runs them in dependency
order, and tests them. The 2026 default for analytics engineering.

**Spark** is the distributed compute layer. You write Python / Scala
/ SQL, Spark parallelizes across a cluster. The right choice when
the data is too big for a single warehouse query (10+ TB).

**Flink** is the streaming equivalent. You write dataflow programs,
Flink runs them with exactly-once semantics on a cluster. The right
choice when the latency SLA is sub-minute.

**The senior move**: "I'd use dbt for the SQL transforms because
they're business-logic-heavy and analyst-friendly. I'd use Spark
only for the heavy joins and aggregations that don't fit in the
warehouse. Flink only if the SLA is sub-minute and the events
can't be batched."

---

## 6. Serving: warehouses, wide-column, search

The serving layer is what the consumer sees. Different consumers
want different things:

| Consumer | Best fit |
|---|---|
| BI / dashboards | Snowflake, BigQuery (columnar SQL) |
| ML features | Feast on a feature store, or a wide-column store (Bigtable, Cassandra) |
| Product feature (real-time) | Redis, Memcached (KV) or a search index (Elasticsearch, OpenSearch) |
| Reverse-ETL (CRM, marketing) | Hightouch, Census, or custom Python |

**The senior move** is to ask "who consumes this and at what
latency?" The answer drives the serving layer. A pipeline that
feeds both a dashboard *and* a real-time product feature needs
two serving layers.

---

## 7. The 2026 default stack

If you were starting a new pipeline at a mid-sized company today,
the default stack looks like:

```
Sources: Postgres, MySQL, SaaS APIs, S3 file drops
  ↓ CDC (Debezium) or polling (Airbyte)
Ingest: Kafka (or Kinesis / Pub/Sub) + S3 landing zone
  ↓ batch (Spark on EMR / Databricks) or stream (Flink)
Storage: Delta Lake on S3 (bronze/silver/gold)
  ↓ SQL transforms (dbt)
Serving: Snowflake / BigQuery for BI; Redis for product features
Orchestration: Airflow or Dagster
Observability: Monte Carlo, Great Expectations, Datadog
```

**The senior move** is to know that this stack exists *and* to
know when to deviate. Not every pipeline needs Kafka. Not every
pipeline needs Spark. The interview is testing your judgment, not
your ability to recite the stack.

---

## 8. The "I've never used that tool" answer

You will be asked about a tool you haven't used. The senior answer:

> "I haven't used Flink in production, but I have used Spark
> Streaming for similar workloads. The trade-off space is the same:
> exactly-once vs at-least-once, state management, watermarking for
> late events. I can reason about Flink from the docs and from the
> Spark experience."

The pattern: name what you *have* done, name the *common axis*
(here: streaming semantics), and project forward. That's a senior
move. The alternative ("I don't know Flink") is a 1/5 in tradeoff
articulation.

---

## Try it

Pick the most recent pipeline you've worked on. Map it onto the
5 categories (orchestration, ingestion, storage, transformation,
serving). What's missing? What's over-engineered? This exercise
is worth more than 3 lessons because it's your real codebase.
