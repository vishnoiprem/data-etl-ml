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
import hmac
import logging
import os
import sqlite3
import threading
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
CACHE_TTL_SECONDS = 60  # cache yfinance results for 1 minute

ET = timezone(timedelta(hours=-5))  # US/Eastern (no DST handling — close enough)


# --------------------------------------------------------------------------- #
#  TTL cache for yfinance                                                     #
# --------------------------------------------------------------------------- #

_cache: dict[str, tuple[float, dict]] = {}  # ticker -> (fetched_at, data)
_cache_lock = threading.Lock()  # fetch_all() uses 8 threads; protect dict


def _cache_get(ticker: str) -> dict | None:
    with _cache_lock:
        entry = _cache.get(ticker)
    if entry is None:
        return None
    fetched_at, data = entry
    if time.time() - fetched_at > CACHE_TTL_SECONDS:
        return None
    return data


def _cache_put(ticker: str, data: dict) -> None:
    # Don't cache fetches that failed — let the next request retry instead
    # of pinning a broken state for 60s.
    if "error" in data and not data.get("price"):
        return
    with _cache_lock:
        _cache[ticker] = (time.time(), data)


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
    """Pull a full snapshot for one ticker. Returns dict, never raises.

    Uses an in-process TTL cache to avoid hammering yfinance. The dashboard
    refreshes every 30s, but we only need fresh data every ~60s for prices
    (yfinance quotes are 15-min delayed during market hours anyway).
    """
    cached = _cache_get(ticker)
    if cached is not None:
        return cached
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
                high = hist["High"].values
                low = hist["Low"].values
                volume = hist["Volume"].values
                out["rsi14"] = _rsi(close)
                macd_info = _macd_state(close)
                out["macd_state"] = macd_info["state"]
                out["macd_hist"] = macd_info["hist"]
                bb = _bollinger(close)
                out["bb_pct"] = bb["pct"]
                out["bb_pos"] = bb["pos"]
                out["vol_annual"] = _annualized_vol(close)
                out["ma20"] = bb["middle"]
                out["hi60"] = float(np.max(high[-60:]))
                out["lo60"] = float(np.min(low[-60:]))
                out["bb_upper"] = bb["upper"]
                out["bb_lower"] = bb["lower"]
                # 5-day sparkline
                out["spark"] = [round(float(x), 2) for x in close[-5:]]
                out["slope_5d_pct"] = float((close[-1] / close[-6] - 1) * 100) \
                    if len(close) >= 6 else 0.0
                # Volume trend: is the recent 5d volume higher than 20d average?
                vol_avg_5d = float(np.mean(volume[-5:]))
                vol_avg_20d = float(np.mean(volume[-20:]))
                if vol_avg_20d > 0:
                    vr = vol_avg_5d / vol_avg_20d
                    if vr > 1.2:
                        out["vol_trend"] = "rising"
                    elif vr < 0.8:
                        out["vol_trend"] = "falling"
                    else:
                        out["vol_trend"] = "normal"
                else:
                    out["vol_trend"] = "normal"
                # Distance from MAs
                if out["ma50"]:
                    out["dist_ma50_pct"] = (p / out["ma50"] - 1) * 100
                if out["ma200"]:
                    out["dist_ma200_pct"] = (p / out["ma200"] - 1) * 100
                # 52w position
                if out["wk52_high"]:
                    out["pct_from_52h"] = (p / out["wk52_high"] - 1) * 100
        except Exception as e:
            log.debug("history fetch failed for %s: %s", ticker, e)
    except Exception as e:
        out["error"] = str(e)
    _cache_put(ticker, out)
    return out


def fetch_all(tickers: list[str]) -> list[dict]:
    """Fetch a list of tickers in parallel."""
    with ThreadPoolExecutor(max_workers=8) as ex:
        return list(ex.map(fetch_ticker, tickers))


# --------------------------------------------------------------------------- #
#  Bull / bear scoring                                                        #
# --------------------------------------------------------------------------- #

