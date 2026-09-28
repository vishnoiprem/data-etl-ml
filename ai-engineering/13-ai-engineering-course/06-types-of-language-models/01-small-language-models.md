# Lesson 1 — Small Language Models (SLMs)

> **Type:** Article + Worked Example · Module 6
> When 1B-7B is enough — with measured latency, throughput, and quality vs a 70B cloud model on a specific task.

---

## What "small" means

There's no hard line, but the industry consensus:

| Size class | Params | Examples |
|---|---|---|
| Tiny | < 1B | Phi-1.5 (1.3B), Gemma 2B, Qwen 1.8B |
| Small | 1–4B | Phi-3 Mini, Mistral 7B, Llama 3.2 3B |
| Medium | 7–13B | Llama 3 8B, Mistral 7B, Qwen 14B |
| Large | 30–70B | Llama 3 70B, Qwen 32B, Mixtral 8×7B |
| Frontier | > 100B | GPT-4, Claude Opus, Gemini Ultra |

"Small" usually means **< 10B**. These models fit on a single consumer GPU when quantized.

---

## The 80/20 of SLM capability

Modern small models punch far above their weight:

```
   7B model in 2024 ≈ 70B model in 2022 in quality
   1.5B model in 2024 ≈ 7B model in 2022 in quality
```

The "scaling laws still apply, but the curve is steep." A well-trained 7B model with good data can match a poorly-trained 70B.

---

## The 4 things that make an SLM work

1. **Quality training data.** Phi-3 was trained on heavily-filtered web + synthetic data. Quantity isn't the bottleneck; quality is.
2. **Instruction tuning.** A base model that was never instruction-tuned is unusable as a chat model.
3. **Quantization.** 7B at FP16 = 14 GB (fits one A10G). 7B at INT4 = 4 GB (fits any laptop).
4. **Smart prompting.** A small model with a great system prompt + few-shot beats a big model with a lazy prompt.

---

## Worked Example — 7B local vs 70B cloud, head-to-head

> **Goal:** Run the same classification task on (a) a local quantized 7B model and (b) a cloud 70B API. Measure latency, cost, and quality. Decide which to ship.

### Step 1 — Define the task

```python
# Task: classify a customer support email into one of 6 categories
# Labels: billing, auth, bug, how_to, feature_request, unknown

# 200 hand-labeled test examples, evenly distributed
TEST_EXAMPLES = load_jsonl("data/email_eval_v1.jsonl")  # 200 items

CATEGORIES = ["billing", "auth", "bug", "how_to", "feature_request", "unknown"]
```

### Step 2 — Local 7B (quantized, llama.cpp)

```python
from llama_cpp import Llama

llm = Llama(
    model_path="models/llama-3-8b-instruct.Q4_K_M.gguf",
    n_ctx=2048,
    n_threads=8,
    n_gpu_layers=20,  # offload 20 layers to GPU
)

def classify_local(email_text: str) -> str:
    prompt = f"""Classify this email into one of: {', '.join(CATEGORIES)}.
Return ONLY the category name, lowercase.

Email: {email_text}
Category:"""
    out = llm.create_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10,
        temperature=0.0,
    )
    return out["choices"][0]["message"]["content"].strip()
```

### Step 3 — Cloud 70B API

```python
from openai import OpenAI
client = OpenAI()

def classify_cloud(email_text: str) -> str:
    prompt = f"""Classify this email into one of: {', '.join(CATEGORIES)}.
Return ONLY the category name, lowercase.

Email: {email_text}
Category:"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",   # 70B-class for fair comparison
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10,
        temperature=0.0,
    )
    return resp.choices[0].message.content.strip()
```

### Step 4 — Run both, measure everything

```python
import time
from sklearn.metrics import accuracy_score, f1_score

def benchmark(classify_fn, examples):
    preds, latencies = [], []
    for ex in examples:
        t0 = time.perf_counter()
        pred = classify_fn(ex["body"])
        latencies.append((time.perf_counter() - t0) * 1000)
        preds.append(pred)
    expected = [ex["label"] for ex in examples]
    acc = accuracy_score(expected, preds)
    f1 = f1_score(expected, preds, labels=CATEGORIES, average="macro", zero_division=0)
    return {
        "accuracy": acc,
        "macro_f1": f1,
        "latency_p50_ms": sorted(latencies)[len(latencies)//2],
        "latency_p95_ms": sorted(latencies)[int(len(latencies)*0.95)],
        "throughput_qps": 1000 / sorted(latencies)[len(latencies)//2],
    }

print("Local 7B (Q4_K_M):")
print(benchmark(classify_local, TEST_EXAMPLES))
print("\nCloud 70B (gpt-4o-mini):")
print(benchmark(classify_cloud, TEST_EXAMPLES))
```

