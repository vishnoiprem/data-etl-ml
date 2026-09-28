# Module 5 — Modern LLM Architecture

> Source: Outcome School · Module 5 · 7 lessons

---

## Course Promise

> "Read the architecture section of any new open-weight model and understand every design choice in it."

Modern LLMs add tricks on top of the basic Transformer: MoE for cheaper inference at scale, GQA for KV-cache memory savings, sliding window for long context, attention sinks for streaming, Flash Attention for GPU efficiency. By the end, DeepSeek-V4's architecture diagram is readable.

---

## Lesson Index

| # | Lesson | Type | Theme |
|---|--------|------|-------|
| 1 | [Evolution of LLM Architecture](./01-evolution-of-llm-architecture.md) | Article + Worked Example | RNN → attention → Transformer → scale → MoE |
| 2 | Mixture of Experts | Article | Routers, sparse activation, load balancing |
| 3 | Grouped Query Attention | Article | MHA → MQA → GQA, the KV-cache savings |
| 4 | Sliding Window Attention | Article | Local attention for long context |
| 5 | Attention Sinks | Article | StreamingLLM, why first tokens matter |
| 6 | Flash Attention | Article | Tiling, online softmax, the GPU memory hierarchy |
| 7 | DeepSeek-V4 | Article | The full architecture: CSA, HCA, mHC, Muon, FP4 |

---

## The Lead Lesson

> **Lesson 1 — [Evolution of LLM Architecture](./01-evolution-of-llm-architecture.md)** — the 10,000-foot view. Worked example: build a tiny Mixture-of-Experts model from the dense baseline, measure the FLOPs and active-parameter savings, and visualize the routing decisions.