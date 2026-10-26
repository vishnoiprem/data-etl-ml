# L6.8: Monitoring and observability — the 3am dashboard

> **FDE framing in one line:** monitoring is the FDE's 3am dashboard. The 4 metrics, the 3 logs, the 2 traces tell the on-call whether the agent is healthy. The dashboard is the artifact that turns a black box into a glass box.

## In 60 seconds

> "4 metrics. Cost (per-run p50/p95/p99, per-tenant per-day, per-process per-month). Latency (per-run p50/p95/p99, by-step, by-tool). Success rate (% of runs that finish). Error rate by category (parse, schema, cost, tool, model). 3 logs: audit (every step), error (every exception), cost (every LLM + tool call). 2 traces: per-request (the full run), per-step (one LLM + tool call). **The dashboard is the artifact the on-call reads at 3am; the alerts are the gate.** The wrong choice is to ship without monitoring (you can't debug what you can't see). The right choice is the 4 + 3 + 2 + alerts as the contract."

**The wrong choice is to read past this block.** The right choice is to recite the 60-second script before you read any other content. The rest of the lecture is the receipt; this is the punchline.

## The 3 things you'll learn

1. The 4 metrics: cost (per-run p50/p95/p99), latency (per-run p50/p95/p99), success rate (% of runs that finish without error), error rate by category (parse, schema, cost, tool, model).
2. The 3 logs: structured audit log (every step), error log (every exception), cost log (every LLM + tool call). The 2 traces: per-request trace (the full agent run), per-step trace (one LLM + tool call).
3. The "dashboard as the contract" pattern: the dashboard is the artifact the customer sees; the on-call sees; the CFO sees. The metrics are the contract; the alerts are the gate.

## Concept

Monitoring and observability is the 8th layer of the shipping agent. The 4 metrics, the 3 logs, the 2 traces tell the on-call whether the agent is healthy. **The dashboard is the artifact that turns a black box into a glass box.** The candidate who can name the 4 metrics + the 3 logs + the 2 traces + the alert thresholds is the candidate who can ship a production agent.

The 4 metrics:

1. **Cost (per-run p50/p95/p99).** The USD cost per agent run, broken down by p50 (median), p95 (95th percentile), p99 (99th percentile). The dashboard shows: cost-per-run histogram, cost-per-tenant-per-day, total-cost-per-process-per-month. The alert: p95 > 2× baseline, or any tenant > 80% of the per-day ceiling.
2. **Latency (per-run p50/p95/p99).** The wall-clock time per agent run. The dashboard shows: latency-per-run histogram, latency-by-step (which LLM call is slowest), latency-by-tool (which tool is slowest). The alert: p95 > 2× baseline, or p99 > 10× baseline.
3. **Success rate (% of runs that finish without error).** The percentage of agent runs that emit a `Final Answer` without hitting a guardrail. The dashboard shows: success-rate-over-time, success-rate-by-tenant, success-rate-by-tool. The alert: success rate < 95%, or any tenant < 90%.
4. **Error rate by category.** The breakdown of errors by category: parse errors (malformed model output), schema errors (wrong args), cost errors (ceiling breached), tool errors (exception), model errors (API timeout). The dashboard shows: error-rate-over-time, error-rate-by-category. The alert: any error category > 5%, or any sudden spike.

The 3 logs:

1. **Structured audit log.** Every step in the agent loop: turn, event, tool, args, result, cost, tokens. The log is shipped to CloudWatch / Datadog / Loki. The on-call searches the log by request_id, by tenant, by error category.
2. **Error log.** Every exception caught by the agent framework. The log includes: stack trace, request_id, tenant, step number, input args, model output (truncated to 1KB). The on-call reads the error log to triage.
3. **Cost log.** Every LLM call and every tool call: timestamp, model, input_tokens, output_tokens, USD_cost, tenant, request_id. The cost log is the source for the cost dashboard.

The 2 traces:

1. **Per-request trace.** The full agent run: system prompt, user message, every assistant message, every tool call, every observation, the final answer. The trace is shipped to OpenTelemetry / Jaeger / Honeycomb. The on-call replays the trace to understand the run.
2. **Per-step trace.** One LLM call + one tool call: model, input, output, tool name, tool args, tool return, latency, cost. The per-step trace is the building block of the per-request trace.

The "dashboard as the contract" pattern is the recognition that the dashboard is the artifact the on-call reads, the customer sees, the CFO reviews. The metrics are the contract; the alerts are the gate; the dashboard is the implementation. **The candidate who names the 4 metrics + the 3 logs + the 2 traces + the alert thresholds is the candidate who can monitor a production agent.**

## The pattern

The 4 metrics + the alert thresholds:

