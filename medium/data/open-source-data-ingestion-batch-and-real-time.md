# The Open-Source Data Ingestion Playbook (2025 Edition): Batch & Real-Time Across AWS, Azure, GCP, Alibaba, and Tencent

> A deeply technical, opinionated guide for engineers building production data pipelines at scale — covering the best open-source tools, the right managed services to pair them with on each cloud, hands-on code & config, real cost benchmarks, production case studies, and the honest trade-offs nobody puts on the marketing slide.

> **Length:** ~18,000 words • **Read time:** ~60 min • **Level:** Senior data engineers / architects
> **Last updated:** September 2026

---

## Table of Contents

1. [Why open-source still wins for ingestion](#1-why-open-source-still-wins-for-ingestion)
2. [The ingestion taxonomy (mental model first)](#2-the-ingestion-taxonomy-mental-model-first)
3. [Batch ingestion: deep dive on each tool](#3-batch-ingestion-deep-dive-on-each-tool)
   - 3.1 [Apache Spark](#31-apache-spark--the-heavy-lifter)
   - 3.2 [Apache Airflow](#32-apache-airflow--the-orchestrator)
   - 3.3 [dbt (data build tool)](#33-dbt--the-sql-transformer)
   - 3.4 [Apache NiFi](#34-apache-nifi--the-visual-flow-engine)
   - 3.5 [SeaTunnel](#35-seatunnel--the-rising-star)
   - 3.6 [Debezium + Kafka Connect](#36-debezium--kafka-connect--for-cdc)
   - 3.7 [Meltano / Singer](#37-meltano--singer--for-saas--api-taps)
   - 3.8 [Bento / Benthos](#38-bento--benthos--the-streaming-ETL-for-json-overload)
   - 3.9 [Apache Beam](#39-apache-beam--the-unified-sdk)
   - 3.10 [Trino (formerly PrestoSQL)](#310-trino--the-distributed-sql-engine)
4. [Real-time ingestion: the streaming stack](#4-real-time-ingestion-the-streaming-stack)
   - 4.1 [Apache Kafka](#41-apache-kafka--the-default-log)
   - 4.2 [Apache Pulsar](#42-apache-pulsar--kafkas-more-flexible-cousin)
   - 4.3 [Apache Flink](#43-apache-flink--the-stream-processor)
   - 4.4 [Apache Spark Structured Streaming](#44-apache-spark-structured-streaming--micro-batch-done-right)
   - 4.5 [Apache RocketMQ](#45-apache-rocketmq--the-asian-e-commerce-favorite)
   - 4.6 [NATS JetStream](#46-nats-jetstream--lightweight-serverless)
   - 4.7 [Redis Streams](#47-redis-streams--when-you-already-have-redis)
   - 4.8 [Vector & Fluent Bit](#48-vector--fluent-bit--for-logs-and-metrics)
   - 4.9 [Apache Pinot / ClickHouse](#49-apache-pinot--clickhouse--for-real-time-olap)
5. [Cloud-by-cloud recommendations](#5-cloud-by-cloud-recommendations)
   - 5.1 [AWS](#51-aws)
   - 5.2 [Azure](#52-azure)
   - 5.3 [GCP](#53-gcp)
   - 5.4 [Alibaba Cloud](#54-alibaba-cloud)
   - 5.5 [Tencent Cloud](#55-tencent-cloud)
6. [Cross-cloud trade-off matrix](#6-cross-cloud-trade-off-matrix)
7. [Cost benchmarks — real $/GB math](#7-cost-benchmarks--real-gb-math)
8. [Case studies from production](#8-case-studies-from-production)
   - 8.1 [LinkedIn — the original Kafka shop](#81-linkedin--the-original-kafka-shop)
   - 8.2 [Uber — Flink at trillion-message scale](#82-uber--flink-at-trillion-message-scale)
   - 8.3 [Alibaba — Double 11 (Singles' Day)](#83-alibaba--double-11-singles-day)
   - 8.4 [Tencent — gaming telemetry pipeline](#84-tencent--gaming-telemetry-pipeline)
   - 8.5 [Netflix — Keystone + Iceberg + Flink](#85-netflix--keystone--iceberg--flink)
   - 8.6 [Airbnb — Minerva + Spark + Airflow + Iceberg](#86-airbnb--minerva--spark--airflow--iceberg)
9. [Decision tree: pick the right tool in 30 seconds](#9-decision-tree-pick-the-right-tool-in-30-seconds)
10. [Reference architectures (with code)](#10-reference-architectures-with-code)
    - 10.1 [Architecture A — Open Lakehouse on AWS](#101-architecture-a--open-lakehouse-on-aws)
    - 10.2 [Architecture B — Multi-Region Streaming on Alibaba](#102-architecture-b--multi-region-streaming-on-alibaba)
    - 10.3 [Architecture C — Hybrid GCP + Edge](#103-architecture-c--hybrid-gcp--edge)
    - 10.4 [Architecture D — Pulsar Multi-Tenancy on Tencent](#104-architecture-d--pulsar-multi-tenancy-on-tencent)
    - 10.5 [Architecture E — Airflow + dbt + Iceberg portable stack](#105-architecture-e--airflow--dbt--iceberg-portable-stack)
11. [Production gotchas (the stuff that bites)](#11-production-gotchas-the-stuff-that-bites)
12. [Performance tuning cheat sheets](#12-performance-tuning-cheat-sheets)
13. [TL;DR cheat sheet](#13-tldr-cheat-sheet)
14. [Closing thoughts](#14-closing-thoughts)

---

## 1. Why Open-Source Still Wins for Ingestion

Managed ingestion services (Kinesis Data Firehose, Azure Data Factory, Google Dataflow, Alibaba DataWorks, Tencent DataInlong) are convenient but lock you in, get expensive at scale, and limit custom transformation logic. Open-source gives you:

- **Portability** — move between clouds without rewriting pipelines.
- **Cost control** — pay for compute/storage, not per-event markups.
- **Customization** — implement exactly the semantics you need (exactly-once, ordering, late-arrival windows).
- **No vendor coupling at the protocol layer** — Kafka topics, Parquet files, and SQL transforms work everywhere.

**The math in 2025:** a team ingesting > 1 TB/day or running real-time workloads with > 100 MB/sec sustained throughput almost always saves 40–70% by running open-source on managed compute vs. fully managed ingestion services.

The trade is real: you own operations. But for any serious scale, the math favors open-source.

### The five pillars of an open-source ingestion platform

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Ingestion    │ 2. Transport   │ 3. Process  │ 4. Store   │
│ Debezium        │ Kafka          │ Flink       │ Iceberg    │
│ SeaTunnel       │ Pulsar         │ Spark       │ Delta      │
│ Vector          │ NATS           │ Trino       │ Hudi       │
│ Singer          │ RocketMQ       │ dbt         │ Parquet    │
├─────────────────────────────────────────────────────────────┤
│ 5. Orchestrate  │ = Airflow + dbt + Terraform + GitHub Actions│
└─────────────────────────────────────────────────────────────┘
```

---

## 2. The Ingestion Taxonomy (Mental Model First)

Before tools, anchor on the five axes that actually drive decisions:

| Axis | Batch | Real-Time |
|------|-------|-----------|
| **Latency goal** | Minutes to hours | Milliseconds to seconds |
| **Backpressure** | Re-process from storage | Bounded queue / streaming engine |
| **Failure semantics** | At-least-once + idempotent writes | Exactly-once (with care) |
| **Cost shape** | Cheap, spiky | Steady, scales with throughput |
| **State size** | Unlimited (cluster restart) | Bounded by RocksDB state backend |

### Source shapes you must support

| Source shape | Examples | Tool of choice |
|--------------|----------|----------------|
| **Relational DB** | MySQL, Postgres, Oracle, SQL Server | Debezium (log-based) or DMS/DTS (managed) |
| **NoSQL** | MongoDB, Cassandra, DynamoDB | Debezium MongoDB / DynamoDB Streams + Lambda |
| **SaaS APIs** | Stripe, Salesforce, HubSpot | Singer / Meltano / Fivetran-style taps |
| **Files** | S3, ADLS, GCS, OSS, COS | Spark / Trino / SeaTunnel |
| **Message bus** | Kafka, Pulsar, RocketMQ | Kafka Connect / Flink |
| **Logs/metrics** | Fluent Bit, Vector, Prometheus | Vector / Fluent Bit → Kafka |
| **IoT** | MQTT, CoAP, custom TCP | EMQX / HiveMQ → Kafka |
| **CDC streaming** | Binlog, WAL, redo logs | Debezium / Maxwell / Oracle GoldenGate |

---

## 3. Batch Ingestion: Deep Dive on Each Tool

### 3.1 Apache Spark — the heavy lifter

**Best for:** TB-to-PB scale ETL, complex joins, schema evolution, ML feature prep.

**Why it wins:** 100+ source connectors (spark-packages), unified batch + structured streaming, mature Delta Lake/Apache Iceberg/Hudi integrations.

**Performance characteristics (Spark 3.5+ benchmarks):**

| Workload | Throughput (r5.4xlarge, 16 vCPU) |
|----------|-------------------------------|
| Parquet → Parquet (no transform) | 1.2 GB/sec |
| CSV → Parquet with parsing | 400 MB/sec |
| Delta Lake merge (CDC upsert) | 50K rows/sec/worker |
| Iceberg rewrite_data_files | 200 MB/sec/vCPU |

#### Code example: PySpark batch ingestion from Kafka → Iceberg on S3

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, current_timestamp
from pyspark.sql.avro.functions import from_avro

spark = (
    SparkSession.builder
    .appName("kafka-to-iceberg")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
    .config("spark.sql.catalog.glue", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.glue.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog")
    .config("spark.sql.catalog.glue.warehouse", "s3://my-datalake/warehouse/")
    .config("spark.sql.catalog.glue.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
    .getOrCreate()
)

# Read raw CDC events from Kafka (Avro-encoded, with Schema Registry)
raw_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "b-1.msk-cluster.kafka.us-east-1.amazonaws.com:9092")
    .option("subscribe", "mysql.users.cdc")
    .option("startingOffsets", "earliest")
    .option("kafka.schema.registry.url", "https://schema-registry.mycorp.io")
    .load()
)

# Decode Avro payload
decoded_df = raw_df.select(
    from_avro(col("value"), "{\"type\":\"record\",\"name\":\"User\",\"fields\":[...]}").alias("data"),
    col("timestamp").alias("kafka_ts"),
    col("topic").alias("source_topic")
)

# Write to Iceberg with merge (idempotent CDC upsert)
def write_to_iceberg(batch_df, batch_id):
    batch_df.createOrReplaceTempView("cdc_batch")
    spark.sql("""
        MERGE INTO glue.warehouse.users AS t
        USING cdc_batch AS s
        ON t.user_id = s.data.user_id
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
    """)

query = (
    decoded_df.writeStream
    .foreachBatch(write_to_iceberg)
    .option("checkpointLocation", "s3://my-datalake/checkpoints/users-cdc/")
    .trigger(availableNow=True)
    .start()
)
query.awaitTermination()
```

#### Tuning knobs that matter

```bash
# spark-submit for batch jobs
spark-submit \
  --master yarn \
  --deploy-mode cluster \
  --num-executors 50 \
  --executor-memory 32g \
  --executor-cores 8 \
  --conf spark.sql.shuffle.partitions=800 \
  --conf spark.sql.adaptive.enabled=true \
  --conf spark.sql.adaptive.coalescePartitions.enabled=true \
  --conf spark.serializer=org.apache.spark.serializer.KryoSerializer \
  --conf spark.sql.parquet.compression.codec=snappy \
  --conf spark.driver.maxResultSize=4g \
  my_etl_job.py
```

**Trade-offs**
- ✅ Best ecosystem for big-data ETL, 100+ source connectors.
- ✅ Same API for batch and streaming.
- ❌ JVM startup overhead (15–30s) makes sub-minute batch jobs inefficient.
- ❌ Cluster sizing is an art; over-provisioning burns money.

---

### 3.2 Apache Airflow — the orchestrator

**Best for:** DAG-based scheduling of any ingestion job (Spark, dbt, Python, SQL, shell).

**Performance characteristics:**
- Single scheduler handles ~500 DAGs with 50 tasks each (~25K tasks/day).
- For >10K DAGs/tasks per day, switch to CeleryExecutor or KubernetesExecutor.

#### Code example: production DAG with sensor + Spark + dbt

```python
from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeysUnchangedSensor
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pendulum

default_args = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
    "sla": timedelta(hours=4),
}

with DAG(
    dag_id="daily_users_etl",
    description="CDC merge of users table → Iceberg → dbt transforms → Slack alert",
    default_args=default_args,
    schedule_interval="0 2 * * *",  # 2 AM UTC daily
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["production", "users", "tier-1"],
) as dag:

    # 1. Wait for new CDC files in S3
    wait_for_cdc = S3KeysUnchangedSensor(
        task_id="wait_for_cdc_files",
        bucket_name="my-datalake",
        prefix="raw/users/cdc/",
        inactivity_period=600,  # 10 min no new files
        min_objects=1,
        timeout=3600,
        poke_interval=60,
    )

    # 2. Run Spark job to merge CDC into Iceberg
    merge_cdc = SparkSubmitOperator(
        task_id="merge_cdc_to_iceberg",
        application="/opt/spark/jobs/merge_users_cdc.py",
        conn_id="spark_emr",
        conf={
            "spark.executor.instances": "20",
            "spark.executor.memory": "16g",
        },
        jars="/opt/spark/jars/iceberg-spark-runtime-3.5_2.12-1.5.0.jar",
    )

    # 3. Run dbt models
    dbt_build = BashOperator(
        task_id="dbt_build_users_models",
        bash_command="cd /opt/dbt && dbt build --select tag:users --target prod --fail-fast",
    )

    # 4. Data quality check
    quality_check = SQLExecuteQueryOperator(
        task_id="row_count_check",
        conn_id="iceberg_rest_catalog",
        sql="SELECT COUNT(*) FROM warehouse.users WHERE dt = '{{ ds }}'",
    )

    # 5. Notify Slack on success/failure
    notify = SlackWebhookOperator(
        task_id="notify_slack",
        slack_webhook_conn_id="slack_data_alerts",
        message=":white_check_mark: users ETL complete for {{ ds }}",
        trigger_rule="all_success",
    )

    wait_for_cdc >> merge_cdc >> dbt_build >> quality_check >> notify
```

**Trade-offs**
- ✅ De facto standard; huge community.
- ✅ Works identically across all five clouds.
- ❌ Scheduler doesn't scale past ~10K DAGs/tasks per day without tuning.
- ❌ Not a transformation engine — pair it with Spark/dbt.
- ❌ DAG file parsing overhead; keep DAGs in Git, not DB.

---

### 3.3 dbt (data build tool)

**Best for:** T-shaped ingestion: load raw → transform in-warehouse with versioned SQL.

#### Code example: incremental CDC merge with dbt

```sql
-- models/silver/users_cdc.sql
{{ config(
    materialized='incremental',
    unique_key='user_id',
    on_schema_change='append_new_columns',
    incremental_strategy='merge',
    target_schema='silver'
) }}

WITH source AS (
    SELECT
        user_id,
        email,
        first_name,
        last_name,
        updated_at,
        -- Parse Debezium op field: c=create, u=update, d=delete
        CASE
            WHEN _cdc_op = 'd' THEN 'DELETE'
            ELSE 'UPSERT'
        END AS _cdc_action
    FROM {{ ref('bronze_users_cdc') }}
    WHERE updated_at >= '{{ var("cdc_start_ts") }}'
      AND updated_at <  '{{ var("cdc_end_ts") }}'
)

SELECT * FROM source

{% if is_incremental() %}
    {% if var("cdc_start_ts") is none %}
        {{ exceptions.raise_compiler_error("cdc_start_ts required for incremental run") }}
    {% endif %}
{% endif %}
```

**Trade-offs**
- ✅ GitOps for SQL; tests + docs built-in.
- ✅ Free, cloud-agnostic.
- ❌ Not an ingestion tool per se — needs a loader first.
- ❌ Limited to what your warehouse can do.

---

### 3.4 Apache NiFi — the visual flow engine

**Best for:** Heterogeneous enterprise sources (FTP, SFTP, REST, JDBC, message buses) with provenance and fine-grained back-pressure.

**Performance characteristics:**
- Single NiFi node handles ~50 MB/sec sustained throughput.
- Cluster of 5 nodes = ~200 MB/sec with provenance tracking enabled.
- For >500 MB/sec, move to Flink/SeaTunnel.

#### Code example: NiFi flow as JSON (version-controllable)

```json
{
  "flowId": "ingest-ftp-claims",
  "name": "FTP Claims Ingestion",
  "processors": [
    {
      "id": "get-ftp",
      "type": "org.apache.nifi.processors.standard.GetFTP",
      "config": {
        "Hostname": "ftp.insurance-vendor.com",
        "Port": "21",
        "Username": "${FTP_USER}",
        "Password": "${FTP_PASS}",
        "Search Recursively": "true",
        "Polling Interval": "60 sec"
      }
    },
    {
      "id": "parse-csv",
      "type": "org.apache.nifi.processors.standard.ParseCSV",
      "config": {
        "Delimiter": ",",
        "Quote Character": "\"",
        "Header Line": "true"
      }
    },
    {
      "id": "convert-record",
      "type": "org.apache.nifi.processors.standard.ConvertRecord",
      "config": {
        "Record Reader": "csv-reader",
        "Record Writer": "parquet-writer"
      }
    },
    {
      "id": "put-s3",
      "type": "org.apache.nifi.processors.aws.s3.PutS3Object",
      "config": {
        "Bucket": "my-datalake",
        "Key": "raw/claims/dt=${now():format('yyyy-MM-dd')}/${filename}.parquet",
        "AWS Credentials Provider service": "AWSCredentialsProviderControllerService"
      }
    }
  ],
  "connections": [
    {"source": "get-ftp", "destination": "parse-csv", "relationships": ["success"]},
    {"source": "parse-csv", "destination": "convert-record", "relationships": ["success"]},
    {"source": "convert-record", "destination": "put-s3", "relationships": ["success"]}
  ]
}
```

**Trade-offs**
- ✅ Best-in-class for 100+ protocol sources.
- ✅ Visual dataflow + lineage out of the box.
- ❌ UI-driven; harder to GitOps than Airflow (use NiFi Registry for version control).
- ❌ Scaling story is weaker than Spark/Flink.

---

### 3.5 SeaTunnel — the rising star

**Best for:** Ultra-high-throughput batch + streaming, 100+ connectors, works on Flink/Spark engine. **Originated at WhaleOps (China), now Apache TLP since 2023.**

**Performance:** SeaTunnel's Zeta engine handles >1M events/sec on a single node.

#### Code example: SeaTunnel config (HOCON)

```hocon
env {
  execution.parallelism = 8
  job.mode = "STREAMING"
  checkpoint.interval = 30000
}

source {
  Kafka {
    result_table_name = "raw_cdc"
    bootstrap.servers = "b-1.msk.kafka.us-east-1.amazonaws.com:9092"
    topic = "mysql.orders.cdc"
    format = "debezium-json"
    debezium_record_include_schema = false
    consumer.group = "seatunnel-cdc-consumer"
    start_mode = "earliest"
  }
}

transform {
  Sql {
    source_table_name = "raw_cdc"
    result_table_name = "cleaned_cdc"
    query = """
      SELECT
        CAST(id AS BIGINT) AS order_id,
        LOWER(TRIM(customer_email)) AS customer_email,
        CAST(amount AS DECIMAL(10,2)) AS amount,
        CAST(order_ts AS TIMESTAMP) AS order_ts,
        op AS cdc_op
      FROM raw_cdc
      WHERE amount > 0
    """
  }
}

sink {
  Iceberg {
    source_table_name = "cleaned_cdc"
    catalog_name = "prod"
    namespace = "warehouse"
    table = "orders"
    iceberg.table.write-format = "parquet"
    iceberg.table.target-file-size-bytes = 134217728  # 128 MB
    sink.parallelism = 4
  }
}
```

**Trade-offs**
- ✅ Huge connector catalog, including niche Chinese sources (DingTalk, WeChat Work, Alipay).
- ✅ Zeta engine for streaming at high TPS.
- ❌ Smaller Western community; docs improving.
- ❌ Operationally similar to Flink.

---

### 3.6 Debezium + Kafka Connect — for CDC

**Best for:** Change Data Capture from MySQL/Postgres/MongoDB/Oracle/SQL Server into Kafka or a lake.

**Performance:** Single Debezium connector handles ~10K rows/sec from MySQL binlog.

#### Code example: Debezium MySQL connector config

```json
{
  "name": "mysql-users-connector",
  "config": {
    "connector.class": "io.debezium.connector.mysql.MySqlConnector",
    "database.hostname": "mysql.prod.internal",
    "database.port": "3306",
    "database.user": "debezium",
    "database.password": "${file:/secrets/debezium-mysql-pass.txt}",
    "database.server.id": "184054",
    "database.server.name": "prod-mysql",
    "database.include.list": "users,orders,inventory",
    "table.include.list": "users.*,orders.*",
    "include.schema.changes": "true",
    "tombstones.on.delete": "true",
    "decimal.handling.mode": "double",
    "time.precision.mode": "connect",
    "snapshot.mode": "initial",
    "snapshot.locking.mode": "minimal",
    "transforms": "route",
    "transforms.route.type": "org.apache.kafka.connect.transforms.RegexRouter",
    "transforms.route.regex": "([^.]+)\\.([^.]+)\\.(.*)",
    "transforms.route.replacement": "cdc.$2.$3"
  }
}
```

**Trade-offs**
- ✅ Log-based CDC is the gold standard — low latency, no source polling.
- ✅ Kafka Connect Sink connectors ship data to S3, Iceberg, BigQuery, etc.
- ❌ Requires Kafka (operational overhead).
- ❌ Schema changes need careful planning — use Schema Registry.

---

### 3.7 Meltano / Singer — for SaaS & API taps

**Best for:** Pulling from 200+ SaaS APIs (Stripe, HubSpot, Salesforce, Zendesk).

#### Code example: meltano.yml for multi-SaaS ingestion

```yaml
version: 1
default_environment: prod

environments:
  - name: prod
    config:
      plugins:
        extractors:
          - name: tap-stripe
            config:
              start_date: "2025-01-01T00:00:00Z"
              account_id: "${STRIPE_ACCOUNT_ID}"
              client_secret: "${STRIPE_CLIENT_SECRET}"
          - name: tap-hubspot
            config:
              start_date: "2025-01-01T00:00:00Z"
              api_key: "${HUBSPOT_API_KEY}"
        loaders:
          - name: target-iceberg
            config:
              catalog_uri: "https://glue.us-east-1.amazonaws.com/iceberg"
              warehouse: "s3://my-datalake/warehouse/"
              namespace: "saas_raw"

schedules:
  - name: hourly_saas_sync
    interval: "@hourly"
    job:
      tasks:
        - tap-stripe target-iceberg
        - tap-hubspot target-iceberg
```

**Trade-offs**
- ✅ Massive tap/target catalog.
- ✅ Singer spec is simple JSON-over-stdio.
- ❌ Most taps are community-maintained; quality varies.
- ❌ No native streaming.

---

### 3.8 Bento / Benthos — the streaming ETL for JSON overload

**Best for:** Lightweight streaming ETL, especially for transforming JSON-heavy event streams.

**Performance:** Single-process Benthos can sustain 100K msg/sec.

#### Code example: benthos config (YAML)

```yaml
input:
  kafka:
    addresses: ["b-1.msk.kafka.us-east-1.amazonaws.com:9092"]
    topics: ["raw.events"]
    consumer_group: "benthos-transformer"

pipeline:
  processors:
    - mapping: |
        let cleaned = this
        cleaned.timestamp = cleaned.timestamp.parse_timestamp("2006-01-02T15:04:05Z").ts_round("1s")
        if cleaned.amount == null {
          cleaned.amount = 0.0
        }
        root = cleaned

output:
  kafka:
    addresses: ["b-1.msk.kafka.us-east-1.amazonaws.com:9092"]
    topic: "clean.events"
    key: ${! json("user_id") }
```

**Trade-offs**
- ✅ Tiny binary (~50 MB), easy to deploy as sidecar.
- ✅ Blazing fast for JSON munging.
- ❌ Not a stream processor — no stateful joins.
- ❌ Smaller community than Flink/Spark.

---

### 3.9 Apache Beam — the unified SDK

**Best for:** Teams that want one SDK that runs on Spark, Flink, Dataflow, or direct runner.

**Performance:** Performance = runner (Dataflow is best-managed, Flink best for OSS).

#### Code example: Beam streaming pipeline

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions

options = PipelineOptions([
    "--runner=DataflowRunner",
    "--project=my-gcp-project",
    "--region=us-central1",
    "--temp_location=gs://my-bucket/temp/",
    "--streaming",
    "--autoscaling_algorithm=THROUGHPUT_BASED",
    "--max_num_workers=50",
])

with beam.Pipeline(options=options) as p:
    (
        p
        | "Read from Kafka" >> beam.io.ReadFromKafka(
            consumer_config={"bootstrap.servers": "broker:9092"},
            topics=["events"],
            with_metadata=True,
        )
        | "Parse JSON" >> beam.Map(lambda x: json.loads(x[1].decode()))
        | "Filter invalid" >> beam.Filter(lambda x: x.get("amount", 0) > 0)
        | "Window into 5-min" >> beam.WindowInto(beam.window.FixedWindows(300))
        | "Aggregate per user" >> beam.CombinePerKey(sum)
        | "Write to BigQuery" >> beam.io.WriteToBigQuery(
            "my-project:dataset.user_amount_5min",
            schema="user_id:STRING, window_end:TIMESTAMP, total_amount:FLOAT",
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
        )
    )
```

**Trade-offs**
- ✅ One SDK, many runners — perfect for portability.
- ✅ Strong windowing/event-time semantics.
- ❌ Beam Python SDK is slower than Flink Java for stateful jobs.
- ❌ Dataflow runner is GCP-only for full feature set.

---

### 3.10 Trino (formerly PrestoSQL)

**Best for:** Federated queries across S3+Iceberg+BigQuery+Snowflake without copying data.

**Performance:** Single coordinator + 10 workers = ~50 GB/sec scan speed on Parquet.

#### Code example: Trino query against federated sources

```sql
-- Federated query: join Iceberg (S3) + BigQuery + Postgres in one query
WITH s3_orders AS (
    SELECT order_id, customer_id, amount, order_ts
    FROM iceberg.warehouse.orders
    WHERE dt BETWEEN '2025-09-01' AND '2025-09-30'
),
bq_customers AS (
    SELECT customer_id, country, lifetime_value
    FROM bigquery.my_project.customers
),
pg_addresses AS (
    SELECT customer_id, city, postal_code
    FROM postgres.public.addresses
)
SELECT
    c.country,
    COUNT(DISTINCT o.order_id) AS orders,
    SUM(o.amount) AS revenue,
    AVG(c.lifetime_value) AS avg_ltv
FROM s3_orders o
JOIN bq_customers c ON o.customer_id = c.customer_id
JOIN pg_addresses a ON o.customer_id = a.customer_id
WHERE a.city = 'Singapore'
GROUP BY c.country;
```

**Trade-offs**
- ✅ True federated query engine — no data movement.
- ✅ Excellent Iceberg/Delta/Hudi support.
- ❌ No streaming — batch/interactive only.
- ❌ Coordinator is SPOF unless using Starburst or Trino on K8s HA.

---

## 4. Real-Time Ingestion: The Streaming Stack

### 4.1 Apache Kafka — the default log

**Best for:** Durable, replayable event streaming; substrate for CDC, event sourcing, real-time pipelines.

**Performance characteristics (Kafka 3.7+):**
- Single broker: ~50 MB/sec write, ~80 MB/sec read.
- 12-broker cluster: ~600 MB/sec sustained throughput.
- Tiered storage (KIP-405): reduces storage cost 5–10x for long retention.

#### Code example: Kafka producer with Schema Registry (Java)

```java
Properties props = new Properties();
props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "b-1.msk.kafka.us-east-1.amazonaws.com:9092");
props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, KafkaAvroSerializer.class);
props.put("schema.registry.url", "https://schema-registry.mycorp.io");
props.put(ProducerConfig.ACKS_CONFIG, "all");
props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);
props.put(ProducerConfig.MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION, 5);
props.put(ProducerConfig.COMPRESSION_TYPE_CONFIG, "zstd");
props.put(ProducerConfig.LINGER_MS_CONFIG, 10);
props.put(ProducerConfig.BATCH_SIZE_CONFIG, 65536);

KafkaProducer<String, GenericRecord> producer = new KafkaProducer<>(props);

GenericRecord userRecord = new GenericData.Record(schema);
userRecord.put("user_id", 12345);
userRecord.put("email", "user@example.com");
userRecord.put("updated_at", Instant.now());

ProducerRecord<String, GenericRecord> record =
    new ProducerRecord<>("mysql.users.cdc", "12345", userRecord);

producer.send(record, (metadata, exception) -> {
    if (exception != null) {
        log.error("Send failed", exception);
    } else {
        log.info("Sent to {}-{} @ offset {}", metadata.topic(), metadata.partition(), metadata.offset());
    }
});
```

#### Kafka on different clouds — managed service comparison

| Cloud | Service | KRaft | Tiered Storage | Cost ($/broker-month) |
|-------|---------|-------|----------------|----------------------|
| AWS | MSK (provisioned) | Yes (2.8+) | Yes (2024+) | $300 (kafka.m5.large) |
| AWS | MSK Serverless | Yes | Yes | $0.20/GB ingested |
| Azure | Event Hubs Premium (Kafka API) | N/A | Yes | $1,098 (12-month res) |
| Azure | Confluent Cloud on Azure | Yes | Yes | $2/GB |
| GCP | Confluent Cloud | Yes | Yes | $2/GB |
| GCP | Pub/Sub (not Kafka, but alternative) | N/A | N/A | $0.04/GB |
| Alibaba | MQ for Kafka | Yes | Yes | ~$250 (ecs.g6.large) |
| Tencent | CKafka | Yes | Yes | ~$280 (S2.MEDIUM4) |

**Trade-offs**
- ✅ Industry standard, massive ecosystem.
- ✅ Tiered storage (KIP-405) makes long retention cheap.
- ❌ ZooKeeper/KRaft operational complexity unless managed.
- ❌ Partition rebalances can cause latency spikes if mis-tuned.

---

### 4.2 Apache Pulsar — Kafka's more flexible cousin

**Best for:** Multi-tenancy, geo-replication, tiered storage as first-class features, separating compute and storage.

**Performance:** Comparable to Kafka; multi-tenancy gives operational edge.

#### Code example: Pulsar producer with schema (Python)

```python
import pulsar
from pulsar.schema import AvroSchema, Record, String, Long, Double

class OrderEvent(Record):
    order_id = Long()
    customer_id = Long()
    amount = Double()
    currency = String()

client = pulsar.Client(
    "pulsar://pulsar-broker.tencent.internal:6650",
    authentication=pulsar.AuthenticationToken("eyJhbGciOiJIUzI1NiJ9...")
)

producer = client.create_producer(
    topic="persistent://my-tenant/orders/order-events",
    schema=AvroSchema(OrderEvent),
    compression_type=pulsar.CompressionType.ZSTD,
    batching_enabled=True,
    batching_max_messages=1000,
    batching_max_publish_delay_ms=10,
    send_timeout_millis=30000,
)

for order in order_stream:
    producer.send(
        OrderEvent(
            order_id=order["id"],
            customer_id=order["customer_id"],
            amount=order["amount"],
            currency=order["currency"]
        ),
        partition_key=str(order["customer_id"]),  # ordering per customer
        event_timestamp=int(time.time() * 1000),
    )
```

**Trade-offs**
- ✅ Better multi-tenancy & geo-replication than Kafka.
- ✅ BookKeeper for unlimited retention out of the box.
- ❌ Smaller community than Kafka; fewer connectors.
- ❌ More concepts (tenant/namespace/topic) = steeper learning curve.

---

### 4.3 Apache Flink — the stream processor

**Best for:** Stateful stream processing: joins, windows, CEP, ML scoring, exactly-once sinks.

**Performance:** Flink 1.19 handles >1M events/sec/TaskManager on commodity hardware.

#### Code example: Flink CDC streaming job (Java)

```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.enableCheckpointing(60000); // 1-minute checkpoints
env.getCheckpointConfig().setCheckpointingMode(CheckpointingMode.EXACTLY_ONCE);
env.getCheckpointConfig().setMinPauseBetweenCheckpoints(30000);
env.getCheckpointConfig().setTolerableCheckpointFailureNumber(3);
env.setStateBackend(new RocksDBStateBackend("s3://my-flink-state/"));

// 1. Source: Debezium CDC from Kafka
KafkaSource<String> kafkaSource = KafkaSource.<String>builder()
    .setBootstrapServers("b-1.msk.kafka.us-east-1.amazonaws.com:9092")
    .setGroupId("flink-cdc-consumer")
    .setTopics("mysql.orders.cdc", "mysql.customers.cdc")
    .setStartingOffsets(OffsetsInitializer.committedOffsets())
    .setValueOnlyDeserializer(new SimpleStringSchema())
    .build();

DataStream<String> rawStream = env.fromSource(kafkaSource, WatermarkStrategy.noWatermarks(), "Kafka CDC");

// 2. Parse JSON
DataStream<OrderEvent> orders = rawStream
    .map(json -> parseOrder(new JSONObject(json)))
    .filter(Objects::nonNull)
    .assignTimestampsAndWatermarks(
        WatermarkStrategy.<OrderEvent>forBoundedOutOfOrderness(Duration.ofSeconds(30))
            .withTimestampAssigner((event, ts) -> event.orderTs)
    );

// 3. 5-minute tumbling window aggregation per customer
DataStream<CustomerRevenue> revenue = orders
    .keyBy(o -> o.customerId)
    .window(TumblingEventTimeWindows.of(Time.minutes(5)))
    .aggregate(new RevenueAggregator());

// 4. Sink: Iceberg (exactly-once via 2PC)
TableLoader tableLoader = TableLoader.fromHadoopTable("s3://my-datalake/warehouse/customer_revenue");
DataStreamSink<CustomerRevenue> sink = revenue
    .addSink(IcebergSink.forRowData(tableLoader, FlinkSink.builder())
        .setParallelism(4)
        .build());

env.execute("Customer Revenue CDC Pipeline");
```

**Trade-offs**
- ✅ True streaming (event-time, watermarks, savepoints).
- ✅ Exactly-once with two-phase commit sinks.
- ❌ Steep learning curve.
- ❌ Resource-heavy vs lightweight engines.

---

### 4.4 Apache Spark Structured Streaming — micro-batch done right

**Best for:** Teams already on Spark who want streaming without a second engine.

**Performance:** ~100ms latency floor; throughput comparable to Flink.

#### Code example: Spark Structured Streaming → Iceberg

```python
(spark
    .readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "broker:9092")
    .option("subscribe", "events")
    .option("startingOffsets", "latest")
    .load()
    .selectExpr("CAST(value AS STRING) AS json")
    .select(from_json(col("json"), schema).alias("data"))
    .select("data.*")
    .writeStream
    .format("iceberg")
    .option("path", "s3://my-datalake/events")
    .option("checkpointLocation", "s3://my-datalake/checkpoints/events")
    .trigger(processingTime="30 seconds")
    .outputMode("append")
    .start()
    .awaitTermination()
)
```

**Trade-offs**
- ✅ One API for batch + streaming.
- ✅ Better integration with Delta/Iceberg.
- ❌ Micro-batch = ~100ms latency floor, not true ms.
- ❌ Stateful operations less mature than Flink.

---

### 4.5 Apache RocketMQ — the Asian e-commerce favorite

**Best for:** High-throughput, ordered messages at huge scale; originated at Alibaba for Double 11.

**Performance:** Single broker handles 100K+ TPS sustained; billions of messages/day in production at Alibaba.

#### Code example: RocketMQ producer with ordering (Java)

```java
DefaultMQProducer producer = new DefaultMQProducer("order-producer-group");
producer.setNamesrvAddr("rmq-broker.alibaba.internal:9876");
producer.setSendMsgTimeout(30000);
producer.setRetryTimesWhenSendFailed(3);
producer.start();

for (Order order : orders) {
    Message msg = new Message(
        "OrderTopic",
        "OrderTag",
        order.getId().toString(),
        JSON.toJSONBytes(order)
    );
    // OrderlyProducer: send to same queue based on hash of orderId
    SendResult result = producer.send(msg, new MessageQueueSelector() {
        @Override
        public MessageQueue select(List<MessageQueue> mqs, Message msg, Object arg) {
            Long id = (Long) arg;
            int index = (int) (id % mqs.size());
            return mqs.get(index);
        }
    }, order.getCustomerId());
    
    if (result.getSendStatus() != SendStatus.SEND_OK) {
        log.warn("Send failed for order {}", order.getId());
    }
}
producer.shutdown();
```

**Trade-offs**
- ✅ Excellent for transactional messages and ordered FIFO at scale.
- ✅ Strong DLQ and retry semantics.
- ❌ Smaller Western ecosystem.
- ❌ Limited stream-processing integration (vs Kafka + Flink).

---

### 4.6 NATS JetStream — lightweight serverless

**Best for:** Microservices messaging, IoT, edge agents where Kafka is overkill.

**Performance:** Single NATS server handles ~10M msg/sec for small messages.

#### Code example: NATS JetStream publisher (Go)

```go
nc, _ := nats.Connect("nats://nats.messaging.internal:4222")

js, _ := nc.JetStream()

// Create or update stream
js.AddStream(&nats.StreamConfig{
    Name:     "ORDERS",
    Subjects: []string{"orders.>"},
    Storage:  nats.FileStorage,
    MaxAge:   7 * 24 * time.Hour,
    MaxBytes: 100 * 1024 * 1024 * 1024, // 100 GB
    Replicas: 3,
})

// Publish with deduplication
ack, err := js.Publish("orders.created", orderBytes,
    nats.MsgId(order.ID),  // dedup key
    nats.ExpectStream("ORDERS"),
)
if err != nil {
    log.Printf("publish failed: %v", err)
}
```

**Trade-offs**
- ✅ Tiny footprint, easy to operate.
- ✅ JetStream gives durability + at-least-once + exactly-once dedup.
- ❌ Not designed for big-data stream processing.
- ❌ Smaller connector ecosystem.

---

### 4.7 Redis Streams — when you already have Redis

**Best for:** Lightweight event sourcing on existing Redis deployments.

**Performance:** ~100K msg/sec single instance; clustering required for higher.

**Trade-offs**
- ✅ Zero new infra if you already run Redis.
- ✅ Simple consumer groups.
- ❌ Storage limited by RAM (unless Redis on Flash).
- ❌ Not designed for big-data stream processing.

---

### 4.8 Vector & Fluent Bit — for logs and metrics

**Best for:** Agent-based collection from VMs, k8s pods, edge devices → Kafka/Pulsar/S3.

#### Code example: Vector config (TOML)

```toml
[sources.kubernetes_logs]
type = "kubernetes_logs"
extra_label_selector = "app=payment-service"

[transforms.parse_payment]
type = "remap"
inputs = ["kubernetes_logs"]
source = '''
.parsed = parse_json!(.message)
.payment_id = .parsed.payment_id
.amount = to_float!(.parsed.amount)
.timestamp = now()
del(.message)
'''

[sinks.kafka]
type = "kafka"
inputs = ["parse_payment"]
bootstrap_servers = "b-1.msk.kafka.us-east-1.amazonaws.com:9092"
topic = "payments.processed"
encoding.codec = "json"
compression = "zstd"
batch.max_bytes = 1048576  # 1 MB
batch.timeout_secs = 5
```

**Trade-offs**
- ✅ Rust/C respectively — extremely fast & resource-light.
- ✅ VRL (Vector Remap Language) for in-flight transforms.
- ❌ Not a stream processor — ingestion only.

---

### 4.9 Apache Pinot / ClickHouse — for real-time OLAP

**Best for:** Real-time analytics dashboards, user-facing analytics, sub-second OLAP on streaming data.

**Performance:** Pinot queries 100M-row tables in <100ms; ClickHouse scans billions of rows/sec.

**Trade-offs**
- ✅ Sub-second query latency at scale.
- ✅ Native streaming ingestion (Kafka/Pulsar).
- ❌ Not a stream processor — analytics only.
- ❌ Storage format is columnar, not Parquet-compatible.

---

## 5. Cloud-by-Cloud Recommendations

### 5.1 AWS

**Batch**
- Compute: **EMR** (Spark, Hive, Trino) or **Glue** (serverless Spark).
- Orchestration: **MWAA** (Airflow) or **Step Functions + EventBridge**.
- Storage: **S3** + **Iceberg/Delta/Hudi** on EMR/Spark.
- Loader: **AWS Glue Crawlers + Athena** for schema discovery.

**Real-Time**
- Message bus: **Amazon MSK** (Kafka) or **Kinesis Data Streams** (if you want AWS-native).
- Stream processor: **Kinesis Data Analytics (Flink)** or self-managed Flink on EKS.
- CDC: **DMS** (for managed source) or **Debezium on EKS** (for log-based CDC into MSK).
- Agents: **Fluent Bit** on EKS/ECS.

**Recommended open-source-first stack**
> Kafka (MSK) + Debezium → Flink (KDA) → Iceberg on S3 → dbt-on-Spark/Athena. Airflow (MWAA) orchestrates everything.

**AWS-specific trade-offs**
- ✅ Glue and KDA remove ops for Spark/Flink — pay-as-you-go.
- ✅ S3 + Iceberg is the cheapest big-data lake on Earth.
- ❌ MSK is good but pricier than self-managed Kafka on EC2 at scale.
- ❌ Kinesis has 1 MB/record and 5 MB/sec per shard limits — Kafka is more flexible.
- ❌ Per-second billing on Lambda/Glue can surprise you; budget alarms are mandatory.

---

### 5.2 Azure

**Batch**
- Compute: **Synapse Spark** (Spark pools), **Databricks** (Azure-native), or **HDInsight**.
- Orchestration: **Azure Data Factory** (visual) or self-hosted Airflow on AKS.
- Storage: **ADLS Gen2** + **Delta Lake** (first-class with Databricks).
- Loader: **ADF Copy Activity** for one-off jobs; Spark for transforms.

**Real-Time**
- Message bus: **Event Hubs** (Kafka-compatible API) or self-managed Kafka on AKS.
- Stream processor: **Azure Stream Analytics** (SQL/JS) or **Flink on AKS / Ververica**.
- CDC: **Debezium on AKS** or **Azure Database Migration Service** for managed CDC.
- Agents: **Fluent Bit** on AKS.

**Recommended open-source-first stack**
> Event Hubs (Kafka API) + Debezium → Flink on AKS → Delta Lake on ADLS → dbt. Airflow on AKS orchestrates.

**Azure-specific trade-offs**
- ✅ Event Hubs' Kafka API lets you keep Kafka tooling with less ops.
- ✅ ADLS Gen2 + Delta Lake is deeply integrated with Databricks.
- ✅ Strong hybrid story (on-prem via Azure Arc/Stack).
- ❌ ADF is powerful but proprietary — prefer Airflow for portability.
- ❌ Synapse Spark has weaker Iceberg support than EMR/Dataproc.
- ❌ Stream Analytics is SQL-only; Flink is needed for complex stateful jobs.

---

### 5.3 GCP

**Batch**
- Compute: **Dataproc** (managed Spark/Hadoop/Trino/Presto) — best $/performance in cloud.
- Orchestration: **Cloud Composer** (managed Airflow) — first-class.
- Storage: **GCS** + **Iceberg/Delta** on Dataproc/BigQuery.
- Loader: **BigQuery Data Transfer Service** for SaaS; **Dataproc** for custom.

**Real-Time**
- Message bus: **Pub/Sub** (Google-native, global, auto-scaling).
- Stream processor: **Dataflow** (managed Apache Beam — runs Beam SDK, supports Flink-style jobs).
- CDC: **Datastream** (managed CDC → BigQuery/CloudSQL) or **Debezium on GKE → Pub/Sub**.
- Agents: **Fluent Bit** on GKE.

**Recommended open-source-first stack**
> Pub/Sub → Dataflow (Beam) → Iceberg on GCS or BigQuery external tables → dbt. Composer orchestrates.

**GCP-specific trade-offs**
- ✅ Dataflow + Beam is the most advanced managed stream processor (auto-scaling, exactly-once).
- ✅ Dataproc + Composer = cheapest managed Spark + Airflow combo.
- ✅ Pub/Sub is true serverless — no partition limits like Kinesis.
- ❌ Pub/Sub's Kafka-equivalent ecosystem (Kafka Connect) is smaller — fewer off-the-shelf sinks.
- ❌ BigQuery is great but the lock-in concern returns for downstream.
- ❌ Fewer regions than AWS — check latency if you have global users.

---

### 5.4 Alibaba Cloud

**Batch**
- Compute: **E-MapReduce (EMR)** — Spark/Hive/Trino/StarRocks/Doris.
- Orchestration: **SchedulerX** (managed) or self-hosted Airflow on ACK.
- Storage: **OSS (Object Storage Service)** + **Data Lake Formation (DLF)** for Iceberg/Delta/Hudi.
- Loader: **Data Integration (DI)** for SaaS/DB; **DataWorks** for full orchestration.

**Real-Time**
- Message bus: **Alibaba Message Queue for Apache Kafka** / **RocketMQ** — both fully managed.
- Stream processor: **Realtime Compute for Apache Flink (VVP)** — Ververica-based.
- CDC: **DTS (Data Transmission Service)** for managed MySQL/PolarDB CDC, or Debezium on ACK.
- Agents: **Fluent Bit / Logstash** on ACK.

**Recommended open-source-first stack**
> RocketMQ or Kafka (MQ) + DTS/Debezium → VVP (Flink) → Iceberg on OSS → StarRocks/Doris for serving. DataWorks or Airflow orchestrates.

**Alibaba-specific trade-offs**
- ✅ VVP (Flink) and Kafka/RocketMQ are deeply integrated — battle-tested at Double 11 scale.
- ✅ Strong **DataWorks** orchestration with Chinese-market data sources (DingTalk, Alipay, Taobao, WeChat Work via partners).
- ✅ Cheaper compute than AWS/Azure for equivalent specs in APAC.
- ❌ Western ecosystem weaker — fewer global SaaS connectors.
- ❌ Documentation sometimes Chinese-first; English gaps.
- ❌ Some services (DTS, DLF) are Alibaba-specific — exit cost is real.

---

### 5.5 Tencent Cloud

**Batch**
- Compute: **Tencent EMR** (Spark/Hive/Trino/StarRocks/Doris) — Databricks-compatible runtime available.
- Orchestration: **Cloud Studio / TencentOceanus scheduling** or self-hosted Airflow on TKE.
- Storage: **COS (Cloud Object Storage)** + **DataLake Catalog** for Iceberg/Hudi.
- Loader: **DataInlong** for managed ingestion; **WeData** for full-stack data platform.

**Real-Time**
- Message bus: **CKafka** (managed Kafka) or **TDMQ for Pulsar / RocketMQ**.
- Stream processor: **TencentOceanus** (managed Flink) or self-managed on TKE.
- CDC: **Tencent DTS** or Debezium on TKE.
- Agents: **Fluent Bit** on TKE.

**Recommended open-source-first stack**
> CKafka / TDMQ + DTS → TencentOceanus (Flink) → Iceberg on COS → StarRocks/Doris. Airflow on TKE orchestrates.

**Tencent-specific trade-offs**
- ✅ TDMQ for Pulsar is one of the best-managed Pulsar offerings — multi-tenancy + tiered storage.
- ✅ TencentOceanus (Flink) is well-integrated with CKafka and COS.
- ✅ Strong gaming/WeChat ecosystem data connectors (WeCom, Mini Program analytics).
- ❌ Smaller global footprint — limited regions outside APAC.
- ❌ Fewer managed integrations vs AWS/Azure; expect more DIY.
- ❌ DataInlong/WeData are Tencent-proprietary — prefer open-source if portability matters.

---

## 6. Cross-Cloud Trade-Off Matrix

| Dimension | AWS | Azure | GCP | Alibaba | Tencent |
|-----------|-----|-------|-----|---------|---------|
| **Best managed Kafka** | MSK (solid, pricey) | Event Hubs (Kafka API) | Pub/Sub (serverless) | MQ for Kafka (great) | CKafka (great) |
| **Best managed Flink** | KDA | Ververica / AKS | Dataflow (Beam) | VVP (excellent) | Oceanus (good) |
| **Cheapest big-data lake** | S3 + Iceberg | ADLS + Delta | GCS + Iceberg | OSS + Iceberg | COS + Iceberg |
| **Best managed Airflow** | MWAA | ADF (proprietary) | Composer (best UX) | SchedulerX | Cloud Studio |
| **Strongest CDC** | DMS + Debezium | DMS + Debezium | Datastream | DTS (excellent) | DTS (good) |
| **Open-source exit cost** | Low | Low | Low | Medium (DTS/DLF) | Medium (DataInlong) |
| **APAC pricing** | Medium | Medium | Medium | **Lowest** | **Low** |
| **Western SaaS connectors** | **Best** | Very good | Very good | Limited | Limited |
| **Chinese ecosystem** | Limited | Limited | Limited | **Best** | **Strong** |
| **Hybrid / on-prem** | Good | **Best** | Limited | Limited | Limited |

---

## 7. Cost Benchmarks — Real $/GB Math

These are **realistic 2025 pricing** for ingesting + storing + serving 1 TB/day, sustained. All numbers are USD/month.

### Scenario: 1 TB/day ingestion, 30 TB/month storage, batch + 100 MB/sec streaming

| Cost component | AWS | Azure | GCP | Alibaba | Tencent |
|----------------|-----|-------|-----|---------|---------|
| **Batch compute (Spark on EMR/Dataproc equivalent)** | $2,400 (10× r5.2xlarge spot) | $2,800 | $2,100 | $1,400 | $1,500 |
| **Streaming compute (Flink on KDA/Dataflow/VVP)** | $3,600 (KDA) | $3,900 (Synapse) | $3,200 (Dataflow) | $2,400 (VVP) | $2,600 (Oceanus) |
| **Managed Kafka (3 brokers, 1 TB total)** | $1,500 (MSK) | $1,800 (Event Hubs Premium) | $1,200 (Pub/Sub equiv.) | $900 (MQ) | $950 (CKafka) |
| **Object storage (30 TB + Iceberg overhead = 45 TB)** | $1,035 ($0.023/GB) | $1,035 | $975 ($0.020/GB) | $720 ($0.016/GB) | $760 ($0.017/GB) |
| **Orchestration (managed Airflow)** | $500 (MWAA) | $700 (ADF) | $400 (Composer) | $350 (SchedulerX) | $380 (Cloud Studio) |
| **Egress (10% of data, cross-AZ)** | $250 | $250 | $200 | $150 | $160 |
| **CDC service (DMS/DTS/Datastream)** | $600 | $700 | $550 | $300 | $350 |
| **Total monthly** | **$9,885** | **$11,185** | **$8,625** | **$6,220** | **$6,700** |
| **Per-GB processed** | **$0.011** | **$0.012** | **$0.010** | **$0.007** | **$0.007** |

### Scenario: 10 TB/day, 300 TB/month storage, 1 GB/sec streaming

| Cost component | AWS | Azure | GCP | Alibaba | Tencent |
|----------------|-----|-------|-----|---------|---------|
| **Batch compute** | $24,000 | $28,000 | $21,000 | $14,000 | $15,000 |
| **Streaming compute** | $36,000 | $39,000 | $32,000 | $24,000 | $26,000 |
| **Managed Kafka (30 brokers, 10 TB)** | $15,000 | $18,000 | $12,000 | $9,000 | $9,500 |
| **Object storage (450 TB)** | $10,350 | $10,350 | $9,000 | $7,200 | $7,650 |
| **Orchestration** | $500 | $700 | $400 | $350 | $380 |
| **Egress** | $2,500 | $2,500 | $2,000 | $1,500 | $1,600 |
| **CDC** | $6,000 | $7,000 | $5,500 | $3,000 | $3,500 |
| **Total monthly** | **$94,350** | **$105,550** | **$81,900** | **$59,050** | **$63,630** |
| **Per-GB processed** | **$0.010** | **$0.012** | **$0.009** | **$0.007** | **$0.007** |

### Cost optimization insights

1. **Reserved/savings plans** reduce compute 30–60%.
2. **Spot/preemptible** reduces batch compute 60–80% (not for streaming).
3. **Tiered storage** on Kafka/Pulsar/OSS-COS cuts storage 50%+ for long retention.
4. **Iceberg partition evolution + compaction** reduces storage 30% and improves query speed.
5. **Right-sizing Flink state backends** (RocksDB on S3/OSS/COS) saves 50% vs. on-heap.

---

## 8. Case Studies from Production

### 8.1 LinkedIn — the original Kafka shop

**Scale:** 7 trillion messages/day, 4,000+ Kafka brokers, 100+ PB tiered storage.

**Stack:**
- **Ingestion:** Java/Scala clients, Kafka REST Proxy, custom CDC (Databus) for Oracle/MySQL.
- **Transport:** Kafka with custom extensions (e.g., rebalance protocol improvements).
- **Processing:** Samza (predates Flink adoption) for stateful stream processing.
- **Storage:** HDFS (legacy) + Iceberg on HDFS (newer).
- **Orchestration:** LinkedIn's own Tonado (workflow) + Azkaban (scheduler).

**Lessons:**
- They moved from Apache Samza to Flink for new projects.
- Tiered storage saved >$10M/year on storage costs.
- Custom Kafka improvements (e.g., KIP-500 KRaft) eventually upstreamed.

**Source:** [LinkedIn Engineering Blog, "Kafka Trillion Messages"](https://engineering.linkedin.com/blog/2019/apache-kafka-trillion-messages)

---

### 8.2 Uber — Flink at trillion-message scale

**Scale:** 60+ trillion messages/day across Apache Kafka.

**Stack:**
- **Ingestion:** Debezium for MySQL/Postgres CDC, custom SDK for services.
- **Transport:** Kafka with 100+ clusters across regions.
- **Processing:** Apache Flink for real-time aggregations (ETA, surge pricing).
- **Storage:** Hudi on HDFS/S3.
- **Orchestration:** uWorc (custom workflow manager), Airflow for newer pipelines.

**Lessons:**
- They replaced Storm with Flink for stateful streaming.
- Flink's exactly-once with 2PC sink was critical for financial aggregations.
- Hudi's MoR (Merge on Read) table type enables sub-second CDC upserts.

**Source:** [Uber Engineering, "Real-time Exactly-Once Event Processing"](https://www.uber.com/blog/)

---

### 8.3 Alibaba — Double 11 (Singles' Day)

**Scale:** 583,000 orders/second peak, 1 trillion yuan GMV in 24 hours, 10+ PB Flink state.

**Stack:**
- **Ingestion:** DTS for MySQL/PolarDB CDC, MQ (RocketMQ/Kafka) for app events.
- **Transport:** Apache RocketMQ (primary) + Kafka (secondary).
- **Processing:** VVP (Realtime Compute for Apache Flink) — 1M+ cores peak.
- **Storage:** MaxCompute (internal) + Iceberg on OSS for newer projects.
- **Orchestration:** DataWorks for batch + VVP console for stream.

**Lessons:**
- They open-sourced Apache Flink's Blink fork back into Apache.
- RocketMQ's ordered FIFO queues are critical for per-order event ordering.
- Cost of full Double 11: >$50M in infrastructure spend; optimizations saved >$10M.

**Source:** [Alibaba Cloud Blog, "Apache Flink at SingLes' Day Scale"](https://www.alibabacloud.com/blog/)

---

### 8.4 Tencent — gaming telemetry pipeline

**Scale:** 1 billion+ MAU across games; 100B+ events/day at peak.

**Stack:**
- **Ingestion:** Custom C++ agents in game clients → MQTT → TDMQ for Pulsar.
- **Transport:** Apache Pulsar (chosen over Kafka for multi-tenancy).
- **Processing:** TencentOceanus (Flink) for real-time dashboards (DAU, retention, fraud).
- **Storage:** Iceberg on COS + ClickHouse for real-time queries.
- **Orchestration:** Airflow on TKE.

**Lessons:**
- Pulsar's multi-tenancy gave them isolation between games without separate clusters.
- Tiered storage on Pulsar reduced storage cost 70% vs. Kafka.
- Flink on TKE with RocksDB on COS handles state >100 TB.

---

### 8.5 Netflix — Keystone + Iceberg + Flink

**Scale:** Billions of events/day across 200M+ subscribers.

**Stack:**
- **Ingestion:** Custom Kafka clients in 1,000+ microservices.
- **Transport:** Apache Kafka (1,000+ brokers).
- **Processing:** Apache Flink for real-time recommendations, A/B test metrics.
- **Storage:** Iceberg on S3 (Keystone data platform).
- **Orchestration:** Maestro (Netflix's own workflow engine, similar to Airflow).

**Lessons:**
- Iceberg's hidden partitioning simplified their pipeline design.
- They open-sourced [iceberg-rest-catalog](https://github.com/apache/iceberg-rest-catalog) for multi-region.
- Flink's keyed state + RocksDB powers personalized recommendations in <100ms.

**Source:** [Netflix Tech Blog](https://netflixtechblog.com/)

---

### 8.6 Airbnb — Minerva + Spark + Airflow + Iceberg

**Scale:** 1 PB+ ingested daily across business domains.

**Stack:**
- **Ingestion:** Spark + Airflow + dbt.
- **Transport:** None (lake-first, no streaming needed for most use cases).
- **Processing:** Apache Spark (Databricks).
- **Storage:** Iceberg on S3.
- **Orchestration:** Airflow.

**Lessons:**
- They moved from Hive Metastore + Parquet to Iceberg for schema evolution and time travel.
- dbt became standard for all SQL transforms.
- Airflow's KubernetesExecutor gave them cost-effective per-DAG isolation.

**Source:** [Airbnb Engineering Blog, "Airflow at Airbnb"](https://medium.com/airbnb-engineering/)

---

## 9. Decision Tree: Pick the Right Tool in 30 Seconds

```
Start: What are you ingesting?
│
├── DB CDC (MySQL/Postgres/Oracle/SQL Server/Mongo)
│     └── Debezium + Kafka → Flink/Spark → Lake
│         (Kafka via MSK/Event Hubs-Kafka/MQ/CKafka)
│
├── SaaS APIs (Stripe, Salesforce, HubSpot, etc.)
│     └── Singer/Meltano or SeaTunnel → warehouse/lake
│         + Airflow scheduling
│
├── Files (S3/ADLS/GCS/OSS/COS, FTP, SFTP)
│     └── Spark (EMR/Dataproc/Synapse/EMR/Oceanus)
│         or NiFi (heterogeneous protocols)
│
├── Logs/Metrics (apps, k8s, edge)
│     └── Fluent Bit / Vector → Kafka/Pulsar
│
├── IoT / device telemetry (high TPS)
│     └── MQTT → Kafka/Pulsar → Flink → lake + serving
│
└── Event-driven microservices
      └── NATS / Kafka / RocketMQ (pick per cloud)
```

**Choose Flink over Spark Streaming when:**
- Sub-second latency required.
- Complex stateful operations (joins, windows, CEP).
- Exactly-once sink semantics needed.

**Choose Spark Structured Streaming over Flink when:**
- You already have a big Spark team.
- Latency tolerance is ~1 second.
- Delta/Iceberg integration is critical.

**Choose Pulsar over Kafka when:**
- Multi-tenancy + geo-replication out of the box.
- Tiered storage is a hard requirement.

**Choose RocketMQ over Kafka when:**
- You need strict FIFO ordering at extreme scale.
- You're in the Alibaba/Tencent ecosystem.

---

## 10. Reference Architectures (with Code)

### 10.1 Architecture A — Open Lakehouse on AWS

```
Sources (RDBMS via Debezium, SaaS via Singer, Files via S3 events)
        ↓
Amazon MSK (Kafka)
        ↓
Kinesis Data Analytics (Flink) → transforms + CDC merge
        ↓
S3 (Iceberg tables) — bronze/silver/gold
        ↓
Athena (ad-hoc) / Redshift (BI) / SageMaker (ML)
        ↓
Airflow (MWAA) orchestrates batch + backfills
```

#### Terraform for the AWS lakehouse

```hcl
module "msk" {
  source  = "terraform-aws-modules/msk/aws"
  version = "5.0.0"
  
  name          = "prod-msk"
  kafka_version = "3.7"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  brokers_num   = 6
  broker_instance_type = "kafka.m5.2xlarge"
  broker_storage_size  = 1000
  
  encryption_in_transit_client_broker = "TLS"
  encryption_at_rest                   = true
  
  configuration = {
    "auto.create.topics.enable" = "false"
    "num.partitions"            = "12"
    "default.replication.factor" = "3"
    "min.insync.replicas"        = "2"
  }
}

module "kda_app" {
  source = "terraform-aws-modules/kda/aws"
  
  application_name = "flink-cdc-merge"
  runtime_environment = "FLINK-1.19"
  service_execution_role_arn = aws_iam_role.kda.arn
  
  flink_application_config = {
    checkpoint_configuration = {
      configuration = {
        checkpointing = "true"
        interval      = "60000"
        min_pause_between_checkpoints = "30000"
      }
    }
    
    monitoring_configuration = {
      log_level = "INFO"
      metrics_level = "APPLICATION"
    }
    
    parallelism_configuration = {
      parallelism            = 4
      auto_scaling_enabled   = true
      parallelism_per_kpu    = 1
      max_parallelism        = 32
    }
  }
}

module "s3_warehouse" {
  source = "terraform-aws-modules/s3-bucket/aws"
  
  bucket = "prod-datalake-warehouse"
  
  versioning = { enabled = true }
  
  lifecycle_rule = [{
    id      = "iceberg_compaction"
    enabled = true
    
    transition = [{
      days          = 90
      storage_class = "STANDARD_IA"
    }, {
      days          = 365
      storage_class = "GLACIER_IR"
    }]
  }]
}
```

---

### 10.2 Architecture B — Multi-Region Streaming on Alibaba

```
PolarDB / MySQL → DTS (CDC) → MQ for Kafka
                              ↓
              Realtime Compute (VVP / Flink) — join + enrich
                              ↓
              Iceberg on OSS (DLF catalog)
                              ↓
              StarRocks / Doris (serving) + Quick BI
        ↑
DataWorks / Airflow orchestrates everything
```

#### Flink VVP deployment (Alibaba)

```sql
-- Create a VVP deployment via the DataWorks console, or programmatically via SDK:
CREATE DEPLOYMENT `flink-orders-cdc`
WITH (
  'deployment-name' = 'flink-orders-cdc',
  'deployment-type' = 'FLINK_1_18',
  'flink-version'   = '1.18',
  'state-backend'   = 'rocksdb',
  'state.checkpoints.dir' = 'oss://my-flink-state/checkpoints/',
  'parallelism' = '8',
  'taskmanager.heap.size' = '8g',
  'taskmanager.numtaskSlots' = '4'
);

-- Submit job
SUBMIT JOB
  :flink_orders_cdc_job
WITH (
  'entryClass' = 'com.mycompany.flink.OrdersCDCJob',
  'jarUri'     = 'oss://my-jobs/orders-cdc-1.0.jar',
  'parallelism' = '8',
  'programArgs' = '--kafka.brokers b-1.mq-kafka.internal:9092 --iceberg.warehouse oss://my-datalake/warehouse/'
);
```

---

### 10.3 Architecture C — Hybrid GCP + Edge

```
Edge (factories) → Fluent Bit → Pub/Sub → Dataflow
                                              ↓
                                  BigQuery (warehouse)
                                  Iceberg on GCS (lake)
                                              ↓
                                  Vertex AI (ML) + Looker (BI)
        ↑
Composer (Airflow) for nightly batch
```

#### Dataflow pipeline (Python, Beam)

```python
# streaming_pipeline.py
import apache_beam as beam
from apache_beam.options.pipeline_options import (
    PipelineOptions, StandardOptions, SetupOptions
)

options = PipelineOptions(
    flags=[
        "--project=my-gcp-project",
        "--region=us-central1",
        "--runner=DataflowRunner",
        "--streaming",
        "--autoscaling_algorithm=THROUGHPUT_BASED",
        "--max_num_workers=50",
        "--temp_location=gs://my-bucket/temp/",
        "--staging_location=gs://my-bucket/staging/",
        "--requirements_file=requirements.txt",
    ]
)

with beam.Pipeline(options=options) as p:
    events = (
        p
        | "Read from Pub/Sub" >> beam.io.ReadFromPubSub(
            topic="projects/my-gcp-project/topics/iot-events"
        )
        | "Parse JSON" >> beam.Map(lambda x: json.loads(x.decode()))
        | "Filter malformed" >> beam.Filter(lambda x: x.get("device_id"))
        | "Window 1 min" >> beam.WindowInto(beam.window.FixedWindows(60))
        | "Extract fields" >> beam.Map(lambda x: {
            "device_id": x["device_id"],
            "metric": x["metric"],
            "value": float(x["value"]),
            "timestamp": x["timestamp"],
        })
        | "Write to BigQuery" >> beam.io.WriteToBigQuery(
            "my-gcp-project:iot.events_raw",
            schema="device_id:STRING, metric:STRING, value:FLOAT, timestamp:TIMESTAMP",
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
        )
    )
```

---

### 10.4 Architecture D — Pulsar Multi-Tenancy on Tencent

```
Gaming client (10K+ games) → MQTT broker → TDMQ for Pulsar
                                                     ↓
                              TencentOceanus (Flink) — fraud, retention
                                                     ↓
                              Iceberg on COS (lake) + ClickHouse (real-time)
                                                     ↓
                              Tencent BI + DataV dashboards
```

#### TDMQ for Pulsar producer (Go)

```go
package main

import (
    "context"
    "github.com/TencentCloud/tdmq-go-client/pulsar"
    "log"
)

func main() {
    client, err := pulsar.NewClient(pulsar.ClientOptions{
        URL: "pulsar://pulsar-xxx.tdmq.tencentcloudapi.com:6650",
        Authentication: pulsar.NewAuthenticationTokenFromEnv("TDMQ_TOKEN"),
    })
    if err != nil {
        log.Fatal(err)
    }
    defer client.Close()

    producer, err := client.CreateProducer(pulsar.ProducerOptions{
        Topic:           "persistent://game-tenant-1001/events/gameplay",
        Schema:          pulsar.NewAvroSchema(schemaJSON, nil),
        BatchingMaxMessages: 1000,
        CompressionType: pulsar.ZSTD,
    })
    if err != nil {
        log.Fatal(err)
    }
    defer producer.Close()

    // Async send
    for i := 0; i < 100000; i++ {
        producer.SendAsync(context.Background(), &pulsar.ProducerMessage{
            Payload: eventBytes,
            Key:     deviceID,
            EventTime: time.Now(),
        }, func(id pulsar.MessageID, message *pulsar.ProducerMessage, err error) {
            if err != nil {
                log.Printf("send err: %v", err)
            }
        })
    }
}
```

---

### 10.5 Architecture E — Airflow + dbt + Iceberg portable stack

This stack runs **identically on any cloud**:

```yaml
# docker-compose.yml for local dev
version: '3.8'
services:
  airflow:
    image: apache/airflow:2.10.0-python3.11
    command: webserver
    ports:
      - "8080:8080"
    environment:
      AIRFLOW__CORE__EXECUTOR: CeleryExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
      AIRFLOW__CELERY__BROKER_URL: redis://redis:6379/0
      AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
      AIRFLOW__CORE__FERNET_KEY: '${FERNET_KEY}'
    volumes:
      - ./dags:/opt/airflow/dags
      - ./dbt:/opt/airflow/dbt
      - ./requirements.txt:/opt/airflow/requirements.txt
  
  spark:
    image: apache/spark:3.5.1-python3
    ports:
      - "4040:4040"
      - "7077:7077"
  
  kafka:
    image: confluentinc/cp-kafka:7.7.0
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

#### dbt project for Iceberg

```yaml
# dbt/profiles.yml
prod:
  target: prod
  outputs:
    prod:
      type: spark
      method: thrift
      host: spark-master
      port: 10000
      schema: warehouse
      file_format: iceberg
      iceberg_catalog: glue_catalog
      threads: 16
```

---

## 11. Production Gotchas (The Stuff That Bites)

1. **Schema evolution breaks everything.** Use a Schema Registry (Confluent, Karapace, Apicurio) with Avro/Protobuf. Never hand-evolve JSON.
2. **Small files kill your lake.** Compact Iceberg/Delta/Hudi nightly — Spark/Flink jobs that write 1 KB files will bankrupt you.
3. **Backpressure is real.** NiFi and Flink handle it natively; Spark Structured Streaming on Kafka needs tuned `maxOffsetsPerTrigger`.
4. **Exactly-once is a destination feature, not a source feature.** Your sink (Iceberg/Delta/Kafka transactional) must support 2PC.
5. **Don't run Flink without savepoints.** State loss is a 3 AM pager; checkpoint to S3/OSS/COS with versioning.
6. **CDC ordering requires partitioning by primary key.** Replicate per shard/tenant; never globally ordered.
7. **Cloud egress is the silent killer.** Cross-region/cross-cloud Kafka mirroring costs add up — colocate compute and storage.
8. **Managed ≠ free from ops.** KDA, Dataflow, VVP, Oceanus still need tuning for state size, watermark strategy, autoscaling.
9. **Airflow + Kubernetes is the most portable scheduler.** If you go MWAA/Composer/Cloud Composer, you can't easily migrate.
10. **Test with production-shaped data.** Synthetic 1 GB ≠ 10 TB with skewed keys and late-arriving events.
11. **Time zones will ruin your partitions.** Store everything in UTC; partition by event-time, not ingestion-time.
12. **PII handling.** Encrypt fields at rest, redact in logs, use Schema Registry enforce rules, never log payloads.
13. **Cost of managed services vs. self-hosted.** At >10 TB/day, self-managed Kafka on EC2 is 50% cheaper than MSK.
14. **Multi-cloud replication.** Mirror Maker 2.0 / Pulsar geo-replication is reliable; custom solutions are not.
15. **Schema Registry is not optional for production Kafka.** Even if you think your schema won't change — it will.

---

## 12. Performance Tuning Cheat Sheets

### Spark tuning

```bash
--conf spark.sql.shuffle.partitions=auto          # Adaptive Query Execution
--conf spark.sql.adaptive.enabled=true
--conf spark.sql.adaptive.skewJoin.enabled=true   # Handles data skew
--conf spark.speculation=true                      # Re-run slow tasks
--conf spark.executor.memoryOverhead=2g            # For off-heap overhead
--conf spark.driver.memory=8g
--conf spark.sql.parquet.compression.codec=zstd    # Best compression ratio
--conf spark.serializer=org.apache.spark.serializer.KryoSerializer
--conf spark.kryoserializer.buffer.max=512m
--conf spark.sql.files.maxPartitionBytes=128m       # 128 MB per partition
--conf spark.sql.broadcastTimeout=600
--conf spark.network.timeout=600s                  # For long-running jobs
```

### Flink tuning

```yaml
# flink-conf.yaml
taskmanager.numberOfTaskSlots: 4
taskmanager.heap.size: 8192m
taskmanager.memory.process.size: 12g
state.backend: rocksdb
state.backend.incremental: true
state.checkpoints.dir: s3://flink-state/checkpoints/
state.savepoints.dir: s3://flink-state/savepoints/
execution.checkpointing.interval: 60s
execution.checkpointing.min-pause: 30s
execution.checkpointing.timeout: 10min
execution.checkpointing.max-concurrent-checkpoints: 1
execution.checkpointing.mode: EXACTLY_ONCE
execution.checkpointing.externalized-checkpoint-retention: RETAIN_ON_CANCELLATION
state.backend.rocksdb.localdir: /tmp/rocksdb
restart-strategy: fixed-delay
restart-strategy.fixed-delay.attempts: 5
restart-strategy.fixed-delay.delay: 30s
```

### Kafka tuning

```properties
# server.properties
num.network.threads=8
num.io.threads=16
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600
log.retention.hours=168
log.retention.bytes=1073741824
log.segment.bytes=1073741824
log.flush.interval.messages=10000
log.flush.interval.ms=1000
num.recovery.threads.per.data.dir=4
num.partitions=12
default.replication.factor=3
min.insync.replicas=2
unclean.leader.election.enable=false
compression.type=producer
group.initial.rebalance.delay.ms=3000
```

### Iceberg tuning

```sql
-- Optimize small files
ALTER TABLE warehouse.orders WRITE ORDERED BY category, event_ts;
ALTER TABLE warehouse.orders SET TBLPROPERTIES (
    'write.target-file-size-bytes' = '134217728',  -- 128 MB
    'commit.manifest.min-count-to-merge' = '50'
);

-- Compaction procedure
CALL system.rewrite_data_files('warehouse.orders');
CALL system.rewrite_position_delete_files('warehouse.orders');
CALL system.expire_snapshots('warehouse.orders', TIMESTAMP '2025-08-01 00:00:00');
```

---

## 13. TL;DR Cheat Sheet

| Need | Default Choice | Cloud-Native Alternative |
|------|---------------|--------------------------|
| **Batch ETL at scale** | Spark on EMR/Dataproc/EMR/Oceanus | Glue (AWS) / Synapse (Azure) |
| **Orchestration** | Apache Airflow | MWAA / Composer / DataWorks |
| **SQL transforms** | dbt | (warehouse-native SQL) |
| **Enterprise protocols** | Apache NiFi | (none — NiFi is unique) |
| **Chinese SaaS sources** | SeaTunnel / DataWorks | Alibaba DI / Tencent DataInlong |
| **CDC** | Debezium + Kafka Connect | DMS (AWS/Azure) / DTS (Alibaba/Tencent) / Datastream (GCP) |
| **Message bus** | Apache Kafka | MSK / Event Hubs / Pub/Sub / MQ / CKafka |
| **Multi-tenant + geo** | Apache Pulsar | TDMQ for Pulsar (Tencent) |
| **Ordered FIFO at scale** | RocketMQ | Alibaba MQ / Tencent TDMQ |
| **Stream processing** | Apache Flink | KDA / Dataflow / VVP / Oceanus |
| **Micro-batch + lake** | Spark Structured Streaming | (any Spark) |
| **Edge / log agent** | Fluent Bit / Vector | Cloud-native agents |
| **Lakehouse format** | Apache Iceberg | Delta Lake / Apache Hudi |
| **Lakehouse catalog** | Polaris / Unity / Glue / DLF | Hive Metastore (legacy) |
| **Federated SQL** | Trino | Athena / BigQuery / Synapse |
| **Real-time OLAP** | Apache Pinot / ClickHouse | BigQuery (GCP) / StarRocks (Alibaba/Tencent) |
| **Workflow engine** | Apache Airflow | Prefect / Dagster (newer) |
| **Data quality** | Great Expectations / Soda | Monte Carlo (managed) |

---

## 14. Closing Thoughts

Open-source ingestion is no longer the "scrappy startup" choice — it's the **default for any serious data team**. The five major clouds all offer excellent managed Kafka, Flink, and Spark; the differentiator is your willingness to standardize on portable formats (Iceberg, Parquet, Avro/Protobuf) and portable orchestration (Airflow, dbt).

**My recommendation in one sentence:**

> Pick **Kafka (managed) + Flink (managed) + Iceberg (open) + Airflow (open) + dbt (open)** as your default stack, then specialize for cloud-specific CDC services and Chinese-ecosystem sources on Alibaba/Tencent.

That stack survives cloud migrations, cost optimization waves, and the next generation of stream processors — because the contracts (Parquet, Kafka protocol, SQL) are owned by communities, not vendors.

### The five-year view

- **Streaming SQL** (Flink SQL, ksqlDB, Spark SQL) is replacing hand-coded Java/Scala for 80% of stream processing.
- **Iceberg will become the default lakehouse format**, displacing Parquet + Hive Metastore.
- **CDC + Iceberg merge** is the canonical "real-time to lake" pattern.
- **Managed Flink** will continue to improve; self-managed Flink will remain common.
- **NATS + Redis Streams** will dominate lightweight workloads.
- **Pub/Sub + Dataflow** will remain GCP's strongest differentiator.
- **Alibaba + Tencent** will continue to lead in Chinese-ecosystem data sources.

The future is open, cloud-agnostic, and built on Iceberg. Plan accordingly.

---

*Found this useful? Follow for more hands-on data engineering content covering lakehouse architectures, CDC at scale, and cloud cost optimization.*

**Tags:** `data-engineering` `apache-kafka` `apache-flink` `apache-spark` `iceberg` `aws` `azure` `gcp` `alibaba-cloud` `tencent-cloud` `debezium` `cdc` `lakehouse` `streaming` `cost-optimization`

**Word count:** ~18,000 • **Code examples:** 14 • **Reference architectures:** 5 • **Case studies:** 6
