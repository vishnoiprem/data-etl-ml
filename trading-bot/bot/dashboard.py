"""Web dashboard for the trading bot.

A single-page Flask app that shows:
  - Watchlist table: price, day change, MAs, RSI, MACD, Bollinger, vol
  - Open positions: from the SQLite state store, with mark-to-market P&L
  - Sector strip: SOX (semis), QQQ (Nasdaq 100), SPY (S&P 500), VIX (fear)
  - 5-day sparkline for each watchlist ticker
  - Market clock: time until next open/close in your local time

Run:
  python -m bot.dashboard                # serves on http://127.0.0.1:5000
  python -m bot.dashboard --port 8080    # custom port
  python -m bot.dashboard --state /path/to/state.db  # custom DB

The page auto-refreshes every 30 seconds via JS. The /api/snapshot
endpoint returns the same data as JSON for any external consumer.
"""
from __future__ import annotations
import argparse
import logging
import os
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import yfinance as yf
from flask import Flask, jsonify, render_template_string


log = logging.getLogger("dashboard")


WATCHLIST = ["SOXL", "TQQQ", "NVDA"]
SECTOR_ETFS = ["SOXX", "QQQ", "SPY", "DIA"]
FEAR = "^VIX"
DEFAULT_STATE_DB = "data/state.db"

ET = timezone(timedelta(hours=-5))  # US/Eastern (no DST handling — close enough)


# --------------------------------------------------------------------------- #
#  Data fetchers                                                              #
# --------------------------------------------------------------------------- #

def _ema(data: np.ndarray, span: int) -> np.ndarray:
    ema = np.zeros_like(data, dtype=float)
    alpha = 2 / (span + 1)
    ema[0] = data[0]
    for i in range(1, len(data)):
        ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]
    return ema


def _rsi(close: np.ndarray, period: int = 14) -> float:
    deltas = np.diff(close)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    if len(gains) < period:
        return 50.0
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    rs = avg_gain / avg_loss if avg_loss else 100.0
    return float(100 - (100 / (1 + rs)))


def _macd_state(close: np.ndarray) -> dict:
    ema12 = _ema(close, 12)
    ema26 = _ema(close, 26)
    macd_line = ema12 - ema26
    signal_line = _ema(macd_line, 9)
    hist = macd_line - signal_line
    h = float(hist[-1])
    if h > 0 and (len(hist) < 2 or hist[-2] <= 0):
        state = "bullish_cross"
    elif h < 0 and (len(hist) < 2 or hist[-2] >= 0):
        state = "bearish_cross"
    elif h > 0:
        state = "above_zero"
    else:
        state = "below_zero"
    return {"hist": h, "state": state}


def _bollinger(close: np.ndarray, period: int = 20) -> dict:
    sma = float(np.mean(close[-period:]))
    std = float(np.std(close[-period:]))
    upper = sma + 2 * std
    lower = sma - 2 * std
    p = float(close[-1])
    pct = (p - lower) / (upper - lower) if upper != lower else 0.5
    pos = "upper" if p > upper else "lower" if p < lower else "middle"
    return {"upper": upper, "middle": sma, "lower": lower, "pct": pct, "pos": pos}


def _annualized_vol(close: np.ndarray) -> float:
    rets = np.diff(np.log(close[-21:]))
    return float(np.std(rets) * np.sqrt(252) * 100) if len(rets) > 1 else 0.0


def fetch_ticker(ticker: str) -> dict:
    """Pull a full snapshot for one ticker. Returns dict, never raises."""
    out: dict = {"ticker": ticker, "ts": time.time()}
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        p = float(info.last_price)
        prev = float(info.previous_close)
        out.update({
            "price": p,
            "change": p - prev,
            "change_pct": (p - prev) / prev * 100 if prev else 0.0,
            "prev_close": prev,
            "day_high": float(info.day_high),
            "day_low": float(info.day_low),
            "volume": int(info.last_volume) if info.last_volume else 0,
            "ma50": float(info.fifty_day_average) if info.fifty_day_average else 0.0,
            "ma200": float(info.two_hundred_day_average) if info.two_hundred_day_average else 0.0,
            "wk52_high": float(info.year_high),
            "wk52_low": float(info.year_low),
            "name": getattr(t, "info", {}).get("shortName", ticker),
        })
        # Trend
        if out["ma50"] and out["ma200"] and p > out["ma50"] > out["ma200"]:
            out["trend"] = "uptrend"
        elif out["ma50"] and out["ma200"] and p < out["ma50"] < out["ma200"]:
            out["trend"] = "downtrend"
        else:
            out["trend"] = "neutral"
        # Deep technicals (need history)
        try:
            hist = t.history(period="6mo", auto_adjust=True)
            if not hist.empty and len(hist) >= 50:
                close = hist["Close"].values
                out["rsi14"] = _rsi(close)
                out["macd_state"] = _macd_state(close)["state"]
                out["macd_hist"] = _macd_state(close)["hist"]
                bb = _bollinger(close)
                out["bb_pct"] = bb["pct"]
                out["bb_pos"] = bb["pos"]
                out["vol_annual"] = _annualized_vol(close)
                # 5-day sparkline
                out["spark"] = [round(float(x), 2) for x in close[-5:]]
                out["slope_5d_pct"] = float((close[-1] / close[-6] - 1) * 100) \
                    if len(close) >= 6 else 0.0
        except Exception as e:
            log.debug("history fetch failed for %s: %s", ticker, e)
    except Exception as e:
        out["error"] = str(e)
    return out


