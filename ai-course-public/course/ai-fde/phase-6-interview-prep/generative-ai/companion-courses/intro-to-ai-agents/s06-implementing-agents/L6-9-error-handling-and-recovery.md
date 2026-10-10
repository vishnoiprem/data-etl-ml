# L6.9: Error handling and recovery — the 4-category taxonomy

> **FDE framing in one line:** every error in an agent falls into one of 4 categories: transient (retry), permanent (escalate), model (re-plan), tool (fallback). The recovery strategy is determined by the category. The wrong choice is to retry a permanent error; the right choice is to match the strategy to the category.

## In 60 seconds

> "4 categories. Transient (network timeout, retry with exponential backoff). Permanent (404, escalate to human). Model (hallucination, re-plan). Tool (exception, fallback to a different tool or model). **The recovery strategy is determined by the category.** Every error is returned to the model as a structured observation; the model decides what to do next. The wrong choice is to retry a permanent error (wastes the cost ceiling). The wrong choice is to silently swallow an error (the model doesn't know). The right choice is to match the strategy to the category + the structured observation pattern."

**The wrong choice is to read past this block.** The right choice is to recite the 60-second script before you read any other content. The rest of the lecture is the receipt; this is the punchline.

## The 3 things you'll learn

1. The 4 error categories: transient (network timeout, retry), permanent (404 not found, escalate), model (hallucination, re-plan), tool (exception, fallback). Each has a different recovery strategy.
2. The 4 recovery strategies: retry (with exponential backoff), escalate (to a human), re-plan (regenerate the plan), fallback (use a different tool or model). The strategy is determined by the category.
3. The "structured error observation" pattern: every error is returned to the model as a structured observation; the model decides what to do next. The agent framework does not silently swallow errors.

## Concept

Error handling and recovery is the 9th layer of the shipping agent. Every error in an agent falls into one of 4 categories; the recovery strategy is determined by the category. **The candidate who can name all 4 categories and the matching recovery strategies is the candidate who can ship a resilient agent.**

The 4 error categories:

1. **Transient.** The error is temporary; a retry will likely succeed. Examples: network timeout, rate limit (429), API temporarily unavailable (503), database deadlock. The recovery strategy: retry with exponential backoff (1s, 2s, 4s, 8s) and jitter; max 3 retries; then escalate.
2. **Permanent.** The error is permanent; a retry will not help. Examples: 404 not found, 400 bad request (the args are wrong even after retry), policy violation (the user is not authorized). The recovery strategy: do not retry; escalate to a human or to a different agent.
3. **Model.** The error is in the model's output; the tool call is correct but the reasoning is wrong. Examples: hallucinated tool call, wrong plan, contradiction between steps. The recovery strategy: re-plan (regenerate the plan or the next step) or escalate to a more capable model.
4. **Tool.** The error is in the tool implementation; the tool itself failed. Examples: tool returns 500, tool returns malformed data, tool returns an exception. The recovery strategy: fallback to a different tool, or retry with a different model, or escalate.

The 4 recovery strategies:

1. **Retry (with exponential backoff).** For transient errors. The retry waits 1s, 2s, 4s, 8s with random jitter; max 3 retries. If still failing, escalate.
2. **Escalate (to a human or to a more capable agent).** For permanent errors. The agent emits a structured observation that the task cannot be completed; the human takes over.
3. **Re-plan (regenerate the plan or the next step).** For model errors. The agent calls the model with a "your previous step was wrong, here is why; please generate a different approach" prompt.
4. **Fallback (use a different tool or model).** For tool errors. The agent tries a different tool (e.g., `web_search` → `cache_lookup`); if no fallback, retry with a different model or escalate.

The "structured error observation" pattern is the recognition that **every error is returned to the model as a structured observation; the model decides what to do next.** The agent framework does not silently swallow errors; the model sees the error, diagnoses it, and decides. The loop driver increments the turn counter; the cost ceiling catches the loop; the model has the information it needs to recover.

## The pattern

The 4-category error classifier:

