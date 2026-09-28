# Course 4 — Retrieval-Augmented Generation with LangChain

> Source: Data Vidhya — Retrieval-Augmented Generation with LangChain
> Level: Intermediate-Advanced | Prereqs: Course 1, basic familiarity with embeddings

---

## Course Promise

> "Build a RAG system in LangChain that you'd actually put in front of users — with eval, hybrid search, reranking, and ACL."

This course assumes you already understand what RAG is (Module 5 of `11-learn-ai-data/` covers the theory). Here you'll build the **LangChain implementation** — loaders, splitters, retrievers, rerankers, and the chains that combine them.

---

## Lesson Index

| # | Lesson | Type | Theme |
|---|--------|------|-------|
| 1 | [RAG in LangChain, end-to-end](./01-rag-langchain-end-to-end.md) | Article + Worked Example | Loaders, splitters, retrievers, the canonical chain |
| 2 | Document loaders | Article | PDF, Notion, Confluence, S3, web |
| 3 | Text splitters | Article | Recursive, semantic, structure-aware, the 400-token sweet spot |
| 4 | Retrievers | Article | Vector, BM25, multi-query, self-query, parent-document |
| 5 | Rerankers | Article | Cross-encoder, Cohere Rerank, LLM rerank |
| 6 | The full RAG chain | Article | LCEL, parallel retrieval, citations, streaming |
| 7 | Agentic RAG | Article | When to use an agent vs a chain, tool selection |
| 8 | RAG eval | Article | Recall@k, faithfulness, citation accuracy |

---

## What "good" looks like after this course

1. You can build a RAG system over arbitrary document types in 100 lines of LangChain.
2. You understand which splitter for which document type.
3. You can defend hybrid + rerank over vector-only with numbers from your eval set.
4. You can wire ACL, citations, and streaming into the chain without breaking the eval.
5. You know when to graduate from a chain to an agent.

---

## The Lead Lesson

> **Lesson 1 — [RAG in LangChain, end-to-end](./01-rag-langchain-end-to-end.md)** — the canonical build. A complete RAG system over 5K internal docs (Notion + S3 PDFs), with hybrid retrieval, Cohere rerank, citations, ACL, and an eval harness. Includes the 4 design decisions that decide quality.
