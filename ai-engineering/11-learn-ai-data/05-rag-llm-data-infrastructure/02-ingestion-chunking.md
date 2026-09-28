# Lesson 2 — Ingestion & Chunking

> **Type:** Article · Module 5 · RAG & LLM Data Infrastructure
> The most-debated stage. Chunk size, overlap, hierarchical strategies, metadata preservation.

---

## Why chunking is the leverage point

**Retrieval quality is mostly chunking quality.** If your chunks don't contain the answer, no embedding or rerank will save you. If they contain the answer with the wrong context, the LLM hallucinates.

```
   ┌──────────────────────────────────────────────────────────┐
   │  QUALITY OF RAG ANSWER ≈                                  │
   │     f(chunking_quality) × f(retrieval_quality)            │
   │                                       × f(LLM_prompting)  │
   │                                                          │
   │  Of these three, chunking_quality is the biggest          │
   │  controllable lever for most teams.                      │
   └──────────────────────────────────────────────────────────┘
```

---

## The chunking spectrum

```
   ❌ BAD                                      ✅ BETTER
   ────────────────────────────────────────────────────────────
   fixed-size 200 token chunks                section-based chunks
                  ↓                                       ↓
   no semantic awareness              preserves heading & context
                  ↓                                       ↓
   "Refund policy: refunds are          "# Refund Policy
    issued within 30 days of             ## Eligibility
    purchase. To request a               Refunds are issued within
    refund, contact support at          30 days of purchase.
    [REFUND_CONTACT_LINK]..."             To request a refund,
                                          contact support at..."
```

The right chunk answer is **the unit of text that, when retrieved, fully answers the question**. That's almost never a fixed-size slice.

---

## The four chunking strategies

### 1. Fixed-size chunks (naive)
```python
chunks = [text[i:i+500] for i in range(0, len(text), 500)]
```

**Pros:** trivial to implement.
**Cons:** cuts mid-sentence, mid-thought; no semantic awareness.

### 2. Sentence / paragraph chunks
```python
chunks = text.split("\n\n")  # paragraph-aware
```

**Pros:** respects natural boundaries.
**Cons:** wildly different chunk sizes; some chunks are 50 tokens, others 2000.

### 3. Recursive / hierarchical chunks
```python
def recursive_chunk(text, max_size=500):
    if len(text) <= max_size:
        return [text]
    # try splitting on paragraph, then sentence, then word
    for sep in ["\n\n", "\n", ". ", " "]:
        if sep in text:
            parts = text.split(sep)
            chunks = []
            for p in parts:
                chunks.extend(recursive_chunk(p, max_size))
            return chunks
    return [text[:max_size]]
```

**Pros:** respects semantic boundaries, produces more-uniform sizes.
**Cons:** still doesn't know about document structure.

### 4. Structure-aware chunks (best for docs)
```python
# parse the doc into its structure first
sections = parse_markdown(doc)       # H1, H2, H3, paragraphs
sections = parse_html(doc, h_tags)    # semantic structure
sections = parse_pdf_with_titles(doc) # use extracted headings

# chunk within each section, preserving heading context
for section in sections:
    chunks = chunk(section.content, max=500)
    for c in chunks:
        c.metadata["heading"] = section.heading
        c.metadata["heading_path"] = section.path  # e.g. ["Refund Policy", "Eligibility"]
```

**Pros:** chunks are semantically coherent; metadata is rich.
**Cons:** requires parsing, which is non-trivial.

---

## The size sweet spot

```
   chunk size            trade-off
   ────────────          ────────────────────────────────────
   < 100 tokens          too small to answer most questions
                         high embedding cost per retrieval
   200-500 tokens        ✅ sweet spot for most retrieval
   500-1000 tokens       good for complex / multi-step questions
                         higher embedding cost
   > 1000 tokens         usually worse — LLM gets confused by long context
                         too vague a "match"
```

For most use cases, **start at 256–512 tokens with 10–20% overlap**, then tune on your eval set.

---

## The overlap story

```
   text:    [====chunk 1====][====chunk 2====][====chunk 3====]
                       \              \
                        \              \
                  overlap region    overlap region
                  (where context    (where the
                   bridges two      bridge carries
                   thoughts)        forward)
```

Without overlap, the answer that *spans* two chunks is lost. With overlap, the bridge context is duplicated in both.

**Typical: 10–20% overlap.** Tune on your eval.

---

## The metadata preservation

Every chunk carries:

| Field | Why |
|---|---|
| `source` (URL / file path) | Citation, debug |
| `doc_id` | Group chunks back to a doc |
| `chunk_index` | Reconstruct the doc |
| `heading` / `section` | Why this chunk exists, helps LLM |
| `heading_path` | Hierarchy — "Refund Policy > Eligibility" |
| `page_number` | For PDFs — citation grounding |
| `created_at` / `updated_at` | Freshness |
| `language` | Filter or rerank |
| `acl` / `visibility` | Permission filter |
| `tags` | Custom tagging |
| `embedding_model_version` | Track model changes |

The metadata is what makes the LLM's answer **grounded**. Without page numbers and section paths, the citation is useless.

---

## The hierarchical strategy

For long documents (whitepapers, books, codebases), use **parent-child chunking**:

```
   PARENT chunks (1000-2000 tokens) — for retrieval ranking, returned in context
      │
      ├── CHILD chunks (200-500 tokens) — for embedding, fine-grained search
```

**Flow at query time:**
1. Embed children. Embed parents with a summary embedding.
2. Retrieve top-k children by similarity.
3. For each child, walk up to the parent.
4. Send parent(s) to LLM as context.

**Why:** children's embedding is precise (small, focused text). Parents give the LLM enough context to answer. This is **the highest-recall pattern** for long-form docs.

---

## The "what to do about tables and code" story

### Tables
- **Naive:** flatten to text. Loses structure.
- **Better:** preserve as Markdown table or HTML. Embedding model reads it.
- **Best:** parse to structured data, embed cell-by-cell with row context.

### Code
- **Naive:** chunk by character. Splits functions.
- **Better:** chunk by function / class boundary.
- **Best:** use a code-aware embedder (Voyage, code-specific model).

---

## The "rechunk when embedding model changes" reminder

When you upgrade your embedder, **you must re-chunk too** if you want to benefit. Different models prefer different chunk sizes. Document the choice:

```yaml
# embedding_config.yml
model: text-embedding-3-large
version: 2026-04-15
chunk_strategy: recursive_semantic
chunk_size: 384
chunk_overlap: 64
metadata:
  - source
  - doc_id
  - chunk_index
  - heading
  - page_number
```

When this changes, every chunk gets re-ingested.

---

## The "end-to-end ingest job" pattern

```python
def ingest_document(doc: Document) -> int:
    """Returns number of chunks upserted."""
    # 1. parse
    sections = parser.parse(doc)              # structured output
    # 2. chunk (structure-aware)
    chunks = []
    for section in sections:
        for c in chunker.chunk(section):
            c.metadata["source"] = doc.source
            c.metadata["doc_id"] = doc.id
            c.metadata["page_number"] = section.page
            c.metadata["heading"] = section.heading
            chunks.append(c)
    # 3. embed (batched)
    embeddings = embedder.embed([c.text for c in chunks], batch_size=100)
    # 4. upsert
    for c, e in zip(chunks, embeddings):
        vector_db.upsert(id=c.id, vector=e, payload=c.metadata)
    return len(chunks)
```

That's the backbone of every RAG ingest job.

---

## What Comes Next

> Lesson 3 — **Production RAG** — the production version: ACL, freshness, observability, prompt engineering, citations, and the eval harness that keeps it honest.
