# 8.4 — BigQuery ML

> **Section 8 · ML on GCP & Capstone · Lecture 8.4 · 8:00**

## 🎯 What you will learn

- Why **BigQuery ML** exists and when it beats Vertex AI for a tabular problem
- The **`CREATE MODEL` syntax**, statement by statement, including every `OPTIONS` clause
- The **model types** and what each is actually good at:
  - `LOGISTIC_REGRESSION`, `LINEAR_REG`, `KMEANS`
  - `TREE_REGRESSOR`, `BOOSTED_TREE_CLASSIFIER` (XGBoost), `DNN_CLASSIFIER`, `DNN_REGRESSOR`
  - `FORECAST` (ARIMA) for time series
- **`TRAINING DATA`** with `WITH` and `OPTIONS` — including `input_label_cols` and `data_split_method`
- **`ML.EVALUATE`** — reading the confusion matrix, the ROC curve, the PR curve, and the lift tables
- **`ML.PREDICT`** — the `TABLE(...)` syntax, the `STRUCT` syntax, and the `EXCEPT` clause
- **Feature engineering in SQL** — the `ML.FEATURES.*` functions, one-hot encoding, `ML.BUCKETIZE`
- The **cost advantage**: no data movement, no endpoint, no pipeline
- The **limits**: what BigQuery ML cannot do that Vertex AI can — and the specific cases where you must leave the warehouse

---

## 🧠 Concept

### What BigQuery ML actually is

BigQuery ML lets you train a model with a `CREATE MODEL` statement and score with a `SELECT`. The model lives in your BigQuery dataset as an object, exactly like a table. You query it with a `SELECT`.

```sql
CREATE OR REPLACE MODEL `my-project.curated.churn_model`
OPTIONS (
  MODEL_TYPE = 'BOOSTED_TREE_CLASSIFIER',
  INPUT_LABEL_COLS = ['churned_30d'],
  DATA_SPLIT_METHOD = 'CUSTOM',
  DATA_SPLIT_COLUMN = 'is_test'
);

SELECT * FROM ML.PREDICT(MODEL `my-project.curated.churn_model`,
  (SELECT * FROM `my-project.curated.scoring_batch`));
```

**That is the whole product.** No container, no training code, no endpoint, no SDK.

### Why it exists

Three reasons, and they are the three reasons it is genuinely good rather than a toy:

**1. No data movement.** This is the headline. A Vertex AI training job has to read your BigQuery table and get it into the training container's memory — over the network, at scale, every retraining. BigQuery ML trains on the data **in place**, in the same storage layer, on the same infrastructure that runs the query. For a 50 GB training table, the difference is minutes versus tens of minutes, and the difference in *network egress and complexity* is much larger than the time.

**2. No serving infrastructure.** `ML.PREDICT` is a query. It runs on BigQuery's slots, scales like a query, and costs like a query. There is no endpoint, no replicas, no minimum node count, no autoscaler, no cold start, no VPC. For batch scoring, this is a massive simplification.

**3. The model is queryable with the rest of your data.** The model's evaluation metrics are in `MODEL` and `EVALUATE` system tables. Its predictions join against your warehouse. Its feature importances are queryable. It is a first-class data object.

### The decision: BigQuery ML vs Vertex AI AutoML Tables

These two solve overlapping problems. The overlap is large and the differences are real.

| | **BigQuery ML** | **Vertex AI AutoML Tables** |
|---|---|---|
| **Training** | `CREATE MODEL` | Console or SDK job |
| **Data location** | BigQuery only | BigQuery, CSV, or a Vertex dataset |
| **Serving** | `ML.PREDICT` in SQL — batch only | Online endpoint (real-time) or batch |
| **Latency** | Query time — seconds to minutes | Online: milliseconds |
| **Custom preprocessing** | SQL expressions, `ML.FEATURES.*` | Full Python — arbitrary transforms |
| **Hyperparameter search** | Limited (`num_trials` for boosted trees) | Full Bayesian search over a parameter space |
| **Feature importances** | Yes, via `MODEL` system tables | Yes, in the console |
| **Cost shape** | BigQuery slot-hours for training + query cost for scoring | Node-hours for training + endpoint node-hours for serving |
| **New model types** | ARIMA, KMEANS, linear models, plus boosted trees and DNN | AutoML's ensemble; plus custom training for anything |
| **Explainability** | `ML.EXPLAIN_PREDICT` (SHAP) | SHAP via the explainability API |
| **Governance** | `MODEL` object, same IAM as your tables, in Data Catalog | Separate Vertex resource hierarchy |

**The decision rule:**

```text
Is the scoring batch?
    └─ YES → BigQuery ML. Almost always.
    └─ NO  (need real-time, sub-second predictions)
        └─ BigQuery ML cannot do it → Vertex AI endpoint.
```

**And the second rule:** if you need custom preprocessing written in Python, deep feature engineering, or a hyperparameter search space wider than BigQuery ML's `num_trials`, use Vertex AI.

**The third rule, which surprises people:** BigQuery ML supports **more model types than AutoML Tables**. `FORECAST` (ARIMA), `KMEANS`, `LINEAR_REG`, `LINEAR_REG` with regularisation options, `DNN_CLASSIFIER` with TensorFlow — several of these have no AutoML Tables equivalent. If you want ARIMA inside BigQuery, BigQuery ML is the *only* option short of writing it yourself.

### The `CREATE MODEL` statement

```sql
CREATE [OR REPLACE] MODEL `project.dataset.model_name`
[TRANSFORM(...)]
OPTIONS (
  model_option = value,
  ...
)
[AS SELECT ...]
```

Three parts, and the third is the important one.

**Part 1 — the model name.** A model is a first-class object in a dataset. It shows up in the console, in `INFORMATION_SCHEMA`, and in Data Catalog. Naming it `curated.churn_model` rather than `scratch.temp_1234` is the first act of discipline, because a model in a scratch dataset will be garbage-collected and nobody will know it mattered.

**Part 2 — `OPTIONS`.** The model type and its hyperparameters. This is where the behaviour lives.

**Part 3 — `AS SELECT` or `TRANSFORM`.** The training data query.

**The `AS SELECT` form:**

```sql
CREATE OR REPLACE MODEL `my-project.curated.churn_model`
OPTIONS (
  MODEL_TYPE = 'BOOSTED_TREE_CLASSIFIER',
  INPUT_LABEL_COLS = ['churned_30d']
)
AS
SELECT
  n_events,
  n_orders,
  total_spend_eur,
  refund_rate,
  region,
  channel,
  churned_30d
FROM `my-project.curated.user_features_daily`
WHERE feature_as_of = '2026-01-15';
```

**The `TRANSFORM` form:**

```sql
CREATE OR REPLACE MODEL `my-project.curated.churn_model`
TRANSFORM(
  ML.ONE_HOT_ENCODER(ML.BUCKETIZE(n_events, [0, 5, 10, 20, 50])) OVER(ORDER BY n_events) AS n_events_bucket,
  ML.BUCKETIZE(total_spend_eur, [0, 50, 100, 250, 500, 1000]) OVER(ORDER BY total_spend_eur) AS spend_bucket,
  CAST(churned_30d AS INT64) AS label
)
OPTIONS (
  MODEL_TYPE = 'LOGISTIC_REGRESSION',
  INPUT_LABEL_COLS = ['label'],
  L1_REG = 0.1,
  L2_REG = 0.1
);
```

**`TRANSFORM` vs `AS SELECT` — the important difference.** `TRANSFORM` only sees the columns of the `TRAINING DATA` subquery and defines the model's *input columns*. `AS SELECT` defines the training data and, by default, **every column in the SELECT becomes a feature** — including the label.

**This is the number one gotcha in BigQuery ML:** with `AS SELECT`, if you include `user_id` in the select list, `user_id` becomes a feature. A high-cardinality identifier as a feature will let the model memorise individual users, produce a spectacular and completely meaningless score, and — because trees can split on it — will not show up as an obvious problem. **Always explicitly project the feature list, or use `TRANSFORM` where the feature set is by construction explicit.**

### The model types

#### `LOGISTIC_REGRESSION`

Multiclass or binary logistic regression, trained with a softmax or sigmoid loss.

```sql
CREATE OR REPLACE MODEL `my-project.curated.churn_model`
OPTIONS (
  MODEL_TYPE = 'LOGISTIC_REGRESSION',
  INPUT_LABEL_COLS = ['churned_30d'],
  L1_REG = 0.01,
  L2_REG = 0.01,
  DATA_SPLIT_METHOD = 'AUTO'
)
AS SELECT ... ;
```

**Options:**