```python
from enum import Enum

class ErrorCategory(Enum):
    TRANSIENT = "transient"
    PERMANENT = "permanent"
    MODEL = "model"
    TOOL = "tool"

def classify_error(error: dict) -> ErrorCategory:
    """Classify an error into one of 4 categories."""
    err = error.get("_err", "")
    message = error.get("message", "")
    if err in ("timeout", "rate_limit", "service_unavailable", "deadlock"):
        return ErrorCategory.TRANSIENT
    if err in ("unknown_tool", "schema_violation", "policy_violation", "not_found", "bad_request"):
        return ErrorCategory.PERMANENT
    if err in ("malformed", "hallucinated_tool", "plan_contradiction"):
        return ErrorCategory.MODEL
    if err in ("exception", "tool_500", "malformed_result"):
        return ErrorCategory.TOOL
    return ErrorCategory.PERMANENT  # Default: don't retry
```

The 4 recovery strategies:

```python
def recover(error: dict, agent: SingleAgent, state: dict) -> dict:
    """Apply the matching recovery strategy for the error category."""
    category = classify_error(error)
    if category == ErrorCategory.TRANSIENT:
        return retry_with_backoff(error, agent, state, max_retries=3)
    if category == ErrorCategory.PERMANENT:
        return escalate_to_human(error, state)
    if category == ErrorCategory.MODEL:
        return replan(error, agent, state)
    if category == ErrorCategory.TOOL:
        return fallback(error, agent, state)
    return escalate_to_human(error, state)

def retry_with_backoff(error: dict, agent: SingleAgent, state: dict, max_retries: int = 3) -> dict:
    """Retry with exponential backoff + jitter."""
    for attempt in range(max_retries):
        wait_s = (2 ** attempt) + random.uniform(0, 1)  # 1s, 2s, 4s + jitter
        time.sleep(wait_s)
        try:
            return agent.tools.call(error["tool"], error["args"])
        except Exception as e:
            if attempt == max_retries - 1:
                return {"_ok": False, "_err": "max_retries_exceeded", "original": error}
    return {"_ok": False, "_err": "max_retries_exceeded"}

def escalate_to_human(error: dict, state: dict) -> dict:
    """Escalate to a human for permanent errors."""
    state["escalation_request"] = {
        "reason": str(error),
        "context": state.get("messages", [])[-3:],  # last 3 messages
        "priority": "high" if error.get("amount_usd", 0) > 100 else "medium",
    }
    return {"_ok": False, "_err": "escalated_to_human", "request": state["escalation_request"]}

def replan(error: dict, agent: SingleAgent, state: dict) -> dict:
    """Re-plan: tell the model the previous step was wrong, ask for a new approach."""
    state["messages"].append({
        "role": "tool",
        "content": json.dumps({
            "_ok": False,
            "_err": "plan_contradiction",
            "hint": "your previous step was wrong. the observation contradicts the plan. please generate a different approach.",
        }),
    })
    return agent.run(state["goal"])  # Re-run from the current state

def fallback(error: dict, agent: SingleAgent, state: dict) -> dict:
    """Try a different tool or model for tool errors."""
    # Try a fallback tool
    if error.get("tool") == "web_search" and "cache_lookup" in agent.tools.tools:
        return agent.tools.call("cache_lookup", error["args"])
    # Try a different model
    if agent.model.name == "gpt-5":
        return retry_with_different_model(error, agent, state, fallback_model="claude-sonnet-4.5")
    return escalate_to_human(error, state)
```

