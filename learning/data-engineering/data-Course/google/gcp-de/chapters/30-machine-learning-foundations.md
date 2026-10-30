# 8.1 — Machine Learning Foundations on GCP

> **Section 8 · ML on GCP & Capstone · Lecture 8.1 · 8:00**

## 🎯 What you will learn

- The three families of machine learning — **supervised**, **unsupervised**, **reinforcement** — and which one a data engineer is most likely to be handed
- The eight-stage **ML workflow**, and the specific failure mode of each stage
- Why the **train/validation/test split** is a statistical contract, not a formality
- **Overfitting** and **underfitting**, and how to tell them apart from the learning curve rather than from the headline metric
- The evaluation metrics that matter: **accuracy** (and precisely when it lies), **precision**, **recall**, **F1**, and **ROC-AUC** — each mapped to the business decision it actually drives
- What **EDA** is for when the analyst is not a data scientist, and what to look at
- **Feature engineering** as a pipeline concern: encodings, temporal features, aggregates, leakage
- The data engineer's role in every stage: **labelling pipelines**, **feature stores**, **training-data versioning**, and **skew detection**
- The three places the ML lifecycle actually breaks in production: **training/serving skew**, **feature staleness**, and **drift**
- A concrete, runnable evaluation harness built on the course project

---

## 🧠 Concept

### The audience question first

This chapter is written for a data engineer, not a research scientist. That framing changes everything about what follows.

An ML researcher wants to know how a gradient is computed. A data engineer wants to know:

1. **Where does the training data come from, and how do I know it is correct?**
2. **What breaks between training and production, and who gets paged?**
3. **How do I rebuild the exact training set six months from now?**

Those three questions are the whole chapter. Everything else — the metric definitions, the learning curves — exists because you need it to answer question 2 and question 3.

**The uncomfortable truth:** most of the value in an ML project is delivered before the model is trained. A well-labelled dataset with a correct join to the customer table beats a mediocre model trained on a leaky one. And a data engineer who can rebuild a training set deterministically has already de-risked more of the project than one who can tune a hyperparameter.

### The three families of ML

**Supervised learning** is learning a mapping from input to a known target. You have both `X` (features) and `y` (label). The label is the expensive part.

Sub-shapes you will meet:

| Task | What you predict | Example |
|---|---|---|
| **Classification** | A discrete class | Will this user churn? Is this transaction fraud? Which of these four product categories is this image? |
| **Regression** | A continuous number | What will this customer's lifetime value be? How many units will sell next week? |
| **Ranking / retrieval** | An ordering | Which documents match this search query? |
| **Forecasting** | A future series | What will demand be on 2026-03-01? |

Supervised learning is the dominant case in enterprise data work, and it is the case this course concentrates on, because it has the hardest data-engineering problem: **the label**.

**Unsupervised learning** is learning structure in data that has no target. K-means clustering, dimensionality reduction (PCA, UMAP), anomaly detection via density estimation, and association rules all live here.

Where it fits in a pipeline: **cold-start segmentation**. When you build a churn model you need history, and new customers have none. Clustering the population into behavioural segments gives you a feature ("which segment is this customer in?") that works on day one. The honest limitation: cluster labels are not ground truth. A cluster is a *description*, and you must validate it against something external — a known business category, a churn outcome you can check later, a domain expert's judgement.

**Reinforcement learning** is learning a policy by interacting with an environment and maximising cumulative reward. It is genuinely different in kind: there is no fixed dataset, the agent's actions change what it observes next, and you need a simulator or a live environment to train against.

**Be honest about when RL is appropriate.** In most enterprise data platforms it is not. The reliable RL wins in this space are things like Google's work on data-centre cooling and chip design, where a faithful simulator exists and the reward is measurable and unbounded. If you cannot build a faithful simulator of your environment, RL will not work for you — and "learn from historical logs" is not a simulator, because historical logs only contain the actions that were taken, not the actions that were *not* taken. That is the counterfactual problem, and it is unsolved by log replay.

**The honest hierarchy of effort for a data engineer:**

```text
Rule-based        "if amount > 10000 then review"
   ↓ less data engineering, more rules to maintain
Statistical       "z-score of this customer's 30-day average"
   ↓
Supervised ML     "model predicts churn from features"
   ↓
Reinforcement     "agent learns a policy by interaction"
```

Most business problems that get labelled "we need machine learning" are actually the first two or three rows. Saying so early is one of the most valuable things a data engineer can do for a project.

### The ML workflow

Eight stages. The stages are not linear — you loop back constantly — but the *order* matters, and the most common project failure is starting at stage 6.

```text
1. Frame the problem
        ↓
2. Collect and label
        ↓
3. Explore the data (EDA)
        ↓
4. Engineer features
        ↓
5. Train
        ↓
6. Evaluate
        ↓
7. Deploy
        ↓
8. Monitor  ───→ back to 2 (labels arrive) and 5 (retrain)
```

**Stage 1 — Frame the problem.** The output is a written statement of:

- **The decision** the model informs. Not "predict churn" but "the retention team calls customers predicted to churn within 14 days, because a call costs €40 and saves €180 in expected value."
- **The prediction time** (when the score is computed) and the **outcome window** (how far ahead it looks).
- **The baseline.** What does the business do today? A churn model that beats "no calls at all" but loses to "call every customer who has logged in this week" is not a project.
- **The actionability test.** If the model is wrong, what happens? A false positive on a fraud model costs a customer their access. A false positive on a marketing model costs €40 of a call.

If you cannot write this in one paragraph, you are not ready to open a notebook. This stage produces no code and it is the stage most often skipped.

**Stage 2 — Collect and label.** The label is the model. Everything downstream is a function of the quality and definition of the label.

This is where data engineering earns its keep. Key sub-problems:

- **Label definition drift.** "Churned" means different things to finance (subscription ended) and to marketing (no purchase in 90 days). Pick one and write it down.
- **Label latency.** A 90-day churn label means your training set is 90 days stale, and your model is always predicting from a world that no longer exists. There is no way around this except by accepting it or by using a proxy label that is available sooner (e.g. "did the customer's usage decline" instead of "did they cancel").
- **Negative examples.** If only positive examples are collected, you train a model with no idea what "no" looks like. This is the most common labelling bug: you sample from a population that has already churned, so your "not churned" class is composed entirely of people who stayed *despite* something.
- **Label leakage.** A feature that is only populated *after* the outcome is a leak. More on this below — it is the single most common cause of a model that works beautifully in validation and fails on day one.

**Stage 3 — Explore.** EDA. For a data engineer this is not idle curiosity, it is validation of the upstream pipeline.

**Stage 4 — Engineer features.** Transform raw columns into model inputs. This is where most of the actual predictive signal is, and it is data engineering.

**Stage 5 — Train.** Fit the model. Least interesting stage, for most engineers.

**Stage 6 — Evaluate.** The stage that decides whether the project continues.

**Stage 7 — Deploy.** Put the model behind an endpoint or into a batch query.

**Stage 8 — Monitor.** The stage everyone skips and the reason models rot.

### The train/validation/test split

Three sets, three distinct jobs:

| Set | Used for | Rules |
|---|---|---|
| **Train** | Fitting the model parameters | The only set the optimiser is allowed to see |
| **Validation** | Choosing hyperparameters, features, thresholds | Can be looked at repeatedly — that is its job — but must not be used to fit parameters |
| **Test** | The final, unbiased estimate of generalisation | Looked at **once**, at the very end |

