# L6.5: Guardrails and cost control — the 5 production guardrails + the 3-level cost ceiling

> **FDE framing in one line:** the 5 production guardrails wrap the loop; the 3-level cost ceiling is the first one. The cost is the first-class metric the on-call reads at 3am, the CFO reads in the monthly review, the customer reads in the dashboard.

## The 3 things you'll learn

1. The 5 production guardrails: loop detector, schema validator, cost ceiling, idempotency, audit log. Each catches a different failure mode.
2. The 3-level cost ceiling: per-run ($0.50), per-tenant ($5/day), per-process ($1000/month). All three are necessary.
3. The "cost as a first-class metric" pattern: the dashboard, the on-call alert, the CFO report. The cost is not a backstop; it is the score.

## Concept

The 5 production guardrails are the layers that wrap the agent loop. Each guardrail catches a different failure mode; together they turn a prototype into a production agent. **The 5 guardrails are not optional; the candidate who names all 5 is the candidate who passes the centerpiece round.**

The 5 production guardrails:

1. **Loop detector.** If the same tool fires N times in a row (N=3 default), the loop aborts with a structured error. The model is told "you've called `web_search` 3 times in a row; break out and ask the user." The loop detector catches the confused-agent failure mode (the model is stuck and retries the same call forever).
2. **Schema validator.** Every tool call is validated against the JSON-Schema-like args spec. The model gets a structured 403 if it tries to call a tool with the wrong args, not a Python `TypeError`. The schema validator catches the hallucinated-tool-call failure mode.
3. **Cost ceiling.** The loop tracks input/output tokens and aborts if the run exceeds `MAX_COST_USD`. The default behavior of a confused agent is to spend the entire budget; the cost ceiling is the only thing that prevents that.
4. **Idempotency on write tools.** Every write tool keys on a stable hash of the canonical args. A retry produces the same side effect or none. The model can safely retry on transient errors. The idempotency cache catches the double-write failure mode.
5. **Audit log.** Every step is a typed log row (turn, event, tool, args, result, cost, tokens). The audit log is the artifact the on-call reads at 3am. It is the first-class deliverable, not a side effect.

The 3-level cost ceiling:

1. **Per-run (USD per agent invocation).** The ceiling on a single agent run. The default is $0.50 for a typical CS-drafter agent, $5.00 for a complex research agent, $50.00 for a batch-processing agent. The per-run ceiling catches the immediate failure.
2. **Per-tenant (USD per tenant per day).** The ceiling on a single customer's daily spend. The default is $5/day for a small team, $50/day for a mid-market team, $500/day for an enterprise team. The per-tenant ceiling catches the customer-level failure.
3. **Per-process (USD per FDE-managed process per month).** The ceiling on the FDE's total monthly spend across all customers. The default is $1000/month for a single FDE managing 10 small customers. The per-process ceiling catches the systemic failure.

The "cost as a first-class metric" pattern is the recognition that the cost is not a backstop; it is the score. The dashboard shows cost-per-run (p50, p95, p99), cost per tenant per day, total cost per process per month, % of ceiling used. The on-call gets paged when any of these exceeds 80% of the ceiling. The CFO gets a monthly report that compares actual cost to the customer's contracted budget.

## The pattern

The 5 guardrails as classes:

```python
# Guardrail 1: Loop detector
class LoopDetector:
    def __init__(self, window: int = 3):
        self.recent = deque(maxlen=window)
    def record(self, tool: str) -> bool:
        self.recent.append(tool)
        return len(self.recent) == self.recent.maxlen and len(set(self.recent)) == 1

# Guardrail 2: Schema validator (built into ToolRegistry)
def validate_args(args: dict, schema: dict) -> list[str]:
    # ... (from L6.3)
    pass

# Guardrail 3: Cost ceiling
class CostCeiling:
    def __init__(self, max_run_usd: float = 0.50, max_tenant_per_day_usd: float = 5.0, max_process_per_month_usd: float = 1000.0):
        self.run_cost = 0.0
        self.tenant_cost_today = 0.0
        self.process_cost_this_month = 0.0
        self.max_run_usd = max_run_usd
        self.max_tenant_per_day_usd = max_tenant_per_day_usd
        self.max_process_per_month_usd = max_process_per_month_usd

    def record(self, model: Model, input_tokens: int, output_tokens: int):
        cost = model.pricing["input"] * input_tokens + model.pricing["output"] * output_tokens
        self.run_cost += cost
        self.tenant_cost_today += cost
        self.process_cost_this_month += cost

    def breached(self) -> tuple[bool, str]:
        if self.run_cost > self.max_run_usd:
            return True, f"per-run: ${self.run_cost:.4f} > ${self.max_run_usd}"
        if self.tenant_cost_today > self.max_tenant_per_day_usd:
            return True, f"per-tenant: ${self.tenant_cost_today:.4f} > ${self.max_tenant_per_day_usd}"
        if self.process_cost_this_month > self.max_process_per_month_usd:
            return True, f"per-process: ${self.process_cost_this_month:.4f} > ${self.max_process_per_month_usd}"
        return False, ""

# Guardrail 4: Idempotency (built into ToolRegistry, from L6.3)

# Guardrail 5: Audit log
class AuditLog:
    def __init__(self, sink=print):
        self.entries = []
        self.sink = sink
    def record(self, event: str, **kwargs):
        entry = {"ts": time.time(), "event": event, **kwargs}
        self.entries.append(entry)
        self.sink(json.dumps(entry))  # Ship to log aggregation (CloudWatch, Datadog, etc.)
```

