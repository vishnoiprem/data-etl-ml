# Resourcing

A 200-person company with a 9.4% hallucination rate problem will
not approve six engineers and a GPU cluster. The resourcing
question is how to be credible at the size the company can afford
*and* grow it as the program proves out. This is the document where
that problem gets specific.

## Headcount, in 3-week units

The build-vs-buy decision is "Path A first," so the resourcing starts
from there. Three people is the smallest team that doesn't have a
bus factor of 1; four is the smallest team that doesn't have
key-person dependency.

| Quarter | Team size | Composition |
|---|---|---|
| **Q1** | 3 | 1 senior ML engineer (eval + training), 1 platform engineer (serving + observability), 1 PM/eng-lead hybrid (data curation, eval ownership) |
| **Q2** | 3 | Same. Don't grow without proven signal. |
| **Q3** | 3 + 1 | Same + 1 ML eval/curation engineer if Path C is funded |
| **Q4** | 4 | + 1 finetune/serving specialist if Path C is funded |
| **Q5** | 5 | + 1 SRE/serving on-call rotation; vLLM in production 24/7 |
| **Q6** | 6 | + 1 multi-model integration engineer |

Hiring freezes are real, and that's why Q1–Q2 is three, not six. The
3-person shape is the one I can defend to a CFO without numbers
backing it yet.

## The minimum composition

Any one of these roles omitted leaves a gap that's costing real
money to leave open:

| Role | What they own | What the gap looks like |
|---|---|---|
| **Senior ML engineer** | Training, evaluation design, model selection | Program stalls at "we don't know which model to choose." |
| **Platform/serving engineer** | vLLM, Prometheus, Grafana | System runs but no one can debug the bad days. |
| **PM/eng-lead hybrid** | Eval set ownership, taxonomy, stakeholder alignment | Program has a model and no spec for "good." |

The PM/eng-lead hybrid is the role AI programs most often under-fund.
It's also the one with the steepest failure mode: without it, the
team optimizes the wrong metric because nobody owns the user outcome.

## The hiring question, broken down

| Role | Time-to-hire (cold market, 2025–2026) | Risk |
|---|---|---|
| Senior ML engineer, fine-tune experience | 4–6 months | Capable candidates are sparse; calibrating "fine-tune" vs "research" is non-trivial |
| Platform/serving engineer | 2–3 months | Easier; tech is well-known |
| PM/eng-lead hybrid | 4–8 months | Most ambiguous role; hard to find people who've done it at this scope |
| ML eval/curation engineer | 2–4 months | Tractable if you can describe the role well |
| SRE for 24/7 AI serving | 3–5 months | AI on-call is new enough that most SREs are juniors in this domain |

The
[People and time](../01-problem-and-constraints/constraints.md#5-people-and-time)
constraint says to budget 1.5–2× the optimistic estimate. That holds here.
Cold-market 6 month estimates are 9–12 months.

## Who I would not hire

| Out | Why |
|---|---|
| A "Head of AI" until Q4 (n=6+) | At n=3–5 the role's mandates are within scope of the eng-lead hybrid; the org gets a bonus layer too early otherwise |
| A "prompt engineer" as a full-time role | Prompting is a *skill*, not a *role*; full-time prompt engineers tend to optimize prompts for metrics that drift |
| A research-only ML engineer | Path C is product-bound. Hiring research here is a 12-month bet on a different bet |
| A "ML platform" team of 3+ before 5+ customers | Platform teams that span <5 use cases under-deliver; you're the first customer |

## The hybrid-ratio trap

The 3-person team is structurally a 2:1 ratio (eng:eng-lead). At 5+,
it swings to 3:1, then 4:1. The trap is reading this ratio the wrong
way:

- Some companies read 3:1 as "we have plenty of engineers." Read
  it instead as "we have exactly enough engineering to spend the
  eng-lead hybrid's time well."
- Eng-lead hybrid at n=3 is *part-time technical*. They should
  have commit rights on the codebase. Without that, they become a
  relay station between product and engineering, and program
  velocity halves.
- The eng-lead hybrid's first 3 months should be a specific kind
  of work: building the eval set and the failure taxonomy. That's
  what unblocks the model decision in Q3.

## What the team works on, by quarter

| Quarter | Senior ML | Platform | Eng-lead hybrid |
|---|---|---|---|
| **Q1** | Eval harness, lm-eval-harness integration | vLLM serving skeleton, Prometheus setup | Eval set curation, taxonomy draft |
| **Q2** | Path A prompt engineering, RAG tuning | Production rollout, Grafana panels | Quarterly eval refresh, adoption tracking |
| **Q3** | Failure taxonomy analysis, residual error reporting | Cost optimization, drift detection | Q3 decision write-up, Phase C scoping |
| **Q4** | Path C scoped experiment (or skip) | Adapter hot-load, alias rollback | Eval cycle, kill criterion gating |
| **Q5** | Path C in production, drift responses | On-call rotation, multi-model prep | Cost reporting, vendor diversification |
| **Q6** | Multi-model routing strategy | Multi-model serving infra | Q6 roadmap re-write |

The columns are the owners, not the only contributors. The senior
ML engineer on Path C in Q4 has a platform engineer reviewing the
serving change. The matrix isn't the org chart; it's accountability.

## Budgets, by quarter, in $k

| Quarter | Eng (3 people) | Eng (4 people) | Compute | Rater | Other | Quarterly total |
|---|---|---|---|---|---|---|
| **Q1** | 220 | – | 5 | 8 | 5 | 238 |
| **Q2** | 220 | – | 5 | 8 | 5 | 238 |
| **Q3** | 220 | – | 5 | 8 | 5 | 238 |
| **Q4** | 220 | 80 | 30 | 8 | 5 | 343 |
| **Q5** | 220 | 80 | 30 | 8 | 15 | 353 |
| **Q6** | 220 | 80 | 30 | 8 | 15 | 353 |
| **6-quarter total** | | | | | | **~1,760** |

The 6-quarter total ~$1.76M is the program's *floor*. That gets
you to a state where Path A and Path C coexist and you have a
multi-model plan. Anything cheaper is under-scoped.

## What I'd ask Finance to commit to

| Commitment | When | What I'd spend it on |
|---|---|---|
| 6-month runway for the 3-person team | Now | Path A + eval program |
| Quarterly eval-set budget ($8k) | Quarterly | Rater refresh, locking the timeline |
| Conditional Path C budget ($120k) | Q3, if justified | One scoped experiment, not a half-commitment |
| Path C production budget (~$250k/yr) | Q5, if Path C shipped | vLLM host, adapter infra, on-call coverage |

Each line item has a kill attached; finance gets the kill at the same
time they approve the spend. This is the opposite of "ask for money,
get money, discover what we spent it on." It's how to keep a six-
quarter program funded without surprise reviews.

## The rule I hold

> Resourcing is sequencing first, hiring second, contracting third,
> opportunistic fourth.

A 3-person team that ships is more credible than a 6-person team
that argues about scope. Earn the headcount with shipped evidence,
not with a slide that says "to do AI, you need 6 engineers" —
because nobody believes that slide, and the people who do are the
people who'd approve the wrong hires.