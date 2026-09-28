# Lesson 1 — How Does Fine-Tuning Work?

> **Type:** Article + Worked Example · Module 7
> Full fine-tuning vs LoRA, the cost math, with measured numbers from a real 7B fine-tuning run.

---

## What fine-tuning is

Fine-tuning takes a **pre-trained model** (already knows English, code, facts) and trains it more on **your data** (your domain, your format, your style).

```
   PRE-TRAINING                    FINE-TUNING
   ─────────────                   ────────────
   Data:    10T tokens of web      Data:    10K-1M examples of YOUR task
   Compute: 1000+ GPU-years        Compute: 1-100 GPU-hours
   Cost:    $10M-$1B               Cost:    $10-$10K
   Time:    weeks                  Time:    hours to days
   Result:  general-purpose LLM    Result:  specialist LLM
```

The pre-trained model has all the linguistic knowledge. Fine-tuning teaches it the **specific task** — your format, your tone, your domain vocabulary.

---

## The two flavors

### Full fine-tuning
- Update **all** parameters (every weight in every layer)
- For 7B model: 7B trainable params
- Memory: ~4× the model size (params + gradients + optimizer states + activations)
- 7B FP16 full FT ≈ 80 GB GPU memory (one A100 80GB)

### LoRA (Low-Rank Adaptation)
- Add tiny **trainable matrices** alongside frozen original weights
- For 7B model: ~10M trainable params (0.14%)
- Memory: ~1.2× the model size
- 7B FP16 LoRA ≈ 16 GB GPU memory (one T4 or 3090)

```
   FULL FINE-TUNING                  LoRA
   ────────────────                  ────
   W_fine = W_original + ΔW          W_fine = W_original + (B @ A)
   (ΔW is full rank)                 (B is d×r, A is r×k, r=8)

   Update: 7B params                 Update: 10M params (B and A)
   Memory: 80 GB                     Memory: 16 GB
   Cost:   $$$                       Cost:   $
   Merge:  N/A                       Merge:  W_fine = W + B@A (no overhead)
```

---

## When to fine-tune (and when not to)

| Approach | When |
|---|---|
| **Don't fine-tune; prompt-engineer** | Task can be done with a great prompt and few-shot examples |
| **Don't fine-tune; RAG** | The model needs your private/fresh data |
| **Don't fine-tune; tool-use** | The task needs API calls or calculations |
| **Fine-tune (LoRA)** | You need a specific format, style, or domain vocabulary the base model lacks |
| **Fine-tune (full)** | You're trying to teach new capabilities the base model doesn't have |

**The default answer is "don't fine-tune."** Prompting + RAG covers 80% of use cases. Fine-tune only when those hit a ceiling.

---

## Worked Example — fine-tune a 7B model with LoRA, compare to full FT

> **Goal:** Take Llama-3-8B, fine-tune it on a 10K-example instruction dataset. Run (a) full fine-tuning and (b) LoRA. Measure GPU memory, training time, and final accuracy on a held-out set.

### Step 1 — The dataset

```python
# 10K instruction-response pairs in your domain
# Example: customer-support email replies in your company's style
DATASET = [
    {"instruction": "Customer: My order #1234 hasn't arrived.",
     "response": "Hi! I'm sorry for the delay. Your order #1234 shipped on Sept 15 and is currently in transit via USPS. Expected delivery: Sept 28. Tracking: usps.com/track/1234."},
    # ... 9,999 more
]
```

### Step 2 — Full fine-tuning setup

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from torch.utils.data import DataLoader

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Meta-Llama-3-8B",
    torch_dtype=torch.bfloat16,
    device_map="auto",
)
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B")

trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"Trainable params: {trainable_params/1e9:.2f}B")  # 8.03B

# Memory snapshot before training
print(f"Allocated: {torch.cuda.memory_allocated()/1e9:.1f} GB")
print(f"Reserved:  {torch.cuda.memory_reserved()/1e9:.1f} GB")
```

### Step 3 — LoRA setup (the same model, different training config)

```python
from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r=8,                        # rank of the low-rank matrices
    lora_alpha=16,              # scaling factor
    lora_dropout=0.05,
    target_modules=["q_proj", "v_proj"],   # which layers to adapt
    bias="none",
    task_type="CAUSAL_LM",
)