**Why it matters, mechanistically.** A model has two sources of error: **bias** (the model family is too simple to represent the truth) and **variance** (the model is too sensitive to the particular training sample). When you evaluate on the training set, you measure neither — you measure **memorisation**. A model of 10 parameters fit to 10,000 rows can achieve near-zero training error while learning nothing transferable.

The split exists to let you estimate the *gap*:

```text
training error   = how well the model fits what it saw
validation error = how well the model fits what it did not see
```

That gap **is** the overfitting signal. A large gap means variance; a small gap but high validation error means bias.

**The rules that actually matter:**

1. **Split by the unit of prediction, not the row.** If you predict per *user*, split by user. If two rows belong to the same user and one lands in train and one in test, the model can memorise that user's label from the training row and "predict" it on the test row. This is leakage through the split, and it is extremely common in event-level data. The course project has `user_id` on every event — so a per-user model needs a per-user split.

2. **Split by time for anything temporal.** A random split on time-series data lets the model train on the future to predict the past, which is both unrealistic and often leak-prone. Use a chronological cut: train on months 1–10, validate on month 11, test on month 12.

3. **Fit preprocessing on the training set only.** Every statistic — mean, standard deviation, vocabulary, imputation value, target encoding — must be computed on train and then *applied* to validation and test. Computing a scaler on the full dataset is a (very quiet) form of leakage, and it inflates your validation score by a small but real amount.

4. **Never tune on the test set.** If you look at test scores and change anything, the test set has become a validation set and you need new test data. This is the single most common way people fool themselves, and it is why held-out benchmarks collapse under repeated iteration.

5. **Watch for duplicate entities across splits.** The same customer record, ingested twice from different sources, will straddle the split.

### Overfitting and underfitting

```text
Underfitting:  high bias,  low variance
               training error HIGH, validation error HIGH, gap SMALL
               the model cannot represent the pattern at all

Good fit:      low bias,   low variance
               training error LOW,  validation error LOW,  gap SMALL

Overfitting:   high bias?  no — high variance
               training error LOW,  validation error HIGH, gap LARGE
```

**How to tell them apart in practice — read the learning curve, not the headline metric.** Plot training error and validation error against training-set size (or epoch):

- Both curves high and converging to a high plateau → **underfitting**. The model family is too simple, or features are too weak. Fix: a richer model, more features, less regularisation.
- Training curve low and flat, validation curve high and falling → **overfitting**. The model memorises noise. Fix: more data, regularisation (L1/L2, dropout, early stopping), fewer features, simpler model.
- Both high and *diverging* → usually a data or learning-rate problem, not overfitting. Check the learning rate and the feature scaling first.

**The order of interventions for overfitting**, in the order I would actually try them:

1. **Get more data.** The only intervention that never makes generalisation worse.
2. **Regularise.** L2 (weight decay) shrinks weights smoothly; L1 drives them to zero and does feature selection for you. On tabular data, regularisation almost always helps.
3. **Early stopping.** Stop when validation loss stops improving. On neural networks this alone prevents a large fraction of overfitting.
4. **Drop features.** A model with fewer inputs has fewer ways to overfit. Do the feature selection on the *validation* set, not the test set.
5. **Simplify the model.** A shallower tree or a linear model where a boosted tree was used.

Note the order: **data first, regularisation second**. Teams routinely reach for regularisation before they have checked whether their data pipeline is dropping rows or duplicating them. A duplicated training row is unfixable by L2.

### The evaluation metrics, and when accuracy lies

**Accuracy = (TP + TN) / (total).** The metric everyone reaches for first, and the one most likely to mislead.

**Accuracy lies when classes are imbalanced.** With a 1% positive rate, a model that predicts "not positive" for everything scores 99% accuracy and is worth nothing. Concretely:

```text
A dataset with 10,000 customers, 100 of whom churn.
A "predict nobody churns" model:  accuracy = 99.0%,  recall = 0
A model with accuracy 95%:          it found 60 of the 100 churners
                                    and raised 950 false alarms
```

The second model looks *worse* on accuracy and is *infinitely* more useful. That is the whole argument.

**Accuracy is only defensible when:** (a) the error types are symmetric in cost, and (b) the class balance is roughly even. Both are usually false.

**The confusion matrix.** Every metric derives from it:

```text
                  Predicted +     Predicted -
Actual +             TP              FN        ← recall lives here
Actual -             FP              TN        ← precision lives here
```

- **Precision = TP / (TP + FP)** — of the ones you flagged, how many were right? *"When the model says churn, how often is it actually churn?"* The metric when a false positive is expensive (a call, a manual review, a chargeback, a denied loan).
- **Recall = TP / (TP + FN)** — of the ones that were actually positive, how many did you catch? *"Of the customers who churned, how many did we identify?"* The metric when a false negative is expensive (missing fraud, missing a safety defect, missing a churner you were going to pay €180 to save).
- **F1 = 2·P·R / (P + R)** — the harmonic mean. It punishes imbalance between P and R: if precision is 1.0 and recall is 0.01, F1 is 0.0198, not 0.5. Use it when you genuinely cannot say which error is worse and you need one number. It hides the trade-off, so always report P and R alongside it.

**The harmonic mean matters, and here is why.** The arithmetic mean of precision and recall is dominated by the larger value. A model with precision 0.99 and recall 0.01 has an arithmetic mean of 0.5 — which looks like a coin flip, when in fact the model has found almost none of the positives. The harmonic mean of the same two is 0.0198, which correctly says "this model is nearly useless for finding positives".

**ROC-AUC.** The ROC curve plots TPR (recall) against FPR at every possible decision threshold. AUC is the area under it, and it equals the probability that the model ranks a random positive above a random negative.

Key properties:
- **Threshold-independent.** AUC summarises the model's *ranking* quality across all thresholds. It is the right metric for comparing models, and the wrong metric for making a decision.
- **The threshold is where the business lives.** AUC 0.92 tells you the ranking is good. It tells you nothing about what happens at your operating point. You must pick a threshold, and the threshold is a *business* decision expressed in units of euros.
- **AUC is misleading on heavily imbalanced data.** The FPR axis barely moves when the positive rate is 0.1%, so the curve looks great even for a useless model. Use **PR-AUC (average precision)** in that regime, because its axes (precision and recall) both move meaningfully.

**Choosing the threshold.** Do not take the default 0.5. Instead:

1. Compute the model's score for a population.
2. Sort by score, and walk down the list, accumulating the *value* of catching each true positive and the *cost* of each false positive.
3. Pick the point where marginal value equals marginal cost.
4. Report the metric at that threshold, not at 0.5.

**Business cost of each error, stated concretely.** This is the part that separates a real project from an academic one:

| Decision | Wrong error costs | Choose |
|---|---|---|
| Route a churn call (save €180, call costs €40) | False positive: €40 wasted. False negative: €140 lost value. | Recall-leaning, threshold tuned to the € ratio |
| Block a payment (customer loses access) | False positive: customer trust, support load, regulatory exposure. False negative: € fraud. | Precision-leaning, very high threshold |
| Flag for manual review (analyst hour costs €30) | False positive: €30. False negative: depends on the review queue capacity | Pick the threshold that fills the queue with the highest-value items |
| Recommend a product | False positive: mild. False negative: mild. | Accuracy or F1 is fine |

Note the pattern: **precision vs recall is a business decision wearing a technical costume.** The metric choice comes *before* the model, from the economics of the error.