```python
# Cost metrics
COST_PER_RUN = Histogram("agent_cost_per_run_usd", "USD per agent run",
                          buckets=[0.01, 0.05, 0.10, 0.50, 1.00, 5.00])
COST_PER_TENANT_PER_DAY = Gauge("agent_cost_per_tenant_per_day_usd",
                                 "USD per tenant per day", ["tenant"])
COST_PER_PROCESS_PER_MONTH = Gauge("agent_cost_per_process_per_month_usd",
                                    "USD per process per month")
# Alert: p95 > 2× baseline, or any tenant > 80% of the per-day ceiling

# Latency metrics
LATENCY_PER_RUN = Histogram("agent_latency_per_run_s", "Seconds per agent run",
                             buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0])
LATENCY_BY_STEP = Histogram("agent_latency_per_step_s", "Seconds per step",
                             ["step_type"], buckets=[0.1, 0.5, 1.0, 2.0, 5.0])
# Alert: p95 > 2× baseline, or p99 > 10× baseline

# Success rate
SUCCESS_RATE = Gauge("agent_success_rate", "Fraction of runs that finish without error")
# Alert: success rate < 95%

# Error rate by category
ERROR_RATE_BY_CATEGORY = Counter("agent_error_rate_by_category",
                                   "Errors by category", ["category"])  # noqa
# Categories: parse, schema, cost, tool, model
# Alert: any category > 5%, or any sudden spike
```

The 3 logs (the structured logging):

```python
import logging, json

# Audit log: every step
audit_logger = logging.getLogger("agent.audit")
audit_logger.info(json.dumps({
    "ts": time.time(),
    "request_id": request_id,
    "tenant": tenant,
    "turn": turn,
    "event": "tool_call",
    "tool": "tracker.lookup",
    "args": {"shipment_id": "PF-1003"},
    "result": {"status": "in_transit"},
    "cost_usd": 0.001,
}))

# Error log: every exception
error_logger = logging.getLogger("agent.error")
try:
    result = tool.call(name, args)
except Exception as e:
    error_logger.error(json.dumps({
        "ts": time.time(),
        "request_id": request_id,
        "tenant": tenant,
        "step": turn,
        "tool": name,
        "args": args,
        "exception": str(e),
        "traceback": traceback.format_exc(),
    }))

# Cost log: every LLM + tool call
cost_logger = logging.getLogger("agent.cost")
cost_logger.info(json.dumps({
    "ts": time.time(),
    "request_id": request_id,
    "tenant": tenant,
    "model": "gpt-5-mini",
    "input_tokens": 1234,
    "output_tokens": 567,
    "cost_usd": 0.0008,
}))
```

