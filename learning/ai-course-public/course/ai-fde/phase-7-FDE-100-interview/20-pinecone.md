# Pinecone — Enterprise FDE

## Company Snapshot
- **HQ**: New York, NY
- **Team Size**: ~30–60
- **Comp**: $170K–$220K; TC $260K–$420K
- **What they deploy**: Vector DB enterprise FDEs (Pinecone Serverless / Dedicated)
- **Travel**: 15–30%

## Interview Process
1. Recruiter
2. Coding + Python
3. ML/RAG design
4. Loop — coding, vector search design, customer scenario

---

## ✅ SUCCESS STORIES

### Vector search design
**Q:** *"Design a 100M-vector search at p95 < 50ms."*
**A (winner):** *"Pinecone Serverless with pod-size tuning + sparse-dense hybrid. Pre-filter by metadata before vector recall. Use pod-type p2.x1 with replicas=4 for read parallelism. Cooldown via async upserts. Add a re-rank step (Cohere Rerank) on top-K=100 for recall quality. Cache top-K per session. Eval: ann-benchmarks + custom latency harness."*
**Why it worked:** Pinecone-native (pods, serverless, replicas), addressed latency, hybrid retrieval.

---

## ❌ REJECTION STORIES
### Vector design
**Q:** *"Which vector DB?"*
**A (loser):** Generic comparison without naming Pinecone primitives.
**What they should have said:** Discuss Pinecone-specific trade-offs: serverless vs dedicated, p1/p2 pod sizes, metadata filtering efficiency, hybrid sparse-dense.

---

## 📚 Reading List
1. Pinecone docs
2. HNSW / ScaNN papers
3. ann-benchmarks
4. RAGAS eval
5. levels.fyi Pinecone
