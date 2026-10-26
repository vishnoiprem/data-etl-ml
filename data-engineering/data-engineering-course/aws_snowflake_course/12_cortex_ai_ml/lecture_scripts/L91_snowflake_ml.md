---
l_id: L91
title: Snowflake ML
duration: "7:30"
prereqs: ["L90 - Cortex Analyst"]
---

# L91 — Snowflake ML

> **Author:** Prem Vishnoi &lt;pvishnoi@avilx.com&gt;
> **Section:** 12 — Cortex AI & Machine Learning
> **Duration:** 7:30

## Prereqs

You're comfortable with Python and a Snowflake role that can
create warehouses and use the `SNOWFLAKE.ML` schema.

## Lecture

Snowflake ML is the **classical ML** + **MLOps** layer of the
Cortex story. Two halves:

1. **Cortex ML functions** — pre-built time-series and
   classification functions you call from SQL.
2. **Snowpark ML + the model registry** — bring your own model
   (scikit-learn, XGBoost, lightgbm, PyTorch) and train it on
   warehouse compute.

### Cortex ML functions

```sql
-- Forecast a daily metric
SELECT ts, value, forecast, lower_bound, upper_bound
FROM TABLE(
  SNOWFLAKE.ML.FORECAST(
    INPUT_DATA => SYSTEM$QUERY_REFERENCE('SELECT ts, value FROM raw.daily_sales'),
    TIMESTAMP_COLNAME => 'ts',
    TARGET_COLNAME => 'value',
    FORECAST_HORIZON => 30
  )
);
```

Other built-ins:

- `SNOWFLAKE.ML.CLASSIFICATION` — multi-class.
- `SNOWFLAKE.ML.ANOMALY_DETECTION` — univariate anomaly scoring.
- `SNOWFLAKE.ML.TOP_INSIGHTS` — automated "what changed?"
  analysis for a KPI.

### Snowpark ML: train a custom model

The shape of every Snowpark training job:

```python
# notebooks/train_fraud_model.py
from snowflake.snowpark import Session
from snowflake.ml.registry import Registry
from snowflake.ml.modeling.xgboost import XGBClassifier

session = Session.builder.getOrCreate()

# 1. Pull training data into a Snowpark DataFrame
df = session.table("analytics.gold.fct_transactions_labeled")

# 2. Train on warehouse compute
model = XGBClassifier(
    input_cols=["amount", "merchant_cat", "hour_of_day"],
    label_cols=["is_fraud"],
    output_cols=["prediction"],
)
model.fit(df)

# 3. Register the model
registry = Registry(session=session, database_name="ml", schema_name="prod")
registry.log_model(
    model=model,
    model_name="fraud_classifier",
    version_name="v1",
    conda_dependencies=["xgboost==2.0.0"],
)
```

The training runs on the warehouse you have bound to the session —
no data movement, no separate cluster.

### The model registry

- **Versions.** `fraud_classifier:v1`, `fraud_classifier:v2`.
- **Stages.** `dev`, `staging`, `prod` — promote with
  `registry.get_model("fraud_classifier").default = "v2"`.
- **Lineage.** Every model tracks the table snapshot, the
  warehouse, and the training code that produced it.

### Inference

Two flavors:

```sql
-- Batch inference from SQL
SELECT *,
       fraud_classifier!PREDICT(
         OBJECT_CONSTRUCT(
           'amount',          amount,
           'merchant_cat',    merchant_cat,
           'hour_of_day',     hour_of_day
         )
       ) AS prediction
FROM analytics.gold.fct_transactions_scoring;
```

```python
# Real-time inference from Python
mv = registry.get_model("fraud_classifier").default
result = mv.run(
    pandas.DataFrame([{"amount": 123.45, "merchant_cat": "Grocery", "hour_of_day": 14}]),
    function_name="predict"
)
```

### Feature Store

For features you reuse across many models:

```python
from snowflake.ml.feature_store import FeatureStore, Entity, FeatureView

fs = FeatureStore(
    session=session,
    database="ml",
    name="features",
    default_warehouse="feature_wh",
)

# Define an entity + a feature view
customer = Entity(name="customer", join_keys=["customer_id"])
fs.register_entity(customer)

fv = FeatureView(
    name="customer_features",
    entities=[customer],
    feature_df=session.sql("SELECT customer_id, lifetime_value, ..."),
    timestamp_col="snapshot_ts",
    refresh_freq="1 day",
)
fs.register_feature_view(fv)
```

At inference time, fetch features by entity key with
`fs.generate_training_set(...)` or `fs.get_feature_view(...).fetch()`.

## Key takeaways

- Cortex ML functions cover forecasting, classification, anomaly
  detection, and top-insights from SQL.
- Snowpark ML trains custom models on warehouse compute; the
  registry handles versioning and deployment.
- Feature Store avoids "which table has the right `lifetime_value`
  column?" once you have more than three models.

## What's next

In **L92 — Snowflake Notebooks** we look at the IDE: a Python
notebook that runs against your Snowflake data and writes back
to Snowflake.