The 5 guardrails wrapped around the loop:

```python
def run_agent_with_5_guardrails(goal: str, agent: SingleAgent) -> dict:
    messages = [{"role": "system", "content": agent.system_prompt},
                {"role": "user", "content": goal}]
    for turn in range(1, agent.max_turns + 1):
        # Guardrail 3: cost ceiling check (3 levels)
        breached, reason = agent.cost.breached()
        if breached:
            agent.audit_log.record("cost_ceiling_breached", turn=turn, reason=reason)
            return {"error": "cost_ceiling_breached", "reason": reason, "turns": turn}

        # Decision
        output = agent.model.fn(messages)
        agent.cost.record(agent.model, len(str(messages)) // 4, len(output) // 4)
        messages.append({"role": "assistant", "content": output})
        agent.audit_log.record("llm_call", turn=turn, cost=agent.cost.run_cost)

        # Parse
        step = parse_step(output)
        if step["type"] == "final":
            agent.audit_log.record("final", turn=turn, answer=step["answer"])
            return {"answer": step["answer"], "turns": turn, "cost_usd": agent.cost.run_cost}
        if step["type"] == "malformed":
            messages.append({"role": "tool", "content": json.dumps({"_ok": False, "_err": "malformed", "hint": step["hint"]})})
            agent.audit_log.record("malformed", turn=turn)
            continue

        # Tool call (with Guardrail 2: schema validation, Guardrail 4: idempotency)
        try:
            args = json.loads(step["args_raw"])
        except Exception:
            args = {"raw": step["args_raw"]}
        result = agent.tools.call(step["tool"], args)

        # Guardrail 1: loop detection
        if agent.loop_detector.record(step["tool"]):
            agent.audit_log.record("loop_detected", tool=step["tool"])
            return {"error": "loop_detected", "tool": step["tool"], "turns": turn}

        messages.append({"role": "tool", "content": json.dumps(result)})
        agent.audit_log.record("tool_call", turn=turn, tool=step["tool"], args=args, result=result, cost=agent.cost.run_cost)

    return {"error": "max_turns_reached", "turns": agent.max_turns}
```

The pattern that wins interviews is the "5 guardrails + 3-level cost ceiling + cost as a score" pattern. The candidate who says "the 5 production guardrails are loop detector, schema validator, cost ceiling, idempotency, audit log. The cost ceiling is enforced at 3 levels: per-run, per-tenant, per-process. **The cost is the first-class metric on the dashboard, the on-call alert, the CFO report.** The wrong choice is no cost ceiling (a confused agent spends the customer's monthly budget in 6 hours). The right choice is all 3 levels + cost as a score" is the candidate who demonstrates the guardrail-mindset.

## Code or example

The 3-level cost ceiling enforcement:

```python
COST_CEILINGS = {
    "cs_drafter": CostCeiling(
        max_run_usd=0.50,                    # per-run: $0.50
        max_tenant_per_day_usd=5.00,         # per-tenant per-day: $5
        max_process_per_month_usd=1000.00,   # per-process per-month: $1000
    ),
    "research_agent": CostCeiling(
        max_run_usd=5.00,                    # per-run: $5 (research is more expensive)
        max_tenant_per_day_usd=50.00,
        max_process_per_month_usd=5000.00,
    ),
    "data_analyst": CostCeiling(
        max_run_usd=2.00,
        max_tenant_per_day_usd=20.00,
        max_process_per_month_usd=2000.00,
    ),
}

# The cost dashboard (Prometheus metrics)
COST_PER_RUN = Histogram("agent_cost_per_run_usd", "USD per agent run",
                          buckets=[0.01, 0.05, 0.10, 0.50, 1.00, 5.00])
CEILING_UTILIZATION = Gauge("agent_ceiling_utilization_ratio",
                              "Fraction of ceiling used (0.0 - 1.0)")

def record_run_complete(run_cost_usd: float, ceiling_usd: float):
    COST_PER_RUN.observe(run_cost_usd)
    CEILING_UTILIZATION.set(run_cost_usd / ceiling_usd)
```