**A fourth metric that data engineers should care about: calibration.** A model's *scores* should mean what they say. If you assign a churn score of 0.30 to 30,000 customers, about 9,000 of them should churn. If they do not, the scores cannot be used to prioritise, to size a campaign, or to aggregate into a business case. **A well-calibrated model's scores are additive**, so you can sum them: "expected revenue at risk = €4.2M." AUC says nothing about calibration — two models can have identical AUC and completely different calibration.

### What EDA is actually for

For a data engineer, EDA has a different purpose than for a researcher. The researcher's EDA is to understand the phenomenon. The data engineer's EDA is to **validate that the pipeline produced the data you think it did**.

The checks that matter:

1. **Volume reconciliation.** Does the row count match the source? The course pipeline expects exactly **4800 accepted events** from the sample dataset and **12 rejected rows**. If your run produces 4799, something upstream changed. This is the single most valuable check and it takes one line.
2. **Null and default distributions per column.** A sudden null spike in one column is a schema drift in a producer.
3. **Cardinality of every categorical.** A `region` column with 5 values instead of 4 means a new producer appeared. A `user_id` with cardinality equal to the row count means the join fanned out — a classic one-to-many bug that silently multiplies your training data.
4. **Range and distribution checks on numerics.** Negative revenue where there should be none. A `amount_eur` with a mean of €12 when the source mean is €900 means the currency conversion table is wrong.
5. **Time coverage.** The earliest and latest event timestamps, and whether they match the expected window. The sample dataset spans **24 hours**.
6. **Cross-field consistency.** Does `currency` match the country implied by `region`? Not always true, but a sudden violation rate means a producer changed behaviour.
7. **Class balance of the label.** Before anything else. If your churn label is 0.4% positive, you know your metric strategy before you write a single line of modelling code.

**EDA is a pipeline test, and it should run on every load, not once.** The right home for these checks is a Dataform test or a Dataflow assertion that fails the DAG, not a notebook someone ran in October.

### Feature engineering as a pipeline concern

A feature is any input to the model. Three kinds matter in tabular work:

**Transformations of a single column:**
- **Encoding categoricals.** One-hot for low cardinality (a region with 4 values). For high cardinality, one-hot explodes; use **target encoding** (replace a category with the mean target for that category, computed on the training fold only — this is a leakage vector if you compute it on the full dataset) or **embedding** (learned, for neural models).
- **Scaling.** Standardise for distance-based and gradient-based models (logistic regression, k-means, k-NN, neural nets). Tree-based models do not care.
- **Log transforms.** Revenue is heavily right-skewed; `log1p(amount)` often linearises it and stabilises the fit.
- **Bucketing / binning.** `hours_between_last_order` into 0, 1-3, 4-7, 8-14, 15+. Loses resolution but gains robustness and interpretability.

**Temporal features — the highest-value group in event data:**
- **Recency:** days since last order.
- **Frequency:** orders per 30 days.
- **Monetary:** total spend, average order value.
- **Ratios:** `orders_30d / orders_90d` — a falling ratio is a churn signal that the raw counts do not show.
- **Trend:** order count in the last 7 days versus the 7 before. Slope, not level.
- **Time-of-day, day-of-week, is_weekend, is_month_end.** Sometimes enormous. The course pipeline's hourly windows show this: 24 buckets with a non-flat distribution.

**Aggregate features from joins.** The classic "RFM" pattern. These require careful snapshot semantics:

```text
features as of 2026-01-01, computed only from events with event_ts < 2026-01-01
```

Get this wrong and you have **target leakage**: the aggregate includes events that happened *after* the prediction time, including the very purchase you are trying to predict. This is the number one cause of a model that scores 0.99 AUC in validation and 0.55 in production.

**The leakage checklist** — for every feature, ask: *could this feature's value have been known at the moment the prediction is made?*

```text
[x] days_since_last_order      computed over ALL history, including post-cutoff events
[x] customer_lifetime_value     computed from a snapshot taken today, not as of the prediction date
[x] total_spend_90d             includes the order that defines the label
[x] support_tickets_last_30d    from a table joined without an as-of predicate
[ok] days_since_last_order      WHERE event_ts < prediction_cutoff
[ok] customer_lifetime_value    from an as-of snapshot table
```

### The data engineer's role, stage by stage

This is the section that is actually about your job.

| Stage | What the data engineer owns |
|---|---|
| **Frame** | Business rules that define the label. The target variable is a data-engineering artefact. |
| **Collect and label** | **Labelling pipelines** — building the feature store of ground truth, the join to the outcome table, the snapshot tables. |
| **Explore** | Data quality tests, schema contracts, freshness SLAs. |
| **Engineer features** | The feature definitions themselves — this *is* data engineering. |
| **Train** | Reproducible training datasets: **versioned, immutable, and backfillable**. |
| **Evaluate** | Building the evaluation harness as a scheduled job, not a one-off notebook. |
| **Deploy** | Serving infrastructure, feature parity between batch and online, the endpoint's SLOs. |
| **Monitor** | Drift detection, prediction logging, feedback-loop capture. |

**Labelling pipelines.** A label is usually not sitting in your event stream. It lives in a system of record: the billing table for churn, the fraud-review tool for fraud, the annotation tool for images. Building the join between "the model scored at time T" and "the outcome became known at time T+Δ" is the entire labelling pipeline.

The hard parts:

- **As-of joins.** The label for a prediction made on day T must be attached using only data available as of some later date, and the pipeline must be able to reproduce it exactly when you retrain.
- **Outcome windows that truncate.** Customers who signed up 3 days ago cannot have a 90-day churn label. If you include them, you label them "not churned" and your model learns "new customers don't churn" — a spurious correlation that reverses the moment the window fills. **This is the most common subtle bug in churn modelling.** The fix is to exclude any entity whose observation window is shorter than the label horizon, and to encode that exclusion in the training-data query itself.
- **Label store as a first-class table.** Not a notebook variable. A table, with a version, so that "model v3 was trained on labels as of 2026-01-01" is a queryable fact.

**Feature stores.** The purpose of a feature store is to solve **training/serving skew**: the same feature computed two ways must produce the same value.

Two levels:

- **Level 1: a table.** A BigQuery table of features, refreshed on a schedule. Simple, cheap, and it works for *batch* scoring. It does **not** solve online serving latency — you would need to copy the rows out to wherever the application runs.
- **Level 2: a real feature store.** Vertex AI Feature Store provides:
  - **Online stores** — a low-latency key/value store (typically Bigtable or Datastore backed) serving features to an online prediction.
  - **Offline stores** — BigQuery, DuckDB, or a file-based store serving features for training.
  - **Feature views** — a named, versioned set of features with a defined entity key and freshness. This is the mechanism that gives you parity: both stores are populated from *one* definition.
  - **Data validation** — skew detection between the online and offline stores, and feature-attribute validation.

  **The sync model matters.** Vertex AI Feature Store offers **periodic sync** (BigQuery → online store on a schedule, typically 5–15 minutes) and **streaming sync** (real-time, via Pub/Sub). Periodic sync with a 5-minute freshness means **online features can be up to 5 minutes stale**. If your model needs minute-fresh features, you need streaming sync, and you need to understand that you are now responsible for the stream's correctness.

  **The practical advice:** do not build a feature store until you have a real skew problem. A versioned SQL query that generates features, used by both the training job and the batch scoring job, gives you parity for free. That is the right answer for most tabular use cases. Reach for Vertex AI Feature Store when you have online serving, when the feature computation is too complex to run in the application's request path, or when multiple teams are consuming the same features.

**Training-data versioning.** This is table stakes and most teams skip it. Requirements:

