# L8.6: Cost management at scale — per-tenant tracking, budget alerts, FinOps

> **FDE framing in one line:** cost management is the FDE's CFO conversation. The agent costs money; the customer wants to know how much, per-tenant, per-day, per-month, with alerts before the bill surprises them. The 3 levels (per-run, per-tenant per-day, per-process per-month) match the budget conversations the CFO has. The wrong choice is to ignore cost (the bill surprises the customer); the right choice is the 3 levels + budget alerts + FinOps discipline.

## The 3 things you'll learn

1. The 3 levels of cost tracking: per-run (every LLM + tool call is metered), per-tenant per-day (the customer's daily bill), per-process per-month (the FDE's monthly bill). Each level answers a different question; the FDE needs all 3.
2. The 4 cost optimization levers: model selection (gpt-5-mini vs gpt-5), cost-aware routing (cheap model for routine steps), caching (idempotency + response cache), batching (combine multiple requests). Each lever reduces cost; the FDE picks the lever that matches the workload.
3. The "FinOps as a discipline" pattern: cost is a first-class metric; the FDE tracks cost daily, alerts on budget breaches, reviews cost weekly, optimizes cost monthly. The discipline is the same as monitoring uptime or latency — cost is a feature, not an afterthought.

## Concept

Cost management is the FDE's conversation with the CFO. The agent costs money: LLM API calls, infrastructure, observability, secrets management, security tools. The CFO wants to know: how much per customer? how much per month? what's the trend? what happens at 10× scale? **The wrong choice is to ship without cost tracking (the bill surprises the customer in month 2). The right choice is the 3 levels + budget alerts + FinOps discipline.**

The 3 levels of cost tracking (from Section 2.4):

1. **Per-run.** Every agent run is metered. The FDE records: timestamp, tenant, request_id, model, input_tokens, output_tokens, tool_calls (and their cost), total_cost_usd. The per-run cost is the granular view; the FDE uses it to identify expensive runs (which customer? which use case? which model?).
2. **Per-tenant per-day.** The customer's daily bill. The FDE aggregates per-run costs by tenant + day. The per-tenant per-day cost is the customer's view; the customer wants to know "how much did I use today" and "how much of my budget is left."
3. **Per-process per-month.** The FDE's monthly bill. The FDE aggregates per-tenant per-day costs across all tenants + all days. The per-process per-month cost is the FDE's view; the FDE wants to know "is the project profitable" and "are we within budget."

The 4 cost optimization levers:

1. **Model selection.** The right model for the right step. The FDE uses gpt-5-mini for routine steps (classification, extraction, simple Q&A) and gpt-5 for hard steps (planning, synthesis, complex tool use). The lever saves 5-10× per token. The FDE's default: gpt-5-mini; gpt-5 only when the eval set proves the need.
2. **Cost-aware routing.** Cheap model for routine steps, expensive model for hard steps. The FDE adds a router (per L2.1) that picks the model based on the step. The lever saves 5-15× per run when the agent has many routine steps and few hard steps.
3. **Caching.** The FDE caches (1) idempotent tool calls (don't call the same tool with the same args twice; L6.3 pattern), (2) LLM responses (don't call the same prompt twice; use a Redis cache with a 1-hour TTL). The lever saves 30-50% of cost when the workload has repeat queries.
4. **Batching.** The FDE combines multiple requests into one LLM call (e.g., "classify these 10 emails" instead of 10 separate calls). The lever saves 2-5× per call when the workload has many similar requests.

The "FinOps as a discipline" pattern is the recognition that cost is a first-class metric. The FDE tracks cost daily, alerts on budget breaches, reviews cost weekly, optimizes cost monthly. **The discipline is the same as monitoring uptime or latency — cost is a feature, not an afterthought.** The FDE who says "cost is a first-class metric, like uptime and latency" is the FDE who can defend the budget to the CFO.

## The pattern

