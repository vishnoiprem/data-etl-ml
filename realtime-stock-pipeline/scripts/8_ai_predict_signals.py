#!/usr/bin/env python3
"""
8_ai_predict_signals.py — AI/ML layer on top of the live BUY signals.

What it does (in order):
  1. Captures the live signal stream (one row per ticker per snapshot) to
     ``ai_signals/signals_log.csv``.
  2. Builds forward-looking *labels* by joining each historical row to the
     future price 5 / 15 / 30 minutes later (when available).
  3. Trains a small logistic-regression + gradient-boosted-tree ensemble
     on the label history to predict:
        P(price moves up >= 0.5% in the next 15 min)
        Expected 15-minute return (E[r])
        80% confidence interval
  4. Re-uses the same features on the *latest* snapshot and prints a
     ranked AI prediction table next to the live signals.

Models are deliberately tiny (no GPU, no heavy deps) so we can re-train
every few minutes without blocking the live dashboard.

Usage:
  python3 scripts/8_ai_predict_signals.py --tickers SOXL,NVDA,AMD
  python3 scripts/8_ai_predict_signals.py --retrain-every 5
  python3 scripts/8_ai_predict_signals.py --predict-only
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import zoneinfo
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Repo-relative imports
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from producer.ticker_universe import get_tickers  # noqa: E402

# Import the live signals script (filename starts with a digit, so use importlib)
import importlib.util as _ilu
import sys as _sys
_SPEC = _ilu.spec_from_file_location(
    "live_buy_signals",
    str(HERE / "7_live_buy_signals.py"),
)
_live = _ilu.module_from_spec(_SPEC)
_sys.modules["live_buy_signals"] = _live  # dataclass needs this in sys.modules
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_live)
NY_TZ = _live.NY_TZ
Signal = _live.Signal
_hours_remaining = _live._hours_remaining
compute_signals = _live.compute_signals
is_market_hours = _live.is_market_hours

# Output paths
DATA_DIR = HERE.parent / "ai_signals"
LOG_PATH = DATA_DIR / "signals_log.csv"
PRED_PATH = DATA_DIR / "latest_predictions.json"
MODEL_DIR = DATA_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Data capture
# --------------------------------------------------------------------------- #

LOG_COLUMNS = [
    "ts_et", "ticker", "action", "confidence",
    "last", "prev_close", "gap_pct", "day_open", "day_high", "day_low",
    "range_pct", "momentum_5m", "expected_move_pct",
    "hours_remaining", "sector",
    # forward-looking labels (filled in lazily)
    "price_p5", "price_p15", "price_p30",
    "ret_p5", "ret_p15", "ret_p30",
]


def _append_snapshot(now_et: datetime, signals: list[Signal]) -> None:
    """Append the current snapshot to the log; don't touch the forward columns yet."""
    is_new = not LOG_PATH.exists()
    with LOG_PATH.open("a", newline="") as fh:
        w = csv.writer(fh)
        if is_new:
            w.writerow(LOG_COLUMNS)
        hours_remaining = _hours_remaining(now_et)
        for s in signals:
            w.writerow([
                now_et.isoformat(), s.ticker, s.action, s.confidence,
                s.last, s.prev_close, s.gap_pct, s.day_open, s.day_high, s.day_low,
                s.range_pct, s.momentum_5m, s.expected_move_pct,
                f"{hours_remaining:.4f}", s.sector,
                # forward labels left blank
                "", "", "", "", "", "",
            ])


