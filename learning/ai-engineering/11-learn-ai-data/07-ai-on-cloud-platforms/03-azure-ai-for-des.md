# Lesson 3 — Azure AI for Data Engineers

> **Type:** Article · Module 7 · AI on Cloud Platforms
> Azure OpenAI, AI Foundry, AI Search, and the Azure / Fabric / Synapse stack.

---

## The Azure AI stack for DEs

```
   AZURE AI SURFACE AREA (DE-RELEVANT)
   ───────────────────────────────────
   FOUNDATION MODELS    Azure OpenAI Service (GPT-4o, o1, ...)
                        Models as a Service (Maas) — Llama, Mistral, Cohere

   EMBEDDINGS           Azure OpenAI text-embedding-3-large / -small
                        Cohere on Azure

   VECTOR SEARCH        Azure AI Search (formerly Cognitive Search)
                        Azure Cosmos DB vector
                        PostgreSQL pgvector (Flexible Server)

   FEATURE STORE        Azure Machine Learning Feature Store
                        (offline: ADLS + Delta; online: Redis Cache)

   MODEL SERVING        Azure AI Foundry (unified model deployment)
                        Azure ML Endpoints (managed / Kubernetes)

   DOCUMENT AI          Azure AI Document Intelligence
                        (formerly Form Recognizer)

   PIPELINES            Azure Data Factory / Synapse Pipelines
                        Azure ML Pipelines
                        Fabric Data Factory

   NOTEBOOKS            Azure ML Studio / Synapse Studio / Fabric
```

For data engineers, the most-used: **Azure OpenAI** (LLMs with enterprise compliance), **AI Search** (vector DB + RAG), **Document Intelligence** (unstructured), **Synapse / Fabric** (the lake + warehouse).

---

## Azure OpenAI Service

The **enterprise-safe** OpenAI endpoint. Same models, with Azure's identity, networking, and compliance.

```python
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-08-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

response = client.chat.completions.create(
    model="gpt-4o",  # deployment name
    messages=[
        {"role": "user", "content": "Summarise this Synapse table ..."}
    ],
)
```

### Models available (2026)

| Provider | Models |
|---|---|
| OpenAI | GPT-4o, GPT-4o-mini, o1, o1-mini, embeddings |
| Meta | Llama 3.x via MaaS |
| Mistral | Mistral Large, Mixtral via MaaS |
| Cohere | Command R+, embed-v3 |

### Why data engineers use Azure OpenAI

- **Enterprise compliance.** SOC2, HIPAA, regional isolation, customer-managed keys.
- **VNet integration.** Endpoints can sit inside your private network.
- **PTU (Provisioned Throughput Units).** Buy reserved capacity for predictable cost.
- **Content filtering.** Built-in safety, plus Azure AI Content Safety for custom filters.

### PTU economics

```
   PAY-AS-YOU-GO                  PROVISIONED (PTU)
   ──────────────                  ────────────────
   Per token                       Per hour (reserved)
   Good for variable load          Good for steady high load
   Surprise bills possible         Predictable bill
   ~$5–30/1M tokens                ~$1–3/hour per PTU
                                   (roughly 100–300 req/min)
```

For DE workloads with steady traffic, **PTUs are 30–50% cheaper** than PAYG.

---

## Azure AI Search (vector DB + RAG)

AI Search is Azure's hybrid search engine with built-in vector + RAG.

```python
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

client = SearchClient(endpoint=endpoint, index_name="docs", credential=cred)

results = client.search(
    search_text="refund policy",
    vector_queries=[VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=10,
        fields="embedding",
    )],
    filter="tenant_id eq 'acme'",
    select=["doc_id", "text", "source_url"],
)
```

| Strength | Weakness |
|---|---|
| Hybrid search (BM25 + vector) native | Less battle-tested at billion-scale |
| Integrated with Azure OpenAI for RAG | Heavier ops than Pinecone |
| ACL + indexer pipeline from ADLS | Less portable than open-source |

