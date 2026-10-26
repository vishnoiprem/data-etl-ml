# Codebook Exercises — Section 6: Vector Databases

> **Paired exercises for [`../ai-engineer-codebook.md` § 6](../ai-engineer-codebook.md#section-6-vector-database-cheat-sheet).**
> These turn reference snippets into active practice. For each reference snippet in the codebook, here are 3-5 challenges that force you to modify, extend, and break the code.

---

## How to use these

1. Open the reference snippet in [`../ai-engineer-codebook.md`](../ai-engineer-codebook.md) — Section 6 (Vector DBs)
2. Read the snippet once
3. Do the exercises below IN ORDER — each builds on the previous
4. For each exercise, benchmark a vector DB on your data, note what you learned

**Time per exercise:** 20-30 min.
**Total time for this section:** 4-6 hours.

---

## Snippet 6.1 — Chroma (Easiest)

**Reference:** [`../ai-engineer-codebook.md#61-chroma-easiest`](../ai-engineer-codebook.md#61-chroma-easiest)

### Exercise 6.1.1: Build a Chroma-backed RAG

```python
# TODO: Index 100 docs in Chroma (in-memory). Build a simple RAG.
# Measure: index time, query latency (p50, p99), recall@5.
# Chroma is great for prototyping but doesn't scale to millions.
```

### Exercise 6.1.2: Chroma persistence modes

```python
# TODO: Compare 3 modes:
# - in-memory (default, lost on restart)
# - persistent (LocalFileStore)
# - client-server (separate process)
# Measure: startup time, query latency, durability.
```

### Exercise 6.1.3: When Chroma breaks down

```python
# TODO: Push Chroma to 1M vectors, 1536-dim. Where does it hurt?
# - Query latency
# - Memory usage
# - Index build time
# - Crash frequency
# This is the moment to migrate to Pinecone / Weaviate / Qdrant.
```

---

## Snippet 6.2 — Pinecone (Production)

**Reference:** [`../ai-engineer-codebook.md#62-pinecone-production`](../ai-engineer-codebook.md#62-pinecone-production)

### Exercise 6.2.1: Index design — namespaces + metadata

```python
# TODO: In a single Pinecone index, use:
# - namespaces for per-user isolation
# - metadata for filtering: {user_id, doc_id, date, type}
# - filter on every query to enforce isolation
# Test: user A queries, verify they only see their own vectors.
```

### Exercise 6.2.2: Pinecone cost model

```python
# TODO: Model your Pinecone cost:
# - $0.096/hour for p1.x1 (1 pod, ~5M vectors)
# - $0.24/hour for p1.x2
# - Storage: included up to pod size, then $0.0002/GB-hour
# - Queries: included in pod cost
# - For 10M vectors: p2.x1 ($0.48/hr) or self-host Qdrant
# Compare: Pinecone vs self-host at scale.
```

### Exercise 6.2.3: Pinecone hybrid query (sparse + dense)

```python
# TODO: Newer Pinecone supports hybrid sparse+dense queries.
# - Sparse: BM25-style for keyword match
# - Dense: vector for semantic
# - Combined with weighted alpha
# Compare: hybrid vs dense alone. Where does hybrid help?
```

---

## Snippet 6.3 — Weaviate

**Reference:** [`../ai-engineer-codebook.md#63-weaviate`](../ai-engineer-codebook.md#63-weaviate)

### Exercise 6.3.1: Self-host Weaviate with Docker

```bash
# TODO: docker run -d -p 8080:8080 semitechnologies/weaviate:latest
# Then index 10K vectors, query. Measure latency.
# Self-host = you control the cost (vs Pinecone's per-pod fee).
```

### Exercise 6.3.2: Weaviate's built-in vectorization

```python
# TODO: Weaviate can call OpenAI / Cohere / HuggingFace to embed for you.
# - No need to embed client-side
# - But: every doc upload = 1 OpenAI call = $$
# Compare: Weaviate-managed embeddings vs your own.
```

### Exercise 6.3.3: Weaviate GraphQL API

```python
# TODO: Query Weaviate with GraphQL:
# {
#   Get {
#     Article(nearText: {concepts: ["AI safety"]}, limit: 5) {
#       title
#       _additional { distance }
#     }
#   }
# }
# - Filter + vector search in one query
# - Useful for multi-modal RAG
```

---

## Snippet 6.4 — pgvector (Postgres)

**Reference:** [`../ai-engineer-codebook.md#64-pgvector-postgresql`](../ai-engineer-codebook.md#64-pgvector-postgresql)

### Exercise 6.4.1: pgvector for small RAG (<100K vectors)

```sql
-- TODO: Enable pgvector. Create a table with an embedding column.
-- CREATE EXTENSION vector;
-- CREATE TABLE docs (id SERIAL, content TEXT, embedding vector(1536));
-- CREATE INDEX ON docs USING ivfflat (embedding vector_cosine_ops);
-- Index 50K vectors. Query. Measure latency.
```

### Exercise 6.4.2: pgvector vs Pinecone cost

```python
# TODO: Compare cost for 1M vectors:
# - Pinecone: p2.x1 pod = $350/mo (1M vectors, 1000 QPS)
# - pgvector on RDS: db.r6g.xlarge = $300/mo (compute) + storage
# - Self-host pgvector on EC2: ~$100/mo
# At what scale does pgvector become a clear winner?
```

### Exercise 6.4.3: pgvector HNSW vs IVFFlat

```python
# TODO: Compare index types:
# - IVFFlat: faster build, slower query, less memory
# - HNSW: slower build, faster query, more memory
# Test: 100K vectors, 1000 queries. Plot p99 latency.
# HNSW is usually the better choice for production.
```

---

## Cross-cutting challenges (Mid+)

### Challenge A: Multi-tenant vector search

```python
# TODO: 1000 tenants in one index. Each can only see their own vectors.
# Implement: per-tenant namespace OR metadata filter on every query.
# Compare: query latency, isolation guarantees, ops complexity.
```

### Challenge B: Migrate from one vector DB to another

```python
# TODO: You have 1M vectors in Pinecone. You want to move to Qdrant (self-host) to save $200/mo.
# - Export: stream all vectors + metadata
# - Transform: rename fields, change IDs
# - Import: bulk insert into new index
# - Verify: same recall@5 on a test set
# How long does it take? How do you cut over with zero downtime?
```

### Challenge C: Vector DB at 100M scale

```python
# TODO: Sketch the architecture for 100M vectors:
# - Single instance: Qdrant / Weaviate can do 10-50M per node
# - Sharded: by tenant, by date, by topic
# - Tiered: hot (recent) on SSD, cold (old) on disk
# - Cost: $1K-5K/mo for managed, $500-2K for self-host
# When do you need to consider this scale? What triggers the move?
```

---

## Architect-level reflections (Senior+)

After completing these exercises, write a 1-page design doc answering:

1. **Vector DB choice at MVP?** (Chroma for <100K, Pinecone for <5M, self-host beyond)
2. **Index type?** (HNSW vs IVFFlat vs SPANN)
3. **Metadata strategy?** (filter on every query for multi-tenancy)
4. **Hybrid search?** (BM25 + vectors, when worth it)
5. **Re-ranking?** (always, or only for hard queries)
6. **Migration triggers?** (cost > $X, scale > Y vectors, latency > Z ms)
7. **Self-host vs managed?** (when you have a DevOps team vs when you don't)
8. **Multi-tenant isolation?** (namespace vs metadata filter vs separate index per tenant)
9. **Backup strategy?** (export vectors to S3 nightly?)
10. **Cost at 1M, 10M, 100M vectors?** (Pinecone vs Weaviate vs Qdrant vs pgvector)

Save these answers. The vector DB choice is one of the biggest cost drivers in any RAG product.

---

## What's next

- Pair with [`../../practice/level-4-rag/`](../../practice/level-4-rag/) for RAG-specific labs
- Move to `section-7-deployment-exercises.md` for deployment patterns
- See [`../../PRACTICE-GUIDE.md`](../../PRACTICE-GUIDE.md) for the full learning path