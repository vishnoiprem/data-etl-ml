# 53. LlamaIndex

- **Role:** AI Engineer (RAG Framework / LLM Infrastructure)
- **Tech stack:** Python, TypeScript, LlamaIndex, FastAPI, vector DBs (Pinecone, Weaviate, Chroma, Qdrant), Postgres, OpenAI/Anthropic APIs, React (LlamaIndex.TS)
- **Comp band:** $180K-$380K (Series A/B, well-funded)
- **Cumulative pass rate:** ~3-5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | 30 min motivation | 1 week | ~50% advance |
| 2. **Technical phone screen** | 60-90 min coding + RAG/LLM design | 1-2 weeks | ~35% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, RAG deep-dive, behavioral | 1 day | ~30% advance |
| 4. **Hiring committee** | Panel review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Verbal + written | 1 week | — |

## Stage 1: Recruiter screen

### Q1.1: "Why LlamaIndex over LangChain?"
**Answer:** Three-bet: (1) LlamaIndex was purpose-built for RAG — the indexing abstractions (readers, parsers, retrievers, query engines, agents) are more cohesive than LangChain's, (2) Jerry Liu (CEO) is technical and accessible — the engineering culture is more "framework by RAG practitioners," (3) the data agents (LlamaAgents) are pushing toward autonomous workflows.
**Tip:** Even better: "I used both, and LlamaIndex's query engine + agent abstractions made my RAG app 30% faster to build."

### Q1.2: "Tell me about the most complex RAG app you've built"
**Answer:** Walk through a real project — be specific about the data sources, chunking strategy, retrieval approach (hybrid, reranking), eval methodology, and the failure modes you debugged.

## Stage 2: Technical phone screen

### Q2.1: Coding — "Implement a recursive text splitter"
**Answer:**
```python
def split_recursive(text, separators=["\n\n", "\n", ". ", " "], chunk_size=500):
    if len(text) <= chunk_size:
        return [text]
    for sep in separators:
        if sep in text:
            parts = text.split(sep)
            result = []
            current = ""
            for p in parts:
                candidate = (current + sep + p) if current else p
                if len(candidate) <= chunk_size:
                    current = candidate
                else:
                    if current:
                        result.append(current)
                    current = p
            if current:
                result.append(current)
            return result
    return [text[:chunk_size]]
```
**Tip:** Mention `SentenceSplitter`, `SemanticSplitter`, and `MarkdownNodeParser` — all real LlamaIndex components.

### Q2.2: LLM — "How would you build a multi-source RAG system (e.g., PDFs + Slack + Notion)?"
**Answer:** Three layers: (1) **connectors** — LlamaIndex's `SimpleDirectoryReader`, `NotionReader`, `SlackReader`, etc., (2) **standardization** — convert all sources to `Document` objects with metadata, (3) **indexing + retrieval** — unified vector index + metadata filtering, hybrid search (vector + BM25 + reranker).

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding
- **Q3.1.1:** Implement a sliding-window chunker with overlap.
- **Q3.1.2:** Build a small RAG retrieval function (cosine + top-k).
- **Q3.1.3:** Implement a simple React-style agent loop (LlamaIndex has `ReActAgent`).

### Round 3.2: System design
- **Q3.2.1:** "Design LlamaIndex's query engine architecture." Discuss: index abstraction, retriever → postprocessor → synthesizer pipeline, streaming, async, observability via `CallbackManager`.
- **Q3.2.2:** "Design a production RAG service for 10M documents." Talk: ingestion pipeline (parsers, embedders), index storage (vector DB + metadata DB), retrieval (hybrid + reranker), query engine, eval suite, observability, cost.

### Round 3.3: RAG / LLM deep-dive
- **Q3.3.1:** "How do you handle multi-hop questions in RAG?" Discuss: sub-question query engine, agentic RAG, recursive retrieval, citations.
- **Q3.3.2:** "How do you evaluate retrieval quality vs answer quality in RAG?" Talk: retrieval metrics (recall@k, MRR, nDCG), answer metrics (faithfulness, relevance), LLM-as-judge, pairwise comparison.

### Round 3.4: Behavioral
- **Q3.4.1:** "Tell me about a time you open-sourced a tool. What did you learn?"
- **Q3.4.2:** "Why RAG? Why agentic AI?"

## Stage 4: Hiring committee
LlamaIndex's committee is technical — Jerry Liu himself often participates. They look for: deep RAG experience (you should know the failure modes), strong production Python or TypeScript skills, and passion for the data-augmented LLM problem. Red flags: never having built a real RAG app, weak on chunking strategies, never having evaluated retrieval.

## Stage 5: Offer
Base is competitive ($180K-$280K), equity is the lever (private, well-funded). Negotiation: equity refreshers + sign-on.

## Tips for the LlamaIndex loop
1. **Build a real LlamaIndex app before the interview** — multi-source RAG, agentic RAG, whatever.
2. **Brute-force chunking strategies** — semantic, recursive, sentence-aware, structural.
3. **Practice the "design a production RAG service" round** — they ask it often.
4. **Be ready to compare LlamaIndex vs LangChain vs Haystack** — they'll ask.
5. **Have opinions on retrieval evaluation** — this is a daily conversation.
6. **Read the LlamaIndex blog and docs** — they publish deep technical posts.
7. **Have OSS contributions to show** — LlamaIndex is OSS-first, so a PR is huge.

## Real candidate report
> "Phone screen was RAG design + coding (recursive chunker). Onsite had 4 rounds including a 'productionize LlamaIndex for 10M docs' round that required knowing caching, async batching, observability. Offer came in 5 days, base $240K + 0.04%." — Levels.fyi, 2025

## Sources
- [LlamaIndex careers](https://www.llamaindex.ai/careers)
- [LlamaIndex blog](https://www.llamaindex.ai/blog)
- [LlamaIndex docs](https://docs.llamaindex.ai)
- [LlamaIndex GitHub](https://github.com/run-llama/llama_index)
- [LlamaIndex Glassdoor](https://www.glassdoor.com/Interview/LlamaIndex-Interview-Questions-E3509200.htm)
