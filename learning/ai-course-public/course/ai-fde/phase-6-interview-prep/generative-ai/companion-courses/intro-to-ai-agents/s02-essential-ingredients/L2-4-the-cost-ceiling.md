# L2.4: The cost ceiling

> **FDE framing in one line:** the cost ceiling is what keeps a confused agent from spending the customer's monthly budget in a single run. It is the single most important guardrail in production; without it, the agent's first incident is a $10K OpenAI bill.

## In 60 seconds

> "Three levels. Per-run: $0.50 default, catches the immediate failure (loop, runaway retry). Per-tenant: $5/day default, catches the customer-level failure (traffic spike, prompt injection). Per-process: $1000/month default, catches the FDE-level failure (vendor price change, model upgrade). Every LLM call records its tokens; every tool call records its credit cost; the loop driver aborts when the ceiling is breached. **The cost is the metric the on-call reads at 3am, the CFO reads in the monthly review, the customer reads in the dashboard.** The wrong choice is to set only a per-run ceiling (a customer with 10K runs/day blows through the per-process ceiling). The wrong choice is to set no ceiling (a confused agent spends the customer's monthly budget in 6 hours). The right choice is all three levels, with the cost as a first-class metric."

**The wrong choice is to read past this block.** The right choice is to recite the 60-second script before you read any other content. The rest of the lecture is the receipt; this is the punchline.

## The 3 things you'll learn

1. The three levels of cost ceiling: per-run (USD), per-tenant (USD/day), per-process (USD/month) — and which dominates for which deployment.
2. The cost-tracking pattern: every LLM call records its tokens; every tool call records its credit cost; the loop driver aborts when the ceiling is breached.
3. The "cost ceiling as score" pattern: the ceiling is the metric the on-call reads at 3am, the metric the CFO reads in the monthly review, and the metric the customer reads in the dashboard.

## Concept

A confused agent will spend the customer's entire monthly budget in a single run if the budget is unbounded. The default behavior of an agent that hits a malformed tool call, a broken API, or a logical loop is to retry until the budget is exhausted. **The cost ceiling is the only thing that prevents this.** It is not optional; it is the first guardrail the FDE writes; it is the first line of the runbook.

