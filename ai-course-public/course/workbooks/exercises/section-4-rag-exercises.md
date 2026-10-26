# Codebook Exercises — Section 4: RAG Patterns

> **Paired exercises for [`../ai-engineer-codebook.md` § 4](../ai-engineer-codebook.md#section-4-rag-patterns).**
> These turn reference snippets into active practice. For each reference snippet in the codebook, here are 3-5 challenges that force you to modify, extend, and break the code.

---

## How to use these

1. Open the reference snippet in [`../ai-engineer-codebook.md`](../ai-engineer-codebook.md) — Section 4 (RAG)
2. Read the snippet once
3. Do the exercises below IN ORDER — each builds on the previous
4. For each exercise, build the RAG component, run it, note what you learned

**Time per exercise:** 20-30 min.
**Total time for this section:** 5-7 hours.

---

## Snippet 4.1 — Simple RAG (No Frameworks)

**Reference:** [`../ai-engineer-codebook.md#41-simple-rag-no-frameworks`](../ai-engineer-codebook.md#41-simple-rag-no-frameworks)

### Exercise 4.1.1: Add a system prompt to constrain answers

```python
# TODO: Modify the simple RAG so the model can ONLY answer from the retrieved chunks.
# System prompt: "Use ONLY the context below. If the answer is not in the context, say 'I don't know based on the provided documents.'"
# Test: ask a question NOT covered by the docs. Verify it says "I don't know" instead of hallucinating.
```

### Exercise 4.1.2: Citation enforcement

```python
# TODO: Force the model to cite sources as [1], [2], etc.
# After generating, parse the citations and look up the source chunks.
# Return: {answer, citations: [{chunk_id, doc_id, page, text}]}
# This is what real products show to users.
```

### Exercise 4.1.3: Re-ranking

```python
# TODO: Retrieve top-20 chunks from vector search.
# Then re-rank with a cross-encoder (e.g., sentence-transformers cross-encoder).
# Keep top-5.
# Measure: does re-ranking improve answer quality on your eval set?
# Cost: 1 cross-encoder call per query = ~5ms for 20 pairs.
```

### Exercise 4.1.4: Hybrid search

```python
# TODO: Combine vector search (semantic) with BM25 (keyword).
# Vector finds "Apple the company", BM25 finds "Apple the fruit" if you typed "apple".
# Reciprocal rank fusion to merge the two result lists.
# Measure: does hybrid outperform either alone?
```

---

## Snippet 4.2 — LangChain RAG

### Exercise 4.2.1: Compare LangChain vs raw RAG

```python
# TODO: Build the same RAG in two ways:
# 1. Raw: openai + pinecone + custom code
# 2. LangChain: RetrievalQA chain
# Compare: code size, control, debug-ability, performance.
# When is LangChain worth the abstraction?
```

### Exercise 4.2.2: Conversational RAG

```python
# TODO: Add multi-turn conversation memory.
# - Re-write the question with chat history before retrieving
# - Use ConversationalRetrievalChain
# - Or roll your own with a follow-up question rewriter
# Test: "What about their pricing?" (after asking about Stripe)
```

### Exercise 4.2.3: Streaming RAG

```python
# TODO: Stream the LLM response token-by-token after retrieval.
# - Retrieve first (blocks until done)
# - Then stream the generation
# Measure: does streaming improve perceived latency?
```

---

## Snippet 4.3 — Advanced Chunking Strategies

**Reference:** [`../ai-engineer-codebook.md#43-advanced-chunking-strategies`](../ai-engineer-codebook.md#43-advanced-chunking-strategies)

### Exercise 4.3.1: Compare chunk sizes

```python
CHUNK_SIZES = [200, 500, 1000, 2000]
# TODO: Chunk the same docs at 4 sizes, embed each, build 4 indices.
# Run 50 questions. Measure:
# - retrieval precision (top-k contains the right chunk?)
# - answer accuracy (does the LLM get it right?)
# - cost (more chunks = more embeddings = more $)
# - latency (more chunks = bigger prompt = slower LLM)
# Plot accuracy vs chunk size.
```

### Exercise 4.3.2: Semantic chunking

```python
# TODO: Instead of fixed-token chunking, split at natural boundaries:
# - Use embeddings to find "semantic breakpoints" (where topic changes)
# - Or use a model to detect section boundaries (e.g., LlamaIndex's SemanticSplitter)
# Compare: does semantic chunking beat fixed-size?
```

### Exercise 4.3.3: Document-aware chunking

```python
# TODO: Use document structure:
# - Markdown: split on ## / ###
# - HTML: split on <h1>, <h2>
# - Code: split on function / class boundaries (tree-sitter)
# - PDF: split on page + section heading (PyMuPDF)
# Each chunk should be self-contained.
```

### Exercise 4.3.4: Parent-document retrieval

```python
# TODO: Embed small chunks (for precision) but return parent chunks (for context).
# Store: small_chunks → parent_chunk_id
# On retrieval: get top-k small_chunks, look up parents, deduplicate
# Best of both worlds.
```

---

## Snippet 4.4 — Hybrid Search (BM25 + Vectors)

### Exercise 4.4.1: Implement RRF

```python
def reciprocal_rank_fusion(ranks_list, k=60):
    # TODO: combine multiple ranked lists using RRF
    # score(d) = sum(1 / (k + rank_i(d)))
    # Merge top-5 from each list
    pass
# Test: 3 different retrievers, 50 questions. Compare merged vs each alone.
```

### Exercise 4.4.2: Query rewriting for hybrid

```python
# TODO: Some queries are better for BM25 (exact terms), others for vector (paraphrase).
# Build a router: if query has >3 specific terms, use BM25-heavy. Else vector-heavy.
# Measure: does routing help?
```

---

## Snippet 4.5 — RAG Evaluation with RAGAS

**Reference:** [`../ai-engineer-codebook.md#45-rag-evaluation-with-ragas`](../ai-engineer-codebook.md#45-rag-evaluation-with-ragas)

### Exercise 4.5.1: Build a RAGAS eval set

```python
# TODO: Create 50 (question, ground_truth_answer, source_doc) tuples.
# Run your RAG. Compute:
# - context_precision: are the retrieved chunks actually relevant?
# - context_recall: did we retrieve all needed chunks?
# - faithfulness: does the answer stick to the context (no hallucination)?
# - answer_relevance: is the answer actually about the question?
# This is your "golden set". Re-run on every prompt / chunking change.
```

### Exercise 4.5.2: Find the worst-performing queries

```python
# TODO: Look at the 10 lowest-scoring queries in your eval set.
# Categorize: are they retrieval failures? Generation failures? Both?
# For each, hypothesize the fix (better chunking? better prompt? more context?).
# Implement one fix. Re-measure.
```

### Exercise 4.5.3: A/B test with RAGAS

```python
# TODO: Change one variable (e.g., chunk size from 1000 to 500).
# Run the eval set before and after.
# RAGAS gives you a delta. Decide: ship or roll back?
# This is how you avoid "improvements" that secretly break things.
```

---

## Cross-cutting challenges (Mid+)

### Challenge A: Build a self-improving RAG

```python
# TODO: When users rate an answer "thumbs down", log:
# - the question
# - the retrieved chunks
# - the answer
# - the user feedback
# Periodically: cluster the thumbs-down, find patterns, fix the root cause.
# This is how mature RAG products get better over time.
```

### Challenge B: Multi-modal RAG

```python
# TODO: Add image support to your RAG:
# - Index images (CLIP embeddings)
# - On query, return text + image chunks
# - GPT-4o reads the image as part of context
# Use case: a UI design RAG (Figma + text specs)
```

### Challenge C: Document hierarchy RAG

```python
# TODO: Build a RAG that respects doc hierarchy:
# - doc > section > paragraph > sentence
# - Embed at sentence level
# - Return sentence + its parent paragraph + grandparent section
# - This gives the LLM more context than the matched sentence alone
# Use case: long technical manuals.
```

---

## Architect-level reflections (Senior+)

After completing these exercises, write a 1-page design doc answering:

1. **What's your chunking strategy?** (size, overlap, semantic vs fixed)
2. **Vector DB choice?** (Pinecone vs Weaviate vs pgvector — when to migrate)
3. **Hybrid search?** (when does it help, what's the cost)
4. **Re-ranking?** (always, never, or for hard queries only)
5. **Re-ranking model?** (cross-encoder vs LLM)
6. **RAG eval set size?** (50? 200? 1000?) and how you maintain it
7. **What metrics matter?** (faithfulness, relevance, latency, cost)
8. **How do you handle "I don't know"?** (refuse to answer vs try harder)
9. **Streaming?** (SSE for the LLM, but should you also stream retrieval?)
10. **Multi-modal?** (when is it worth the complexity)

Save these answers. RAG is the most-deployed AI pattern. Get the architecture right.

---

## What's next

- Pair with [`../../practice/level-4-rag/`](../../practice/level-4-rag/) for the deeper labs
- Move to `section-5-agents-exercises.md` for agent patterns
- See [`../../PRACTICE-GUIDE.md`](../../PRACTICE-GUIDE.md) for the full learning path