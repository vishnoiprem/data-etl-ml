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

## Worked Example — Bedrock + OpenSearch RAG over S3-stored PDFs

> **Goal:** Build a RAG system over 1M internal PDFs (compliance docs, contracts, runbooks). Stack: AWS-only. Use Bedrock for LLMs, OpenSearch for vectors, Textract for parsing, SageMaker Pipelines for ingest orchestration. Multi-tenant via AWS IAM.

### Architecture

```
   ┌──────────────────┐
   │  S3 bucket       │  s3://company-docs/  (1M PDFs, versioned)
   │  (raw PDFs)      │
   └────────┬─────────┘
            │  (event: PutObject)
            ▼
   ┌──────────────────┐
   │  EventBridge     │  routes to Step Functions
   │  + SQS           │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────────────────────────────────────┐
   │  Step Functions state machine                    │
   │                                                  │
   │  [Textract OCR + tables]                         │
   │        │                                         │
   │        ▼                                         │
   │  [Chunk (400 tok, recursive)]                    │
   │        │                                         │
   │        ▼                                         │
   │  [Bedrock Titan Embeddings]                      │
   │        │                                         │
   │        ▼                                         │
   │  [OpenSearch k-NN upsert + BM25]                 │
   └────────┬─────────────────────────────────────────┘
            │
            ▼
   ┌──────────────────────────────────────────────────┐
   │  QUERY TIME                                      │
   │                                                  │
   │  [API Gateway + Lambda]                          │
   │        │                                         │
   │        ▼                                         │
   │  [Embed via Bedrock Titan]                       │
   │        │                                         │
   │        ▼                                         │
   │  [OpenSearch hybrid search (BM25 + k-NN)]        │
   │        │                                         │
   │        ▼                                         │
   │  [Cohere Rerank on Bedrock] (optional)           │
   │        │                                         │
   │        ▼                                         │
   │  [Bedrock Claude Sonnet (answer + citations)]    │
   └──────────────────────────────────────────────────┘
```

### Step 1 — Ingest: Textract + chunk + embed

```python
# ingest/handler.py — invoked by Step Functions
import json
import boto3
from typing import Iterator

textract = boto3.client("textract")
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
s3 = boto3.client("s3")
opensearch = boto3.client("opensearch")


def handler(event, context):
    bucket = event["bucket"]
    key = event["key"]

    # 1. Textract
    response = textract.start_document_text_detection(
        DocumentLocation={"S3Object": {"Bucket": bucket, "Name": key}},
        FeatureTypes=["TABLES", "FORMS"],
    )
    job_id = response["JobId"]
    # poll until done (or use async pagination)
    text = wait_for_textract(job_id)
    tables = wait_for_textract_tables(job_id)

    # 2. Chunk (recursive, structure-aware)
    chunks = recursive_chunk(text, max_tokens=400, overlap=80)

    # 3. Embed (Bedrock Titan)
    embeddings = []
    for batch in batched(chunks, batch_size=20):
        body = json.dumps({"inputText": [c.text for c in batch]})
        resp = bedrock.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        embeddings.extend(json.loads(resp["body"].read())["embedding"])

    # 4. Upsert to OpenSearch
    for chunk, emb in zip(chunks, embeddings):
        opensearch.index(
            index="company-docs",
            body={
                "doc_id": chunk.doc_id,
                "tenant_id": chunk.tenant_id,
                "chunk_index": chunk.index,
                "text": chunk.text,
                "embedding": emb,
                "source_url": f"s3://{bucket}/{key}",
                "page_number": chunk.page_number,
                "heading_path": chunk.heading_path,
                "last_modified": chunk.last_modified,
            },
        )
```

### Step 2 — Query: Bedrock + OpenSearch hybrid

