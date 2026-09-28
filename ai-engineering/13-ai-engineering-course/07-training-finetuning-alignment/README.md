# Module 7 — Training, Fine-Tuning, and Alignment

> Source: Outcome School · Module 7 · 11 lessons

---

## Course Promise

> "Know when to fine-tune, how LoRA makes it cheap, and how RLHF, PPO, DPO, and GRPO align a model."

This module covers the full adaptation stack: from full fine-tuning to LoRA to prefix tuning to knowledge distillation, then the alignment story — RLHF, InstructGPT, PPO, DPO, and the newer GRPO.

---

## Lesson Index

| # | Lesson | Type | Theme |
|---|--------|------|-------|
| 1 | [How Does Fine-Tuning Work?](./01-how-does-fine-tuning-work.md) | Article + Worked Example | Full fine-tuning vs LoRA, the cost math |
| 2 | LoRA | Article | Low-rank updates, the merge step |
| 3 | Prefix Tuning | Article | Trainable prefixes, no weight changes |
| 4 | Knowledge Distillation | Article | Teacher → student, temperature softmax |
| 5 | Continual Learning | Article | Catastrophic forgetting and how to fight it |
| 6 | Deep RL from Human Preferences | Article | The 2017 paper that started RLHF |
| 7 | InstructGPT | Article | SFT → RM → PPO, the GPT-3 instruction pipeline |
| 8 | RLHF | Article | The full pipeline, the KL penalty |
| 9 | PPO | Article | Clipped surrogate objective, the on-policy step |
| 10 | DPO | Article | Direct preference optimization, no reward model |
| 11 | GRPO | Article | Group-relative, the DeepSeek-R1 algorithm |

---

## The Lead Lesson

> **Lesson 1 — [How Does Fine-Tuning Work?](./01-how-does-fine-tuning-work.md)** — the foundational lesson. Worked example: take a 7B base model, fine-tune it on a 10K-example instruction dataset, compare full fine-tuning vs LoRA on (a) quality on a held-out set, (b) GPU memory, (c) wall-clock time. Numbers, not vibes.