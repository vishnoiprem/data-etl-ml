# GenAI Sub-Lesson 2 — RAG Patterns (the canonical FDE GenAI primer)

> **RAG (Retrieval-Augmented Generation) is the canonical FDE GenAI pattern.** 80% of FDE GenAI systems at AI companies are RAG systems (Anthropic, OpenAI, Sierra, LangChain, Databricks, Google, Microsoft). The FDE signal: a candidate who can explain **BM25 + dense + RRF + hybrid retrieval + reranking + the eval set as the regression check** — is signaling they can ship a GenAI system that doesn't hallucinate.

---

## Why RAG is the FDE signal

The 4 things the interviewer is testing:

1. **Can you explain why RAG exists?** The candidate who can say "LLMs hallucinate; RAG grounds them in real data; the eval set is the contract" is signaling they understand the hallucination problem.
2. **Can you pick the right retriever?** BM25 (keyword), dense (semantic), hybrid (BM25 + dense + RRF). The candidate who names the **hybrid retriever with RRF fusion** is signaling they understand the retrieval problem.
3. **Can you name the chunking strategy?** The candidate who can say "chunk size 256-512 tokens, 10-20% overlap, hierarchical for long docs, table-aware for tables" is signaling they understand the chunking problem.
4. **Can you name the eval metrics?** RAGAS: faithfulness, answer relevance, context precision, context recall. The candidate who names the 4 metrics is signaling they can ship a RAG system.

**The FDE pattern:** explain the hallucination problem + name the hybrid retriever + name the chunking strategy + name the eval metrics. The depth of the answer matches the depth of the FDE role.

---

## The 4 sections of the canonical RAG answer

### Section 1: Why RAG exists (60 seconds)

**The hallucination problem:**

- LLMs generate plausible-sounding but factually wrong text. The cause: the model interpolates between training-data points, but it doesn't know what it doesn't know.
- RAG grounds the model in **real, retrieved documents** — the model generates text that is anchored to actual sources, not to its parametric memory.
- The eval set is the contract: the candidate who can say "the eval set is the regression check; if the RAG system fails on a query, the eval set catches it" is signaling they operate a RAG system.

**The 3 alternatives to RAG (and when to use them):**

1. **Long context.** Stuff all the documents into the prompt. Works for < 128K tokens, expensive, slow.
2. **Fine-tuning.** Train the model on the documents. Works for stable, large corpora; doesn't update in real-time; expensive.
3. **Tool use.** Let the model call a search tool. Works for web search; less reliable for enterprise data.

**The pattern:** RAG is the default. Long context is the fallback. Fine-tuning is the optimization. Tool use is the complement.

---

### Section 2: The hybrid retriever (90 seconds)

**The 3 retrieval methods:**

1. **BM25 (keyword).** Lexical search. Fast, deterministic, good for exact-match queries (SKU, ID, name). Misses paraphrases.
2. **Dense (semantic).** Embed the query and the documents; retrieve by cosine similarity. Good for paraphrases; misses exact-match. Slow + expensive.
3. **Hybrid (BM25 + dense + RRF).** Run both retrievers; fuse the rankings with **Reciprocal Rank Fusion** (RRF). Best of both worlds: exact-match AND paraphrase. **This is the production default.**

**Reciprocal Rank Fusion (RRF), in 2 sentences:**

For each query, the BM25 retriever returns a ranked list of documents; the dense retriever returns a ranked list. RRF computes a score for each document as `sum(1 / (k + rank_in_list))` across both lists, then re-ranks. Documents that appear high in both lists win. `k` is a smoothing constant (typically 60).

**The 2 things to add for depth:**

1. **Reranking.** After the hybrid retriever, run a cross-encoder reranker (e.g., `bge-reranker-large`, `cohere-rerank-3`) on the top-20 to re-rank to top-5. The cross-encoder is more accurate but slower; it's worth it for the final cut.
2. **Metadata filtering.** Filter by date, source, ACL, etc. before retrieval. The candidate who names metadata filtering is signaling they understand enterprise RAG.

---

### Section 3: Chunking (60 seconds)

**The 4 chunking strategies:**

1. **Fixed-size chunks (256-512 tokens, 10-20% overlap).** The default. Works for prose. Loses structure for tables, code, headers.
2. **Hierarchical chunks (parent + child).** Chunk into small children (256 tokens) for retrieval, but return the parent (1024 tokens) for context. Works for long docs.
3. **Semantic chunks.** Split on semantic boundaries (sentence, paragraph, section). Better than fixed for prose; slower.
4. **Structure-aware chunks (markdown, HTML, tables).** For tables, serialize as row-wise with headers repeated. For code, split on function/class boundaries. For markdown, split on headers.

**The 3 chunking failure modes:**

