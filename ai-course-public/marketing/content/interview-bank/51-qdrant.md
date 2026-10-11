# 51. Qdrant

- **Role:** Software Engineer (Vector Database / Distributed Systems)
- **Tech stack:** Rust, Python, gRPC, Kubernetes, HNSW, Product Quantization, S3-compatible storage, Prometheus, ClickHouse (for payloads)
- **Comp band:** $170K-$340K (Berlin-based, well-funded, OSS-first)
- **Cumulative pass rate:** ~3-5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | 30 min motivation | 1 week | ~50% advance |
| 2. **Technical phone screen** | 60-90 min coding + vector internals | 1-2 weeks | ~35% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, vector internals, behavioral | 1 day | ~30% advance |
| 4. **Hiring committee** | Panel review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Verbal + written | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Qdrant?"
**Answer:** Three-bet: (1) Qdrant is the only vector DB written in Rust top to bottom, so you get C-like search latency with memory safety, (2) the OSS + on-prem + Cloud model gives you deployment flexibility, (3) Andrey Vasnetsov and the founding team are still coding here, which is rare at this stage.
**Tip:** Qdrant switched from AGPL to Apache 2.0 in 2024, so mentioning that switch and what it unlocked for adoption lands well.

### Q1.2: "Tell me about your experience with vector search"
**Answer:** Walk through one concrete project. Name the dataset size, the embedding dimension, the recall target you picked, and the latency you ended up shipping. Numbers beat adjectives.

## Stage 2: Technical phone screen

### Q2.1: Coding — "Build an HNSW insert function"
**Answer:**
```rust
fn insert(graph: &mut HnswGraph, vec: Vec<f32>, m: usize) {
    let entry = random_level();
    let mut curr = graph.entry_point;
    for level in (entry..=graph.max_level).rev() {
        curr = greedy_search(graph, vec.as_slice(), curr, level);
    }
    let mut neighbors = search_neighbors(graph, vec.as_slice(), m);
    let node = graph.add_node(vec, entry, neighbors);
    for n in neighbors {
        graph.add_edge(node, n, m);
        n.prune_neighbors(m);
    }
    graph.entry_point = node; // or update if higher level
}
```
**Tip:** Qdrant's HNSW is SIMD-optimized. Discuss: AVX-512, distance kernels in registers, Cargo's release profile.

### Q2.2: Vector internals — "How does Qdrant handle filtered search?"
**Answer:** Qdrant stuffs the payload filter into the HNSW graph traversal itself, so the search skips neighbors that don't match instead of post-filtering the result set. At 100M+ vectors with selective filters, that's a 10x latency win over naive post-filtering. The trick is that HNSW has to be re-ranked with a composite score (vector distance + filter match).

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding
- **Q3.1.1:** Implement cosine similarity for batched vectors.
- **Q3.1.2:** Build a small top-k heap.
- **Q3.1.3:** Implement a sliding window percentile.

### Round 3.2: System design
- **Q3.2.1:** "Design Qdrant's sharded architecture." Discuss: consistent hashing by vector ID, replicated shards, write-ahead log, snapshot/backup, multi-tenant collection isolation.
- **Q3.2.2:** "Design a low-latency vector search service." Talk: in-memory graph cache, query routing, request coalescing, SIMD batch processing, observability.

### Round 3.3: Vector DB deep-dive
- **Q3.3.1:** "Compare HNSW vs IVF vs PQ. When would you use each in a production system?" Discuss: HNSW for high recall, IVF for memory efficiency, PQ for very large scale with quantization.
- **Q3.3.2:** "How do you optimize HNSW for high-dimensional vectors (e.g., 4096-dim embeddings)?" Talk: dimensionality reduction (PCA, OPQ), quantization (PQ, SQ), SIMD distance kernels.

### Round 3.4: Behavioral
- **Q3.4.1:** "Tell me about an OSS contribution you made."
- **Q3.4.2:** "Why vector DBs? Why Rust?"

## Stage 4: Hiring committee
Qdrant's committee is technical and European (Berlin HQ). They look for: Rust fluency, distributed systems depth, vector indexing knowledge, and OSS love. Red flags: weak on Rust, not knowing what HNSW is, no OSS contributions.

## Stage 5: Offer
Base is competitive for EU (or US remote, $200K-$300K), equity is meaningful (private, growing fast). Negotiation: equity and sign-on (Qdrant recently raised a large round).

## Tips for the Qdrant loop
1. **Be ready to code in Rust** — Qdrant's stack is Rust; even Python interview questions might touch Rust performance concepts.
2. **Brute-force HNSW internals** — graph construction, search, parameters (M, ef_construction, ef_search).
3. **Read the Qdrant engineering blog and source** — they have great deep-dives.
4. **Have a real Qdrant project** — semantic search, RAG, recommendation system.
5. **Show OSS contributions** — even docs or tests. Qdrant is OSS-first.
6. **Practice the recall vs latency tradeoff** — Qdrant engineers live in this space.
7. **Have opinions on AGPL vs Apache 2.0** — Qdrant made the switch; show you understand the implications.

## Real candidate report
> "Phone screen was 90 minutes — Rust coding (HNSW insert simplified), vector internals, and a system design round on Qdrant's sharded architecture. Onsite had 4 rounds including a Rust-specific deep dive. Offer: 180K EUR base + equity, EU benefits." — Levels.fyi, 2025

## Sources
- [Qdrant careers](https://qdrant.tech/careers/)
- [Qdrant engineering blog](https://qdrant.tech/blog)
- [Qdrant docs](https://qdrant.tech/documentation)
- [Qdrant GitHub](https://github.com/qdrant/qdrant)
- [Qdrant Glassdoor](https://www.glassdoor.com/Interview/Qdrant-Interview-Questions-E3508900.htm)