```python
# query/handler.py — Lambda behind API Gateway
import json
import boto3
from opensearchpy import OpenSearch

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
client = OpenSearch(
    hosts=[{"host": "search-xxx.us-east-1.es.amazonaws.com", "port": 443}],
    http_auth=(("user", "pass")),  # from Secrets Manager
    use_ssl=True,
)


def handler(event, context):
    user_query = event["query"]
    user_tenant = event["tenant_id"]      # from JWT claim
    user_roles = event["roles"]            # from JWT claim

    # 1. Embed query
    resp = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps({"inputText": user_query}),
    )
    query_emb = json.loads(resp["body"].read())["embedding"]

    # 2. Hybrid search with ACL filter (key part!)
    body = {
        "size": 10,
        "query": {
            "bool": {
                "must": {
                    "hybrid": {
                        "queries": [
                            {"match": {"text": user_query}},
                            {"knn": {
                                "embedding": {
                                    "vector": query_emb,
                                    "k": 50,
                                }
                            }},
                        ]
                    }
                },
                # ACL FILTER AT QUERY TIME — not in the LLM prompt
                "filter": [
                    {"term": {"tenant_id": user_tenant}},
                    {"bool": {"should": [
                        {"term": {"visibility": "public"}},
                        {"terms": {"allowed_roles": user_roles}},
                    ]}},
                ],
            }
        },
    }
    results = client.search(index="company-docs", body=body)

    chunks = [hit["_source"] for hit in results["hits"]["hits"]]

    # 3. Generate answer with citations (Bedrock Claude Sonnet)
    context = "\n\n".join(
        f"[Source {i+1}: {c['source_url']}, page {c.get('page_number', '?')}]\n{c['text']}"
        for i, c in enumerate(chunks)
    )
    prompt = f"""Answer using ONLY the sources below. Cite each claim with [Source N].
If the sources don't contain the answer, say "I don't know" — do not make up information.

SOURCES:
{context}

QUESTION: {user_query}

ANSWER:"""

    resp = bedrock.invoke_model(
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }),
    )
    answer = json.loads(resp["body"].read())["content"][0]["text"]

    # 4. Return with citations
    return {
        "answer": answer,
        "citations": [{"doc_id": c["doc_id"], "page": c["page_number"]} for c in chunks],
    }
```

### Step 3 — IAM policies (the AWS-native ACL pattern)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::123456789012:role/data-platform"},
      "Action": "es:ESHttp*",
      "Resource": "arn:aws:es:us-east-1:123456789012:domain/company-docs/*",
      "Condition": {
        "StringEquals": {
          "aws:RequestTag/tenant_id": "${aws:PrincipalTag/tenant_id}"
        }
      }
    }
  ]
}
```

The IAM role has a `tenant_id` tag. OpenSearch evaluates the resource policy and only returns documents matching the user's tenant. **ACL at the infra layer, not in code.**

### Cost roll-up (1M PDFs, 5K queries/day, single tenant for simplicity)

```
   ONE-TIME INGEST
   ────────────────
   Textract (1M pages × $1.50/1000):               $1,500  (one-shot)
   Bedrock Titan Embed (1M pages × 600 tok × 1M):
       = 600M tokens × $0.10/M                      $60     (one-shot)

   RECURRING (per month)
   ──────────────────────
   OpenSearch (managed t3.small.search × 3 AZ):     $200/mo
   Bedrock Titan Embed (5K queries × 200 tok):      $0.10/mo
   Bedrock Claude Sonnet (5K × 1.5K tok × $3/M):
       = 22.5M tokens × $3                          $68/mo
   Bedrock Claude Sonnet output (5K × 200 tok × $15/M):
       = 3M tokens × $15                            $45/mo
   S3 storage (1M PDFs, 50GB total):                $1.15/mo
   Lambda invocations:                               $0.20/mo
   ──────────────────────────────────────────────
   Total recurring:                                 ~$315/mo
   + one-shot ingest:                               $1,560
```

That's **less than $0.003 per query** for the entire pipeline. Affordable for internal use.

### What this example demonstrates

- The components actually touch (Textract → chunk → Bedrock → OpenSearch → Bedrock).
- The ACL pattern at **two layers**: OpenSearch query filter (semantic) + IAM policy (infra).
- The cost is **real** and **defensible** in a budget review.
- The architecture is **AWS-native** — minimal glue code. The trade-off is vendor lock-in (Lesson 2 covers alternatives).
- The IAM policy tag-based ACL is a pattern unique to AWS — if you're on AWS, this is the cheapest way to do per-tenant isolation.

This is the kind of architecture diagram you'd put in a kickoff doc and a cost doc on the same day.

---

## What Comes Next

> Lesson 2 — **GCP AI for Data Engineers** — Vertex AI, BigQuery, Vector Search, and the GCP-native data + AI stack.