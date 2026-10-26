# Monitoring

This document covers the *operational* monitoring — the layer that
tells you at 3am that something is wrong with the serving system.
Quality monitoring (eval, drift, taxonomy) is
`../02-data-and-eval/eval-strategy.md`; this is uptime, latency,
cost, and error rate.

The two layers are deliberately separate because they have different
cadences, different owners, and different responses. Quality drift
develops over weeks; serving failure develops over minutes.

## The three signals, and why only three

A serving system exposes thousands of metrics. The Head of AI's job
is to name the three that determine whether to roll back.

### 1. Latency (p50 / p95 / p99)

- **p50** is what most requests feel like. If p50 is bad, something
  is structurally wrong (bad batching config, wrong model size, GPU
  thermal throttling).
- **p95** is what the user who has a bad day notices. This is the
  SLO contract number.
- **p99** is the tail that finance hears about when a customer
  complains. Track it, but don't build an SLO on it.

Prometheus metric: `REQUEST_LATENCY` histogram, partitioned by
adapter alias.

### 2. Error rate (5xx + timeouts, by category)

- 5xx from the serving layer.
- Timeouts at the client boundary.
- **Budget-gate rejections** — these are *not* errors, they're a
  control working. They get a separate counter so the dashboard
  doesn't alarm on them.

The category breakdown matters more than the rate. "0.7% errors" is
uninformative; "0.7% errors, all of them tokenization failures on
inputs >8192 tokens" is actionable in five minutes.

### 3. Cost per request

- `REQUEST_COST` counter, attributed to the adapter alias that
  handled the request.
- Aggregated by Grafana into $/1k, $/day, $/month.
- **Budget-gate rejections are also cost events** — a rejected
  request has zero cost, which is the point.

Cost is the third signal because it's the only one with a direct
conversation with Finance. Latency and errors are engineering
concerns; cost is an org-level constraint that gates everything.

## The dashboard, in three panels

Grafana, provisioned (`infra/grafana/provisioning/dashboards/`):

**Panel 1 — "Is it up?"**

- Uptime over 24h / 7d / 30d, per service.
- Error rate by category, stacked, last 6h.
- `/healthz` status.

**Panel 2 — "Is it fast?"**

- p50 / p95 / p99 latency, last 6h, by adapter alias.
- Comparison to last week at the same hour (day-of-week effect).
- GPU utilization and memory.

**Panel 3 — "Is it affordable?"**

- Cost per 1k requests, by adapter alias.
- Cumulative spend this month vs. budget gate.
- Requests served vs. requests rejected by the gate.

Three panels is not a limitation; it's a discipline. A dashboard
with 15 panels has zero panels that anyone reads.

## Drift, the fourth signal (quality layer)

The drift detector lives in `agent/monitor.py` and emits a
`DRIFT_SCORE` gauge. It's the bridge between the operational layer
and the quality layer:

- Drift < 0.3 for 5 consecutive days: healthy. No action.
- Drift > 0.3 for 5 consecutive days: **the serving system is fine
  and the model is wrong.** Trigger a Tier-2 re-evaluation.

The drift score is computed on the distribution of *request
embeddings*, not on output quality — because output quality needs
labels and request embeddings don't. It's a leading indicator, and
it exists precisely so drift is caught before the eval set is
refreshed.

## What alerts, and what doesn't

| Signal | Alert? | Severity |
|---|---|---|
| `/healthz` failing | Yes | P1 |
| Error rate > 1% for 15 min | Yes | P2 |
| p95 > 2× SLO for 30 min | Yes | P2 |
| Monthly spend > 80% of budget | Yes | P3 |
| Budget gate rejecting > 5% of requests | Yes | P3 |
| Drift score > 0.3 for 5d | Yes (quality P2) | P3 |
| p99 latency up 20% week-over-week | No | — |
| GPU memory > 90% | No (unless sustained 1h) | — |
| Single adapter usage > 95% | No | — |

The "no" rows are as important as the "yes" rows. Alert fatigue is
real: an on-call rotation that gets 8 alerts a week stops reading
them, and the one that mattered gets ignored with the rest. I'd
rather have 3 alerts a week that mean something than 20 that don't.

## On-call, the human layer

The dashboard tells you what. The on-call rotation tells you what
to do about it. At the sizes in
[`org-design.md`](./org-design.md#at-200500-people-515-ai-engineers),
on-call is a rotation between the platform and ML engineers, one
week each. The runbook for each alert type is one page:

| Alert type | First action | Second action |
|---|---|---|
| `/healthz` down | Restart the serving container | Check GPU health; page infra if it recurs |
| Error rate > 1% | Check Grafana for which category spiked | Roll back to previous adapter alias |
| p95 > 2× SLO | Check batch size, GPU memory | Roll back if not resolved in 30 min |
| Spend > 80% | Check budget gate config | Alert PM; consider lowering per-request max_tokens |
| Drift > 0.3 for 5d | Trigger Tier-2 eval | Decide: refresh eval or roll back |

"Roll back to previous adapter alias" is the first action for most
alerts, because it's one command and it fixes most things.
Rebuilding, retraining, or debugging from scratch should be the
*second* action, taken only after rollback doesn't fix it.

## What I would refuse to alert on

| Refusal | Why |
|---|---|
| Every p99 spike | p99 is noisy at low request volumes; it produces false alarms |
| Per-request cost changes | Cost varies by request length; alert on aggregates |
| Any metric with no documented response | An alert without a runbook entry is noise |
| Model quality regressions | Those are caught by the eval harness, not by Prometheus; alerting on them is alerting on labels |
| Anything outside the three signals | Discipline. The three signals have owners; the twentieth signal has nobody |

## Cost of the monitoring layer

Self-hosted (Prometheus + Grafana + Evidently):

- ~$60/mo for the stack.
- ~8 hours/quarter maintaining dashboards and alerts.
- 1 week of setup, amortized over the program's life.

The alternative — a managed observability vendor — costs 5–10× and
adds a data-egress question ("does our request log leave the
company?"). For a 200-person company with a compliance constraint,
self-hosted Prometheus is the answer. Revisit if the team grows
past the point where 8 hours/quarter becomes 8 hours/week.

## The rule I hold

> If a signal doesn't have a documented first action, it doesn't
> get an alert.

The monitoring layer's value is entirely in the mapping from signal
to action. A metric with no action is interesting; a metric with no
action *and* an alert is actively harmful, because it trains the
on-call to ignore the panel where the real signal lives.