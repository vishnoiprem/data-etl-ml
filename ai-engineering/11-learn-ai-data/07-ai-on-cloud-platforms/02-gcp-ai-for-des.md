# Lesson 2 — GCP AI for Data Engineers

> **Type:** Article · Module 7 · AI on Cloud Platforms
> Vertex AI, BigQuery, Vector Search, and the GCP-native data + AI stack.

---

## The GCP AI stack for DEs

```
   GCP AI SURFACE AREA (DE-RELEVANT)
   ─────────────────────────────────
   FOUNDATION MODELS    Vertex AI Model Garden
                        (Claude, Gemini, Llama, Mistral, ...)
                        Vertex AI Studio (prompt playground)

   EMBEDDINGS           Vertex AI Text Embeddings API
                        multimodal: image + text

   VECTOR SEARCH        Vertex AI Vector Search (formerly Matching Engine)
                        AlloyDB pgvector
                        BigQuery vector search (newer)

   FEATURE STORE        Vertex AI Feature Store
                        (offline: BigQuery / GCS; online: Vertex online)

   MODEL SERVING        Vertex AI Endpoints
                        Vertex AI Model Registry
                        Serverless prediction

   DOCUMENT AI          Document AI (OCR + extractors + custom processors)

   PIPELINES            Vertex AI Pipelines (Kubeflow)
                        + Dataflow / Dataproc / Composer (Airflow)

   NOTEBOOKS            Vertex AI Workbench / Colab Enterprise
```

For data engineers, the most-used surfaces: **Vertex AI** (model serving + endpoints), **Vertex AI Vector Search** (vector DB), **Vertex AI Feature Store** (online features), **Document AI** (unstructured), **BigQuery** (the lake + offline features).

---

## Vertex AI — the unified model platform

Vertex AI is the **single API** to data prep, training, deployment, monitoring, and feature management.

```python
from vertexai.generative_models import GenerativeModel

model = GenerativeModel("gemini-1.5-pro")
response = model.generate_content(
    "Summarise the events in this BigQuery table: ..."
)
print(response.text)
```

### Models available (2026)

| Provider | Models |
|---|---|
| Google | Gemini 1.5 Pro, Flash, Nano |
| Anthropic | Claude 3.5 Sonnet, Claude 3 Haiku |
| Meta | Llama 3.x |
| Mistral | Mistral, Mixtral |

### Why data engineers use Vertex AI

- **One platform for the ML lifecycle.** Data → Train → Deploy → Monitor, all in one UI.
- **Tight BigQuery integration.** Models can read BigQuery tables natively.
- **Vector Search is fast and managed.** (Was Matching Engine.)
- **Feature Store is BigQuery-native.** Offline = BigQuery, online = managed.
- **Pipelines = Kubeflow.** Standard, portable.

---

## Vertex AI Vector Search

Vector DB as a managed service. ANN at billion-scale, low ops.

```python
from google.cloud import aiplatform

# Create index
index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
    display_name="docs",
    contents_delta_uri="gs://bucket/embeddings/",
    dimensions=768,
    approximate_neighbors_count=50,
    distance_measure="DOT_PRODUCT_DISTANCE",
)

# Deploy to endpoint
endpoint = index.deploy(
    deployed_index_id="docs_endpoint",
    machine_type="e2-standard-16",
    min_replica_count=1,
)

# Query
response = endpoint.find_neighbors(
    queries=[query_embedding],
    num_neighbors=10,
)
```

| Strength | Weakness |
|---|---|
| Billion-scale, fully managed | IAM setup is heavier than Pinecone |
| Strong filter / metadata | Less ergonomic client library |
| Tight with BigQuery | Less portable |

---

## Vertex AI Feature Store

```python
from google.cloud.aiplatform import FeatureStore

fs = FeatureStore()

# Define feature view (BigQuery source)
fv = fs.create_feature_view(
    name="user_clicks_30d",
    source=fs.FeatureViewSource(
        big_query_source=aiplatform.gapic.FeatureView.BigQuerySource(
            table_uri="bq://project.dataset.user_clicks",
            entity_id_columns=["user_id"],
        )
    ),
    entity_id_columns=["user_id"],
)
```

| Strength | Weakness |
|---|---|
| BigQuery-native offline | GCP-only |
| Online serving low-latency | Less feature-engineering tooling than Tecton |
| One platform with Vertex | Tied to Vertex AI for serving |

---

## BigQuery as the AI substrate

