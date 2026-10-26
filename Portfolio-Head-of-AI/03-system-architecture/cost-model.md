# Cost Model

This is the document Finance reads first. It exists so the numbers in
`../01-problem-and-constraints/success-metrics.md` and the numbers on
a CFO's slide are the same numbers, and so that *the conversation*
about AI spend happens with units attached.

## The three number sets that must agree

There are exactly three places the cost number lives:

1. **The serving layer.** `agent/client.py` records `cost_usd` per
   request, attributed to the adapter alias that handled it.
2. **The observability layer.** Prometheus + Grafana aggregate those
   `cost_usd` records into panels ($ per 1k requests, $ per day, $
   per month).
3. **The board deck.** Pulled from Grafana, formatted in a slide.

If those three are computed by different code paths, they will
disagree within one quarter. The first argument of this document is
that they are the *same code path* — `agent/client.py` writes the
prom-counter that Grafana queries.

## The cost inputs

For a fine-tuned Llama 3.1 8B served on a single A10G:

| Input | Value | Source |
|---|---|---|
| GPU rental, A10G 24GB | ~$0.70/hr, ~$520/mo on-demand | AWS p3 / Lambda Labs |
| Idle cost | $520/mo | Yes, idle. vLLM preallocates. |
| Per-request compute | ~$0.0004 per 1k input + 1k output tokens | Measured by `agent/client.py` |
| HF token for private base | $0 here, $20/mo on Team | Configurable |
| Adapter merge compute | One-time, ~$5/run | Empirically |
| Storage (model + adapter + logs) | ~$30/mo | S3 class tier |
| Observability (Prom + Grafana) | ~$60/mo | Self-hosted |
| **Total monthly, serving 24/7** | **~$700–$1,200 fixed + variable** | |

That's dramatically cheaper than the $4k/day the company was paying
the third-party API at, *if and only if* the workload justifies a
dedicated GPU. At 200 RPS sustained, it doesn't. At 2,000 RPS, it
unambiguously does.

## The sensitivity table that matters

The numbers nobody writes down but everyone needs:

| Daily requests | API cost | Self-host cost | Δ | Verdict |
|---|---|---|---|---|
| 1,000 | $130 | $700 (mostly idle) | -$570 | API |
| 5,000 | $670 | $700 + $10 compute | -$40 | roughly tied |
| 10,000 | $1,330 | $700 + $20 compute | +$610 | Self-host |
| 50,000 | $6,700 | $1,000 + $100 compute | +$5,600 | Self-host (and start doubling up GPUs) |

The crossover is around 5k–10k daily requests for 8B-class serving.
Below that, self-host is a luxury. Above that, it pays back within a
quarter. This is the number that decides Path A vs. Path C
*quantitatively* — and `../01-problem-and-constraints/build-vs-buy-decision.md`
makes the qualitative argument that even at 9k requests/day you'd
choose Path A first because the fine-tune's accuracy ceiling depends
on data you don't have yet.

## The hidden costs

These are the costs that crash engineering budgets. Naming them
explicitly so they don't surprise anyone:

| Category | First-year estimate | Comments |
|---|---|---|
| **Annotation + eval rater time** | $40k–$80k | Refreshed quarterly. Pays for itself or kills the program; there is no middle. |
| **Engineering salaries (this is one team)** | $1.5M–$3M | The big number. Doesn't show in API-vs-self-host comparisons. |
| **On-call / incident response** | ~$30k–$60k | For a service running 24/7. Often missed. |
| **Auditing / compliance overhead** | $30k–$100k | Scales with risk tier, not with traffic. |
| **Model-refresh migrations** | ~$20k–$50k per swap | When the base model version changes, every adapter needs re-evaluation. |
| **Storage growth (logs, eval rows, telemetry)** | $5k–$15k/yr | Doubling annually. |
| **Abandoned experiments (writeoffs)** | $20k–$100k | Fine-tunes that didn't ship. Pretax. |

The last row matters. A team that's shipping fine-tunes will have
*more* that don't ship than that do. That's not failure; that's
iteration. But Finance will amortize the cost over the winners,
which makes the winners look artificially expensive. Track it
separately.

## Cost per 1k requests, by adapter

The reference implementation produces this directly. Format from
`../01-problem-and-constraints/success-metrics.md` Cost row:

| Adapter | p50 $/1k | p95 $/1k | p99 $/1k | Daily requests | Monthly $ |
|---|---|---|---|---|---|
| `champion-v3` (LoRA-adapter) | $0.08 | $0.14 | $0.22 | 9,000 | ~$320 |
| Path A baseline (vendor) | $0.34 | $0.55 | $0.78 | 9,000 | ~$1,300 |

(The board-deck-level "we saved $1k/day" claim is the difference
between those two monthly cells.)

## The pattern I'd never let happen

> A team optimizes the serving cost while the budget gate is broken.

Both are visible on the same dashboard for a reason. If the gate
trips, an unfixed gate looks like a serving improvement in the very
short term. A cost gate that nobody reads is a budget overrun that
narrates itself as efficiency.

## What I show the CFO at the 1:1

Three numbers, in this order:

1. **Monthly recurring spend** (last month, current trajectory).
2. **Cost per task served** (last 30 days, p50 and p95).
3. **What we're buying with the next dollar** (a single line of plain
   English per proposed spend).

Item 3 is the number that decides whether we get more budget. It
forces the team to articulate the marginal value of capacity before
we add it. A proposal that can't fill in item 3 doesn't get funded,
because the proposal is "we'd like to run more inference" and the
question "why" is unanswered.

## The rule I hold

> If Finance can't trace a dollar from invoice to run_id, the cost
> model is broken, regardless of how the dashboards look.

Run_id on every cost record. Adapter alias on every cost record.
Time on every cost record. If those three are present, the trace is
always possible. If any one is missing, it's never possible.

That is what `agent/client.py` writes and what MLflow tracks. It's
the cost in this document and the cost in the live system, agreeing
by construction.