The 3 levels of cost tracking (the FDE's reference):

```python
COST_LEVELS = {
    "per_run": {
        "what": "Every agent run is metered: timestamp, tenant, request_id, model, input_tokens, output_tokens, tool_calls, total_cost_usd",
        "where_stored": "Postgres (cost_events table) + OpenTelemetry metrics (agent_cost_per_run_usd)",
        "questions_answered": "Which run is the most expensive? Which model is the most expensive? Which tenant is the most expensive per-run?",
        "alert_threshold": "any run > 5x the average run cost",
        "retention": "90 days (then aggregate)",
    },
    "per_tenant_per_day": {
        "what": "Sum of per-run costs grouped by tenant + day",
        "where_stored": "Postgres (cost_daily table) + OpenTelemetry metrics (agent_cost_per_tenant_per_day_usd)",
        "questions_answered": "How much did tenant X use today? How much of tenant X's budget is left?",
        "alert_threshold": "any tenant > 80% of per-day ceiling",
        "retention": "1 year",
    },
    "per_process_per_month": {
        "what": "Sum of per-tenant per-day costs across all tenants + all days",
        "where_stored": "Postgres (cost_monthly table) + OpenTelemetry metrics (agent_cost_per_process_per_month_usd)",
        "questions_answered": "Is the project profitable? Are we within budget? What is the cost trend?",
        "alert_threshold": "> 80% of per-month budget (critical alert; page CFO)",
        "retention": "indefinite",
    },
}
```

The 4 cost optimization levers compared:

```python
COST_LEVERS = {
    "model_selection": {
        "description": "Pick the right model for the right step",
        "example": "gpt-5-mini for classification, gpt-5 for planning",
        "savings": "5-10x per token",
        "tradeoff": "lower accuracy on hard steps",
        "when_to_use": "Always (the default)",
    },
    "cost_aware_routing": {
        "description": "Router picks the model based on the step",
        "example": "Cheap model for routine; expensive model for hard",
        "savings": "5-15x per run",
        "tradeoff": "router adds complexity; need a router logic",
        "when_to_use": "Agent has >5 steps with mixed complexity",
    },
    "caching": {
        "description": "Cache idempotent tool calls + LLM responses",
        "example": "Redis cache with 1-hour TTL for LLM responses",
        "savings": "30-50% when workload has repeat queries",
        "tradeoff": "stale cache risk; cache key management",
        "when_to_use": "Workload has repeat queries (FAQ, common templates)",
    },
    "batching": {
        "description": "Combine multiple requests into one LLM call",
        "example": "Classify 10 emails in one call instead of 10 calls",
        "savings": "2-5x per call",
        "tradeoff": "higher latency per call; batching overhead",
        "when_to_use": "Workload has many similar requests arriving in a short window",
    },
}
```

The per-run cost tracking (the FDE's instrumentation):

```python
import tiktoken

class CostTracker:
    """Track the cost of every agent run."""

    PRICING = {
        # 2026 LLM pricing (per 1M tokens)
        "gpt-5": {"input": 2.50, "output": 10.00},
        "gpt-5-mini": {"input": 0.15, "output": 0.60},
        "claude-sonnet-4.5": {"input": 3.00, "output": 15.00},
        "claude-haiku-4.5": {"input": 0.80, "output": 4.00},
    }

    def __init__(self, db, metrics):
        self.db = db
        self.metrics = metrics

    def record_llm_call(self, model: str, input_tokens: int, output_tokens: int, tenant: str, request_id: str):
        cost_usd = (
            input_tokens / 1_000_000 * self.PRICING[model]["input"]
            + output_tokens / 1_000_000 * self.PRICING[model]["output"]
        )
        # Write to Postgres
        self.db.execute(
            "INSERT INTO cost_events (ts, tenant, request_id, kind, model, input_tokens, output_tokens, cost_usd) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (datetime.utcnow(), tenant, request_id, "llm_call", model, input_tokens, output_tokens, cost_usd),
        )
        # Emit OpenTelemetry metric
        self.metrics.histogram("agent_cost_per_call_usd", cost_usd, {"model": model, "tenant": tenant})
        return cost_usd

    def record_tool_call(self, tool: str, cost_credits: int, tenant: str, request_id: str):
        cost_usd = cost_credits * 0.001  # 1 credit = $0.001
        self.db.execute(
            "INSERT INTO cost_events (ts, tenant, request_id, kind, tool, cost_credits, cost_usd) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (datetime.utcnow(), tenant, request_id, "tool_call", tool, cost_credits, cost_usd),
        )
        return cost_usd
```

The per-tenant per-day cost dashboard (the CFO's view):

```python
TENANT_COST_DASHBOARD = {
    "panel_1_today": {
        "type": "table",
        "title": "Cost per tenant (today)",
        "query": "SELECT tenant, SUM(cost_usd) AS cost_today, MAX(per_day_ceiling_usd) AS ceiling, SUM(cost_usd) / MAX(per_day_ceiling_usd) AS pct_used FROM cost_events WHERE DATE(ts) = CURRENT_DATE GROUP BY tenant",
        "columns": ["tenant", "cost_today", "ceiling", "pct_used", "alert"],
    },
    "panel_2_trend": {
        "type": "graph",
        "title": "Cost trend per tenant (last 30 days)",
        "query": "SELECT DATE(ts) AS day, tenant, SUM(cost_usd) AS cost FROM cost_events WHERE ts > NOW() - INTERVAL '30 days' GROUP BY DATE(ts), tenant",
        "x_axis": "day",
        "y_axis": "cost_usd",
        "series": "tenant",
    },
    "panel_3_top_tenants": {
        "type": "table",
        "title": "Top 10 tenants by cost (last 30 days)",
        "query": "SELECT tenant, SUM(cost_usd) AS cost_30d FROM cost_events WHERE ts > NOW() - INTERVAL '30 days' GROUP BY tenant ORDER BY cost_30d DESC LIMIT 10",
    },
    "panel_4_budget_alerts": {
        "type": "alert_list",
        "title": "Budget alerts",
        "alerts": [
            {"tenant": "acme", "pct_used": 0.85, "severity": "warning", "action": "notify customer"},
            {"tenant": "beta", "pct_used": 0.95, "severity": "critical", "action": "page on-call + notify customer"},
        ],
    },
}
```

The FinOps discipline (the FDE's monthly cadence):

```python
FINOPS_DISCIPLINE = {
    "daily": {
        "duration_min": 5,
        "actions": [
            "Check the cost dashboard for any tenant > 80% of per-day ceiling",
            "Check the per-process cost is on track for the month",
            "Check the per-run cost is within baseline (no anomalies)",
        ],
        "output": "Slack #finops: daily cost summary",
    },
    "weekly": {
        "duration_min": 30,
        "actions": [
            "Review the cost trend per tenant (which tenants are growing? which are shrinking?)",
            "Review the most expensive runs (which model? which use case? optimization opportunity?)",
            "Review the cost per step (which step is the most expensive? batching? caching?)",
            "Identify 1 cost optimization opportunity (model change, caching, batching)",
        ],
        "output": "Weekly FinOps report (1 page); 1 optimization task added to the backlog",
    },
    "monthly": {
        "duration_min": 120,
        "actions": [
            "Review the per-process per-month cost vs budget",
            "Review the cost trend (is the project profitable? is the cost growing faster than usage?)",
            "Review the cost optimization wins from the last month",
            "Forecast the next month's cost (based on the trend + planned new customers)",
            "Present to the CFO: cost actual vs budget, trend, forecast, optimization plan",
        ],
        "output": "Monthly FinOps report + CFO presentation",
    },
}
```

The pattern that wins interviews is the "3 levels + 4 levers + FinOps discipline" pattern. The candidate who says "I track cost at 3 levels (per-run, per-tenant per-day, per-process per-month); I optimize with 4 levers (model selection, cost-aware routing, caching, batching); I run FinOps daily/weekly/monthly. The wrong choice is to ship without cost tracking (the bill surprises the customer). The right choice is the 3 levels + 4 levers + the FinOps discipline" is the candidate who demonstrates the FinOps-mindset.

## Code or example

The 5 most common cost errors and fixes:

```python
COST_ERRORS = {
    "bill_shock": {
        "symptom": "Customer's bill is 10x higher than expected in month 2",
        "cause": "Cost was not tracked; the customer's usage grew; no per-tenant budget",
        "fix": "Add per-tenant per-day cost tracking; add budget alerts at 80%; review cost with the customer monthly",
    },
    "expensive_model_for_easy_task": {
        "symptom": "Cost per run is high; the agent uses gpt-5 for classification",
        "cause": "Default model is gpt-5; routine steps use gpt-5",
        "fix": "Switch routine steps to gpt-5-mini; add cost-aware routing; verify the accuracy is still acceptable",
    },
    "no_caching": {
        "symptom": "Same tool call is made 100 times; cost is 100x the necessary",
        "cause": "No idempotency cache; no LLM response cache",
        "fix": "Add an idempotency cache for tool calls (L6.3 pattern); add an LLM response cache for common queries",
    },
    "no_batching": {
        "symptom": "100 emails are processed one at a time; cost is 100 LLM calls",
        "cause": "Each email is a separate agent run",
        "fix": "Batch 10 emails into one agent run; process 100 emails in 10 runs (saves 90% of LLM calls)",
    },
    "model_drift": {
        "symptom": "Cost per run increases over time without a corresponding value increase",
        "cause": "Model upgrade (gpt-4 → gpt-5) without a re-evaluation; system prompt changes that cause the model to call more tools",
        "fix": "Track cost per run over time; alert on > 20% cost increase week-over-week; investigate the prompt or model change",
    },
}
```

The 4 budget alert patterns (the FDE's reference):

```python
BUDGET_ALERTS = {
    "soft_alert": {
        "condition": "per-tenant per-day cost > 60% of per-day ceiling",
        "severity": "info",
        "action": "Slack #finops: 'tenant X is at 60% of daily ceiling'",
        "frequency": "Once per day",
    },
    "warning_alert": {
        "condition": "per-tenant per-day cost > 80% of per-day ceiling",
        "severity": "warning",
        "action": "Slack #oncall + email to customer's account manager: 'tenant X is at 80% of daily ceiling; consider raising the ceiling'",
        "frequency": "Once per day",
    },
    "critical_alert": {
        "condition": "per-tenant per-day cost > 95% of per-day ceiling",
        "severity": "critical",
        "action": "Page on-call + customer's account manager + customer's technical contact: 'tenant X is at 95%; the agent will be rate-limited tomorrow'",
        "frequency": "Once per day; or immediately when the threshold is crossed",
    },
    "process_breach_alert": {
        "condition": "per-process per-month cost > 80% of per-month budget",
        "severity": "critical",
        "action": "Page FDE on-call + CFO: 'project X is at 80% of monthly budget'",
        "frequency": "Once per week (or immediately when crossed)",
    },
}
```

The AtlasMart cost management (the case study):

```python
ATLASMART_COST = {
    "monthly_target": "$200",
    "cost_breakdown": {
        "llm_api_calls": {"monthly_usd": 100, "percentage": 50, "per_run_usd": 0.001, "monthly_runs": 100_000},
        "infrastructure": {"monthly_usd": 80, "percentage": 40, "details": "K8s + Postgres + Redis + S3 + CloudWatch"},
        "observability": {"monthly_usd": 30, "percentage": 15, "details": "Grafana Cloud + Prometheus + Loki + Tempo"},
        "security": {"monthly_usd": 50, "percentage": 25, "details": "API Gateway + Secrets Manager + Auth0"},
        "total": {"monthly_usd": 200, "percentage": 100, "vs_budget": "on target"},
    },
    "optimization_levers": [
        {"lever": "model_selection", "implemented": True, "savings": "5x for routine steps"},
        {"lever": "cost_aware_routing", "implemented": True, "savings": "3x average per run"},
        {"lever": "caching", "implemented": True, "savings": "30% for repeat queries (FAQ)"},
        {"lever": "batching", "implemented": False, "potential_savings": "2x for batch workloads", "planned_date": "Q1 2027"},
    ],
    "alerts": [
        {"alert": "tenant_cost_warning", "threshold": "80% of per-day ceiling", "severity": "warning"},
        {"alert": "tenant_cost_critical", "threshold": "95% of per-day ceiling", "severity": "critical"},
        {"alert": "process_cost_breach", "threshold": "80% of per-month budget", "severity": "critical"},
        {"alert": "cost_per_run_anomaly", "threshold": "any run > 5x average", "severity": "warning"},
    ],
    "finops_cadence": {
        "daily": "Check dashboard; alert on breaches",
        "weekly": "Cost trend review; 1 optimization task",
        "monthly": "CFO presentation; cost actual vs budget; forecast",
    },
    "next_month_forecast": "$215 (10% growth from new tenants); still within budget",
}
```

## Production addendum

The cost management question is the answer to "how do you manage cost at scale." The 60-second script:

> "3 levels. Per-run (every LLM + tool call metered), per-tenant per-day (the customer's daily bill), per-process per-month (the FDE's monthly bill). 4 levers: model selection, cost-aware routing, caching, batching. FinOps discipline: daily dashboard check, weekly trend review, monthly CFO presentation. The wrong choice is to ship without cost tracking (the bill surprises the customer). The right choice is the 3 levels + 4 levers + FinOps + 4 budget alerts + the 5 most common errors."

This is the difference between a candidate who says "we track cost" and a candidate who says "3 levels, 4 levers, FinOps daily/weekly/monthly, 4 budget alerts (soft, warning, critical, process breach), the CFO presentation is the artifact." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-applications/service/cost.py` — the cost tracker.
- **Reference implementation**: `course/hardcode/level-8-infrastructure/06-cost.md` — the canonical cost management setup.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/19-cost-management.md` — cost management as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-3-capstone/projects/03-distilled-slm/` — the SLM is the cost lever.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/11-infrastructure.md` — cost management as a system design topic.

## The 3 questions this lecture preps you for

1. **"How do you manage cost at scale?"** Answer: 3 levels (per-run, per-tenant per-day, per-process per-month). 4 levers (model selection, cost-aware routing, caching, batching). FinOps discipline (daily/weekly/monthly). 4 budget alerts (soft, warning, critical, process breach). The CFO presentation is the artifact.
2. **"What are the 4 cost optimization levers?"** Answer: (1) model selection — gpt-5-mini for routine, gpt-5 for hard (5-10× savings); (2) cost-aware routing — cheap model for routine, expensive for hard (5-15× savings); (3) caching — idempotency + LLM response cache (30-50% savings); (4) batching — combine multiple requests (2-5× savings). The FDE picks the lever that matches the workload.
3. **"What is FinOps as a discipline?"** Answer: cost is a first-class metric (like uptime and latency). Daily: check dashboard, alert on breaches. Weekly: trend review, 1 optimization task. Monthly: CFO presentation, cost actual vs budget, forecast. The discipline is the same as monitoring uptime — cost is a feature, not an afterthought.

## Read next

`S9-ai-agents-in-business/L9-1-the-business-case-for-ai-agents.md` — Section 9 closes the course with the business case for AI agents. ROI, use cases, the customer conversation, the FDE's commercial toolkit. From agent to product to business.