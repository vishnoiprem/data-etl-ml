# Lesson 3 — Vector DB Comparison

> **Type:** Article · Module 4 · Vector Databases & Embeddings
> Pinecone vs Weaviate vs Qdrant vs Milvus vs pgvector vs the cloud-managed services. The 2026 landscape.

---

## The 30-second take

| Use case | Pick |
|---|---|
| **Don't want to run infra** | Pinecone serverless |
| **Self-hosted, full control** | Qdrant or Milvus |
| **Already on Postgres** | pgvector |
| **Hybrid search + BM25 native** | Weaviate or Vespa |
| **Billion-scale, cost-sensitive** | Milvus or Qdrant with quantisation |
| **Cloud-native, your data is already there** | Vertex Matching Engine / Azure AI Search / Databricks Vector Search |
| **Just exploring, <100K vectors** | Chroma (in-memory) or pgvector |

---

## The detailed comparison

### Dedicated vector DBs

| Engine | Indexing | Strengths | Weaknesses | Cost (2026) |
|---|---|---|---|---|
| **Pinecone** | HNSW + proprietary | Serverless, zero-ops, fast | Vendor lock-in, can be pricey at scale | Pay per pod or serverless per query |
| **Weaviate** | HNSW + PQ | Strong hybrid search, modules for embedders | Operational overhead at scale | Open-source (BSD) + enterprise |
| **Qdrant** | HNSW + scalar/PQ | Rust performance, fast, filter-rich | Newer community | Open-source (Apache 2.0) + cloud |
| **Milvus** | HNSW, IVF, PQ, etc. | Billion-scale, many index types | Steeper learning curve | Open-source (Apache 2.0) + Zilliz Cloud |
| **Chroma** | HNSW | Easiest local dev, fast prototyping | Not for production | Open-source |

### Hybrid (SQL + vector)

| Engine | Notes |
|---|---|
| **pgvector** | Postgres extension. HNSW + IVF. Easy if you're already on Postgres. <10 M vectors comfortably. |
| **AlloyDB AI** (GCP) | Google's Postgres-compatible with vector + ML. |
| **SingleStore** | Distributed SQL with vector. |
| **ClickHouse** | Vector search as a column type. |

### Search engines

| Engine | Notes |
|---|---|
| **Elastic / OpenSearch** | Vector + BM25 hybrid, mature, ops-heavy. |
| **Vespa** | Best-in-class hybrid search, complex to operate. |
| **Typesense** | Lightweight, easier than Elastic. |

### Cloud-managed

| Service | Notes |
|---|---|
| **Vertex AI Matching Engine** (GCP) | Google's managed vector DB. Tight BigQuery / Vertex integration. |
| **Azure AI Search** | Microsoft's hybrid + vector. |
| **AWS OpenSearch Service** | OpenSearch as a service. |
| **Bedrock Knowledge Base** | AWS-managed RAG (vector + retrieval). |
| **Databricks Vector Search** | Delta-based, integrates with Unity Catalog. |
| **Snowflake Cortex Search** | In-warehouse vector search. |

---

## The "decision framework"

```
   ┌──────────────────────────────────────────────────────────┐
   │  ARE YOU ALREADY ON A WAREHOUSE / DB?                    │
   │                                                          │
   │  Postgres     ──► pgvector (until ~10M vectors)          │
   │  BigQuery     ──► BigQuery vector + Gemini                │
   │  Snowflake    ──► Cortex Search                          │
   │  Databricks   ──► Databricks Vector Search               │
   │                                                          │
   │  No → ARE YOU CLOUD-NATIVE?                              │
   │                                                          │
   │  AWS          ──► OpenSearch or Bedrock KB or Aurora pgv.│
   │  GCP          ──► Vertex Matching Engine                 │
   │  Azure        ──► Azure AI Search                        │
   │                                                          │
   │  No → ARE YOU OPTIMISING FOR COST OR FEATURES?           │
   │                                                          │
   │  Cost at scale ──► Milvus or Qdrant self-hosted          │
   │  Zero-ops       ──► Pinecone serverless                  │
   │  Hybrid search   ──► Weaviate or Vespa                  │
   │  Full control    ──► Qdrant (Rust, simple)               │
   └──────────────────────────────────────────────────────────┘
```

---

## The Pinecone vs Qdrant vs Weaviate breakdown

### Pinecone
- **Strengths:** Easiest to productionise. Serverless mode = zero infra. Strong metadata filtering. Multi-tenant.
- **Weaknesses:** Vendor lock-in. At billion scale, cost becomes a real line item. Less flexibility than self-hosted.
- **Pick when:** You want to ship fast and not run infra.

### Qdrant
- **Strengths:** Rust performance. Excellent metadata filtering. Easy to self-host. Apache 2.0. Cloud offering if you don't want to self-host.
- **Weaknesses:** Smaller community than Weaviate.
- **Pick when:** You want full control, Rust performance, and don't want to pay Pinecone prices.

### Weaviate
- **Strengths:** Built-in hybrid search (BM25 + vector). Built-in modules for many embedders. Strong semantic + keyword.
- **Weaknesses:** Operational overhead at scale; modules can be limiting.
- **Pick when:** Hybrid search is a hard requirement and you want it out of the box.

### Milvus
- **Strengths:** Billion-scale proven. Many index types. Flexible.
- **Weaknesses:** Steeper learning curve; multiple concepts to manage (collection, partition, index, segment).
- **Pick when:** You have billion-scale and ops engineers.

---

## pgvector — the underrated option

If you're **already on Postgres**, pgvector is the obvious first choice:

```sql
-- Create the extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add a column
ALTER TABLE documents ADD COLUMN embedding vector(1536);

-- Index
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);

-- Query: top 10 similar to a query embedding
SELECT id, content
FROM documents
WHERE tenant_id = 'acme'
  AND created_at > '2026-01-01'
ORDER BY embedding <=> $1
LIMIT 10;
```

**Works up to ~10 M vectors** before you need a dedicated engine. **Many production RAG systems never outgrow it.**

---

## The "lock-in" question

| Engine | Lock-in risk |
|---|---|
| Pinecone | 🔴 High — proprietary |
| Qdrant / Weaviate / Milvus | 🟢 Low — open-source, can migrate |
| pgvector | 🟢 None — Postgres |
| Vertex Matching Engine | 🔴 High — GCP |
| Azure AI Search | 🔴 High — Azure |

If lock-in matters, **self-hosted open-source** or **pgvector**.

---

## The cost model

| Engine | Cost driver | Typical monthly (10M vectors, 1M queries) |
|---|---|---|
| Pinecone serverless | per query + storage | ~$500–2000 |
| Qdrant cloud | per pod + storage | ~$300–800 |
| Milvus self-hosted | EC2/infra + storage | ~$200–500 |
| pgvector on existing RDS | storage + small CPU | ~$50–200 |
| Vertex Matching Engine | per node hour | ~$500–1500 |

**pgvector is dramatically cheaper** if you have the Postgres to run it on.

---

## The "I chose wrong" recovery plan

If you picked Pinecone and need to leave:

1. Export vectors as JSON / Parquet (Pinecone supports this).
2. Set up Qdrant / Milvus / pgvector.
3. Bulk-load with metadata.
4. Re-run your eval set. Confirm recall parity.
5. Cut over.

Plan for this on day one. Don't get caught.

---

## What Comes Next

> Lesson 4 — **Embedding Pipelines** — building the production pipeline: source → chunk → embed → upsert → refresh, with versioning and rollback.
