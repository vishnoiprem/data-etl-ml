# Vector DB Comparison

> Pinecone vs Weaviate vs Qdrant vs Milvus vs pgvector vs Chroma vs LanceDB. Decision framework for 2026.

---

## TL;DR decision framework

```
   ┌──────────────────────────────────────────────────────────┐
   │  "Are you already on Postgres / Aurora?"                  │
   │   YES ──► pgvector. No new infra. Good to ~10M vectors.   │
   │                                                          │
   │  "Single-cloud, want managed, ops-light?"                 │
   │   AWS ──► OpenSearch k-NN                                │
   │   GCP ──► Vertex AI Vector Search                         │
   │   Azure ──► Azure AI Search                               │
   │                                                          │
   │  "Multi-cloud / portable, want managed?"                  │
   │   Pinecone. Pay per pod, no infra to run.                │
   │                                                          │
   │  "Self-hosted, want most popular OSS?"                    │
   │   Qdrant (Rust, fast, good filters) or Weaviate (Go).    │
   │                                                          │
   │  "Billion-scale + production?"                            │
   │   Milvus (or Pinecone Enterprise).                        │
   │                                                          │
   │  "Embedded / in-process / RAG prototype?"                 │
   │   Chroma (Python-native) or LanceDB.                     │
   └──────────────────────────────────────────────────────────┘
```

---

## Feature comparison

| Feature | Pinecone | Weaviate | Qdrant | Milvus | pgvector | Chroma | LanceDB |
|---|---|---|---|---|---|---|---|
| **License** | Closed (managed) | Open (BSL since v1.27) | Open (Apache 2.0) | Open (Apache 2.0) | Open (Postgres) | Open (Apache 2.0) | Open (Apache 2.0) |
| **Hosted** | Yes | Yes (WCD) | Yes (Qdrant Cloud) | Yes (Zilliz) | via Postgres services | via Chroma Cloud | via hosted options |
| **Self-host** | No | Yes | Yes | Yes | Yes | Yes | Yes |
| **ANN algo** | Proprietary | HNSW | HNSW + IVF | HNSW, IVF, PQ, DiskANN | HNSW + IVF | HNSW | IVF (Lance columnar) |
| **Hybrid search** | Sparse-dense | Native | Native | Native (via ranker) | Manual (BM25 + recency) | Limited | Limited |
| **Metadata filters** | Strong | Strong | Strong (best) | Strong | Strong (SQL) | Weak | Moderate |
| **Multi-tenancy** | Namespaces | Namespaces / tenants | Collections | Databases / partitions | Schemas | Collections | Namespaces |
| **Vector dim** | Up to 20k | Up to 65k | Up to 65k | Up to 65k | Up to 16k (pgvector) | Up to 65k | Up to 65k |
| **Recall ceiling** | 99%+ | 99%+ | 99%+ | 99%+ | 95%+ (HNSW) | 95%+ | 95%+ |
| **Latency p50** | < 10ms | < 15ms | < 10ms | < 15ms | < 20ms | < 30ms | < 30ms |
| **Best scale** | 10B+ vectors | 1B | 1B | 10B+ | ~10M (in a single Postgres) | ~10M | ~100M |
| **Community size** | Large | Large | Large | Large | Huge (Postgres) | Growing | Growing |
| **SDK languages** | Python, JS, Go, Java | Python, JS, Go, Java | Python, Rust, JS, Go, Java | Python, JS, Go, Java, C++ | Any Postgres client | Python, JS | Python |

---

## Cost comparison (rough, 2026)

For 10M vectors at 1024-dim, ~10 QPS average, ~100ms p95:

| Option | Monthly cost (approx) |
|---|---|
| **Pinecone Serverless** | $200–400 |
| **Pinecone Pod (p2.x1)** | $300–500 |
| **Weaviate Embedded** (single node) | $50 (compute) |
| **Weaviate Cloud** (Enterprise) | $400–800 |
| **Qdrant Cloud** (single node) | $200–400 |
| **Milvus / Zilliz** (single node) | $300–600 |
| **Milvus / Zilliz Enterprise** | $1k–3k |
| **pgvector** (Aurora / RDS / Postgres) | $100–300 (DB) |
| **OpenSearch k-NN** (managed) | $300–600 |
| **Chroma** (self-hosted) | $50–100 |
| **LanceDB** (self-hosted) | $50–100 |