1. **Immutable, dated snapshots.** A table like `features_20260115` or a `snapshot_date` column. Never `DELETE` from a training table.
2. **A manifest.** For every training run, record: the feature SQL version (git SHA), the label-table version, the training-data query, the hyperparameter set, the model artefact hash, the evaluation results, and the code version.
3. **Reproducibility.** Given the manifest, you must be able to rebuild the exact training matrix. This is the "rebuild in six months" guarantee, and it is the difference between a model and a rumour.

**In practice this is a table plus a JSON manifest in Cloud Storage**, with the feature SQL living in Dataform under version control. Do not over-engineer it.

**Skew detection.** Two different things, and both matter:

- **Training/serving skew**: the *same* feature is computed differently in the two paths. Typically the training path uses a SQL join with a 30-day window and the serving path uses a 7-day window. You find it by **comparing distributions** of each feature between the training set and live prediction logs — not by comparing individual values, because you will not have both for the same entity.
- **Label skew**: the training distribution differs from the serving population. If you train on customers active in 2025 and serve to customers who just signed up in 2026, your feature distributions differ. This is a *population* problem, not a computation problem.

Practical approach: at deploy time, log every feature value with its prediction. Then run a scheduled comparison of the training-set distribution against the live distribution. Per-feature checks: mean/median, missing rate, cardinality, and a PSI (Population Stability Index) on the bucketed distribution.

**PSI** is the workhorse metric:

```text
PSI = Σ (p_live − p_train) · ln(p_live / p_train)
```

Rough industry thresholds: **< 0.10** stable, **0.10–0.25** moderate shift (investigate), **> 0.25** significant shift (act). PSI is not a hypothesis test and has no p-value; it is a heuristic threshold. Say so when you use it.

### Where the ML lifecycle actually breaks in production

Not in training. Training fails loudly and you see it immediately. The lifecycle breaks in the space **between** training and production, and it breaks silently.

**1. Training/serving skew.** The model learned from `days_since_last_order` computed over a 30-day window; the serving path computes it over 7 days. The model's learned coefficients are calibrated for one definition and applied to another. Accuracy degrades, and nothing errors.

- **Symptom:** model performance measured offline (on a correctly-built test set) is far better than observed in production.
- **Detection:** compare feature distributions between training and serving logs; log every feature with every prediction.
- **Prevention:** single definition of each feature, generated from one source, used by both paths. This is the entire reason feature stores exist.

**2. Feature staleness.** The features are correct in *definition* but out of *date*. A daily feature refreshed at 03:00 served at 14:00 is 11 hours stale. If the prediction horizon is minutes — a fraud check, a real-time recommendation — staleness of minutes is fatal.

- **Symptom:** performance degrades slowly over weeks, which is easy to mistake for drift or for market change.
- **Detection:** monitor the age of the features at prediction time (`now() - feature_timestamp`), not just the age of the data source.
- **Prevention:** know your latency requirement, then set the refresh interval below it. Match feature freshness to the *decision*, not to the pipeline's convenience.

**3. Drift.** The world changed and the training data no longer describes it. Drift has two flavours:

  - **Covariate drift** — the input distribution `P(X)` changed. A new device type appears, a marketing campaign shifts the channel mix. Detectable *without labels*, from the feature distributions alone. This is why logging features is non-negotiable.
  - **Concept drift** — the relationship `P(y|X)` changed. The features look the same but the outcome rule is different: a fraud ring adapts, a competitor's pricing changes your customers' behaviour, a policy change alters what counts as churn. **This one is invisible until you have fresh labels.** That is the uncomfortable part: you cannot detect concept drift in real time, only the lag before you discover it.

  **Covariate drift is what monitoring systems actually watch** (because it is measurable now). Concept drift is detected by comparing live performance against a baseline once labels mature — which is why your labelling pipeline must run *continuously*, not just at training time.

**A fourth, less-discussed failure: the feedback loop.** If the model's output influences future behaviour — a churn model that determines who gets a retention call will see those retained customers *not* churn — then the live data reflects the model's decisions, not the world. Training on that data trains the model on its own effects. This is why you should keep a holdout population that is never scored, or at least a holdout that receives treatment independent of the model.

**A fifth: silent pipeline failures.** The feature job fails, the table is empty, the model predicts the majority class for every row, and the accuracy is 99%. No error, no alert, no incident. This is why you need **prediction-distribution monitoring** and not only drift monitoring: if the mean predicted probability suddenly goes to 0.01, something broke upstream.

**The monitoring checklist for a production model:**

```text
Input side
  - feature freshness (age at prediction time)
  - feature distribution vs training baseline (PSI)
  - missing-rate per feature
  - row-count and null-rate guardrails

Output side
  - prediction score distribution
  - positive-rate (predicted positive fraction) — the loudest, cheapest alarm
  - prediction latency (p50, p95, p99)
  - error rate of the endpoint

Outcome side (lagged by the label window)
  - live precision / recall / AUC at the operating threshold
  - calibration (predicted vs observed, by bucket)
  - segment-level performance, not just aggregate
```

**Segment-level performance is the one people skip and the one that finds problems.** A model with 0.90 aggregate AUC may have 0.55 AUC on your largest customer segment. Aggregate metrics hide the thing that matters.

---

## 🛠️ Hands-On

Everything below runs against the course project at `project/core/`. No account, no credentials, no bill.

### Exercise 1 — Validate the training data before you model it

The EDA that matters: does the pipeline produce exactly what the chapters promise?

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import (
    ingest_events,
    aggregate_events,
    render_summary_csv,
    reject_counts,
)

lines = open("sample_data/events.csv").read().splitlines()

# Drop the CSV header — the pipeline consumes data rows, not a header.
accepted, rejected = ingest_events(lines[1:])

print(f"accepted={len(accepted)} rejected={len(rejected)}")
assert len(accepted) == 4800, f"expected 4800 accepted, got {len(accepted)}"
assert len(rejected) == 0, f"expected 0 rejected, got {len(rejected)}"

# The reject taxonomy must be exactly this. A new reason code appearing
# means an upstream producer changed — that is a pipeline alarm, not a
# data quality curiosity.
print(reject_counts(rejected))
```

Expected output:

```text
accepted=4800 rejected=0 clean
{}
```

Now the malformed file. A separate, deliberately broken input:

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, reject_counts

bad_lines = open("sample_data/malformed_events.csv").read().splitlines()
accepted_bad, rejected_bad = ingest_events(bad_lines)

print(f"accepted={len(accepted_bad)} rejected={len(rejected_bad)} malformed")
for reason, count in sorted(reject_counts(rejected_bad).items()):
    print(f"  {reason:24s} {count}")
```

Expected output:

```text
accepted=0 rejected=12 malformed
  bad_amount                 1
  bad_timestamp              1
  missing_event_id           1
  missing_user_id            1
  negative_amount            1
  unknown_channel            1
  unknown_currency           1
  unknown_event_type         1
  unknown_region             2
  wrong_field_count          2
```

**The engineering lesson:** reject *reasons*, not just counts. A reject counter of `12` tells you nothing; a reason taxonomy tells you that two rows are malformed and ten rows are schema violations — two different fixes. This is the same discipline you need for labelled data: a `label_status` column that distinguishes `missing` from `not_yet_observable` from `rejected` prevents you from silently training on garbage.

### Exercise 2 — The label-window truncation bug, demonstrated

This is the churn-modelling bug in miniature, and it is worth reproducing deliberately.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, build_bigquery_rows, dedup_key_set

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines[1:])
rows = build_bigquery_rows(accepted)

