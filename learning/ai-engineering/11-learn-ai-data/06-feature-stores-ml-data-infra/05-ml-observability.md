# Lesson 5 — ML Observability

> **Type:** Article · Module 6 · Feature Stores & ML Data Infrastructure
> Detecting drift, skew, and silent regressions in production ML.

---

## The silent failure mode

ML models fail **silently**. A traditional microservice throws a 500, you get paged. An ML model returns confidently-wrong predictions, your dashboards show "all green," and customers churn.

```
   TRADITIONAL SERVICE                     ML SERVICE
   ───────────────────                     ──────────
   error rate = 5%                         error rate = 0%
   paged immediately                       silent degradation
                                          model accuracy dropped from
                                          0.91 → 0.72 over 3 weeks,
                                          nobody noticed.
```

This is why **ML observability** is a discipline. It's not enough to log predictions. You have to log **the inputs that produced them** and **the downstream outcomes they influenced**, so you can detect when reality shifts under the model.

---

## The three layers of ML observability

### 1. Data observability — is the input distribution shifting?
- Feature values today vs. feature values at training time
- Volume, missingness, schema changes
- Out-of-range values

### 2. Model observability — is the model behaving?
- Prediction distribution shift
- Confidence / score distribution
- Per-segment accuracy (where you have ground truth)

### 3. Outcome observability — is the model helping?
- Downstream business metrics (CTR, conversions, fraud caught, NPS)
- Delayed labels (purchase happened? refund happened?)

```
   ┌──────────────────────────────────────────────┐
   │  DATA              MODEL           OUTCOME   │
   │  ────              ─────           ───────   │
   │  feature drift     score drift     CTR ↓     │
   │  schema change     confidence ↓    AOV ↓     │
   │  missing values    unfair segment   refund ↑  │
   │  volume shift      calibration      retention │
   │                                              │
   │  cheap to detect   medium           slow,    │
   │  (no labels)       (need labels)    costly   │
   └──────────────────────────────────────────────┘
```

---

## The data drift types

```
   COVARIATE DRIFT          (P(X) changes)
   ──────────────
   The input distribution shifted.
   E.g. user ages skewing older; "device=mobile" share jumps
   from 60% → 85%.
   Detect: PSI, KS test, population stability index.


   CONCEPT DRIFT            (P(Y|X) changes)
   ──────────────
   The same input means something different now.
   E.g. "click on ad" no longer means "intent to buy"
   as much as it used to.
   Detect: monitor downstream outcomes.


   LABEL DRIFT              (P(Y) changes)
   ──────────────
   The class balance changed.
   E.g. fraud rate doubled in a week.
   Detect: monitor label distribution (with delayed feedback).


   FEATURE DRIFT            (a feature broke)
   ──────────────
   One feature's distribution changed because of an upstream
   pipeline change, not the world.
   E.g. "country_code" used to be ISO-2, now it's ISO-3.
   Detect: per-feature distribution + schema checks.
```

The **covariate drift** is the cheapest to detect and the most often conflated with concept drift. Different fixes: covariate → retrain or reweight; concept → revisit labels, may need a new model.

---

## Detecting drift

### Statistical tests
- **PSI (Population Stability Index)**: bucket the distribution, compare to baseline
- **KS test (Kolmogorov–Smirnov)**: continuous features
- **Chi-squared**: categorical features
- **JS divergence**: distributions as a whole
- **Wasserstein distance**: continuous, sensitive to shift in mass

```python
from scipy.stats import ks_2samp, chi2_contingency
import numpy as np

def psi(expected, actual, bins=10):
    expected_percents = np.histogram(expected, bins=bins)[0] / len(expected)
    actual_percents = np.histogram(actual, bins=bins)[0] / len(actual)
    psi = np.sum((actual_percents - expected_percents) *
                 np.log(actual_percents / expected_percents))
    return psi

# PSI < 0.1   = stable
# 0.1–0.25   = small shift, watch
# > 0.25     = significant shift, retrain
```