The unique GCP move: **BigQuery itself does AI**. Vector search, embeddings, even model invocation from SQL.

```sql
-- Generate embeddings inside BigQuery
SELECT
  text,
  ML.GENERATE_EMBEDDING(
    MODEL `project.dataset.text_embed_model`,
    STRUCT(text AS content)
  ) AS embedding
FROM docs;

-- Vector search in SQL (BigQuery vector index)
SELECT base.doc_id, neighbor.doc_id, distance
FROM docs base, docs neighbor
WHERE base.doc_id = 'doc-1'
ORDER BY distance
LIMIT 5;
```

```sql
-- Call Gemini from SQL
SELECT
  ml_generate_text_result,
  prompt
FROM ML.GENERATE_TEXT(
  MODEL `project.dataset.gemini_model`,
  (SELECT 'Summarise this report' AS prompt),
  STRUCT(0.2 AS temperature, 1024 AS max_output_tokens)
);
```

This is the **lowest-friction way to do AI inside your warehouse**. No ETL out, no separate infra. AI in the lake.

---

## Document AI

```python
from google.cloud import documentai

client = documentai.DocumentProcessorServiceClient()
processor = client.processor_path("project", "us", "processor-id")

with open("doc.pdf", "rb") as f:
    document = documentai.RawDocument(content=f.read(), mime_type="application/pdf")

request = documentai.ProcessRequest(name=processor, raw_document=document)
result = client.process_document(request=request)
```

Document AI processors:
- **Form Parser** — extract from forms
- **OCR** — generic text from images/PDFs
- **Custom Extractor** — train on your own docs
- **Custom Classifier** — categorise documents

| Strength | Weakness |
|---|---|
| Best handwriting OCR (2026) | Higher per-doc cost than Textract |
| Custom extractors | Custom training data is on you |
| Tight Cloud Storage integration | GCP-only |

---

## Dataflow + Vertex AI

For streaming + AI:

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from vertexai.generative_models import GenerativeModel

class EnrichWithLLM(beam.DoFn):
    def process(self, element):
        model = GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(f"Tag this event: {element['text']}")
        element["tags"] = response.text
        yield element

with beam.Pipeline(options=PipelineOptions()) as p:
    (p
     | "Read" >> beam.io.ReadFromPubSub(...)
     | "Enrich" >> beam.ParDo(EnrichWithLLM())
     | "Write" >> beam.io.WriteToBigQuery("project.dataset.enriched"))
```

The pattern: Dataflow for stream processing, Vertex AI for LLM calls, BigQuery for the lake.

---

## The "BigQuery-centric" pattern

```
   GCP AI (for BigQuery shops)
   ──────────────────────────
   ┌────────────────────────────────────────────────┐
   │  BigQuery (the lake + offline features)         │
   │   │                                            │
   │   ├──► ML.GENERATE_TEXT() / GENERATE_EMBEDDING │
   │   │     (call Gemini / embed from SQL)          │
   │   │                                            │
   │   ├──► Vector index (BigQuery vector search)   │
   │   │                                            │
   │   └──► Feature view (offline features)          │
   │                                                │
   │  Vertex AI Feature Store (online)               │
   │   │                                            │
   │   └──► Online serving < 50ms                    │
   │                                                │
   │  Vertex AI Endpoints                            │
   │   │                                            │
   │   └──► Model serving for online inference       │
   └────────────────────────────────────────────────┘
```

If your data lives in BigQuery, **stay in BigQuery for as much of the AI pipeline as possible**. Move to Vertex only when you need online latency.

---

## Cost modelling

```
   Per million events (typical GCP DE workload):
   ────────────────────────────────────────────
   Gemini 1.5 Flash (1M tokens in):       $0.075
   Gemini 1.5 Pro (1M tokens in):         $1.25
   Vertex Text Embed (1M tokens):         $0.025
   Vector Search (managed, 100GB):        ~$200/mo
   Feature Store online:                 ~$200/mo
   BigQuery vector search (per query):    ~$0.001
   Document AI (1000 pages):             $1.50
   ───────────────────────────────
   Total: ~$500/mo + per-call costs
```

GCP is generally the **cheapest of the three clouds** for AI inference at scale (Gemini Flash is very cheap).

---

## What Comes Next

> Lesson 3 — **Azure AI for Data Engineers** — Azure OpenAI, AI Foundry, AI Search, and the Azure / Fabric / Synapse stack.