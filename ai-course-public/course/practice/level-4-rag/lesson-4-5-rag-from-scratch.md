# Lesson 4.5: Building RAG from Scratch

> **The 100-line pattern that powers every AI product you've ever used.**
> 45-60 min. Code-heavy. No frameworks — just `numpy` and `openai`.

## 🎯 Architect Level

- [ ] 🟢 **Junior (1-2 yrs)** — implement and run
- [ ] 🟡 **Mid (3-5 yrs)** — extend with monitoring
- [ ] 🟠 **Senior (6-10 yrs)** — add multi-tenancy
- [ ] 🔴 **Staff (10+ yrs)** — design the SLA, capacity model, incident playbook

---

## 🧠 Concept (5 min)

**RAG (Retrieval-Augmented Generation)** is three steps:

1. **Embed** your documents into vectors (numerical representations of meaning).
2. **Retrieve** the most similar documents to a user's question (by vector distance).
3. **Generate** an answer using the LLM with the retrieved documents as context.

That's it. The whole pattern is ~100 lines of Python.

Why does it work? Because **embeddings capture meaning**. The vector for "king" minus the vector for "man" plus the vector for "woman" is close to the vector for "queen". This means a search for "how do I cancel my subscription" can find the doc titled "Termination Policy" even though they share zero words.

The architect's mental model:
- **Embeddings are lossy.** They capture meaning, not exact wording. If the user searches for a specific SKU, RAG will fail. Use keyword search (BM25) alongside.
- **Chunking is the secret sauce.** Bad chunks → bad retrieval → bad answers. Most RAG failures are chunking failures.
- **Context window is your budget.** You can fit ~3-5 chunks in a 4K-token context. Choose wisely.

Three things you must know before you build:
- **Cosine similarity** is the standard distance metric for text embeddings. Range: -1 to 1 (in practice: 0 to 1).
- **Top-k retrieval**: retrieve the k most similar chunks (usually k=3-10). More is not better — long contexts degrade LLM performance.
- **Re-ranking**: an optional second pass with a cross-encoder model. Adds latency, improves quality.

---

## 🛠️ Build It (45 min)

### Spec

Build a complete RAG system in **one Python file**, no frameworks. The system must:

1. Take a list of 10+ documents (any topic)
2. Embed them all on startup using OpenAI's `text-embedding-3-small`
3. Take a user's question
4. Return the top 3 most similar documents
5. Pass those documents to `gpt-4o-mini` as context
6. Return the LLM's answer
7. Print the retrieved documents with their similarity scores

### Acceptance Criteria

**Functional:**
- [ ] Runs with `python lesson-4-5-rag-from-scratch.py`
- [ ] No LangChain, no LlamaIndex, no frameworks — only `openai` and `numpy`
- [ ] Returns a coherent answer to "What is [topic]?"
- [ ] Prints similarity scores for each retrieved doc
- [ ] Uses `text-embedding-3-small` (1536-dim) and `gpt-4o-mini`

**Quality:**
- [ ] All functions have docstrings
- [ ] Type hints on all function signatures
- [ ] No magic numbers — use named constants
- [ ] Single class or set of functions; not 500 lines of code

**Observability (Mid+):**
- [ ] Print token usage for the embedding + generation calls
- [ ] Print total wall-clock time
- [ ] Log the retrieved documents (id + score) for debugging
- [ ] For Senior+: log estimated cost per query

### Starter Code

Open `lesson-4-5-rag-from-scratch.py` in the same folder. It has a `TODO` per step.

### Solution

The same `.py` file has the complete solution after the `# === SOLUTION ===` divider. The full implementation is ~80 lines.

---

## 🏛️ Architect Notes

### Trade-offs

| Approach | Pros | Cons | Pick when |
|---|---|---|---|
| **RAG (this lab)** | Always up-to-date, low cost, no training | Limited by retrieval quality, doesn't learn | Most cases (docs, Q&A, support) |
| Fine-tuning | Learns domain knowledge, faster inference | Expensive, slow to update, needs 100s of examples | Repeated patterns, specific style |
| Long context (200K) | No retrieval needed | Expensive ($5/query at 200K), slow, lost-in-the-middle | Small doc collections (<100 docs) |
| Hybrid (RAG + keyword) | Best of both | More moving parts | Production-grade Q&A |

