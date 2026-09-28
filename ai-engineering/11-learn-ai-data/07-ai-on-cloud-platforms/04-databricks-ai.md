# Lesson 4 — Databricks AI

> **Type:** Article · Module 7 · AI on Cloud Platforms
> Mosaic AI, Unity Catalog, Vector Search on Delta, and the lakehouse-AI pattern.

---

## The Databricks AI stack for DEs

```
   DATABRICKS AI SURFACE AREA (DE-RELEVANT)
   ────────────────────────────────────────
   FOUNDATION MODELS    Mosaic AI Model Serving
                        Databricks Model Garden (DBRX, Llama, Mistral, Claude via API)

   EMBEDDINGS           Mosaic AI Embeddings (BGE, e5, OpenAI proxy)

   VECTOR SEARCH        Mosaic AI Vector Search
                        (Delta-native, HNSW or IVF)

   FEATURE STORE        Databricks Feature Store
                        (offline: Delta; online: online tables)

   MODEL SERVING        Mosaic AI Model Serving
                        Serverless or dedicated endpoints

   DOCUMENT AI          Databricks AI Functions for extraction
                        + custom PySpark / Python

   PIPELINES            Lakeflow (Spark + declarative ETL)
                        Delta Live Tables (DLT)
                        Workflows (DAG orchestrator)

   GOVERNANCE           Unity Catalog (lineage, ACL, feature/model registry)

   NOTEBOOKS            Databricks Notebooks (Python / SQL / Scala / R)
```

For data engineers, the unique value: **AI lives inside the same Delta Lake as the data**. No ETL out, no separate vector DB — embeddings sit next to the source rows in Delta tables, governed by Unity Catalog.

---

## Mosaic AI Model Serving

```python
import mlflow.deployments

client = mlflow.deployments.get_deploy_client("databricks")

response = client.predict(
    endpoint="databricks-llama-3-70b-instruct",
    inputs={
        "messages": [
            {"role": "user", "content": "Summarise this Delta table ..."}
        ],
        "max_tokens": 512,
    },
)
print(response["choices"][0]["message"]["content"])
```

| Strength | Weakness |
|---|---|
| Same Databricks workspace | DBU cost |
| Pay-per-token, serverless or dedicated | Smaller model catalogue than Bedrock |
| Unity Catalog lineage | Less compliance tooling than Azure |

---

## Mosaic AI Vector Search

A **Delta-native** vector DB. Embeddings live in a Delta table; the search engine indexes them.

```python
from databricks.vector_search.client import VectorSearchClient

# Create vector index from a Delta table
client = VectorSearchClient()
index = client.create_delta_sync_index(
    endpoint_name="vs_endpoint",
    index_name="main.default.docs_index",
    source_table="main.default.docs",
    embedding_source_column="text",
    embedding_model_endpoint="databricks-bge-large-en",
    primary_key="doc_id",
)

# Sync (incremental)
index.sync()

# Query
results = index.similarity_search(
    query="refund policy",
    columns=["doc_id", "source_url", "text"],
    num_results=10,
)
```

| Strength | Weakness |
|---|---|
| Embeddings live in Delta (no copy) | Less mature than Pinecone / Weaviate |
| Unity Catalog governs the index | Limited to Delta Lake |
| Auto-sync from source table | Newer, smaller community |

The killer feature: **your embeddings are governed by Unity Catalog**. ACL, lineage, audit — same as your data.

---

## Databricks Feature Store

```python
from databricks.feature_engineering import FeatureEngineeringClient

fe = FeatureEngineeringClient()

# Define feature table backed by Delta
fe.create_table(
    name="main.ml.user_clicks_30d",
    primary_keys=["user_id"],
    timestamp_keys=["event_ts"],
    schema="user_id STRING, event_ts TIMESTAMP, clicks INT",
    description="Daily click count per user, last 30 days",
)

# Online table for serving
fe.create_online_table(
    name="main.ml.user_clicks_30d_online",
    source_table="main.ml.user_clicks_30d",
    primary_keys=["user_id"],
    timestamp_keys=["event_ts"],
)
```

| Strength | Weakness |
|---|---|
| Same Delta lake as offline features | Online store is newer, less battle-tested |
| Unity Catalog governance | Databricks-only |
| Point-in-time joins native | Tighter coupling to Spark |

