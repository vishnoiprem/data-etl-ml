# Constraints

Every AI initiative is shaped by the same five categories of constraints,
and most AI initiatives are killed by ignoring one of them. This document
exists to make the constraints legible so the decisions in
`build-vs-buy-decision.md` and the metrics in `success-metrics.md` have
something to be realistic against.

## The five categories

### 1. Budget

**How it constrains:** Almost every AI choice is a budget question in
disguise.

| Bucket | Typical annual cost, 200-person company |
|---|---|
| External API (LLM serving) | $200k–$2M |
| Self-hosted GPU inference | $80k–$400k, but committed in 6-12 month contracts |
| Engineering salaries (the AI team) | $1.5M–$3M for 3–6 people |
| ML platform / MLOps tooling | $40k–$120k |
| Annotation and human review | $50k–$300k, growing with usage |
| Annual benchmarks of compute + storage | $30k–$60k |

**The trap:** budget conversations collapse into "the model is too expensive."
The real budget question is "what mix of capabilities and headcount makes
the program survive 6 quarters, not just this one?"

### 2. Data

**How it constrains:** Most AI features are killed by data, not model.

- **Provenance.** Where did the training examples come from? Are we
  allowed to use them for fine-tuning? Customer data, especially in
  regulated industries, has consent terms that often exclude fine-tuning
  by default. (See `agentic-ai/19-mlops-finetune-genai/README.md` for
  the same constraint, applied to a public dataset.)
- **Volume.** A meaningful fine-tune usually wants ≥10k high-quality
  examples. Most teams think they have this; most teams don't, because
  their "examples" are logs that have not been curated.
- **Distribution match.** A model trained on Jan–Jun tickets will fail
  in Jul when the product line changes. Hold-out by time, not just by
  row. The eval set is refreshed quarterly.
- **Quality labels.** Human-rated labels are the most expensive input.
  A 500-row labeled eval set is *the* artifact; anything else is noise.

### 3. Latency / Throughput

**How it constrains:** Sets which models and serving patterns are even
on the menu.

| Latency budget | Realistic serving target |
|---|---|
| <100ms p95 | Small base + aggressive caching + small context. Edge-only |
| <500ms p95 | Open 7B-class model on a GPU, continuous batching |
| <2s p95 | Same as above with longer context, or 8B with vLLM |
| <10s p95 | Anything reasonable; chat assistants easily here |

If the latency requirement is <100ms, you are *not* building an LLM
product. Knowing that early is the whole game.

### 4. Compliance

**How it constrains:** Compliance looks like paperwork until it doesn't.

- **PII and data residency.** EU AI Act + GDPR + sectoral rules (HIPAA,
  PCI, GLBA) impose training-data, inference-data, and log-retention
  constraints that interact non-linearly.
- **Audit trail requirements.** A regulated use case needs to produce,
  on demand, *why* the model said what it said — meaning a request store,
  a prompt-version store, a model-version store, and a tooling bridge
  between them.
- **Risk tiering.** EU AI Act classifies systems into risk tiers with
  different obligations; "high-risk" systems need conformity assessment
  before deployment. Most teams I've seen are unclear which tier their
  system falls into.

### 5. People and time

This is the constraint people forget to model:

- **Hiring.** A 6-month AI project that depends on hiring a senior ML
  engineer is a 9–12 month project. Most companies underestimate this
  by 2x.
- **Concentration risk.** If one person owns both the model *and* the
  serving stack *and* the data pipeline, you have a bus factor of 1 and
  the org is fragile.
- **Learning curve.** Even strong generalist engineers take 3–6 months
  to become fluent in fine-tuning + serving + monitoring. Build
  learning time into the plan, not just engineering time.

## What this looks like when constraints conflict

The five categories are not orthogonal. Real conflicts I have watched
or caused:

- **Budget vs. latency.** Cutting cost by switching to a smaller model
  usually loosens latency budgets — sometimes even more than expected
  because the smaller model can serve more concurrent requests.
- **Data vs. compliance.** The cheapest data to train on is often the
  data you cannot legally train on. The next-cheapest is log data the
  team doesn't think to instrument for, which means a 6-month discovery
  before any training can start.
- **People vs. time.** Optimizing a serving stack requires hours of
  training, partnerships, and trial-and-error. It does not run on a
  one-week sprint. Pretending otherwise is how you get a system that
  works for the demo and falls over at first scale.

## The constraint audit we run before funding anything

Before we fund, I make sure the team can answer:

1. **Budget** — "What is the floor, the ceiling, and the 18-month total?"
2. **Data** — "Where do ≥10k labeled examples come from, or what gets us
   there in ≤12 weeks?"
3. **Latency** — "What is the user's actual tolerance? Have we measured
   it, or are we guessing?"
4. **Compliance** — "What risk tier is this system, who reviews us, and
   what's the audit trail format we have to produce?"
5. **People** — "Who is doing the work in the first 4 weeks? What happens
   if they're unavailable?"

If any of those doesn't have a real answer, the initiative is not ready
to be funded; it's ready to be researched. The difference matters for
the company's expectations and the team's morale.

## Wired to the reference implementation

The constraints above are precisely why `agentic-ai/19-mlops-finetune-genai/`
was built the way it was:

- **Budget:** hard budget gates (`agent/gates.py`) that refuse to spend the
  next cent once a limit is hit. The argument for build-vs-buy
  documentation needs cost numbers that cannot silently drift.
- **Data:** a leakage filter that explicitly drops any training row
  whose prompt overlaps the held-out eval set, so the model cannot
  be cheating on the headline number without us noticing.
- **Latency:** a serving target with p50/p95/p99 exposure in Prometheus,
  partitioned by adapter alias, so we can compare adapter versions
  apples-to-apples on the served system.
- **Compliance:** a model registry in MLflow with `@Champion` aliasing
  and a `run_id` on every adapter, so "which version served that request
  yesterday" is a one-line query.
- **People:** synthetic-mode wiring in the test suite so a junior engineer
  can ship the project without a GPU, and an end-to-end pipeline script
  (`scripts/run_pipeline.sh`) so a new team member can run the whole
  thing once and understand it.

The shape of the artifact is downstream of the shape of the constraints.
Ignoring constraints makes the artifact impossible to defend in review.
