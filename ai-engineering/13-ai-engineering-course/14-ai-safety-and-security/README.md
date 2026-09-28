# Module 14 — AI Safety and Security

> Source: Outcome School · Module 14 · 3 lessons

---

## Course Promise

> "Defend an LLM application against the most common attacks."

Three lessons: how guardrails work, the prompt injection attack surface (and the defenses that actually work), and how LLM watermarking identifies AI-generated text.

---

## Lesson Index

| # | Lesson | Type | Theme |
|---|--------|------|-------|
| 1 | [LLM Guardrails](./01-llm-guardrails.md) | Article + Worked Example | Input + output filtering, layered defense |
| 2 | Prompt Injection | Article | Direct, indirect, why it's not SQL injection |
| 3 | LLM Watermarking | Article | Hidden signals in token selection |

---

## The Lead Lesson

> **Lesson 1 — [LLM Guardrails](./01-llm-guardrails.md)** — the practical layer. Worked example: build a guardrail pipeline (regex → classifier → LLM-judge) in front of a chat endpoint, attack it with 50 known-bad prompts, measure the catch rate and false-positive rate.