def score_ticker(t: dict) -> dict:
    """Return bull/bear reasons, key levels, and a verdict.

    Pure rule-based — no ML, no advice. Each rule is a transparent heuristic
    over the technical indicators. The verdict is one of:
      BUY    — bull score beats bear by 2+
      HOLD   — bull == bear (or +1)
      WAIT   — bear score beats bull
      AVOID  — strong downtrend / broken structure
    """
    if "error" in t or not t.get("price"):
        return {"ticker": t.get("ticker", "?"), "verdict": "NO_DATA",
                "bull": [], "bear": [], "levels": {}, "score": (0, 0)}

    bull: list[str] = []
    bear: list[str] = []
    p = t["price"]

    # --- trend structure ---------------------------------------------------
    if t.get("trend") == "uptrend":
        bull.append("uptrend intact: price > 50d > 200d")
    elif t.get("trend") == "downtrend":
        bear.append("downtrend: price < 50d < 200d")
    else:
        bull.append("neutral MA structure (mixed)")

    # --- RSI ---------------------------------------------------------------
    rsi = t.get("rsi14", 50)
    if rsi < 30:
        bull.append(f"RSI {rsi:.0f} — oversold, mean-reversion candidate")
    elif rsi < 40:
        bull.append(f"RSI {rsi:.0f} — near oversold, room to bounce")
    elif rsi > 70:
        bear.append(f"RSI {rsi:.0f} — overbought, pullback risk")
    elif rsi > 60:
        bull.append(f"RSI {rsi:.0f} — strong but not extreme")
    else:
        bull.append(f"RSI {rsi:.0f} — neutral, no extremes")

    # --- MACD --------------------------------------------------------------
    ms = t.get("macd_state", "")
    if ms in ("above_zero", "bullish_cross"):
        bull.append(f"MACD {ms} — momentum positive")
    elif ms in ("below_zero", "bearish_cross"):
        bear.append(f"MACD {ms} — momentum negative")

    # --- Bollinger ---------------------------------------------------------
    bb_pct = t.get("bb_pct", 0.5)
    bb_pos = t.get("bb_pos", "middle")
    if bb_pos == "lower":
        bull.append(f"BB at lower band ({bb_pct*100:.0f}%) — stretched downside")
    elif bb_pos == "upper":
        bear.append(f"BB at upper band ({bb_pct*100:.0f}%) — stretched upside")
    elif bb_pct > 0.65:
        bull.append(f"BB at {bb_pct*100:.0f}% — upper half, momentum positive")
    elif bb_pct < 0.35:
        bear.append(f"BB at {bb_pct*100:.0f}% — lower half, momentum negative")
    else:
        bull.append(f"BB at {bb_pct*100:.0f}% — middle of range, no extreme")

    # --- 5-day slope -------------------------------------------------------
    slope = t.get("slope_5d_pct", 0)
    if slope < -10:
        bear.append(f"5d slope {slope:+.1f}% — sharp recent drop")
    elif slope < -3:
        bear.append(f"5d slope {slope:+.1f}% — mild pullback")
    elif slope > 5:
        bull.append(f"5d slope {slope:+.1f}% — strong recent run")
    elif slope > 1:
        bull.append(f"5d slope {slope:+.1f}% — grinding higher")

    # --- volume trend ------------------------------------------------------
    vt = t.get("vol_trend", "normal")
    if vt == "rising":
        bull.append("volume rising (5d > 20d × 1.2) — conviction in current move")
    elif vt == "falling":
        bear.append("volume falling (5d < 20d × 0.8) — no conviction")

    # --- distance to MA50 --------------------------------------------------
    d50 = t.get("dist_ma50_pct", 0)
    if d50 < -5:
        bull.append(f"price {d50:+.1f}% below MA50 — deep-discount buy-the-dip")
    elif d50 > 10:
        bear.append(f"price {d50:+.1f}% above MA50 — extended, mean-reversion risk")

    # --- 52w high position -------------------------------------------------
    p52 = t.get("pct_from_52h", 0)
    if p52 > -5:
        bull.append(f"only {p52:+.1f}% from 52w high — breakout territory")
    elif p52 < -60:
        bear.append(f"{p52:+.1f}% from 52w high — heavy drawdown, recovery story")

    # --- verdict -----------------------------------------------------------
    score = len(bull) - len(bear)
    if t.get("trend") == "downtrend" and score < 2:
        verdict = "AVOID"
    elif score >= 2:
        verdict = "BUY"
    elif score >= 1:
        verdict = "HOLD"
    elif score == 0:
        verdict = "HOLD"
    else:
        verdict = "WAIT"

    # --- key levels --------------------------------------------------------
    ma50 = t.get("ma50", 0)
    ma200 = t.get("ma200", 0)
    lo60 = t.get("lo60", 0)
    hi60 = t.get("hi60", 0)
    levels = {
        "stop":       round(ma50 * 0.93, 2) if ma50 else 0,
        "support_1":  ma50,
        "support_2":  ma200,
        "support_3":  lo60,
        "resist_1":   hi60,
        "resist_2":   t.get("wk52_high", 0),
        "entry_now":  p,
        "entry_pullback": t.get("ma20", ma50),
    }
    return {
        "ticker": t["ticker"],
        "name": t.get("name", t["ticker"]),
        "price": p,
        "change_pct": t.get("change_pct", 0),
        "verdict": verdict,
        "score": (len(bull), len(bear)),
        "bull": bull,
        "bear": bear,
        "levels": levels,
        "rsi": rsi,
        "macd_state": ms,
        "bb_pct": bb_pct,
        "trend": t.get("trend", "neutral"),
        "vol_annual": t.get("vol_annual", 0),
        "slope_5d": slope,
    }


