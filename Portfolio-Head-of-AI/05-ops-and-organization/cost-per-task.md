# Cost per Task

Cost per task is the metric that makes an AI initiative legible to
Finance. This document defines it precisely, because "cost" is
ambiguous enough that two teams can report different numbers for the
same system and both be defensible.

## The definition

> **Cost per task = (inference cost + human review cost + infra
> amortized) / tasks completed.**

Not per request. A *request* is not a *task*. Some tasks complete in
one request; some require five. If you report $/request, you reward
the team for making requests smaller, which is the wrong incentive.

## The three components, and which ones teams forget

### 1. Inference cost

Model tokens, tool calls, retry overhead. This is the number
`agent/client.py` computes, and it's the number on the Grafana
"affordable" panel in [`monitoring.md`](./monitoring.md).

- p50 and p95, by adapter alias.
- Includes retry overhead — a 3% retry rate on a $0.40 request adds
  $0.012/task, which sounds trivial until the retry rate is 30%.

### 2. Human review cost — the one teams omit

Every AI system in production has a human in the loop somewhere. If
the human is reviewing 5% of outputs at 45 seconds each, that's:

```
0.05 × 45s = 2.25s of human time per task
at $50/hr blended:  2.25/3600 × $50 = $0.031/task
```

$0.031 sounds small. At 9,000 tasks/day, it's $8,400/month. That
is a real number that does not appear on any LLM-serving dashboard,
and it's the number that surprises Finance most.

**Every cost-per-task report must include this.** A model at $0.08
per 1k tokens with 20% human review is more expensive than a model
at $0.14 per 1k with 2% human review, and the dashboards will tell
you the opposite.

### 3. Infra amortized

The GPU, the observability stack, the storage, the MLflow server.
Amortized over the quarter, divided by tasks in the quarter.

- GPU: $700–$1,200/month per host.
- Observability: $60/month.
- Storage: $30/month.
- MLflow: self-hosted, ~$0 marginal.

At 9,000 tasks/day = 270k tasks/month, a $1,300/month fixed cost
amortizes to $0.005/task. Small, but it's the number that makes
Path C look good at scale, and it should be in the table.

## The worked example

For the ticket-classification workload (9,000 tasks/day,
270k/month), Path C (fine-tuned 8B + adapter):

| Component | $/task |
|---|---|
| Inference (p50) | 0.010 |
| Inference (p95) | 0.017 |
| Human review (5% × 45s) | 0.031 |
| Infra amortized | 0.005 |
| **Total (p50)** | **$0.046** |
| **Total (p95)** | **$0.053** |

Against Path A (vendor API):

| Component | $/task |
|---|---|
| Inference (p50) | 0.048 |
| Inference (p95) | 0.075 |
| Human review (5% × 45s) | 0.031 |
| Infra amortized (vendor, ~0) | 0.000 |
| **Total (p50)** | **$0.079** |
| **Total (p95)** | **$0.106** |

Path C is ~42% cheaper per task at p50. That's the real number,
and it's the one that makes the build-vs-buy doc's cost argument
in `../03-system-architecture/cost-model.md` defensible rather than
optimistic.

**But** — and this is the load-bearing caveat — Path C costs $250k
in one-time engineering to get to. At 270k tasks/month and $0.033/task
saved, payback is ~7,600 tasks = ~28 days of operation. That's the
payback argument, and it assumes the fine-tune actually works. If
the fine-tune shows no improvement (R1 in
`../04-delivery/risk-register.md`), the payback never arrives and
the $250k is a write-off.

## The four questions this metric has to answer

1. **Is the cost falling over time?** If not, we're not getting more
   efficient — we're just getting more traffic.
2. **Where is the cost concentrated?** A single high-traffic
   endpoint can be 60% of spend. Optimizing it moves the average.
3. **Is human review falling?** A falling cost-per-task with a
   flat human-review-rate is a *worse* trend than flat inference
   cost with a falling review rate.
4. **Is the metric honest?** Cost-per-task is easy to game by
   splitting tasks. We hold the line by reporting tasks-completed
   (from adoption tracking), not requests-served.

## Anti-patterns I would refuse

| Anti-pattern | Why |
|---|---|
| Reporting $/request and calling it $/task | Wrong denominator; rewards the wrong behavior |
| Omitting human review from the total | It's the largest single component in most systems |
| Using a blended "p50 for cost, p95 for latency" report | The user who costs you p95 is the one complaining about p95 |
| Amortizing infra over *all* tasks when some endpoints are much heavier | A per-endpoint breakdown is more honest; report both |
| Comparing a pre-fine-tune Path C number to a post-fine-tune one without saying so | The fine-tune changes cost/task; the comparison needs a timestamp |
| Hiding a spike behind a quarterly average | The spike is the interesting part |

The last row is the one that costs careers. Quarterly averages hide
the incident in `incident-postmortem.md` — the 11-day drift window
would be invisible in a quarterly view. Always report monthly, and
for anything with an incident, daily for the affected window.

## What I'd put in the monthly report

One table, four rows:

| Metric | This month | Last month | Trend |
|---|---|---|---|
| Tasks completed | 270k | 265k | +2% |
| Cost per task (p50) | $0.046 | $0.051 | -10% |
| Cost per task (p95) | $0.053 | $0.058 | -9% |
| Human review rate | 5% | 6% | -1pt |

Four rows, one table, monthly, generated from the same Grafana
panels. That's the whole report. Everything else is commentary.

## The rule I hold

> Cost per task is the number you report to Finance. Everything else
> — $/1k tokens, GPU hours, tokens per second — is a diagnostic for
> engineers, not a number the business runs on.

The moment the Head of AI's primary financial metric becomes
"tokens per second," the conversation has drifted from "are we
solving a problem" to "are we optimizing a benchmark," and the
business has lost the thread. Cost per task keeps the thread.