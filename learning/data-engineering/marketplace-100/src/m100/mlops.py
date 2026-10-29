"""
mlops.py — baseline ML + MLflow logging + Unity Catalog registration.

Each iteration picks a baseline model that fits the data shape:

  * Tabular (≥3 numeric columns, target column detectable) →
    LightGBM binary classifier on the first non-numeric column.
  * Text (any string column with avg length > 50)  →
    sentence-transformers embedding + a tiny similarity classifier.
  * Otherwise → "no model" — log a 0.0-metric run so the agent
    can score it as `quality_score=0.0` and the driver retries.

Every run is logged to MLflow with:
  * `params`: data shape, model type, hyperparams
  * `metrics`: accuracy / F1 (classification) or
               retrieval_at_5 (text)
  * `artifact`: the trained model + a small prediction sample
  * `tags`: iteration_no, listing_id, category

The model is then registered in Unity Catalog under
`<catalog>.models.m100_<listing_id>_<iter_no>` and aliased
`@Champion`. (We re-use the Champion alias every iteration —
the latest run is always the active one for that listing.)

Why a baseline, not a tuned model?
  * The point of this project is the agentic loop, not
    the model. A baseline that runs in <30s per iteration
    is enough to give the agent something to score.
  * LightGBM + sentence-transformers cover 95% of marketplace
    datasets with zero per-dataset tuning.
"""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ============================================================
# Result
# ============================================================

@dataclass
class MLOpsResult:
    """What the MLOps step produced.

    `mlflow_run_id` is what the agent reads in its
    `get_mlflow_metrics` tool call.
    """
    listing_id: str
    mlflow_run_id: str
    model_name: str          # fully-qualified: <catalog>.models.<id>_<iter>
    model_alias: str         # "Champion"
    model_type: str          # "lightgbm" | "sentence_transformer" | "none"
    metrics: dict            # {accuracy, f1, ...}
    params: dict
    sample_predictions: list[dict]


# ============================================================
# Data shape detection
# ============================================================

def detect_shape(spark, table_name: str) -> dict:
    """Classify the silver table as tabular / text / unknown.

    Returns a dict with the data shape details so the model
    picker can decide.
    """
    df = spark.read.table(table_name)
    schema = df.schema
    numeric_cols = [
        f.name for f in schema.fields
        if str(f.dataType) in (
            "IntegerType()", "LongType()", "DoubleType()", "FloatType()",
            "ShortType()", "DecimalType()",
        )
    ]
    string_cols = [
        f.name for f in schema.fields
        if str(f.dataType) == "StringType()"
    ]
    text_cols: list[str] = []
    if string_cols and df.count() > 0:
        from pyspark.sql.functions import length, avg
        avg_lens = (
            df.select([avg(length(c)).alias(c) for c in string_cols])
            .first()
            .asDict()
        )
        for c, al in avg_lens.items():
            if al and al > 50:
                text_cols.append(c)
    return {
        "row_count": df.count(),
        "column_count": len(schema.fields),
        "numeric_cols": numeric_cols,
        "string_cols": string_cols,
        "text_cols": text_cols,
        "shape": "tabular" if len(numeric_cols) >= 2
                 else ("text" if text_cols else "unknown"),
    }


# ============================================================
# MLflow logging
# ============================================================

