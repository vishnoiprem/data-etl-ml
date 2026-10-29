# Codebook Exercises — Section 10: Cheat Sheets

> **Paired exercises for [`../ai-engineer-codebook.md` § 10](../ai-engineer-codebook.md#section-10-cheat-sheets).**
> These turn reference snippets into active practice. For each reference snippet in the codebook, here are 3-5 challenges that force you to modify, extend, and break the code.

---

## How to use these

1. Open the reference snippet in [`../ai-engineer-codebook.md`](../ai-engineer-codebook.md) — Section 10 (Cheat Sheets)
2. Read the snippet once
3. Do the exercises below IN ORDER — each builds on the previous
4. For each exercise, make a decision, defend it with numbers

**Time per exercise:** 15-25 min.
**Total time for this section:** 4-6 hours.

---

## Snippet 10.1 — Model Selection Guide

**Reference:** [`../ai-engineer-codebook.md#101-model-selection-guide`](../ai-engineer-codebook.md#101-model-selection-guide)

### Exercise 10.1.1: Choose a model for 5 use cases

```python
USE_CASES = [
    {"name": "extract name from email", "max_latency_ms": 200, "max_cost_per_1k": 0.01},
    {"name": "summarize a 10-page legal doc", "max_latency_ms": 10000, "max_cost_per_1k": 1.0},
    {"name": "real-time chat for a chatbot", "max_latency_ms": 1500, "max_cost_per_1k": 0.5},
    {"name": "generate 1000 marketing emails", "max_latency_ms": 60000, "max_cost_per_1k": 5.0},
    {"name": "code a 200-line feature", "max_latency_ms": 30000, "max_cost_per_1k": 2.0},
]
# TODO: For each, pick the right model. Justify with latency + cost.
# Build a pick_model(use_case) -> str function.
```

### Exercise 10.1.2: Quality vs cost trade-off

```python
# TODO: For "summarize a 10-page legal doc":
# - gpt-4o-mini: $0.05/doc, quality 7/10
# - gpt-4o: $0.50/doc, quality 9/10
# - claude-3-5-sonnet: $0.60/doc, quality 9.5/10
# When is the 2x quality worth 10x cost? Run a user study.
```

### Exercise 10.1.3: Build a model router

```python
# TODO: Smart routing:
# - "Classify this as positive/negative" -> gpt-4o-mini
# - "Write me an essay" -> gpt-4o
# - "Long doc" (>50K tokens) -> claude-3-5-sonnet
# Implement a router that picks the right model per request.
# Track savings vs always using the best model.
```

### Exercise 10.1.4: Open-source vs proprietary

```python
# TODO: For your use case, compare:
# - GPT-4o: $2.50/1M in, $10/1M out
# - Llama 3 70B self-hosted: ~$0.50/1M (amortized GPU cost)
# - Llama 3 8B self-hosted: ~$0.10/1M
# What's the breakeven monthly volume? When is self-hosting worth it?
```

---

## Snippet 10.2 — Pricing Reference (per 1M tokens, 2026)

**Reference:** [`../ai-engineer-codebook.md#102-pricing-reference-per-1m-tokens-2026`](../ai-engineer-codebook.md#102-pricing-reference-per-1m-tokens-2026)

### Exercise 10.2.1: Model your monthly bill

```python
# TODO: For your capstone (1 of the 5):
# - How many requests per user per day?
# - Average input tokens?
# - Average output tokens?
# - Which model?
# Calculate: monthly cost per user, monthly cost at 100 users, 1K users, 10K users.
# At what price point are you profitable?
```

### Exercise 10.2.2: Optimize the largest cost

```python
# TODO: Look at your monthly bill by component:
# - LLM generation: 60% of cost
# - Embeddings: 20%
# - Vector DB: 10%
# - Other: 10%
# Where can you cut 50%? Probably LLM (use cheaper model, use caching).
```

### Exercise 10.2.3: Prompt caching savings

```python
# TODO: If you have a stable system prompt (5K tokens) and 1000 queries/day:
# - Without caching: 5K * 1000 = 5M tokens/day
# - With 90% caching: 500K tokens/day
# - Savings: 4.5M tokens × $0.15/1M = $675/day = $20K/month
# Estimate: how much would prompt caching save you?
```

### Exercise 10.2.4: Compare 5 model price points

```python
# TODO: For a typical 1500-token input + 500-token output:
# - gpt-4o-mini:  $0.0002 + $0.0003 = $0.0005
# - gpt-4o:        $0.0038 + $0.0050 = $0.0088
# - claude-3-5-haiku: $0.0008 + $0.004  = $0.0048
# - claude-3-5-sonnet: $0.003 + $0.015 = $0.018
# - o1-mini: $0.003 + $0.012 = $0.015
# 1000 such requests per day: $0.50 - $18. Trade-off: quality vs cost.
```

### Exercise 10.2.5: Hidden costs

```python
# TODO: Beyond LLM tokens, what else costs money?
# - Vector DB ($/pod-hour or $/GB)
# - Postgres ($/month or $/row)
# - Hosting ($/container-hour)
# - Whisper (audio minutes)
# - Tavily (search queries)
# - Sentry (events)
# - Email (recipients)
# - S3 (storage + egress)
# Add all of these to your cost model. Where are you surprised?
```

---

## Snippet 10.3 — Common Latencies (p50)

**Reference:** [`../ai-engineer-codebook.md#103-common-latencies-p50`](../ai-engineer-codebook.md#103-common-latencies-p50)

### Exercise 10.3.1: Latency budget

```python
# TODO: For a "real-time chat" feature with 1500ms target:
# - User input processing: 50ms
# - Embedding the question: 100ms
# - Vector search: 50ms
# - LLM generation (first token): 300ms
# - LLM generation (full response, 200 tokens): 1000ms
# - Total: 1500ms
# You're at the limit. Where can you cut?
# Hint: streaming helps perceived latency more than actual latency.
```

### Exercise 10.3.2: Measure YOUR latencies

```python
# TODO: For each external call, measure p50 and p99:
# - OpenAI chat completion
# - OpenAI embedding
# - Pinecone query
# - Tavily search
# - Your Postgres query
# - Your internal services
# Build a latency waterfall. Find the biggest contributors.
```

### Exercise 10.3.3: Latency optimization techniques

```python
# TODO: For each slow operation, try a fix:
# - LLM call: stream the response, parallel function calls, smaller model
# - Vector search: cache, smaller k, lower dim
# - Postgres: index, denormalize, materialize
# - Network: CDN, regional, preconnect
# Measure: before/after p50 and p99.
```

### Exercise 10.3.4: When is latency "good enough"?

```python
# TODO: Different features have different SLOs:
# - Real-time chat: < 2s to first token
# - Document upload: < 30s end-to-end
# - Report generation: < 5min
# - Batch indexing: hours
# Define SLOs per feature. Don't over-engineer the slow ones.
```

---

## Snippet 10.4 — Token Limits

**Reference:** [`../ai-engineer-codebook.md#104-token-limits`](../ai-engineer-codebook.md#104-token-limits)

### Exercise 10.4.1: Stay under the limit

```python
# TODO: For each model, know the limit:
# - gpt-4o-mini: 128K tokens
# - gpt-4o: 128K tokens
# - claude-3-5-sonnet: 200K tokens
# - gemini-1.5-pro: 2M tokens
# Build a helper: truncate_to_limit(prompt, model) that fits.
# Test: 200K-token prompt to gpt-4o. Verify it works (or fails gracefully).
```

### Exercise 10.4.2: Lost in the middle

```python
# TODO: Models do worse on info in the middle of long contexts.
# Test: ask questions about the start, middle, end of a 100K-token doc.
# Plot: accuracy vs position. You'll see a U-shape.
# Mitigate: put the most important info at the start or end.
```

### Exercise 10.4.3: Chunking to fit

```python
# TODO: For RAG with a 128K context:
# - Reserve 2K for the system prompt
# - Reserve 500 for the user question
# - 125.5K for retrieved chunks
# If top-5 chunks are too big, use top-3. Or summarize first.
# Always know your budget.
```

### Exercise 10.4.4: Cost vs context length

```python
# TODO: Bigger context = bigger bill.
# Compare a 1K vs 100K prompt on the same model:
# - 1K: $0.0025 input
# - 100K: $0.25 input
# Use the smallest context that still works. Measure: at what context length does accuracy plateau?
```

---

## Cross-cutting challenges (Mid+)

### Challenge A: Build a "model decision matrix"

```python
# TODO: For your product, build a decision matrix:
# - 5 candidate models
# - 5 criteria: cost, latency, quality, context length, features
# - Weight each criterion
# - Score each model
# - Pick the winner
# Repeat quarterly. The model landscape changes fast.
```

### Challenge B: Capstone cost model

```python
# TODO: For one of the 5 capstones, build a full cost model:
# - Per-request cost (LLM + vector + storage)
# - Per-user monthly cost
# - At 100, 1K, 10K, 100K users
# - At which price point is the unit economics healthy?
# Write a 1-page report.
```

### Challenge C: Capstone latency budget

```python
# TODO: For one of the 5 capstones, build a full latency budget:
# - Per-endpoint p50 / p95 / p99
# - Identify the slowest dependency
# - Propose 3 optimizations
# - Estimate the savings of each
```

---

## Architect-level reflections (Senior+)

After completing these exercises, write a 1-page design doc answering:

1. **Default model?** (gpt-4o-mini for cost, gpt-4o for quality, when to use which)
2. **Fallback model?** (when primary is down or rate-limited)
3. **Self-hosted open-source?** (when does the math work out?)
4. **Pricing strategy?** (per-seat, per-request, per-token, hybrid)
5. **Latency SLOs?** (per feature, not one number for the whole app)
6. **Context length strategy?** (how much context you actually need, what's the cost)
7. **Cost at 100, 1K, 10K, 100K users?** (chart the curve)
8. **What costs surprised you?** (the line items you didn't expect)
9. **How do you track cost per feature?** (tag every LLM call)
10. **How do you stay on top of model changes?** (new models, new pricing, new capabilities)

Save these answers. Numbers are how you defend decisions to your team, your users, and your investors.

---

## What's next

- Pair with [`../../practice/level-10-cheatsheets/`](../../practice/level-10-cheatsheets/) for the deeper labs
- See [`../../PRACTICE-GUIDE.md`](../../PRACTICE-GUIDE.md) for the full learning path
- Start your capstone from [`../../capstone-starters/`](../../capstone-starters/)