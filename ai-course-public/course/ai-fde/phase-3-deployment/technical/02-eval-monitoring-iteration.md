# Lesson T2 — Evaluation, monitoring, and iteration

> **The eval harness from Phase 2 runs in CI. Phase 3 adds the live loop.** 45 minutes. Hands-on: wire `/feedback`, expose `/metrics`, and read the weekly iteration report.

By the end of this lesson you can stand up the **3-loop iteration cadence** that keeps a Phase 3 system improving without the FDE in the room. You have a `/feedback` endpoint that records thumbs, a `/metrics` endpoint that exposes Prometheus text, a `usage.jsonl` log line per draft, and a `render_iteration_report()` that joins all three into a one-screen markdown summary.

The PacificFreight scenario: Mei has been using the drafter for 4 weeks. She sends 150 emails/day through it. **The eval set says we're at 0.62 context precision** — good but not great. The FDE needs to know: is Mei finding it useful, which drafts does she revert, and what does the cost look like? The 3-loop iteration cadence answers all three.

---

## 🎯 Outcome

You produce one artifact:

- `service/eval.py::render_iteration_report()` — a one-screen markdown report that joins the eval set, the live `usage.jsonl`, and the baseline. Plus a new `iteration-report` subcommand on the eval CLI: `python3 service/eval.py iteration-report --since-days 7`.

When you finish, you can stand up the 3-loop iteration cadence (online metrics → offline eval → user feedback) and explain why each loop catches what the other two miss.

## 🧠 Mindset

A production LLM system needs **three measurement loops**, and they catch different failure modes:

