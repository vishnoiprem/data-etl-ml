# Codebook Exercises — Section 2: Production Patterns

> **Paired exercises for [`../ai-engineer-codebook.md` § 2](../ai-engineer-codebook.md#section-2-production-patterns).**
> These turn reference snippets into active practice. For each reference snippet in the codebook, here are 3-5 challenges that force you to modify, extend, and break the code.

---

## How to use these

1. Open the reference snippet in [`../ai-engineer-codebook.md`](../ai-engineer-codebook.md) — Section 2 (Production Patterns)
2. Read the snippet once
3. Do the exercises below IN ORDER — each builds on the previous
4. For each exercise, write the code, run it, note what you learned

**Time per exercise:** 15-25 min.
**Total time for this section:** 4-6 hours.

---

## Snippet 2.1 — Retry with Exponential Backoff

**Reference:** [`../ai-engineer-codebook.md#21-retry-with-exponential-backoff`](../ai-engineer-codebook.md#21-retry-with-exponential-backoff)

### Exercise 2.1.1: Add jitter to backoff

Pure exponential backoff creates thundering-herd problems when many clients retry at the same moment. Add full jitter:

```python
import random
# TODO: Modify the retry helper:
# - Replace `wait = 2 ** attempt` with `wait = random.uniform(0, 2 ** attempt)` (full jitter)
# - Or use "equal jitter": `wait = 2 ** attempt + random.uniform(0, 2 ** attempt)`
# - Or use decorrelated jitter: `wait = min(cap, random.uniform(base, prev_wait * 3))`
# Compare: which spread is best? What's the worst-case wait?
```

**Architect insight:** AWS Architecture Blog recommends full jitter for distributed systems. Equal jitter reduces max wait. Decorrelated jitter is best for tight latency SLOs.

### Exercise 2.1.2: Distinguish retryable from non-retryable errors

Don't retry everything — some errors are permanent:

```python
from openai import RateLimitError, APIError, BadRequestError, AuthenticationError
# TODO: Build a retry helper that:
# - RETRIES: RateLimitError (429), APIError (5xx), Timeout
# - DOES NOT RETRY: BadRequestError (400), AuthenticationError (401)
# - Logs every retry decision
# Use a RetryDecision enum: RETRY, FAIL, RETRY_THEN_FAIL
```

**Architect insight:** Retrying on `BadRequestError` wastes time AND money. The model won't suddenly produce valid input.

### Exercise 2.1.3: Add a circuit breaker

After 5 consecutive failures, stop calling the API for 60s. This protects you from cascading outages:

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout_s=60):
        # TODO: track failures, open the circuit after threshold
        # call() should raise CircuitOpenError if breaker is open
        # Auto-reset after reset_timeout_s
        pass

# Wrap your retry helper:
@circuit_breaker
def call_llm(...):
    ...
```

**Architect insight:** Circuit breakers protect downstream. If OpenAI has an outage, your circuit opens, you fail fast, return a cached response (if you have one), and alert.

### Exercise 2.1.4: Per-request retry budget

A single user shouldn't burn 1000 retries. Cap total retries per request:

```python
# TODO: Add a retry budget to a request context:
# - Each request starts with retry_budget = 10
# - Each retry decrements budget
# - When budget hits 0, raise (don't retry)
# - Log remaining budget per request
# This prevents one misbehaving user from exhausting your retry pool.
```

---

## Snippet 2.2 — Fallback to Different Models

### Exercise 2.2.1: Build a quality-aware fallback chain

```python
# TODO: If primary model returns low-confidence or low-quality output,
# fall back to the next in chain. Chain order:
# [gpt-4o-mini, gpt-4o, claude-3-5-sonnet, gemini-pro]
# "Low confidence" = response has "I don't know" or similar
# Log every fallback with the reason.
```

### Exercise 2.2.2: Cost-aware fallback

```python
PRIMARY = ("gpt-4o-mini", 0.15, 0.60)
FALLBACK = ("gpt-4o", 2.50, 10.00)
# TODO: For cheap tasks (classification, extraction), only use mini.
# For hard tasks (reasoning, generation), use gpt-4o.
# Build a `pick_model(task_complexity)` function.
# Track cost savings from routing.
```

### Exercise 2.2.3: Multi-vendor fallback

```python
# TODO: If OpenAI is down (5xx for 30s), switch to Anthropic.
# If Anthropic is down too, switch to local Llama 3 70B.
# Use a /health endpoint per provider. Track provider uptime.
# This is what big companies do to avoid vendor lock-in.
```

---

## Snippet 2.3 — Token Counting & Cost Tracking

### Exercise 2.3.1: Per-user cost dashboard

```python
# TODO: Track cost per user_id, not just per request.
# Build a dict: {user_id: total_cost, request_count, last_request_at}
# Expose a GET /admin/cost?user_id=X endpoint (admin-only)
# Add a budget: if user.monthly_cost > $X, reject new requests
# (or charge overage).
```

### Exercise 2.3.2: Alert on cost anomalies

```python
# TODO: If a single request costs > $1 (or > 10x your avg),
# alert (log + email/Slack). This catches runaway loops and bugs.
# Build a sliding-window cost baseline. Alert if current > 5x baseline.
```

### Exercise 2.3.3: Cost attribution across services

```python
# TODO: Tag every LLM call with a service name (e.g., "rag", "agent", "summary")
# Then build a cost-per-service report.
# Which service is the biggest contributor? Where to optimize first?
```

---

## Snippet 2.4 — Async Batch Processing

### Exercise 2.4.1: Batch with controlled concurrency

```python
import asyncio
# TODO: Process 100 documents in parallel, but limit to 10 concurrent LLM calls.
# Use asyncio.Semaphore(10). For each doc, await a process() coroutine.
# Measure: how much faster than sequential? How much higher error rate?
```

### Exercise 2.4.2: Failed batch per item

```python
# TODO: If one item in the batch fails, don't fail the whole batch.
# Use return_exceptions=True in asyncio.gather.
# Collect successes and failures separately.
# Retry just the failures.
```

### Exercise 2.4.3: Batch progress tracking

```python
# TODO: For a batch of 100 docs, emit progress events:
# {"done": 25, "total": 100, "errors": 2, "eta_s": 60}
# Stream these to the client via SSE so the UI shows a progress bar.
```

---

## Snippet 2.5 — Streaming with FastAPI

### Exercise 2.5.1: SSE endpoint with structured events

```python
# TODO: Build a /chat/stream SSE endpoint that sends:
# - event: token       data: "..."
# - event: done        data: {"total_tokens": 250}
# - event: error       data: {"message": "..."}
# Use sse-starlette or StreamingResponse with media_type="text/event-stream"
```

### Exercise 2.5.2: Cancel a stream mid-response

```python
# TODO: If the client disconnects, stop the LLM stream.
# Use request.is_disconnected() in a loop.
# (You can't truly cancel an in-flight OpenAI request, but you can stop iterating.)
# Test with a slow stream and a client that disconnects at 1s.
```

### Exercise 2.5.3: Stream with token-level cost tracking

```python
# TODO: As tokens stream, accumulate cost.
# Send {"cost_so_far": 0.001} events every 50 tokens.
# Send a final {"total_cost": 0.05} event on done.
```

---

## Snippet 2.6 — Response Caching (Redis)

### Exercise 2.6.1: Cache by prompt hash

```python
import hashlib, json
import redis
# TODO: Cache every (model, system_prompt, user_prompt, temperature) → response
# Key: sha256(json.dumps({"model": m, "sys": s, "user": u, "temp": t}))
# TTL: 1 hour for chat, 24 hours for embeddings, 7 days for RAG retrieval
# Measure: cache hit rate over 1000 requests.
```

### Exercise 2.6.2: Cache stampede protection

```python
# TODO: If 1000 users ask the same question at once, only one hits OpenAI.
# Use a Redis lock (SETNX) with 30s expiry.
# If lock fails, poll Redis for the cached result (or compute yourself).
```

### Exercise 2.6.3: Smart cache invalidation

```python
# TODO: When a new doc is uploaded, invalidate all cache entries for that user's RAG queries.
# When the system prompt changes, invalidate everything.
# When the model version changes, invalidate everything.
# Use tagged keys: cache:{tag}:{hash}
```

---

## Snippet 2.7 — Semantic Cache (GPTCache)

### Exercise 2.7.1: Compare exact vs semantic cache hit rate

```python
# TODO: Run 1000 paraphrased questions ("What's the weather?" vs "How's the weather today?")
# Exact cache: ~0% hit rate
# Semantic cache: 80%+ hit rate
# What's the false-positive rate? (different intent, similar text)
```

### Exercise 2.7.2: Threshold tuning

```python
# TODO: Tune the semantic similarity threshold.
# 0.95+: only near-exact matches
# 0.85+: similar but not identical
# 0.75+: very loose
# Find the sweet spot for your domain: high recall (catches more) vs precision (no wrong answers).
```

---

## Cross-cutting challenges (Mid+)

### Challenge A: Build a "smart retry" with budget + breaker

```python
# TODO: Combine exercises 2.1.3 and 2.1.4:
# - Per-request retry budget (10)
# - Global circuit breaker (5 consecutive)
# - Per-endpoint breaker (so OpenAI being slow doesn't kill your Anthropic calls)
# Log every decision. Alert when breakers open.
```

### Challenge B: Build a cost-aware router

```python
# TODO: Build a router that picks the cheapest model that can handle a request:
# - Easy classification → gpt-4o-mini
# - Hard reasoning → gpt-4o
# - Long context (>50K tokens) → claude-3-5-sonnet
# - Privacy-sensitive → local llama
# Track: how much did routing save you?
```

### Challenge C: Build a degradation ladder

```python
# TODO: When OpenAI is degraded, automatically degrade your service:
# 1. First: return cached responses (cache hit rate matters now)
# 2. Then: switch to cheaper model (lose quality, stay up)
# 3. Then: switch to local model (lose quality, no cost)
# 4. Then: return "service degraded" error
# Implement this as a fallback chain.
```

---

## Architect-level reflections (Senior+)

After completing these exercises, write a 1-page design doc answering:

1. **What's your retry strategy?** (exponential backoff with jitter, max retries, what's retryable)
2. **What's your fallback chain?** (which models, in what order, on what trigger)
3. **What's your circuit-breaker policy?** (failure threshold, reset timeout)
4. **How do you budget retries per request?**
5. **How do you cache? When do you invalidate?**
6. **How do you track cost per user / per service?**
7. **What's your runbook when OpenAI has an outage?**
8. **How do you alert on cost anomalies?**

Save these answers. They're the difference between a toy and a production system.

---

## What's next

- Pair with [`../../practice/level-2-production/`](../../practice/level-2-production/) for the deeper labs
- Move to `section-3-prompt-engineering-exercises.md` for prompt patterns
- See [`../../PRACTICE-GUIDE.md`](../../PRACTICE-GUIDE.md) for the full learning path