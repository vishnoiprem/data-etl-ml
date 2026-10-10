# 50. Chroma

- **Role:** Software Engineer (Vector Database / RAG Tooling)
- **Tech stack:** Python, Rust, TypeScript, FastAPI, ClickHouse, DuckDB, HNSW, SQLite, Postgres
- **Comp band:** $180K-$380K (small team, high equity, post-Series A/B)
- **Cumulative pass rate:** ~3-5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | 30 min motivation | 1 week | ~50% advance |
| 2. **Technical phone screen** | 60 min coding + vector DB | 1-2 weeks | ~40% advance |
| 3. **Onsite (3-4 rounds)** | Coding, system design, ML/RAG, founder | 1 day | ~30% advance |
| 4. **Hiring committee** | Panel review | 1 week | ~60% advance |
| 5. **Offer** | Verbal + written | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Why Chroma?"
**Answer:** Three-bet: (1) Chroma is the most popular Python-native vector DB — the developer experience is unmatched for RAG use cases, (2) Jeff Huber (ex-Hub, ex-Cohere) + Anton Troynikov (co-author of Chroma) are pushing toward becoming the SQLite of vector search (embedded + serverless), (3) the new Rust core (`chroma-rs`) makes it production-grade.
**Tip:** Chroma competes with FAISS for the prototype/small-scale use case. Mention you've used Chroma + LangChain or LlamaIndex.

### Q1.2: "Tell me about a RAG project you built"
**Answer:** Walk through a concrete project: e.g., built a doc Q&A system using Chroma + OpenAI embeddings + a frontend. Mention the failure modes (chunking, retrieval quality) and how you fixed them.

## Stage 2: Technical phone screen

### Q2.1: Coding — "Implement a sliding-window chunker for documents"
**Answer:**
```python
def chunk(text, window=500, overlap=50):
    chunks = []
    i = 0
    while i < len(text):
        chunk_end = min(i + window, len(text))
        chunks.append(text[i:chunk_end])
        i += window - overlap
    return chunks
```
**Tip:** Better chunkers: sentence-aware, semantic (use embedding similarity between sentences to detect boundaries), or recursive (Markdown structure). Chroma supports all of these via its `langchain-chroma` integration.

### Q2.2: Vector DB — "How would you evaluate retrieval quality in a RAG system?"
**Answer:** Three pillars: (1) **retrieval metrics** — recall@k, MRR (mean reciprocal rank), nDCG, (2) **end-to-end metrics** — answer relevance (LLM-as-judge), faithfulness (no hallucination), (3) **human eval** — domain expert review. Chroma integrates with Ragas, TruLens, and Phoenix.

## Stage 3: Onsite (3-4 rounds)

### Round 3.1: Coding
- **Q3.1.1:** Implement a top-k cosine similarity.
- **Q3.1.2:** Build a small LRU cache.
- **Q3.1.3:** Parse a JSON config and validate it.

### Round 3.2: System design
- **Q3.2.1:** "Design Chroma's hybrid in-process + server mode." Discuss: client library (`chromadb`), local mode (SQLite + DuckDB), server mode (ClickHouse), async workers, copy-on-write data structures.
- **Q3.2.2:** "Design a multi-tenant RAG service." Talk: per-tenant collection isolation, query quotas, embedding model caching, prefix caching, observability.

### Round 3.3: RAG / ML deep-dive
- **Q3.3.1:** "How do you choose chunk size and overlap for a RAG system?" Discuss: tradeoff between granularity (small chunks) and context (large chunks). Pro tip: evaluate on your eval set; Chroma has tooling for this.
- **Q3.3.2:** "How do you handle multi-modal RAG (text + images)?" Talk: CLIP embeddings, hybrid index, layout-aware chunking, multi-vector search.

### Round 3.4: Founder/behavioral
- **Q3.4.1:** "Tell me about a tool you built that other developers loved."
- **Q3.4.2:** "Why RAG? What's the next 2 years of vector DBs look like?"

## Stage 4: Hiring committee
Chroma is small (~50 people), tight loop. The committee is the founders + 1-2 senior engs. They look for: production Python or Rust chops, RAG/ML practitioner credibility, and DX obsession. Red flags: never having built a RAG app, weak on embeddings/vector search basics.

## Stage 5: Offer
Base is competitive for the size ($180K-$280K), equity is the lever — Chroma is private, early-mid stage, so equity has real upside. Negotiation: equity grants.

## Tips for the Chroma loop
1. **Build a real Chroma project before the interview** — RAG app, semantic search, etc.
2. **Brute-force vector search fundamentals** — HNSW, cosine, recall@k.
3. **Have opinions on RAG frameworks** — LangChain, LlamaIndex, Haystack, etc. Chroma competes with the embedding store layer.
4. **Show fluency in Python + Rust** — Chroma is moving toward Rust core for performance.
5. **Be ready for a founder round** — Jeff Huber and Anton are technical and ask deep questions.
6. **Read the Chroma blog** — they publish architecture and product posts.
7. **Have an OSS contribution** to a related project.

## Real candidate report
> "Phone screen was RAG internals (chunking, retrieval eval) + coding. Onsite had a 'design a multi-tenant RAG service' round that was tricky. Founder round asked me to design the next 2 years of vector DBs. Offer: $220K + 0.05% equity, 4 days." — Levels.fyi, 2025

## Sources
- [Chroma careers](https://www.trychroma.com/careers)
- [Chroma docs](https://docs.trychroma.com)
- [Chroma blog](https://www.trychroma.com/blog)
- [Chroma GitHub](https://github.com/chroma-core/chroma)
- [Chroma Glassdoor](https://www.glassdoor.com/Interview/Chroma-Interview-Questions-E3508800.htm)
