"""Streamlit 4-page dashboard for realtime-crypto-sentiment.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Pages (tabs):
1. Overview       — KPI cards (cash, equity, today's PnL, signal counts).
2. Sentiment      — tweets_1m.avg_sentiment 5-min line; top-10 mentions bar.
3. Prices+Signals — dual-axis prices_1m + BUY/SELL markers.
4. Paper PnL      — equity curve, drawdown, win-rate gauge, trade log.

Auto-refresh: 60s by default (overridable via DASHBOARD_REFRESH env).

Read-only against TimescaleDB. No write paths.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Make the project root importable when launched via `streamlit run dashboard/app.py`
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from loguru import logger
from sqlalchemy import text

from src.config import settings
from src.store import db

# ── Streamlit page config (must be first st call) ────────────────────────

st.set_page_config(
    page_title="Realtime Crypto Sentiment",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
    initial_sidebar_state="expanded",
)

REFRESH_MS = int(os.environ.get("DASHBOARD_REFRESH", "60000"))

try:
    from streamlit_autorefresh import st_autorefresh

    st_autorefresh(interval=REFRESH_MS, key="auto-refresh")
except Exception as e:  # pragma: no cover
    st.sidebar.warning(f"streamlit-autorefresh unavailable: {e}")


# ── Data accessors (cached) ──────────────────────────────────────────────

@st.cache_data(ttl=30, show_spinner=False)
def _query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Run a read-only SQL and return a DataFrame. Cached 30s."""
    engine = db.get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def _kpis() -> dict:
    """Compute dashboard KPIs from `paper_trades` and `positions`."""
    trades = _query(
        "SELECT ts, side, qty, price_usd, fee_usd, cash_after, symbol "
        "FROM paper_trades ORDER BY ts DESC LIMIT 500"
    )
    last_cash = float(trades["cash_after"].iloc[0]) if not trades.empty else settings.starting_cash_usd
    positions = _query(
        "SELECT ts, symbol, qty, avg_price, realized_pnl FROM positions "
        "WHERE qty > 0 ORDER BY ts DESC"
    )
    # Mark-to-market with the latest price per symbol
    if not positions.empty:
        latest = _query(
            "SELECT DISTINCT ON (symbol) symbol, price_usd FROM prices "
            "ORDER BY symbol, ts DESC"
        )
        positions = positions.merge(latest, on="symbol", how="left")
        positions["mkt_value"] = positions["qty"] * positions["price_usd"].fillna(positions["avg_price"])
    else:
        positions["mkt_value"] = []
    position_value = float(positions["mkt_value"].sum()) if not positions.empty else 0.0
    equity = last_cash + position_value
    # Realized PnL
    realized = float(positions["realized_pnl"].sum()) if not positions.empty else 0.0
    # Today's PnL = sum realized + sum unrealized since today's first trade
    today = datetime.utcnow().date().isoformat()
    today_trades = trades[trades["ts"].astype(str).str.startswith(today)] if not trades.empty else trades
    return {
        "cash": last_cash,
        "equity": equity,
        "position_value": position_value,
        "realized_pnl": realized,
        "trade_count": int(len(trades)),
        "today_trades": int(len(today_trades)),
    }


def _signal_counts() -> pd.DataFrame:
    return _query(
        "SELECT action, COUNT(*) AS n FROM signals "
        "WHERE ts > NOW() - INTERVAL '24 hours' "
        "GROUP BY action ORDER BY n DESC"
    )


def _sentiment_per_symbol(minutes: int = 60) -> pd.DataFrame:
    """Avg sentiment per symbol over the last `minutes` minutes."""
    if db.get_engine().dialect.name == "postgresql":
        return _query(
            "SELECT symbol, AVG(sentiment_score) AS avg_sent, COUNT(*) AS n "
            "FROM tweets "
            "WHERE sentiment_score IS NOT NULL "
            "AND ts > NOW() - (:m || ' minutes')::INTERVAL "
            "GROUP BY symbol ORDER BY avg_sent DESC",
            {"m": str(minutes)},
        )
    return _query(
        "SELECT symbol, AVG(sentiment_score) AS avg_sent, COUNT(*) AS n "
        "FROM tweets "
        "WHERE sentiment_score IS NOT NULL "
        "AND ts > datetime('now', :m) "
        "GROUP BY symbol ORDER BY avg_sent DESC",
        {"m": f"-{minutes} minutes"},
    )


