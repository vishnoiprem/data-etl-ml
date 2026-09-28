# Lesson 1 — Harness Engineering

> **Type:** Article + Worked Example · Module 11
> The harness: tools, prompts, callbacks, eval — the layer around the agent that production requires.

---

## What a harness is

A **harness** is everything that surrounds an AI agent's raw `think → act → observe` loop: prompts, tool validation, retries, timeouts, observability, cost tracking, eval hooks.

```
   AGENT (raw)                       AGENT (with harness)
   ──────────                        ────────────────────
   LLM calls a tool.                 LLM calls a tool:
                                       - validate args (Pydantic)
                                       - log to tracer
                                       - check rate limits
                                       - execute (with timeout)
                                       - retry on transient errors
                                       - log result
                                       - record cost
                                       - eval hook fires
```

Without the harness, the agent works in a notebook. With the harness, it works in production.

---

## Why harness engineering matters

The harness is **most of the code** in a production agent. A senior engineer's harness includes:

1. **Input validation.** Every tool argument is type-checked. The model hallucinates; Pydantic catches it.
2. **Tool execution.** Timeouts, retries with exponential backoff, idempotency keys.
3. **Observability.** Every step logged with trace ID, prompt, response, latency, tokens, cost.
4. **Cost tracking.** Per-call USD cost summed across the run.
5. **Eval hooks.** Sample 1% of runs for human review; auto-reject runs that go off-policy.
6. **Safety.** Output filtering (PII, prompt injection), action allowlists.
7. **Error recovery.** Fallback tools, partial results, graceful degradation.

A 30-line raw agent becomes 300 lines with a harness. That ratio is normal.

---

## The harness architecture

```
   ┌────────────────────────────────────────────────────────────┐
   │   HARNESS                                                    │
   │                                                             │
   │   user_input                                                 │
   │      │                                                      │
   │      ▼                                                      │
   │   [Input Guardrail]    PII redaction, prompt injection      │
   │      │                                                      │
   │      ▼                                                      │
   │   [Agent Loop]         with retry, timeout, fallback        │
   │      │                                                      │
   │      ▼                                                      │
   │   [Tool Execution]     validate, execute, log               │
   │      │                                                      │
   │      ▼                                                      │
   │   [Output Guardrail]   filter, redact, check format         │
   │      │                                                      │
   │      ▼                                                      │
   │   [Eval Hook]          score, sample, alert                 │
   │      │                                                      │
   │      ▼                                                      │
   │   [Tracer]             LangSmith / OpenTelemetry             │
   │      │                                                      │
   │      ▼                                                      │
   │   final_output                                              │
   └────────────────────────────────────────────────────────────┘
```

---

## Worked Example — build a harness around the agent from Module 10

> **Goal:** Take the 80-line math agent, wrap it in a 200-line harness. Add input validation, tool retry, observability, cost tracking, output filtering, eval hooks, and a CI gate.

### Step 1 — Pydantic schemas for tools

```python
from pydantic import BaseModel, Field, field_validator

class CalculatorArgs(BaseModel):
    expression: str = Field(description="Math expression with only safe characters")

    @field_validator("expression")
    def safe_chars(cls, v):
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in v):
            raise ValueError(f"invalid chars in {v!r}")
        return v
```

The harness validates every tool call before execution. If the model says `calculator(expression="import os")`, Pydantic raises and the agent retries.

### Step 2 — The tool wrapper with retry, timeout, logging

```python
import time
import logging
from functools import wraps

logger = logging.getLogger("agent.harness")

def traced_tool(name: str):
    """Decorator that adds retry, timeout, cost tracking, logging."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            call_id = f"call_{int(time.time() * 1000)}"

            # Validate args
            try:
                if name == "calculator":
                    validated = CalculatorArgs(**kwargs)
                    kwargs = validated.model_dump()
            except Exception as e:
                logger.warning(f"[{call_id}] validation failed: {e}")
                raise

            # Retry with exponential backoff
            for attempt in range(3):
                try:
                    result = fn(*args, **kwargs)
                    elapsed = time.perf_counter() - start
                    logger.info(f"[{call_id}] {name} ok in {elapsed:.2f}s")
                    return {"ok": True, "result": result, "elapsed_s": elapsed, "call_id": call_id}
                except Exception as e:
                    if attempt == 2:
                        logger.error(f"[{call_id}] {name} failed after 3 attempts: {e}")
                        return {"ok": False, "error": str(e), "call_id": call_id}
                    time.sleep(0.5 * (2 ** attempt))
        return wrapper
    return decorator

@traced_tool("calculator")
def calculator(expression: str) -> str:
    return str(eval(expression))
```

### Step 3 — Cost tracking

