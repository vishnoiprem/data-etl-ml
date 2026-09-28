# Lesson 4 — Embedding Pipelines

> **Type:** Article · Module 4 · Vector Databases & Embeddings
> The production pipeline: source → chunk → embed → upsert → refresh, with versioning and rollback.

---

## The pipeline

```
   SOURCES                  TRANSFORM                 STORE
   ───────                  ─────────                 ─────
   docs/PDFs ──┐
   Notion  ────┤
   Tickets ────┼──►  parse  ──►  chunk  ──►  embed  ──► vector DB
   DB rows ────┤                                    ▲
              │     metadata                       │
              │     filters                        │ upsert / refresh
              └────────────────────────────────────┘
```

The DE work is everything **except** the "embed" call. Ingestion, parsing, chunking, metadata, freshness, ACL, refresh — that's your job.

---

## The 5 stages

### Stage 1 — Source extraction

```python
# Generic interface
class Source(Protocol):
    def list_items(self, since: datetime) -> Iterator[Item]: ...
    def get_content(self, item_id: str) -> bytes: ...
    def get_metadata(self, item_id: str) -> dict: ...
```

Each source (Notion, Confluence, S3, SFTP, DB) implements this interface. The rest of the pipeline is source-agnostic.

### Stage 2 — Parse

Convert bytes → structured text + metadata:

- **PDFs**: `unstructured`, `pdfplumber`, `pypdf`, or vendor APIs (Textract, Document AI).
- **HTML**: BeautifulSoup, `trafilatura`.
- **Office docs**: `python-docx`, `openpyxl`.
- **Code**: tree-sitter, language-specific parsers.
- **Images** (for OCR / vision): Tesseract, AWS Textract, Google Document AI, GPT-4o vision.

Always preserve: page numbers, section headings, document version, source URL.

### Stage 3 — Chunk

**This is the most-debated stage.** (Lesson 2 of Module 5.)

Quick heuristic: 200–500 tokens per chunk, 10–20% overlap, preserve headings as chunk metadata.

### Stage 4 — Embed

```python
from openai import OpenAI

client = OpenAI()
response = client.embeddings.create(
    model="text-embedding-3-small",
    input=[chunk.text for chunk in chunks],
)
embeddings = [d.embedding for d in response.data]
```

**Batch where possible** — embedding APIs are far cheaper per call at batch size 100 vs. 1.

### Stage 5 — Upsert + metadata

```python
vector_db.upsert(
    ids=[chunk.id for chunk in chunks],
    vectors=embeddings,
    payloads={
        "tenant_id": chunk.tenant_id,
        "doc_id": chunk.doc_id,
        "chunk_index": chunk.index,
        "text": chunk.text,
        "source": chunk.source,
        "created_at": chunk.created_at,
        "acl": chunk.acl,
        "tags": chunk.tags,
    },
)
```

---

## The metadata schema

A solid metadata schema covers:

| Field | Why |
|---|---|
| `tenant_id` | Multi-tenant isolation |
| `doc_id` | Track which doc each chunk came from |
| `chunk_index` | Reconstruct the document from chunks |
| `text` | The chunk content (for reranking / display) |
| `source` | URL, file path, table name |
| `created_at` / `updated_at` | Freshness filters |
| `acl` / `visibility` | Permission filtering |
| `language` | Language filters |
| `doc_type` | Document type filters |
| `tags` | Custom tags (project, owner, etc.) |
| `embedding_model_version` | Which model produced this vector |

The `embedding_model_version` field is **critical** — when you change embedding models, you need to re-embed everything, and you need to track which model is on which chunk.

---

## The "refresh" patterns

### Full rebuild
Re-embed everything. Simple, expensive.
```
   trigger: new embedding model OR major schema change
   frequency: rare (every few months)
   duration: hours/days at scale
```

### Incremental
Only embed new / changed documents.
```
   trigger: source-side change detection (CDC, webhooks, polls)
   frequency: every few minutes to hourly
   duration: minutes
```

### Hybrid (most common)
Incremental for new content; weekly full rebuild for completeness.
```
   trigger:
     - incremental: on source change
     - weekly: full re-sync (catches missed changes)
```

---

## The "what about deletes" question

When a document is deleted at the source, **the chunks must be deleted from the vector DB**. Otherwise you have stale vectors being retrieved for queries.

```
   source deleted doc
        │
        ▼
   emit delete event (CDC / webhook / poll)
        │
        ▼
   find all chunks with doc_id
        │
        ▼
   vector_db.delete(ids=[chunk_ids])
```

Same for ACL changes (visibility changed → re-index).

---

## The "model upgrade" plan

When you upgrade to a better embedding model:

1. **Re-embed in parallel.** Old vectors + new vectors, on the same chunks.
2. **A/B test.** 10% of queries use new model, 90% old. Compare recall.
3. **Cut over.** 100% new model.
4. **Delete old vectors.** Free storage.
5. **Update the manifest.** `embedding_model_version` on every chunk.

The hard part is **in-flight consistency during the cutover**. Plan for it.

---

## The pipeline observability

What you log and alert on:

```
   Per-stage metrics:
   - source: items extracted, items failed
   - parse: documents parsed, parse errors, avg parse time
   - chunk: chunks produced, avg chunk size
   - embed: API calls, tokens, latency, errors, cost
   - upsert: vectors upserted, conflicts, latency

   End-to-end:
   - freshness: time from source change → vector available
   - completeness: source count vs vector count
   - drift: chunk size distribution, embedding norms
```

If your "embedding freshness SLO" is 1 hour, you need an alert at 2 hours.

---

## The "minimum viable embedding pipeline"

For a prototype:

```python
def embed_and_store(items):
    for item in items:
        chunks = chunk(item.text, size=500, overlap=50)
        for i, c in enumerate(chunks):
            vec = embed(c)
            vector_db.upsert(
                id=f"{item.id}_{i}",
                vector=vec,
                payload={
                    "doc_id": item.id,
                    "chunk_index": i,
                    "text": c,
                    "source": item.source,
                },
            )
```

For production, add: batched API calls, error handling, retry, observability, freshness SLO, ACL, model versioning, deletion handling.

---

## What Comes Next

> Lesson 5 — **Hybrid Search** — combining BM25 (lexical) and ANN (semantic) for the highest-quality retrieval.