The cost-ceiling loop (the FDE's whiteboard):

```
   ┌──────────────────────────────────────────────────────────┐
   │                    AGENT LOOP                            │
   │                                                          │
   │   sense → decide → act → observe → (back to sense)      │
   │                │                                        │
   │                ▼                                        │
   │          ┌──────────────┐                               │
   │          │  CostTracker │  per_run_usd  per_tenant_usd  │
   │          │              │  per_process_usd (rolling)     │
   │          └──────┬───────┘                               │
   │                 │                                       │
   │                 ▼                                       │
   │          ┌──────────────┐                               │
   │          │ _check_      │  run_cost > max_run_usd?       │
   │          │  ceiling()   │  tenant_cost > max_tenant_usd? │
   │          │              │  process_cost > max_process?   │
   │          └──────┬───────┘                               │
   │                 │                                       │
   │        ┌────────┴────────┐                              │
   │        │                 │                              │
   │        ▼                 ▼                              │
   │    continue        RAISE CostCeilingBreached             │
   │    loop            (loop driver aborts run,              │
   │                    returns error envelope to user)       │
   └──────────────────────────────────────────────────────────┘
```

The three levels of cost ceiling:

1. **Per-run (USD per agent invocation).** The ceiling on a single agent run. The default is $0.50 per run for a typical CS-drafter agent, $5.00 for a complex research agent, $50.00 for a batch-processing agent. The per-run ceiling catches the immediate failure: a loop, a runaway retry, a broken tool.
2. **Per-tenant (USD per tenant per day).** The ceiling on a single customer's daily spend. The default is $5/day for a small team, $50/day for a mid-market team, $500/day for an enterprise team. The per-tenant ceiling catches the slower failure: a customer who has a traffic spike, a customer whose users have discovered a prompt-injection attack, a customer whose integration is broken in a way that retries amplify.
3. **Per-process (USD per FDE-managed process per month).** The ceiling on the FDE's total monthly spend across all customers. The default is $1000/month for a single FDE managing 10 small customers. The per-process ceiling catches the systemic failure: a vendor price change, a usage pattern shift, a model upgrade that increases tokens-per-task.

All three levels are necessary. The per-run ceiling catches the immediate failure; the per-tenant ceiling catches the customer-level failure; the per-process ceiling catches the FDE-level failure. **The cost ceiling at all three levels is the FDE's first line of defense against the customer's first incident.**

The cost-tracking pattern: every LLM call records its input tokens, output tokens, and USD cost; every tool call records its credit cost (in the rate limiter's accounting); the loop driver aborts when the ceiling is breached. The pattern is invariant across the three levels:

```python
class CostTracker:
    """Per-run cost tracker with multi-level ceiling enforcement."""

    def __init__(self, max_run_usd: float = 0.50, max_tenant_usd_per_day: float = 5.00):
        self.run_cost = 0.0
        self.max_run_usd = max_run_usd
        self.tenant_cost_today = 0.0
        self.max_tenant_usd_per_day = max_tenant_usd_per_day

    def record_llm_call(self, model: str, input_tokens: int, output_tokens: int):
        cost = PRICING[model]["input"] * input_tokens / 1_000_000 \
             + PRICING[model]["output"] * output_tokens / 1_000_000
        self.run_cost += cost
        self.tenant_cost_today += cost
        self._check_ceiling()

    def record_tool_call(self, cost_credits: int):
        # Convert credits to USD (e.g., 1 credit = $0.001)
        cost = cost_credits * 0.001
        self.run_cost += cost
        self.tenant_cost_today += cost
        self._check_ceiling()

    def _check_ceiling(self):
        if self.run_cost > self.max_run_usd:
            raise CostCeilingBreached(f"per-run: ${self.run_cost:.4f} > ${self.max_run_usd}")
        if self.tenant_cost_today > self.max_tenant_usd_per_day:
            raise CostCeilingBreached(f"per-tenant: ${self.tenant_cost_today:.4f} > ${self.max_tenant_usd_per_day}")
```

The "cost ceiling as score" pattern is the recognition that the ceiling is the metric the on-call reads at 3am, the metric the CFO reads in the monthly review, and the metric the customer reads in the dashboard. **The cost ceiling is not a backstop; it is the first-class metric.** The dashboard shows: cost per run (p50, p95, p99), cost per tenant per day, total cost per process per month, % of ceiling used. The on-call gets paged when any of these exceeds 80% of the ceiling. The CFO gets a monthly report that compares actual cost to the customer's contracted budget.

## The pattern

The pattern that wins interviews is the "three-level ceiling + cost-as-score" pattern. The candidate who says "the cost ceiling is enforced at three levels — per-run, per-tenant, per-process — and the cost is the metric the on-call reads at 3am and the CFO reads in the monthly review" is the candidate who demonstrates the production mindset.

The three-level ceiling is the answer to "how do you prevent cost blowouts." The 60-second script:

> "Three levels. Per-run: $0.50 default, catches the immediate failure (loop, runaway retry). Per-tenant: $5/day default, catches the customer-level failure (traffic spike, prompt injection). Per-process: $1000/month default, catches the FDE-level failure (vendor price change, model upgrade). Every LLM call records its tokens; every tool call records its credit cost; the loop driver aborts when the ceiling is breached. **The cost is the metric the on-call reads at 3am, the CFO reads in the monthly review, the customer reads in the dashboard.** The wrong choice is to set only a per-run ceiling (a customer with 10K runs/day blows through the per-process ceiling). The wrong choice is to set no ceiling (a confused agent spends the customer's monthly budget in 6 hours). The right choice is all three levels, with the cost as a first-class metric."

## Code or example

The cost ceiling in the agent loop:

```python
def run_agent(goal: str, tracker: CostTracker, llm, max_turns: int = 10):
    """Agent loop with cost ceiling enforcement."""
    messages = [{"role": "user", "content": goal}]
    for turn in range(1, max_turns + 1):
        try:
            output = llm(messages)
        except CostCeilingBreached as e:
            return {"error": f"cost ceiling breached: {e}", "turns": turn}
        # Record cost (model + tokens)
        tracker.record_llm_call(model="gpt-5-mini",
                                input_tokens=count_tokens(messages),
                                output_tokens=count_tokens(output))
        step = parse_step(output)
        if step["type"] == "final":
            return {"answer": step["answer"], "turns": turn, "cost_usd": tracker.run_cost}
        obs = call_tool(step["tool"], step["args"])
        tracker.record_tool_call(cost_credits=TOOLS[step["tool"]]["cost_credits"])
        messages.append({"role": "tool", "content": str(obs)})
    return {"error": f"max turns ({max_turns}) reached", "turns": max_turns, "cost_usd": tracker.run_cost}
```

The cost-aware model router:

```python
def pick_model_within_budget(task: str, remaining_budget_usd: float) -> str:
    """Pick the model whose cost-per-step fits the remaining budget."""
    if remaining_budget_usd < 0.01:
        return "gpt-5-mini"  # cheapest option
    if remaining_budget_usd < 0.05 and task in ("planning", "synthesis"):
        return "gpt-5-mini"  # downgrade hard steps if budget is tight
    return pick_model(task)  # default: pick by task
```

The cost dashboard (Prometheus metrics):

```python
from prometheus_client import Histogram, Gauge

COST_PER_RUN = Histogram("agent_cost_per_run_usd", "USD per agent run",
                          buckets=[0.01, 0.05, 0.10, 0.50, 1.00, 5.00])
CEILING_UTILIZATION = Gauge("agent_ceiling_utilization_ratio",
                              "Fraction of ceiling used (0.0 - 1.0)")

def record_run_complete(run_cost_usd: float, ceiling_usd: float):
    COST_PER_RUN.observe(run_cost_usd)
    CEILING_UTILIZATION.set(run_cost_usd / ceiling_usd)
```

## Production addendum

The cost ceiling is the answer to the "how do you prevent cost blowouts" interview question. The 60-second script:

> "Three levels — per-run, per-tenant, per-process. The per-run catches the immediate failure; the per-tenant catches the customer-level failure; the per-process catches the FDE-level failure. Every LLM call records its tokens; every tool call records its credit cost; the loop driver aborts when the ceiling is breached. **The cost is the metric the on-call reads at 3am, the CFO reads in the monthly review, the customer reads in the dashboard.** The default ceilings: $0.50 per run, $5/day per tenant, $1000/month per process. The wrong choice is no ceiling (a confused agent spends the customer's monthly budget in 6 hours). The wrong choice is a single per-run ceiling (a customer with 10K runs/day blows through the per-process ceiling). The right choice is all three, with the cost as a first-class metric on the dashboard."

This 60-second pitch is the difference between a candidate who says "we track cost" and a candidate who says "three levels — per-run, per-tenant, per-process — and the cost is the metric the on-call reads at 3am." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-6-production/lesson-11-6-cost-optimization.py` — the three-level cost tracker.
- **Reference implementation**: `course/practice/level-5-agents/lesson-9-6-production-agents.py::CostTracker` — the per-run tracker with circuit-breaker integration.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — the cost ceiling as a first-class FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/03-distilled-slm/` — the SLM as the cost-ceiling enabler (10-50× cost reduction).
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — the cost ceiling in the centerpiece system design.

## The 3 questions this lecture preps you for

1. **"How do you prevent cost blowouts?"** Answer: three-level cost ceiling — per-run ($0.50 default), per-tenant per-day ($5 default), per-process per-month ($1000 default). Every LLM call records tokens; every tool call records credit cost; the loop driver aborts when the ceiling is breached. The cost is the metric on the dashboard.
2. **"What is the cost-ceiling-as-score pattern?"** Answer: the cost is the first-class metric, not a backstop. The dashboard shows cost-per-run (p50, p95, p99), cost per tenant per day, total cost per process per month. The on-call gets paged at 80% of the ceiling. The CFO gets a monthly report. The customer sees the cost in their dashboard.
3. **"What is the default behavior of a confused agent?"** Answer: spend the entire budget. A confused agent that hits a malformed tool call, a broken API, or a logical loop will retry until the budget is exhausted. The cost ceiling is the only thing that prevents this. **The cost ceiling is the single most important guardrail in production.**

## Read next

`L2-5-the-system-prompt.md` — the fifth ingredient. The system prompt is the contract between the model and the agent. A bad system prompt is the difference between an agent that works and an agent that loops.