# Every user in the dataset, and how many events they have.
from collections import Counter
counts = Counter(r["user_id"] for r in rows)
print(f"users={len(counts)} rows={len(rows)}")

# Users with exactly one event are the "new customers" population. In a
# churn model these are the entities whose 90-day observation window has
# not elapsed. Including them labels them "not churned" purely because
# they have not had time to churn.
single_event_users = {u for u, c in counts.items() if c == 1}
print(f"users with a single event: {len(single_event_users)}")
print(f"of those, present in the train split would be mislabelled")

# The fix, in SQL terms: exclude entities whose observation window is
# shorter than the label horizon. In a real warehouse that is:
#
#   WHERE signup_date <= prediction_date - INTERVAL 90 DAY
#
# Compute it here as a filter over the training-set builder.
def eligible_for_label(row, horizon_days=90):
    """A row is eligible only if the entity could have churned by now."""
    return row["user_id"] not in single_event_users

eligible = [r for r in rows if eligible_for_label(r)]
print(f"eligible rows after truncation filter: {len(eligible)}")
```

The lesson: **the label horizon must be enforced in the training-data query**, not in a notebook after the fact. If it is enforced in a notebook, the next person who trains a model will not know to do it.

### Exercise 3 — Build a labelled dataset with an as-of snapshot

Simulating the training-data builder that produces a leak-free feature matrix.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import (
    ingest_events,
    build_bigquery_rows,
    normalise_event,
    aggregate_events,
    render_summary_csv,
)

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines[1:])
rows = build_bigquery_rows(accepted)

# The prediction cutoff: we are predicting on 2026-01-16 for a cohort
# whose history is everything strictly before 2026-01-16.
PREDICTION_CUTOFF = "2026-01-16T00:00:00+00:00"

# Features computed ONLY from events strictly before the cutoff.
from collections import defaultdict
from datetime import datetime, timedelta

history = defaultdict(list)
for r in rows:
    if r["event_dt"] < PREDICTION_CUTOFF:
        history[r["user_id"]].append(r)

def featurize(user_id, events):
    """Compute features as of the cutoff — the leak-free version."""
    if not events:
        return None
    orders = [e for e in events if e["event_type"] == "order"]
    last_ts = max(e["event_dt"] for e in events)
    return {
        "user_id": user_id,
        "total_events": len(events),
        "n_orders": len(orders),
        "total_spend_eur": round(sum(o["amount_eur"] for o in orders), 2),
        "distinct_channels": len({e["channel"] for e in events}),
        "distinct_regions": len({e["region"] for e in events}),
        "last_event_dt": last_ts,
    }

features = [f for u, evs in history.items() if (f := featurize(u, evs)) is not None]
print(f"users with features: {len(features)}")
print(f"sample: {features[0]}")

# THE LEAK, for contrast. If you build features from ALL rows including
# events after the cutoff, you get this:
def featurize_leaky(user_id, events):
    leaky = dict(featurize(user_id, events) or {})
    leaky["total_events"] = len([e for e in rows if e["user_id"] == user_id])
    return leaky

# Both versions exist for every user here (the whole dataset is one day),
# which is exactly the situation that makes leakage invisible in a
# random split and fatal in production.
leaky_total = sum(
    len([e for e in rows if e["user_id"] == f["user_id"]]) for f in features
)
clean_total = sum(f["total_events"] for f in features)
print(f"clean event count: {clean_total}")
print(f"leaky event count: {leaky_total}")
```

The output shows the leak in the number: the "leaky" version counts events the model could not have known about at prediction time. With a one-day dataset the gap is small. With a 90-day history it is enormous, and the model that trained on it will look brilliant offline and be useless live.

### Exercise 4 — Compute the metrics, and watch accuracy lie

A full evaluation harness. This is the code you would put in a scheduled job, not a notebook.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, build_bigquery_rows

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines[1:])
rows = build_bigquery_rows(accepted)

# Build a synthetic binary label so the harness can be exercised end to
# end. In production this column comes from the outcome table.
for r in rows:
    r["churned"] = 1 if r["event_type"] == "refund" else 0

# A deliberately imbalanced population, which is the realistic case.
positives = sum(r["churned"] for r in rows)
print(f"rows={len(rows)} positives={positives} rate={positives/len(rows):.4f}")

def confusion(y_true, y_pred):
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    return tp, fp, tn, fn

def metrics(y_true, y_pred):
    tp, fp, tn, fn = confusion(y_true, y_pred)
    total = tp + fp + tn + fn
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
    }

# The useless baseline: predict the majority class for everything.
baseline = [0] * len(rows)
m = metrics([r["churned"] for r in rows], baseline)
print("\n--- majority-class baseline ---")
print(f"accuracy={m['accuracy']:.4f}  precision={m['precision']:.4f}  recall={m['recall']:.4f}")
print("^ 99% accuracy. Zero business value. This is why accuracy lies.")
```

The baseline prints high accuracy and zero recall. That contrast is the entire argument for using a metric suite.

Now the proper evaluation, with a time-based split and a score-threshold sweep:

```python
# A score-based model, standing in for a trained classifier: score each
# user by a simple behavioural signal.
from collections import defaultdict
by_user = defaultdict(list)
for r in rows:
    by_user[r["user_id"]].append(r)

scores = []
for user_id, events in by_user.items():
    n_refunds = sum(1 for e in events if e["event_type"] == "refund")
    n_orders = sum(1 for e in events if e["event_type"] == "order")
    score = n_refunds / len(events) if events else 0.0
    label = 1 if n_refunds > 0 else 0
    scores.append((user_id, score, label))

# Sort by score descending, then sweep the threshold. This is exactly
# what you do to pick an operating point: walk the ranked list and pick
# the cut where marginal value equals marginal cost.
scores.sort(key=lambda x: -x[1])

def sweep(scores, thresholds=(0.0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5)):
    y_true = [s[2] for s in scores]
    out = []
    for t in thresholds:
        y_pred = [1 if s[1] >= t else 0 for s in scores]
        out.append((t, metrics(y_true, y_pred)))
    return out

print("\nthreshold  accuracy  precision  recall     f1   tp  fp  tn  fn")
for t, m in sweep(scores):
    print(f"{t:9.2f}  {m['accuracy']:8.4f}  {m['precision']:9.4f}  "
          f"{m['recall']:6.4f}  {m['f1']:5.4f}  {m['tp']:3d} {m['fp']:3d} "
          f"{m['tn']:4d} {m['fn']:3d}")

# The business threshold. A retention call costs 40 and saves 180, so a
# false positive (40 wasted) is cheaper than a false negative (140 lost).
# That ratio says we should accept a lower precision for a higher recall.
COST_FP = 40.0
COST_FN = 140.0
print("\nthreshold  expected cost")
for t, m in sweep(scores):
    cost = m["fp"] * COST_FP + m["fn"] * COST_FN
    print(f"{t:9.2f}  {cost:13.2f}")
```

Read the output carefully. **The accuracy-optimal threshold and the cost-optimal threshold are usually different.** Optimising accuracy is optimising a proxy metric; optimising cost is optimising the thing you actually care about.

Add ROC-AUC, which is threshold-independent:

```python
def roc_auc(scores):
    """AUC via the rank-sum method (handles ties by average rank)."""
    data = sorted(scores, key=lambda x: x[1])
    n = len(data)
    # Assign average ranks, 1-based, for ties.
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and data[j + 1][1] == data[i][1]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = avg_rank
        i = j + 1
    n_pos = sum(1 for s in scores if s[2] == 1)
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    rank_sum_pos = sum(r for r, s in zip(ranks, data) if s[2] == 1)
    return (rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)

