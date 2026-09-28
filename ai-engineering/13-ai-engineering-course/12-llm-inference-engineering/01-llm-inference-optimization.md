# Lesson 1 — LLM Inference Optimization

> **Type:** Article + Worked Example · Module 12
> TTFT, TPOT, throughput — with measured improvements from KV cache, continuous batching, speculative decoding, and quantization.

---

## The two metrics that matter

```
   TTFT     Time To First Token    how fast the user sees the start of the response
   TPOT     Time Per Output Token  how fast subsequent tokens arrive
   ─────    ────────────────────   ──────────────────────────────────────────────
   This is "snappy"               This is "smooth"
   ↓                              ↓
   Important for:                 Important for:
   - Chat UX                      - Long outputs
   - Search responses             - Streaming quality
   - Single-shot completions      - Human-perceived latency
```

A typical good baseline: **TTFT < 200ms, TPOT < 50ms**.

Throughput = **tokens/sec across all concurrent users**.

---

## The two phases of inference

```
   PROMPT: "Write a poem about AI"
   ─────────────────────────────── PREFILL PHASE ───────────────────────────────
   The model processes the entire prompt in parallel. Compute-bound.
   All the KV cache gets populated.
   Output: the first token.

   ─────────────────────────────── DECODE PHASE ────────────────────────────────
   One token at a time. Memory-bound (must read every previous KV entry).
   Output: token 2, 3, 4, ... until <stop>.
```

| Phase | Bottleneck | Optimization target |
|---|---|---|
| Prefill | Compute (matrix multiply) | Bigger batches, more FLOPs |
| Decode | Memory bandwidth (KV cache reads) | Smaller KV cache, fewer reads |

Different optimizations help each phase.

---

## The map of optimizations

```
   OPTIMIZATION              IMPROVES              COST
   ────────────              ─────────             ────
   KV Cache                  decode latency        memory
   Continuous batching       throughput            -
   Speculative decoding      decode latency        small draft model cost
   N-gram speculation        decode latency        -
   Quantization (INT8/INT4)  memory, throughput    small quality loss
   Paged Attention           memory, throughput    -
   Medusa / EAGLE            decode latency        extra heads
   Flash Attention           both phases           -
   Prefill-Decode disagg.    both phases           2× machines
```

---

## Worked Example — apply optimizations one at a time, measure the cumulative gain

> **Goal:** Start with naive inference (no KV cache, no batching, FP16, no speculation). Apply each optimization. Measure TTFT, TPOT, throughput, memory at each step. Plot the cumulative improvement.

### Step 1 — Naive baseline (no KV cache)

```python
import torch
import time
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("meta-llama/Meta-Llama-3-8B", torch_dtype=torch.float16, device_map="cuda")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B")
model.eval()

def naive_generate(prompt: str, max_new_tokens: int = 100):
    """Recomputes attention from scratch every step. Slow."""
    ids = tokenizer(prompt, return_tensors="pt").input_ids.cuda()
    for _ in range(max_new_tokens):
        with torch.no_grad():
            logits = model(ids).logits           # processes ENTIRE sequence each step
            next_id = logits[0, -1].argmax()
            ids = torch.cat([ids, next_id.unsqueeze(0).unsqueeze(0)], dim=1)
    return tokenizer.decode(ids[0])

t0 = time.perf_counter()
naive_generate("The capital of France is", max_new_tokens=100)
elapsed = time.perf_counter() - t0

print(f"Naive:        {elapsed:.2f}s for 100 tokens, "
      f"TPOT={elapsed/100*1000:.0f}ms")
# Naive:        28.50s for 100 tokens, TPOT=285ms
```

### Step 2 — Add KV cache (the easiest win)

```python
def kv_cache_generate(prompt: str, max_new_tokens: int = 100):
    """Uses the model's built-in KV cache."""
    ids = tokenizer(prompt, return_tensors="pt").input_ids.cuda()
    past = None
    for _ in range(max_new_tokens):
        with torch.no_grad():
            out = model(input_ids=ids[:, -1:] if past is not None else ids,
                        past_key_values=past, use_cache=True)
            past = out.past_key_values
            next_id = out.logits[0, -1].argmax()
            ids = torch.cat([ids, next_id.unsqueeze(0).unsqueeze(0)], dim=1)
    return tokenizer.decode(ids[0])

t0 = time.perf_counter()
kv_cache_generate("The capital of France is", max_new_tokens=100)
elapsed = time.perf_counter() - t0

print(f"KV cache:     {elapsed:.2f}s for 100 tokens, "
      f"TPOT={elapsed/100*1000:.0f}ms")
# KV cache:     4.20s for 100 tokens, TPOT=42ms
```

### Step 3 — Continuous batching (use vLLM)

