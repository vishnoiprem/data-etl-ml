# Lesson 1 — RAG Architecture

> **Type:** Article · Module 5 · RAG & LLM Data Infrastructure
> The data engineering of retrieval-augmented generation, end-to-end.

---

## What RAG is

**Retrieval-Augmented Generation** = ground an LLM's answer in your own data, at query time. The LLM doesn't know your internal docs. RAG retrieves the relevant ones and puts them in the prompt.

```
   ┌──────────────────────────────────────────────────────────────┐
   │                      RAG FLOW                                 │
   │                                                              │
   │   USER QUERY                                                 │
   │      │                                                       │
   │      ▼                                                       │
   │   ┌─────────┐                                                │
   │   │ Rewrite │  optional: HyDE, expansion, clarification       │
   │   └────┬────┘                                                │
   │        ▼                                                     │
   │   ┌─────────┐                                                │
   │   │ Retrieve│  hybrid (BM25 + vector) + metadata filters      │
   │   └────┬────┘                                                │
   │        ▼                                                     │
   │   ┌─────────┐                                                │
   │   │ Rerank  │  optional: cross-encoder, LLM rerank            │
   │   └────┬────┘                                                │
   │        ▼                                                     │
   │   ┌─────────┐                                                │
   │   │   LLM   │  prompt = query + retrieved context + history   │
   │   └────┬────┘                                                │
   │        ▼                                                     │
   │      ANSWER  (+ citations, confidence, caveats)              │
   └──────────────────────────────────────────────────────────────┘
```

The DE work is everything **except** the LLM call. Retrieval, chunking, ingestion, freshness, ACL, eval — that's your job.

---

## The two parts of the loop

### Offline (index time)
```
   source docs → parse → chunk → embed → vector DB
                                      ↓
                              (refresh on change)
```

### Online (query time)
```
   user query → rewrite → retrieve → rerank → LLM → answer
                                       ↘ eval ↗
```

The offline work is ~80% of the engineering effort. The online work is ~20% but is what the user sees.

---

## The components

| Component | What | DE owns? |
|---|---|---|
| **Sources** | Notion, Confluence, PDFs, DBs | maybe |
| **Parsing** | PDF → text, HTML → text, OCR | yes (or vendor) |
| **Chunking** | Split docs into retrieval units | yes |
| **Embedding** | Vector per chunk | mostly vendor |
| **Vector DB** | Store + ANN search | yes |
| **Metadata filters** | tenant, date, doc type | yes |
| **Query rewriting** | Expand, clarify, HyDE | yes |
| **Hybrid retrieval** | BM25 + vector + metadata | yes |
| **Reranking** | Cross-encoder / LLM | mostly vendor |
| **LLM** | Generation | vendor |
| **Prompt assembly** | Query + context + history | yes |
| **Eval & observability** | Recall, faithfulness, latency | yes |
| **ACL** | Who can see what | yes |

---

## The retrieval quality spectrum

```
   WORSE                                              BETTER
   ────────────────────────────────────────────────────────
   vector-only (top-5)  →  hybrid (top-50)  →  rerank (top-10)  →  +query rewrite  →  +HyDE
```

Each step costs more (latency, money) but typically improves recall. Most production systems land at **hybrid + rerank + light rewrite**.

---

## The "retrieval-failure → bad answer" chain

```
   BAD RETRIEVAL
       ↓
   wrong context in prompt
       ↓
   LLM "hallucinations" an answer based on wrong context
       ↓
   user sees a confident, plausibly-wrong answer
       ↓
   trust erodes
```

**RAG quality is retrieval quality.** If the LLM gets the wrong 10 documents, no prompt will save you.

---

## The minimum viable architecture

```
   ingest:
     upload PDFs to S3
        ↓
     parse + chunk (offline)
        ↓
     embed + upsert (offline)
        ↓
     vector DB ready

   query:
     user asks
        ↓
     embed query
        ↓
     vector DB top-10 (cosine)
        ↓
     prompt = query + context
        ↓
     LLM → answer
```

This is **5× more code than I show here**, but the data flow is the backbone. With this, you can demo. Without eval and ACL, you can't ship.

---

## The production architecture

```
   ┌────────────┐
   │  Sources   │ (Notion, Confluence, S3, SFTP, tickets)
   └─────┬──────┘
         │
         ▼  ingestion
   ┌────────────┐    ┌───────────────┐
   │  Parse +   │───►│  Object store │ (S3, GCS) — original bytes
   │  Chunk     │    └───────────────┘
   └─────┬──────┘
         │
         ▼  embed (batched, async)
   ┌────────────┐    ┌───────────────┐
   │  Embedder  │───►│  Vector DB    │  Pinecone / Qdrant / pgvector
   └────────────┘    └───────┬───────┘
                             │
   ┌────────────┐            │
   │  Lexical   │────────────┤
   │  index     │            │
   └─────┬──────┘            │
         │                   │
         └────────┬──────────┘
                  ▼  query time
            ┌──────────┐
            │ Retrieve │ (hybrid + metadata)
            └─────┬────┘
                  ▼
            ┌──────────┐
            │ Rerank   │
            └─────┬────┘
                  ▼
            ┌──────────┐
            │   LLM    │
            └─────┬────┘
                  ▼
                ANSWER
                  │
                  ▼
            ┌──────────────────┐
            │ Eval + observability │
            └──────────────────┘
```

---

## The "what gets better with scale" intuition

| Scale | What changes |
|---|---|
| 1K docs | Single script, in-memory, no metadata |
| 100K docs | Real vector DB, basic chunking, no eval |
| 1M docs | Hybrid search, metadata filters, basic eval |
| 10M docs | Cross-encoder rerank, query rewrite, full eval harness |
| 100M docs | Distributed index, quantisation, freshness SLO, observability |

The shape doesn't change. The operational weight does.

---

## The 5 design questions for any RAG system

1. **What's the chunking strategy?** (Lesson 2)
2. **What's the retrieval strategy?** (Lesson 5 of Module 4)
3. **What's the freshness SLO?** (How stale can the index be?)
4. **What's the eval set?** (How do you measure quality?)
5. **What's the ACL model?** (Who can see which chunks?)

If you can't answer all 5 with specifics, you're building a demo, not a system.

---

## The "what AI does" breakdown

```
   AI-INVOLVED                              DE-INVOLVED
   ────────────                              ────────────
   Embedding the chunks         Source extraction + parse
   Embedding the query          Chunking strategy
   LLM generation               Vector DB ops (index, scale, ACL)
   Optional: LLM rerank         Metadata schema
   Optional: query rewrite      Eval harness
                                Freshness SLO
                                Cost monitoring
                                Incident response
```

The DE work is **the boring 80%** that makes the AI 20% reliable.

---

## What Comes Next

> Lesson 2 — **Ingestion & Chunking** — the most-debated stage. Chunk size, overlap, hierarchical strategies, metadata preservation, and the tradeoffs.
