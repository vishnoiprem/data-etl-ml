# 04 — FM Evaluation Framework

> **Customer problem:** With 14 GenAI use-cases in production, we have no consistent way to detect quality regressions when models, prompts, or retrieval indices change. Build an evaluation framework that gates promotion of any change.

This project implements a **multi-tier evaluation harness** with quality regression detection:
- Offline evals (golden sets, adversarial sets)
- Online evals (sampled production traffic)
- LLM-as-judge metrics
- Statistical regression detection (bootstrap CIs, paired tests)

---

## 1. Theory: Why FM evals are hard

Traditional ML eval = `accuracy_score(y_true, y_pred)`. With LLMs:

- Outputs are **free-form text**, not labels.
- A "correct" answer can be phrased many ways (no exact match).
- Quality is **multidimensional**: faithfulness, helpfulness, safety, format, latency, cost.
- Evaluation is **expensive** (LLM-as-judge calls cost money + time).
- **Variance** is high: re-running the same prompt twice gives different outputs.

The framework must make this tractable.

## 2. The four eval tiers

| Tier | What it answers | Run when | Cost |
|---|---|---|---|
| 1. Unit/regression | Did this specific behavior change? | Every PR | seconds |
| 2. Golden-set offline | Did task quality change? | Before promotion | minutes, $1–$10 |
| 3. Adversarial / red-team | Did safety / robustness change? | Before promotion | minutes, $1–$10 |
| 4. Online / shadow | Is prod quality drifting? | Continuously | per-call cost |

## 3. Metric taxonomy

### Reference-based (we have a gold answer)
- **Exact match / F1** — for short, structured outputs.
- **BLEU / ROUGE** — translation, summarization (not great).
- **Semantic similarity** — embed both, cosine similarity.

### Reference-free (no gold)
- **Faithfulness** — answer is grounded in retrieved context (RAGAS).
- **Answer relevance** — answer addresses the question.
- **Context precision** — retrieved context is relevant.
- **Toxicity / PII** — model-based scorers, often Bedrock Guardrails.

### Production
- **Latency p50/p95/p99**, cost, error rate.
- **Refusal rate** — proxy for over-cautious models.
- **User signal** — thumbs up/down, dwell time, regenerations.

## 4. Regression detection

Two questions:
1. *Is the new model statistically worse?*
2. *Is the difference practically meaningful?*

We use:
- **Bootstrap confidence intervals** for each metric (resample 1000x).
- **Paired test** (Wilcoxon signed-rank) when same prompts run on both models.
- **Practical thresholds** (e.g., "regression = >2pt drop AND CI excludes zero").

## 5. Architecture

```
┌────────────────────────────────────────────────────────────────┐
│              Eval Catalog (S3 + DynamoDB)                       │
│  golden_sets/ (versioned)  +  adversarial_sets/                 │
└──────────────────────────────┬─────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│              SageMaker Pipelines — Eval Runner                  │
│   ┌──────────┐  ┌──────────────┐  ┌────────────────────┐       │
│   │  Inputs  │→ │  Batch infer │→ │ Score (incl. LLM   │       │
│   │  golden  │  │  via Bedrock │  │  judge via Bedrock)│       │
│   └──────────┘  └──────────────┘  └─────────┬──────────┘       │
│                                              ▼                  │
│                                   ┌────────────────────┐        │
│                                   │ Regression checker │        │
│                                   └─────────┬──────────┘        │
└─────────────────────────────────────────────┼───────────────────┘
                                              ▼
                                   PASS → Model Registry approved
                                   FAIL → block + Slack alert
```

## 6. Quick Start

```bash
pip install -r requirements.txt
make demo
```

The demo:
1. Loads two synthetic "candidate models" (different stub LLMs).
2. Runs both against a golden set + an adversarial set.
3. Computes per-metric scores with bootstrap CIs.
4. Decides PASS/FAIL via the regression policy and prints the gate report.

## 7. What "Done" Looks Like

| Metric | Target |
|---|---|
| Eval suite runtime | < 15 min |
| Eval cost | < $5 / candidate |
| Regression detection accuracy | > 95% on injected regressions |
| Coverage | ≥ 1 golden set + ≥ 1 adv set per use case |