The 3am dashboard (the on-call's view):

```python
DASHBOARD_PANELS = {
    "cost": {
        "cost_per_run_p50": "$0.012",
        "cost_per_run_p95": "$0.045",
        "cost_per_run_p99": "$0.120",
        "cost_per_tenant_per_day": {"mei": "$2.30", "sarah": "$1.50", "daniel": "$0.80"},
        "total_cost_per_month": "$297.45 / $1000 budget = 30%",
        "alert": "none (under 80%)",
    },
    "latency": {
        "latency_p50": "1.2s",
        "latency_p95": "3.5s",
        "latency_p99": "8.0s",
        "alert": "none (within baseline)",
    },
    "success_rate": {
        "overall": "98.5%",
        "by_tenant": {"mei": "99.0%", "sarah": "98.0%", "daniel": "98.5%"},
        "alert": "none (above 95%)",
    },
    "errors_by_category": {
        "parse": "0.5%",
        "schema": "0.3%",
        "cost": "0.1%",
        "tool": "0.4%",
        "model": "0.2%",
        "alert": "none (all under 5%)",
    },
}
```

The pattern that wins interviews is the "4 metrics + 3 logs + 2 traces + alert thresholds" pattern. The candidate who says "I monitor 4 metrics (cost, latency, success rate, error rate by category), log 3 streams (audit, error, cost), trace 2 levels (per-request, per-step). The dashboard is the artifact the on-call reads at 3am; the alerts are the gate; the metrics are the contract. The wrong choice is to ship without monitoring (you can't debug what you can't see). The right choice is the 4 + 3 + 2 + alerts" is the candidate who demonstrates the observability-mindset.

## Code or example

The alert thresholds (the production rules):

```yaml
# alerts.yaml
alerts:
  cost_p95_breach:
    condition: cost_per_run_p95 > 2 * baseline_p95
    severity: warning
    action: page on-call
  cost_per_tenant_breach:
    condition: cost_per_tenant_per_day > 0.8 * ceiling_per_tenant_per_day
    severity: warning
    action: page on-call, notify customer
  cost_per_process_breach:
    condition: cost_per_process_per_month > 0.8 * ceiling_per_process_per_month
    severity: critical
    action: page on-call + CFO
  latency_p95_breach:
    condition: latency_p95 > 2 * baseline_p95
    severity: warning
    action: page on-call
  success_rate_below_95:
    condition: success_rate < 0.95
    severity: warning
    action: page on-call
  error_category_spike:
    condition: any error category > 5% OR 2× baseline
    severity: warning
    action: page on-call
```

The OpenTelemetry trace (the per-request trace):

```python
from opentelemetry import trace
tracer = trace.get_tracer("agent")

def run_agent_with_tracing(goal: str, agent: SingleAgent) -> dict:
    with tracer.start_as_current_span("agent_run") as span:
        span.set_attribute("request_id", request_id)
        span.set_attribute("tenant", tenant)
        span.set_attribute("goal", goal[:200])
        messages = [{"role": "system", "content": agent.system_prompt}, {"role": "user", "content": goal}]
        for turn in range(1, agent.max_turns + 1):
            with tracer.start_as_current_span(f"turn_{turn}") as turn_span:
                # Cost check
                if agent.cost.breached():
                    turn_span.set_attribute("error", "cost_ceiling_breached")
                    return {"error": "cost_ceiling_breached"}
                # LLM call
                with tracer.start_as_current_span("llm_call") as llm_span:
                    output = agent.model.fn(messages)
                    llm_span.set_attribute("model", agent.model.name)
                    llm_span.set_attribute("cost_usd", agent.cost.run_cost)
                # Parse + dispatch
                # ...
        span.set_attribute("answer", step["answer"][:200])
        return {"answer": step["answer"], "turns": turn}
```

The PacificFreight monitoring setup (the canonical FDE use case):

```python
# PacificFreight runs on Daniel's VM; monitoring is via Prometheus + Grafana
# Metrics: scraped every 15s by node_exporter
# Logs: shipped to Loki via promtail
# Traces: shipped to Jaeger via OpenTelemetry
# Alerts: Alertmanager → PagerDuty

# The 3am dashboard (Grafana):
# - Panel 1: Cost per run (p50/p95/p99)
# - Panel 2: Latency per run (p50/p95/p99)
# - Panel 3: Success rate over time
# - Panel 4: Errors by category
# - Panel 5: Cost per tenant per day
# - Panel 6: Total cost per month vs budget
```

## Production addendum

The monitoring question is the answer to "how do you monitor an agent in production." The 60-second script:

> "4 metrics. Cost (per-run p50/p95/p99, per-tenant per-day, per-process per-month). Latency (per-run p50/p95/p99, by-step, by-tool). Success rate (% of runs that finish). Error rate by category (parse, schema, cost, tool, model). 3 logs: audit (every step), error (every exception), cost (every LLM + tool call). 2 traces: per-request (the full run), per-step (one LLM + tool call). **The dashboard is the artifact the on-call reads at 3am; the alerts are the gate.** The wrong choice is to ship without monitoring (you can't debug what you can't see). The right choice is the 4 + 3 + 2 + alerts as the contract."

This is the difference between a candidate who says "we have logs" and a candidate who says "4 metrics, 3 logs, 2 traces, alert thresholds, dashboard as the contract, 3am recovery playbook." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-core-build/service/telemetry.py` — the production telemetry.
- **Reference implementation**: `course/hardcode/level-8-evaluation-testing/11-llm-as-judge-eval.py` — the production monitoring setup.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — monitoring as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — the orchestrator's monitoring setup.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — monitoring as a system design pattern.

## The 3 questions this lecture preps you for

1. **"How do you monitor an agent in production?"** Answer: 4 metrics (cost, latency, success rate, error rate by category), 3 logs (audit, error, cost), 2 traces (per-request, per-step). The dashboard is the artifact the on-call reads at 3am; the alerts are the gate; the metrics are the contract. The alert thresholds: p95 cost > 2× baseline, p95 latency > 2× baseline, success rate < 95%, any error category > 5%.
2. **"What is the difference between metrics, logs, and traces?"** Answer: metrics are aggregated numbers (cost per run, latency p95, success rate) — fast to query, good for dashboards. Logs are discrete events (audit log, error log) — good for debugging specific runs. Traces are the full request lifecycle (per-request, per-step) — good for replaying a specific run. **The 3 are not interchangeable; the FDE needs all 3.**
3. **"What are the alert thresholds for an agent?"** Answer: cost p95 > 2× baseline (warning), any tenant > 80% of per-day ceiling (warning, notify customer), process > 80% of per-month ceiling (critical, page CFO), latency p95 > 2× baseline (warning), success rate < 95% (warning), any error category > 5% or 2× baseline (warning). **The alerts are the gate; they catch the failures before the customer notices.**

## Read next

`L6-9-error-handling-and-recovery.md` — the 9th lecture. The 4 error categories: transient (retry), permanent (escalate), model (re-plan), tool (fallback). The retry/replan/escalate/fallback strategies for each.