### Indexer pattern (managed ingestion)

```
   ADLS (PDFs, JSON, ...)
        │
        ▼
   AI Search Indexer
     ├──► skillset: chunk → embed → extract entities
     └──► writes to AI Search index
```

You can run a **fully managed ingest pipeline** without writing embedding code. For most Azure RAG, this is the default.

---

## Azure AI Foundry

The unified portal for building, deploying, and operating AI apps.

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=os.environ["PROJECT_CONNECTION_STRING"],
)

# Deploy model
client.deployments.create_or_update(
    model="gpt-4o",
    deployment_name="gpt-4o-prod",
    sku={"name": "Standard", "capacity": 30},
)
```

AI Foundry wraps model deployment, prompt flow, evaluation, monitoring, and content safety into one UI/API.

---

## Azure AI Document Intelligence

```python
from azure.ai.formrecognizer import DocumentAnalysisClient

client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

with open("doc.pdf", "rb") as f:
    poller = client.begin_analyze_document("prebuilt-layout", document=f)
result = poller.result()

# Extract tables, key-value pairs, layout
for table in result.tables:
    for cell in table.cells:
        print(cell.content)
```

| Strength | Weakness |
|---|---|
| Pre-built models for invoices, receipts, contracts | Per-page cost adds up |
| Custom models for forms | Custom training data is on you |
| Strong table extraction | Azure-only |

---

## Synapse / Fabric + AI

For data engineers, **the lake + warehouse** is usually Synapse or Fabric. AI services plug in:

```sql
-- Synapse SQL: call Azure OpenAI from a SQL query (via external endpoint)
SELECT
  *,
  dbo.CallOpenAI(text_column) AS summary
FROM events;
```

```python
# Fabric notebook (PySpark): call Azure OpenAI
import openai
client = AzureOpenAI(...)

df = spark.read.format("delta").load("Tables/events")
def summarize(text):
    return client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"Summarise: {text}"}],
    ).choices[0].message.content

summary_udf = udf(summarize, StringType())
df.withColumn("summary", summary_udf("text")).write.format("delta").mode("overwrite").save("Tables/summarised")
```

The pattern: Fabric / Synapse for ETL, AI services for enrichment, Delta / OneLake for the lake.

---

## The "Azure + enterprise compliance" sweet spot

```
   ┌─────────────────────────────────────────────────────┐
   │  Azure AI wins when:                                │
   │                                                     │
   │   - You're an enterprise with regulatory burden     │
   │     (SOC2, HIPAA, FedRAMP, data residency)          │
   │   - You need VNet integration / private endpoints   │
   │   - You want PTUs for cost predictability          │
   │   - You already use Synapse / Fabric / ADLS         │
   │   - You want a single-vendor support contract      │
   │                                                     │
   │  Azure AI loses when:                               │
   │                                                     │
   │   - You want the cheapest inference (GCP wins)      │
   │   - You're multi-cloud and want portability         │
   │   - You want best-in-class vector DB at scale       │
   │     (Pinecone / Weaviate win)                        │
   └─────────────────────────────────────────────────────┘
```

---

## Cost modelling

```
   Per million events (typical Azure DE workload):
   ──────────────────────────────────────────────
   Azure OpenAI GPT-4o (1M tokens):       $5
   Azure OpenAI GPT-4o-mini:              $0.15
   Embeddings (text-embedding-3-small):  $0.02
   AI Search (S2 tier, 100GB):           ~$250/mo
   Document Intelligence (1000 pages):   $1.50
   AI Foundry:                           $0 (managed control plane)
   ────────────────────────────────────
   Total: ~$300/mo + per-call costs
```

---

## What Comes Next

> Lesson 4 — **Databricks AI** — Mosaic AI, Unity Catalog, vector search on Delta, and the lakehouse-AI pattern.