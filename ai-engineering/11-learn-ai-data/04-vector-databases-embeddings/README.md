# Module 4 — Vector Databases & Embeddings

> 7 lessons · The infrastructure of semantic search, RAG, and LLM-backed features
> Embeddings, ANN indexes, hybrid search, scale.

---

## Lesson Index

| # | Lesson | Type | Notes |
|---|--------|------|-------|
| 1 | [Embeddings Demystified](./01-embeddings-demystified.md) | Article | [Open](./01-embeddings-demystified.md) |
| 2 | [Vector DB Fundamentals](./02-vector-db-fundamentals.md) | Article | [Open](./02-vector-db-fundamentals.md) |
| 3 | [Vector DB Comparison](./03-vector-db-comparison.md) | Article | [Open](./03-vector-db-comparison.md) |
| 4 | [Embedding Pipelines](./04-embedding-pipelines.md) | Article | [Open](./04-embedding-pipelines.md) |
| 5 | [Hybrid Search](./05-hybrid-search.md) | Article | [Open](./05-hybrid-search.md) |
| 6 | [Vectors at Scale](./06-vectors-at-scale.md) | Article | [Open](./06-vectors-at-scale.md) |
| 7 | [Quiz: Vector Databases & Embeddings](./07-quiz-vectors.md) | Quiz | [Open](./07-quiz-vectors.md) |

---

## Module Outcomes

By the end of Module 4 you can:

1. **Explain** what an embedding is, what it preserves, and what it loses.
2. **Choose** between cosine, dot-product, and Euclidean distance for your retrieval task.
3. **Pick** the right vector database for your scale, latency, and operational constraints.
4. **Design** an embedding pipeline: source → chunk → embed → upsert → refresh.
5. **Combine** lexical (BM25) and semantic (ANN) retrieval for higher-quality search.
6. **Operate** a vector store at scale: sharding, replication, quantization, freshness.
7. **Evaluate** retrieval quality (recall@k, MRR, NDCG) and debug bad hits.

---

## The vector landscape at a glance

```
   ┌──────────────────────────────────────────────────────────────┐
   │                  VECTOR DB FAMILY                            │
   ├──────────────────────┬───────────────────────────────────────┤
   │  Dedicated vector DBs │ Pinecone · Weaviate · Qdrant · Milvus│
   │  Hybrid (SQL+vector)  │ pgvector · AlloyDB · SingleStore     │
   │  Search engines       │ Elastic · OpenSearch · Vespa        │
   │  Cloud-managed        │ Vertex AI Matching Engine · Azure   │
   │                       │ AI Search · Databricks Vector Search│
   └──────────────────────┴───────────────────────────────────────┘
   Same embeddings, very different operational stories.
```

(Full comparison in [`resources/vector-db-comparison.md`](../../resources/vector-db-comparison.md).)
