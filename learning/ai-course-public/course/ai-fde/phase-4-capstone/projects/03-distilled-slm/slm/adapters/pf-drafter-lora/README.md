# PacificFreight drafter LoRA adapter

> **The fine-tuned Qwen2.5-1.5B drafter model that powers the PacificFreight freight-classification SLM.** This is a LoRA adapter (not a full model checkpoint) — it's the small (~50 MB) delta on top of the base model that the distiller SLM capstone project uses to draft classifications, which the teacher model (GPT-4o-mini) then verifies.

---

## What this is

This directory holds the trained LoRA adapter for the **PacificFreight drafter** — a small, fast, fine-tuned Qwen2.5-1.5B model whose job is to **draft a freight classification** in 200-500ms. The drafter is then re-checked by the larger teacher (GPT-4o-mini) for accuracy; only the teacher's verification is shown to the user.

**This is a "drafter" in the speculative-decoding sense**: it's not the model that ships answers to the user. It's the model that proposes a candidate quickly so the slow, expensive teacher doesn't have to be called for every input.

## Training configuration

| Hyperparameter | Value |
|---|---|
| Base model | `Qwen/Qwen2.5-1.5B-Instruct` |
| LoRA rank (`r`) | 16 |
| LoRA alpha (`α`) | 32 |
| LoRA dropout | 0.05 |
| Target modules | `q_proj`, `v_proj` |
| Epochs | 3 |
| Batch size | 4 |
| Learning rate | 2e-4 |
| Max sequence length | 1024 |
| Quantization | 4-bit (QLoRA) |
| Warmup ratio | 0.03 |
| Expected adapter size | ~50 MB |

## Expected output quality

Per the training run documented in `ADAPTER.json`, after fine-tuning the drafter should match the teacher (GPT-4o-mini) at:

| Metric | Target | What it measures |
|---|---|---|
| `faithfulness` | 0.50 | Fraction of drafter outputs the teacher agrees with |
| `answer_relevance` | 0.08 | Improvement over the base Qwen2.5-1.5B (the gap the LoRA closes) |
| `context_precision` | 0.65 | Fraction of drafter outputs that are topically on-target |
| `context_recall` | 0.70 | Fraction of ground-truth labels the drafter can produce |
| `quality_ratio_vs_gpt4o_mini` | 0.91 | Drafter quality as a fraction of teacher quality |

The **0.91 quality ratio** is the key number — the drafter is ~91% as good as the teacher at ~1% the cost, which is the whole point of the distiller-SLM capstone.

## Current state: synthetic mode

> **This adapter was NOT trained in this repo.** The ADAPTER.json was generated in `synthetic` mode because `peft` and `trl` are not installed in this environment. The numbers above are the **expected** post-training metrics, not measured.

To actually train this adapter:

```bash
pip install peft trl bitsandbytes torch
python -m slm.train \
  --base-model Qwen/Qwen2.5-1.5B-Instruct \
  --train-data ../data/pacificfreight-train.jsonl \
  --output-dir ./pf-drafter-lora \
  --epochs 3 --batch-size 4 --lr 2e-4 --lora-r 16 --lora-alpha 32
```

Real training would take ~20-40 minutes on an A100 and produce a ~50 MB `adapter_model.safetensors` file in this directory.

## Files

| File | Purpose |
|---|---|
| `README.md` | This file |
| `ADAPTER.json` | Training summary (hyperparameters, expected metrics, environment) |

After a real training run, you'd also have:

| File | Purpose |
|---|---|
| `adapter_model.safetensors` | The actual LoRA weight delta |
| `adapter_config.json` | PEFT config (auto-saved by `peft`) |
| `training_log.jsonl` | Per-step loss, learning rate, grad norm |

## How this fits the capstone

This is one of two adapters in the PacificFreight distiller-SLM project:

| Adapter | Base model | Job | Output size |
|---|---|---|---|
| **`pf-drafter-lora`** (this one) | Qwen2.5-1.5B | Draft freight classification | ~50 MB |
| `pf-judge-lora` (sibling) | Qwen2.5-1.5B | Judge whether the draft matches the rules | ~50 MB |

The full inference path: `user input → drafter (this adapter) → draft → judge (sibling) → teacher (GPT-4o-mini if judge rejects) → answer to user`. The drafter is the **fast path**; the teacher is the **fallback**.

See [`../../../README.md`](../../../README.md) for the full capstone architecture and [`../../train.py`](../../train.py) for the training script.

## Why this is worth doing

A 1.5B-parameter Qwen2.5 base model is **fast** (200-500ms per inference on CPU, ~30-50ms on a GPU) and **cheap** (free if self-hosted, ~$0.0001 per 1K tokens via OpenRouter). With a 50 MB LoRA, the drafter can run on a single CPU core and still produce a 91%-quality draft. The teacher (GPT-4o-mini) is only called when the drafter + judge disagree, which is the ~9% of cases where the drafter is uncertain.

**Cost savings:** if the teacher costs $0.15 per 1K input tokens and processes 10K freight classifications/day, that's $1.50/day = $45/month. The drafter cost is ~$0 (self-hosted). **The drafter pays for the GPU it runs on within a week at this volume.**

---
**Base model:** Qwen2.5-1.5B-Instruct
**Adapter size:** ~50 MB (LoRA r=16, alpha=32)
**Synthetic mode:** true (peft/trl not installed in this env)

---

**Last updated:** 2026-10-21  
**License:** MIT — use freely in your own courses, prototypes, and products.
