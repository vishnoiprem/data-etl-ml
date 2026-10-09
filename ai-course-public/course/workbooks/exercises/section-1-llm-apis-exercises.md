# Codebook Exercises — Section 1: LLM API Patterns

> **Paired exercises for [`../ai-engineer-codebook.md` § 1](../ai-engineer-codebook.md#section-1-llm-api-patterns).**
> These turn reference snippets into active practice. For each reference snippet in the codebook, here are 3-5 challenges that force you to modify, extend, and break the code.

---

## How to use these

1. Open the reference snippet in [`../ai-engineer-codebook.md`](../ai-engineer-codebook.md) — Section 1 (LLM APIs)
2. Read the snippet once
3. Do the exercises below IN ORDER — each builds on the previous
4. For each exercise, write the code, run it, note what you learned

**Time per exercise:** 10-20 min.
**Total time for this section:** 3-5 hours.

---

## Snippet 1.1 — Basic chat completion

**Reference:** [`../ai-engineer-codebook.md#11-openai--basic-chat-completion`](../ai-engineer-codebook.md#11-openai--basic-chat-completion)

### Exercise 1.1.1: Add response validation

The reference assumes everything works. Add error handling:

```python
# TODO: Wrap the basic chat call in a function that:
# - catches openai.APIError, RateLimitError, APITimeoutError
# - retries RateLimitError with exponential backoff (3x)
# - returns a dict: {"content": str, "tokens": int, "retries": int, "latency_ms": int}
```

**Hint:** `time.sleep(2 ** attempt)` for backoff.

### Exercise 1.1.2: Add a usage tracker

Build a `UsageTracker` class that records every call:

```python
class UsageTracker:
    def __init__(self):
        self.calls = []  # list of {model, prompt_tokens, completion_tokens, cost_usd, ts}

    def record(self, model: str, prompt_tokens: int, completion_tokens: int):
        # TODO: compute cost from PRICING dict and append to self.calls
        pass

    def total_cost(self) -> float:
        # TODO: sum all costs
        pass

    def report(self) -> str:
        # TODO: return a string summary: total calls, total tokens, total cost, by model
        pass

# Use it
tracker = UsageTracker()
# ... make 10 chat calls ...
print(tracker.report())
```

**Hint:** PRICING = `{"gpt-4o-mini": {"input": 0.15, "output": 0.60}}` (per 1M tokens).

### Exercise 1.1.3: Compare 3 models on the same prompt

Send the same question to `gpt-4o-mini`, `gpt-4o`, and `claude-3-5-sonnet`:

```python
PROMPT = "Explain the CAP theorem in 2 sentences."
# TODO: Call each model, print content + token usage + estimated cost + latency
# Then answer: which is best for this prompt and why?
```

**Stretch:** Run the same prompt 10 times for each model and compute mean + stddev for latency.

### Exercise 1.1.4: Temperature experiment

Send the prompt "Write a tagline for an AI startup" 5 times at temperature 0, 0.7, and 1.5:

```python
# TODO: Print all 15 responses. Observe:
# - At temp 0: identical (or nearly so)
# - At temp 0.7: varied but coherent
# - At temp 1.5: may be creative or nonsensical
```

**Architect insight:** Temperature > 1 rarely makes sense for production. It's a tradeoff between determinism and creativity.

### Exercise 1.1.5: System prompt matters (Junior+)

Take the same user question: "What's the best database?"

```python
SYSTEM_PROMPTS = [
    "You are a helpful assistant.",              # baseline
    "You are a PostgreSQL expert. Recommend only PostgreSQL.",
    "You are a contrarian. Argue against conventional wisdom.",
    "You are a teacher. Explain like I'm 10.",
]
# TODO: Send the same question with each system prompt
# Observe how the system prompt shapes the answer
```

**Architect insight:** The system prompt is configuration, not instruction. Use it for persona, capabilities, constraints — not for the task itself.

---

## Snippet 1.2 — Streaming

### Exercise 1.2.1: Build a streaming chat UI in 50 lines

```python
# TODO: Build a CLI streaming chat that:
# - prints tokens as they arrive (no buffering)
# - shows partial response time per token
# - sums up total tokens at end
# Hint: use 'stream=True', accumulate with chunk.choices[0].delta.content
```

### Exercise 1.2.2: Streaming with cancellation

```python
# TODO: Start a streaming call but cancel it after 100ms.
# Hint: there's no clean cancellation, but you can stop iterating the generator.
# Discuss: how would you handle this in a FastAPI/WebSocket context?
```

### Exercise 1.2.3: Aggregate streamed output to JSON

```python
# TODO: Stream a response, collect all tokens, return as JSON:
# {"full_text": "...", "num_chunks": int, "first_token_ms": int, "last_token_ms": int}
# This is what you'd return from an SSE endpoint.
```

---

## Snippet 1.3 — Function calling

### Exercise 1.3.1: Build a weather agent with 3 functions

```python
tools = [
    {"type": "function", "function": {"name": "get_weather", ...}},
    {"type": "function", "function": {"name": "convert_temp", ...}},
    {"type": "function", "function": {"name": "get_forecast", ...}},
]
# TODO: User asks "What's the weather in Tokyo in Fahrenheit?"
# The model should call get_weather (Celsius) THEN convert_temp
# Implement the loop that handles multi-step tool calls
```

**Architect insight:** Multi-step tool calls are the basis of all AI agents. Get good at this.

### Exercise 1.3.2: Add tool-call validation with Pydantic

```python
# TODO: Use Pydantic to define the schema for each tool, validate the model's output
# If validation fails, send back an error message and ask for retry
# This catches schema drift and model hallucination
```

### Exercise 1.3.3: Implement "I don't have a tool for that"

```python
# TODO: When the model wants to call a tool you didn't register, return:
# {"error": "tool_not_registered", "tool_name": "..."}
# and let the LLM respond naturally to the user
# Discuss: how would you log this as a missing capability?
```

---

## Snippet 1.4 — JSON mode

### Exercise 1.4.1: Extract structured data from messy text

```python
MESSY_INPUT = """
Customer: John Smith
Order: #12345
Items: 2x Widget A ($10 each), 1x Widget B ($25)
Total: $45
Address: 123 Main St, Springfield, IL 62701
"""
# TODO: Use JSON mode + Pydantic to extract:
# - customer_name
# - order_id
# - items (list of {name, quantity, price})
# - total
# - shipping_address (structured)
```

### Exercise 1.4.2: Validate and recover from bad JSON

```python
# TODO: Sometimes the model returns invalid JSON despite JSON mode.
# Implement a retry loop:
# 1. Try to parse the response
# 2. If parse fails, send the error back to the model and ask it to fix
# 3. Cap retries at 3
# Test with deliberately malformed system prompts to trigger failures
```

### Exercise 1.4.3: Schema-first prompt design

```python
# TODO: Define a JSON schema FIRST, then write the prompt
# Use jsonschema library to validate the output
# Compare: schema-first vs prompt-first — which gives more reliable results?
```

---

## Snippet 1.5 — Vision

### Exercise 1.5.1: Image Q&A with cost awareness

```python
# TODO: Compare cost for the same image at 'low', 'high', 'auto' detail
# Document: which detail level to use for OCR, which for UI screenshots, which for product photos
```

### Exercise 1.5.2: Multi-image input

```python
# TODO: Send 2 images (e.g., "before" and "after") and ask the model to compare them
# Observe: does the model use both images? Does order matter?
```

---

## Snippet 1.6 — Anthropic Claude basics

### Exercise 1.6.1: System prompts comparison

```python
# TODO: Send the same user message to OpenAI and Claude with similarly-worded system prompts
# Note which one follows instructions more literally vs. which is more "creative"
```

### Exercise 1.6.2: Long context

```python
# TODO: Paste a 100K-token document into Claude. Ask a question about the END of the doc
# Note: "lost in the middle" — does the model do better on questions about the start/end vs middle?
```

---

## Snippet 1.7 — Prompt caching

### Exercise 1.7.1: Measure the savings

```python
# TODO: Cache a long document in the system prompt
# Call the API 10 times, measure token cost on first call vs subsequent
# Verify: are you getting the 90% discount advertised?
```

**Architect insight:** Prompt caching pays off when you have a stable context (system prompt, few-shot examples, large docs) and many queries against it.

---

## Snippet 1.8 — Anthropic tool use

### Exercise 1.8.1: Compare OpenAI and Anthropic tool calling

```python
# TODO: Define the same tool (e.g., get_weather) using OpenAI's function-calling format and Anthropic's tool-use format
# Send the same question to both models with the respective tool definition
# Compare: code complexity, error handling, edge cases
```

---

## Snippet 1.9 — Google Gemini

### Exercise 1.9.1: Multi-modal input

```python
# TODO: Send text + image to Gemini in one call
# Note: Gemini's multi-modal API is different from OpenAI's
```

### Exercise 1.9.2: Function calling with Gemini

```python
# TODO: Define a tool for Gemini, send a request, observe how it compares to OpenAI's
```

---

## Snippet 1.10 — Open-source models

### Exercise 1.10.1: Run Llama 3 locally

```bash
# Install Ollama: https://ollama.com
ollama pull llama3
# TODO: Query it via REST API (or Python client)
# Compare latency and quality to OpenAI on a few prompts
```

### Exercise 1.10.2: Trade-offs table (fill this in)

| Concern | GPT-4o-mini | Llama 3 70B (self-hosted) |
|---|---|---|
| Latency (p50) | ?ms | ?ms (your machine) |
| Cost per 1M tokens | $0.15 | $? (depends on hardware) |
| Quality (your subjective rating) | ?/10 | ?/10 |
| Privacy | OpenAI sees your data | Data stays local |
| Uptime | OpenAI SLA | Your SLA |
| When to pick | Production, low ops | Privacy, regulated, demos |

---

## Cross-cutting challenges (Mid+)

### Challenge A: Build a model router

```python
# TODO: Build a function that takes a request and routes to the right model:
# - Simple classification → gpt-4o-mini
# - Code generation → claude-3-5-sonnet
# - Long document analysis → claude-3-5-sonnet (200K context)
# - Privacy-sensitive → local Llama
# - Cost-sensitive bulk → gpt-4o-mini
# Implement smart routing based on request properties
```

### Challenge B: Build a fallback chain

```python
# TODO: If primary model fails or returns bad output, try the next in chain:
# [gpt-4o-mini, gpt-4o, claude-3-5-sonnet, gemini-pro, local-llama]
# Log every fallback, measure MTTR, alert if fallback rate > 10%
```

### Challenge C: Cost-aware load balancer

```python
# TODO: Given a request with a max_cost constraint, pick the cheapest model that can handle it
# Build a cost lookup table: {model: {input_cost, output_cost, capabilities}}
# Implement: pick_cheapest_model(request, max_cost) → model name
```

---

## Architect-level reflections (Senior+)

After completing these exercises, write a 1-page design doc answering:

1. **If you're shipping a customer-facing chatbot, which model would you pick and why?**
2. **At what monthly API spend would you start self-hosting?**
3. **What's your fallback strategy when OpenAI has an outage?**
4. **How do you handle token cost surprises?**
5. **What's your prompt caching strategy?**
6. **When would you use multiple models in one pipeline?**

Save these answers. They'll come up in interviews and design reviews.

---

## What's next

- Pair this with the per-lesson labs in [`../../practice/level-1-foundations/`](../../practice/level-1-foundations/) for deeper context
- Move to `section-2-production-exercises.md` for retry patterns, fallbacks, and observability
- See [`../../PRACTICE-GUIDE.md`](../../PRACTICE-GUIDE.md) for the full learning path
