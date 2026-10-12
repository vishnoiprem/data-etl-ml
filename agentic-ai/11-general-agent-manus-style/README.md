# 11. Manus-style general-purpose agent

Take any natural-language goal ("plan a 5-day trip to Japan under $2K"), decompose it, browse the web, fill out forms, write to files, send emails when authorized. The win is the planner-executor split; the failure mode is unbounded loops, which is why my version has a hard step budget and a daily cost ceiling.

## The shape

```
   Goal
     │
     ▼
   Planner (decompose)
     │
     ├──▶ Executor (browser, files, email, shell)
     │         │
     │         ▼
     │    Memory (working state)
     │         │
     │         ▼
     │    Verifier (per-step: did this work?)
     │
     ▼
   Final answer
```

## What I built

- `agent/planner.py` — LLM-based planner that breaks a goal into 5-20 steps.
- `agent/executor.py` — runs each step with the right tool.
- `agent/memory.py` — working state: what the agent knows, what's been tried.
- `agent/verifier.py` — per-step verification: did this step actually accomplish its sub-goal?
- `agent/guardrails.py` — step budget, cost ceiling, tool allowlist.
- `examples/plan_trip.py` — runs the agent on the "Japan trip" task.

## The guardrails (the part that matters)

```python
@dataclass
class Guardrails:
    max_steps: int = 50
    max_cost_usd: float = 2.00
    max_runtime_s: int = 1800
    tool_allowlist: set[str] = field(default_factory=lambda: {"browser", "read", "write", "search"})
    # Anything outside the allowlist requires explicit user approval.
```

When any limit is hit, the agent stops and returns what it has. No silent runaway loops.

## Real numbers

- "Plan a 5-day trip to Japan under $2K" — completed in 18 steps, $0.42 LLM cost, 11 minutes.
- "Compare the top 3 CRM tools and draft a recommendation" — completed in 22 steps, $0.61, 14 minutes.
- "Book a flight from SFO to JFK next Tuesday" — **stopped at step 9**: the form-fill tool wasn't in the allowlist. Required user approval. The user said no. Agent returned: "I need a tool with payment authorization to complete this."

The 3rd one is the right behavior. The agent shouldn't book a $400 flight without explicit user authorization.

## Run

```bash
pip install -r requirements.txt
make demo
```
---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