def _label_rows(history: pd.DataFrame, futures: dict[tuple[datetime, str], float]) -> None:
    """Update forward columns for rows whose future price is now known.

    ``futures`` is keyed by ``(ts_et_rounded_to_minute, ticker)`` and stores
    the actual price observed N minutes after that snapshot.
    """
    if not LOG_PATH.exists():
        return
    df = pd.read_csv(LOG_PATH)
    for col in (
        "price_p5", "price_p15", "price_p30",
        "ret_p5", "ret_p15", "ret_p30",
    ):
        if col not in df.columns:
            df[col] = ""
    for idx, row in df.iterrows():
        try:
            ts = pd.Timestamp(row["ts_et"]).to_pydatetime()
        except Exception:
            continue
        last = row.get("last")
        if pd.isna(last) or not last:
            continue
        for n, pcol, rcol in [
            (5, "price_p5", "ret_p5"),
            (15, "price_p15", "ret_p15"),
            (30, "price_p30", "ret_p30"),
        ]:
            if df.at[idx, pcol] not in ("", None) and not pd.isna(df.at[idx, pcol]):
                continue
            # Match the (ts + n min) rounded to the minute — the futures
            # index drops sub-minute precision.
            target_ts = (ts + timedelta(minutes=n)).replace(second=0, microsecond=0)
            fkey = (target_ts, row["ticker"])
            future_price = futures.get(fkey)
            if future_price is None:
                continue
            df.at[idx, pcol] = round(float(future_price), 4)
            df.at[idx, rcol] = round((float(future_price) - float(last)) / float(last), 6)
    df.to_csv(LOG_PATH, index=False)


def _get_future_prices(symbols: tuple[str, ...], max_minutes: int = 30) -> dict[tuple[datetime, str], float]:
    """Fetch 1m bars for the last 90 minutes; index every minute boundary.

    Returns a dict keyed by (datetime_N_minutes_ago, ticker) -> price N minutes later.
    """
    if not symbols:
        return {}
    try:
        data = yf.download(
            tickers=symbols,
            period="1d",
            interval="1m",
            group_by="ticker",
            progress=False,
            threads=True,
        )
    except Exception as exc:
        print(f"[warn] yf.download future prices failed: {exc}", file=sys.stderr)
        return {}

    from pandas import MultiIndex
    futures: dict[tuple[datetime, str], float] = {}
    now = datetime.now(NY_TZ)
    for sym in symbols:
        try:
            if isinstance(data.columns, MultiIndex):
                sub = data[sym] if sym in data.columns.get_level_values(0) else None
            else:
                sub = data
            if sub is None or sub.empty:
                continue
            sub = sub.dropna(how="all")
            for n in (5, 15, 30):
                target = now - timedelta(minutes=n)
                if target.tzinfo is None:
                    target = target.replace(tzinfo=NY_TZ)
                # Find the bar at or just after the target time
                idx = sub.index.get_indexer([target], method="ffill")[0]
                if idx < 0 or idx >= len(sub):
                    continue
                bar_ts = sub.index[idx]
                bar_ts = bar_ts.to_pydatetime()
                if bar_ts.tzinfo is None:
                    bar_ts = bar_ts.replace(tzinfo=NY_TZ)
                # Round the bar to the nearest minute boundary
                rounded = bar_ts.replace(second=0, microsecond=0)
                price = float(sub["Close"].iloc[idx])
                futures[(rounded, sym)] = price
        except Exception as exc:
            print(f"[warn] future-price build failed for {sym}: {exc}", file=sys.stderr)
    return futures


# --------------------------------------------------------------------------- #
# Feature engineering + model
# --------------------------------------------------------------------------- #

FEATURE_COLS = [
    "gap_pct", "range_pct", "momentum_5m", "expected_move_pct",
    "confidence", "hours_remaining", "near_low", "ticker_code",
]


