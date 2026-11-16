"""
SCB AML Platform — ML Risk Classifier
======================================

Trains a gradient-boosted classifier on the engineered feature store
to predict whether a customer is **high-risk** (composite_aml_score ≥
ML_RISK_LABEL_THRESHOLD).

Why this exists alongside the rules engine:
  The rules engine flags known suspicious patterns (CTR, structuring,
  sanctions, PEP wire). The ML model catches *unknown* patterns — a
  customer whose feature mix is statistically similar to past confirmed
  bad actors but doesn't match any single rule. Real-world AML teams
  run both: rules for explainability + ML for sensitivity.

Output:
  data/ml_models/risk_classifier_v{ts}.joblib   — trained model
  data/ml_models/latest.joblib                 — symlink/pointer
  output/ml/risk_predictions.parquet           — per-customer prob
  output/ml/model_metrics.json                 — accuracy, AUC, etc.

Trained on the synthetic data: small but realistic enough to demonstrate
the full train → evaluate → predict → serve loop end-to-end.
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from scb_aml_platform.config.settings import (
    BASE_DIR, ML_MODEL_DIR, ML_RISK_LABEL_THRESHOLD,
)

PROCESSED_DIR = Path(BASE_DIR) / "data" / "processed"
ML_OUTPUT_DIR = Path(BASE_DIR) / "output" / "ml"
ML_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
# FEATURE ENGINEERING
# ─────────────────────────────────────────────
FEATURE_COLS = [
    "txn_count_1d", "txn_volume_1d_usd",
    "txn_count_7d", "txn_volume_7d_usd",
    "txn_count_30d", "txn_volume_30d_usd",
    "txn_count_90d", "txn_volume_90d_usd",
    "volume_change_pct_7d",
    "count_just_below_threshold", "structuring_flag", "structuring_score",
    "unique_countries_30d", "high_risk_vol_usd", "total_cross_border_usd",
    "cross_border_ratio",
    "degree_centrality", "betweenness_centrality",
    "degree_from_txns", "degree_from_rels",
    "avg_txn_size_usd", "avg_txn_size_change_pct",
    "dormancy_days", "channel_diversity_score",
    "kyc_age_days",
]

# String columns we one-hot encode
CATEGORICAL_COLS = ["country_code", "kyc_status"]


def build_training_table() -> pd.DataFrame:
    """Join feature store + risk profiles, derive the label.

    Label = 1 (high_risk) if composite_aml_score ≥ threshold, else 0.

    The fixed threshold (ML_RISK_LABEL_THRESHOLD) is appropriate for
    real data. On the synthetic data, the score distribution is
    narrower (max ~50) so we ALSO include customers who triggered any
    AML rule in the positive class — those are the ground-truth bad
    actors in this dataset.
    """
    feature_path = PROCESSED_DIR / "aml_feature_store.parquet"
    risk_path = PROCESSED_DIR / "customer_risk_profiles.parquet"
    rules_path = Path(BASE_DIR) / "output" / "alerts" / "rules_alerts.parquet"
    if not feature_path.exists() or not risk_path.exists():
        raise FileNotFoundError(
            "Run spark jobs 1-3 + risk_scoring before training the ML model"
        )
    features = pd.read_parquet(feature_path)
    risk = pd.read_parquet(risk_path)[["customer_id", "composite_aml_score"]]
    df = features.merge(risk, on="customer_id", how="inner")
    # Label: 1 if composite score >= threshold OR has any rule alert
    df["label"] = (df["composite_aml_score"] >= ML_RISK_LABEL_THRESHOLD).astype(int)
    if rules_path.exists():
        alerted = pd.read_parquet(rules_path)["customer_id"].unique()
        df.loc[df["customer_id"].isin(alerted), "label"] = 1
    return df


def _prepare_X(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Return (X, feature_names). Coerces dtypes and one-hot encodes
    categorical columns. Keeps the same transform for train + predict.
    """
    cols = [c for c in FEATURE_COLS if c in df.columns]
    X = df[cols].copy()
    # numeric
    for c in cols:
        if X[c].dtype == "object":
            X[c] = pd.to_numeric(X[c], errors="coerce")
    X = X.fillna(0)
    # categorical
    cat_dummies = []
    for c in CATEGORICAL_COLS:
        if c in df.columns:
            d = pd.get_dummies(df[c].astype(str), prefix=c)
            cat_dummies.append(d)
    if cat_dummies:
        X = pd.concat([X] + cat_dummies, axis=1)
    return X, list(X.columns)