| Option | Meaning |
|---|---|
| `L1_REG` | L1 regularisation. Drives coefficients to zero — performs feature selection. |
| `L2_REG` | L2 regularisation (ridge). Shrinks coefficients smoothly. Does not zero them. |
| `DATA_SPLIT_METHOD` | `'AUTO'` (default: 80/10/10), `'RANDOM'`, `'CUSTOM'`, `'SEQ'`, `'NO_SPLIT'` |
| `DATA_SPLIT_COLUMN` | Boolean column marking the split, used with `'CUSTOM'` |
| `DATA_SPLIT_EVAL_FRACTION` | Eval fraction with `'AUTO'` or `'RANDOM'` |
| `DATA_SPLIT_TRAIN_FRACTION` | Train fraction with `'AUTO'` or `'RANDOM'` |
| `LEARN_RATE` | Learning rate for the optimiser |
| `MAX_ITERATIONS` | Maximum training iterations |

**Note the `DATA_SPLIT_METHOD` values — this is important and under-used:**

- `'AUTO'` — random 80% train / 10% eval / 10% test. **Default, and wrong for temporal data.**
- `'RANDOM'` — random split with a specified fraction.
- `'CUSTOM'` — you provide a boolean `DATA_SPLIT_COLUMN`. **This is the option you want**, because it lets you encode your own split semantics in a column and be explicit about it.
- `'SEQ'` — sequential split by row order, for time series.
- `'NO_SPLIT'` — no split. The entire table is training data. Only for `FORECAST`.

**The practical recommendation:** always use `'CUSTOM'` with an explicit split column, because it makes the split visible in the data, reviewable by a human, and reproducible. The random default silently breaks your temporal logic.

#### `LINEAR_REG`

Ordinary least squares (or ridge regression with `L2_REG`).

```sql
CREATE OR REPLACE MODEL `my-project.curated.ltv_model`
OPTIONS (
  MODEL_TYPE = 'LINEAR_REG',
  INPUT_LABEL_COLS = ['lifetime_value_eur'],
  L2_REG = 0.01
)
AS SELECT ... ;
```

Use for continuous targets: revenue, lifetime value, session duration, sensor readings. It is fast, interpretable (the coefficients are the story), and a genuinely good baseline. **Always fit a `LINEAR_REG` before anything else.** If the gradient-boosted model beats it by 0.01 AUC, the boosted model is not earning its complexity.

#### `KMEANS`

Unsupervised clustering.

```sql
CREATE OR REPLACE MODEL `my-project.curated.customer_segments`
OPTIONS (
  MODEL_TYPE = 'KMEANS',
  K = 5,
  MIN_INITIALIZATION = 10,
  MAX_ITERATIONS = 50,
  INPUT_LABEL_COLS = []
)
AS
SELECT
  total_spend_eur,
  n_orders,
  days_since_last_order,
  refund_rate
FROM `my-project.curated.user_features_daily`
WHERE feature_as_of = '2026-01-15';
```

**Options:** `K` (the number of clusters), `MIN_INITIALIZATION` (number of k-means++ initialisations — more is more stable), `MAX_ITERATIONS`, `DISTANCE_TYPE` (`'EUCLIDEAN'` default, or `'COSINE'`).

**`DISTANCE_TYPE = 'COSINE'` is the one people miss.** Euclidean distance on unnormalised features means the feature with the largest scale dominates the clustering. If `total_spend_eur` ranges to 10,000 and `refund_rate` ranges to 0.05, you will get four clusters of spenders and one cluster of everything else. Either normalise the features first, or use cosine distance.

**`K` is a guess, and you should treat it as one.** Run a range of K values and inspect the cluster profiles. There is no elbow method built into BigQuery ML; you query the centroid table and look.

#### `TREE_REGRESSOR`

A single decision tree for regression. Included for completeness. In practice, a single tree is almost always beaten by `BOOSTED_TREE_CLASSIFIER` or `LINEAR_REG`, and it overfits badly. Use it when you need a single interpretable rule set.

#### `BOOSTED_TREE_CLASSIFIER` (and `BOOSTED_TREE_REGRESSOR`)

**This is the workhorse.** It is XGBoost, running inside BigQuery.

```sql
CREATE OR REPLACE MODEL `my-project.curated.churn_model`
OPTIONS (
  MODEL_TYPE = 'BOOSTED_TREE_CLASSIFIER',
  INPUT_LABEL_COLS = ['churned_30d'],
  L1_REG = 0.0,
  L2_REG = 1.0,
  NUM_TRIALS = 20,
  MAX_TREE_DEPTH = 6,
  LEARN_RATE = 0.1,
  DATA_SPLIT_METHOD = 'CUSTOM',
  DATA_SPLIT_COLUMN = 'is_test'
)
AS SELECT ... ;
```

**The options that matter:**

| Option | Default | Meaning |
|---|---|---|
| `NUM_TRIALS` | 1 | Number of hyperparameter configurations tried. **Set this above 1.** |
| `MAX_TREE_DEPTH` | 6 | Maximum depth of each tree. Deeper overfits. |
| `LEARN_RATE` | 0.1 | Shrinkage applied to each tree's contribution. |
| `L1_REG` | 0 | L1 regularisation on leaf weights |
| `L2_REG` | 1 | L2 regularisation on leaf weights |
| `MIN_REL_L1` | — | Threshold for pruning a leaf |

**`NUM_TRIALS` is the knob people leave at 1.** With `NUM_TRIALS = 1` you get one model with default hyperparameters, and you have done no hyperparameter search at all. With `NUM_TRIALS = 20` BigQuery runs 20 configurations and keeps the best by AUC. **The cost of this is BigQuery slot-hours, not node-hours** — which is the key economic difference from Vertex AI.

**How the trials work:** BigQuery samples from the hyperparameter space using a randomised search, evaluates each configuration on the eval split, and selects by AUC. It is a randomised search, not Bayesian — less efficient than Vertex's, but far cheaper and much simpler.

#### `DNN_CLASSIFIER` and `DNN_REGRESSOR`

A TensorFlow neural network trained inside BigQuery.

```sql
CREATE OR REPLACE MODEL `my-project.curated.churn_dnn`
OPTIONS (
  MODEL_TYPE = 'DNN_CLASSIFIER',
  INPUT_LABEL_COLS = ['churned_30d'],
  HIDDEN_UNITS = [64, 32],
  BATCH_SIZE = 256,
  DROPOOUT = 0.1,
  L1_REG = 0.0,
  L2_REG = 0.0,
  MAX_ITERATIONS = 1000,
  LEARN_RATE = 0.001
)
AS SELECT ... ;
```

**Options:** `HIDDEN_UNITS` (a list — `[64, 32]` is a two-layer network with 64 and 32 units), `BATCH_SIZE`, `DROPOUT`, `MAX_ITERATIONS`, `LEARN_RATE`, `L1_REG`, `L2_REG`, `INIT_LEARN_RATE`, `OPTIMIZER` (`'ADAM'` or `'SGD'`).

**When to use a DNN over boosted trees:** on tabular data, boosted trees are usually equal or better. A DNN earns its place when you have **high-cardinality categorical features with meaningful embeddings**, a very large dataset, or unstructured inputs you have embedded. For a standard tabular churn problem, **start with `BOOSTED_TREE_CLASSIFIER` and only move to a DNN if you have a specific reason.**

#### `FORECAST` (ARIMA)

Time-series forecasting inside BigQuery. This is the model type with no AutoML Tables equivalent at all.

```sql
CREATE OR REPLACE MODEL `my-project.curated.revenue_forecast`
OPTIONS (
  MODEL_TYPE = 'FORECAST',
  HORIZON = 30,
  MODEL_OPTIONS = (holl_winters_triple = true)
)
AS
SELECT
  TIMESTAMP_MICROS(CAST(timestamp_micros AS INT64)) AS time_series_timestamp,
  value
FROM `my-project.curated.hourly_revenue`
WHERE time_series_timestamp BETWEEN
      TIMESTAMP('2025-01-01') AND TIMESTAMP('2025-12-31');
```

**Options:**

| Option | Meaning |
|---|---|
| `HORIZON` | Number of future points to predict |
| `MODEL_OPTIONS` | A struct of ARIMA/Holt-Winters settings |
| `MODEL_OPTIONS (holl_winters_triple = true)` | Use triple exponential smoothing |
| `MODEL_OPTIONS (auto_arima = true)` | Auto-select the ARIMA order |
| `MODEL_OPTIONS (arima_order = [3,1,2])` | Explicit (p,d,q) |
| `MODEL_OPTIONS (data_frequency = 'per_hour')` | The seasonality of the series |

**The critical constraint: the input must be a regular time series.** ARIMA on irregular data produces nonsense. You need one row per time bucket, with **no gaps**. If your series has missing hours, you must fill them with zeros (or `NULL`) before training — a gap is a value the model must interpret.

**The `data_frequency` option matters** for the seasonality: hourly data with a daily period needs `data_frequency = 'per_hour'` for the model to know that 24 observations make a day.

**A caveat on the historical window:** `FORECAST` fits on the data you give it. It does not know about structural changes, promotions, or seasonality that will occur in the forecast horizon. And a 30-day horizon from a model trained on last year's data is 30 days of extrapolation, which is where ARIMA is weakest.

