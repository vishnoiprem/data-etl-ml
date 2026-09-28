# Course 3 — Prompt Engineering with LangChain

> Source: Data Vidhya — Prompt Engineering with LangChain
> Level: Intermediate | Prereqs: Course 1

---

## Course Promise

> "Stop typing prompts into a chat box. Build prompt templates you can version, A/B test, evaluate, and ship to production."

Prompt engineering at scale is not about clever wording. It's about **templated, versioned, evaluated prompts** that behave deterministically when the model changes, the inputs drift, or the team rotates.

---

## Lesson Index

| # | Lesson | Type | Theme |
|---|--------|------|-------|
| 1 | [Prompts as code](./01-prompts-as-code.md) | Article + Worked Example | Templates, partials, few-shot injection, Jinja |
| 2 | Zero-shot vs few-shot | Article | When to use which, format pitfalls |
| 3 | Chain-of-thought | Article | When CoT helps, when it doesn't, "think before you answer" |
| 4 | Structured output prompting | Article | JSON, XML, function-calling schemas |
| 5 | System prompts that scale | Article | Role, constraints, examples, edge cases |
| 6 | Prompt versioning & A/B testing | Article | Git, LangSmith, statistical significance |
| 7 | Prompt security | Article | Prompt injection, jailbreaks, output filtering |
| 8 | When NOT to prompt-engineer | Article | Fine-tuning, retrieval, tools — pick the right tool |

---

## What "good" looks like after this course

1. Every prompt lives in a `.py` file with a template, not in a chat box.
2. Every prompt change is a PR with an eval gate.
3. Few-shot examples are loaded from a dataset, not hardcoded.
4. System prompts explicitly call out constraints and edge cases.
5. You know when to prompt-engineer vs fine-tune vs retrieve vs build a tool.

---

## The Lead Lesson

> **Lesson 1 — [Prompts as code](./01-prompts-as-code.md)** — the discipline of treating prompts as production assets. Includes a worked example that builds a customer-email classification system with templated prompts, dynamically-loaded few-shot examples, version-controlled system prompts, and a 4-way A/B test (zero-shot vs few-shot vs CoT vs JSON-mode).