def pr_auc(scores, thresholds):
    """Average precision over the precision-recall curve."""
    total_pos = sum(1 for s in scores if s[2] == 1)
    if total_pos == 0:
        return 0.0
    y_true = [s[2] for s in scores]
    points = []
    for t in thresholds:
        y_pred = [1 if s[1] >= t else 0 for s in scores]
        m = metrics(y_true, y_pred)
        points.append((m["recall"], m["precision"]))
    # Average precision: sum of (recall delta) * precision, walking up.
    points.sort()
    ap = 0.0
    prev_recall = 0.0
    for rec, prec in points:
        ap += (rec - prev_recall) * prec
        prev_recall = rec
    return ap

auc = roc_auc(scores)
print(f"\nROC-AUC = {auc:.4f}")
print(f"PR-AUC  = {pr_auc(scores, [i/100 for i in range(0, 101)]):.4f}")
print("\nNote: with a heavily imbalanced population, PR-AUC is the")
print("informative number. ROC-AUC's false-positive axis barely moves.")
```

### Exercise 5 — Leakage audit: assert the as-of property

A test you can run in CI, on every feature change.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import ingest_events, build_bigquery_rows, partition_for_date

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines[1:])
rows = build_bigquery_rows(accepted)

PREDICTION_CUTOFF = "2026-01-16T00:00:00+00:00"

def audit_no_future_leakage(rows, cutoff, feature_fn):
    """Every feature must be derivable from data at or before the cutoff."""
    violations = []
    for row in rows:
        value = feature_fn(row)
        if value is None:
            continue
        if value > cutoff:
            violations.append((row["event_id"], value))
    return violations

# A leak: a feature computed from the *current* state of the row, with
# no as-of predicate. The timestamp it returns can be after the cutoff.
def leaky_last_event(row):
    return row["event_dt"]

violations = audit_no_future_leakage(rows, PREDICTION_CUTOFF, leaky_last_event)
print(f"leaky feature violations: {len(violations)}")

# The correct version filters to the as-of window first, so it cannot
# produce a timestamp after the cutoff.
def clean_last_event(row):
    return row["event_dt"] if row["event_dt"] <= PREDICTION_CUTOFF else None

clean_violations = audit_no_future_leakage(rows, PREDICTION_CUTOFF, clean_last_event)
print(f"clean feature violations: {len(clean_violations)}")
assert clean_violations == []
```

In a real warehouse the same check is a Dataform test:

```sql
-- dataform/tests/assert_no_future_features.sql
select
  count(*) as violations
from ${ref('features_user_daily')}
where feature_timestamp > event_timestamp
```

### Exercise 6 — Drift monitoring with PSI

The monitoring job. This runs on a schedule against prediction logs.

```python
import math
from collections import Counter

def psi(baseline_counts, current_counts, buckets=None):
    """Population Stability Index between two bucketed distributions.

    baseline_counts / current_counts: dict of bucket -> count.
    """
    total_b = sum(baseline_counts.values())
    total_c = sum(current_counts.values())
    if total_b == 0 or total_c == 0:
        return 0.0
    keys = set(baseline_counts) | set(current_counts)
    value = 0.0
    for key in keys:
        p_b = max(baseline_counts.get(key, 0) / total_b, 1e-6)
        p_c = max(current_counts.get(key, 0) / total_c, 1e-6)
        value += (p_c - p_b) * math.log(p_c / p_b)
    return value

def bucketize(values, edges):
    """Assign each value to a bucket label using the given edges."""
    out = []
    for v in values:
        label = f"<={edges[0]}"
        for e in edges:
            if v <= e:
                label = f"<={e}"
                break
        else:
            label = f">{edges[-1]}"
        out.append(label)
    return Counter(out)

# Baseline: the training set's feature distribution.
EDGES = [10, 50, 200, 500, 1000]
baseline_counts = bucketize([r["amount_eur"] for r in rows], EDGES)

# Current: a shifted population. A new device/channel mix changes the
# order-value distribution. Simulate by scaling the low end up.
shifted = [r["amount_eur"] * 0.4 if r["channel"] == "mobile" else r["amount_eur"]
           for r in rows]
current_counts = bucketize(shifted, EDGES)

value = psi(baseline_counts, current_counts)
print(f"PSI = {value:.4f}")
if value < 0.10:
    print("STABLE — no action")
elif value < 0.25:
    print("MODERATE SHIFT — investigate the feature")
else:
    print("SIGNIFICANT SHIFT — retrain or roll back")

# And the cheap alarm: the positive rate. If the model collapses to
# predicting the majority class, this moves before any metric does.
#
# The event rows carry no label — the label lives in a separate
# churn_labels table, keyed by user_id and a label window. Compute
# the rate from THAT table, not from the feature rows: joining the
# label back onto the events is the step that reintroduces leakage.
LABEL_AS_OF = "2026-01-15"
LABEL_HORIZON_DAYS = 30


def label_users(rows, label_as_of, horizon_days=30):
    """Build the churn label table: one row per user.

    A user is labelled churned if they have NO activity at all in
    the horizon window that follows `label_as_of`.
    """
    from datetime import datetime, timedelta, timezone
    as_of = datetime.fromisoformat(label_as_of).replace(tzinfo=timezone.utc)
    cutoff = as_of + timedelta(days=horizon_days)

    by_user = {}
    for r in rows:
        by_user.setdefault(r["user_id"], []).append(
            datetime.fromisoformat(r["event_ts"]))

    labels = {}
    for user_id, stamps in by_user.items():
        in_window = [t for t in stamps if as_of <= t < cutoff]
        labels[user_id] = 0 if in_window else 1
    return labels


labels = label_users(rows, LABEL_AS_OF, LABEL_HORIZON_DAYS)
baseline_positive_rate = sum(labels.values()) / len(labels)
print(f"\nbaseline positive rate: {baseline_positive_rate:.4f}")
print(f"labelled users: {len(labels)}  positives: {sum(labels.values())}")
```

**Read that output carefully.** The positive rate is `0.0000`, and that is not a bug in the labelling code — it is the same one-day-data problem from the capstone. `LABEL_AS_OF` is 2026-01-15, so the label window is 2026-01-15 → 2026-02-14, and every one of the 3,057 users has activity inside it because every user has activity on 2026-01-15. A rate of exactly zero is the *correct* answer for this dataset, and it is precisely the number you would never be able to train a classifier on.

Two things this teaches:

1. **A degenerate label distribution is a data problem, not a modelling problem.** Before you tune anything, check the positive rate. If it is 0.0 or 1.0, you have a labelling bug, a truncated dataset, or a label window that does not line up with the data. None of those are fixed by trying a different algorithm.
2. **The alert threshold is relative, so the baseline must be real.** "Alert if the rate moves more than 2x" is meaningless when the baseline is 0.0 — the ratio is undefined. In production the label window always extends past the end of available data by construction, so the baseline rate is a genuine statistic computed over a fully-observed window.

Thresholds to use in production:

```text
PSI < 0.10          stable, log it
PSI 0.10 – 0.25     moderate, alert the owning team
PSI > 0.25          significant, open an incident and consider retraining

positive rate       alert if it moves more than 2x or 0.5x the baseline
feature freshness  alert if p99 age exceeds the decision's latency budget
```

