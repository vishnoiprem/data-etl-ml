# Module 3 — Generative AI and the Transformer Architecture

> Source: Outcome School · Module 3 · 15 lessons

---

## Course Promise

> "Draw the Transformer from memory and explain every block inside it, including the math behind Q, K, and V."

This is the heart of the curriculum. Every modern AI system is a Transformer variant. By the end you'll understand tokenization, embeddings, self-attention, multi-head attention, causal masking, RoPE, and the feed-forward network.

---

## Lesson Index

| # | Lesson | Type | Theme |
|---|--------|------|-------|
| 1 | [What is Generative AI?](./01-what-is-generative-ai.md) | Article + Worked Example | The big picture: from discriminative to generative |
| 2 | Autoregressive Models | Article | The chain rule of probability, the generation loop |
| 3 | BPE Tokenization | Article | How text becomes integers, the merge algorithm |
| 4 | Embeddings | Article | Meaning in N-D, the famous word math |
| 5 | RNN vs Transformer | Article | Sequential vs parallel, why attention wins |
| 6 | Transformer Architecture | Article | The canonical encoder-decoder, end to end |
| 7 | Encoder vs Decoder | Article | When to use which, the three Transformer variants |
| 8 | Self Attention | Article | The core mechanism, step by step |
| 9 | The Math of Q, K, V | Article | The dot-product attention, with numbers |
| 10 | Scaling by √dₖ | Article | Why the scaling factor exists, the variance argument |
| 11 | Causal Masking | Article | Why LLMs can't see the future |
| 12 | Multi-Head Attention | Article | Many heads, one concatenation |
| 13 | Cross Attention | Article | When query and key come from different sources |
| 14 | RoPE | Article | Rotary position embeddings, the rotation math |
| 15 | Feed-Forward Network | Article | The expand-then-contract pattern, MoE FFNs |

---

## The Lead Lesson

> **Lesson 1 — [What is Generative AI?](./01-what-is-generative-ai.md)** — the framing lesson. Worked example: build a tiny character-level Transformer from scratch in PyTorch (4 layers, 4 heads, ~10M params) and train it on Shakespeare. Show the loss curve, sample text at different temperatures, and visualize the attention patterns.