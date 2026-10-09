# ADR-0002 — Mock vector store over Pinecone for Phase 2

- **Status:** accepted (will revisit at 10K chunks)
- **Date:** 2026-W3 (Phase 2, week 1)
- **Owner:** FDE
- **Stakeholders consulted:** Daniel (IT), CEO (cost ceiling)

## Context

The drafter needs to retrieve the top-3 policy chunks for a query. The corpus is 22 chunks (PF style guide, ~3.2KB). At this size, the choice is between an in-process mock and a hosted vector DB (Pinecone, Weaviate, pgvector).

## Decision

For Phase 2 we use a **deterministic in-process mock** (`MockVectorStore` in `service/rag.py`) — token-overlap scoring with a fixed seed. We replace it with a real vector store in Phase 3 when the corpus is large enough to need it.

## Considered alternatives

| Option | Cost | Setup | Verdict |
|---|---|---|---|
| **In-process mock (token overlap)** | $0 | 0 minutes | ✅ chosen for Phase 2 |
| pgvector (single VM) | $0 (free extension) | 2 hours | rejected — 22 chunks, no need for a real DB |
| Pinecone (serverless) | ~$0 at 22 chunks | 30 min + API key | rejected — premature infra; cost ceiling is the spec |
| Weaviate | VM + 1 container | 2 hours | rejected — over-engineered |
| FAISS in-process | $0 | 30 min | rejected — adds a dep without changing the answer for 22 chunks |

## Consequences

- 13/13 pytest cases run offline with no API key. The CI gate is green on a $5/mo VM.
- The retrieval quality is **worse** than a real vector DB on real-world queries (typos, multi-language, "where is my parcel?"). This is the gap Phase 3 closes with the **hybrid retriever** (BM25 + dense + RRF).
- The `MockVectorStore` is a contract: any replacement must implement `retrieve(query, k, source_filter) -> list[RetrievedChunk]` with the same return shape. **Phase 3 swaps the impl behind the contract; the rest of the service doesn't change.**

## When to revisit

| Trigger | Migration |
|---|---|
| > 10K chunks in the corpus | pgvector on the same VM (free extension) |
| > 100K chunks | Pinecone serverless ($0 at this volume; the API key is the cost) |
| Multi-language queries fail eval set > 5% | Move to dense retrieval (sentence-transformers + FAISS) — done in Phase 3 T1 |

## Why this is the right call

- The cost ceiling is the spec. **Adding a vector DB before the corpus needs it is a cost ceiling breach for $0 of value.** Mei's daily volume is 150 drafts/day; 22 chunks covers the entire retrieval surface.
- The contract-first design (ADR-0001's Pydantic models + this ADR's `retrieve()` signature) means the migration is a 1-file change, not a service-wide refactor. The 13/13 tests stay green.
