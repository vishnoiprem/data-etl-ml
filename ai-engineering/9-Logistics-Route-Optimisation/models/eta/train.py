"""
ETA Prediction Model — Training

Algorithm : XGBoost (falls back to sklearn GradientBoosting if XGB absent)
Split     : time-based — last 7 days as hold-out test set
Target    : actual_minutes (time driver spent on this single delivery leg)
Artifacts : eta_model.pkl, feature_names.pkl, feature_importance.csv,
            metrics.json, test_predictions.csv
"""

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT))
from features.feature_engineering import FEATURE_COLS, TARGET_COL

DATA_DIR      = _ROOT / "data" / "sample"
ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _time_split(df: pd.DataFrame, test_days: int = 7):
    df["date"] = pd.to_datetime(df["date"])
    cutoff = df["date"].max() - pd.Timedelta(days=test_days)
    return df[df["date"] <= cutoff].copy(), df[df["date"] > cutoff].copy()


def _metrics(y_true, y_pred, naive=None) -> dict:
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mape = float(np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1))) * 100)
    w5   = float(np.mean(np.abs(y_true - y_pred) <= 5)  * 100)
    w10  = float(np.mean(np.abs(y_true - y_pred) <= 10) * 100)
    out  = dict(mae=round(mae, 2), rmse=round(rmse, 2), mape=round(mape, 2),
                within_5min_pct=round(w5, 1), within_10min_pct=round(w10, 1))
    if naive is not None:
        naive_mae = float(mean_absolute_error(y_true, naive))
        out["naive_mae"]       = round(naive_mae, 2)
        out["improvement_pct"] = round((1 - mae / naive_mae) * 100, 1)
    return out


# ── Training ───────────────────────────────────────────────────────────────────

def train_eta_model():
    print("  Loading features …")
    df = pd.read_csv(DATA_DIR / "features.csv")

    avail = [c for c in FEATURE_COLS if c in df.columns]
    X, y  = df[avail], df[TARGET_COL]

    train_df, test_df = _time_split(df, test_days=7)
    X_tr, y_tr = train_df[avail], train_df[TARGET_COL]
    X_te, y_te = test_df[avail],  test_df[TARGET_COL]
    print(f"  Train: {len(X_tr):,}  |  Test: {len(X_te):,}")

    # ── Model ──────────────────────────────────────────────────────────────────
    try:
        import xgboost as xgb
        model = xgb.XGBRegressor(
            n_estimators=350,
            max_depth=6,
            learning_rate=0.04,
            subsample=0.80,
            colsample_bytree=0.80,
            min_child_weight=5,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            n_jobs=-1,
            verbosity=0,
        )
        model_name = "XGBoost"
    except ImportError:
        from sklearn.ensemble import GradientBoostingRegressor
        model = GradientBoostingRegressor(
            n_estimators=250, max_depth=5, learning_rate=0.05,
            subsample=0.80, random_state=42,
        )
        model_name = "GradientBoosting (sklearn)"

    print(f"  Training {model_name} …")
    model.fit(X_tr, y_tr)

    # ── Evaluation ─────────────────────────────────────────────────────────────
    tr_pred = model.predict(X_tr)
    te_pred = model.predict(X_te)

    naive = (test_df["distance_km"] / 25.0 * 60 + 5.0) if "distance_km" in test_df.columns else None

    tr_m = _metrics(y_tr.values, tr_pred)
    te_m = _metrics(y_te.values, te_pred, naive=naive.values if naive is not None else None)

    # ── Feature importance ─────────────────────────────────────────────────────
    fi = pd.DataFrame({"feature": avail, "importance": model.feature_importances_})
    fi = fi.sort_values("importance", ascending=False).reset_index(drop=True)

    # ── Save artifacts ─────────────────────────────────────────────────────────
    joblib.dump(model, ARTIFACTS_DIR / "eta_model.pkl")
    joblib.dump(avail, ARTIFACTS_DIR / "feature_names.pkl")
    fi.to_csv(ARTIFACTS_DIR / "feature_importance.csv", index=False)

    result = dict(model_name=model_name, features=avail,
                  n_train=len(X_tr), n_test=len(X_te),
                  train_metrics=tr_m, test_metrics=te_m)
    with open(ARTIFACTS_DIR / "metrics.json", "w") as f:
        json.dump(result, f, indent=2)

    # Save test predictions for dashboard
    preds_df = test_df[["delivery_id", "date", TARGET_COL]].copy() if "delivery_id" in test_df.columns else test_df[["date", TARGET_COL]].copy()
    preds_df["predicted_minutes"] = te_pred
    if "distance_km" in test_df.columns:
        preds_df["naive_minutes"] = naive.values
    preds_df.to_csv(ARTIFACTS_DIR / "test_predictions.csv", index=False)

    # ── Console summary ────────────────────────────────────────────────────────
    print(f"  ✓ {model_name} — {len(avail)} features")
    print(f"  ✓ Test  MAE:  {te_m['mae']} min  |  RMSE: {te_m['rmse']} min  |  MAPE: {te_m['mape']}%")
    print(f"  ✓ Within 5 min: {te_m['within_5min_pct']}%  |  Within 10 min: {te_m['within_10min_pct']}%")
    if "naive_mae" in te_m:
        print(f"  ✓ Naive baseline MAE: {te_m['naive_mae']} min  →  ML improvement: {te_m['improvement_pct']}%")
    print(f"  ✓ Artifacts → {ARTIFACTS_DIR}/")
    print(f"\n  Top-5 features:")
    for _, row in fi.head(5).iterrows():
        bar = "█" * int(row["importance"] * 40)
        print(f"    {row['feature']:25s}  {bar}  {row['importance']:.4f}")

    return model, result


if __name__ == "__main__":
    train_eta_model()
