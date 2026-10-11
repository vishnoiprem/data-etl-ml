# 36. Perplexity AI

- **Role:** AI Engineer / ML Engineer (Search, Retrieval, RAG, Inference)
- **Tech stack:** Python, PyTorch, vLLM, SGLang, Triton, CUDA, Typescript (full-stack), React, Next.js, MongoDB, Postgres, Redis
- **Comp band:** $250K-$700K (L3-L5); senior crosses $900K+; equity + cash, 4-year vest
- **Cumulative pass rate:** ~2-3%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Mission alignment, comp, fit | 1 week | ~50% advance |
| 2. **Technical phone screens (2-3)** | 1 coding + 1 ML/system | 1-2 weeks | ~35% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, ML, behavior | 1-2 days | ~30% advance |
| 4. **Founders + hiring committee** | Cross-functional review, mission fit | 1-2 weeks | ~60% advance |
| 5. **Offer** | Comp, team match | 1 week | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Why Perplexity?"
**Answer:** "Three reasons. First, Perplexity is the only AI product that has rebuilt search from scratch around LLMs — not a chatbot wrapper, but a true answer engine. Second, the team density is unmatched for a ~200-person company — ex-OpenAI, ex-Meta, ex-Google. Third, I want to ship at the frontier of agentic search."
**Tip:** Reference specific Perplexity products — *Pro Search*, *Pages*, *Focus*, *Spaces*, *Comet* (browser).

### Q1.2: "How do you stay current on AI research?"
**Answer:** Be specific — arxiv digests, Twitter follows, papers you've read, repos you've cloned. Perplexity is a research-aware company.
**Tip:** Perplexity hires people who *read papers*. Show you do.

## Stage 2: Technical phone screens (90 min)

### Q2.1: Coding: "Implement a simple RAG pipeline"
**Answer:** Chunking → embeddings → vector DB → retrieval with re-rank.
```python
def simple_rag(query, docs, embed, llm):
    chunks = chunk(docs)
    vectors = [embed(c) for c in chunks]
    q_vec = embed(query)
    top = retrieve(q_vec, vectors, k=5)
    context = "\n".join(top)
    return llm(f"Context: {context}\nQ: {query}\nA:")
```
**Tip:** Perplexity loves *build-something-real* style coding. They want to see your practical chops.

### Q2.2: ML/System: "Design Perplexity's search pipeline"
**Answer:** (1) Query understanding — decomposition, classification (factual/timeliness/opinion), query rewriting; (2) Multi-source retrieval — web (Bing + internal crawler), vector DB of indexed pages, knowledge base; (3) Re-ranking with cross-encoder; (4) LLM synthesis with citations; (5) Streaming response with token-level citations; (6) Latency budget 2-5s; (7) Eval on factual accuracy + citation quality.
**Tip:** Perplexity is the canonical RAG company. Reference *Pages*, *Focus*, *Spaces* by name.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding (60 min, 2 questions)
- Q: Implement streaming LLM output with cancellation.
- Q: Parse a complex JSON spec into a typed structure.
- Optional 3rd: Distributed-systems question on idempotency, retries, or rate limiting.

### Round 3.2: System design (60 min)
- Q: Design Perplexity's Pages product. Long-form article generation from a query, source aggregation, fact-check pipeline, publish/share flow, and version control.
- Q: Design a web-scale retrieval system. Crawling pipeline, indexing (BM25 + dense), freshness via incremental indexing, and 100K+ QPS.

### Round 3.3: ML deep-dive (60 min)
- Q: How would you improve citation accuracy in Perplexity answers? Better extractive quote selection, post-generation verification, a hallucination classifier, and eval on CiteME-style benchmarks.
- Q: How would you design a multi-modal search for Perplexity? Image + text query, OCR pipeline, visual encoder, and multi-modal embeddings.

### Round 3.4: Behavioral (60 min)
- Q: Why this mission, making knowledge accessible? Perplexity hires on mission alignment.
- Q: A time you shipped a product at startup speed.
- Q: Disagreement with a co-founder or PM.

## Stage 4: Founders + hiring committee
Perplexity has a tight culture. A committee of senior engineers + sometimes a founder (Aravind, Denis, Johnny) reviews. They look for: (1) technical bar, (2) mission alignment ("knowledge is power"), (3) shipping speed, (4) humble intensity. Perplexity is *small* — every hire matters.

## Stage 5: Offer
Cash + RSUs. Perplexity has grown comp aggressively through 2024-2025. Negotiation is real and the founders have authority. Team match after loop. SF HQ is main hub.

## Tips for the Perplexity loop
- Read Aravind's essays and follow the team's Twitter — mission alignment matters.
- For ML rounds, RAG depth is critical — show you've built RAG systems end-to-end.
- For system design, retrieval + citation + streaming are the trifecta.
- Show you've read recent papers (DeepSeek-R1, RAG surveys, agent benchmarks).
- Perplexity culture is "ship and learn" — be ready to discuss fast iteration.
- Reference specific products — *Pro Search*, *Pages*, *Focus*, *Spaces*, *Comet* browser.
- Quantify scale: "500M+ queries/month", "10K QPS", "sub-2s latency".

## Real candidate report
> "Loop for Search/RAG team. 4 rounds in 1 day, all in-person at SF. The coding round was a simple RAG implementation. The ML round was on citation accuracy and they wanted me to discuss extractive quote selection and post-hoc verification. The system design was on Pages (article generation). Founders round was 'mission fit' flavored. Offer at L4, ~$520K total, 3 weeks." — Blind, 2025-10

## Sources
- [Perplexity Careers](https://www.perplexity.ai/careers)
- [Levels.fyi Perplexity salaries](https://www.levels.fyi/companies/perplexity-ai/salaries)
- [Perplexity blog](https://blog.perplexity.ai/)
- [Aravind Srinivas Twitter](https://twitter.com/AravSrinivas)
- [r/MachineLearning Perplexity thread](https://www.reddit.com/r/MachineLearning/)