### What to compute continuously

| Signal | Cost | Tells you |
|---|---|---|
| Per-feature PSI vs baseline | Cheap | Feature distribution shifted |
| Per-feature missingness rate | Cheap | Pipeline broke |
| Per-feature mean / std | Cheap | Schema or scale changed |
| Schema diff (column names, types) | Cheap | Upstream changed |
| Prediction distribution | Cheap | Model behavior changed |
| Confidence / score distribution | Cheap | Calibration issues |
| Per-segment accuracy | Costly (needs labels) | Model unfair or out of skill |
| Downstream outcome | Slow (days/weeks) | Business impact |

---

## The "shadow / canary / champion-challenger" deployment pattern

To catch silent regressions, deploy new models in parallel with the production model and compare.

```
   traffic:  "new user signed up"
                │
        ┌───────┴───────┐
        ▼               ▼
   Champion         Challenger
   (current prod)   (new model)
        │               │
        ▼               ▼
    prediction        prediction
        │               │
        └───────┬───────┘
                ▼
           A/B log
           compare over N events
```

| Mode | What it does | When to use |
|---|---|---|
| **Shadow** | Challenger gets the input, logs prediction, but the response is from champion | Before any production exposure. Detects gross failures. |
| **Canary** | 5% of traffic to challenger, 95% to champion | Once shadow passes. Watches for skew in outcomes. |
| **A/B** | 50/50 split, measure downstream outcome | When you want statistical comparison. |

The promotion rule: if challenger matches or beats champion on your guardrail metrics (accuracy, latency, business KPIs) over the test window, promote.

---

## The "silent feature regression" trap

```
   WEEK 1:    model accuracy = 0.91
   WEEK 2:    upstream changes how "session_duration" is computed.
              (was: seconds, now: minutes)
   WEEK 3:    model accuracy = 0.62.  No alert.

   Why: nobody alerted on the 100x scale change in session_duration.
        The schema didn't change. The value did.
```

The fix: **per-feature alarm on distribution shape, not just schema**. Mean, std, min, max percentiles, missing rate. If any one of them jumps, page someone.

---

## The "delayed ground truth" pattern

Most production ML doesn't have instant labels. You can only know if a churn prediction was right months later. To detect regressions faster, use **proxy labels**:

| True label | Proxy (fast) |
|---|---|
| Churn | Inactivity in 7 days |
| Fraud | Manual review queue |
| LTV | Refund / repeat purchase |
| Click | Already known |
| Conversion | Already known |

Proxy labels catch fast problems. True labels catch slow ones. **Use both.**

---

## The "fairness / segment drift" check

A model can be accurate overall but **catastrophic for a segment**.

```python
# Per-segment accuracy check
def check_fairness(predictions, labels, segments):
    for segment in segments.unique():
        mask = (segments == segment)
        acc = (predictions[mask] == labels[mask]).mean()
        if acc < GLOBAL_ACC * 0.7:
            flag("drift", segment, acc)
```

In production, watch for **per-segment** accuracy drop. The aggregate may be flat.

---

## What "good" looks like

- **Drift detected within 1 hour** of an upstream pipeline change
- **Per-feature distribution monitored**, not just overall
- **Per-segment accuracy tracked**, not just aggregate
- **Champion-challenger running** for every model change
- **Proxy labels give early signal**, true labels confirm
- **Alerts to a human**, not to a metrics dashboard

---

## Tooling

| Tool | Focus |
|---|---|
| **Arize Phoenix** | Open-source ML observability |
| **WhyLabs** | Data + model drift |
| **Evidently AI** | Open-source drift + reports |
| **Fiddler** | Model monitoring + explanations |
| **Grafana + custom** | Build it yourself (cheap, more work) |

For most teams, **Evidently or Phoenix + Grafana** is 80% of what you need, free.

---

## What Comes Next

> Lesson 6 — **LLMOps** — same observability principles, but for LLM applications: prompt versioning, eval harnesses, feedback loops, and the things LLMs break that classic models don't.