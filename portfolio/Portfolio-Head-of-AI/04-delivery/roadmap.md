# Roadmap

A roadmap is a sequenced bet. Every line on this timeline is
defensible by what it *unblocks*, not by what it *is*. If a sequence
doesn't have a unblock ordering it isn't a roadmap; it's a wish list.

## The principle

> A roadmap doesn't say "what we want to build." It says "what we
> will stop doing if this isn't done in 12 weeks."

That second question is the one most AI roadmaps refuse to answer,
and it's why most AI roadmaps quietly lose their budget in Q3.

## The 6-quarter plan

| Quarter | Theme | What gets shipped | What we kill if we don't |
|---|---|---|---|
| **Q1** | Don't build a fine-tune. Get legible. | Path A: retrieval + prompt over internal docs. Eval harness built. Cost dashboard live. | None — this is observation, not commitment. |
| **Q2** | Use Path A. | First 5 ticket intents at p50 ≤ 0.9s, p95 ≤ 2s. Eval set refreshed quarterly. Adoption ≥50%. | The fine-tune program — see kill below. |
| **Q3** | Re-litigate the fine-tune decision. | After 6 months of Path A data: residual error breakdown by `failure-taxonomy.md` buckets. | The fine-tune program if F1+F5 ≥ 60%. |
| **Q4** | Conditional Path C, scoped. | One 12-week adapter experiment with a defined kill criterion. | Either the adapter or the next initiative in the queue, not both. |
| **Q5** | Operate + extend. | Path A + Path C coexisting. Adapter swapped in/out by alias. | The vendor contract renewal — Path C has to win by Q5. |
| **Q6** | Decouple from the model. | Multi-model serving. Per-task routing: cheap model for bulk, big model for the long tail. | The single-vendor dependency. |

The pattern is **observe → commit → re-litigate → commit → extend**.
Each transition is gated by evidence from the previous quarter, not
by a calendar.

## What the gates look like, concretely

**Q1 → Q2 gate:** eval harness running on a 200-row held-out set,
weekly, with per-intent scores. Costs and latencies exposed in
Grafana.

**Q2 → Q3 gate (the re-evaluation):** 6 months of Path A production
data, run through the failure taxonomy. The output is a number:
"What percentage of residual errors are F1, F2, …, F7?" If F1+F5
≥60%, Path A is still in flight; the fine-tune program is *not*
funded yet.

**Q3 → Q4 gate:** Path C is funded only as a 12-week scoped
experiment. The kill criterion is set *before training starts*:
"doesn't lift Tier-2 holdout score by ≥3 absolute points in 6 weeks
of training, stop and migrate to a bigger base model."

**Q4 → Q5 gate:** adapter is in production serving a non-trivial
percentage of traffic (target ≥30%). Eval set has been refreshed
mid-experiment and didn't show regression. Drift score is <0.3 for
two consecutive weeks.

**Q5 → Q6 gate:** Path C is contributing ≥40% of total request
volume without regression on the Path A backlog. Cost per task on
Path C is ≤ Path A's p95. Multi-model serving is more than a
diagram.

## What the kills look like

| Killed | Trigger | Replacement |
|---|---|---|
| Path C, planned | Q3 failure taxonomy shows F1 dominant | Continued Path A investment |
| Path C, in flight | Q4 kill criterion not met | Big-base-model vendor evaluation (now justified by real data) |
| Self-hosting | Q5 cost per task exceeds Path A's p95 | Vendor fallback — same client, config flip |
| Single-model commitment | Q6 multi-model not showing wins | Stay single-model; document why |

Each kill is named in advance because the moment of killing is the
moment of maximum internal pressure not to. Pressure that doesn't
have a written counter cannot be resisted.

## Dependencies, in order

The roadmap's content, ordered by what unblocks what:

```
         ┌─────────────────────────────────────────┐
         │ Q1: Eval harness + Path A retrieval     │  ←── unblocks everything below
         └────────────────────┬────────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────────┐
         │ Q2: Path A in production, observed      │
         └────────────────────┬────────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────────┐
         │ Q3: Failure taxonomy, residual error    │
         └────────────────────┬────────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────────┐
         │ Q4: Conditional fine-tune (scoped)      │
         └────────────────────┬────────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────────┐
         │ Q5: Path A + Path C coexisting          │
         └────────────────────┬────────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────────┐
         │ Q6: Multi-model serving                  │
         └─────────────────────────────────────────┘
```

Each step's evidence is what unlocks the next. That's the unblock
relation; everything else is decoration.

## Why not parallel-track Path A and Path C

I have a specific answer. The temptation on every AI team is to
"keep options open" by parallel-tracking the fine-tune. The 6-month
cost of that is:

- $250k of engineering time on Path C, going to a model that may
  improve 0 points and may regress 2.
- Continued 9.4% hallucination rate on Path A because nobody has
  100% focus on it.
- A failure-taxonomy analysis that doesn't happen because the team
  didn't prioritize it.

Sequencing solves this. **Path A is the default; Path C is the
option that gets exercised only if Path A's residual errors are
the right shape.**

## What I would not put on a roadmap

| Out | Why |
|---|---|
| Quarterly new features | Features are quarterly bets on the model layer, not roadmap lines |
| Vendor showcases | "Try model X" is a 2-week evaluation, not a quarter |
| Agentic frameworks upgrades | Frameworks are plumbing; swap them quietly |
| Org-chart redesign | Org design (`org-design.md`) is a separate document with its own cadence |
| Anything not named with a kill | If I can't name what we'd stop, I shouldn't be doing it |

## The rule I hold

> A roadmap without explicit gates is a wish list. A roadmap with
> explicit gates but no explicit kills is a hostage negotiation.

Both halves matter. Both are missing from most AI roadmaps I've seen
at the 200-person stage. Putting both halves on the same page is
what makes the sequence defensible to a CFO and a board.