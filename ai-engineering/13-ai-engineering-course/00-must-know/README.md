# Module 0 — Must Know

> Source: Outcome School AI Engineering Course · Module 0
> Lessons: 1

---

## Why this module exists

Before any depth, six words come up in every AI Engineering conversation. If you don't have crisp definitions for these, every later module is harder than it needs to be.

```
   THE SIX WORDS
   ─────────────
   LLM            Large Language Model — what we're building on
   RAG            Retrieval-Augmented Generation — how we give it knowledge
   MCP            Model Context Protocol — how it talks to tools/data
   Agent          LLM + loop + tools + memory — how it does work
   Fine-tuning    How we adapt a pre-trained model to our task
   Quantization   How we make models small enough to run cheaply
```

---

## Lesson Index

| # | Lesson | Type | Theme |
|---|--------|------|-------|
| 1 | [The six words of AI engineering](./01-the-six-words.md) | Article + Worked Example | LLM, RAG, MCP, Agent, Fine-tuning, Quantization — with a 1-page mental model for each |

---

## The Lead Lesson

> **Lesson 1 — [The six words](./01-the-six-words.md)** — crisp, analogy-first definitions of each. Worked example: build a one-page system that uses all six together (a quantized local LLM answering questions from a RAG knowledge base via MCP, wrapped in an agent loop with optional fine-tuning).