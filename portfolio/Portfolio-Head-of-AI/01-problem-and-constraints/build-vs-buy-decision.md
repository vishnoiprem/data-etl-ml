# Build vs. Buy — MLOps Fine-Tune for a Domain Assistant

The first job of a Head of AI is not to build. It is to *decide* — including
deciding what **not** to build. This document is my concrete answer to one
specific decision, deliberately chosen because it comes up at every company
shipping LLMs internally.

## The decision

A 200-person company is spending $4k/day on a third-party API for an internal
assistant that handles ~9,000 ticket-classification + drafting requests/day.
Engineering has complained for six months that the model's accuracy on their
specific ticket taxonomy is 71%, with a 9.4% hallucination rate on
company-specific entities (product names, internal policy). The CTO wants the
team to "fine-tune a better model."

We have to choose one of three paths:

| Path | Direct cost, year 1 | Time to value | Risk |
|---|---|---|---|
| **A. Stay on the API**, focus on prompt engineering + RAG over internal docs | $200k (API) + ~$120k (1 engineer, 6 months) | 4–8 weeks | Low. Caps accuracy at base model. |
| **B. Self-host an open base model, no fine-tune** (e.g. Llama 3.1 8B on Lambda Labs) | ~$90k hosting + ~$140k eng | 8–12 weeks | Medium. Accuracy roughly equivalent for out-of-distribution intents. |
| **C. Build an MLOps fine-tune pipeline** (Path B + QLoRA on ~30k curated examples) | ~$250k (Path B + ~$110k one-time eng) + ongoing tracking infra | 12–20 weeks | Medium-high. Maintenance cost + drift risk. |

## My recommendation: **Path A first, conditional Path C in 6–12 months**

That reads as boring. The rest of this document is why.

## The reasoning

### 1. Path C is a *bet*, not a *purchase*

Fine-tuning shows diminishing returns when the failure mode is *retrieval*
or *tool-use*, not *foundation capability*. For this company's stated
problem — "model doesn't know our product names" — a RAG layer over a
vector store of internal product docs almost certainly closes most of the
9.4% hallucination gap at a fraction of the cost.

If I were the Head of AI here, I would not let the team start a fine-tune
project until we had **measured where the residual error comes from**. That
means: a labeled eval set of ~500 tickets, a failure taxonomy, error
breakdown by category. If 70% of errors are "model should have looked up the
internal product doc," fine-tuning is the wrong lever.

### 2. Path C is a 6-month commitment disguised as a 6-week sprint

The visible work is "fine-tune Llama and serve it." The real work is
everything else:

- **Curate a training set with consent + provenance** — 3+ months of legal
  cross-check on customer-ticket data, not 3 weeks.
- **Build evaluation** that the team trusts — the hardest part. Internal
  stakeholders won't accept a Prometheus dashboard as evidence, they want
  a 200-row human-rated eval set refreshed quarterly.
- **Build the operational apparatus** — drift detection, rollback,
  monitoring for the *served* model, not just the training run.
- **Hire for it** — most teams I've seen do not have an ML engineer who
  *also* owns a serving stack. There's a real org question, not just a
  tech question.

### 3. Path A lets us *learn what to fine-tune*

The right time to commit to Path C is when we have evidence — from Path A
running for 6 months — that:

- The retrieval failure rate has dropped to near-zero (good; means we've
  extracted what we can from context).
- The remaining errors are consistently *reasoning* failures or
  *style-of-response* failures the base model can't fix with context alone.
- We have ≥10k labeled examples drawn from the *real* distribution,
  including the long-tail intents.

At that point, the fine-tune has a target — it's not "improve the model,"
it's "fix the specific failure mode X we have shown the model can't fix
from context alone." That's the only kind of fine-tune I'd fund.

### 4. Saying "yes" to fine-tuning is also saying "no" to other AI work

A Head of AI's hardest job is sequencing against a fixed budget. If I
spend $250k and 6 months of team capacity on a fine-tune, that is the
fine-tune we **don't** do:

- A vendor evaluation for the second agent use case (~$30k, 6 weeks)
- A code-assistant rollout for engineering (~$80k, 12 weeks, but with a
  real 4-5x productivity story)
- A governance framework that lets the company actually scale beyond
  one model (~$60k, 12 weeks, low visible ROI, high optionality)

The fine-tune project also creates **organizational drag**: it requires
the team to learn an entirely new toolchain (QLoRA, MLflow, vLLM) and
*stay current* on it. For a 200-person company that may need to swap
bases in 12 months, that drag is expensive.

## What I would actually fund first

If I have to fund *something*, in this order:

1. **Path A**, with explicit success criteria: ≤2% hallucination rate on
   company entities, ≤80ms p95 retrieval latency, eval harness built and
   run weekly, cost per 1k tokens documented.
2. **A vendor evaluation** for the second use case (this is where the
   company learns what *buying* AI feels like at scale).
3. **A governance spine**: data inventory, model registry, risk tiering,
   incident playbook. Cheap, doesn't show up in revenue, pays for itself
   the first time something goes wrong.

And **only if** those three are in flight and showing real signal:

4. **Path C** as a 12-week scoped experiment with a defined kill criterion:
   "doesn't lift the held-out regression score by ≥3 points in 6 weeks
   of training, stop and migrate to a bigger base model."

## Reference implementation

The decision document above is the judgment. The working code in
`agentic-ai/19-mlops-finetune-genai/` is the implementation, if and when
Path C becomes the right move. It is *not* a recommendation to start with
fine-tuning — it's the artifact you reach for when the reasoning above
gets you to "yes, fine-tune, and here's exactly how."

## What this decision looks like if I'm wrong

The single failure mode I'm most worried about is that I'm being
*too cautious* — that fine-tuning, even a mediocre one, would have
shipped 6 months ago and is currently the reason we're behind a
competitor. I can't disprove that prospectively. I can mitigate it by:

- Setting a hard date (6 months from Path A launch) at which we
  *re-litigate* the decision with real data.
- Naming a single owner for that re-evaluation, not a committee.
- Funding a small parallel fine-tune spike in the engineering team's
  20% time, with no executive visibility, so we have data when we
  re-litigate.