The structured error observation (the model's view):

```python
# The model receives the error as an observation
messages.append({
    "role": "tool",
    "content": json.dumps({
        "_ok": False,
        "_err": "rate_limit",  # Transient
        "message": "API rate limit exceeded; retry after 2s",
        "retry_after_s": 2,
        "category": "transient",
        "hint": "wait 2s and retry the same call",
    }),
})

# The model reads the observation, decides what to do
# For transient: wait and retry
# For permanent: try a different approach or escalate
# For model: re-plan
# For tool: try a different tool
```

The pattern that wins interviews is the "4 categories + 4 strategies + structured observation" pattern. The candidate who says "I classify errors into 4 categories (transient, permanent, model, tool); the recovery strategy is determined by the category (retry, escalate, re-plan, fallback). Every error is returned to the model as a structured observation; the model decides what to do next. The wrong choice is to retry a permanent error (wastes the cost ceiling). The right choice is to match the strategy to the category" is the candidate who demonstrates the error-mindset.

## Code or example

The error handling loop (the production pattern):

```python
def run_agent_with_error_handling(goal: str, agent: SingleAgent) -> dict:
    messages = [{"role": "system", "content": agent.system_prompt}, {"role": "user", "content": goal}]
    for turn in range(1, agent.max_turns + 1):
        if agent.cost.breached():
            return {"error": "cost_ceiling_breached"}
        output = agent.model.fn(messages)
        agent.cost.record(agent.model, len(str(messages)) // 4, len(output) // 4)
        messages.append({"role": "assistant", "content": output})
        step = parse_step(output)
        if step["type"] == "final":
            return {"answer": step["answer"]}
        if step["type"] == "malformed":
            # Model error: structured observation
            messages.append({"role": "tool", "content": json.dumps({"_ok": False, "_err": "malformed", "category": "model"})})
            continue
        # Tool call
        try:
            args = json.loads(step["args_raw"])
        except Exception:
            args = {"raw": step["args_raw"]}
        result = agent.tools.call(step["tool"], args)
        if not result["_ok"]:
            # Apply recovery strategy based on error category
            recovered = recover(result, agent, {"messages": messages, "goal": goal})
            if recovered.get("_ok"):
                result = recovered
            else:
                messages.append({"role": "tool", "content": json.dumps(recovered)})
                continue
        messages.append({"role": "tool", "content": json.dumps(result)})
    return {"error": "max_turns_reached"}
```

The error rate by category dashboard:

```python
ERROR_RATE_BY_CATEGORY = {
    "transient": "0.5%",   # Retried successfully
    "permanent": "0.3%",   # Escalated to human
    "model": "1.2%",       # Re-planned successfully
    "tool": "0.4%",        # Fell back to a different tool
    "total": "2.4%",       # Of all runs
}
# Alert: any category > 5% or 2× baseline
```

## Production addendum

The error handling question is the answer to "how do you handle errors in an agent." The 60-second script:

> "4 categories. Transient (network timeout, retry with exponential backoff). Permanent (404, escalate to human). Model (hallucination, re-plan). Tool (exception, fallback to a different tool or model). **The recovery strategy is determined by the category.** Every error is returned to the model as a structured observation; the model decides what to do next. The wrong choice is to retry a permanent error (wastes the cost ceiling). The wrong choice is to silently swallow an error (the model doesn't know). The right choice is to match the strategy to the category + the structured observation pattern."

This is the difference between a candidate who says "we handle errors" and a candidate who says "4 categories, 4 strategies, structured error observation, the model decides what to do next." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-1-foundations/README.md` — the error taxonomy.
- **Reference implementation**: `course/hardcode/level-9-failure-handling/17-circuit-breaker-llm.py` — the production error handling.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — error handling as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/01-mcp-drafter/` — the MCP server's error handling.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — error handling as a system design pattern.

## The 3 questions this lecture preps you for

1. **"How do you handle errors in an agent?"** Answer: 4 categories. Transient (retry with exponential backoff: 1s, 2s, 4s + jitter, max 3 retries). Permanent (escalate to human). Model (re-plan: tell the model the previous step was wrong, ask for a different approach). Tool (fallback: try a different tool or model). The recovery strategy is determined by the category. **Every error is returned to the model as a structured observation; the model decides what to do next.**
2. **"What is the structured error observation pattern?"** Answer: every error is returned to the model as a typed `_ok/_err` envelope. The envelope includes: the error category, a hint for recovery, the retry_after_s (for transient), the request_id (for escalation). The model reads the envelope, diagnoses the error, and decides. The agent framework does not silently swallow errors.
3. **"What is the difference between retry and fallback?"** Answer: retry is for transient errors — the same call is repeated with exponential backoff. Fallback is for tool errors — a different tool or model is tried. Retry is the right strategy when the error is temporary (network timeout); fallback is the right strategy when the tool itself is broken.

## Read next

`L6-10-debugging-the-production-agent.md` — the 10th and final lecture of Section 6. The 5-step debugging playbook: reproduce (replay the audit log), isolate (which guardrail fired), diagnose (root cause), fix (the smallest change that resolves), verify (the regression check). The 3am debugging playbook.