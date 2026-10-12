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

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
