# Module 8 — Prompt Engineering and Context Engineering

> Source: Outcome School · Module 8 · 5 lessons

---

## Course Promise

> "Design prompts and contexts that make an LLM reliable, fast, and cheap."

Prompt engineering is the discipline of getting the most out of an LLM by what you put in front of it. Context engineering is the broader discipline — everything that goes into the context window: instructions, retrieved docs, few-shot examples, tools, memory, history.

---

## Lesson Index

| # | Lesson | Type | Theme |
|---|--------|------|-------|
| 1 | [Chain-of-Thought Prompting](./01-chain-of-thought.md) | Article + Worked Example | Zero-shot vs few-shot CoT, the reasoning step |
| 2 | Prompt Chaining | Article | When one prompt isn't enough |
| 3 | Prompt Caching | Article | The exact-prefix rule, 90% cost savings |
| 4 | Context Engineering | Article | The discipline bigger than prompt engineering |
| 5 | Context Compaction | Article | Long conversations, summarization, what to keep |

---

## The Lead Lesson

> **Lesson 1 — [Chain-of-Thought Prompting](./01-chain-of-thought.md)** — the technique that unlocked reasoning in LLMs. Worked example: take GSM8K-style math problems, compare (a) zero-shot, (b) zero-shot-CoT, (c) few-shot-CoT on accuracy and cost. Show the actual reasoning traces from each approach.