The cost as a score (the dashboard view):

```python
# On-call dashboard (3am view)
DASHBOARD_VIEW = {
    "last_24h": {
        "cost_per_run_p50": 0.012,
        "cost_per_run_p95": 0.045,
        "cost_per_run_p99": 0.120,
        "cost_per_tenant_per_day": {"mei": 2.30, "sarah": 1.50, "daniel": 0.80},
        "total_cost_per_month": 297.45,  # out of $1000 budget = 30% used
        "ceiling_utilization": 0.30,  # < 80%, no alert
    },
    "alerts": [],  # No alerts; all under 80%
}

# The on-call checks this every shift. The cost is the first number they look at.
```

The cost-aware model router (the FDE's lever):

```python
def pick_model_within_budget(task: str, remaining_budget_usd: float) -> str:
    """Pick the model whose cost-per-step fits the remaining budget."""
    if remaining_budget_usd < 0.01:
        return "gpt-5-mini"  # Cheapest option when budget is tight
    if remaining_budget_usd < 0.05 and task in ("planning", "synthesis"):
        return "gpt-5-mini"  # Downgrade hard steps when budget is tight
    return pick_model(task)  # Default: pick by task
```

## Production addendum

The guardrails question is the answer to "what guardrails do you ship with an agent." The 60-second script:

> "5 production guardrails. Loop detector (catches confused iterations on the same tool). Schema validator (catches malformed tool calls, returns structured 403). Cost ceiling (catches budget blowouts at 3 levels: per-run, per-tenant, per-process). Idempotency (prevents double-writes on retries via sha256(args) cache). Audit log (the artifact the on-call reads at 3am). **The cost ceiling is the most important; it is the first guardrail the FDE writes.** The cost is the first-class metric on the dashboard, the on-call alert, the CFO report. The wrong choice is to ship without a cost ceiling (a confused agent spends the customer's monthly budget in 6 hours). The right choice is all 5 guardrails + the 3-level cost ceiling + the cost as a score."

This is the difference between a candidate who says "we have guardrails" and a candidate who says "5 guardrails (loop, schema, cost, idempotency, audit), 3-level cost ceiling (per-run, per-tenant, per-process), cost as a first-class metric on the dashboard." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-5-agents/lesson-9-6-production-agents.py` — the full 5-guardrail shipping agent.
- **Reference implementation**: `course/practice/level-6-production/lesson-11-3-cost-tracking.py` — the production cost tracker.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/06-cost-ceiling.md` — the cost ceiling as a first-class pattern.
- **Phase 4 project**: `course/ai-fde/phase-3-capstone/projects/03-distilled-slm/` — the SLM as the cost-ceiling enabler.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — guardrails as a system design pattern.

## The 3 questions this lecture preps you for

1. **"What guardrails do you ship with an agent?"** Answer: 5 guardrails. (1) Loop detector — catches confused iterations on the same tool. (2) Schema validator — catches malformed tool calls, returns structured 403. (3) Cost ceiling — catches budget blowouts at 3 levels (per-run, per-tenant, per-process). (4) Idempotency — prevents double-writes on retries via sha256(args) cache. (5) Audit log — the artifact the on-call reads at 3am.
2. **"What are the 3 levels of the cost ceiling?"** Answer: per-run ($0.50 default, catches the immediate failure), per-tenant per-day ($5 default, catches the customer-level failure), per-process per-month ($1000 default, catches the FDE-level failure). All 3 are necessary; the per-run alone misses the slow failure; the per-tenant alone misses the systemic failure.
3. **"What is the cost-as-a-first-class-metric pattern?"** Answer: the cost is not a backstop; it is the score. The dashboard shows cost-per-run (p50, p95, p99), cost per tenant per day, total cost per process per month, % of ceiling used. The on-call gets paged when any of these exceeds 80% of the ceiling. The CFO gets a monthly report. The customer sees the cost in their dashboard. **The cost is the metric the business reads.**

## Read next

`L6-6-testing-and-evaluation.md` — the 6th lecture. The eval set is the spec; the contract tests are the gate; the regression checks are the safety net; the A/B tests are the optimization lever. The FDE ships an eval set with every agent.