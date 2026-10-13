# LLM evaluation harness (reproducible runs)

A single run, all metrics, one row. Every run gets a unique id; a run is reproducible from `(run_id, model_id, prompt_version, eval_set_sha)`. The harness is the artifact; the model weights are downstream.

## Shape

```
   labeled eval set (items[])        model_fn(prompt) -> response
            │                                  │
            └──────────────┬───────────────────┘
                           ▼
                  run_eval(items, model_fn)
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
        item_results  aggregates     run_id
        (per-item)    (per-metric)   (sha of all inputs + outputs)
                           │
                           ▼
                  RunRecord
                  (persisted to disk/MLflow/W&B)
```

## What I built

- `eval/score.py` — `EvalItem` (prompt + expected + rubric) + `ItemResult` (per-item scores) + `RunRecord` (the row) + `run_eval()`.
- `score_item()` computes multiple metrics per item: `exact_match`, `rubric_pass` (must_contain + must_not_contain), `length`.
- `aggregate()` rolls up to per-metric rate (for binary) or mean/p95 (for continuous).
- `run_id` is a SHA of `model_id + prompt_version + eval_set_sha + item_results` — the same run with the same outputs gets the same id.
- Smoke test: 4 questions, run a "good" model (returns gold) and a "bad" model (returns "I don't know"), compare aggregates.

## Real numbers

- Eval set sizes: 100-1000 items per task; full harness = 10-50K items across 5-10 tasks.
- Reproducibility: identical inputs + identical model + temperature=0 → identical outputs → identical run_id.
- Metric choice: exact_match for short-form, rubric for long-form, LLM-as-judge for subjective, BLEU/ROUGE for translation/summarization.
- A run takes 5-30 min on 1K items with a hosted model; longer locally.

## What I learned the hard way

- **The eval set is the most important artifact.** A weak eval set gives you confident wrong answers. Invest in it; version it; never edit it on the fly.
- **The prompt version is the second most important.** "v1", "v2", ... in a registry. Without it, you can't tell which prompt produced which score.
- **Temperature 0 for eval.** Anything else is non-reproducible.
- **Aggregate metrics hide item-level regressions.** Always persist the per-item results. A 0.5% drop in aggregate might be 5 of 1000 items completely broken.
- **Run ID dedup.** If you accidentally re-run, the run_id is the same and you can skip writing it again. Saves money on hosted models.

## When to use

- You're shipping a model and need to know if v2 is better than v1.
- You're tuning prompts and need before/after evidence.
- You're comparing models (Llama vs Mistral vs Claude) on the same task.

## When NOT to use

- Quick A/B in dev (use 5 items and a notebook).
- Tasks without a meaningful gold answer (creative writing — use a human eval).

## Run

```bash
pip install -r requirements.txt
make smoke
```

---

## What this is NOT

- **Not an LLM-as-judge replacement.** The
  `rubric_pass` (must_contain / must_not_contain) and
  `exact_match` metrics work for tasks with a
  defensible right answer. For subjective tasks
  (creative writing, open-ended chat), LLM-as-judge
  is the right tool, and it needs its own calibration
  to be reliable.
- **Not an offline-only harness.** The pattern
  generalizes to online eval (log interactions →
  run metrics on a sampled subset → write back to
  the same `RunRecord` schema). The shape is the
  same; the cadence is different.
- **Not a model leaderboard.** A `RunRecord` is
  one model + one prompt + one eval set at one
  temperature. A leaderboard is many `RunRecord`s
  cross-referenced; that's a different artifact.
- **Not a substitute for human review.** The harness
  catches regressions and validates versions. It
  doesn't tell you whether the model is *useful*
  in production. The two are different questions;
  use both.

---

## Related directories

- [`../17-mlops-control-plane/`](../17-mlops-control-plane/) —
  the deployment + canary + rollback patterns that
  consume the `RunRecord` to decide whether to
  promote a model.
- [`../19-rerank-service/`](../19-rerank-service/) —
  the rerank eval that this harness can measure
  (retriever recall, reranker lift).
- [`../28-rlhf-dpo-train/`](../28-rlhf-dpo-train/) —
  the alignment training that this harness scores
  (the SFT → DPO progress, the preference
  margin).
- [`../33-mlflow-tracker/`](../33-mlflow-tracker/) —
  the experiment-tracking integration; the
  `RunRecord` lands in MLflow / W&B as a run.

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
