# Module 6 — Types of Language Models

> Source: Outcome School · Module 6 · 5 lessons

---

## Course Promise

> "Know which kind of model to pick for which problem."

Not every language model is a large text-generating LLM. This module covers the spectrum: small models for the edge, reasoning models that think before they answer, recursive models for huge contexts, diffusion text models, and decision-only System One models.

---

## Lesson Index

| # | Lesson | Type | Theme |
|---|--------|------|-------|
| 1 | [Small Language Models (SLMs)](./01-small-language-models.md) | Article + Worked Example | When 1B-7B is enough |
| 2 | Large Reasoning Models (LRMs) | Article | Test-time compute, o1/o3/R1-style |
| 3 | Recursive Language Models (RLMs) | Article | Code-as-context for huge inputs |
| 4 | Diffusion Language Models (DLMs) | Article | Parallel generation, the new paradigm |
| 5 | Jev & System One Models | Article | Decision-only, cannot hallucinate, calibrated |

---

## The Lead Lesson

> **Lesson 1 — [Small Language Models (SLMs)](./01-small-language-models.md)** — the most operationally important decision. Worked example: take a 7B model, quantize it to 4-bit, run it on a single consumer GPU, and benchmark its latency, throughput, and quality vs a 70B cloud model for a specific task — the cost/quality tradeoff with real numbers.