def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Construct a feature matrix from the log DataFrame.

    Adds:
      - ``near_low``           — 1 if last <= day_low * 1.01 else 0
      - ``ticker_code``        — LabelEncoded ticker (one int per symbol)
    """
    df = df.copy()
    df["near_low"] = (
        (df["last"].astype(float) <= df["day_low"].astype(float) * 1.01)
        .astype(int)
    )
    df["ticker_code"] = (
        df["ticker"].astype("category").cat.codes
    )
    # Coerce numeric
    for col in FEATURE_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _train(history: pd.DataFrame) -> tuple[object, object, object, object, int]:
    """Train a classifier + regressor ensemble on whatever labels we have.

    Prefers ret_p15 when ≥30 rows available; otherwise falls back to ret_p5
    so the model can produce predictions within 5-10 min of starting up.
    Returns (clf, gb_clf, reg, scaler, n_train, horizon_min).
    """
    # Pick the longest horizon with at least 30 labels.
    horizon = None
    feats = pd.DataFrame()
    if history["ret_p15"].notna().sum() >= 30:
        horizon = 15
        feats = _build_features(history.dropna(subset=["ret_p15"]))
    elif history["ret_p5"].notna().sum() >= 30:
        horizon = 5
        feats = _build_features(history.dropna(subset=["ret_p5"]))
    else:
        # Not enough data yet — report current count of the longest available.
        n5 = int(history["ret_p5"].notna().sum())
        n15 = int(history["ret_p15"].notna().sum())
        return None, None, None, None, max(n5, n15), 15

    X = feats[FEATURE_COLS].fillna(0.0).to_numpy()
    y_ret = feats[f"ret_p{horizon}"].astype(float).to_numpy()
    y_up = (y_ret >= (0.003 if horizon == 5 else 0.005)).astype(int)

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    clf = LogisticRegression(max_iter=500, class_weight="balanced")
    clf.fit(Xs, y_up)

    reg = GradientBoostingRegressor(
        n_estimators=80, max_depth=3, learning_rate=0.05, random_state=0,
    )
    reg.fit(Xs, y_ret)

    gb_clf = GradientBoostingClassifier(
        n_estimators=80, max_depth=3, learning_rate=0.05, random_state=0,
    )
    gb_clf.fit(Xs, y_up)

    return clf, gb_clf, reg, scaler, len(feats), horizon


def _predict(
    history: pd.DataFrame,
    latest: list[Signal],
    models: tuple,
) -> list[dict]:
    clf, gb_clf, reg, scaler, n_train, horizon = models
    if clf is None:
        return []

    # Build a DataFrame for the latest snapshot
    rows = []
    for s in latest:
        rows.append({
            "ticker": s.ticker,
            "gap_pct": s.gap_pct or 0.0,
            "range_pct": s.range_pct or 0.0,
            "momentum_5m": s.momentum_5m or 0.0,
            "expected_move_pct": s.expected_move_pct or 0.0,
            "confidence": s.confidence or 0.0,
            "hours_remaining": _hours_remaining(datetime.now(NY_TZ)),
            "near_low": int(
                s.last is not None and s.day_low is not None
                and s.last <= s.day_low * 1.01
            ),
        })
    df = pd.DataFrame(rows)
    # Match ticker_code with the *history* category mapping, unseen tickers -> -1
    cat_map = {t: i for i, t in enumerate(sorted(history["ticker"].unique()))}
    df["ticker_code"] = df["ticker"].map(cat_map).fillna(-1).astype(int)
    X = df[FEATURE_COLS].fillna(0.0).to_numpy()
    Xs = scaler.transform(X)

    p_lr = clf.predict_proba(Xs)[:, 1]
    p_gb = gb_clf.predict_proba(Xs)[:, 1]
    p_up = 0.5 * p_lr + 0.5 * p_gb
    e_ret = reg.predict(Xs)

    # 80% CI: std of residual on training set * 1.28.
    target_col = f"ret_p{horizon}"
    train_feats = _build_features(history.dropna(subset=[target_col]))
    if len(train_feats) > 1:
        train_X = scaler.transform(train_feats[FEATURE_COLS].fillna(0.0).to_numpy())
        train_preds = reg.predict(train_X)
        train_actual = train_feats[target_col].astype(float).to_numpy()
        sigma = float(np.std(train_actual - train_preds))
    else:
        sigma = 0.01
    half_width = 1.28 * sigma

    out = []
    for i, s in enumerate(latest):
        out.append({
            "ticker": s.ticker,
            "last": s.last,
            f"p_up_{horizon}m": round(float(p_up[i]), 4),
            f"e_ret_{horizon}m": round(float(e_ret[i]), 6),
            f"ci_low_{horizon}m": round(float(e_ret[i]) - half_width, 6),
            f"ci_high_{horizon}m": round(float(e_ret[i]) + half_width, 6),
            "model_n_train": n_train,
            "model_horizon": horizon,
        })
    out.sort(key=lambda r: -r[f"p_up_{horizon}m"])
    return out


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

def _render_ai(preds: list[dict], now_et: datetime) -> str:
    if not preds:
        return "  (not enough history yet — need ~30 labeled rows; run for 5-15 min)"
    n = preds[0]["model_n_train"]
    h = preds[0]["model_horizon"]
    lines = [
        f"=== AI predictions — {now_et.strftime('%H:%M:%S ET')} "
        f"(trained on {n} rows, horizon={h}m) ===",
        f"{'TICKER':<7} {'LAST':>9} {f'P(UP_{h}m)':>9} {f'E[ret_{h}m]':>11}  "
        f"{'80% CI':>20}  {'VERDICT':>10}",
        "─" * 75,
    ]
    for p in preds:
        p_up = p[f"p_up_{h}m"]
        e_ret = p[f"e_ret_{h}m"]
        verdict = "BUY" if p_up >= 0.55 and e_ret > 0 else (
            "WATCH" if p_up >= 0.45 else "HOLD"
        )
        ci = f"[{p[f'ci_low_{h}m']*100:+.2f}%, {p[f'ci_high_{h}m']*100:+.2f}%]"
        lines.append(
            f"{p['ticker']:<7} "
            f"{p['last']:>9.2f} "
            f"{p_up*100:>8.1f}% "
            f"{e_ret*100:>+10.3f}%  "
            f"{ci:>20}  "
            f"{verdict:>10}"
        )
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Main loop
# --------------------------------------------------------------------------- #

def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AI/ML predictor on top of the live signal stream.")
    p.add_argument("--tickers", type=str, default=None,
                   help="Comma-separated tickers (default: full universe).")
    p.add_argument("--poll-seconds", type=int, default=60)
    p.add_argument("--retrain-every", type=int, default=5,
                   help="Re-train the model every N polls (default 5).")
    p.add_argument("--predict-only", action="store_true",
                   help="Skip capture; only predict from the existing log.")
    p.add_argument("--once", action="store_true")
    return p.parse_args(argv)


def _resolve_universe(args) -> list[dict]:
    if args.tickers:
        wanted = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        by_symbol = {t["ticker"]: t for t in get_tickers()}
        return [
            by_symbol.get(sym, {"ticker": sym, "sector": "", "index_membership": ""})
            for sym in wanted
        ]
    return list(get_tickers())


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    universe = _resolve_universe(args)
    if not universe:
        print("No tickers — nothing to do.", file=sys.stderr)
        return 2

    models = (None, None, None, None, 0)
    last_train = 0
    polls_since_train = 999

    print(
        f"=== AI predictor — {len(universe)} tickers, "
        f"refresh {args.poll_seconds}s, retrain every {args.retrain_every} polls ===",
        flush=True,
    )

    try:
        while True:
            now_et = datetime.now(NY_TZ)
            signals = compute_signals(universe, now_et=now_et)

            # 1. Capture
            if not args.predict_only:
                _append_snapshot(now_et, signals)
                # 2. Build future prices and label old rows
                symbols = tuple(s.ticker for s in signals)
                futures = _get_future_prices(symbols)
                _label_rows(pd.DataFrame(), futures)

            # 3. Train
            polls_since_train += 1
            if polls_since_train >= args.retrain_every and LOG_PATH.exists():
                try:
                    history = pd.read_csv(LOG_PATH)
                    if len(history) >= 30:
                        models = _train(history)
                        polls_since_train = 0
                except Exception as exc:
                    print(f"[warn] train failed: {exc}", file=sys.stderr)

            # 4. Predict on the *latest* snapshot using the most recent features
            preds: list[dict] = []
            if models[0] is not None and LOG_PATH.exists():
                try:
                    history = pd.read_csv(LOG_PATH)
                    preds = _predict(history, signals, models)
                    PRED_PATH.write_text(json.dumps({
                        "ts_et": now_et.isoformat(),
                        "predictions": preds,
                    }, indent=2))
                except Exception as exc:
                    print(f"[warn] predict failed: {exc}", file=sys.stderr)

            print(_render_ai(preds, now_et), flush=True)

            if args.once:
                return 0
            time.sleep(args.poll_seconds)
    except KeyboardInterrupt:
        print("\nstopped.", flush=True)
        return 0


if __name__ == "__main__":
    sys.exit(main())
