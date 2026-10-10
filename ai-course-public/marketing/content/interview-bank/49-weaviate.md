# 49. Weaviate

- **Role:** Software Engineer (Vector Database / Distributed Systems)
- **Tech stack:** Go, Python, GraphQL, gRPC, Kubernetes, HNSW, IVF, Product Quantization, S3-compatible storage, Prometheus, Jaeger
- **Comp band:** $180K-$360K (Series C, well-funded, OSS-first)
- **Cumulative pass rate:** ~3-5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | 30 min motivation | 1 week | ~50% advance |
| 2. **Technical phone screen** | 60 min coding + vector DB | 1-2 weeks | ~40% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, vector internals, behavioral | 1 day | ~30% advance |
| 4. **Hiring committee** | Panel review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Verbal + written | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Weaviate over Pinecone or Qdrant?"
**Answer:** Three-bet: (1) Weaviate is OSS-first (you can self-host), so the engineering culture is more transparent, (2) Weaviate's modular vector indexing (plug any algorithm) is more flexible than Pinecone's managed-only, (3) the GraphQL API + generative search modules are a real differentiator.
**Tip:** Weaviate is European HQ'd (Amsterdam). Mention if you have EU experience or interest — they like diversity of background.

### Q1.2: "Tell me about your experience with vector search"
**Answer:** Walk through a concrete project: e.g., built a semantic search over a corpus, hit scaling issues, switched from FAISS to Weaviate for distributed support.

## Stage 2: Technical phone screen

### Q2.1: Coding — "Implement approximate nearest neighbors using LSH"
**Answer:**
```python
import numpy as np
class LSH:
    def __init__(self, dim, n_tables=5, n_bits=10):
        self.tables = []
        for _ in range(n_tables):
            self.tables.append(np.random.randn(n_bits, dim))
    def hash_(self, v):
        return [tuple(np.sign(t @ v) > 0) for t in self.tables]
    def insert(self, id, v):
        for table, h in zip(self.tables, self.hash_(v)):
            table.setdefault(h, []).append((id, v))
    def query(self, v, k=10):
        cands = set()
        for h, table in zip(self.hash_(v), self.tables):
            for id, vec in table.get(h, []):
                cands.add((id, vec))
        return sorted(cands, key=lambda x: -np.dot(x[1], v))[:k]
```
**Tip:** Weaviate supports multiple algorithms — HNSW is default, but they support ANNOY, PQ, and IVF too.

### Q2.2: Vector DB — "How would you benchmark recall vs latency in a vector DB?"
**Answer:** Three pillars: (1) **ground truth**: brute-force k-NN, (2) **recall@k**: % of true top-k in approximate top-k, (3) **latency**: p50/p95/p99 with concurrency sweeps. ANN-Benchmarks is the standard.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding
- **Q3.1.1:** Implement cosine similarity (numpy).
- **Q3.1.2:** Build a small top-k heap.
- **Q3.1.3:** Parse a JSON schema and validate it.

### Round 3.2: System design
- **Q3.2.1:** "Design Weaviate's sharded vector index." Discuss: consistent hashing by vector ID, replicated shards, query fan-out, tenant isolation, hot shards.
- **Q3.2.2:** "Design a hybrid search system (BM25 + vector)." Talk: query rewriting, score fusion (linear combination vs reciprocal rank fusion), index alignment, re-ranking with cross-encoder.

### Round 3.3: Vector DB deep-dive
- **Q3.3.1:** "How does HNSW handle concurrent inserts?" Discuss: lock-free graph (atomic CAS), epoch-based reclamation, multi-threaded search, replication for read scaling.
- **Q3.3.2:** "Compare HNSW vs IVF vs PQ in terms of memory, recall, build time, query latency." Tradeoffs: HNSW high recall, high memory; IVF balanced; PQ low memory, lower recall.

### Round 3.4: Behavioral
- **Q3.4.1:** "Tell me about an OSS project you contributed to."
- **Q3.4.2:** "Why vector DBs? Why open source?"

## Stage 4: Hiring committee
Weaviate is OSS-first, so the committee values: open-source contributions, technical depth on vector indexing, and a real passion for the "semantic search" problem. Red flags: not knowing what product quantization is, never having used Weaviate.

## Stage 5: Offer
Base is competitive for EU ($150K-$250K EUR-equivalent, or US $200K-$300K), equity is meaningful (private, growing). Negotiation: equity refreshers + the EU-style benefits (28 days PTO, etc.).

## Tips for the Weaviate loop
1. **Use Weaviate Cloud before the interview** — spin up a cluster, import some data, run searches.
2. **Contribute a small PR to Weaviate** — even docs. Huge positive signal.
3. **Brute-force HNSW internals** — graph construction, search algorithm, parameter tuning.
4. **Practice hybrid search (BM25 + vector)** — Weaviate's generative search modules are a hot area.
5. **Have opinions on OSS vs source-available vector DBs** — Qdrant went AGPL, Weaviate stayed BSL, etc.
6. **Read Weaviate's blog and Bob van Luijt's posts** — the CEO is technical and public.
7. **Show fluency in Go** — most of Weaviate's core is Go.

## Real candidate report
> "Phone screen was HNSW internals + coding. Onsite 4 rounds including 'design a hybrid search system' that was hard — they really pushed on the recall/latency tradeoff. Offer came in 5 days. Equity grant was higher than expected (0.05%+)." — Levels.fyi anonymous, 2025

## Sources
- [Weaviate careers](https://weaviate.io/careers)
- [Weaviate engineering blog](https://weaviate.io/blog)
- [Weaviate docs](https://weaviate.io/developers/weaviate)
- [Weaviate GitHub](https://github.com/weaviate/weaviate)
- [Weaviate Glassdoor](https://www.glassdoor.com/Interview/Weaviate-Interview-Questions-E3507900.htm)
