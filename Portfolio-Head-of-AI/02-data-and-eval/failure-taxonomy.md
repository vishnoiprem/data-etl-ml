# Failure Taxonomy

The build-vs-buy decision in
`../01-problem-and-constraints/build-vs-buy-decision.md` refuses to
fund a fine-tune until we know *where the residual error comes from*.
"This document is the answer to that condition.

Without a taxonomy, every failure looks the same — the model was
wrong — and the response is always "make the model better." With one,
most failures resolve to a specific lever, and a lot of them turn out
to not need a fine-tune at all.

## The seven buckets

Every error on the 500-row diagnostic eval gets exactly one primary
bucket. "Primary" is load-bearing: a wrong answer that also failed to
retrieve is one failure, not two, or the percentages won't sum.

| # | Bucket | Definition | Right lever |
|---|---|---|---|
| **F1** | Retrieval gap | The model didn't have the fact in context | RAG / index, **not** fine-tuning |
| **F2** | Knowledge gap | The fact isn't in any index — the org doesn't have it written down | Write the doc. Nothing else works. |
| **F3** | Reasoning gap | The facts were in context, the model still got it wrong | This is the only bucket fine-tuning reliably fixes |
| **F4** | Format / style gap | Right answer, wrong shape — wrong length, wrong register, wrong JSON | Prompt + structured output, maybe a light fine-tune |
| **F5** | Instruction-following gap | Model ignored an explicit constraint in the prompt | Prompt. Always prompt first. |
| **F6** | Refusal / over-caution | Model declined, or hedged into uselessness | System prompt calibration, threshold tuning |
| **F7** | Evaluation ambiguity | Raters disagreed; the label may be wrong | Fix the eval set. Not a model bug. |

## The diagnostic, and what it decides

The diagnostic is the 500-row labeled eval + a failure taxonomy +
an error breakdown by category, run *before* committing to Path C.

The distribution that decision hinges on:

> **If ≥60% of errors are F1 or F5, fine-tuning is the wrong lever.**

That threshold is not arbitrary. It's the point at which retrieval and
prompt engineering have clearly failed to close the gap, and the
residual is genuinely about model behavior rather than about what we
fed the model.

Concretely, for the ticket-classification workload in the
build-vs-buy doc:

| If the breakdown is… | Then… |
|---|---|
| Mostly F1 (model didn't know our product names) | RAG over internal product docs. This is the *expected* answer. |
| Mostly F3 (knew it, misclassified) | Path C is justified — this is the bucket it fixes. |
| Mostly F4/F5 | Structured output + prompt. Cheap. Two weeks. |
| Mostly F2 | The org has a documentation problem. Escalate; don't fine-tune. |
| Mostly F7 | Stop. Your eval set is broken. Fix it before anything else. |

**The uncomfortable outcome is F2.** A large F2 bucket means no amount
of model work helps, because the answer doesn't exist. I've seen a
quarter of engineering capacity go into a fine-tune that was
pathologically incapable of fixing a missing internal wiki page.

## How I assign buckets without it becoming a 6-week project

The full version is three raters, a disagreement review, and a
written taxonomy doc. That's the right version for a quarterly
re-baseline. For a first pass, this is enough:

1. **Two raters**, independently, on 200 rows (not 500 — the first
   pass is directional).
2. Each rater assigns one primary bucket per row. Buckets are on a
   printed card; no free-text "other" on the first pass, because
   "other" is where good intentions go to die.
3. **Adjudicate disagreements yourself.** You're the Head of AI; this
   is 3 hours and it teaches you more than the metrics do.
4. Anything that doesn't fit a bucket becomes F7 by definition.
   That forces taxonomy growth to be deliberate rather than
   accidental.

Turnaround: about a week of part-time rater time. It produces the
single most decision-relevant artifact in the entire program.

## Why F7 is in the taxonomy at all

Because F7 is the bucket teams refuse to track, and it's the one
that invalidates everything else.

If 15% of your eval rows are ambiguous, then a "9.4% → 7.1%
hallucination rate" improvement is inside the noise band. You cannot
tell whether you improved or whether your raters got less strict.
Reporting a trend without reporting the ambiguity rate is how a
program convinces itself it worked.

F7 rows go into an **ambiguity set** and get re-written. They're not
discarded — they're the highest-information rows in the set, because
they tell you your task definition is underspecified.

## The taxonomy is versioned

Buckets get added, renamed, and split. A run's failure breakdown is
only comparable to another run's if they used the same taxonomy
version. So:

- Taxonomy version goes in the MLflow run params, next to
  `is_synthetic`.
- A taxonomy change invalidates trend lines; you re-baseline, you
  don't splice.

This is unglamorous and it's the difference between a real eval program
and a series of unrelated snapshots.

## What this looks like wired to code

| Concern | Implementation |
|---|---|
| Leakage between train and eval | `agent/dataset.py` — Jaccard filter against `HELD_OUT_PROMPTS` |
| Which rows were graded how | `agent/evaluate.py` — per-row scores logged to MLflow |
| Run-to-run comparability | Taxonomy version + eval-set version in run params |
| Trend aggregation by bucket | `scripts/ablation_table.py` queries the tracking server |
| Drift in the failure mix | `agent/monitor.py` — drift score on request-embedding distribution |

`scripts/ablation_table.py` is the piece that matters most here. It
means the README's failure-breakdown table is *generated from the
tracking server*, not typed by hand. Hand-typed tables drift from the
runs within a quarter; generated ones can't.

## The rule I hold

> Never fund a model change until you can name the bucket the change
> targets, and show that the change moves that bucket's count.

No bucket named → don't fund. Bucket named → wrong bucket for
fine-tuning → fund the cheaper lever instead. This is the whole
argument of `../01-problem-and-constraints/build-vs-buy-decision.md`
reduced to one sentence.