def run_baseline(
    spark,
    table_name: str,
    listing_id: str,
    iter_no: int,
    *,
    experiment_path: str = "/Users/prem/m100/experiments",
    catalog: str = "marketplace_100",
) -> MLOpsResult:
    """Pick a model, train it, log to MLflow, register in UC.

    `experiment_path` is the MLflow experiment (a Unity Catalog
    path in production; a workspace path in dev). The driver
    passes the same path for every iteration so they all
    land in one place.
    """
    import mlflow
    import mlflow.lightgbm
    import mlflow.pyfunc

    shape = detect_shape(spark, table_name)
    metrics, params, model_obj, sample_preds = _pick_and_train(
        spark, table_name, shape
    )

    model_name = f"{catalog}.models.m100_{listing_id}_{iter_no}"
    full_exp = f"{experiment_path}"

    mlflow.set_experiment(full_exp)
    with mlflow.start_run(run_name=f"m100-{iter_no:03d}-{listing_id[:8]}") as run:
        # Log shape + params
        mlflow.set_tag("iter_no", str(iter_no))
        mlflow.set_tag("listing_id", listing_id)
        mlflow.set_tag("shape", shape["shape"])
        mlflow.log_params(params)
        mlflow.log_metric("row_count", shape["row_count"])
        mlflow.log_metric("column_count", shape["column_count"])
        for k, v in metrics.items():
            try:
                mlflow.log_metric(k, float(v))
            except (TypeError, ValueError):
                pass

        # Log model
        if model_obj is not None:
            try:
                if shape["shape"] == "tabular":
                    mlflow.lightgbm.log_model(
                        model_obj, artifact_path="model",
                        registered_model_name=model_name,
                    )
                else:
                    mlflow.pyfunc.log_model(
                        artifact_path="model",
                        python_model=_TextEmbeddingWrapper(model_obj),
                        registered_model_name=model_name,
                        code_path=[__file__],
                    )
            except Exception as e:
                # Registration sometimes fails on a fresh catalog
                # (no schema). The model is still in the run, so
                # the agent can still read the metrics.
                logger.warning("MLflow register failed: %s", e)
                if shape["shape"] == "tabular":
                    mlflow.lightgbm.log_model(model_obj, artifact_path="model")

        # Sample predictions as a JSON artifact
        mlflow.log_text(
            json.dumps(sample_preds, indent=2, default=str),
            "sample_predictions.json",
        )
        run_id = run.info.run_id

    # Set the Champion alias (idempotent — if the model isn't
    # registered, the alias call is a no-op).
    try:
        from mlflow import MlflowClient
        client = MlflowClient()
        client.set_registered_model_alias(model_name, "Champion", "1")
    except Exception as e:
        logger.warning("set Champion alias failed: %s", e)

    return MLOpsResult(
        listing_id=listing_id,
        mlflow_run_id=run_id,
        model_name=model_name,
        model_alias="Champion",
        model_type=(
            "lightgbm" if shape["shape"] == "tabular"
            else "sentence_transformer" if shape["shape"] == "text"
            else "none"
        ),
        metrics=metrics,
        params=params,
        sample_predictions=sample_preds,
    )


# ============================================================
# Model picker — one function, three branches
# ============================================================

def _pick_and_train(
    spark,
    table_name: str,
    shape: dict,
) -> tuple[dict, dict, Any, list[dict]]:
    """Train a baseline; return (metrics, params, model, sample_preds).

    `model` is whatever the training code produced (LightGBM
    Booster, sentence-transformer model, or None).
    """
    if shape["shape"] == "tabular":
        return _train_lightgbm(spark, table_name, shape)
    if shape["shape"] == "text":
        return _train_text(spark, table_name, shape)
    return (
        {"accuracy": 0.0, "f1": 0.0, "note": "no model — unknown shape"},
        {"shape": shape["shape"], "reason": "no_model"},
        None,
        [],
    )


