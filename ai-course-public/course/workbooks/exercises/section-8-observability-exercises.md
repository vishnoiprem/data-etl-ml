# Codebook Exercises — Section 8: Observability

> **Paired exercises for [`../ai-engineer-codebook.md` § 8](../ai-engineer-codebook.md#section-8-observability).**
> These turn reference snippets into active practice. For each reference snippet in the codebook, here are 3-5 challenges that force you to modify, extend, and break the code.

---

## How to use these

1. Open the reference snippet in [`../ai-engineer-codebook.md`](../ai-engineer-codebook.md) — Section 8 (Observability)
2. Read the snippet once
3. Do the exercises below IN ORDER — each builds on the previous
4. For each exercise, instrument something, break it, find it via the observability tool

**Time per exercise:** 20-30 min.
**Total time for this section:** 4-6 hours.

---

## Snippet 8.1 — LangSmith Setup

**Reference:** [`../ai-engineer-codebook.md#81-langsmith-setup`](../ai-engineer-codebook.md#81-langsmith-setup)

### Exercise 8.1.1: Trace a simple LLM call

```python
# TODO: Set LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY=...
# Run a simple chat completion. Open LangSmith.
# Verify: you see the LLM call, the input, the output, latency, tokens, cost.
```

### Exercise 8.1.2: Trace a RAG pipeline

```python
# TODO: Run a RAG query with LangChain. Open LangSmith.
# Verify: you see the full chain — retriever, prompt template, LLM call, output parser.
# Click into the retriever to see the retrieved chunks.
# This is how you debug "why is RAG giving bad answers?"
```

### Exercise 8.1.3: Trace an agent

```python
# TODO: Run a ReAct agent with a tool. Open LangSmith.
# Verify: you see every step — thought, action, observation, next thought.
# This is the only way to debug agents. Don't ship an agent without it.
```

### Exercise 8.1.4: Build an eval dataset in LangSmith

```python
# TODO: Upload 50 (input, expected_output) pairs to a LangSmith dataset.
# Run your LLM chain on the dataset.
# View: per-example latency, cost, output diff.
# Re-run after every prompt change. Catch regressions.
```

### Exercise 8.1.5: Compare two prompts

```python
# TODO: Run the same eval dataset with prompt A and prompt B.
# LangSmith shows: which is better on which inputs?
# Pick the winner. Track in your "prompt changelog".
```

---

## Snippet 8.2 — Custom Logging

**Reference:** [`../ai-engineer-codebook.md#82-custom-logging`](../ai-engineer-codebook.md#82-custom-logging)

### Exercise 8.2.1: JSON structured logs

```python
import json, logging
# TODO: Replace print() / basicConfig() with JSON logs:
# {"ts": "...", "level": "INFO", "msg": "...", "user_id": "...", "request_id": "...", "latency_ms": 123}
# Use python-json-logger or write a custom formatter.
# Verify: each line is valid JSON, parseable by log aggregators.
```

### Exercise 8.2.2: Log the right things

```python
# TODO: For every LLM call, log:
# - model
# - input_tokens, output_tokens
# - cost_usd
# - latency_ms
# - user_id, request_id
# - error (if any)
# - input_hash (so you can dedupe but not log PII)
# Build a helper: @log_llm_call that does this automatically.
```

### Exercise 8.2.3: Correlation IDs

```python
# TODO: Generate a request_id at the edge. Pass it through:
# - HTTP middleware → all log lines
# - LLM calls (as a tag in LangSmith)
# - Database queries (as a column or context)
# - Error reports (Sentry tag)
# Now you can search across all systems for one user request.
```

### Exercise 8.2.4: Sensitive data redaction

```python
# TODO: Before logging, redact:
# - email addresses
# - API keys
# - credit card numbers
# - phone numbers
# Use a regex-based filter. Test: log a message with all of these, verify they appear as [REDACTED].
# Never log PII. GDPR + common sense.
```

### Exercise 8.2.5: Log levels done right

```python
# TODO: Use levels correctly:
# - DEBUG: variable values, query results (off in prod)
# - INFO: request started, request completed, important events
# - WARNING: retry, fallback, deprecated API, slow query
# - ERROR: failed request, API error
# - CRITICAL: service down, data loss
# Set up log routing: ERROR+ to PagerDuty, WARNING+ to Slack, INFO+ to log storage.
```

---

## Snippet 8.3 — Helicone Integration

**Reference:** [`../ai-engineer-codebook.md#83-helicone-integration`](../ai-engineer-codebook.md#83-helicone-integration)

### Exercise 8.3.1: Proxy mode

```python
# TODO: Point OpenAI client at Helicone's proxy:
# base_url = "https://oai.helicone.ai/v1"
# Add Helicone-Auth: Bearer <your-key>
# Make 10 calls. Open Helicone dashboard.
# Verify: all 10 calls are tracked with cost, latency, prompts.
# Helicone is "observability-as-a-proxy" — no code change beyond base_url.
```

### Exercise 8.3.2: User tracking

```python
# TODO: Tag every call with user_id:
# Helicone-User-Id: user_123
# Then per-user dashboards:
# - which user is costing the most
# - which user is having the most errors
# - which user is using which model
```

### Exercise 8.3.3: Cost ceilings

```python
# TODO: Set a Helicone rate limit:
# $X per user per day
# If user exceeds, return 429
# This prevents a buggy loop from running up your bill.
```

### Exercise 8.3.4: Caching with Helicone

```python
# TODO: Enable Helicone's prompt caching:
# Cache-Control: max-age
# Same prompt + same model = same response, served from cache
# Save on cost AND latency. Especially for high-traffic deterministic queries.
```

---

## Cross-cutting challenges (Mid+)

### Challenge A: Build a "postmortem" template

```python
# TODO: When a major incident happens, write a postmortem:
# - Timeline (UTC)
# - Detection (who/what noticed)
# - Impact (users affected, $ lost, requests failed)
# - Root cause
# - Resolution
# - Action items (5 Whys)
# - What observability helped
# - What observability was missing
# Use this format for the next 3 incidents. Build muscle memory.
```

### Challenge B: SLO-based alerting

```python
# TODO: Define SLOs (Service Level Objectives):
# - 99.9% availability (< 9 hours downtime/year)
# - p95 latency < 2s
# - Error rate < 0.1%
# - Cost per user < $X/mo
# Alert on SLO burn rate, not raw metrics.
# "Burn rate" = how fast you're consuming your error budget.
```

### Challenge C: Cost dashboard

```python
# TODO: Build a dashboard showing:
# - total cost today / this week / this month
# - cost per model
# - cost per user (top 10)
# - cost per endpoint
# - cost per feature (e.g., RAG vs chat vs embedding)
# Refresh daily. Set alerts on anomalies.
# This is how you catch "I left a loop running" before the bill arrives.
```

---

## Architect-level reflections (Senior+)

After completing these exercises, write a 1-page design doc answering:

1. **What observability tools do you use?** (LangSmith, Helicone, Sentry, Datadog, custom)
2. **What do you log for every LLM call?** (tokens, cost, latency, model, user)
3. **How do you trace a request end-to-end?** (request_id propagated everywhere)
4. **How do you debug a "bad" LLM response?** (replay the exact prompt, see the exact context)
5. **How do you catch regressions?** (eval suite run on every prompt change)
6. **What alerts do you have?** (cost anomaly, error spike, latency spike, breaker open)
7. **How do you track cost per user?** (tag every call with user_id)
8. **What's your data retention?** (30 days? 90 days? forever?)
9. **Who gets paged?** (on-call rotation, escalation policy)
10. **What's your "golden path" to debug a customer complaint?** (3 steps, max)

Save these answers. Observability is what separates "shipped" from "production".

---

## What's next

- Pair with [`../../practice/level-8-observability/`](../../practice/level-8-observability/) for the deeper labs
- Move to `section-9-utilities-exercises.md` for utility patterns
- See [`../../PRACTICE-GUIDE.md`](../../PRACTICE-GUIDE.md) for the full learning path