### `TRAINING DATA` and the split

For the model types where you supply a subquery, `TRAINING DATA` gives you explicit control over the training set.

```sql
CREATE OR REPLACE MODEL `my-project.curated.churn_model`
OPTIONS (
  MODEL_TYPE = 'BOOSTED_TREE_CLASSIFIER',
  INPUT_LABEL_COLS = ['churned_30d'],
  DATA_SPLIT_METHOD = 'CUSTOM',
  DATA_SPLIT_COLUMN = 'split',
  NUM_TRIALS = 20
)
TRAINING DATA AS
SELECT
  user_id,          -- a feature you should NOT include
  n_events,
  n_orders,
  total_spend_eur,
  refund_rate,
  region,
  channel,
  churned_30d,
  CASE
    WHEN feature_as_of < '2026-01-01' THEN 'TRAIN'
    WHEN feature_as_of < '2026-01-10' THEN 'EVAL'
    ELSE 'TEST'
  END AS split
FROM `my-project.curated.user_features_daily`
WHERE feature_as_of < '2026-01-15';
```

Note the `split` column holds `'TRAIN'`, `'EVAL'`, `'TEST'` strings. **`DATA_SPLIT_COLUMN` with `DATA_SPLIT_METHOD = 'CUSTOM'` accepts a boolean**, where `TRUE` means test and `FALSE` means train-and-eval (BigQuery then splits that portion further). It does *not* accept a three-way string label in all model types. **The robust pattern is to materialise a boolean `is_test` column** and use `'CUSTOM'`:

```sql
  CASE WHEN feature_as_of >= '2026-01-10' THEN TRUE ELSE FALSE END AS is_test
```

**The temporal split, done correctly.** The example above is the right shape: train on the past, evaluate on the middle, test on the most recent. Note it uses `feature_as_of`, not the event timestamp — the feature snapshot date is the correct axis, because that is what determines whether a feature would have been available at prediction time.

**The `DATA_SPLIT_METHOD = 'AUTO'` default is a random split.** For a temporal problem that means the model trains on data from the future to predict the past. On a churn model, it will look excellent and generalise badly.

### Reading the results: `ML.EVALUATE`

```sql
SELECT
  * EXCEPT (label, predicted_label_probs)
FROM ML.EVALUATE(MODEL `my-project.curated.churn_model`);
```

The output depends on the model type.

**For a classifier**, one row with:

| Column | Meaning |
|---|---|
| `precision` | Precision at the default threshold (0.5) |
| `recall` | Recall at the default threshold |
| `f1_score` | F1 at the default threshold |
| `accuracy` | Accuracy at the default threshold |
| `log_loss` | Log loss — a proper scoring rule, sensitive to overconfident wrong answers |
| `roc_auc` | Area under the ROC curve |
| `pr_auc` | Area under the precision-recall curve |

**And critically — two more tables for the threshold-independent curves:**

```sql
-- The full ROC curve.
SELECT * FROM ML.ROC(
  MODEL `my-project.curated.churn_model`,
  TABLE `my-project.curated.churn_test`
);

-- The full PR curve.
SELECT * FROM ML.PRC(
  MODEL `my-project.curated.churn_model`,
  TABLE `my-project.curated.churn_test`
);
```

Both return the false positive rate, true positive rate, precision, recall, and threshold at each point. **This is how you pick a threshold** — you read the PR curve, pick the point where the business cost is minimised, and use that threshold everywhere.

**For `KMEANS`,** `ML.EVALUATE` returns one row per cluster with `num_points`, `centroid_*` features, and the `distance_from_centroid` statistics.

**For `FORECAST`,** `ML.EVALUATE` returns the forecast rows with the predicted value and the actual value where known, so you can compute the error directly.

**The `ML.WEIGHTS` function** returns the model weights for linear models:

```sql
SELECT * FROM ML.WEIGHTS(MODEL `my-project.curated.churn_model`);
```

**And feature importances** for boosted trees and DNNs:

```sql
SELECT
  feature_name,
  ROUND(importance, 4) AS importance,
  ROUND(weighted_gain, 4) AS weighted_gain,
  ROUND(weighted_average_gain, 4) AS weighted_average_gain
FROM ML.FEATURE_IMPORTANCES(MODEL `my-project.curated.churn_model`)
ORDER BY importance DESC;
```

**Three different importance measures, and they mean different things:**

- **`importance`** — the number of times the feature was used to split across all trees. Sensitive to features that offer many small splits.
- **`weighted_gain`** — the total gain (improvement in the loss) from all splits on that feature, across all trees. This is usually the more meaningful measure of predictive power.
- **`weighted_average_gain`** — `weighted_gain` normalised by the number of times the feature was used. **This is the one to compare across features with different split frequencies**, and it is the one people forget.

**Read `weighted_average_gain` when comparing features.** A feature used 500 times with a small gain each may have a high `importance` and a low `weighted_average_gain`.

### `ML.PREDICT`

Three forms.

**`TABLE(...)` — the form you will use 95% of the time:**

```sql
SELECT
  user_id,
  predicted_churned_30d,
  predicted_churned_30d_probs[OFFSET(0)].prob
FROM ML.PREDICT(
  MODEL `my-project.curated.churn_model`,
  (SELECT * FROM `my-project.curated.scoring_batch`)
);
```

**Mechanics of the output:**
- `predicted_<label_column>` — the hard prediction at the default threshold.
- `predicted_<label_column>_probs` — an **ARRAY of STRUCTs**, one per class, each with `label` and `prob`, sorted **descending by probability**. So `[OFFSET(0)]` is the *predicted* class and its probability.

**The `EXCEPT` clause** removes the label from the input, which you need when the scoring table still contains it:

```sql
SELECT *
FROM ML.PREDICT(
  MODEL `my-project.curated.churn_model`,
  (SELECT * EXCEPT(churned_30d) FROM `my-project.curated.scoring_batch`)
);
```

**`STRUCT(...)` — for scoring single rows:**

```sql
SELECT ML.PREDICT(
  MODEL `my-project.curated.churn_model`,
  STRUCT(
    14 AS n_events,
    3 AS n_orders,
    482.15 AS total_spend_eur,
    0.0714 AS refund_rate,
    'EMEA' AS region,
    'web' AS channel
  )
);
```

**The inline-`TABLE` form — no subquery at all:**

```sql
SELECT ML.PREDICT(
  MODEL `my-project.curated.churn_model`,
  TABLE(
    SELECT 14 AS n_events, 3 AS n_orders, 482.15 AS total_spend_eur
  )
);
```

**The prediction table must match the model's input schema exactly.** Column names, order (for `STRUCT`), and types. A missing column, an extra column, or a type mismatch (INT64 vs FLOAT64) produces a schema error. The reliable way to avoid this is to derive the scoring table's columns from the model's own schema:

```sql
-- Get the model's input schema so you can build a matching table.
SELECT feature_name, feature_type
FROM ML.FEATURE_IMPORTANCES(MODEL `my-project.curated.churn_model`);
```

Or, more robustly, keep a view that projects exactly the model's features, and score from that view.

### The scoring pattern for production

The way BigQuery ML earns its keep is a **scoring table built by a scheduled query**, joined back to the entities.

```sql
-- 1. Build the scoring batch from the latest feature snapshot.
CREATE OR REPLACE TABLE `my-project.curated.scoring_batch`
AS
SELECT
  user_id,
  n_events,
  n_orders,
  total_spend_eur,
  avg_order_value_eur,
  refund_rate,
  region,
  channel
FROM `my-project.curated.user_features_daily`
WHERE feature_as_of = (
  SELECT MAX(feature_as_of)
  FROM `my-project.curated.user_features_daily`
);

-- 2. Score it and write the scores back.
CREATE OR REPLACE TABLE `my-project.curated.churn_scores`
AS
SELECT
  user_id,
  predicted_churned_30d AS churn_predicted,
  predicted_churned_30d_probs[OFFSET(0)].prob AS churn_probability
FROM ML.PREDICT(
  MODEL `my-project.curated.churn_model`,
  (SELECT * FROM `my-project.curated.scoring_batch`)
);

-- 3. Join the scores back for the business.
SELECT
  s.user_id,
  s.churn_probability,
  u.total_spend_eur,
  u.region
FROM `my-project.curated.churn_scores` s
JOIN `my-project.curated.user_features_daily` u
  ON s.user_id = u.user_id
WHERE u.feature_as_of = '2026-01-15'
  AND s.churn_probability >= 0.35
ORDER BY s.churn_probability DESC;
```

**This runs on a schedule from Composer.** Step 1, 2, and 3 are three statements in one scheduled query. There is no endpoint, no training pipeline, no container, no SDK. **This is the single strongest argument for BigQuery ML.**

### Feature engineering in SQL

BigQuery ML has a family of `ML.FEATURES.*` functions.

**`ML.BUCKETIZE`** — bin a numeric feature.