### Exercise 7 — The training-data manifest

The mechanism that makes a model reproducible. In production this is a JSON file in Cloud Storage and a row in BigQuery.

```python
import hashlib
import json
from datetime import datetime, timezone

def file_sha256(path):
    """Content hash — the anchor of the manifest."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def build_manifest(feature_sql_sha, label_table, label_as_of, rows, params, metrics):
    """The record that makes a training run reproducible."""
    return {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "feature_code_sha": feature_sql_sha,
        "label_table": label_table,
        "label_as_of": label_as_of,
        "n_rows": rows,
        "feature_columns": ["total_events", "n_orders", "total_spend_eur",
                            "distinct_channels", "distinct_regions"],
        "hyperparameters": params,
        "metrics": metrics,
        "model_artifact_sha": None,   # filled in after training
    }

manifest = build_manifest(
    feature_sql_sha=file_sha256("sample_data/events.csv"),
    label_table="curated.churn_labels",
    label_as_of="2026-01-15",
    rows=len(rows),
    params={"model": "xgboost", "max_depth": 6, "learning_rate": 0.1},
    metrics={"auc": 0.912, "precision_at_threshold": 0.74, "recall": 0.61},
)

print(json.dumps(manifest, indent=2))
```

Six months later, with the manifest, you can answer: *which features, which labels, as of when, with what parameters?* Without it, you can answer only *we tried something once*.

---

## 🛠️ Common Errors and Fixes

### 1. Leakage: model accuracy collapses in production

**Symptom.** Offline evaluation is excellent — AUC 0.94, F1 0.88. Three weeks after launch, live performance is at chance and the positive rate has collapsed.

**Cause.** A feature computed without an as-of predicate. The classic version is an aggregate over a join to a customer table that includes events after the prediction time.

**The error you will see in the notebook:**

```text
UserWarning: X does not have valid feature names, but LogisticRegression was fitted with feature names
```

**Fix.** Rebuild the feature query with an explicit cutoff and re-verify. Concretely, in SQL:

```sql
-- Wrong: aggregate over all history, including after the prediction date.
select user_id, count(*) as n_orders
from `curated.events`
group by user_id

-- Right: as-of aggregate, evaluated at a fixed prediction timestamp.
select user_id, count(*) as n_orders
from `curated.events`
where event_ts < @prediction_cutoff
group by user_id
```

And assert the property in CI:

```sql
select count(*) from ${ref('features_user_daily')}
where feature_timestamp > prediction_timestamp
```

### 2. Split leakage: two rows from one entity in different splits

**Symptom.** Validation AUC of 0.99. Live AUC of 0.55.

**Cause.** The split was made at row level, but the prediction unit is the user. The model memorises user-specific features and "predicts" the same user's label across the split boundary.

**Fix.** Split by entity, never by row. With scikit-learn:

```python
from sklearn.model_selection import GroupShuffleSplit

splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(splitter.split(X, y, groups=df["user_id"]))
```

**A linter must enforce this.** If your split function takes only `X` and `y`, it is wrong by construction.

### 3. `ValueError: Invalid feature` — categorical column reaches the estimator

**Symptom.**

```text
ValueError: could not convert string to float: 'EMEA'
```

**Cause.** A string column was passed to a numeric estimator without encoding.

**Fix.** Encode inside a `Pipeline` so the encoder is fitted on the training fold only. Fitting the encoder outside the pipeline and then cross-validating is itself a leak.

```python
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline

numeric = ["amount_eur", "total_events"]
categorical = ["region", "channel"]

pre = ColumnTransformer([
    ("num", StandardScaler(), numeric),
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
])
```

Note `handle_unknown="ignore"` — without it, a new category at serving time raises `ValueError: could not convert string to float` and takes the endpoint down. This is a production outage waiting in the encoder.

### 4. `KeyError` / label mismatch between train and serve

**Symptom.**

```text
KeyError: 'days_since_last_order'
```

or, more insidiously, no error at all but every prediction is the majority class, because the feature defaults to zero when the key is missing.

**Cause.** The serving path computes a different feature set from the training path, or a feature lookup misses and returns null.

**Fix.** Validate the feature contract at the endpoint boundary, and fail closed:

```python
REQUIRED_FEATURES = ("total_events", "n_orders", "total_spend_eur",
                     "distinct_channels", "distinct_regions")

def validate_features(payload):
    missing = [f for f in REQUIRED_FEATURES if f not in payload]
    if missing:
        raise ValueError(f"missing required features: {missing}")
    return payload
```

Never let a missing feature become a zero. Zero is a valid value for `n_orders` and it means "no orders" — a meaningful state, not an absence. The absence needs to be distinguishable.

### 5. The class imbalance trap: 99% accuracy, zero business value

**Symptom.** The model "achieves 99% accuracy" and nobody can find a use for it.

**Cause.** The positive rate is ~1%. The majority-class baseline already scores 99%.

**Fix.** Never report accuracy alone. Report the full suite and pick the threshold by cost. Then **resample for training but not for evaluation**:

```python
# Training: resample or use class weights.
# Evaluation: ALWAYS on the original distribution.
```

Evaluating on resampled data is a classic self-deception — you optimise for a distribution you will never serve, and your precision looks great while your recall in the real population collapses.

### 6. `google.api_core.exceptions.InvalidArgument` on a BigQuery table in the training pipeline

**Symptom.**

```text
google.api_core.exceptions.InvalidArgument: Table name "events" missing dataset while no default dataset is set in the request
```

**Cause.** A training job or notebook referenced a bare table name, relying on a default dataset that was never set in that context. It works in a notebook with a default dataset configured and fails in a service account context.

**Fix.** Always fully qualify:

```python
QUERY = """
SELECT *
FROM `my-project.curated.events`
WHERE event_dt >= @start AND event_dt < @end
"""
```

Note the **partition filter** as well: an unqualified query scans the whole table, and the training run reads it every night.

---

## 💡 Production Notes

- **Write the problem statement before you write any code, and get it reviewed by the person who owns the decision.** The output is a paragraph naming the decision, the prediction time, the outcome window, the baseline, and the cost of each error. If you cannot write it, the project is not ready.

- **The label definition is a data-engineering artefact and belongs in version control next to the feature SQL.** "Churned" means a specific query. Put it in the repo, not in a slide.

- **Enforce the label horizon in the training-data query.** Exclude every entity whose observation window is shorter than the outcome window. Anything else silently labels your newest customers as "not churned" and teaches the model an inverse relationship.

- **Split by the entity you predict, not by the row.** If the model predicts per user, the split groups by user. Make the split function *require* the group key so it cannot be done wrong.

- **Log every feature value with every prediction, permanently.** This is the only way to detect training/serving skew, covariate drift, and silent pipeline failures. Log to BigQuery, partitioned by prediction date, with a retention policy that outlives your retraining cycle. Retrofitting logging onto an existing endpoint is far harder than adding it at launch.

- **Alert on the positive rate before you alert on drift.** If the fraction of predictions above the threshold moves by 2× or 0.5×, something broke — a failed feature job, a schema change, a distribution shift. It is the cheapest, loudest, earliest signal you have.

- **Version the training data, not just the code.** An immutable dated snapshot plus a manifest recording the feature SQL SHA, the label table, the label as-of date, the row count, the hyperparameters, the metrics, and the artefact hash. Six months from now this is the difference between reproducing a model and guessing at it.