# ─────────────────────────────────────────────
# TRAIN / EVALUATE
# ─────────────────────────────────────────────
def train_model(test_size: float = 0.25, random_state: int = 42) -> dict:
    """Train a GradientBoostingClassifier and return metrics + paths.

    Returns:
        {
          "model_path": Path,
          "metrics": {accuracy, precision, recall, f1, auc, ...},
          "n_train": int, "n_test": int,
          "feature_importances": {feature: importance, ...},
        }
    """
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        roc_auc_score, classification_report, confusion_matrix,
    )
    import joblib

    logger.info("=" * 60)
    logger.info("ML Risk Classifier — Training")
    logger.info("=" * 60)

    df = build_training_table()
    logger.info(f"Training table: {len(df)} customers | "
                f"label distribution: {df['label'].value_counts().to_dict()}")

    X, feature_names = _prepare_X(df)
    y = df["label"].values

    if y.sum() < 2 or (len(y) - y.sum()) < 2:
        # Need at least 2 of each class to split / score AUC.
        logger.warning("Imbalanced labels — using full data for both train and test")
        X_train, X_test, y_train, y_test = X, X, y, y
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state,
            stratify=y,
        )

    logger.info(f"Train: {len(X_train)} | Test: {len(X_test)} | "
                f"Features: {X.shape[1]}")

    model = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=3,
        learning_rate=0.05,
        random_state=random_state,
    )
    t0 = time.time()
    model.fit(X_train, y_train)
    train_seconds = round(time.time() - t0, 2)
    logger.info(f"Trained in {train_seconds}s")

    # ── Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "auc": round(float(roc_auc_score(y_test, y_proba)) if len(set(y_test)) > 1 else 0.0, 4),
        "train_seconds": train_seconds,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "n_positive_test": int(y_test.sum()),
    }
    metrics["confusion_matrix"] = confusion_matrix(y_test, y_pred).tolist()

    importances = dict(zip(feature_names, [round(float(v), 4) for v in model.feature_importances_]))
    top_features = dict(sorted(importances.items(), key=lambda kv: -kv[1])[:10])
    metrics["top_features"] = top_features

    logger.info(f"  Accuracy : {metrics['accuracy']}")
    logger.info(f"  Precision: {metrics['precision']}")
    logger.info(f"  Recall   : {metrics['recall']}")
    logger.info(f"  F1       : {metrics['f1']}")
    logger.info(f"  AUC      : {metrics['auc']}")
    logger.info(f"  Top features: {list(top_features.keys())[:5]}")

    # ── Persist
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    ML_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = ML_MODEL_DIR / f"risk_classifier_{ts}.joblib"
    joblib.dump({"model": model, "feature_names": feature_names}, model_path)
    latest = ML_MODEL_DIR / "latest.joblib"
    joblib.dump({"model": model, "feature_names": feature_names}, latest)
    logger.success(f"Model saved: {model_path} (+ latest.joblib)")

    # ── Predict on ALL customers → parquet
    all_proba = model.predict_proba(X)[:, 1]
    preds = pd.DataFrame({
        "customer_id": df["customer_id"].values,
        "true_label": y,
        "ml_risk_proba": np.round(all_proba, 4),
        "ml_predicted_high_risk": (all_proba >= 0.5).astype(int),
        "composite_aml_score": df["composite_aml_score"].values,
    })
    pred_path = ML_OUTPUT_DIR / "risk_predictions.parquet"
    preds.to_parquet(pred_path, index=False)
    logger.success(f"Predictions: {len(preds)} customers → {pred_path}")

    # ── Metrics JSON
    metrics["model_path"] = str(model_path)
    metrics["predictions_path"] = str(pred_path)
    metrics["trained_at"] = datetime.utcnow().isoformat() + "Z"
    metrics_path = ML_OUTPUT_DIR / "model_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2))
    logger.success(f"Metrics: {metrics_path}")

    return {
        "model_path": model_path,
        "metrics": metrics,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "feature_importances": importances,
    }


# ─────────────────────────────────────────────
# INFERENCE (used by Lucid Search API + UI)
# ─────────────────────────────────────────────
class RiskClassifier:
    """Lightweight inference wrapper. Loads `latest.joblib` once."""

    def __init__(self, model_path: Optional[Path] = None):
        import joblib
        path = Path(model_path) if model_path else ML_MODEL_DIR / "latest.joblib"
        if not path.exists():
            raise FileNotFoundError(
                f"No model at {path}. Run ml.risk_classifier.train_model() first."
            )
        bundle = joblib.load(path)
        self.model = bundle["model"]
        self.feature_names = bundle["feature_names"]
        logger.info(f"RiskClassifier loaded: {path.name} ({len(self.feature_names)} features)")

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        """Score all rows in df. Returns 1-D array of P(high_risk)."""
        X, _ = _prepare_X(df)
        # Align columns to training schema — fill missing with 0
        X = X.reindex(columns=self.feature_names, fill_value=0)
        return self.model.predict_proba(X)[:, 1]


def run() -> dict:
    """End-to-end: train + persist + write predictions."""
    return train_model()


if __name__ == "__main__":
    run()
