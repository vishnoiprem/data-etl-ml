# Module 5 — RAG & LLM Data Infrastructure

> 7 lessons · The data engineering of retrieval-augmented generation
> Ingestion, chunking, production RAG, eval, unstructured at scale, frameworks.

---

## Lesson Index

| # | Lesson | Type | Notes |
|---|--------|------|-------|
| 1 | [RAG Architecture](./01-rag-architecture.md) | Article | [Open](./01-rag-architecture.md) |
| 2 | [Ingestion & Chunking](./02-ingestion-chunking.md) | Article | [Open](./02-ingestion-chunking.md) |
| 3 | [Production RAG](./03-production-rag.md) | Article | [Open](./03-production-rag.md) |
| 4 | [RAG Evaluation](./04-rag-evaluation.md) | Article | [Open](./04-rag-evaluation.md) |
| 5 | [Unstructured at Scale](./05-unstructured-at-scale.md) | Article | [Open](./05-unstructured-at-scale.md) |
| 6 | [LLM Frameworks](./06-llm-frameworks.md) | Article | [Open](./06-llm-frameworks.md) |
| 7 | [Quiz: RAG & LLM Data Infrastructure](./07-quiz-rag.md) | Quiz | [Open](./07-quiz-rag.md) |

---

## Module Outcomes

By the end of Module 5 you can:

1. **Design** a RAG system end-to-end: ingestion, embedding, retrieval, generation, eval.
2. **Chunk** documents for retrieval quality (size, overlap, metadata, hierarchical strategies).
3. **Operate** a production RAG pipeline with freshness, ACLs, and observability.
4. **Evaluate** RAG quality with retrieval metrics, generation metrics, and end-to-end LLM-as-judge.
5. **Process** unstructured data (PDFs, images, audio, HTML) at scale.
6. **Pick** between LangChain, LlamaIndex, Haystack, and custom pipelines for your use case.
7. **Debug** bad RAG answers: where they come from and how to fix them.

---

## The RAG pipeline at a glance

```
   ┌──────────────────────────────────────────────────────────────────┐
   │                    RAG PIPELINE — DATA FLOW                      │
   │                                                                  │
   │   SOURCES              INDEX                 QUERY               │
   │   ───────              ─────                 ─────               │
   │                                                                  │
   │   Docs/PDFs ──┐                                                            │
   │   Notion  ────┤                                                            │
   │   Tickets ────┼──►  chunk  ──►  embed  ──►  vector DB  ──┐       │       │
   │   DB rows ────┤                              ▲           │       │       │
   │              │     extract         metadata  │           ▼       │       │
   │              │     ┌──────┐         filters   │      ┌─────────┐ │       │
   │              └────►│parse │──────────┐        │      │retrieve │ │       │
   │                    └──────┘          │        └──────│ + rerank│ │       │
   │                                        │                └────┬────┘ │       │
   │                                        │                     ▼      │       │
   │                                        │              ┌──────────┐│       │
   │                                        │              │   LLM    ││       │
   │                                        │              └────┬─────┘│       │
   │                                        │                   ▼       │       │
   │                                        │                answer     │       │
   │                                        │                            │       │
   │   eval / observability ◄────────── every link in this chain ──────┘       │
   └──────────────────────────────────────────────────────────────────┘
```

The DE work is the entire horizontal axis: ingest, parse, chunk, embed, upsert, refresh, ACL, eval. The LLM is one box in the middle.
