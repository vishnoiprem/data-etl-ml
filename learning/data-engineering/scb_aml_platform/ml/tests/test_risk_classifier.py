"""
Tests for the ML risk classifier.

Covers:
  - build_training_table returns a labeled DataFrame
  - train_model produces a persisted model + metrics + predictions
  - AUC > 0.5 (model is learning something, not random)
  - RiskClassifier inference wrapper loads the trained model
  - predict_proba returns valid probabilities
  - End-to-end: training → inference on new rows
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(HERE))

from scb_aml_platform.data.dummy.generate_dummy_data import main as _gen  # noqa: E402
from scb_aml_platform.aml_engine.rules.rules_engine import run as rules_run  # noqa: E402
from scb_aml_platform.aml_engine.risk_scoring.risk_scoring_engine import run as risk_run  # noqa: E402
from scb_aml_platform.spark.feature_engineering.job3_feature_engineering import run as fe_run  # noqa: E402
from scb_aml_platform.ml.risk_classifier import (  # noqa: E402
    build_training_table, _prepare_X, train_model, RiskClassifier,
)
from scb_aml_platform.config.settings import BASE_DIR, ML_MODEL_DIR  # noqa: E402

DUMMY_DIR = Path(BASE_DIR) / "data" / "dummy"
PROCESSED_DIR = Path(BASE_DIR) / "data" / "processed"
ML_OUTPUT_DIR = Path(BASE_DIR) / "output" / "ml"


@pytest.fixture(scope="module", autouse=True)
def _setup():
    _gen()
    fe_run()
    risk_run()
    rules_run()
    yield


def test_build_training_table_returns_labeled_frame():
    df = build_training_table()
    assert "label" in df.columns
    assert "composite_aml_score" in df.columns
    assert "customer_id" in df.columns
    assert df["label"].isin([0, 1]).all()
    assert df["label"].sum() >= 1, "no positive labels — model cannot learn"


def test_prepare_X_produces_numeric_matrix():
    df = build_training_table()
    X, names = _prepare_X(df)
    assert X.shape[0] == len(df)
    assert X.shape[1] == len(names)
    # No object dtypes (one-hot + numeric coercion)
    assert not any(X.dtypes == object)
    # No NaNs
    assert not X.isna().any().any()


def test_train_model_persists_artifacts():
    out = train_model()
    assert "model_path" in out
    assert "metrics" in out
    assert out["model_path"].exists()
    # Latest pointer exists
    assert (ML_MODEL_DIR / "latest.joblib").exists()
    # Metrics JSON written
    metrics_path = ML_OUTPUT_DIR / "model_metrics.json"
    assert metrics_path.exists()
    # Predictions parquet written
    preds_path = ML_OUTPUT_DIR / "risk_predictions.parquet"
    assert preds_path.exists()
    preds = pd.read_parquet(preds_path)
    assert "ml_risk_proba" in preds.columns
    assert "ml_predicted_high_risk" in preds.columns
    assert preds["ml_risk_proba"].between(0, 1).all()


def test_train_model_learns_something():
    """AUC > 0.5 means the model beats random — basic sanity check."""
    out = train_model()
    auc = out["metrics"]["auc"]
    assert auc > 0.5, f"model AUC {auc} is no better than random"


def test_risk_classifier_inference_round_trip():
    """Train → load → predict on the same frame gives probs in [0,1]."""
    train_model()
    clf = RiskClassifier()
    df = build_training_table()
    proba = clf.predict_proba(df)
    assert len(proba) == len(df)
    assert proba.min() >= 0
    assert proba.max() <= 1
    # Some positive predictions
    assert (proba >= 0.5).sum() >= 1


def test_risk_classifier_aligns_columns():
    """Inference on a DataFrame missing some training columns must
    not crash — missing columns are filled with 0."""
    train_model()
    clf = RiskClassifier()
    # Build a DataFrame with only one feature
    df = build_training_table()[["customer_id", "txn_count_30d"]]
    proba = clf.predict_proba(df)
    assert len(proba) == len(df)
    assert proba.min() >= 0 and proba.max() <= 1


def test_risk_classifier_raises_when_model_missing(monkeypatch, tmp_path):
    """If latest.joblib doesn't exist, RiskClassifier must raise FileNotFoundError."""
    from scb_aml_platform.ml import risk_classifier
    monkeypatch.setattr(risk_classifier, "ML_MODEL_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        RiskClassifier()
