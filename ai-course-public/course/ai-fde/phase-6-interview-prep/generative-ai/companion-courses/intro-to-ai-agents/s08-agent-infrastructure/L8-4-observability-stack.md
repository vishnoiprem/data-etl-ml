# L8.4: Observability stack — logs, metrics, traces, and the 3am dashboard

> **FDE framing in one line:** observability is the FDE's 3am dashboard. The 3 pillars (logs, metrics, traces) tell the on-call whether the agent is healthy. The right stack turns a black box into a glass box; the wrong stack leaves the on-call guessing. The FDE ships logs + metrics + traces from day 1; the dashboard is the artifact that turns data into a story.

## The 3 things you'll learn

1. The 3 pillars of observability: logs (discrete events, "what happened"), metrics (aggregated numbers, "how much / how fast"), traces (the full request lifecycle, "where did the time go"). The 3 are not interchangeable; the FDE needs all 3.
2. The 3 stack options: open-source (Prometheus + Grafana + Loki + Jaeger, $$ engineering depth), managed (Datadog, $$$ low complexity), cloud-native (CloudWatch + CloudWatch + X-Ray, $ mid complexity). The right choice depends on the team's engineering depth + the budget.
3. The "OpenTelemetry as the standard" pattern: OTel is the standard for logs + metrics + traces; the FDE instruments the agent with OTel; the FDE picks the backend (Jaeger, Honeycomb, Tempo) that matches the team's skill. The instrument-once pattern decouples instrumentation from storage.

## Concept

Observability is the FDE's ability to answer "what is happening inside the agent right now." The 3 pillars — logs, metrics, traces — answer 3 different questions. **Logs answer "what happened." Metrics answer "how much / how fast." Traces answer "where did the time go." The FDE needs all 3; the wrong choice is to ship without observability (the 3am page is a black box).**

The 3 pillars of observability:

1. **Logs.** Discrete events. Every step in the agent's run is a log entry: timestamp, request_id, tenant, event, level, message. The FDE uses logs to debug specific runs (the customer says "my run failed" → the FDE searches the logs by request_id). The right tool: Loki (open-source), CloudWatch Logs (managed), Datadog Logs (managed).
2. **Metrics.** Aggregated numbers. The agent emits metrics: cost_per_run histogram, latency_per_run histogram, success_rate gauge, error_rate_by_category counter. The FDE uses metrics to monitor the system (the dashboard shows p95 latency, success rate, cost). The right tool: Prometheus (open-source), CloudWatch Metrics (managed), Datadog Metrics (managed).
3. **Traces.** The full request lifecycle. Each request is a trace; each trace has spans (LLM call, tool call, observation). The FDE uses traces to understand latency and cost per step (which step is slow? which step is expensive?). The right tool: Jaeger (open-source), Tempo (open-source), Honeycomb (managed), X-Ray (managed).

The 3 stack options:

1. **Open-source (Prometheus + Grafana + Loki + Jaeger).** The FDE operates the stack; the engineering team maintains it. The right choice when the customer has an engineering team, has $0 budget for observability, or wants full control. The cost: $0 (software) + $50-200/month (infrastructure: 3-4 small VMs or a managed K8s cluster).
2. **Managed (Datadog).** Datadog does it all. The right choice when the customer has budget ($50-500/month), wants to skip the operational overhead, or has a small team. The cost: $0.10/host/month + $0.05/GB logs + $0.05/metric.
3. **Cloud-native (CloudWatch + X-Ray).** The cloud provider's native stack. The right choice when the customer is all-in on one cloud (AWS, GCP, Azure) and doesn't want to operate a separate observability stack. The cost: $0.30/GB logs + $0.30/million metric updates.

The "OpenTelemetry as the standard" pattern is the recognition that OTel is the standard for instrumentation. The FDE instruments the agent with OTel: every LLM call is a span; every tool call is a span; every metric is emitted via OTel; every log is structured. The OTel collector sends the data to the backend (Jaeger, Honeycomb, Datadog). **The instrument-once pattern decouples instrumentation from storage; the FDE can switch backends without changing the code.**