def _tweet_volume_5m() -> pd.DataFrame:
    """Time-bucketed tweet count + avg sentiment over the last 5 min."""
    if db.get_engine().dialect.name == "postgresql":
        return _query(
            "SELECT time_bucket('1 minute', ts) AS bucket, "
            "COUNT(*) AS tweets, AVG(sentiment_score) AS avg_sent "
            "FROM tweets "
            "WHERE ts > NOW() - INTERVAL '5 minutes' "
            "AND sentiment_score IS NOT NULL "
            "GROUP BY bucket ORDER BY bucket ASC"
        )
    return _query(
        "SELECT strftime('%Y-%m-%d %H:%M:00', ts) AS bucket, "
        "COUNT(*) AS tweets, AVG(sentiment_score) AS avg_sent "
        "FROM tweets WHERE ts > datetime('now', '-5 minutes') "
        "AND sentiment_score IS NOT NULL "
        "GROUP BY bucket ORDER BY bucket ASC"
    )


def _top_mentions(limit: int = 10) -> pd.DataFrame:
    """Top-N symbols by tweet count over the last hour."""
    if db.get_engine().dialect.name == "postgresql":
        return _query(
            "SELECT symbol, COUNT(*) AS mentions FROM tweets "
            "WHERE ts > NOW() - INTERVAL '1 hour' "
            "GROUP BY symbol ORDER BY mentions DESC LIMIT :lim",
            {"lim": limit},
        )
    return _query(
        "SELECT symbol, COUNT(*) AS mentions FROM tweets "
        "WHERE ts > datetime('now', '-1 hour') "
        "GROUP BY symbol ORDER BY mentions DESC LIMIT :lim",
        {"lim": limit},
    )


def _price_series(symbol: str, hours: int = 1) -> pd.DataFrame:
    if db.get_engine().dialect.name == "postgresql":
        return _query(
            "SELECT bucket, close FROM prices_1m "
            "WHERE symbol=:s AND bucket > NOW() - (:h || ' hours')::INTERVAL "
            "ORDER BY bucket ASC",
            {"s": symbol, "h": str(hours)},
        )
    return _query(
        "SELECT ts AS bucket, price_usd AS close FROM prices "
        "WHERE symbol=:s AND ts > datetime('now', :h) ORDER BY ts ASC",
        {"s": symbol, "h": f"-{hours} hours"},
    )


def _signals(symbol: str, hours: int = 1) -> pd.DataFrame:
    if db.get_engine().dialect.name == "postgresql":
        return _query(
            "SELECT ts, action, score, sentiment_zscore, momentum_zscore, reason "
            "FROM signals "
            "WHERE symbol=:s AND ts > NOW() - (:h || ' hours')::INTERVAL "
            "ORDER BY ts ASC",
            {"s": symbol, "h": str(hours)},
        )
    return _query(
        "SELECT ts, action, score, sentiment_zscore, momentum_zscore, reason "
        "FROM signals WHERE symbol=:s AND ts > datetime('now', :h) ORDER BY ts ASC",
        {"s": symbol, "h": f"-{hours} hours"},
    )


def _trade_log(limit: int = 100) -> pd.DataFrame:
    return _query(
        "SELECT ts, symbol, side, qty, price_usd, fee_usd, cash_after, reason "
        "FROM paper_trades ORDER BY ts DESC LIMIT :lim",
        {"lim": limit},
    )


