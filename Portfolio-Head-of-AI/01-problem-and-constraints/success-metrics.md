# Success Metrics

This is the document I'd want a Director of Engineering and a CFO to read
together. It defines what "good" looks like for an AI initiative in *their*
language, with numbers, and makes one claim that will probably be the most
defensible thing I say in an interview:

> **If an AI initiative can't be evaluated, it shouldn't be funded past
> the first quarter.**

## The single page

Every AI initiative has the same six metric slots. They are filled in
different ways, but the slots don't change:

| Slot | What it measures | Why it matters | Who owns it |
|---|---|---|---|
| **Quality** | Task-completion rate, or its analog for non-task systems (faithfulness, calibration). | The reason we built it. | ML + product |
| **Cost** | $ per 1k requests, including serving, infra, and human review. | Tells us if we can afford to keep shipping. | Eng + Finance |
| **Latency** | p50 / p95 / p99 end-to-end. | Whether users will tolerate it. | Eng |
| **Reliability** | Error rate by category, uptime. | What the SLO contract is. | Eng |
| **Risk** | Drift score, hallucination rate, audit-failure rate. | Whether the system can stay in production. | Compliance + product |
| **Adoption** | WaAU (weekly active users), task coverage, abandonment rate. | Whether it was worth shipping. | Product + GTM |

These are **not six independent metrics**. They are coupled:

- Improving quality often costs cost (bigger model, more context).
- Tightening latency often reduces quality (smaller context window).
- Tightening cost often increases risk (smaller model, less review).

The Head of AI's job is to make these trade-offs *visible* and *defensible*,
not to pretend a single number can summarize an initiative.

## Example: the fine-tune initiative

For the build-vs-buy question in `build-vs-buy-decision.md`, here are the
six slots filled in.

### Quality

| Metric | Today (Path A, baseline) | Target (Path C) | Source |
|---|---|---|---|
| Hallucination rate on company entities | 9.4% | ≤2% | 200-row held-out eval, refreshed monthly |
| Task-completion on top-5 ticket categories | 71% | ≥85% | Same eval, broken down per category |

The eval set is **the work**, not a deliverable. The most common failure mode
of fine-tune projects is grading themselves on the training distribution,
which proves nothing. We grade on a held-out, refreshed, human-rated set
of *real* tickets.

### Cost

| Metric | Today | Target | Notes |
|---|---|---|---|
| $ per 1k requests | $0.44 | ≤$0.20 | Includes API + retrieval + human review |
| Annual hosting (Path C) | $200k | ≤$120k | vLLM continuous batching + 8B base + adapter |
| Annual API residual spend | $200k | ≤$40k | Only for tasks the fine-tuned model can't handle |

The cost target has two bars: a *floor* ($/1k) and a *ceiling* (annual).
You can't hit either without the other; both should be reported each month.

### Latency

| Metric | Today | Target |
|---|---|---|
| p50 end-to-end | 1.4s | ≤0.9s |
| p95 end-to-end | 4.8s | ≤2.0s |

For an internal assistant, p95 is what users notice. For a customer-facing
system, both matter and p99 is also worth tracking.

### Reliability

| Metric | Today | Target |
|---|---|---|
| SLO error rate (5xx + timeouts) | 0.7% | ≤0.3% |
| Monthly incidents ≥P2 | 4 | ≤1 |

### Risk

| Metric | Today | Target |
|---|---|---|
| Drift score (Evidently, request-embedding) | n/a | ≤0.3 for ≥5 consecutive days; >0.3 triggers re-evaluation |
| Hallucination rate (above) | 9.4% | ≤2% |
| Audit-failure rate (sampled policy violations) | 2.1% | ≤0.5% |

### Adoption

This is the one most teams under-report. We *built the thing* — did anyone
use it?

| Metric | Today | Target |
|---|---|---|
| Weekly active users | 0 (pre-launch) | ≥70% of support team within 90 days of GA |
| Tasks completed per WAU per week | 0 | ≥8 |
| Abandonment rate | n/a | ≤15% |

The "70% of support team within 90 days" target is a *real* target. If we
can't move that number, we don't have a product; we have a science project.
A Head of AI who pretends adoption will happen by itself is avoiding the
hardest measure.

## The one question we ask every quarter

> "If we shut this down tomorrow, who cares and how much?"

That question is the antidote to sunk-cost reasoning. It also surfaces
adoption failures fast: if the answer to "who cares" is shrinking, the
initiative is failing regardless of what the dashboards say.

## Metric-table hygiene

A few rules I hold the org to:

- **No "%-better" without a baseline reference.** "30% better" is
  meaningless without specifying "than what, in what population, on what
  metric, measured when."
- **No accuracy claims that aren't tested out-of-distribution.** The
  training-distribution accuracy is fine for debugging. The OOD accuracy
  is the only number that matters.
- **No quarterly-snapshot metrics for systems under active change.** A
  monthly snapshot is too coarse if we're shipping weekly. A weekly
  snapshot for a stable system is too noisy.

## Reference implementation

The serving stack in `agentic-ai/19-mlops-finetune-genai/` exposes these
metrics as a Prometheus endpoint, partitions them by model version,
attaches a dollar cost per token, and gates the run on a budget. The
"Cost" row above is *not* assumed — it comes from the same client that
talks to the served model (`agent/client.py`), which means the cost
column in this document and the cost in the live system can never drift
apart.

The eval harness (`agent/evaluate.py`) is what produces the "Quality"
row. The held-out eval set, the lm-eval-harness integration, and the
per-task scores that get logged to MLflow are the same machinery that
powers both the headline number and the regression signal.
