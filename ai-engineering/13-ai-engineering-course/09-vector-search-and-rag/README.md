# Module 9 — Vector Search and RAG

> Source: Outcome School · Module 9 · 13 lessons

---

## Course Promise

> "Build a production-grade RAG pipeline and pick the right retrieval technique for the data."

From vector database internals (ANN, HNSW, IVF, PQ) to hybrid search, rerankers, ColBERT, chunking strategies, HyDE, semantic caching, and the advanced RAG variants (Agentic RAG, GraphRAG, Vectorless RAG).

---

## Lesson Index

| # | Lesson | Type | Theme |
|---|--------|------|-------|
| 1 | [How Does a Vector Database Work?](./01-how-does-a-vector-database-work.md) | Article + Worked Example | The internals, the ANN algorithms, the tradeoffs |
| 2 | ANN Search | Article | KD-trees, LSH, IVF, HNSW |
| 3 | Semantic Search | Article | Embeddings + similarity, the canonical flow |
| 4 | Hybrid Search | Article | BM25 + vector, RRF fusion |
| 5 | Rerankers | Article | Bi-encoder vs cross-encoder, the two-stage pattern |
| 6 | ColBERT | Article | Late interaction, MaxSim, the middle ground |
| 7 | Chunking Strategies | Article | Fixed, sentence, recursive, semantic, contextual, agentic |
| 8 | HyDE | Article | Hypothetical documents, search with fake answers |
| 9 | Embedding Cache | Article | The cache key, LRU eviction, TTL |
| 10 | Semantic Caching | Article | Match by meaning, the threshold tradeoff |
| 11 | Agentic RAG | Article | When the agent drives retrieval |
| 12 | GraphRAG | Article | Knowledge graphs + vector, local/global search |
| 13 | Vectorless RAG | Article | RAG without embeddings, tree-structured retrieval |

---

## The Lead Lesson

> **Lesson 1 — [How Does a Vector Database Work?](./01-how-does-a-vector-database-work.md)** — the foundation. Worked example: build a tiny vector DB from scratch in NumPy (brute force → IVF → HNSW) over 100K random vectors, measure latency/recall at each step, and produce the operating-point chart that drives every production decision.