---

## AI Functions — SQL-near AI

```sql
-- ai_query: call any model endpoint from SQL
SELECT
  text,
  ai_query(
    "databricks-llama-3-70b-instruct",
    CONCAT("Extract the company name from: ", text)
  ) AS company_name
FROM events;

-- ai_summarize: short summary
SELECT ai_summarize(text) FROM events;

-- ai_classify: sentiment or category
SELECT ai_classify(text, ARRAY['positive', 'neutral', 'negative']) AS sentiment
FROM events;
```

This is the **Databricks version of `ML.GENERATE_TEXT`** — LLM calls from SQL.

---

## Unity Catalog for AI assets

Unity Catalog governs **all AI assets** the same way it governs data:

```
   Unity Catalog
   ├── Tables (data)
   ├── Models (registered ML models)
   ├── Features (feature store tables)
   ├── Functions (registered UDFs, including AI Functions)
   ├── Volumes (files, including raw PDFs)
   └── Lineage (column-level, table-level, model-level)
```

For DEs, this means:
- **PII tags** apply to embeddings too (so PII data doesn't accidentally end up in a public model)
- **Lineage** tracks source data → features → model → serving endpoint
- **ACL** applies to embeddings the same way it applies to source rows

---

## The "lakehouse AI" pattern

```
   ┌──────────────────────────────────────────────────────────┐
   │  Databricks Lakehouse AI                                 │
   │                                                          │
   │   raw data → Bronze (Delta)                              │
   │       │                                                  │
   │       ▼                                                  │
   │   cleaned → Silver (Delta)                              │
   │       │                                                  │
   │       ▼                                                  │
   │   features → Gold (Delta) + Feature Store                │
   │       │                                                  │
   │       ▼                                                  │
   │   embeddings → Gold (Delta) + Vector Search index        │
   │       │                                                  │
   │       ▼                                                  │
   │   model training (MLflow) → Model Registry                │
   │       │                                                  │
   │       ▼                                                  │
   │   Model Serving endpoint                                 │
   │                                                          │
   │   All in one Delta lake. All governed by Unity Catalog.  │
   └──────────────────────────────────────────────────────────┘
```

The data and the AI are in **one system**. No data movement. No separate vector DB. No separate feature store. One governance model.

---

## DLT + AI (streaming enrichment)

```python
import dlt
from pyspark.sql.functions import *

@dlt.table
def enriched_events():
    return (
        dlt.read_stream("events_raw")
        .withColumn("summary",
            expr("ai_summarize(text)"))
        .withColumn("sentiment",
            expr("ai_classify(text, array('positive','negative','neutral'))"))
    )
```

DLT (Delta Live Tables) for declarative ETL + AI enrichment. Same DAG, same quality expectations, AI is just another transform.

---

## When to pick Databricks AI

```
   ┌─────────────────────────────────────────────────────┐
   │  Databricks AI wins when:                            │
   │                                                     │
   │   - Your data lives in Delta Lake                    │
   │   - You want one governance model                   │
   │     (Unity Catalog covers data + AI)                │
   │   - You have heavy Spark workloads                  │
   │   - You want embeddings + features in the same lake │
   │                                                     │
   │  Databricks AI loses when:                          │
   │                                                     │
   │   - You don't have a Delta lake                     │
   │   - You want the absolute cheapest inference        │
   │   - You want the broadest model catalogue           │
   │     (Bedrock / Vertex are wider)                    │
   └─────────────────────────────────────────────────────┘
```

---

## Cost modelling

```
   Per million events (typical Databricks DE workload):
   ──────────────────────────────────────────────────
   Mosaic LLM (DBRX or Llama 3 70B, 1M tokens):    $2
   Embeddings (BGE-large, 1M tokens):              $0.10
   Vector Search endpoint:                         ~$300/mo
   Online feature tables:                          ~$200/mo
   Workflows / DLT compute:                        $0.15/DBU
   Unity Catalog:                                  free
   ──────────────────────────────────────────
   Total: ~$500/mo + compute costs
```

DBU cost is the wildcard; a steady workload is predictable, a spike can be 5–10× monthly.

---

## What Comes Next

> Lesson 5 — **Snowflake Cortex** — Cortex functions, Cortex Search, and the "AI inside the warehouse" pattern.