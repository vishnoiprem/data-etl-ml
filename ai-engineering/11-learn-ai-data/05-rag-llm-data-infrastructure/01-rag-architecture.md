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

## Worked Example — a 5-design-question design brief, end-to-end

> **Brief:** *"Design a RAG bot over our 50,000 Notion pages. Internal employees only. Refresh: every 6 hours. ACL: only show pages the user is permitted to see."*

This is the kind of brief a senior DE receives in a 1:1 or a kickoff doc. Walk it through the 5 design questions from the lesson.

### Q1 — Chunking strategy

```
   Decision: recursive structure-aware chunking, 400 tokens with 80-token overlap

   Reasoning:
   - Notion content is a mix of prose, headings, tables, code blocks.
   - Fixed-size chunking breaks paragraphs mid-sentence.
   - Sentence chunking explodes the count for long pages.
   - Recursive with structure-awareness: respect headings, code blocks, lists.
   - 400 tokens = ~1 paragraph in technical docs. Sweet spot for embedding
     granularity (covered in Lesson 2).
   - 80-token overlap = 20%, prevents losing cross-paragraph context.

   Metadata per chunk:
   - page_id (Notion)
   - parent_page_id (for tree traversal)
   - workspace_id (for ACL)
   - user_permissions[] (Notion's permission list)
   - last_edited_time (for freshness SLO)
   - heading_path[] (e.g., ["Refund", "> Eligibility"])
   - chunk_index_in_page (ordinal)
   - content_type ("prose", "table", "code", "list")
```

### Q2 — Retrieval approach

```
   Decision: hybrid (BM25 + vector) with cross-encoder rerank

   Reasoning:
   - Notion queries mix exact-term ("policy-D-12") and semantic
     ("what's our cancellation policy").
   - Pure vector misses exact IDs; pure BM25 misses paraphrases.
   - RRF fusion over BM25-top-50 + vector-top-50 → top-100 union.
   - Cross-encoder rerank (Cohere Rerank 3) on top-100 → final top-10.
   - Adds ~50ms but recovers 5-10% recall. (Lesson 3 of this module.)

   Where to filter ACL:
   - At the vector DB query: WHERE workspace_id IN :user_workspaces
     AND (visibility='public' OR user_id IN :page_editors).
   - NOT in the LLM prompt. LLM can be prompt-injected.
```

### Q3 — Freshness SLO

```
   Decision: 6-hour freshness (matches the brief)

   Mechanism:
   - Notion API → webhook on page change → Kafka event.
   - Consumer picks up page_id, fetches new content, re-chunks,
     re-embeds, upserts into vector DB.
   - Pages edited > 6h ago are stale (alert if lag exceeds SLA).
   - Full re-ingest of all 50K pages nightly to catch missed webhooks.

   Cost check:
   - 50K pages × ~600 tokens = 30M tokens to embed at full re-ingest.
   - At $0.02/1M (Cohere embed-v3 / OpenAI small) = $0.60/night.
   - Trivial. The infra to wire webhooks is the bigger cost.
```

### Q4 — Eval set

```
   Decision: 200-query eval set, hand-curated over 2 days

   Composition:
   - 120 "production-realistic" queries (mix of factual, multi-hop)
   - 30 "hard" queries (multi-step, edge cases)
   - 30 "guardrail" queries (PII, off-topic, prompt injection)
   - 20 "freshness" queries (recently edited pages)

   Per query, capture:
   - query text
   - expected_doc_ids (3-5 ground-truth Notion pages)
   - expected_answer (1-2 sentences, hand-written)
   - difficulty (easy / medium / hard)
   - user_context (which workspaces this user can access)

   Refresh: quarterly + every time Notion adds a major feature.

   Run nightly at 01:00 against prod pipeline. Track:
   - recall@10 (was the right page in the top-10?)
   - MRR (how high was the first hit?)
   - faithfulness (LLM-as-judge, 1-5)
   - citation_accuracy (LLM-as-judge, 1-5)
   - p95 latency
   - cost per query
   - guardrail pass rate (must not regress)
```

### Q5 — ACL model

```
   Decision: filter at the vector DB query; Notion permissions drive metadata

   Reasoning:
   - Notion has its own permission model: workspace, page-level user lists,
     public-to-workspace, restricted-to-team.
   - At ingest, attach every chunk with the page's effective permissions.
   - At query, join against the requesting user's permissions.
   - Fail-closed: if permission metadata is missing, refuse to show.

   Metadata schema per chunk:
   {
     "page_id": "...",
     "workspace_id": "...",
     "parent_page_id": "...",
     "user_emails_with_access": ["alice@co.com", "bob@co.com"],
     "team_ids_with_access": ["team-eng", "team-data"],
     "visibility": "workspace" | "team" | "restricted" | "public",
     "last_edited_time": "..."
   }

   Query filter:
   WHERE
     workspace_id = :user_workspace
     AND (
       visibility = 'workspace'
       OR :user_email IN user_emails_with_access
       OR :user_team IN team_ids_with_access
     )
     AND NOT archived
```

### Putting it together — the cost roll-up

```
   Embeddings (50K pages × 600 tok × nightly re-ingest × $0.02/1M) = $0.60/day
   Vector DB (managed Pinecone, 100K chunks @ 1536d)              = $70/mo
   BM25 (OpenSearch S2 tier)                                      = $150/mo
   Cohere Rerank (5K queries/day × ~$0.001/query)                  = $150/mo
   LLM serving (Claude Haiku for routing, Sonnet for answers,
                5K queries × ~$0.005/query)                        = $750/mo
   Eval + monitoring                                              = $50/mo
   ────────────────────────────────────────────────────────────
   Total: ~$1,200/mo, ~$0.008/query
```

That's a real number you can put in a budget doc. $1,200/mo for an internal tool that handles 5K queries/day across 200 employees.

### What this example demonstrates

- All 5 design questions answered with **specifics** (numbers, schema, threshold).
- The interplay: ACL metadata drives the chunk schema, which drives the vector DB query, which drives the LLM context, which drives what the user can see. **The DE owns the chain.**
- A real cost roll-up that survives scrutiny in a budget review.
- The 80/20: you answered 5 design questions in maybe 90 minutes of focused work. That becomes the kickoff doc. Without these answers, the project is "we're building a RAG" — and it never ships.

This is the kind of design brief that should exist for every RAG project before a single line of code is written. If you can't fill it in, the project isn't ready.

---

## What Comes Next

> Lesson 2 — **Ingestion & Chunking** — the most-debated stage. Chunk size, overlap, hierarchical strategies, metadata preservation, and the tradeoffs.
