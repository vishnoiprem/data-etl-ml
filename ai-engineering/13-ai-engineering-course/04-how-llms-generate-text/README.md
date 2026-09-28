# Module 4 — How LLMs Generate Text

> Source: Outcome School · Module 4 · 4 lessons

---

## Course Promise

> "Know exactly what happens between the prompt and the final answer, and which knobs change the output."

This module covers the sampling layer: temperature, top-k, top-p, and token streaming — and the failure mode called "lost in the middle" that every long-context system must defend against.

---

## Lesson Index

| # | Lesson | Type | Theme |
|---|--------|------|-------|
| 1 | [Temperature](./01-temperature.md) | Article + Worked Example | The single number that decides boring vs creative |
| 2 | Top-k and Top-p Sampling | Article | Fixed-k, cumulative-p, when to use which |
| 3 | Token Streaming | Article | SSE, the HTTP mechanics, why "loading..." is gone |
| 4 | Lost in the Middle | Article | The U-shaped attention curve, how to fix it |

---

## The Lead Lesson

> **Lesson 1 — [Temperature](./01-temperature.md)** — the most over-discussed, under-understood knob. Worked example: same prompt, four temperatures (0.0, 0.3, 0.7, 1.2). Show the softmax distributions, the probability spread, and the resulting text quality/diversity tradeoff with measured numbers.