def _equity_curve(hours: int = 24) -> pd.DataFrame:
    """Build a mark-to-market equity curve by joining prices + positions over time.

    Cheap approximation: re-evaluate equity at the close of each 1-min bucket by
    replaying the paper_trade cash balance forward and applying price moves.
    """
    if db.get_engine().dialect.name == "postgresql":
        prices = _query(
            "SELECT bucket, symbol, close FROM prices_1m "
            "WHERE bucket > NOW() - (:h || ' hours')::INTERVAL "
            "ORDER BY bucket ASC, symbol ASC",
            {"h": str(hours)},
        )
    else:
        prices = _query(
            "SELECT ts AS bucket, symbol, price_usd AS close FROM prices "
            "WHERE ts > datetime('now', :h) ORDER BY ts ASC, symbol ASC",
            {"h": f"-{hours} hours"},
        )
    trades = _query(
        "SELECT ts, symbol, side, qty, price_usd, cash_after FROM paper_trades "
        "ORDER BY ts ASC"
    )
    if prices.empty:
        return pd.DataFrame(columns=["ts", "equity"])
    # Pivot to wide: rows=bucket, columns=symbol
    pv = prices.pivot_table(index="bucket", columns="symbol", values="close").sort_index()
    eq = pd.Series(index=pv.index, dtype=float)
    cash = settings.starting_cash_usd
    qty: dict[str, float] = {}
    cost_basis: dict[str, float] = {}  # for unrealized
    trade_iter = iter(trades.to_dict("records")) if not trades.empty else iter(())
    next_trade = next(trade_iter, None)
    pv_iter = pv.iterrows()
    for ts, row in pv_iter:
        # Apply any trades that occurred at-or-before this ts
        while next_trade is not None and pd.Timestamp(next_trade["ts"]) <= pd.Timestamp(ts):
            cash = float(next_trade["cash_after"])
            if next_trade["side"] == "BUY":
                qty[next_trade["symbol"]] = qty.get(next_trade["symbol"], 0.0) + float(next_trade["qty"])
                cost_basis[next_trade["symbol"]] = float(next_trade["price_usd"])
            else:  # SELL closes the position
                qty[next_trade["symbol"]] = 0.0
                cost_basis[next_trade["symbol"]] = 0.0
            next_trade = next(trade_iter, None)
        # Mark-to-market
        m2m = sum(
            qty.get(s, 0.0) * float(p) for s, p in row.items() if pd.notna(p) and qty.get(s, 0.0) > 0
        )
        eq.loc[ts] = cash + m2m
    eq = eq.fillna(method="ffill").fillna(settings.starting_cash_usd)
    return pd.DataFrame({"ts": eq.index, "equity": eq.values})


# ── UI helpers ───────────────────────────────────────────────────────────

def _kpi_card(label: str, value: str, delta: str | None = None) -> None:
    st.metric(label=label, value=value, delta=delta)


def _render_header() -> None:
    st.title(":chart_with_upwards_trend: Realtime Crypto Sentiment")
    st.caption(
        f"Refresh every {REFRESH_MS // 1000}s · DB: `{settings.database_url.split('@')[-1]}` · "
        f"Last render: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    st.caption(
        ":warning: **Decision-support only — not financial advice.** "
        "Paper-trades simulated at last-tick. Past performance ≠ future results. "
        "See `docs/trading_disclaimer.md`."
    )


# ── Pages ────────────────────────────────────────────────────────────────