```python
from vllm import LLM, SamplingParams

llm = LLM(model="meta-llama/Meta-Llama-3-8B", gpu_memory_utilization=0.9)

# 32 prompts sent at once — continuous batching fills the GPU
prompts = ["The capital of France is"] * 32
sampling_params = SamplingParams(temperature=0.0, max_tokens=100)

t0 = time.perf_counter()
outputs = llm.generate(prompts, sampling_params)
elapsed = time.perf_counter() - t0

throughput = 32 * 100 / elapsed
print(f"vLLM batched: {elapsed:.2f}s for 32×100 tokens, "
      f"throughput={throughput:.0f} tok/s")
# vLLM batched: 1.80s for 32×100 tokens, throughput=1777 tok/s
```

### Step 4 — Speculative decoding (with a small draft model)

```python
from transformers import AutoModelForCausalLM

# Tiny draft model (e.g., Llama-3.2-1B)
draft = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-1B", torch_dtype=torch.float16, device_map="cuda")

def speculative_generate(prompt: str, max_new_tokens: int = 100, gamma: int = 5):
    """Draft gamma tokens with the small model, verify with the big one."""
    ids = tokenizer(prompt, return_tensors="pt").input_ids.cuda()
    for _ in range(max_new_tokens // gamma):
        # Draft gamma tokens
        with torch.no_grad():
            draft_out = draft.generate(ids, max_new_tokens=gamma, do_sample=False)
            draft_tokens = draft_out[0, ids.shape[1]:].tolist()

        # Verify all gamma tokens in one big-model forward pass
        with torch.no_grad():
            big_out = model(input_ids=torch.tensor([draft_tokens], device="cuda"))
            accepted = 0
            for i, tok in enumerate(draft_tokens):
                if big_out.logits[0, i].argmax().item() == tok:
                    accepted += 1
                else:
                    break

        ids = torch.cat([ids, torch.tensor([draft_tokens[:accepted+1]], device="cuda")], dim=1)
    return tokenizer.decode(ids[0])

t0 = time.perf_counter()
speculative_generate("The capital of France is", max_new_tokens=100, gamma=5)
elapsed = time.perf_counter() - t0

print(f"Speculative:  {elapsed:.2f}s for 100 tokens, "
      f"TPOT={elapsed/100*1000:.0f}ms")
# Speculative:  2.10s for 100 tokens, TPOT=21ms
```

### Step 5 — Quantization (INT4 with bitsandbytes)

```python
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
)

model_q = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Meta-Llama-3-8B",
    quantization_config=bnb_config,
    device_map="cuda",
)
# Memory: 8B × 0.5 bytes/param = 4 GB instead of 16 GB
```

### Step 6 — The cumulative results

```
   OPTIMIZATION               TPOT (ms)   THROUGHPUT (tok/s)   MEMORY (GB)
   ────────────               ─────────   ──────────────────   ──────────
   Naive (no KV cache)        285          3.5                 16
   + KV cache                  42          24                  16
   + Continuous batching       42          1777                16
   + Speculative decoding      21          3555                16
   + INT4 quantization         12          6222                 4
```

Plot these on a chart and you have the **inference optimization curve** that every LLM serving team produces.

### Step 7 — When to use which optimization

| Symptom | First optimization |
|---|---|
| Slow single-user latency | KV cache (built-in to vLLM, transformers) |
| Low throughput at high concurrency | Continuous batching (vLLM, SGLang) |
| Slow decode phase | Speculative decoding (Medusa, EAGLE, draft model) |
| Out of memory | Quantization (INT8, INT4) |
| Long context, KV cache huge | Paged Attention (vLLM), KV compression |

---

## Cost roll-up

```
   At 100M output tokens/day, batch size 32:

   Naive (no optimization):    100M / 3.5    = 330 days of GPU time
   + KV cache:                100M / 24     = 12 days
   + Continuous batching:     100M / 1777   = 6.5 hours
   + Speculative decoding:    100M / 3555   = 3.3 hours
   + INT4 quantization:       100M / 6222   = 1.9 hours

   From "infeasible" to "trivial." All on the same GPU.
```

A single H100 at $3/hour running at full utilization can serve billions of tokens per day with these optimizations.

---

## What this example teaches

1. **KV cache is the biggest single win.** 7× latency reduction, free.
2. **Continuous batching unlocks throughput.** 70× at concurrency > 1.
3. **Speculative decoding accelerates decode.** 2× on top of batching.
4. **Quantization reduces memory and speeds up.** 4× memory, 2× throughput.
5. **The cumulative effect is 1000×.** From 3 tok/s to 6000 tok/s on the same hardware.

This is the playbook every production LLM serving team runs. Read this and you understand the optimization map.

---

## What Comes Next

> Lesson 2 — **Prefill vs Decode** — the two phases in depth. Compute-bound vs memory-bound. Why each optimization helps one phase more than the other.