```sql
ML.BUCKETIZE(n_events, [0, 5, 10, 20, 50]) OVER (ORDER BY n_events)
```

Returns the bucket index. For a boosted tree, this matters less than you would think — trees split on thresholds automatically. **It matters a lot for logistic regression**, where a linear coefficient cannot express "the effect is zero until 20 events, then steep."

**`ML.ONE_HOT_ENCODER`** — turn a categorical into a set of indicator columns.

```sql
ML.ONE_HOT_ENCODER(region) OVER(ORDER BY region) AS region_onehot
```

**`ML.POLYNOMIAL`** — polynomial expansion.

```sql
ML.POLYNOMIAL(total_spend_eur, degree=2) OVER (ORDER BY total_spend_eur)
```

**`ML.FEATURES.CROSSED`** — cross two categorical features.

```sql
ML.FEATURES.CROSSED(STRUCT(region, channel)) OVER(ORDER BY region, channel)
```

**`ML.FEATURES.TIME_*`** — a family of time-feature extractors.

```sql
ML.FEATURES.TIME_DAY(CAST(ts AS TIMESTAMP)) AS day_of_week
ML.FEATURES.TIME_HOUR(CAST(ts AS TIMESTAMP)) AS hour_of_day
ML.FEATURES.TIME_DAY_OF_WEEK(CAST(ts AS TIMESTAMP)) AS dow
ML.FEATURES.TIME_DIFF(CAST(ts AS TIMESTAMP), CAST(prev_ts AS TIMESTAMP)) AS secs_since_prev
```

**`ML.FEATURES.QUANTILES`** — discretise by quantiles rather than fixed boundaries.

```sql
ML.FEATURES.QUANTILES(total_spend_eur, 10) OVER (ORDER BY total_spend_eur) AS spend_decile
```

**The `OVER (ORDER BY ...)` clause is mandatory** on every one of these. It is the analytic-window syntax that makes the function operate row-wise over the input rather than as an aggregate. Omitting it produces an error.

**Which of these are actually worth it?**

For **`BOOSTED_TREE_CLASSIFIER`**: mostly none of them. The tree finds the thresholds itself. Bucketising a feature before a tree is at best neutral and at worst harmful — you throw away information the tree could have used.

For **`LOGISTIC_REGRESSION`**: nearly all of them. A linear model cannot learn a threshold, so bucketising a feature is how you give it the capacity to. One-hot encoding is mandatory for categoricals.

**The rule:** the feature engineering you need is inversely proportional to the model's capacity. Trees need none; linear models need a lot; DNNs need the raw numeric columns (they learn their own representations).

**But there is a feature-engineering step that matters for every model type: the aggregate features.** You cannot express "orders in the last 30 days" as a `ML.FEATURES.*` function. You compute it in a SQL window function or a join, and it is where most of the signal lives:

```sql
CREATE OR REPLACE TABLE `my-project.curated.user_features_daily` AS
SELECT
  user_id,
  DATE(TIMESTAMP_SECONDS(event_ts)) AS feature_as_of,
  COUNT(*) AS n_events,
  COUNTIF(event_type = 'order') AS n_orders,
  SUM(IF(event_type = 'order', amount_eur, 0)) AS total_spend_eur,
  COUNTIF(event_type = 'refund') AS n_refunds,
  SAFE_DIVIDE(
    COUNTIF(event_type = 'refund'), COUNT(*)
  ) AS refund_rate,
  COUNT(DISTINCT channel) AS n_channels,
  COUNT(DISTINCT region) AS n_regions,
  -- Recency: the most recent order before the snapshot.
  MAX(IF(event_type = 'order', TIMESTAMP_SECONDS(event_ts), NULL)) AS last_order_ts
FROM `my-project.curated.events`
WHERE event_dt < '2026-01-16'      -- the as-of predicate
GROUP BY user_id, feature_as_of;
```

**The `WHERE event_dt < '2026-01-16'` predicate is the whole ballgame.** Without it you have leakage. With it you have a training table you can rebuild deterministically.

### The cost advantage

```text
VERTEX_AI_TRAINING_PER_NODE_HOUR = 3.67   (Vertex AI training)
BIGQUERY_ONDEMAND_PER_TB = 6.25           (BigQuery on-demand scan)
BIGQUERY_SLOT_HOUR = 0.06                 (BigQuery flat-rate slot-hour)
```

**Vertex AI path for a churn model, retrained monthly:**

```text
Training: 4 node-hours × $3.67                    = $14.68/month
Endpoint: 1 replica, always on, ~730 hours/month  ≈ $292/month
                                                        ────────────
Total                                            ≈ $307/month
```

**BigQuery ML path for the same model:**

```text
Training: BigQuery runs the CREATE MODEL on its own slots.
          A 1M-row boosted-tree model with NUM_TRIALS=20 takes
          perhaps 20-40 slot-hours of compute.
          30 slot-hours × $0.06                     = $1.80
Scoring: a query that reads a 100 MB table and scores
          1M rows — a fraction of a cent.
                                                   ────────────
Total                                            ≈ $2/month
```

**That is a 150× difference, and the endpoint is most of it.**

But the *real* comparison is not the dollar figure — it is the **operational surface**:

```text
Vertex AI                              BigQuery ML
─────────────────────────────          ─────────────────────────
container image                        none
training code + versioning             none
pipeline definition (kfp)              none
model registry entry                   a model object in a dataset
endpoint + replicas + autoscaler       none
serving code                           one SELECT
monitoring config                      one scheduled query
retraining orchestration               one scheduled query
online prediction                      not supported
```

**BigQuery ML's one real disadvantage: no online prediction.** `ML.PREDICT` is a query. If you need a sub-second, per-request score inside an application request path, BigQuery ML cannot serve it and you need a Vertex AI endpoint. That is the single deciding factor.

**A hybrid pattern** that gets the best of both, and is worth knowing:

```text
Train with BigQuery ML          → the model lives in BigQuery
       │
       ├─→ export the model     → upload to Vertex AI Model Registry
       │                          → deploy to an endpoint
       │                          → serve online
       │
       └─→ score in bulk        → ML.PREDICT in a scheduled query
```

BigQuery ML models can be exported: `EXPORT MODEL OPTIONS (URI = 'gs://bucket/model/')` writes a TensorFlow saved model, a joblib file, or the native format. You can then upload it to Vertex AI and deploy it to an endpoint. **The training happens in the warehouse where the data already is, and the serving happens on an endpoint where the latency is.** This is the pattern I would actually build for a production tabular model that needs online scoring.

### The limits

What BigQuery ML cannot do, and what you do instead.

**1. No online / real-time prediction.** The biggest one. Batch only.

→ Use a Vertex AI endpoint, or export the model from BigQuery ML and deploy it.

**2. No custom training code.** You cannot write a custom loss, a custom preprocessing transform in Python, or a bespoke architecture.

→ Use Vertex AI custom training. If you need Python-level feature engineering, BigQuery ML is out.

**3. Limited hyperparameter search.** `NUM_TRIALS` is a randomised search over a fixed space, and only for the boosted-tree models. There is no Bayesian search.

→ Use Vertex AI AutoML Tables or a custom training job with a proper search space.

**4. No feature store, no training/serving skew management.** BigQuery ML scores from a table you build. If your online path computes features differently from the training table, nothing detects it.

→ Use Vertex AI Feature Store, or rigorously reuse one SQL view for both.

**5. No native support for unstructured inputs.** Images, audio, and raw text do not go into a BigQuery ML model directly. You would have to extract features (embeddings) first.

→ Use Vertex AI, or a pre-trained API to extract embeddings and then train a tabular model on the embeddings.

**6. Limited model types.** BigQuery ML has a fixed set. Notably **missing**: any transformer, any neural architecture beyond a plain MLP, gradient-boosted *regression* is present but LightGBM/CatBoost-style models are not, and there is no survival analysis, no ranking model, and no recommendation model.

→ Vertex AI, or a custom training job.

**7. Limited hyperparameter control for DNNs.** No dropout schedule, no batch-norm, no custom optimiser beyond Adam/SGD, no early stopping configuration.

→ Vertex AI.

**8. Model monitoring is manual.** There is no built-in drift detection, no prediction logging, no skew detection. You build it with scheduled queries.

→ Vertex AI model monitoring.

**9. No feature store-backed online/offline parity.** Already covered in 4.

**10. `DATA_SPLIT_METHOD = 'AUTO'` is a random split.** Not a limit of the platform so much as a trap in its defaults, but it is the thing that bites hardest.

→ Use `'CUSTOM'` with an explicit boolean split column, always.

---

## 🛠️ Hands-On

### Exercise 1 — The training table, built correctly

Everything before BigQuery ML is data engineering. This uses the course project.

