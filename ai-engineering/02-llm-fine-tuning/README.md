# 02 — LLM Fine-Tuning Pipeline

> **Customer problem:** Off-the-shelf foundation models hit only 71% accuracy on our domain-specific extraction tasks (insurance underwriting). Build a repeatable fine-tuning pipeline that lifts task accuracy to ≥92% while keeping costs predictable and the data fully in our VPC.

This project shows the *theory and mechanics* of LLM fine-tuning end-to-end: data preparation, the parameter-efficient methods (LoRA/QLoRA), instruction tuning format, the RLHF loop, and evaluation. The code runs **fully offline on CPU using a tiny logistic-regression "model"** as a stand-in so you can see the full pipeline shape without GPUs. Real production training in `scripts/sagemaker_train.py` is a thin wrapper over PEFT + SageMaker Training.

---

## 1. Theory: When to fine-tune (and when not to)

| Situation | Recommendation |
|---|---|
| Need new factual knowledge | **RAG** — fine-tuning is unreliable for facts |
| Need a specific output format/style | **Fine-tune** (light, instruction tuning) |
| Need narrow-domain reasoning (legal clauses, ICD-10 coding) | **Fine-tune** (LoRA on instructions) |
| Need to align tone, refusal behavior | **RLHF / DPO** |
| Few-shot prompting works | **Don't fine-tune** — prompt engineer |

Fine-tuning trades **operational complexity** (your own model artifact, serving infra, eval cycles) for **task quality and unit cost**. Most teams should reach for prompting + RAG first, fine-tune second.

## 2. The four flavors

### 2.1 Continued pre-training (CPT)
Train on raw domain text to expand the model's vocabulary/style. Rare in enterprise — expensive, hard to evaluate, often yields little.

### 2.2 Supervised Fine-Tuning (SFT) / Instruction Tuning
Train on `(instruction, response)` pairs. The standard chat-tuning recipe. Format matters a lot:

```json
{
  "messages": [
    {"role": "system", "content": "You are an insurance underwriting assistant."},
    {"role": "user", "content": "Extract the policyholder DOB and SSN last-4 from this declaration page: ..."},
    {"role": "assistant", "content": "{\"dob\": \"1985-03-12\", \"ssn_last4\": \"4421\"}"}
  ]
}
```

### 2.3 Parameter-efficient: LoRA / QLoRA
Instead of updating all weights, train **low-rank adapters** alongside frozen base weights.

LoRA decomposes each weight update as ΔW = BA where A ∈ ℝ^{r×k}, B ∈ ℝ^{d×r}, with r ≪ min(d,k). For r=8 on a 7B model you train ~0.1% of parameters and get ~95% of the quality.

QLoRA loads the base model in 4-bit NF4 quantization, freezes it, and trains LoRA adapters in fp16. This lets a 70B model fine-tune on a single 80GB GPU.

### 2.4 RLHF / DPO / RLAIF
After SFT, align further from human (or AI) preferences.

- **RLHF** = train a reward model on `(prompt, chosen, rejected)` triples, then PPO against it. Powerful, complex, unstable.
- **DPO** (Direct Preference Optimization) = skip the reward model; optimize a closed-form objective directly on preference pairs. **This is the modern default** — same data, much simpler.
- **RLAIF** = label preferences with a stronger LLM instead of humans. Cheap, scalable, surprisingly effective.

This project demonstrates DPO conceptually since it's now the standard.

## 3. AWS Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                         Data Preparation                                 │
│  S3 (raw labels) → Glue → SageMaker Ground Truth → S3 (instruction.jsonl)│
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  SageMaker Training Job (LoRA / QLoRA)                  │
│  Container: HuggingFace DLC + PEFT + bitsandbytes + accelerate          │
│  Instance:  ml.g5.12xlarge (4× A10G, 96GB)  or  ml.p4d.24xlarge (8×A100)│
│  Spot:      Yes (with checkpoint-on-interruption)                       │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ (adapter weights, ~50MB)
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    SageMaker Model Registry (versioned)                 │
│   Model package: base_model_id + adapter_artifact + eval_metrics       │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│       SageMaker Inference Components — multi-tenant adapter serving    │
│   1 base model + N adapters hot-swapped per request                    │
└────────────────────────────────────────────────────────────────────────┘
```

## 4. Project Layout

```
02-llm-fine-tuning/
├── README.md
├── Makefile
├── requirements.txt
├── src/
│   ├── data_prep.py       Build instruction-format JSONL from raw labels
│   ├── lora_demo.py       Minimal LoRA-style adapter demo on toy classifier
│   ├── dpo_demo.py        DPO loss math + tiny preference-pair training
│   └── eval_classifier.py Holdout evaluation
├── sample_data/
│   ├── raw_labels.jsonl   Synthetic insurance declaration pages + extractions
│   └── preferences.jsonl  Synthetic (prompt, chosen, rejected) triples
├── scripts/
│   ├── prepare_data.py    CLI: raw_labels → instruction.jsonl
│   ├── train_lora.py      CLI: tiny LoRA demo
│   ├── train_dpo.py       CLI: DPO demo
│   ├── evaluate.py        CLI: pre vs post fine-tune eval
│   └── sagemaker_train.py Production training-job launcher (illustrative)
└── tests/
```

## 5. Quick Start

```bash
pip install -r requirements.txt
make demo
```

The demo runs:
1. `data_prep` — converts 200 synthetic raw labels into instruction-format JSONL.
2. `train_lora` — tiny LoRA-style adapter on a logistic-regression classifier (the math, not the model). Plots the loss curve.
3. `train_dpo` — DPO loss on synthetic preference pairs, showing reward separation grows.
4. `evaluate` — pre vs. post fine-tune accuracy.

## 6. Production Path

For real LoRA fine-tuning on Bedrock or SageMaker, swap `scripts/train_lora.py` for `scripts/sagemaker_train.py` which:
- Uploads `instruction.jsonl` to S3.
- Launches a SageMaker `HuggingFace` Estimator with PEFT, deepspeed, gradient checkpointing.
- Outputs adapter artifacts (`.safetensors`) to a versioned S3 prefix.
- Registers the resulting model package in SageMaker Model Registry with eval metrics.

Bedrock now also supports fine-tuning Claude Haiku, Llama 3, and Titan directly via `CreateModelCustomizationJob` — see `scripts/bedrock_finetune.py`.

## 7. What "Done" Looks Like

| Metric | Target | How measured |
|---|---|---|
| Task accuracy (eval set) | ≥ 92% | Held-out 500-example eval set |
| Cost per training run | ≤ $300 | SageMaker job billing |
| Training time | ≤ 6 hours | Job duration |
| Adapter size | ≤ 100 MB | Adapter artifact on S3 |
| Inference latency (p95) | ≤ 1.5 s | SageMaker endpoint metric |
| Quality regression on general tasks | < 5% drop | MMLU-style held-out probe |
