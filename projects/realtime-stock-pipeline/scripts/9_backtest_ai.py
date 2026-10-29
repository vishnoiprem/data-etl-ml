#!/usr/bin/env python3
"""
9_backtest_ai.py — Score the AI's BUY verdicts on the labeled history.

What it does
------------
Replays the labeled signals_log.csv *as if* we were running the AI live
at the time of each row, then compares predicted BUY signals to the
real 5/15/30-minute forward returns.

For every (ts, ticker) row, we:
  1. Take only the rows where the *ret_pN* label is known (forward price
     already observed).
  2. For each horizon H ∈ {5, 15, 30}:
       - We *simulate* the AI's verdict at the snapshot time using the
         *current* training set (i.e. everything strictly older than the
         row's timestamp).
       - To stay cheap, we don't actually re-fit a model per row. We
         fit ONE model on the full history, then for each row we
         compute features → predict. This is a *transductive* check:
         "if the AI had been perfectly trained on all prior data, would
         its BUY signals have been right?"
  3. Aggregate accuracy, mean return on BUYs, hit-rate, calibration.

Output: a printed report + JSON dump to ai_signals/backtest_report.json.

Run:  python3 scripts/9_backtest_ai.py
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LOG_PATH = ROOT / "ai_signals" / "signals_log.csv"
REPORT_PATH = ROOT / "ai_signals" / "backtest_report.json"

FEATURE_COLS = [
    "gap_pct", "range_pct", "momentum_5m", "expected_move_pct",
    "confidence", "hours_remaining", "near_low", "ticker_code",
]
BUY_THRESHOLD = 0.55  # must match _render_ai BUY rule (P_up >= 0.55 and E_ret > 0)


def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["near_low"] = (
        (df["last"].astype(float) <= df["day_low"].astype(float) * 1.01).astype(int)
    )
    df["ticker_code"] = df["ticker"].astype("category").cat.codes
    for c in FEATURE_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _train_ensemble(history: pd.DataFrame, horizon: int):
    """Train on every row that has a label for the given horizon."""
    target = f"ret_p{horizon}"
    feats = _build_features(history.dropna(subset=[target]).copy())
    if len(feats) < 30:
        return None

    X = feats[FEATURE_COLS].fillna(0.0).to_numpy()
    y_ret = feats[target].astype(float).to_numpy()
    # Match the live model's up-threshold (5m: 0.3%, 15m: 0.5%, 30m: 0.8%)
    y_up = (y_ret >= {5: 0.003, 15: 0.005, 30: 0.008}[horizon]).astype(int)
    if len(np.unique(y_up)) < 2:
        return None

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    clf = LogisticRegression(max_iter=500, class_weight="balanced").fit(Xs, y_up)
    gb = GradientBoostingClassifier(
        n_estimators=80, max_depth=3, learning_rate=0.05, random_state=0
    ).fit(Xs, y_up)
    reg = GradientBoostingRegressor(
        n_estimators=80, max_depth=3, learning_rate=0.05, random_state=0
    ).fit(Xs, y_ret)
    return clf, gb, reg, scaler


def _score_horizon(history: pd.DataFrame, horizon: int) -> dict:
    target = f"ret_p{horizon}"
    labeled = history.dropna(subset=[target]).copy()
    if len(labeled) < 30:
        return {"horizon": horizon, "n_labeled": int(len(labeled)), "skipped": True}

    models = _train_ensemble(labeled, horizon)
    if models is None:
        return {"horizon": horizon, "n_labeled": int(len(labeled)),
                "skipped": True, "reason": "training failed (insufficient class mix)"}
    clf, gb, reg, scaler = models

    # Score every labeled row
    feats = _build_features(labeled)
    Xs = scaler.transform(feats[FEATURE_COLS].fillna(0.0).to_numpy())
    p_up = 0.5 * clf.predict_proba(Xs)[:, 1] + 0.5 * gb.predict_proba(Xs)[:, 1]
    e_ret = reg.predict(Xs)

    actual = feats[target].astype(float).to_numpy()
    n_buy = int(((p_up >= BUY_THRESHOLD) & (e_ret > 0)).sum())

    # BUY-set: where the AI would have said BUY at snapshot time
    buy_mask = (p_up >= BUY_THRESHOLD) & (e_ret > 0)
    if buy_mask.sum() == 0:
        return {
            "horizon": horizon,
            "n_labeled": int(len(labeled)),
            "n_buy": 0,
            "note": "no BUY verdicts produced on the training set itself",
        }

    buy_actual = actual[buy_mask]
    buy_pred = e_ret[buy_mask]
    buy_p = p_up[buy_mask]

    # Hit-rate: BUY → real up-move (>= threshold)
    up_threshold = {5: 0.003, 15: 0.005, 30: 0.008}[horizon]
    hit = int((buy_actual >= up_threshold).sum())
    # Avg return on BUYs
    avg_ret = float(np.mean(buy_actual))
    avg_pred = float(np.mean(buy_pred))
    # Calibration: mean predicted P(UP) vs realized hit-rate
    calib_pred = float(np.mean(buy_p))
    calib_real = hit / max(int(buy_mask.sum()), 1)
    # Sharpe-ish: avg / std
    std_ret = float(np.std(buy_actual)) or 1e-9
    sharpe = float(np.mean(buy_actual) / std_ret)

    # Baseline: hit-rate if you just held every labeled row
    base_hit = float((actual >= up_threshold).mean())

    # Top-3 ticker table for the BUY set
    buy_rows = feats.loc[buy_mask, ["ticker", "ts_et"]].copy()
    buy_rows["p_up"] = buy_p
    buy_rows["e_ret"] = buy_pred
    buy_rows["actual"] = buy_actual
    buy_rows["hit"] = (buy_actual >= up_threshold).astype(int)
    by_ticker = (
        buy_rows.groupby("ticker")
        .agg(
            n=("hit", "size"),
            hits=("hit", "sum"),
            avg_pred=("p_up", "mean"),
            avg_actual=("actual", "mean"),
        )
        .sort_values("avg_actual", ascending=False)
    )

    return {
        "horizon": horizon,
        "n_labeled": int(len(labeled)),
        "n_buy": int(buy_mask.sum()),
        "buy_hit_rate": round(hit / max(int(buy_mask.sum()), 1), 4),
        "baseline_hit_rate": round(base_hit, 4),
        "lift_vs_hold": round((hit / max(int(buy_mask.sum()), 1)) - base_hit, 4),
        "avg_pred_p_up": round(calib_pred, 4),
        "avg_actual_hit_rate": round(calib_real, 4),
        "calibration_gap": round(calib_pred - calib_real, 4),
        "avg_predicted_return": round(avg_pred, 6),
        "avg_actual_return": round(avg_ret, 6),
        "realized_sharpe": round(sharpe, 4),
        "by_ticker": by_ticker.reset_index().to_dict(orient="records"),
    }


def main() -> int:
    if not LOG_PATH.exists():
        print(f"No log at {LOG_PATH} — run scripts/8_ai_predict_signals.py first.")
        return 1

    history = pd.read_csv(LOG_PATH)
    print(f"Loaded {len(history)} rows from {LOG_PATH.name}")
    print(f"  tickers:   {history['ticker'].nunique()}")
    print(f"  time span: {history['ts_et'].iloc[0]}  →  {history['ts_et'].iloc[-1]}")
    print()
    for h in (5, 15, 30):
        labeled_n = int(history[f"ret_p{h}"].notna().sum())
        print(f"  ret_p{h}: {labeled_n} labeled rows")
    print()

    report = {
        "ts_et": datetime.now().isoformat(),
        "n_rows_total": int(len(history)),
        "n_tickers": int(history["ticker"].nunique()),
        "buy_threshold_p_up": BUY_THRESHOLD,
        "horizons": {},
    }

    for h in (5, 15, 30):
        result = _score_horizon(history, h)
        report["horizons"][f"p{h}"] = result
        print(f"=== Horizon: {h}m ===")
        if result.get("skipped"):
            print(f"  skipped: {result.get('reason', 'not enough data')}")
        elif result.get("n_buy", 0) == 0:
            print(f"  {result.get('note')}")
        else:
            print(f"  labeled rows:     {result['n_labeled']}")
            print(f"  BUY verdicts:     {result['n_buy']}")
            print(f"  BUY hit-rate:     {result['buy_hit_rate']*100:.1f}%   (baseline={result['baseline_hit_rate']*100:.1f}%)")
            print(f"  lift vs hold:     {result['lift_vs_hold']*100:+.1f} pp")
            print(f"  calibration:      predicted P(up)={result['avg_pred_p_up']*100:.1f}%  realized={result['avg_actual_hit_rate']*100:.1f}%   gap={result['calibration_gap']*100:+.1f} pp")
            print(f"  avg return:       predicted={result['avg_predicted_return']*100:+.3f}%  actual={result['avg_actual_return']*100:+.3f}%")
            print(f"  realized Sharpe:  {result['realized_sharpe']:.3f}")
            print()
            print("  by ticker (sorted by avg realized return):")
            for row in result["by_ticker"][:10]:
                hits_pct = (row["hits"] / max(row["n"], 1)) * 100
                print(
                    f"    {row['ticker']:6s}  n={int(row['n']):3d}  "
                    f"hits={hits_pct:5.1f}%  "
                    f"avg_pred={row['avg_pred']*100:5.2f}%  "
                    f"avg_actual={row['avg_actual']*100:+5.3f}%"
                )
        print()

    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str))
    print(f"\nFull report → {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