```python
import sys
sys.path.insert(0, "project/core")

from pipeline_logic import (
    ingest_events,
    build_bigquery_rows,
    aggregate_events,
    render_summary_csv,
)
from collections import defaultdict

lines = open("sample_data/events.csv").read().splitlines()
accepted, _ = ingest_events(lines[1:])
rows = build_bigquery_rows(accepted)

PREDICTION_CUTOFF = "2026-01-16T00:00:00+00:00"
FEATURE_AS_OF = "2026-01-16"

history = defaultdict(list)
for r in rows:
    if r["event_dt"] < PREDICTION_CUTOFF:
        history[r["user_id"]].append(r)

feature_rows = []
for user_id, events in history.items():
    orders = [e for e in events if e["event_type"] == "order"]
    refunds = [e for e in events if e["event_type"] == "refund"]
    total = sum(o["amount_eur"] for o in orders)
    feature_rows.append({
        "user_id": user_id,
        "n_events": len(events),
        "n_orders": len(orders),
        "n_refunds": len(refunds),
        "total_spend_eur": round(total, 2),
        "avg_order_value_eur": round(total / len(orders), 2) if orders else 0.0,
        "refund_rate": round(len(refunds) / len(events), 4),
        "n_channels": len({e["channel"] for e in events}),
        "region": events[0]["region"],
        "channel": events[0]["channel"],
        "feature_as_of": FEATURE_AS_OF,
        "churned_30d": 1 if refunds else 0,
        # The explicit split. A boolean is_test column is the robust
        # form for DATA_SPLIT_METHOD='CUSTOM'.
        "is_test": False,
    })

print(f"training rows: {len(feature_rows)}")
positives = sum(r["churned_30d"] for r in feature_rows)
print(f"positives: {positives}  rate: {positives/len(feature_rows):.4f}")

# The feature list the model will see. Explicitly excludes user_id.
FEATURE_COLS = [
    "n_events", "n_orders", "n_refunds", "total_spend_eur",
    "avg_order_value_eur", "refund_rate", "n_channels",
    "region", "channel",
]
print(f"\nmodel features ({len(FEATURE_COLS)}): {FEATURE_COLS}")
print("excluded: user_id (identifier — would be memorised)")
print("excluded: feature_as_of, is_test (split metadata)")
```

### Exercise 2 — The `CREATE MODEL` statements

The full set, one per model type.

```sql
-- 1. A linear baseline. ALWAYS fit this first.
CREATE OR REPLACE MODEL `my-project.curated.ltv_linear`
OPTIONS (
  MODEL_TYPE = 'LINEAR_REG',
  INPUT_LABEL_COLS = ['total_spend_eur'],
  L2_REG = 0.01,
  DATA_SPLIT_METHOD = 'CUSTOM',
  DATA_SPLIT_COLUMN = 'is_test'
)
AS
SELECT
  n_events, n_orders, total_spend_eur, refund_rate, n_channels
FROM `my-project.curated.user_features_daily`
WHERE feature_as_of = '2026-01-16';

-- 2. The workhorse: boosted trees with a real hyperparameter search.
CREATE OR REPLACE MODEL `my-project.curated.churn_model`
OPTIONS (
  MODEL_TYPE = 'BOOSTED_TREE_CLASSIFIER',
  INPUT_LABEL_COLS = ['churned_30d'],
  NUM_TRIALS = 20,
  MAX_TREE_DEPTH = 6,
  LEARN_RATE = 0.1,
  L1_REG = 0.0,
  L2_REG = 1.0,
  DATA_SPLIT_METHOD = 'CUSTOM',
  DATA_SPLIT_COLUMN = 'is_test'
)
AS
SELECT
  n_events, n_orders, n_refunds, total_spend_eur,
  avg_order_value_eur, refund_rate, n_channels, region, channel,
  churned_30d
FROM `my-project.curated.user_features_daily`
WHERE feature_as_of = '2026-01-16';

-- 3. Logistic regression, with the bucketisation that makes a linear
--    model able to express a threshold.
CREATE OR REPLACE MODEL `my-project.curated.churn_logistic`
OPTIONS (
  MODEL_TYPE = 'LOGISTIC_REGRESSION',
  INPUT_LABEL_COLS = ['label'],
  L1_REG = 0.01,
  L2_REG = 0.01,
  DATA_SPLIT_METHOD = 'CUSTOM',
  DATA_SPLIT_COLUMN = 'is_test'
)
TRANSFORM(
  ML.BUCKETIZE(n_events, [0, 5, 10, 20, 50]) OVER(ORDER BY n_events) AS n_events_bucket,
  ML.BUCKETIZE(total_spend_eur, [0, 50, 100, 250, 500, 1000]) OVER(ORDER BY total_spend_eur) AS spend_bucket,
  CAST(churned_30d AS INT64) AS label
)
AS
SELECT n_events, total_spend_eur, churned_30d
FROM `my-project.curated.user_features_daily`
WHERE feature_as_of = '2026-01-16';

-- 4. Clustering. COSINE distance so the spend feature does not
--    dominate the Euclidean geometry.
CREATE OR REPLACE MODEL `my-project.curated.customer_segments`
OPTIONS (
  MODEL_TYPE = 'KMEANS',
  K = 5,
  DISTANCE_TYPE = 'COSINE',
  MIN_INITIALIZATION = 10,
  MAX_ITERATIONS = 50
)
AS
SELECT
  total_spend_eur,
  n_orders,
  refund_rate,
  n_channels
FROM `my-project.curated.user_features_daily`
WHERE feature_as_of = '2026-01-16';

-- 5. A time-series forecast on the hourly revenue series.
CREATE OR REPLACE MODEL `my-project.curated.revenue_forecast`
OPTIONS (
  MODEL_TYPE = 'FORECAST',
  HORIZON = 24,
  MODEL_OPTIONS = (holl_winters_triple = true, data_frequency = 'per_hour')
)
AS
SELECT
  TIMESTAMP_MICROS(CAST(time_sec AS INT64)) AS time_series_timestamp,
  revenue_eur AS value
FROM `my-project.curated.hourly_revenue`
WHERE time_series_timestamp BETWEEN
      TIMESTAMP('2026-01-01 00:00:00') AND TIMESTAMP('2026-01-14 23:00:00');
```

### Exercise 3 — Evaluating and reading the model

```sql
-- The headline metrics.
SELECT
  precision, recall, f1_score, accuracy,
  log_loss, roc_auc, pr_auc
FROM ML.EVALUATE(MODEL `my-project.curated.churn_model`);

-- The full ROC curve, for choosing a threshold.
SELECT
  false_positive_rate, true_positive_rate,
  precision, recall, thresholds
FROM ML.ROC(
  MODEL `my-project.curated.churn_model`,
  TABLE `my-project.curated.churn_test`
)
ORDER BY false_positive_rate;

-- The PR curve, which is the more informative one on imbalanced data.
SELECT
  precision, recall, thresholds
FROM ML.PRC(
  MODEL `my-project.curated.churn_model`,
  TABLE `my-project.curated.churn_test`
)
ORDER BY recall DESC;

-- Feature importances. Read weighted_average_gain to compare features
-- with different split frequencies.
SELECT
  feature_name,
  importance,
  weighted_gain,
  weighted_average_gain
FROM ML.FEATURE_IMPORTANCES(MODEL `my-project.curated.churn_model`)
ORDER BY weighted_average_gain DESC;

-- The linear model's coefficients. This is the interpretability that
-- the boosted tree does not give you.
SELECT * FROM ML.WEIGHTS(MODEL `my-project.curated.ltv_linear`);

-- The cluster centroids, to see what the clusters actually are.
SELECT * FROM ML.EVALUATE(MODEL `my-project.curated.customer_segments`);
```

### Exercise 4 — Scoring, and the threshold decision

```sql
-- Batch scoring with the TABLE(...) form.
CREATE OR REPLACE TABLE `my-project.curated.churn_scores`
AS
SELECT
  user_id,
  predicted_churned_30d AS churn_predicted,
  predicted_churned_30d_probs[OFFSET(0)].prob AS churn_probability
FROM ML.PREDICT(
  MODEL `my-project.curated.churn_model`,
  (SELECT * FROM `my-project.curated.scoring_batch`)
);

-- The business query: who to call, ranked, with the value attached.
-- The threshold comes from the PR curve and the cost ratio, not
-- from the default of 0.5.
SELECT
  s.user_id,
  ROUND(s.churn_probability, 4) AS churn_probability,
  u.total_spend_eur,
  u.region,
  u.channel
FROM `my-project.curated.churn_scores` s
JOIN `my-project.curated.user_features_daily` u
  ON s.user_id = u.user_id
WHERE u.feature_as_of = '2026-01-16'
  AND s.churn_probability >= 0.35
ORDER BY s.churn_probability DESC
LIMIT 1000;

-- Scoring a single row with STRUCT.
SELECT ML.PREDICT(
  MODEL `my-project.curated.churn_model`,
  STRUCT(
    14 AS n_events,
    3 AS n_orders,
    0 AS n_refunds,
    482.15 AS total_spend_eur,
    160.72 AS avg_order_value_eur,
    0.0714 AS refund_rate,
    1 AS n_channels,
    'EMEA' AS region,
    'web' AS channel
  )
);
```