def page_overview() -> None:
    st.subheader("Overview")
    try:
        k = _kpis()
    except Exception as e:
        st.error(f"DB error: {e}")
        return

    cols = st.columns(4)
    cols[0].metric("Cash (USD)", f"${k['cash']:,.2f}")
    cols[1].metric("Equity (USD)", f"${k['equity']:,.2f}")
    cols[2].metric("Today's trades", str(k["today_trades"]))
    cols[3].metric("Realized PnL (USD)", f"${k['realized_pnl']:+,.2f}")

    st.markdown("### Open positions")
    positions = _query(
        "SELECT symbol, qty, avg_price, realized_pnl FROM positions "
        "WHERE qty > 0 ORDER BY symbol"
    )
    if positions.empty:
        st.info("No open positions yet. Run `make pipeline` in another terminal to start trading.")
    else:
        latest = _query("SELECT DISTINCT ON (symbol) symbol, price_usd FROM prices ORDER BY symbol, ts DESC")
        merged = positions.merge(latest, on="symbol", how="left")
        merged["mkt_value"] = merged["qty"] * merged["price_usd"].fillna(merged["avg_price"])
        merged["unrealized_pnl"] = (merged["price_usd"].fillna(merged["avg_price"]) - merged["avg_price"]) * merged["qty"]
        st.dataframe(
            merged[["symbol", "qty", "avg_price", "price_usd", "mkt_value", "unrealized_pnl", "realized_pnl"]]
            .round(4)
            .style.format({
                "avg_price": "${:.2f}",
                "price_usd": "${:.2f}",
                "mkt_value": "${:.2f}",
                "unrealized_pnl": "${:+.2f}",
                "realized_pnl": "${:+.2f}",
            }),
            use_container_width=True,
        )

    st.markdown("### 24h signal mix")
    try:
        sc = _signal_counts()
    except Exception as e:
        st.error(f"signal query failed: {e}")
        sc = pd.DataFrame()
    if sc.empty:
        st.info("No signals in the last 24h yet.")
    else:
        st.bar_chart(sc.set_index("action"))


def page_sentiment() -> None:
    st.subheader("Sentiment")
    window = st.slider("Lookback (minutes)", 5, 240, 60, step=5)
    avg = _sentiment_per_symbol(minutes=window)
    if avg.empty:
        st.info("No scored tweets in window yet. Start the pipeline and wait ~60s for first scrape cycle.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### Avg sentiment by symbol (last {window}m)")
        chart = avg.set_index("symbol")[["avg_sent"]]
        st.bar_chart(chart, color="#1f77b4")

    with c2:
        st.markdown(f"### Tweet volume by symbol (last 1h)")
        tm = _top_mentions(limit=10)
        if tm.empty:
            st.info("No tweet activity yet.")
        else:
            fig = px.bar(tm, x="symbol", y="mentions", title="Top symbols by mentions")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 5-min sentiment timeline")
    tv = _tweet_volume_5m()
    if tv.empty:
        st.info("Not enough recent scored tweets.")
    else:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=tv["bucket"], y=tv["tweets"], name="Tweets", marker_color="#7f7f7f", opacity=0.5))
        fig.add_trace(go.Scatter(
            x=tv["bucket"], y=tv["avg_sent"], name="Avg sentiment",
            yaxis="y2", line=dict(color="#d62728", width=2),
        ))
        fig.update_layout(
            yaxis=dict(title="Tweet count"),
            yaxis2=dict(title="Avg sentiment", overlaying="y", side="right", range=[-1, 1]),
            height=350, margin=dict(l=40, r=40, t=30, b=30),
        )
        st.plotly_chart(fig, use_container_width=True)


def page_prices_signals() -> None:
    st.subheader("Prices + Signals")
    symbols = settings.symbols
    sym = st.selectbox("Symbol", options=symbols, index=0)
    hours = st.slider("Window (hours)", 1, 24, 6, step=1)

    px_df = _price_series(sym, hours=hours)
    sig_df = _signals(sym, hours=hours)

    if px_df.empty:
        st.info(f"No price data for {sym} in last {hours}h. Start the pipeline and wait ~30s.")
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=px_df["bucket"], y=px_df["close"], name=f"{sym} price",
        line=dict(color="#1f77b4", width=2),
    ))
    if not sig_df.empty:
        buys = sig_df[sig_df["action"] == "BUY"]
        sells = sig_df[sig_df["action"] == "SELL"]
        if not buys.empty:
            fig.add_trace(go.Scatter(
                x=buys["ts"], y=px_df.set_index("bucket")["close"].reindex(buys["ts"], method="nearest").values,
                mode="markers", name="BUY", marker=dict(symbol="triangle-up", size=12, color="#2ca02c"),
            ))
        if not sells.empty:
            fig.add_trace(go.Scatter(
                x=sells["ts"], y=px_df.set_index("bucket")["close"].reindex(sells["ts"], method="nearest").values,
                mode="markers", name="SELL", marker=dict(symbol="triangle-down", size=12, color="#d62728"),
            ))
    fig.update_layout(height=500, xaxis_title="time (UTC)", yaxis_title="price (USD)")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Recent signals")
    if sig_df.empty:
        st.info("No signals in window.")
    else:
        st.dataframe(
            sig_df.sort_values("ts", ascending=False).head(50).reset_index(drop=True),
            use_container_width=True,
        )


