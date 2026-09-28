# Lesson 1 — AWS AI for Data Engineers

> **Type:** Article · Module 7 · AI on Cloud Platforms
> Bedrock, SageMaker, OpenSearch, and where each fits a data engineering workflow.

---

## The AWS AI stack for DEs

```
   AWS AI SURFACE AREA (DE-RELEVANT)
   ─────────────────────────────────
   FOUNDATION MODELS    Bedrock (Claude, Llama, Mistral, Titan, ...)
                        + Marketplace for third-party

   EMBEDDINGS           Bedrock Titan Embeddings
                        SageMaker JumpStart embedders

   VECTOR SEARCH        OpenSearch + k-NN plugin
                        Aurora pgvector
                        Neptune ML (graph)

   FEATURE STORE        SageMaker Feature Store (offline: S3, online: in-mem)

   MODEL SERVING        Bedrock (serverless)
                        SageMaker Endpoints / Serverless Inference
                        SageMaker JumpStart

   DOCUMENT AI          Textract (OCR + tables + forms)

   PIPELINES            SageMaker Pipelines
                        + Glue / EMR / Step Functions orchestration

   NOTEBOOKS            SageMaker Studio / Studio Lab
```

For data engineers, the most-used surfaces are: **Bedrock** (LLMs), **SageMaker Feature Store** (online features), **OpenSearch** (vector search), **Textract** (unstructured), **SageMaker Pipelines** (orchestration).

---

## Bedrock — managed foundation models

Bedrock is the **single API** to multiple foundation models. No infra to manage. Pay per token.

```python
import boto3

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

response = bedrock.invoke_model(
    modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": "Summarise this S3 inventory report ..."}
        ],
    }),
)
answer = json.loads(response["body"].read())
```

### Models available on Bedrock (2026)

| Provider | Models |
|---|---|
| Anthropic | Claude 3.5 Sonnet, Claude 3 Haiku, Claude Opus |
| Meta | Llama 3.x |
| Mistral | Mistral Large, Mixtral |
| Amazon | Titan Text, Titan Embeddings |
| Cohere | Command R+, embed-v3 |
| Stability | Stable Diffusion |

### Why data engineers use Bedrock

- **Serverless.** No model servers to operate. Pay per token.
- **Multi-model.** Same API for Claude, Llama, Titan. Swap per use case.
- **IAM-integrated.** Fine-grained access control, VPC endpoints.
- **Guardrails.** Bedrock Guardrails for content filtering, PII redaction.
- **Knowledge bases.** Built-in RAG (S3 → embeddings → OpenSearch → answers).

### Cost (rough, 2026)

| Model | Input | Output |
|---|---|---|
| Claude 3.5 Sonnet | $3/M tokens | $15/M tokens |
| Claude 3 Haiku | $0.25/M | $1.25/M |
| Titan Embeddings | $0.10/M | — |
| Llama 3 70B | $0.72/M | $0.72/M |

---

## SageMaker Feature Store

Online + offline feature store, native to AWS.

```python
import sagemaker
from sagemaker.feature_store.feature_group import FeatureGroup

fg = FeatureGroup(name="user-clicks-30d", sagemaker_session=session)

fg.create(
    record_identifier_name="user_id",
    event_time_feature_name="event_ts",
    online_store_config={"EnableOnlineStore": True},
)
```

| Strength | Weakness |
|---|---|
| IAM-integrated, SageMaker-native | Less flexible than Feast / Tecton |
| Online + offline in one | Online store less battle-tested than Redis |
| Time travel via offline store | AWS-only |

For "we're a SageMaker shop" teams, this is the default. For multi-cloud, use Feast.

---

## OpenSearch + k-NN (vector search)

OpenSearch is AWS's search engine; the k-NN plugin adds vector search.

```python
import boto3
from opensearchpy import OpenSearch, helpers

# Create k-NN index
client.indices.create(
    index="docs",
    body={
        "settings": {"index.knn": True},
        "mappings": {
            "properties": {
                "embedding": {"type": "knn_vector", "dimension": 1024},
                "text": {"type": "text"},
                "metadata": {"type": "object"},
            }
        },
    },
)

# Query
client.search(
    index="docs",
    body={
        "size": 10,
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_embedding,
                    "k": 50,
                }
            }
        },
    },
)
```