### Exercise 5 — The scoring table schema contract

The most common runtime error, and how to prevent it structurally.

```python
"""Build the scoring table to match the model's input schema exactly.

The rule: derive the column list from the model, never from a
hand-maintained list that can drift.
"""

MODEL_FEATURES = [
    "n_events", "n_orders", "n_refunds", "total_spend_eur",
    "avg_order_value_eur", "refund_rate", "n_channels",
    "region", "channel",
]

# The types BigQuery expects. Getting INT64 vs FLOAT64 wrong is a
# schema error, not a silent coercion.
MODEL_TYPES = {
    "n_events": "INT64",
    "n_orders": "INT64",
    "n_refunds": "INT64",
    "total_spend_eur": "FLOAT64",
    "avg_order_value_eur": "FLOAT64",
    "refund_rate": "FLOAT64",
    "n_channels": "INT64",
    "region": "STRING",
    "channel": "STRING",
}


def build_scoring_query(table, feature_as_of):
    """Generate the projection that exactly matches the model schema."""
    projections = ",\n  ".join(
        f"CAST({col} AS {MODEL_TYPES[col]}) AS {col}"
        for col in MODEL_FEATURES
    )
    return f"""
CREATE OR REPLACE TABLE `{table}` AS
SELECT
  user_id,
  {projections}
FROM `my-project.curated.user_features_daily`
WHERE feature_as_of = '{feature_as_of}'
"""


def verify_model_schema(model_features, model_types):
    """Assert the local contract matches what the model expects.

    In production this list comes from ML.FEATURE_IMPORTANCES or from
    the model's own schema, and the check runs in CI.
    """
    assert set(model_features) == set(MODEL_FEATURES), (
        f"feature mismatch: model={sorted(model_features)} "
        f"local={sorted(MODEL_FEATURES)}"
    )
    for col in model_features:
        assert col in model_types, f"missing type for {col}"
    return True


def check_scoring_table_schema(scoring_columns):
    """Catch a scoring table that drifted from the model's schema."""
    expected = set(MODEL_FEATURES)
    received = set(scoring_columns)
    missing = expected - received
    extra = received - expected
    if missing:
        raise ValueError(f"scoring table missing model features: {sorted(missing)}")
    if extra:
        raise ValueError(
            f"scoring table has extra columns the model does not accept: "
            f"{sorted(extra)}"
        )
    return True


print(build_scoring_query("my-project.curated.scoring_batch", "2026-01-16"))
```

### Exercise 6 — The cost comparison, BigQuery ML vs Vertex AI

```python
import sys
sys.path.insert(0, "project/core")

from cost_model import estimate, VERTEX_AI_TRAINING_PER_NODE_HOUR

print("=" * 70)
print("COST COMPARISON: BigQuery ML vs Vertex AI, monthly")
print("=" * 70)

# --- Vertex AI path ---
training_hours = 4
vertex_training = estimate(
    "vertex-ai", training_node_hours=training_hours, monthly=False
)
print(f"\nVertex AI training ({training_hours} node-hours): "
      f"${vertex_training.total:,.2f}")
print(f"  (${VERTEX_AI_TRAINING_PER_NODE_HOUR}/node-hour)")

# The endpoint: always on, 1 replica. BigQuery ML has no equivalent.
ENDPOINT_MONTHLY = 292.00
print(f"Vertex AI endpoint (1 replica, always on): ${ENDPOINT_MONTHLY:,.2f}")
vertex_total = vertex_training.total + ENDPOINT_MONTHLY
print(f"Vertex AI monthly total: ${vertex_total:,.2f}")

# --- BigQuery ML path ---
# The CREATE MODEL runs on BigQuery's own slots.
TRAINING_SLOT_HOURS = 30
bq_training = estimate("bigquery", slot_hours=TRAINING_SLOT_HOURS, monthly=False)
print(f"\nBigQuery ML training ({TRAINING_SLOT_HOURS} slot-hours): "
      f"${bq_training.total:,.2f}")
for line in bq_training.lines:
    print(f"  {line.label:30s} {line.quantity:8.1f} {line.unit:16s} ${line.cost:8.2f}")

# Scoring: a query reading a 100 MB table, scoring 1M rows.
SCORING_TB = 0.0001
bq_scoring = estimate("bigquery", scanned_tb=SCORING_TB, monthly=False)
print(f"\nBigQuery ML scoring ({SCORING_TB} TB scanned): "
      f"${bq_scoring.total:,.2f}")

bq_total = bq_training.total + bq_scoring.total
print(f"BigQuery ML monthly total: ${bq_total:,.2f}")

print(f"\nRatio: Vertex AI is {vertex_total / bq_total:.0f}x more expensive")

# --- The year-over-year view, with tuning included ---
TRIALS = 20
tuning_hours = TRIALS * training_hours
yearly_vertex = (
    (vertex_training.total + tuning_hours * VERTEX_AI_TRAINING_PER_NODE_HOUR)
    * 12
    + ENDPOINT_MONTHLY * 12
)
yearly_bq = (bq_training.total * 12) + (bq_scoring.total * 12)
print(f"\nAnnual, including {TRIALS}-trial tuning each month:")
print(f"  Vertex AI : ${yearly_vertex:,.2f}")
print(f"  BigQuery ML: ${yearly_bq:,.2f}")
print(f"  Difference: ${yearly_vertex - yearly_bq:,.2f}/year")

# --- What BigQuery ML cannot do ---
print("\n" + "=" * 70)
print("WHERE BIGQUERY ML CANNOT GO")
print("=" * 70)
print("  Online prediction with sub-second latency  -> Vertex AI endpoint")
print("  Custom preprocessing in Python            -> Vertex AI custom job")
print("  Bayesian hyperparameter search            -> Vertex AI AutoML Tables")
print("  Native drift/skew monitoring              -> Vertex AI monitoring")
print("  Image, audio, or raw-text inputs          -> Vertex AI / prebuilt APIs")
print("  Transformers, embeddings, ranking models   -> Vertex AI custom training")
```

### Exercise 7 — The drift monitor, written as SQL

Because BigQuery ML has no built-in monitoring, you write it. This is a scheduled query.

```sql
-- Compare the live score distribution against the training baseline.
-- Run this daily. A large divergence means the world changed or the
-- pipeline broke.
WITH
baseline AS (
  SELECT
    churn_probability,
    NTILE(10) OVER (ORDER BY churn_probability) AS decile
  FROM `my-project.curated.churn_scores_baseline`
),
current AS (
  SELECT
    churn_probability,
    NTILE(10) OVER (ORDER BY churn_probability) AS decile
  FROM `my-project.curated.churn_scores`
  WHERE scored_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
),
baseline_dist AS (
  SELECT decile, COUNT(*) AS n, COUNT(*) / SUM(COUNT(*)) OVER () AS pct
  FROM baseline GROUP BY decile
),
current_dist AS (
  SELECT decile, COUNT(*) AS n, COUNT(*) / SUM(COUNT(*)) OVER () AS pct
  FROM current GROUP BY decile
)
SELECT
  b.decile,
  ROUND(b.pct, 4) AS baseline_pct,
  ROUND(c.pct, 4) AS current_pct,
  ROUND((c.pct - b.pct) * (
    LN(GREATEST(c.pct, 0.0001) / GREATEST(b.pct, 0.0001))
  ), 6) AS psi_contribution
FROM baseline_dist b
JOIN current_dist c USING (decile)
ORDER BY b.decile;

-- The positive-rate alarm. Cheapest, loudest, earliest signal.
SELECT
  COUNTIF(churn_probability >= 0.35) / COUNT(*) AS positive_rate,
  (SELECT COUNTIF(churn_probability >= 0.35) / COUNT(*)
   FROM `my-project.curated.churn_scores_baseline`) AS baseline_rate
FROM `my-project.curated.churn_scores`
WHERE scored_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY);

-- Volume guard. A model that stopped scoring looks like a model that
-- predicts the majority class, which looks like a high-accuracy model.
SELECT
  COUNT(*) AS scored_rows,
  COUNT(DISTINCT user_id) AS distinct_users,
  MIN(scored_at) AS first_score,
  MAX(scored_at) AS last_score
FROM `my-project.curated.churn_scores`
WHERE scored_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY);
```

### Exercise 8 — Exporting to Vertex AI for online serving

The hybrid pattern. Train in the warehouse, serve on an endpoint.

```sql
-- 1. Export the BigQuery ML model.
EXPORT MODEL OPTIONS (
  URI = 'gs://my-project-vertex-models/churn/export/',
  FORMAT = 'TENSORFLOW_SAVED_MODEL'
)
MODEL `my-project.curated.churn_model`;
```

