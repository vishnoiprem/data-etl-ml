# Eval Strategy

This is the chapter that decides whether the rest of the program is
real. Every claim in
`../01-problem-and-constraints/build-vs-buy-decision.md` — the 9.4%
hallucination rate, the "Path C is a bet not a purchase" argument —
rests on the eval machinery existing *before* the fine-tune starts,
not after.

## The failure mode this prevents

The most common failure in a fine-tune program is **grading yourself
on the training distribution.** You fine-tune on tickets, you test on
tickets, you report 89%, and it means nothing because the model has
seen the shape of the answer.

The second-most-common is **evaluating before you can measure**. Teams
ship a model, users report it's worse, and nobody can say *which*
category got worse, so the response is guesswork.

The only defense for both is an eval harness that runs on every
change and produces a per-category breakdown.

## Three tiers, run at different cadences

Not one eval, but three, because they answer different questions:

| Tier | What it answers | Cadence | Cost | Where |
|---|---|---|---|---|
| **Tier 0 — CI smoke** | "Did I break the pipeline?" | Every PR | Seconds | `tests/test_smoke_synthetic.py` |
| **Tier 1 — regression suite** | "Did this change make the model worse?" | Every PR, nightly on main | ~20 min GPU | `agent/evaluate.py` on held-out domain tasks |
| **Tier 2 — human-rated eval** | "Is this good enough to ship?" | Monthly, pre-release | 40–60 hrs rater time | `agent/evaluate.py` + human loop |

The failure I most want to avoid is **skipping Tier 2 and promoting
on Tier 1**. Tier 1 is automated, cheap, and measures the wrong thing
at the margin — it's a *regression* signal, not a *quality* signal. A
model can improve every automated benchmark and still be worse on
your actual distribution.

### Tier 0: the synthetic smoke

8 synthetic samples → 1 training step → adapter loads → serving
endpoint returns 200. It exists purely to make `make test` meaningful.
It proves the plumbing, and it proves it in seconds on a machine with
no GPU. If this fails, nothing downstream is worth reading.

### Tier 1: the regression suite

`agent/evaluate.py` wraps `lm-eval-harness` on three tasks chosen for
what they each catch:

| Task | What a drop means |
|---|---|
| `arc_challenge` | Reasoning degraded. Usually the LoRA rank or target modules changed. |
| `hellaswag` | General instruction-following collapsed. Usually the chat template is wrong. |
| `truthfulqa_mc2` | The model got more confidently wrong. This is the hallucination proxy. |

Plus a **held-out domain task** — 200 rows never seen in training,
graded on the domain-specific criteria (in the reference
implementation, correctness of the company's entity names).

The gate: a PR that drops any task by more than 2 points fails CI.
This is the rule from `agentic-ai/README.md` §2 ("eval is in the loop,
not after"), implemented rather than stated.

### Tier 2: the human-rated eval

This is the one that actually decides ship/no-ship, and the one teams
budget for last when they should budget for it first.

- **200 rows**, sampled from the *live* distribution, refreshed
  **quarterly**.
- **3 raters per row**, 3-point scale (correct / partially correct /
  wrong), plus a required justification string on every "wrong."
- **Blind** — the rater doesn't see which model produced the output.
- **Disagreement is data.** If two raters disagree on a row, that row
  goes into the ambiguity set and the taxonomy in
  `failure-taxonomy.md` gets a new bucket.

The justification string matters more than the score. Scores tell you
*that* quality moved; justifications tell you *why*, and the "why" is
what determines which lever to pull.

## Time-based holdout is the only honest holdout

A random row-level split leaks in a specific, predictable way: the
same customer phrasing the same answer, appearing in both train and
eval. You report a number and it evaporates on contact with July.

So:

- Eval is drawn from a **time window after** the training window.
- The eval set is **not** refreshed from the same distribution the
  model was trained on; it's re-sampled from current traffic.
- When the product line changes, the eval set changes with it. This is
  the "distribution match" constraint from
  `../01-problem-and-constraints/constraints.md` (§2).

## The number I'd put in the board deck

Not "accuracy." **Hallucination rate on company entities, on a
held-out human-rated set, refreshed monthly.**

- Today (Path A baseline): 9.4%
- Target (Path C): ≤2%

Why that one and not aggregate accuracy:

1. It's the thing engineering actually complained about for six
   months. The metric matches the complaint.
2. It's binary per-row, so raters agree with each other more often
   than on "task completion."
3. It's hard to accidentally improve by making the model more
   cautious — which is exactly the failure mode of a naive RAG
   prompt.

If I can only report one number, it's this one.

## Where the cost lives

40–60 hours of rater time per refresh is not a rounding error; it's
roughly $5–8k per quarter at blended contractor rates. That is
explicitly in the cost model in
`../03-system-architecture/cost-model.md`, and it's the reason the
build-vs-buy doc argues for Path A first — Path A's eval set is the
same artifact, so the rater cost is paid once and reused either way.

## What I would refuse to do

- **Ship on aggregate accuracy alone.** It's the metric most likely
  to improve while the actual user experience degrades.
- **Let the model grade itself.** Even with a stronger judge model,
  self-evaluation on the training distribution is circular. A judge
  is a useful *second* opinion, not the primary signal.
- **Freeze the eval set.** A frozen eval set is a benchmark you
  overfit to over time. Refresh it quarterly even when the numbers
  look good — *especially* when they look good.

## The rule I hold

> The eval set is the deliverable. The model is an artifact.

`../01-problem-and-constraints/build-vs-buy-decision.md` argues that
Path C shouldn't be funded until we have a labeled eval set and a
failure taxonomy. That's not caution for its own sake — it's the
argument that *the eval set is the thing you build first*. Everything
else is downstream of being able to measure.