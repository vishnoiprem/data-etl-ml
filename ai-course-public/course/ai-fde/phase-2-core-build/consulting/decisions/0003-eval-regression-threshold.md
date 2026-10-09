# ADR-0003 — Eval regression threshold 0.05

- **Status:** accepted
- **Date:** 2026-W4 (Phase 2, week 2)
- **Owner:** FDE
- **Stakeholders consulted:** Mei (CS), Sarah (ops)

## Context

The eval set returns 4 metrics on 30 rows. The question is: **what change in a metric should block a deploy?** Too tight and we ship nothing; too loose and we ship regressions.

## Decision

**Any single-metric drop > 0.05 (5 percentage points) blocks the deploy.** The CI gate runs on every PR; the deploy pipeline blocks on the gate.

## Considered alternatives

| Threshold | Trade-off | Verdict |
|---|---|---|
| 0.01 (1pp) | Catches every blip; high false-positive rate; the team learns to ignore alerts | rejected — alert fatigue is worse than a regression |
| **0.05 (5pp)** | Catches real regressions, tolerates LLM non-determinism | ✅ chosen |
| 0.10 (10pp) | Only catches catastrophic regressions; misses the "silent rot" case | rejected — the postmortem (Case Study #3) caught a 5pp drop that would have been missed |
| Manual review | Flexible, no false positives | rejected — the postmortem incident happened on a Wednesday, not at the Monday cadence; manual review was 4 days too slow |
| Two-metric drop | More robust to single-metric flukes | rejected — we only have 4 metrics; requiring 2 drops to fail makes the gate too loose on the worst regressions |

## Consequences

- The eval set runs on every PR touching `service/`, `shared/eval_set.jsonl`, or `shared/style-guide.md`. CI fails on `any metric delta > 0.05`.
- A prompt change that drops faithfulness by 0.07 is blocked; a change that drops it by 0.03 is allowed (and noted in the iteration report).
- The threshold is a config in `service/eval.py` (default 0.05). Changing the threshold is itself an ADR-worthy decision.

## The math behind 0.05

- 30 rows × 4 metrics = 120 observations.
- The 95% confidence interval on a proportion at n=30 is roughly ±0.18. A 0.05 drop is below the CI for a single run.
- We need **two consecutive runs** to confirm a 0.05 regression — that's why the CI gate fails the PR but the Monday iteration review can re-evaluate.
- The 0.05 number is the **observed effect size** in Case Study #3 (the postmortem): the 0.07 faithfulness drop is what would have been a SEV-1 in production.

## Why this is the right call

- The eval set is the spec. A threshold that's too tight turns the eval into a tax; a threshold that's too loose turns it into a checkbox. 0.05 is the point where the threshold catches real regressions without creating alert fatigue.
- **The threshold is the contract between the prompt engineer and the customer.** Below it, the prompt changes ship; above it, they go back to the drawing board. The eval set is the regression detector; the threshold is the rejection line.

## When to revisit

| Trigger | Change |
|---|---|
| Eval set grows to 100+ rows | Lower threshold to 0.03 (smaller CI per run) |
| Mei's thumbs-up rate drops > 3pp | Lower threshold to 0.03 (a tighter signal) |
| More than 2 false-positive CI fails per month | Raise threshold to 0.07 |
