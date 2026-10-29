# Lesson 7 — Quiz: Vector Databases & Embeddings

> **Type:** Quiz · Module 4 · Vector Databases & Embeddings
> Self-check on the seven lessons. Answers at the bottom.

---

## Section A — Conceptual

**Q1.** Which distance metric is most common for text embeddings?
- A) Euclidean (L2)
- B) Manhattan (L1)
- C) Cosine similarity
- D) Hamming

**Q2.** Which ANN index family is graph-based?
- A) IVF
- B) PQ
- C) HNSW
- D) LSH

**Q3.** The single biggest cost lever at billion-vector scale is:
- A) Choosing the right embedding model
- B) Quantisation
- C) Picking the right cloud
- D) Using hybrid search

**Q4.** Which vector DB is the most natural fit if you're already on Postgres?
- A) Pinecone
- B) Weaviate
- C) pgvector
- D) Milvus

**Q5.** The "M" in Matryoshka embeddings refers to:
- A) Memory-efficient storage
- B) Multi-resolution embeddings (variable dimension)
- C) Multi-tenant isolation
- D) Multi-lingual support

**Q6.** Which is **not** a hybrid-search fusion method?
- A) Reciprocal Rank Fusion
- B) Weighted score fusion
- C) Cross-encoder reranking
- D) Bucket aggregation

**Q7.** At 1B vectors with 1536 dims and float32, raw vector storage is approximately:
- A) 60 GB
- B) 600 GB
- C) 6 TB
- D) 60 TB

---

## Section B — Scenario

**Q8.** Your team is starting a RAG project for 200K internal documents (~50M chunks after splitting). You already have a Postgres warehouse. What vector DB do you pick and why?

**Q9.** You're at 50M vectors and your recall@10 has dropped from 0.92 to 0.86 over the last month. Walk through the debugging steps.

**Q10.** A stakeholder asks "should we use a vector DB or just store embeddings in S3 and load them into memory?" What's your answer?

---

## Section C — Practical

**Q11.** Write the metadata schema you would use for a multi-tenant RAG system over a knowledge base.

**Q12.** List 5 things you would include in an "embedding pipeline observability" dashboard.

**Q13.** You need to upgrade from `text-embedding-3-small` (1536 dim) to `text-embedding-3-large` (3072 dim) for 100M vectors. Outline the migration plan in 5–7 steps.

---

## Section D — Open

**Q14.** Pick a real retrieval use case from your work. Sketch: the embedding model, the chunking strategy, the metadata schema, and the eval set you would build.

---

## Answer Key

<details>
<summary>A1</summary>