```python
def export_and_deploy(bucket_uri, endpoint_name="churn-endpoint"):
    """Upload the exported BigQuery ML model and deploy it online.

    This is the pattern that gets BigQuery ML's cheap training AND
    Vertex AI's low-latency serving. The two are not mutually
    exclusive.
    """
    from google.cloud import aiplatform

    aiplatform.init(project=PROJECT_ID, location=REGION)

    uploaded = aiplatform.Model.upload(
        display_name="churn-model-from-bqml",
        artifact_uri=bucket_uri.rstrip("/"),
        serving_container_image_uri=(
            "us-docker.pkg.dev/vertex-ai/prediction/tf2-cpu.2-15:latest"
        ),
    )

    endpoint = aiplatform.Endpoint(
        endpoint_name=endpoint_name, project=PROJECT_ID, location=REGION
    )
    endpoint.deploy(
        model=uploaded,
        machine_type="n1-standard-4",
        min_replica_count=1,
        max_replica_count=10,
        traffic_split={"0": 100},
        sync=True,
    )
    return endpoint
```

**The parity check that must accompany this pattern.** The BigQuery ML model was trained on features built by one SQL query. The Vertex endpoint receives features built by your application code. **They must be the same definition.** The way to guarantee this is to have the application read the features from the same view the training table was built from.

```sql
-- The single source of truth. Both the training table and the
-- application read from this view.
CREATE OR REPLACE VIEW `my-project.curated.v_features_current` AS
SELECT
  user_id,
  n_events,
  n_orders,
  n_refunds,
  total_spend_eur,
  avg_order_value_eur,
  refund_rate,
  n_channels,
  region,
  channel
FROM `my-project.curated.user_features_daily`
WHERE feature_as_of = (
  SELECT MAX(feature_as_of) FROM `my-project.curated.user_features_daily`
);
```

---

## 🛠️ Common Errors and Fixes

### 1. `google.api_core.exceptions.InvalidArgument: Table name "..." missing dataset while no default dataset is set in the request`

**Symptom.**

```text
google.api_core.exceptions.InvalidArgument: Table name "events" missing dataset while no default dataset is set in the request
```

**Cause.** A query or a `ML.PREDICT` call referenced an unqualified table name, relying on a default dataset set in a notebook context that does not exist in your scheduled query or pipeline.

**Fix.** Fully qualify every table reference:

```sql
-- Wrong
SELECT * FROM events;

-- Right
SELECT * FROM `my-project.curated.events`;
```

### 2. `google.api_core.exceptions.InvalidArgument: Schema mismatch: Model expects columns ... but got ...`

**Symptom.**

```text
google.api_core.exceptions.InvalidArgument: Schema mismatch: Model expects columns
[n_events, n_orders, total_spend_eur, refund_rate, region, channel] but got
[user_id, n_events, n_orders, total_spend_eur, refund_rate, region, channel]
```

**Cause.** The scoring table contains a column the model was not trained on — most often `user_id`, carried through from the feature table.

**Fix.** Project exactly the model's features, or use `EXCEPT`:

```sql
SELECT *
FROM ML.PREDICT(
  MODEL `my-project.curated.churn_model`,
  (SELECT * EXCEPT(user_id, feature_as_of) FROM `my-project.curated.scoring_batch`)
);
```

**The structural fix:** derive the scoring table's projection from the model's own schema rather than from `SELECT *`. See Exercise 5.

### 3. `ValueError: Invalid feature` / `InvalidArgument: Column not present in feature columns`

**Symptom.**

```text
google.api_core.exceptions.InvalidArgument: Column not present in feature columns: n_refunds
```

**Cause.** Two distinct problems with the same symptom:

- The training table and the scoring table have different columns.
- With `AS SELECT` (rather than `TRANSFORM`), a column present in the training `SELECT` that is not in the model's feature list.

**Fix.** Use `TRANSFORM` so the feature set is explicit by construction:

```sql
CREATE OR REPLACE MODEL `my-project.curated.churn_model`
TRANSFORM(
  n_events,
  n_orders,
  n_refunds,
  total_spend_eur,
  refund_rate,
  region,
  channel,
  CAST(churned_30d AS INT64) AS label
)
OPTIONS (
  MODEL_TYPE = 'BOOSTED_TREE_CLASSIFIER',
  INPUT_LABEL_COLS = ['label']
)
AS SELECT * FROM `my-project.curated.user_features_daily`
WHERE feature_as_of = '2026-01-16';
```

### 4. The model has a 0.99 AUC and production performance is at chance

**Symptom.** `ML.EVALUATE` reports `roc_auc = 0.993`. The live scores are random.

**Cause.** Leakage. With `DATA_SPLIT_METHOD = 'AUTO'` (the default), BigQuery does a **random** split — so for a temporal problem it trains on the future to predict the past. Worse, if a feature was computed without an as-of predicate, the label leaks directly.

**Fix.** Always use `'CUSTOM'` with an explicit split column, and apply the as-of filter in the feature SQL:

```sql
OPTIONS (
  MODEL_TYPE = 'BOOSTED_TREE_CLASSIFIER',
  INPUT_LABEL_COLS = ['churned_30d'],
  DATA_SPLIT_METHOD = 'CUSTOM',
  DATA_SPLIT_COLUMN = 'is_test',
  NUM_TRIALS = 20
)
```

And in the feature-building SQL:

```sql
-- The as-of predicate. Without it you have leakage.
SELECT
  user_id,
  COUNTIF(event_type = 'order') AS n_orders,
  SUM(IF(event_type = 'order', amount_eur, 0)) AS total_spend_eur
FROM `my-project.curated.events`
WHERE event_dt < '2026-01-16'      -- <-- this
GROUP BY user_id;
```

### 5. `FORECAST` produces nonsense or errors

**Symptom.**

```text
google.api_core.exceptions.InvalidArgument: The time series has gaps or is not evenly spaced
```

**Cause.** ARIMA requires a **regular, gapless** time series. If your hourly data has missing buckets, the model cannot fit.

**Fix.** Fill the gaps with a `generate_series` grid and a left join:

```sql
WITH grid AS (
  SELECT TIMESTAMP_SECONDS(ts) AS time_series_timestamp
  FROM UNNEST(GENERATE_ARRAY_ARRAY(
    TIMESTAMP_SECONDS(TIMESTAMP('2026-01-01 00:00:00')),
    TIMESTAMP_SECONDS(TIMESTAMP('2026-01-14 23:00:00')),
    INTERVAL 1 HOUR
  )) AS ts
),
series AS (
  SELECT time_series_timestamp, revenue_eur
  FROM `my-project.curated.hourly_revenue`
)
SELECT
  grid.time_series_timestamp,
  IFNULL(series.revenue_eur, 0) AS value
FROM grid
LEFT JOIN series USING (time_series_timestamp)
ORDER BY time_series_timestamp;
```

Also set `data_frequency` correctly (`'per_hour'` for hourly data) so the model knows the seasonality period.

### 6. `KMEANS` returns clusters that make no sense

**Symptom.** Four clusters that are just spend tiers, and one cluster with everything else.

**Cause.** Euclidean distance on features with wildly different scales. `total_spend_eur` (range 0-10,000) dominates `refund_rate` (range 0-0.1).

**Fix.** Either normalise the features before clustering, or use cosine distance:

```sql
OPTIONS (
  MODEL_TYPE = 'KMEANS',
  K = 5,
  DISTANCE_TYPE = 'COSINE',
  MIN_INITIALIZATION = 10
)
```

And inspect the centroids to confirm the clusters are meaningful:

```sql
SELECT * FROM ML.EVALUATE(MODEL `my-project.curated.customer_segments`);
```

### 7. `ML.PREDICT` returns the wrong class for a multiclass model

**Symptom.** `predicted_label_probs[OFFSET(0)].prob` is not the probability of the predicted class.

**Cause.** `predicted_<label>_probs` is an **ARRAY of STRUCTs sorted descending by probability**, not a fixed-position array. `[OFFSET(0)]` is the highest-probability class, which is normally the prediction — but if you are reading the probability of a *specific* class, you must search for it by label rather than index.

**Fix.**

```sql
SELECT
  predicted_label,
  (SELECT p.prob
   FROM UNNEST(predicted_label_probs) AS p
   WHERE p.label = predicted_label) AS predicted_prob,
  (SELECT p.prob
   FROM UNNEST(predicted_label_probs) AS p
   WHERE p.label = 'churned') AS churn_probability
FROM ML.PREDICT(
  MODEL `my-project.curated.churn_model`,
  (SELECT * FROM `my-project.curated.scoring_batch`)
);
```

---

## 💡 Production Notes

- **Always use `DATA_SPLIT_METHOD = 'CUSTOM'` with an explicit boolean split column.** The `'AUTO'` default is a random split, which is wrong for every temporal problem and hides leakage behind a beautiful score.

- **Use `TRANSFORM` rather than `AS SELECT` so the feature list is explicit.** With `AS SELECT`, every column in the query becomes a feature — including `user_id`, which trees will memorise without any visible sign.