| Strength | Weakness |
|---|---|
| Integrated with Elasticsearch / Logstash / Kibana | ANN quality behind Pinecone / Weaviate |
| Hybrid search (BM25 + vector) native | Heavier ops than serverless vector DBs |
| Cost-effective at scale | Less ergonomic than Pinecone |

---

## Textract (document AI)

For PDFs, scanned forms, tables.

```python
textract = boto3.client("textract")
response = textract.analyze_document(
    Document={"S3Object": {"Bucket": "docs", "Name": "key"}},
    FeatureTypes=["TABLES", "FORMS", "LAYOUT"],
)
# Parse blocks → text + tables
```

Used for ingestion pipelines over PDFs (see Module 5, Lesson 5).

---

## Glue / EMR + AI

For DE workflows, Glue and EMR are the **compute**; AI services plug in.

```python
# Glue job: enrich events with LLM-generated tags
from awsglue.context import GlueContext

glue = GlueContext(SparkContext.getOrCreate())

df = glue.create_dynamic_frame.from_catalog(database="events", table_name="raw")
df = df.apply_mapping([...])

# Tag with Bedrock (in a UDF)
def tag_with_llm(text):
    response = bedrock.invoke_model(...)
    return response.json()["tags"]

tagged = df.map(lambda r: tag_with_llm(r["text"]))
tagged.toDF().write.format("iceberg").save("s3://lake/tagged/")
```

The pattern: Glue/EMR for ETL, Bedrock for enrichment, S3/Iceberg for the lake.

---

## When to pick AWS vs alternatives

```
   ┌────────────────────────────────────────────────────────┐
   │  "We are an AWS shop, heavy SageMaker users"           │
   │  ──► Bedrock + SageMaker Feature Store + OpenSearch.   │
   │                                                        │
   │  "We are AWS shop but want best-of-breed vector DB"    │
   │  ──► Bedrock + Pinecone (hosted elsewhere) + Glue.     │
   │                                                        │
   │  "We are multi-cloud, don't want lock-in"              │
   │  ──► Bedrock for AWS, Vertex for GCP, but standardize  │
   │      on a portable vector DB (Pinecone / Weaviate).    │
   │                                                        │
   │  "We are AWS but heavy on Snowflake"                   │
   │  ──► Snowflake Cortex instead of Bedrock for SQL-near. │
   └────────────────────────────────────────────────────────┘
```

---

## The "Bedrock Knowledge Bases" pattern

Bedrock offers a **managed RAG** service: drop docs in S3, Bedrock chunks / embeds / stores in OpenSearch, exposes a `RetrieveAndGenerate` API.

```python
import boto3

bedrock_agent = boto3.client("bedrock-agent-runtime")
response = bedrock_agent.retrieve_and_generate(
    input={"text": "What is the refund policy?"},
    retrieveAndGenerateConfiguration={
        "type": "KNOWLEDGE_BASE",
        "knowledgeBaseConfiguration": {
            "knowledgeBaseId": "kb-abc123",
            "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
        },
    },
)
```

| Strength | Weakness |
|---|---|
| Zero glue code for RAG | Less control over chunking / retrieval |
| Pre-built ingest from S3 | Citations less rich than custom |
| Cheaper than building from scratch | Vendor-locked retrieval choices |

For prototype-to-prod on AWS, this is the fastest path. For fine-grained control, build the RAG yourself on OpenSearch + Bedrock.

---

## Cost modelling

```
   Per million events (typical DE workload):
   ────────────────────────────────────────
   Textract OCR (1000 pages):       $1.50
   Bedrock Titan Embed (1M tokens): $100
   Bedrock Sonnet (1M tokens in):   $3
   OpenSearch (managed, 100GB):     $200/mo
   SageMaker Feature Store online:  $250/mo
   ───────────────────────────
   Total: ~$600/mo + per-call costs
```

---

## What Comes Next

> Lesson 2 — **GCP AI for Data Engineers** — Vertex AI, BigQuery, Vector Search, and the GCP-native data + AI stack.