**Architect insight:** RAG is the default. Add fine-tuning only when retrieval fails 50%+ of the time despite good chunking and re-ranking. Use long context only when your doc set is small enough to fit.

### Capacity Model

| Volume | Embeddings latency | Retrieval latency | LLM latency | Total p99 |
|---|---|---|---|---|
| 100 docs | 2-3 sec (one-time) | <1 ms | 1-2 sec | ~3 sec (first query), ~2 sec (subsequent) |
| 10K docs | 5-10 min (one-time) | <10 ms | 1-2 sec | ~2 sec |
| 1M docs | 8-15 hours (one-time) | 50-200 ms | 1-2 sec | ~2.5 sec |
| 100M docs | Days (one-time, parallel) | 100-500 ms (needs HNSW + GPU) | 1-2 sec | ~3 sec |

**Rule of thumb:** For <100K docs, in-memory `numpy` is fine. For 1M+ docs, use a vector database (Pinecone, Weaviate, Qdrant) with HNSW index.

### Cost Model (per 1K queries, 2026)

Assume: avg 3 retrieved chunks, 1K token context, 200 token answer.

| Component | Cost per 1K queries |
|---|---|
| Embeddings (query side, 1K queries × 50 tokens) | $0.01 |
| Vector search (in-memory or DB) | $0 (compute only) |
| LLM: GPT-4o-mini (1K input + 200 output tokens × 1K queries) | $0.27 |
| LLM: GPT-4o (1K input + 200 output tokens × 1K queries) | $9.50 |
| LLM: Claude 3.5 Sonnet | $6.30 |

**At 1M queries/day with GPT-4o-mini: $280/day = $8,400/month** in LLM cost alone. This is the dominant cost.

### When NOT to use this lab's content

**Don't use RAG for:**
- Real-time data (stock prices, weather) — RAG is for static knowledge. Use tools/functions instead.
- Exact-match lookups (order by ID, get user by email) — RAG is fuzzy. Use SQL.
- Tasks where the LLM already knows the answer (general knowledge) — RAG adds cost and latency with no quality gain.

**When RAG fails:**
- User searches for a specific code (e.g., "find my order #12345") — use keyword search, not RAG.
- User asks about events after the doc was written — your docs are stale. RAG can't help.
- User asks something not in your docs — RAG hallucinates confidently. You need a "I don't know" guardrail.

### Production Checklist

- [ ] Embedding model is pinned (don't switch without re-embedding everything)
- [ ] Documents are chunked (typically 200-1000 tokens, 10-20% overlap)
- [ ] Each chunk has metadata: source, timestamp, author, doc_id
- [ ] Retrieval uses both vector AND keyword search (hybrid)
- [ ] Top-k is bounded (3-10 chunks, not 50)
- [ ] LLM context is sized correctly (don't send 100K tokens if you only need 2K)
- [ ] Eval set exists (50+ Q&A pairs) and is run on every change
- [ ] RAGAS or similar measures faithfulness, relevance, context precision
- [ ] Caching layer for repeated queries
- [ ] Rate limits per user
- [ ] "I don't know" response when retrieval confidence is low

---

## 🌙 Reflect (10 min)

1. **What did I build?**
   A RAG system. What surprised you about how easy the core pattern is?

2. **What was hard?**
   Was the cosine similarity? The prompt engineering for the generation step? The chunking decision?

3. **What would I change at 10× scale?**
   If you had 1M documents instead of 10, what breaks? (Hint: in-memory numpy, embedding latency at ingest, retrieval precision.)

4. **What's tomorrow's lab?**
   Lesson 4.6: LangChain RAG. You'll do the same thing in 30 lines using a framework. Then decide: framework or roll your own?

---

## References

- [Codebook § 4.1](../../workbooks/ai-engineer-codebook.md#41-simple-rag-no-frameworks) — the same pattern in 50 lines
- [Codebook § 4.2](../../workbooks/ai-engineer-codebook.md#42-langchain-rag) — same in LangChain
- [Codebook § 4.5](../../workbooks/ai-engineer-codebook.md#45-rag-evaluation-with-ragas) — eval with RAGAS
- [Lesson script for 3.2](../../scripts/lesson-3-2-rag-script.md) — full 28-min video script
- [RAGAS docs](https://docs.ragas.io/) — evaluation framework
- [Pinecone learning center](https://www.pinecone.io/learn/) — vector database fundamentals