- **Apply the as-of predicate in the feature-building SQL, not in the model statement.** The leakage happens in the feature table; the model statement only amplifies it.

- **Fit a `LINEAR_REG` baseline before anything else.** If the boosted tree beats it by 0.01 AUC, the boosted tree is not earning its operational complexity.

- **Set `NUM_TRIALS` above 1.** The default of 1 means no hyperparameter search happened. Twenty trials on BigQuery slots is cheap compared with the same search on Vertex node-hours.

- **Read `weighted_average_gain`, not `importance`, when comparing features.** `importance` counts split frequency and over-weights features that offer many small splits.

- **Pick the threshold from the PR curve and the cost ratio, then apply it everywhere.** `ML.EVALUATE` reports metrics at the default threshold of 0.5, which is almost never the right operating point.

- **Build the scoring table from a view, not from `SELECT *`.** A view that projects exactly the model's features is the structural defence against schema mismatch errors and against feature drift between the model and the scorer.

- **Monitor BigQuery ML yourself.** There is no built-in drift detection. Write the scheduled queries: the PR curve on a fixed test set, the positive-rate check, and the volume guard. Chapter 8.1's PSI implementation applies directly.

- **Score in bulk with a scheduled query, not a per-row job.** `ML.PREDICT` over a million rows is one query; a loop over a million rows is a disaster. Always the set-based form.

- **Export to Vertex AI when you need online serving.** `EXPORT MODEL` writes a TensorFlow saved model you can upload to the Model Registry and deploy to an endpoint. Train where the data is, serve where the latency is.

- **Watch the BigQuery ML feature set for accidental growth.** A `SELECT *` in a model statement silently adds a column to the feature set, which changes the model without changing the code. Review the `MODEL` system table after every training run.

---

## 🔑 Key Takeaways

- **BigQuery ML trains and scores with SQL.** `CREATE MODEL` and `ML.PREDICT`, no container, no pipeline, no endpoint.
- **The three reasons it exists:** no data movement (trains on the data in place), no serving infrastructure (a query, not an endpoint), and the model is a first-class queryable object.
- **BigQuery ML vs AutoML Tables:** if the scoring is batch, use BigQuery ML. If you need sub-second online predictions, you need Vertex AI. If you need Python-level preprocessing or a wider search, use Vertex AI.
- **BigQuery ML supports model types AutoML Tables does not** — `FORECAST` (ARIMA), `KMEANS`, `LINEAR_REG`, `DNN_CLASSIFIER`. For ARIMA inside the warehouse, BigQuery ML is the only option.
- **`AS SELECT` makes every column a feature.** Including `user_id`. Use `TRANSFORM` so the feature set is explicit by construction.
- **`DATA_SPLIT_METHOD = 'AUTO'` is a random split** and is wrong for every temporal problem. Use `'CUSTOM'` with an explicit boolean `is_test` column, always.
- **The model types:** `LOGISTIC_REGRESSION` (with `L1_REG`/`L2_REG`), `LINEAR_REG`, `KMEANS` (with `K`, `DISTANCE_TYPE`, `MIN_INITIALIZATION`), `TREE_REGRESSOR`, `BOOSTED_TREE_CLASSIFIER` (XGBoost, with `NUM_TRIALS`, `MAX_TREE_DEPTH`, `LEARN_RATE`), `DNN_CLASSIFIER` (with `HIDDEN_UNITS`, `DROPOUT`), `FORECAST` (with `HORIZON`, `MODEL_OPTIONS`).
- **`NUM_TRIALS = 1` means no hyperparameter search happened.** Set it to 20; it runs on BigQuery slots, not Vertex node-hours.
- **`ML.EVALUATE`** gives precision, recall, F1, accuracy, log loss, ROC-AUC and PR-AUC at the default threshold. **`ML.ROC`** and **`ML.PRC`** give the full curves — which is where the threshold comes from.
- **`ML.FEATURE_IMPORTANCES`** returns three measures: `importance` (split count), `weighted_gain` (total gain), `weighted_average_gain` (gain normalised by use). **Compare features on `weighted_average_gain`.**
- **`ML.PREDICT` output:** `predicted_<label>` plus `predicted_<label>_probs` — an ARRAY of STRUCTs **sorted descending by probability**. To get a specific class's probability, search by label, do not index.
- **`ML.FEATURES.*` and `ML.BUCKETIZE`/`ML.ONE_HOT_ENCODER`** all require the `OVER (ORDER BY ...)` clause.
- **Feature engineering is inversely proportional to model capacity.** Trees need none; logistic regression needs bucketising and one-hot encoding; DNNs need raw numerics.
- **Aggregate features carry the signal** — orders in 30 days, spend, recency — and must be computed with an explicit as-of predicate.
- **The cost advantage is roughly 150×.** Vertex AI ≈ $307/month (training + always-on endpoint); BigQuery ML ≈ $2/month. **The endpoint is most of the difference.**
- **The operational surface is the real win:** no container, no training code, no pipeline definition, no registry entry, no endpoint, no serving code, no monitoring config. A scheduled query.
- **BigQuery ML's limits:** no online prediction, no custom training code, no Bayesian search, no feature store or skew management, no unstructured inputs, a fixed model set, and manual monitoring.
- **The hybrid that gets both:** train with BigQuery ML, `EXPORT MODEL` to GCS, upload to the Vertex AI Model Registry, deploy to an endpoint for online serving. Train where the data is; serve where the latency is.
- **Structure beats discipline.** A view that projects exactly the model's features prevents schema-mismatch errors and feature drift between the model and the scorer.

---

## 📚 Practice Exercises

1. **The full BigQuery ML pipeline.** Using `project/core/pipeline_logic.py` and `sample_data/events.csv`, build the feature table with an as-of filter and an explicit `is_test` split column. Write the `CREATE MODEL` statements for `LINEAR_REG`, `LOGISTIC_REGRESSION` with `TRANSFORM`, and `BOOSTED_TREE_CLASSIFIER`. Then write the scoring query and the business query. Predict the `roc_auc` of each and explain why they would differ.

2. **Threshold selection from the PR curve.** Write a SQL query that produces the PR curve for the churn model, then a Python function that takes the curve rows and a cost ratio (false positive €40, false negative €140) and returns the threshold that minimises expected cost. Compare it to the default threshold of 0.5 and explain the difference in terms of who gets called.

3. **Leakage in BigQuery ML.** Write three versions of the feature table: (a) with the as-of predicate, (b) with the predicate but a random `is_test` split, (c) without the predicate. State what `ML.EVALUATE` would report for each and why. Then write the CI test that would catch the difference.

4. **Model selection memo.** Using the course cost module, write a memo comparing three approaches for a daily churn score over 1 million users: (a) BigQuery ML `BOOSTED_TREE_CLASSIFIER` with `NUM_TRIALS = 20`, (b) Vertex AI AutoML Tables with an endpoint, (c) BigQuery ML trained then exported to a Vertex endpoint. Give the monthly cost of each from `cost_model`, the latency, the operational surface, and the conditions under which each is right.

5. **KMEANS on customer segments.** Build a clustering model over the user features. Try both `EUCLIDEAN` and `COSINE` distance. Describe the resulting cluster profiles and explain the difference. Then propose a validation: how would you check that the clusters are useful, given that cluster labels are not ground truth?

6. **The forecast model.** Build a `FORECAST` model over the hourly revenue series from the course pipeline (24 windows). Write the query that fills any gaps with a `generate_series` grid. Set `HORIZON` and `data_frequency`. Then explain why a 24-hour horizon is safer than a 90-day one for this series, and what a 90-day forecast would need to be trustworthy.

7. **Schema contract and CI.** Write the CI check that reads the model's feature list from `ML.FEATURE_IMPORTANCES` and compares it against the scoring view's column list, failing on any difference in either direction. Then write the migration path if a feature is legitimately added: how do you retrain, validate, and promote without a scoring window where the old and new schemas disagree?

8. **The drift monitor in SQL.** Write the three scheduled queries for a BigQuery ML model: the PSI calculation over score deciles, the positive-rate comparison against the baseline, and the volume guard. Then write the Composer DAG that runs them and the alerting policy — what pages a human, what opens a ticket, and what triggers a retraining of the BigQuery ML model.

---

## 📖 Further Reading

- [BigQuery ML — Introduction](https://cloud.google.com/bigquery/docs/bqml-introduction)
- [BigQuery ML — CREATE MODEL Statement](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create)
- [BigQuery ML — Model Types and Model Options](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create)
- [BigQuery ML — ML.PREDICT](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-predict)
- [BigQuery ML — ML.EVALUATE](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-evaluate)
- [BigQuery ML — ML.FEATURES Functions](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-feature)
- [BigQuery ML — Training and Evaluating Models](https://cloud.google.com/bigquery/docs/evaluate-overview)
- [Vertex AI AutoML — Tabular Data Classification and Regression](https://cloud.google.com/vertex-ai/docs/tabular-data/classification-regression/overview)