## The pattern

The 3 pillars × 3 stack options matrix (the FDE's reference):

```python
OBSERVABILITY_MATRIX = {
    "logs": {
        "open_source": "Loki + Grafana",
        "managed": "Datadog Logs",
        "cloud_native": "CloudWatch Logs",
        "what_to_log": ["agent.audit (every step)", "agent.error (every exception)", "agent.cost (every LLM + tool call)"],
        "retention": "7-30 days hot + 1 year cold (S3)",
        "query_pattern": "{tenant=\"mei\"} |= \"error\" | json | latency_ms > 5000",
    },
    "metrics": {
        "open_source": "Prometheus + Grafana",
        "managed": "Datadog Metrics",
        "cloud_native": "CloudWatch Metrics",
        "what_to_emit": ["Histogram: agent_cost_per_run_usd", "Histogram: agent_latency_per_run_s", "Gauge: agent_success_rate", "Counter: agent_error_total{category}"],
        "retention": "30 days high-res + 1 year down-sampled",
        "query_pattern": "histogram_quantile(0.95, sum(rate(agent_latency_per_run_s_bucket[5m])) by (le))",
    },
    "traces": {
        "open_source": "Jaeger + Tempo",
        "managed": "Honeycomb",
        "cloud_native": "X-Ray",
        "what_to_trace": ["agent.run (the full run)", "agent.llm_call (one LLM call)", "agent.tool_call (one tool call)"],
        "retention": "7-30 days",
        "query_pattern": "service:pf-agent trace_id:abc123 (Honeycomb) OR service.name=pf-agent traceId=abc123 (Jaeger)",
    },
}
```

The 3 stack options compared:

```python
STACK_OPTIONS = {
    "open_source": {
        "tools": "Prometheus (metrics) + Loki (logs) + Jaeger/Tempo (traces) + Grafana (dashboards)",
        "engineering_depth": "high (the team operates the stack)",
        "monthly_cost_usd": "50-200 (3-4 small VMs)",
        "best_for": "engineering-first, $0 budget for observability, full control",
        "weakness": "operational overhead; the team is on-call for the observability stack too",
    },
    "managed": {
        "tools": "Datadog (logs + metrics + traces + APM + RUM)",
        "engineering_depth": "low (Datadog does the work)",
        "monthly_cost_usd": "100-1000",
        "best_for": "small team, budget for observability, skip the operational overhead",
        "weakness": "expensive at scale; vendor lock-in",
    },
    "cloud_native": {
        "tools": "CloudWatch (logs + metrics) + X-Ray (traces)",
        "engineering_depth": "medium (managed but limited)",
        "monthly_cost_usd": "50-300",
        "best_for": "all-in on AWS/GCP/Azure, want native integration",
        "weakness": "limited features compared to Datadog; harder to debug across services",
    },
}
```

The OpenTelemetry instrumentation (the FDE's standard):

```python
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider

# Initialize OTel (at startup)
trace.set_tracer_provider(TracerProvider())
metrics.set_meter_provider(MeterProvider())

tracer = trace.get_tracer("agent")
meter = metrics.get_meter("agent")

# Define metrics
cost_per_run = meter.create_histogram(
    name="agent_cost_per_run_usd",
    unit="USD",
    description="USD per agent run",
)
latency_per_run = meter.create_histogram(
    name="agent_latency_per_run_s",
    unit="s",
    description="Seconds per agent run",
)
success_rate = meter.create_gauge(
    name="agent_success_rate",
    description="Fraction of runs that finish without error",
)
error_total = meter.create_counter(
    name="agent_error_total",
    description="Total errors by category",
)

# Instrument the agent
def run_agent_with_observability(goal: str, agent: SingleAgent) -> dict:
    with tracer.start_as_current_span("agent_run") as span:
        span.set_attribute("goal", goal[:200])
        span.set_attribute("tenant", agent.tenant)
        start = time.time()
        try:
            result = agent.run(goal)
            latency = time.time() - start
            latency_per_run.record(latency)
            cost_per_run.record(result["cost_usd"])
            success_rate.set(1.0)
            span.set_attribute("answer", result["answer"][:200])
            return result
        except Exception as e:
            success_rate.set(0.0)
            error_total.add(1, {"category": classify_error(e)})
            span.set_attribute("error", str(e))
            raise
```

The 3am dashboard (the on-call's view):

```python
DASHBOARD_PANELS = {
    "panel_1_cost_per_run": {
        "type": "graph",
        "title": "Cost per run (p50/p95/p99)",
        "query": "histogram_quantile(0.5, agent_cost_per_run_usd_bucket) (p50)\nhistogram_quantile(0.95, agent_cost_per_run_usd_bucket) (p95)\nhistogram_quantile(0.99, agent_cost_per_run_usd_bucket) (p99)",
        "alert": "p95 > 2x baseline for 10 minutes",
    },
    "panel_2_latency_per_run": {
        "type": "graph",
        "title": "Latency per run (p50/p95/p99)",
        "query": "histogram_quantile(0.5, agent_latency_per_run_s_bucket) (p50)\nhistogram_quantile(0.95, agent_latency_per_run_s_bucket) (p95)\nhistogram_quantile(0.99, agent_latency_per_run_s_bucket) (p99)",
        "alert": "p95 > 2x baseline for 10 minutes",
    },
    "panel_3_success_rate": {
        "type": "stat",
        "title": "Success rate (last 24h)",
        "query": "sum(rate(agent_runs_total{status=\"success\"}[24h])) / sum(rate(agent_runs_total[24h]))",
        "alert": "success_rate < 0.95 for 5 minutes",
    },
    "panel_4_errors_by_category": {
        "type": "pie",
        "title": "Errors by category (last 24h)",
        "query": "sum by (category) (rate(agent_error_total[24h]))",
        "alert": "any category > 5% or 2x baseline",
    },
    "panel_5_cost_per_tenant_per_day": {
        "type": "table",
        "title": "Cost per tenant per day",
        "query": "sum by (tenant) (rate(agent_cost_per_run_usd_sum[24h]))",
        "alert": "any tenant > 80% of per-day ceiling",
    },
    "panel_6_total_cost_per_month": {
        "type": "stat",
        "title": "Total cost per month vs budget",
        "query": "sum(increase(agent_cost_per_run_usd_sum[30d]))",
        "alert": "> 80% of per-month budget",
    },
}
```

The OpenTelemetry collector config (the FDE's reference):

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: "0.0.0.0:4317"
      http:
        endpoint: "0.0.0.0:4318"

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024
  memory_limiter:
    check_interval: 1s
    limit_percentage: 80
    spike_limit_percentage: 20

exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"
  loki:
    endpoint: "http://loki:3100/loki/api/v1/push"
  jaeger:
    endpoint: "jaeger:14250"
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, memory_limiter]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      processors: [batch, memory_limiter]
      exporters: [prometheus]
    logs:
      receivers: [otlp]
      processors: [batch, memory_limiter]
      exporters: [loki]
```

The pattern that wins interviews is the "3 pillars × 3 stacks + OTel as the standard" pattern. The candidate who says "I instrument with OpenTelemetry (logs + metrics + traces); I pick Prometheus + Grafana + Loki + Jaeger for open-source, Datadog for managed, CloudWatch for cloud-native. The 3am dashboard has 6 panels (cost, latency, success rate, errors, cost per tenant, total cost). The wrong choice is to ship without observability (the 3am page is a black box). The right choice is the 3 pillars × 3 stacks + OTel + the 6-panel dashboard" is the candidate who demonstrates the observability-mindset.

## Code or example

The 4 OTel query patterns (the FDE's debugger):

```python
OTEL_QUERIES = {
    "find_slow_runs": {
        "purpose": "Find the 10 slowest runs in the last hour",
        "prometheus": 'topk(10, histogram_quantile(0.99, sum by (trace_id, le) (rate(agent_latency_per_run_s_bucket[1h]))))',
        "jaeger": "service:pf-agent latency:>5s lookback:1h",
        "result": "List of trace IDs sorted by latency",
    },
    "find_expensive_runs": {
        "purpose": "Find the 10 most expensive runs in the last hour",
        "prometheus": 'topk(10, sum by (trace_id) (rate(agent_cost_per_run_usd_sum[1h])))',
        "jaeger": "service:pf-agent ; look for spans with cost_usd > 0.10",
        "result": "List of trace IDs sorted by cost",
    },
    "find_failing_tenant": {
        "purpose": "Find the tenant with the highest error rate",
        "prometheus": 'topk(5, sum by (tenant) (rate(agent_error_total[5m])) / sum by (tenant) (rate(agent_runs_total[5m])))',
        "loki": '{tenant=~".+"} | json | error_category!="null" | stats sum by tenant',
        "result": "List of tenants sorted by error rate",
    },
    "find_slowest_step": {
        "purpose": "Find which step (LLM call vs tool call) is the slowest",
        "jaeger": "service:pf-agent ; drill down to a specific trace ; look at span duration breakdown",
        "result": "Span durations per step (LLM call vs tool call)",
    },
}
```

The 5 most common observability errors and fixes:

```python
OBSERVABILITY_ERRORS = {
    "cardinality_explosion": {
        "symptom": "Prometheus memory grows unbounded; Datadog cost spikes",
        "cause": "High-cardinality label (request_id, prompt) on a metric",
        "fix": "Move high-cardinality data to logs; only use low-cardinality labels on metrics (tenant, model, status)",
    },
    "log_loss": {
        "symptom": "Logs from a specific run are missing",
        "cause": "Log agent (Fluent Bit) crashed; log retention expired; log agent was filtered out",
        "fix": "Verify the log agent is healthy; check the log retention; verify the log agent's filter rules",
    },
    "trace_sampling": {
        "symptom": "Some traces are missing; can't find a specific run",
        "cause": "Head-based sampling is set too low (e.g., 1%); only 1% of traces are kept",
        "fix": "Use tail-based sampling (keep 100% of slow / failing traces; sample 10% of successful); or increase the head-based sample rate",
    },
    "metric_drift": {
        "symptom": "Metric values don't match the logs",
        "cause": "Aggregation at the metric level (sum, average) loses information",
        "fix": "Use histograms (not averages); add exemplars to link metrics to traces",
    },
    "alert_fatigue": {
        "symptom": "On-call ignores alerts; real issues are missed",
        "cause": "Too many alerts; thresholds too sensitive; alerts don't have runbooks",
        "fix": "Reduce to 5-10 actionable alerts; add runbooks to each alert; tune thresholds based on baseline",
    },
}
```

The AtlasMart observability stack (the case study):

```python
ATLASMART_OBSERVABILITY = {
    "stack": {
        "metrics": "Prometheus + Grafana (open-source)",
        "logs": "Loki + Grafana (open-source)",
        "traces": "Tempo + Grafana (open-source)",
        "alerting": "Alertmanager + PagerDuty",
        "instrumentation": "OpenTelemetry (the standard)",
        "monthly_cost": "$80 (Grafana Cloud free tier + Prometheus + Loki + Tempo on a small EC2)",
    },
    "dashboards": [
        {"name": "3am On-Call Dashboard", "panels": 6, "panels_list": ["cost_per_run", "latency_per_run", "success_rate", "errors_by_category", "cost_per_tenant_per_day", "total_cost_per_month"]},
        {"name": "Cost Dashboard (CFO)", "panels": 4, "panels_list": ["total_cost_per_month", "cost_per_tenant", "cost_trend", "budget_remaining"]},
        {"name": "Performance Dashboard (Engineering)", "panels": 6, "panels_list": ["p50_p95_p99_latency", "throughput_per_second", "error_rate_by_category", "llm_call_latency", "tool_call_latency", "active_runs"]},
    ],
    "alerts": [
        {"name": "cost_p95_breach", "condition": "cost_per_run_p95 > 2x baseline", "severity": "warning", "action": "page on-call"},
        {"name": "success_rate_below_95", "condition": "success_rate < 0.95", "severity": "warning", "action": "page on-call"},
        {"name": "error_category_spike", "condition": "any category > 5% or 2x baseline", "severity": "warning", "action": "page on-call"},
        {"name": "latency_p95_breach", "condition": "latency_p95 > 2x baseline", "severity": "warning", "action": "page on-call"},
        {"name": "tenant_cost_breach", "condition": "any tenant > 80% of per-day ceiling", "severity": "critical", "action": "page on-call + notify customer"},
    ],
    "runbook_url_per_alert": "https://atlasmart.atlassian.net/wiki/spaces/ONCALL/pages/1234567/{alert_id}",
}
```

## Production addendum

The observability question is the answer to "how do you monitor an agent in production." The 60-second script:

> "3 pillars (logs, metrics, traces) × 3 stack options (open-source, managed, cloud-native). OpenTelemetry is the standard; the FDE instruments once, picks the backend later. The 3am dashboard has 6 panels: cost per run, latency per run, success rate, errors by category, cost per tenant per day, total cost per month. The alerts are the gate (5-10 actionable alerts with runbooks). The wrong choice is to ship without observability (the 3am page is a black box). The right choice is the 3 × 3 + OTel + 6-panel dashboard + 5-10 alerts with runbooks."

This is the difference between a candidate who says "we have logs" and a candidate who says "3 pillars × 3 stacks, OpenTelemetry as the standard, 6-panel 3am dashboard, 5-10 alerts with runbooks, 4 OTel query patterns, 5 most common errors." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/ai-fde/phase-2-core-build/service/telemetry.py` — the production telemetry.
- **Reference implementation**: `course/hardcode/level-8-evaluation-testing/11-llm-as-judge-eval.py` — the canonical observability setup.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — monitoring as an FDE pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/02-multi-agent-dispatcher/` — multi-agent requires per-agent observability.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — observability as a system design topic.

## The 3 questions this lecture preps you for

1. **"How do you monitor an agent in production?"** Answer: 3 pillars (logs, metrics, traces) × 3 stack options (open-source: Prometheus + Grafana + Loki + Jaeger; managed: Datadog; cloud-native: CloudWatch + X-Ray). OpenTelemetry is the standard for instrumentation. The 3am dashboard has 6 panels; the alerts are the gate (5-10 actionable alerts with runbooks).
2. **"What is the OpenTelemetry as the standard pattern?"** Answer: OTel is the standard for logs + metrics + traces. The FDE instruments once with OTel; the OTel collector sends the data to a backend (Jaeger, Honeycomb, Tempo). The instrument-once pattern decouples instrumentation from storage; the FDE can switch backends without changing the code.
3. **"What is the 3am dashboard?"** Answer: 6 panels: cost per run (p50/p95/p99), latency per run (p50/p95/p99), success rate, errors by category, cost per tenant per day, total cost per month. The alerts are the gate (cost p95 breach, success rate < 95%, error category spike, latency p95 breach, tenant cost breach). Each alert has a runbook URL.

## Read next

`L8-5-the-security-perimeter.md` — the security pillar. API gateway, mTLS, rate limiting, secrets management, audit logs. The compliance layer that turns the agent into a product the customer's CISO will approve.