def page_paper_pnl() -> None:
    st.subheader("Paper PnL")
    hours = st.slider("Window (hours)", 1, 168, 24, step=1)

    eq = _equity_curve(hours=hours)
    if eq.empty:
        st.info("No equity data yet. Run the pipeline for a few minutes.")
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=eq["ts"], y=eq["equity"], name="Equity (USD)", fill="tozeroy", line=dict(color="#2ca02c")))
    # Drawdown overlay
    running_max = eq["equity"].cummax()
    dd = running_max - eq["equity"]
    fig.add_trace(go.Scatter(x=eq["ts"], y=dd, name="Drawdown (USD)", yaxis="y2", line=dict(color="#d62728", width=1)))
    fig.update_layout(
        height=400,
        yaxis=dict(title="Equity (USD)"),
        yaxis2=dict(title="Drawdown (USD)", overlaying="y", side="right"),
        margin=dict(l=40, r=40, t=30, b=30),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Trade stats
    log = _trade_log(limit=500)
    if log.empty:
        st.info("No paper trades yet.")
    else:
        sells = log[log["side"] == "SELL"]
        wins = 0
        if not sells.empty:
            # Approx win-rate by realized PnL on each sell row's cash_after delta
            sells_sorted = sells.sort_values("ts")
            cash_before = sells_sorted["cash_after"].shift(1, fill_value=settings.starting_cash_usd)
            pnl = sells_sorted["cash_after"] - cash_before
            wins = int((pnl > 0).sum())
        total = len(sells)
        win_rate = (wins / total) if total else 0.0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Trades", str(len(log)))
        c2.metric("Sells (closed)", str(total))
        c3.metric("Win rate", f"{win_rate:.0%}")
        c4.metric("Total fees (USD)", f"${log['fee_usd'].sum():.2f}")

        st.markdown("### Trade log (most recent 100)")
        st.dataframe(
            log.head(100).style.format({
                "qty": "{:.6f}",
                "price_usd": "${:.2f}",
                "fee_usd": "${:.4f}",
                "cash_after": "${:,.2f}",
            }),
            use_container_width=True,
        )


# ── Main ─────────────────────────────────────────────────────────────────

def main() -> None:
    _render_header()
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Sentiment", "Prices + Signals", "Paper PnL"])
    with tab1:
        page_overview()
    with tab2:
        page_sentiment()
    with tab3:
        page_prices_signals()
    with tab4:
        page_paper_pnl()

    with st.sidebar:
        st.markdown("### Status")
        try:
            n_tweets = int(_query("SELECT COUNT(*) AS n FROM tweets").iloc[0]["n"])
            n_prices = int(_query("SELECT COUNT(*) AS n FROM prices").iloc[0]["n"])
            n_signals = int(_query("SELECT COUNT(*) AS n FROM signals").iloc[0]["n"])
            n_trades = int(_query("SELECT COUNT(*) AS n FROM paper_trades").iloc[0]["n"])
            st.write(f"Tweets: **{n_tweets:,}**")
            st.write(f"Prices: **{n_prices:,}**")
            st.write(f"Signals: **{n_signals:,}**")
            st.write(f"Paper trades: **{n_trades:,}**")
        except Exception as e:
            st.error(f"DB unreachable: {e}")
        st.markdown("---")
        st.caption("v0.1 · ProsusAI/FinBERT + Binance WS + Nitter mirrors")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("dashboard crashed")
        st.error("Dashboard error — see terminal logs.")