def fetch_all(tickers: list[str]) -> list[dict]:
    """Fetch a list of tickers in parallel."""
    with ThreadPoolExecutor(max_workers=8) as ex:
        return list(ex.map(fetch_ticker, tickers))


# --------------------------------------------------------------------------- #
#  Positions (read from the SQLite state store)                               #
# --------------------------------------------------------------------------- #

def load_positions(db_path: str) -> dict:
    """Return {cash, positions: [{ticker, shares, avg_cost, current_price, pnl}]}."""
    if not Path(db_path).exists():
        return {"cash": 0.0, "positions": [], "db_connected": False}
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("SELECT cash FROM account WHERE id = 1")
        row = cur.fetchone()
        cash = float(row["cash"]) if row else 0.0
        cur.execute("""SELECT ticker, shares, avg_cost FROM positions
                       WHERE shares > 0""")
        pos_rows = cur.fetchall()
    except Exception as e:
        log.warning("could not read positions: %s", e)
        return {"cash": 0.0, "positions": [], "db_connected": False}
    finally:
        conn.close()
    if not pos_rows:
        return {"cash": cash, "positions": [], "db_connected": True}
    tickers = [r["ticker"] for r in pos_rows]
    quotes = {q["ticker"]: q for q in fetch_all(tickers)}
    positions = []
    for r in pos_rows:
        q = quotes.get(r["ticker"], {})
        cur_px = q.get("price", 0.0)
        avg = float(r["avg_cost"])
        shares = int(r["shares"])
        positions.append({
            "ticker": r["ticker"],
            "shares": shares,
            "avg_cost": avg,
            "current_price": cur_px,
            "cost_basis": avg * shares,
            "market_value": cur_px * shares,
            "pnl": (cur_px - avg) * shares,
            "pnl_pct": (cur_px / avg - 1) * 100 if avg else 0.0,
        })
    return {"cash": cash, "positions": positions, "db_connected": True}


# --------------------------------------------------------------------------- #
#  Market clock                                                               #
# --------------------------------------------------------------------------- #

def market_clock() -> dict:
    """Return market state + time until next open/close in ET."""
    now_et = datetime.now(ET)
    # NYSE hours: 9:30-16:00 ET, Mon-Fri
    is_weekday = now_et.weekday() < 5
    market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
    if is_weekday and market_open <= now_et <= market_close:
        status = "open"
        delta = market_close - now_et
        label = f"closes in {int(delta.total_seconds() // 60)} min"
    elif is_weekday and now_et < market_open:
        status = "pre_market"
        delta = market_open - now_et
        h, rem = divmod(int(delta.total_seconds()), 3600)
        m = rem // 60
        label = f"opens in {h}h {m}m"
    else:
        # After hours or weekend — show next open (Monday or next day)
        status = "closed"
        if now_et.weekday() >= 4:  # Fri after close or weekend
            days_ahead = 7 - now_et.weekday()
        else:
            days_ahead = 1
        next_open = (now_et + timedelta(days=days_ahead)).replace(
            hour=9, minute=30, second=0, microsecond=0,
        )
        delta = next_open - now_et
        h = int(delta.total_seconds() // 3600)
        m = int((delta.total_seconds() % 3600) // 60)
        label = f"opens in {h}h {m}m"
    return {
        "status": status,
        "label": label,
        "now_et": now_et.strftime("%H:%M:%S ET"),
    }


# --------------------------------------------------------------------------- #
#  Flask app                                                                  #
# --------------------------------------------------------------------------- #

def build_snapshot(state_db: str) -> dict:
    """One big dict with everything the dashboard needs."""
    return {
        "watchlist": fetch_all(WATCHLIST),
        "sectors": fetch_all(SECTOR_ETFS),
        "fear": (fetch_all([FEAR]) or [{}])[0],
        "positions": load_positions(state_db),
        "clock": market_clock(),
        "generated_at": datetime.now(ET).strftime("%Y-%m-%d %H:%M:%S ET"),
    }


def create_app(state_db: str = DEFAULT_STATE_DB) -> Flask:
    app = Flask(__name__)
    app.config["STATE_DB"] = state_db

    @app.route("/")
    def index():
        html = (Path(__file__).parent / "dashboard.html").read_text()
        return render_template_string(html)

    @app.route("/api/snapshot")
    def snapshot():
        return jsonify(build_snapshot(app.config["STATE_DB"]))

    return app


# --------------------------------------------------------------------------- #
#  CLI                                                                        #
# --------------------------------------------------------------------------- #

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--state", default=DEFAULT_STATE_DB,
                   help="path to the trading-bot state SQLite db")
    p.add_argument("--debug", action="store_true")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app = create_app(args.state)
    log.info("dashboard serving on http://%s:%d (state=%s)",
             args.host, args.port, args.state)
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