| Loop | What it catches | Latency | Cost |
|---|---|---|---|
| **Online metrics** (`/metrics`, Prometheus) | Latency spikes, error rates, circuit-breaker trips, rate-limited requests | Real-time (1s scrape) | Free (in-process) |
| **Offline eval** (Phase 2's `run_eval`) | Quality regressions, top-1 wrong, answer drift from baseline | Hours (run nightly) | $0.10 per 30-row run (mock) |
| **User feedback** (`/feedback`) | "I reverted this draft" qualitative signal, thumbs-down notes | Days (CS team reviews) | Free (1 API call per draft) |

The trap:

1. **The "we have an eval, we're good" trap.** The eval set is 30 rows. The real failure is on row 31 — the Vietnamese email about a refund that nobody added to the eval set. **The eval only catches failures that look like the eval.**
2. **The "we have metrics, we're good" trap.** `/metrics` shows `pf_draft_latency_seconds{outcome="ok"} p95=2.3s`. That's a great number. It tells you nothing about whether the draft was correct. **Metrics are health, not quality.**
3. **The "users will tell us" trap.** Mei has reverted 3 drafts this week. She hasn't said anything because she's busy. The feedback loop requires you to **build the thumbs button into the CS tool**, not wait for someone to email you.

> **FDE rule:** if you only ship one loop, ship the offline eval. If you ship two, add online metrics. If you ship three, add the feedback button. **All three is what "production" means.**

## 🛠️ Practice — the 3-loop cadence

### Loop 1: online metrics

`GET /metrics` returns Prometheus text format. A Prometheus server scrapes it every 15 seconds. The CS team's Grafana dashboard plots the 4 key panels:

```promql
# Panel 1: Draft throughput
rate(pf_drafts_total{outcome="ok"}[5m])

# Panel 2: P95 draft latency
histogram_quantile(0.95, rate(pf_draft_latency_seconds_bucket[5m]))

# Panel 3: Circuit-breaker state
pf_circuit_state{downstream="openai"}

# Panel 4: Rate-limited requests
rate(pf_drafts_total{outcome="rate_limited"}[5m])
```

The metrics are emitted in `service/app.py::_draft_pipeline` after every call:

```python
telemetry_mod.REGISTRY.counter(
    "pf_drafts_total", labels={"outcome": outcome}
).inc()
telemetry_mod.REGISTRY.histogram(
    "pf_draft_latency_seconds", labels={"outcome": outcome}
).observe(latency_ms / 1000.0)
_USAGE_LOG.log(
    request_id=request_id, outcome=outcome, latency_ms=latency_ms,
    model=response.model, cost_usd=response.cost_usd,
    circuit_state=circuit_mod.STATE_NAME[_LLM_BREAKER.state],
    user_id=user_key, shipment_id=shipment_id, n_contexts=len(all_chunks),
)
```

### Loop 2: offline eval (Phase 2 — unchanged)

The 30-row eval set runs in CI on every PR. The Phase 2 regression check (threshold 0.05) catches quality drops before they ship. **Phase 3 keeps this exactly as-is** — the eval set is the spec; the metrics are the liveness check.

The new piece in Phase 3 is **running the eval against the live usage data**, not just the frozen set:

```bash
$ python3 service/eval.py eval --set shared/eval_set.jsonl --report eval_report.md
Rows: 30  |  Errors: 0  |  Total time: 46 ms
faithfulness=0.4105  ansrel=0.0406  ctxp=0.6167  ctxr=0.6028
Wrote report to eval_report.md
```

### Loop 3: user feedback

`POST /feedback` records a thumb on a draft. The CS tool (Phase 4's web UI) shows 👍 / 👎 / 😐 buttons next to every draft. Each click writes a line to `usage.jsonl`:

```json
{"ts": 1791552517.36, "request_id": "fb0", "outcome": "feedback", "latency_ms": 0, "model": "n/a", "cost_usd": 0.0, "circuit_state": "closed", "user_id": "cs_team", "feedback_rating": -1, "note": "wrong address"}
```

The rating field is the key signal. The free-text `note` is gold — Mei types "wrong address" or "should mention refund" or "great draft, no changes", and that text is the prompt for next week's experiment.

### The iteration report

`render_iteration_report()` joins all three loops into a one-screen markdown. The FDE reads it on Monday morning:

```bash
$ python3 service/eval.py iteration-report --usage-log usage.jsonl --since-days 7
```

The output:

```markdown
# Iteration Report (Phase 3 T2)

Window: last 7 days  |  Cutoff: 2026-10-08 ...

## Top-line

| Metric | Value |
|---|---|
| Drafts | 1,043 |
| Fallback responses | 2 |
| Rate-limited | 0 |
| Total cost | $0.55 |
| P50 latency | 120 ms |
| P95 latency | 4,200 ms |

## Feedback (CS team thumbs)

| Rating | Count | % |
|---|---|---|
| 👍 (+1) | 832 | 79.8% |
| 👎 (-1) | 87 | 8.3% |
| 😐 (0) | 124 | 11.9% |

**Thumbs-up rate: 79.8%**  (target: ≥ 80% for Phase 3 sign-off)

## Per-day breakdown

| Day | Drafts | Cost (USD) | Errors |
|---|---|---|---|
| 2026-10-02 | 142 | $0.07 | 0 |
| 2026-10-03 | 158 | $0.08 | 0 |
| 2026-10-04 | 165 | $0.09 | 1 |
| ... | ... | ... | ... |

## Recent thumbs-down notes

- "wrong address" (Mei)
- "should mention refund policy" (Mei)
- "drafted a refund response — should have escalated" (Mei)
```

The FDE reads this in 60 seconds. The action items are obvious:

1. **P95 latency is 4.2s, target is 4.0s.** Investigate the slow drafts. Probably a few multi-shipment emails that trigger a 2nd retrieval.
2. **3 thumbs-down about refunds.** Either the prompt is wrong (escalation rule not strong enough) or the eval set is missing refund scenarios. Both are true.
3. **Thumbs-up is 79.8%, target is 80%.** Almost there. The Phase 3 sign-off bar is at 80% — the drafter is one prompt fix away.

### The weekly cadence

This is the **iteration ritual** the FDE hands off to the next person. Every Monday, 30 minutes:

1. **Read the iteration report.** Note the top 3 action items.
2. **Pick ONE experiment.** Hypothesis → change → measurement → success criterion. Example: "Hypothesis: if I move the Hard rules chunk to position 1 in the system prompt, the refund escalation rate will improve from 90% to 99%. Change: edit `service/rag.py::build_rag_prompt` to put `style-guide#4` first. Measurement: add 5 refund rows to the eval set; re-run; expect context_precision to lift 0.05. Success: if yes, ship; if no, revert."
3. **Wed-Thu: implement.** Smallest possible change.
4. **Friday: ship + measure.** The CI eval must pass. The next Monday's iteration report will show whether the experiment worked.

The artifact that survives the FDE's exit: the **iteration cadence + the experiment template + the eval set as the spec**. The next FDE inherits the cadence, the eval, and the last 4 weeks of iteration reports.

---

## 🏛️ FDE Lens — the cost of measurement

The temptation is to measure everything. Don't.

| Don't measure | Why not |
|---|---|
| Token-level perplexity | Tells you nothing about customer satisfaction. Costs latency. |
| Embedding similarity between draft and style guide | Cosine score on a small corpus. Noisy. Not actionable. |
| Per-token latency breakdown | The network is the bottleneck. Sub-second granularity is noise. |
| Number of retrieved contexts | The right number is 3. Counting doesn't help. |

| Do measure | Why |
|---|---|
| Thumbs-up rate | The only signal that comes from the CS team, not from us. |
| P95 latency | The patience ceiling. Mei leaves the page at 4s. |
| Total cost per week | Daniel's budget is $5/month; we need to know we're under. |
| Hallucination rate (per-eval) | The regulatory risk. The eval set is frozen, so the number is comparable. |
| Eval delta vs baseline | The 0.05 regression check. Tells you if this week's prompt broke last week's. |

> **FDE rule:** if a metric doesn't change a decision, don't measure it. **Three good metrics beat thirty mediocre ones.**

## 🌙 Reflect

Write 3-5 sentences:

1. The Phase 2 eval has 4 metrics. The Phase 3 iteration report adds 4 more (drafts, fallback, rate-limited, cost). Is the new list a superset, or are some redundant?
2. Mei says "I reverted 3 drafts this week." You don't have the feedback loop yet — you ask her to remember. The next week, she remembers 2. **What's the systematic cost of the missing feedback loop?**
3. The iteration report shows P95 latency 4.2s. The `/metrics` histogram shows it's the 95th percentile. Mei is on a slow wifi. The system is fine. **What does this tell you about reading metrics in isolation?**
4. The 3-loop cadence is described as "Monday: review, Tue: pick experiment, Wed-Thu: implement, Friday: ship." The customer asks "why don't you ship more often?" What do you say?
5. The eval set has 30 rows. The feedback loop is showing 79.8% thumbs-up. The eval says context_precision=0.62. **Which number do you trust, and why?**

**What's next** — T3 adds the failure handling that keeps the 3-loop cadence honest: a circuit breaker so the system degrades gracefully when OpenAI is down, a rate limiter so Mei can't accidentally DoS the service, a PII redactor so customer emails don't leak to the LLM, and a `GET /circuit/state` endpoint so Daniel can see what's happening. The artifact that survives: the runbook + the on-call rotation.