---

## When to pick each

### Pinecone
- **Pros:** Zero ops, strong hybrid, easy scale, good SDK.
- **Cons:** Vendor lock-in, cost grows fast, no on-prem.
- **Pick if:** You're a small team, can't / won't operate a vector DB.

### Weaviate
- **Pros:** Mature, hybrid search native, GraphQL API, multi-modal.
- **Cons:** BSL licence for v1.27+, ops complexity at scale.
- **Pick if:** Hybrid search is critical, multi-modal.

### Qdrant
- **Pros:** Rust (fast), best-in-class metadata filters, Apache 2.0.
- **Cons:** Newer than Weaviate; smaller ecosystem.
- **Pick if:** Strong filtering matters (e.g., ACL), self-hosting preferred.

### Milvus
- **Pros:** Billion-scale, multi-algo (HNSW / IVF / PQ / DiskANN), production-tough.
- **Cons:** Complex ops at scale; needs careful tuning.
- **Pick if:** 1B+ vectors, large ML team.

### pgvector
- **Pros:** Zero new infra, transactional consistency with Postgres, SQL joinable, PII/ACL via Postgres RLS.
- **Cons:** Limited to ~10M vectors; HNSW recall ceiling; no dedicated hybrid search.
- **Pick if:** You're already on Postgres, scale < 10M vectors.

### Chroma
- **Pros:** Python-native, simplest possible API, great for prototypes.
- **Cons:** Not production-grade at scale.
- **Pick if:** Prototyping, single-machine, < 1M vectors.

### LanceDB
- **Pros:** Columnar, serverless embedding, great with PyArrow.
- **Cons:** Newer, smaller community.
- **Pick if:** Embedded analytics, ML pipelines with columnar data, serverless.

---

## The "metadata filter" decision

If ACL / filtering is core, **Qdrant** has the strongest story. **Weaviate** and **Pinecone** are close. **pgvector** lets you JOIN with relational data (often the right pattern anyway). **Milvus** has partition key support for very large tenant counts.

---

## The "hybrid search" decision

| Vector DB | Native hybrid? |
|---|---|
| Pinecone | Yes (sparse-dense, native) |
| Weaviate | Yes (native, multiple vectorisers per object) |
| Qdrant | Yes (named vectors + sparse) |
| Milvus | Yes (via hybrid search API) |
| pgvector | No native (BM25 via tsvector, fuse in app) |
| Chroma | No native |
| LanceDB | Limited |

If hybrid is **non-negotiable**, Pinecone / Weaviate / Qdrant all qualify. Choose based on hosting model.

---

## Migration path

When you outgrow a vector DB:

```
   Chroma  ─────────►  pgvector / Qdrant / Weaviate
       (prototyping)            (early prod)

   pgvector ─────────►  Qdrant / Weaviate / Pinecone
       (< 10M vectors)            (10M–100M+ vectors)

   Qdrant / Weaviate ─────────►  Pinecone / Milvus
       (self-hosted)               (managed / billion-scale)

   Cost gate: if vector DB > $5k/mo, re-evaluate host model.
```

The migration involves:
1. Re-embed with a normalised 1024-dim vector (or whatever you target).
2. Recreate indexes.
3. Re-run eval set, compare recall@k vs current.
4. Cut over with feature flag.
5. Decommission the old DB after 7 days of stability.

---

## Anti-patterns

1. **Using two vector DBs in production.** Pick one. The cost of operation is real.
2. **Re-embedding on schema change.** If your index is on `id + vector + metadata`, schema on metadata fields doesn't require re-embedding.
3. **Filters that force full-scan.** If a query filters by `category = "X"` and 99% of vectors aren't category X, your index isn't helping. Partition or split.
4. **Over-tagging metadata.** Every metadata field is indexed. Keep it to ≤ 10 fields.
5. **Pointless dimensionality.** 3072-d embeddings don't magically beat 1024-d for most tasks. Cost grows linearly with dim.
6. **No recall@10 baseline.** If you don't measure recall vs ground truth, you're flying blind.