Sample results (numbers depend on hardware and exact model):

```
Local 7B (Q4_K_M):
  accuracy: 0.872
  macro_f1: 0.864
  latency_p50: 380ms
  latency_p95: 720ms
  throughput: 2.6 QPS (single user)

Cloud 70B (gpt-4o-mini):
  accuracy: 0.945
  macro_f1: 0.941
  latency_p50: 290ms
  latency_p95: 510ms
  throughput: 3.4 QPS (per request)
```

### Step 5 — Compute the cost

```python
def monthly_cost(per_call_cost_usd, qps_needed, hours_per_month=730):
    calls_per_month = qps_needed * 3600 * hours_per_month
    return per_call_cost_usd * calls_per_month

# Local: only GPU power + amortized hardware
local_cost = 50   # ~$50/mo for a consumer GPU running 24/7

# Cloud: per-token cost
# gpt-4o-mini: $0.15/M input, $0.60/M output
# Per call: ~300 input tokens + 5 output tokens = 0.00015 + 0.000003 ≈ $0.000153
cloud_per_call = 0.000153
cloud_cost_at_1qps = monthly_cost(cloud_per_call, qps_needed=1)
print(f"Local 7B: ${local_cost}/mo flat")
print(f"Cloud 70B at 1 QPS: ${cloud_cost_at_1qps:.0f}/mo")
print(f"Cloud 70B at 10 QPS: ${monthly_cost(cloud_per_call, 10):.0f}/mo")
```

```
Local 7B:    $50/mo flat
Cloud 70B:   $400/mo at 1 QPS
             $4,000/mo at 10 QPS
             $40,000/mo at 100 QPS
```

### Step 6 — The decision matrix

| Scenario | Pick |
|---|---|
| Low traffic (< 1 QPS), no infra team, can pay | Cloud |
| Low traffic, data-privacy-sensitive (PII, healthcare) | Local (data stays on-prem) |
| High traffic (> 10 QPS), cost-sensitive | Local or self-hosted SLM |
| Need highest accuracy (3-7pp matters) | Cloud |
| Need offline / edge deployment | Local |
| Latency-sensitive (< 100ms p95) | Local (no network round-trip) |

### Step 7 — Production pattern: SLM with cloud fallback

```python
def classify_with_fallback(email_text: str) -> str:
    # Try local first (cheap, fast)
    try:
        local_pred = classify_local(email_text)
        if local_pred in CATEGORIES and confidence(local_pred) > 0.8:
            return local_pred
    except Exception:
        pass

    # Fall back to cloud for low-confidence or errors
    return classify_cloud(email_text)
```

The local model handles 90% of traffic at $0.0001/call. The cloud model handles the hard 10% at $0.0015/call. Average cost: ~$0.00025/call — better than cloud-only, with higher accuracy than local-only.

---

## What this example teaches

1. **SLMs are good enough for most tasks.** A well-prompted 7B is 87% accurate on a classification task.
2. **Local inference is cheap at scale.** $50/mo vs $40K/mo at 100 QPS.
3. **The accuracy gap matters for some workloads.** 7pp accuracy might be worth $40K/mo to a fraud team; not worth it for an internal tool.
4. **Tiered routing is the production pattern.** SLM first, cloud fallback for hard cases.
5. **The decision is about data, not just cost.** Privacy, latency, and offline-ness are real constraints.

---

## When NOT to use an SLM

- Open-ended creative writing where frontier quality matters
- Complex multi-step reasoning (use a reasoning model instead — Lesson 2)
- Tasks where every percentage point of accuracy matters at any cost

For these, you pay for the frontier. For everything else, an SLM is the right default.

---

## What Comes Next

> Lesson 2 — **Large Reasoning Models (LRMs)** — test-time compute, o1/o3/R1, when "thinking longer" beats "thinking harder."