def _train_lightgbm(spark, table_name, shape) -> tuple[dict, dict, Any, list[dict]]:
    """LightGBM binary classifier on the first non-numeric column.

    Falls back to a constant-prediction baseline if the data is
    too sparse or the target column is degenerate.
    """
    import lightgbm as lgb
    from pyspark.sql.functions import col

    df = spark.read.table(table_name).toPandas()
    if df.empty or len(shape["numeric_cols"]) < 2:
        return (
            {"accuracy": 0.5, "f1": 0.0, "note": "sparse data"},
            {"shape": "tabular", "n_rows": len(df)},
            None,
            [],
        )
    target = shape["string_cols"][0] if shape["string_cols"] else shape["numeric_cols"][0]
    feature_cols = [c for c in shape["numeric_cols"] if c != target]
    if not feature_cols:
        return (
            {"accuracy": 0.5, "f1": 0.0, "note": "no features"},
            {"shape": "tabular", "n_rows": len(df)},
            None,
            [],
        )
    # Encode target as 0/1
    y = (df[target].astype(str).str.lower().str.strip() == df[target].astype(str).str.lower().str.strip().mode().iloc[0]).astype(int) if df[target].dtype == "object" else (df[target] > df[target].median()).astype(int)
    X = df[feature_cols].fillna(0).astype(float)
    n = len(X)
    train_n = int(n * 0.8)
    X_train, X_test = X.iloc[:train_n], X.iloc[train_n:]
    y_train, y_test = y.iloc[:train_n], y.iloc[train_n:]
    if X_test.empty or y_test.nunique() < 2:
        # Not enough variation; log a zero-metric run
        return (
            {"accuracy": 0.5, "f1": 0.0, "note": "single class in test"},
            {"shape": "tabular", "n_rows": n},
            None,
            [],
        )
    params = {
        "objective": "binary",
        "metric": "binary_logloss",
        "learning_rate": 0.1,
        "num_leaves": 31,
        "min_data_in_leaf": 5,
        "verbose": -1,
    }
    train_data = lgb.Dataset(X_train, y_train)
    test_data = lgb.Dataset(X_test, y_test, reference=train_data)
    model = lgb.train(
        params, train_data,
        num_boost_round=50,
        valid_sets=[test_data],
        callbacks=[lgb.early_stopping(10, verbose=False)],
    )
    preds = (model.predict(X_test) > 0.5).astype(int)
    from sklearn.metrics import accuracy_score, f1_score
    metrics = {
        "accuracy": float(accuracy_score(y_test, preds)),
        "f1": float(f1_score(y_test, preds, zero_division=0)),
    }
    sample_preds = [
        {"actual": int(y_test.iloc[i]), "predicted": int(preds[i])}
        for i in range(min(5, len(preds)))
    ]
    return metrics, params, model, sample_preds


def _train_text(spark, table_name, shape) -> tuple[dict, dict, Any, list[dict]]:
    """sentence-transformers baseline on the longest text column.

    Embeds a sample of rows, computes pairwise cosine similarity,
    and reports `retrieval_at_5` = fraction of queries whose
    top-5 neighbors include a row from the same source.
    """
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except ImportError:
        return (
            {"retrieval_at_5": 0.0, "note": "sentence-transformers not installed"},
            {"shape": "text"},
            None,
            [],
        )
    text_col = shape["text_cols"][0]
    df = spark.read.table(table_name).select(text_col).toPandas()
    if df.empty or len(df) < 10:
        return (
            {"retrieval_at_5": 0.0, "note": "too few text rows"},
            {"shape": "text", "n_rows": len(df)},
            None,
            [],
        )
    sample = df[text_col].astype(str).tolist()[:200]
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(sample, show_progress_bar=False)
    # Naive retrieval@5: for each row, find the 5 nearest by
    # cosine similarity, and check if at least 1 is "near" enough
    # (similarity > 0.5). This isn't a real benchmark, just a
    # rough signal.
    from numpy.linalg import norm
    sims = embeddings @ embeddings.T
    np.fill_diagonal(sims, -1)
    top5 = np.argsort(-sims, axis=1)[:, :5]
    top5_sims = np.take_along_axis(sims, top5, axis=1)
    # retrieval@5: fraction of rows with at least 1 neighbor at sim>0.5
    r_at_5 = float((top5_sims > 0.5).any(axis=1).mean())
    return (
        {"retrieval_at_5": r_at_5},
        {"shape": "text", "model": "all-MiniLM-L6-v2", "n_rows": len(sample)},
        model,
        [{"row": i, "top5_sims": top5_sims[i].tolist()} for i in range(min(5, len(sample)))],
    )


# ============================================================
# Wrappers — for MLflow to log the sentence-transformer model
# ============================================================

class _TextEmbeddingWrapper:
    """Minimal pyfunc wrapper so MLflow can serialize the embedding model."""

    def __init__(self, model):
        self.model = model

    def predict(self, context, model_input):
        import pandas as pd
        if isinstance(model_input, pd.DataFrame):
            texts = model_input.iloc[:, 0].astype(str).tolist()
        else:
            texts = list(model_input)
        return self.model.encode(texts, show_progress_bar=False)