1. **Chunking severs clauses from defined terms.** "The Agreement" appears in chunk 1, but "The Agreement means..." appears in chunk 2. The retriever can't connect them. **Fix:** semantic chunks, or include the section header in every chunk.
2. **Tables are chunked as prose.** The table's structure is lost. **Fix:** serialize tables as CSV or markdown, with headers repeated.
3. **Version confusion.** Three versions of the same doc exist; the retriever returns the wrong one. **Fix:** metadata filter on `version` or `date`.

---

### Section 4: The RAGAS eval (60 seconds)

**The 4 RAGAS metrics:**

1. **Faithfulness.** Is the answer grounded in the retrieved context? (no hallucination)
2. **Answer relevance.** Is the answer relevant to the query? (no off-topic)
3. **Context precision.** Are the retrieved chunks relevant? (retriever quality)
4. **Context recall.** Did we retrieve all the relevant chunks? (retriever coverage)

**The 2 things to add for depth:**

1. **LLM-as-judge.** Use a strong LLM (GPT-4o, Claude Sonnet) to grade the 4 metrics. Calibrate against human grades on 50 examples before trusting.
2. **Slice reporting.** Don't report aggregate metrics. Report by query type (factual, comparison, multi-hop). Aggregate 91% can hide a 60% slice.

**The pattern:** the eval set is the regression check. If the metric drops > 5%, the eval catches it. The eval set is the spec.

---

## The 5 most common RAG questions

| Question | The FDE answer (60 sec) |
|---|---|
| 1. "How do you prevent hallucination?" | "RAG with citations. Confidence-based routing. The eval-set-as-spec regression check. Force 'I don't know' as a valid response. Reduce temperature for high-stakes queries." |
| 2. "BM25 vs dense vs hybrid?" | "BM25 is fast + good for exact-match; dense is good for paraphrases. Hybrid (BM25 + dense + RRF) is the production default. Add a cross-encoder reranker for the final cut." |
| 3. "How do you chunk a long document?" | "Hierarchical: small children (256 tokens) for retrieval, large parents (1024 tokens) for context. For tables, serialize row-wise with headers repeated. For code, split on function boundaries." |
| 4. "What if the retrieval returns nothing relevant?" | "Force 'I don't know' as a valid response. Threshold the retrieval score; if no chunk is above the threshold, return a fallback. Add a hybrid retriever to catch paraphrases the keyword retriever misses." |
| 5. "How do you evaluate RAG?" | "RAGAS: faithfulness, answer relevance, context precision, context recall. LLM-as-judge, calibrated against human grades. Report by slice, not aggregate. The eval set is the regression check." |

---

## The 5 anti-patterns for RAG

1. **Skipping the hybrid retriever.** Dense-only misses exact-match; BM25-only misses paraphrases. The candidate who doesn't name the hybrid is signaling they don't understand retrieval.
2. **Skipping the reranker.** Hybrid + reranker is the production default. The candidate who doesn't name the reranker is signaling they don't operate a RAG system at scale.
3. **Skipping the chunking story.** The candidate who doesn't mention **chunk size + overlap + table-aware + hierarchical** is signaling they haven't shipped a RAG system.
4. **Skipping the citations.** The candidate who doesn't name **citations in every response** is signaling they don't think about hallucination.
5. **Skipping the eval set.** The candidate who doesn't name **RAGAS + LLM-as-judge + slice reporting + the eval set as the spec** is signaling they don't ship a RAG system.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "How do you handle multi-hop queries?" | "Decompose the query into sub-queries. Retrieve for each sub-query. Combine the results. The cross-encoder reranker helps. The eval set should include multi-hop queries." |
| 2. "How do you scale RAG to 10M documents?" | "Hierarchical navigable small worlds (HNSW) for vector search. Shard the index. Pre-filter by metadata. Quantize the embeddings. The retrieval is O(log N) per query, not O(N)." |
| 3. "How do you update the index in real-time?" | "Incremental indexing: when a doc is added/updated, compute the embedding and add to the index. Use a write-through cache for hot docs. The eval set should include freshness queries." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../system-design/09-agentic-ai.md` | The agent architecture that uses RAG for grounding |
| `../company-experiences/databricks-ai-fde.md` | The RAG-over-enterprise-data-lake signature question |
| `../company-experiences/google-ai-engineer.md` | The Vertex AI + BigQuery grounding pattern |

---

## The thesis

**RAG is the canonical FDE GenAI pattern.** The candidate who names **hybrid retriever (BM25 + dense + RRF) + cross-encoder reranker + hierarchical chunking + RAGAS eval + the eval set as the spec** — is signaling they can ship a GenAI system that doesn't hallucinate.

**The 4-section answer (why RAG, hybrid retriever, chunking, eval) is the muscle memory.** The 5 questions are the practice bank. The 5 anti-patterns are the disqualifiers.

**General prep gets you past the resume screen. RAG prep gets you past the GenAI depth round at Anthropic, OpenAI, Sierra AI, LangChain, Databricks, Google, and Microsoft.**