```python
class CostTracker:
    """Sum up token and USD cost across an agent run."""
    PRICES = {   # per 1M tokens
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o":      {"input": 2.50, "output": 10.00},
    }

    def __init__(self, model: str):
        self.model = model
        self.input_tokens = 0
        self.output_tokens = 0

    def record(self, usage):
        self.input_tokens += usage.prompt_tokens
        self.output_tokens += usage.completion_tokens

    @property
    def cost_usd(self) -> float:
        p = self.PRICES[self.model]
        return (
            self.input_tokens / 1e6 * p["input"]
            + self.output_tokens / 1e6 * p["output"]
        )
```

### Step 4 — Output guardrail

```python
def output_guardrail(text: str) -> str:
    """Filter the final answer before returning to the user."""
    # Strip any leaked system-prompt tokens
    banned = ["system prompt:", "<|im_start|>", "<function_calls>"]
    for b in banned:
        text = text.replace(b, "[REDACTED]")

    # Truncate absurdly long outputs
    if len(text) > 4000:
        text = text[:4000] + "\n\n[truncated]"

    return text
```

### Step 5 — Eval hook (sample for human review)

```python
import random
import json

class EvalHook:
    """Sample 5% of runs for human review."""
    def __init__(self, sample_rate: float = 0.05):
        self.sample_rate = sample_rate
        self.sampled = []

    def __call__(self, run_data: dict):
        if random.random() < self.sample_rate:
            self.sampled.append(run_data)
            # Persist for human review
            with open("eval/sampled_runs.jsonl", "a") as f:
                f.write(json.dumps(run_data) + "\n")

        # Also auto-flag suspicious runs
        if run_data["cost_usd"] > 0.50:  # a single run > 50 cents
            logger.warning(f"High-cost run: ${run_data['cost_usd']:.3f}")
```

### Step 6 — The full harness

```python
def run_agent_with_harness(user_query: str, max_steps: int = 5, timeout_s: int = 30) -> dict:
    cost_tracker = CostTracker("gpt-4o-mini")
    eval_hook = EvalHook(sample_rate=0.05)

    # Input guardrail
    user_query = input_guardrail(user_query)

    start = time.perf_counter()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]
    steps = []

    for step_num in range(1, max_steps + 1):
        if time.perf_counter() - start > timeout_s:
            return {"error": "timeout", "steps": steps}

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=[TOOL_SCHEMA],
        )
        cost_tracker.record(response.usage)
        msg = response.choices[0].message
        messages.append(msg)

        if msg.tool_calls:
            for tc in msg.tool_calls:
                fn_args = json.loads(tc.function.arguments)
                tool_result = calculator(**fn_args)   # uses @traced_tool wrapper
                steps.append({"step": step_num, "tool": tc.function.name, "args": fn_args, "result": tool_result})
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(tool_result),
                })
        else:
            final = output_guardrail(msg.content)
            elapsed = time.perf_counter() - start

            run_data = {
                "query": user_query,
                "final": final,
                "steps": steps,
                "n_steps": step_num,
                "input_tokens": cost_tracker.input_tokens,
                "output_tokens": cost_tracker.output_tokens,
                "cost_usd": cost_tracker.cost_usd,
                "elapsed_s": elapsed,
            }
            eval_hook(run_data)
            return run_data

    return {"error": "max_steps_exceeded", "steps": steps}
```

### Step 7 — CI gate

```python
# eval/ci_gate.py
EVAL_SET = [...]  # 50 math problems
results = []
for ex in EVAL_SET:
    out = run_agent_with_harness(ex["q"])
    results.append({"q": ex["q"], "expected": ex["a"], "got": out.get("final", ""), "steps": out.get("n_steps", 0)})

accuracy = sum(abs(parse(r["got"]) - r["expected"]) < 0.01 for r in results) / len(results)
avg_cost = sum(r.get("cost_usd", 0) for r in [run_agent_with_harness(ex["q"]) for ex in EVAL_SET]) / len(EVAL_SET)

# Quality gates
assert accuracy >= 0.90, f"accuracy regressed to {accuracy:.3f}"
assert avg_cost < 0.05, f"cost per call too high: ${avg_cost:.3f}"
print(f"Eval passed: accuracy={accuracy:.3f}, avg_cost=${avg_cost:.4f}")
```

A PR that breaks the harness — wrong tool schema, missing retry, broken guardrail — fails the CI gate.

---

## What this example teaches

1. **The harness is more code than the agent.** ~200 lines of harness around an 80-line agent.
2. **Every layer earns its keep.** Validation catches hallucinations. Retry handles transient errors. Eval catches regressions. Tracing is non-negotiable.
3. **Pydantic is the contract.** The model and the code agree on what tools accept.
4. **Cost tracking is a feature.** Without it, you can't defend a model change.
5. **CI gates are the regression detector.** Eval that runs nightly but doesn't block PRs is documentation.

Read this and you understand why senior engineers' agent codebases are 80% harness, 20% agent.

---

## What Comes Next

> Lesson 2 — **Loop Engineering** — designing the repeating cycle. Termination conditions, error paths, parallel branches, the part of the harness that loops.