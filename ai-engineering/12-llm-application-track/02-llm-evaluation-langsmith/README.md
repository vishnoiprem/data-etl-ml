# Course 2 — LLM Application Evaluation with LangSmith

> Source: Data Vidhya — LLM Application Evaluation with LangSmith
> Level: Intermediate-Advanced | Prereqs: Course 1, basic pytest

---

## Course Promise

> "Ship LLM changes with the same confidence you ship database migrations — because you have a regression suite that catches it."

This is the course most teams skip, then regret. Evaluation is not "vibes and a smoke test." It's a **systematic harness** with datasets, evaluators, experiment tracking, and CI gating. LangSmith is the platform; this course teaches you how to use it without becoming a hostage to it.

---

## Lesson Index

| # | Lesson | Type | Theme |
|---|--------|------|-------|
| 1 | [Why eval is the moat](./01-why-eval-is-the-moat.md) | Article + Worked Example | The 200-query set, eval-first vs eval-last, regression detection |
| 2 | LangSmith fundamentals | Article | Projects, traces, runs, datasets, examples |
| 3 | Building an eval dataset | Article | Source, label, schema, freshness |
| 4 | Evaluators — code, LLM-as-judge, human | Article | Exact match, embedding distance, labeled-score-string |
| 5 | Running experiments | Article | `evaluate()`, splits, comparison, parallel runs |
| 6 | CI gating & regression detection | Article | GitHub Actions, thresholds, alerting |
| 7 | Online eval & production monitoring | Article | Drift, feedback collection, annotation queues |
| 8 | Pairwise evaluation & human preference | Article | Head-to-head, ELO, calibration |

---

## What "good" looks like after this course

1. Every PR that touches a prompt, model, or chain runs an eval suite.
2. Regressions are caught **before merge**, not in production.
3. You can answer "is the new model better than the old?" with a number, not a vibe.
4. You have an eval set that refreshes quarterly (not "the eval set we wrote in 2024").
5. You can defend a model swap with an eval report attached.

---

## The Lead Lesson

> **Lesson 1 — [Why eval is the moat](./01-why-eval-is-the-moat.md)** — the framing, the failure modes, and a complete CI-gated eval pipeline against a real LangSmith dataset. Includes a worked example that gates a model swap from Haiku → Sonnet behind a 92% exact-match threshold.