def score_all(tickers: list[str]) -> list[dict]:
    return [score_ticker(t) for t in fetch_all(tickers)]


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

    # Optional basic auth — read from env, never from a file. If neither is
    # set, auth is disabled (dev convenience). Set both DASHBOARD_USER and
    # DASHBOARD_PASSWORD to enable.
    app.config["AUTH_USER"] = os.environ.get("DASHBOARD_USER", "").strip()
    app.config["AUTH_PASSWORD"] = os.environ.get("DASHBOARD_PASSWORD", "").strip()
    app.config["AUTH_ENABLED"] = bool(
        app.config["AUTH_USER"] and app.config["AUTH_PASSWORD"]
    )

    def _check_auth() -> str | None:
        """Returns an error response if auth fails, else None."""
        if not app.config["AUTH_ENABLED"]:
            return None
        from flask import request
        # Browser dialog sends Basic auth header on every request.
        # We use hmac.compare_digest for the comparison so the response
        # time doesn't leak how many leading characters of the password
        # the attacker guessed correctly (constant-time compare).
        auth = request.authorization
        if not auth:
            return _unauth()
        expected_user = app.config["AUTH_USER"]
        expected_pass = app.config["AUTH_PASSWORD"]
        # hmac.compare_digest requires equal-length bytes; mismatch
        # lengths still return False in constant time, but we still
        # call it for both fields to avoid a length oracle.
        user_ok = hmac.compare_digest(
            auth.username.encode("utf-8"),
            expected_user.encode("utf-8"),
        )
        pass_ok = hmac.compare_digest(
            auth.password.encode("utf-8"),
            expected_pass.encode("utf-8"),
        )
        if not (user_ok and pass_ok):
            return _unauth()
        return None

    def _unauth():
        resp = jsonify({"error": "unauthorized"})
        resp.status_code = 401
        resp.headers["WWW-Authenticate"] = 'Basic realm="trading-bot"'
        return resp

    @app.route("/")
    def index():
        err = _check_auth()
        if err is not None:
            return err
        html = (Path(__file__).parent / "dashboard.html").read_text()
        return render_template_string(html)

    @app.route("/api/snapshot")
    def snapshot():
        err = _check_auth()
        if err is not None:
            return err
        return jsonify(build_snapshot(app.config["STATE_DB"]))

    @app.route("/api/analysis")
    def analysis():
        err = _check_auth()
        if err is not None:
            return err
        return jsonify({
            "tickers": score_all(WATCHLIST),
            "generated_at": datetime.now(ET).strftime("%Y-%m-%d %H:%M:%S ET"),
        })

    @app.route("/api/alerts")
    def alerts_list():
        err = _check_auth()
        if err is not None:
            return err
        # Read alerts from the state DB (if it exists)
        from broker.state import State
        try:
            st = State(app.config["STATE_DB"])
            rows = st.list_alerts(only_active=True)
            out = [{
                "id": r.id, "ticker": r.ticker, "kind": r.kind,
                "threshold": r.threshold, "note": r.note,
                "last_price": r.last_price,
                "created_at": r.created_at,
            } for r in rows]
        except Exception as e:
            out = []
            log.debug("could not read alerts: %s", e)
        return jsonify({"alerts": out})

    return app


