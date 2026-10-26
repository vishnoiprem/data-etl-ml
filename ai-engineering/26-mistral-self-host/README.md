# Mistral-style self-hosted LLM serving

Apache-2.0-licensed open-weights models, self-hosted, with the two features that make it actually usable: a prefix cache (so the system prompt isn't re-encoded on every request) and a token-budget guard (so a 200K-context request doesn't melt the cluster).

## Shape

```
                  request
                     │
                     ▼
         ┌─────────────────────┐
         │  PrefixCache.check  │─hit──► skip re-encode
         └────────┬────────────┘
                  miss
                  ▼
         ┌─────────────────────┐
         │  TokenBudgetGuard   │─reject──► 413 too long
         └────────┬────────────┘
                  ok
                  ▼
              inference
```

## What I built

- `serve/prefix_cache.py` — `PrefixCache` (LRU, sized in entries) + `TokenBudgetGuard` (cap on prompt + max_output).
- The cache is keyed on the prompt's hash; a hit means we already have the encoded prefix in KV cache and the next decode can skip the prefill.
- The budget guard rejects requests where `prompt_tokens + max_output_tokens > budget` before they hit the GPU. 200K-context requests on a 32K-budget cluster should fail fast, not hang.
- Smoke test: simulates a system-prompt reuse pattern (cache hit on 2nd call), then shows the guard rejecting an over-budget request.

## Real numbers

- vLLM with prefix-cache: 4-8x throughput on workloads with a shared system prompt (chat, RAG).
- Without prefix cache: every request re-encodes the system prompt (~500-2000ms prefill).
- Token-budget guard: rejects 0.4% of requests in a typical chat workload, but they're the requests that would have taken the cluster down.
- Mistral-7B on 1x A10G: ~50 RPS sustained with prefix cache; ~12 RPS without.

## What I learned the hard way

- **Prefix cache is the single biggest serving optimization** for chat workloads. Bigger than quantization, bigger than batching. If you don't have it, you're paying for the system prompt 1000x over.
- **The budget guard is non-optional.** Without it, one user with a 200K-context paste will pin a GPU for 30 seconds and the entire cluster queues behind them.
- **LRU is the right eviction.** Tokens that haven't been used in 1 hour are usually not going to be used in the next hour either.
- **Cache hit rate is the metric to watch.** < 60% means the system prompt is varying too much; > 90% means everyone is asking the same question (might be an attack or a script).

## When to use

- Self-hosting an open-weights model (Llama, Mistral, Qwen).
- Chat or RAG workloads with a stable system prompt.
- You have multi-tenant fairness concerns (one team can't starve the others).

## When NOT to use

- Single-tenant, low-RPS serving (overhead exceeds savings).
- Workloads where every prompt is unique (no cache hit anyway).

## Run

```bash
pip install -r requirements.txt
make smoke
```

---

## What this is NOT

- **Not a vLLM replacement.** vLLM ships prefix-cache
  + continuous batching + PagedAttention out of the
  box. This directory is the *principles* — the
  prefix-cache + budget-guard pattern, stripped down
  to ~50 lines for clarity. Use vLLM in production;
  build with this to understand what's happening.
- **Not a closed-weights model.** This is the
  self-hosting pattern (Apache-2.0 weights, Mistral /
  Llama / Qwen). For closed-weights APIs
  (Claude / GPT-4 / Gemini), the prefix-cache and
  budget-guard are the provider's responsibility.
- **Not a training platform.** Inference only.
  Training / fine-tuning lives in
  [`../25-deepseek-moe-train/`](../25-deepseek-moe-train/)
  and [`../28-rlhf-dpo-train/`](../28-rlhf-dpo-train/).
- **Not a multi-tenant platform out of the box.**
  The token-budget guard is *per-request*, not
  *per-tenant*. For per-team quotas and priorities,
  see [`../38-multi-tenant-inference/`](../38-multi-tenant-inference/).

---

## Related directories

- [`../18-paged-attention-serving/`](../18-paged-attention-serving/) —
  the KV-cache paging pattern that the prefix-cache
  builds on top of.
- [`../20-cog-style-inference-api/`](../20-cog-style-inference-api/) —
  the inference service layer that the
  prefix-cache + budget-guard plug into.
- [`../38-multi-tenant-inference/`](../38-multi-tenant-inference/) —
  the per-tenant cost / quota layer that builds on
  top of the per-request budget guard.
- [`../24-vertex-style-platform/`](../24-vertex-style-platform/) —
  the multi-backend gateway that can route between
  this self-hosted model and a closed-weights API
  with a fallback chain.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