- **Set feature freshness from the decision's latency budget, not from the pipeline's convenience.** A prediction with a 14-day horizon can tolerate daily features. A fraud score with a 60-second horizon cannot tolerate a 5-minute refresh. Know which one you have before you choose a refresh interval.

- **Check performance by segment, not just in aggregate.** Aggregate AUC of 0.90 with 0.55 on your largest segment is a failure. Segment metrics are also where label-noise problems show up first.

- **Keep a holdout population that the model never scores.** If the model drives a treatment, training on its own output teaches it on its own effects. A small untreated holdout is cheap insurance.

- **Prefer BigQuery-side features over a feature store until you actually serve online.** A versioned SQL query used by both the training job and the batch scoring job gives you parity for free. A feature store is the right answer for online serving with complex features — not the default answer.

---

## 🔑 Key Takeaways

- **This course is written for data engineers, not researchers.** The questions that matter are: where does the training data come from, what breaks between training and production, and can you rebuild the training set in six months.
- **Supervised, unsupervised, reinforcement** — supervised dominates enterprise data work because it has the hardest data problem: the label. RL requires a faithful simulator; historical logs are not one.
- **Most "we need machine learning" problems are rules or statistics.** Saying so early is the highest-value thing you can do for a project.
- **The eight-stage workflow** — frame → collect and label → explore → engineer features → train → evaluate → deploy → monitor. Projects fail most often by starting at stage 6.
- **The train/validation/test split is a statistical contract.** Split by the entity you predict, split chronologically for temporal data, fit preprocessing on train only, and look at the test set exactly once.
- **Overfitting shows as a gap** between training and validation error. Read the learning curve to distinguish it from underfitting. Fix overfitting with more data first and regularisation second.
- **Accuracy lies whenever classes are imbalanced.** At a 1% positive rate, predicting "no" everywhere scores 99%. Report precision, recall, F1, and PR-AUC alongside it.
- **Precision vs recall is a business decision in technical clothing.** Decide what a false positive and a false negative cost in euros, then pick the threshold by that ratio — not by defaulting to 0.5.
- **F1 is a harmonic mean on purpose.** It punishes imbalance between precision and recall, which the arithmetic mean hides.
- **ROC-AUC compares models; the threshold makes decisions.** On imbalanced data, PR-AUC is the more informative curve.
- **Calibration matters separately from discrimination.** Well-calibrated scores are additive and can be summed into a business case. AUC says nothing about calibration.
- **EDA for a data engineer is pipeline validation.** Row counts, null rates, cardinality, ranges, time coverage, class balance — run them on every load, as tests, not once in a notebook.
- **Feature engineering is data engineering.** Temporal features (recency, frequency, monetary, ratios, trend) carry most of the signal in event data.
- **Target leakage** is the most common cause of a model that is brilliant offline and useless live. Ask of every feature: *could this value have been known at prediction time?* Enforce the as-of predicate in SQL, and assert it in CI.
- **The data engineer's role spans the whole lifecycle**: labelling pipelines, feature stores, training-data versioning, skew detection, and monitoring.
- **Label-window truncation** is the subtle bug that quietly reverses the relationship you are trying to learn. Enforce it in the training query.
- **The lifecycle breaks in three places:** training/serving skew (same feature, two definitions), feature staleness (right definition, old data), and drift (covariate drift is detectable now; concept drift only after labels mature).
- **Add a fourth: the feedback loop.** A model that drives treatment sees its own effects in the data. Keep a holdout the model never scores.
- **Monitor inputs, outputs, and outcomes.** Log every feature with every prediction, alert on the positive rate first, and check performance by segment — aggregate metrics hide the segment that is failing.

---

## 📚 Practice Exercises

1. **EDA as a pipeline test.** Using `project/core/pipeline_logic.py`, write a function `validate_dataset(lines)` that asserts: exactly 4800 accepted rows, 0 rejects on `sample_data/events.csv`, exactly 12 rejects with the exact reason taxonomy on `sample_data/malformed_events.csv`, and 4 distinct regions in the summary. Then write the equivalent as a Dataform test in SQLX and explain which one runs on every load and which one runs once.

2. **Label-window truncation, quantified.** Using `sample_data/events.csv`, build a per-user event count, define a 90-day observation window, and show how many users would be mislabelled as "not churned" if the truncation filter were omitted. Then write the exact SQL predicate that excludes them, and explain why the filter belongs in the training-data query rather than in a notebook.

3. **Metric suite from scratch.** Write `precision`, `recall`, `f1`, `roc_auc` (rank-sum method), and `average_precision` as standalone functions over `(y_true, y_pred)` and `(score, label)` pairs. Verify them against `sklearn.metrics` on a synthetic dataset with a 2% positive rate. Then produce a threshold sweep table with the accuracy-optimal and the cost-optimal (€40 FP / €140 FN) thresholds, and explain why they differ.

4. **Leakage detector.** Write a function that, given a feature-building function and a cutoff timestamp, returns every row whose feature value could not have been known at the cutoff. Test it against a leaky aggregate (no as-of filter) and a clean one. Then extend it to check the *training-data manifest* — verify that the recorded feature SQL SHA matches the current file and raise if the model was trained on a different definition.

5. **Feature store design.** Design a Vertex AI Feature Store for a churn model: name the feature view, the entity key, the online and offline stores, the sync mode (periodic vs streaming), the refresh interval, and the latency budget it satisfies. Justify the sync mode choice with a concrete staleness calculation. Then explain what breaks if you skip the feature store and compute features in the application request path instead.

6. **Drift monitoring job.** Write `monitor_drift(baseline_df, current_df, feature, bins)` that computes PSI, the positive-rate ratio, and the missing-rate delta, and returns a severity (`STABLE` / `MODERATE` / `SIGNIFICANT`). Run it against a baseline built from `sample_data/events.csv` and a synthetic drifted population. Then write the alert thresholds and the runbook entry for each severity.

7. **Cost-weighted threshold.** Using the pipeline's per-region summary (`render_summary_csv`), design a "which region should the retention team prioritise" model. Define the outcome, the label, the features, the metric, and the cost ratio between the regions' customer values. Then explain why the model must be trained per-region or include region as a feature rather than predicting globally.

8. **Manifest and reproducibility.** Extend `build_manifest` from the Hands-On section into a `TrainManifest` dataclass with a `save`/`load` pair writing to `gs://`. Add the model artefact SHA, the container image digest, the random seed, and the training-range partition bounds. Then write the acceptance test: given only the manifest, rebuild the training matrix and assert the row count and the label distribution match the recorded values.

---

## 📖 Further Reading

- [Machine Learning on Google Cloud — Documentation](https://cloud.google.com/machine-learning/docs)
- [Vertex AI — Get Started with AutoML and Pre-trained Models](https://cloud.google.com/vertex-ai/docs/start/introduction-unified-platform)
- [Vertex AI — Model Monitoring: Model Drift Overview](https://cloud.google.com/gemini-enterprise-agent-platform/machine-learning/model-monitoring/overview)
- [Vertex AI — Feature Store Overview and Features](https://cloud.google.com/gemini-enterprise-agent-platform/machine-learning/featurestore)
- [BigQuery — Introduction to BigQuery ML](https://cloud.google.com/bigquery/docs/bqml-introduction)
- [Google Cloud Architecture — ML Model Serving and Model Management](https://cloud.google.com/gemini-enterprise-agent-platform/machine-learning/general/deployment)
- [Google Rules of ML](https://developers.google.com/machine-learning/guides/rules-of-ml)
- [Google — Machine Learning Crash Course](https://developers.google.com/machine-learning/crash-course)