# --------------------------------------------------------------------------- #
#  CLI                                                                        #
# --------------------------------------------------------------------------- #

def _port_in_use(host: str, port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.connect((host, port))
            return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            return False


def _find_free_port(host: str, start: int, max_tries: int = 20) -> int:
    for p in range(start, start + max_tries):
        if not _port_in_use(host, p):
            return p
    raise RuntimeError(f"no free port in {start}..{start + max_tries}")


def diagnose() -> int:
    """Print a one-shot diagnosis. Returns exit code."""
    print("═══ dashboard diagnosis ═══")
    # 1. Imports
    try:
        from flask import Flask  # noqa: F401
        print("  ✓ flask installed")
    except ImportError:
        print("  ✗ flask NOT installed — run: pip install flask")
        return 1
    try:
        import yfinance  # noqa: F401
        print("  ✓ yfinance installed")
    except ImportError:
        print("  ✗ yfinance NOT installed — run: pip install yfinance")
        return 1
    try:
        import numpy  # noqa: F401
        print(f"  ✓ numpy {numpy.__version__}")
    except ImportError:
        print("  ✗ numpy NOT installed — run: pip install numpy")
        return 1
    # 2. Data fetch
    print("  · fetching live quote for SOXL…", end=" ", flush=True)
    try:
        q = fetch_ticker("SOXL")
        if "error" in q:
            print(f"FAIL: {q['error']}")
            return 1
        print(f"${q['price']:.2f}")
    except Exception as e:
        print(f"FAIL: {e}")
        return 1
    # 3. Port availability
    for port in (5000, 8000, 8080, 5050):
        if not _port_in_use("127.0.0.1", port):
            print(f"  ✓ port {port} is free")
            break
    else:
        print("  ⚠ common dashboard ports are all in use — pass --port to choose one")
    # 4. State DB
    db = DEFAULT_STATE_DB
    if Path(db).exists():
        print(f"  ✓ state db found: {db}")
    else:
        print(f"  · state db not found at {db} (positions will be empty — that's OK)")
    # 5. Auth
    if os.environ.get("DASHBOARD_USER") and os.environ.get("DASHBOARD_PASSWORD"):
        print(f"  ✓ auth enabled (user={os.environ['DASHBOARD_USER']!r})")
    else:
        print("  · auth disabled (set DASHBOARD_USER + DASHBOARD_PASSWORD to enable)")
    print()
    print("diagnosis complete. start the server with: make dashboard")
    print("  or, if port 5000 is taken: python -m bot.dashboard --port 5050")
    return 0


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--state", default=DEFAULT_STATE_DB,
                   help="path to the trading-bot state SQLite db")
    p.add_argument("--debug", action="store_true")
    p.add_argument("--check", action="store_true",
                   help="diagnose dependencies and exit")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if args.check:
        raise SystemExit(diagnose())
    # Auto-fallback if the requested port is taken
    if _port_in_use(args.host, args.port):
        fallback = _find_free_port(args.host, args.port + 1)
        log.warning("port %d is in use — falling back to %d", args.port, fallback)
        args.port = fallback
    app = create_app(args.state)
    url = f"http://{args.host}:{args.port}"
    log.info("dashboard serving on %s (state=%s)", url, args.state)
    print()
    print(f"  ┌──────────────────────────────────────────┐")
    print(f"  │  open this in your browser:              │")
    print(f"  │                                          │")
    print(f"  │    {url:^38s} │")
    print(f"  │                                          │")
    print(f"  │  press Ctrl+C to stop                    │")
    print(f"  └──────────────────────────────────────────┘")
    print()
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