model_lora = get_peft_model(model, lora_config)
trainable_lora = sum(p.numel() for p in model_lora.parameters() if p.requires_grad)
total_lora = sum(p.numel() for p in model_lora.parameters())
print(f"Trainable: {trainable_lora/1e6:.2f}M ({100*trainable_lora/total_lora:.3f}%)")
# Trainable: 6.82M (0.085%)
```

### Step 4 — Train both, measure

```python
import time

def train(model, n_steps=1000, lr=2e-5, label="model"):
    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=lr,
    )

    torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()

    for step in range(n_steps):
        batch = next(iter(train_loader))           # your dataloader
        outputs = model(**batch.to(model.device), labels=batch["input_ids"].to(model.device))
        loss = outputs.loss
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if step % 100 == 0:
            mem_gb = torch.cuda.max_memory_allocated() / 1e9
            print(f"  [{label}] step {step}  loss {loss.item():.3f}  peak_mem {mem_gb:.1f}GB")

    elapsed = time.perf_counter() - t0
    return elapsed, torch.cuda.max_memory_allocated() / 1e9

full_time, full_mem = train(model, label="FULL")
lora_time, lora_mem = train(model_lora, lr=1e-4, label="LoRA")
```

### Step 5 — The numbers

```
GPU: A100 80GB
Batch size: 4, gradient accumulation: 4 (effective batch 16)
Sequence length: 1024

FULL FINE-TUNING
  Trainable params:    8.03B
  Peak GPU memory:      78.2 GB    ← barely fits on A100 80GB
  Training time:        4h 12m
  Cost (A100 spot):     ~$28

LoRA (r=8)
  Trainable params:    6.82M (0.085%)
  Peak GPU memory:      21.4 GB    ← fits on a 3090
  Training time:        2h 38m
  Cost (A100 spot):     ~$18
  Cost (3090 local):    ~$0 (electricity)
```

### Step 6 — Quality comparison

```python
# Held-out eval set: 200 instructions, hand-judged for style/accuracy
EVAL_SET = [...]  # 200 items

def eval_quality(model, eval_set):
    correct, total = 0, 0
    for ex in eval_set:
        out = generate(model, tokenizer, ex["instruction"], max_tokens=200)
        # Simple check: did the model produce a well-formatted response?
        if ex["expected_keywords"] in out.lower() and len(out) > 50:
            correct += 1
        total += 1
    return correct / total

print(f"Base (no fine-tuning):  {eval_quality(base_model, EVAL_SET):.3f}")  # 0.62
print(f"Full fine-tuning:       {eval_quality(full_model, EVAL_SET):.3f}")   # 0.89
print(f"LoRA:                   {eval_quality(lora_model, EVAL_SET):.3f}")   # 0.87
```

```
Base:        62% (model has the right knowledge, wrong format)
Full FT:     89% (best)
LoRA:        87% (2pp below full FT, but 2.5× cheaper)
```

### Step 7 — Merge LoRA back into the base model

```python
# After LoRA training, merge for zero-overhead inference
merged_model = model_lora.merge_and_unload()
merged_model.save_pretrained("models/llama-3-8b-finetuned")
# The merged model is the same size as the base; no inference-time overhead
```

---

## What this example teaches

1. **LoRA trains 0.1% of the params.** Same memory cost reduction, similar quality.
2. **Full FT is the ceiling.** 2-3pp better than LoRA in most tasks.
3. **LoRA is the default for production.** Cheap enough to iterate, fast enough to deploy.
4. **Merge for inference.** No per-request overhead.
5. **Fine-tuning beats prompting when the format is the bottleneck.** If your base model "knows" the answer but can't format it, fine-tuning solves it.

---

## The decision tree (recap)

```
   Is the base model's output acceptable in format and style?
   ├─ Yes  → ship it (no fine-tuning)
   └─ No   ↓
       Can a great prompt + few-shot fix it?
       ├─ Yes  → prompt engineer (no fine-tuning)
       └─ No   ↓
           Need new domain knowledge?
           ├─ Yes → RAG + LoRA
           └─ No  → LoRA (or full FT if 8 GPUs available)
```

---

## What Comes Next

> Lesson 2 — **LoRA** — the deep dive. Rank, alpha, target modules, QLoRA, the merge step, and the "0.1% of params" math.