**C** — Cosine similarity. Most text embedding models are trained with cosine or dot-product loss. Use Euclidean only when absolute position matters (it usually doesn't for text).

</details>

<details>
<summary>A2</summary>

**C** — HNSW (Hierarchical Navigable Small Worlds). IVF is partition-based; PQ is compression-based; LSH is hashing.

</details>

<details>
<summary>A3</summary>

**B** — Quantisation. Scalar int8 gives 4× reduction; PQ gives 16–64×. The cost difference is the dominant lever.

</details>

<details>
<summary>A4</summary>

**C** — pgvector. You're already on Postgres. Don't add a new system for what you can do with an extension.

</details>

<details>
<summary>A5</summary>

**B** — Multi-resolution embeddings. Train at high dim, embed at variable dim at inference. Like Matryoshka dolls (nested).

</details>

<details>
<summary>A6</summary>

**D** — Bucket aggregation is not a fusion method. RRF, weighted score, and cross-encoder reranking are the standard approaches.

</details>

<details>
<summary>A7</summary>

**C** — 1B × 1536 × 4 bytes = 6.144 TB raw. With index overhead, 12–18 TB.

</details>

<details>
<summary>A8</summary>

A model answer:

**Pick pgvector.** You're already on Postgres. 50M chunks is well within pgvector's comfort zone (up to ~10M; we'd push to ~50M with HNSW + reasonable metadata). It avoids adding a new system, ops surface, and integration complexity. The cost is storage + small CPU on the existing instance. If we outgrow pgvector, the migration path to Qdrant or Weaviate is straightforward — vectors are vectors, we own the embedder.

If for some reason pgvector doesn't work (e.g. our DBA team blocks extensions, or recall is too low at this scale), I'd pick Qdrant Cloud for the self-host-grade control without self-hosting.

</details>

<details>
<summary>A9</summary>

A model answer — debugging steps in order:

1. **Check the embedding model version.** Did someone roll back? Are new chunks being embedded with the old model?
2. **Check the chunking.** Did the chunking strategy change? A regression in chunking can drop recall without changing the embedder.
3. **Run the eval set.** Which queries regressed? Look for patterns (specific topic, specific length, specific doc type).
4. **Check the metadata filters.** Did a filter get added that excludes relevant chunks?
5. **Check the index health.** HNSW can degrade if `ef_construction` was tuned too low during recent bulk inserts.
6. **Sample the bad hits.** Look at the actual retrieved chunks — are they irrelevant, or just ranked poorly?
7. **Rerank.** Add a cross-encoder reranker. Often recovers 5–10% recall without touching anything else.
8. **Investigate source drift.** Did the source documents change in a way that broke the embedding?

</details>

<details>
<summary>A10</summary>

A model answer:

S3 + load-into-memory works only at very small scale (<100K vectors) and very low query volume (<1 QPS). Beyond that, you lose:
- Sub-second ANN search
- Real-time updates
- Metadata filtering
- Production SLAs (uptime, latency, recall)

For anything serious, a vector DB is the right call. The cost of a vector DB at small scale (pgvector on existing Postgres) is essentially zero. At larger scale, the cost of running your own ANN search in S3 quickly exceeds the cost of a managed vector DB.

Reserve "S3 + in-memory" for prototypes and demos.

</details>

<details>
<summary>A11</summary>

A model answer:

```yaml
metadata:
  tenant_id: string        # isolation
  doc_id: string           # chunk → doc
  chunk_index: int         # reassemble
  text: string             # the chunk content
  source: string           # URL, file path, table name
  source_type: string      # "confluence", "notion", "ticket"
  created_at: timestamp    # freshness
  updated_at: timestamp    # freshness
  acl: list[string]        # ["org:acme", "team:data-eng"]
  language: string         # "en", "es", ...
  doc_type: string         # "policy", "runbook", "spec"
  tags: list[string]       # ["pii:no", "tier:1"]
  embedding_model: string  # "text-embedding-3-small@2024-01"
  embedding_dim: int       # 1536
  embedding_version: int   # bumped on re-embed
```

</details>

<details>
<summary>A12</summary>

A model answer:

1. **Throughput** — vectors embedded/upserted per minute
2. **Freshness lag** — time from source change to vector available
3. **Completeness** — source count vs vector count (delta = bug)
4. **Embedding cost** — dollars per day / per million chunks
5. **Recall on held-out eval** — run nightly against 50-query eval set, alert on drop > 2%
6. **Query latency** — p50, p95, p99 per shard
7. **Index size** — vector count, memory used, growth rate

</details>

<details>
<summary>A13</summary>

A model answer:

1. **Stand up new index** (or new collection) alongside old. Bump `embedding_version` in metadata.
2. **Backfill** — re-embed all 100M chunks in batches of 10K. Throttle to ~100K/min. ~16 hours.
3. **A/B test** — 10% of queries go to new index; 90% to old. Compare recall on held-out eval set.
4. **Tune** — adjust alpha (lexical/semantic weight), reranker threshold based on A/B results.
5. **Cut over** — flip 100% of queries to new index. Monitor for 24h.
6. **Delete old vectors** — free storage. Bump `embedding_version` to new value.
7. **Update docs** — record the migration in the change log; update the catalog with the new model name.

Total time: 1–2 weeks including monitoring windows.

</details>

<details>
<summary>A14</summary>

This is a personal exercise. The four pieces you should be able to articulate:

- **Embedding model:** Why this model? (cost, accuracy, latency, language support)
- **Chunking strategy:** Size, overlap, hierarchical? Metadata preserved?
- **Metadata schema:** Which fields, why, who owns them?
- **Eval set:** How many queries, how curated, how refreshed, how scored?

If you can't articulate all four, you don't have a plan — you have a prototype.

</details>

---

*End of Module 4. Move to [Module 5 — RAG & LLM Data Infrastructure](../05-rag-llm-data-infrastructure/README.md).*
