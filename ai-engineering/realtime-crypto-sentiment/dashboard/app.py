"""Streamlit 4-page dashboard for realtime-x-sentiment.

Author: Prem Vishnoi <pvishnoi@avishnoi@avilx.com>

Pages (tabs):
1. Overview       — KPI cards (cash, equity, today's PnL, signal counts).
2. Sentiment      — avg sentiment per tracked tag, 5-min timeline.
3. Paper PnL      — equity curve (cash-after), trade log, win-rate gauge.
4. 🔥 Trending   — top-10 cashtags/hashtags/keywords in the last 5 min.

Auto-refresh: 60s by default (overridable via DASHBOARD_REFRESH env).

Read-only against TimescaleDB. No write paths.

Note: there is no live price feed. The paper broker uses synthetic
unit prices derived from tweet engagement, so all monetary figures
are in "units" (not USD).
"""
from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
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
    page_title="Real-time X.com Sentiment",
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
        "SELECT ts, side, qty, price, fee, cash_after, symbol "
        "FROM paper_trades ORDER BY ts DESC LIMIT 500"
    )
    last_cash = float(trades["cash_after"].iloc[0]) if not trades.empty else settings.starting_units
    positions = _query(
        "SELECT ts, symbol, qty, avg_price, realized_pnl FROM positions "
        "WHERE qty > 0 ORDER BY ts DESC"
    )
    # Mark-to-market: no live price feed, so positions are valued at
    # their avg_price (no unrealized PnL component).
    if not positions.empty:
        positions["mkt_value"] = positions["qty"] * positions["avg_price"]
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
        "trade_count": len(trades),
        "today_trades": len(today_trades),
    }


def _signal_counts() -> pd.DataFrame:
    if db.get_engine().dialect.name == "postgresql":
        return _query(
            "SELECT action, COUNT(*) AS n FROM signals "
            "WHERE ts > NOW() - INTERVAL '24 hours' "
            "GROUP BY action ORDER BY n DESC"
        )
    return _query(
        "SELECT action, COUNT(*) AS n FROM signals "
        "WHERE ts > datetime('now', '-24 hours') "
        "GROUP BY action ORDER BY n DESC"
    )


def _sentiment_per_symbol(minutes: int = 60) -> pd.DataFrame:
    """Avg sentiment per tag over the last `minutes` minutes."""
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
        df = _query(
            "SELECT time_bucket('1 minute', ts) AS bucket, "
            "COUNT(*) AS tweets, AVG(sentiment_score) AS avg_sent "
            "FROM tweets "
            "WHERE ts > NOW() - INTERVAL '5 minutes' "
            "AND sentiment_score IS NOT NULL "
            "GROUP BY bucket ORDER BY bucket ASC"
        )
    else:
        df = _query(
            "SELECT strftime('%Y-%m-%d %H:%M:00', ts) AS bucket, "
            "COUNT(*) AS tweets, AVG(sentiment_score) AS avg_sent "
            "FROM tweets WHERE ts > datetime('now', '-5 minutes') "
            "AND sentiment_score IS NOT NULL "
            "GROUP BY bucket ORDER BY bucket ASC"
        )
    if not df.empty and "bucket" in df.columns:
        df["bucket"] = pd.to_datetime(df["bucket"], utc=True)
    return df


def _top_mentions(limit: int = 10) -> pd.DataFrame:
    """Top-N tags by tweet count over the last hour."""
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


def _signals(symbol: str, hours: int = 1) -> pd.DataFrame:
    if db.get_engine().dialect.name == "postgresql":
        df = _query(
            "SELECT ts, action, score, sentiment_zscore, momentum_zscore, reason "
            "FROM signals "
            "WHERE symbol=:s AND ts > NOW() - (:h || ' hours')::INTERVAL "
            "ORDER BY ts ASC",
            {"s": symbol, "h": str(hours)},
        )
    else:
        df = _query(
            "SELECT ts, action, score, sentiment_zscore, momentum_zscore, reason "
            "FROM signals WHERE symbol=:s AND ts > datetime('now', :h) ORDER BY ts ASC",
            {"s": symbol, "h": f"-{hours} hours"},
        )
    if not df.empty and "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"], utc=True)
    return df


def _trade_log(limit: int = 100) -> pd.DataFrame:
    df = _query(
        "SELECT ts, symbol, side, qty, price, fee, cash_after, reason "
        "FROM paper_trades ORDER BY ts DESC LIMIT :lim",
        {"lim": limit},
    )
    if not df.empty and "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"], utc=True)
    return df


@st.cache_data(ttl=30)
def _trending_tags(minutes: int = 5, limit: int = 10) -> pd.DataFrame:
    """Top-N tags (cashtags, hashtags, keywords) by mention count over
    the last `minutes` minutes. Returns DataFrame with columns:
    tag, kind, total_count, avg_sentiment, sample_text, sample_url.
    """
    rows = db.fetch_trending_tags(minutes=minutes, limit=limit)
    if not rows:
        # Always return a DataFrame with the expected columns so callers
        # can use `df.empty`, `df["kind"]`, etc. without type-checking.
        return pd.DataFrame(columns=[
            "tag", "kind", "total_count", "avg_sentiment",
            "sample_text", "sample_url",
        ])
    df = pd.DataFrame(rows)
    # Normalize DB-schema names → dashboard-contract names.
    if "tag_kind" in df.columns and "kind" not in df.columns:
        df = df.rename(columns={"tag_kind": "kind"})
    if "avg_sent" in df.columns and "avg_sentiment" not in df.columns:
        df = df.rename(columns={"avg_sent": "avg_sentiment"})
    return df


# ── UI helpers ───────────────────────────────────────────────────────────

def _kpi_card(label: str, value: str, delta: str | None = None) -> None:
    st.metric(label=label, value=value, delta=delta)


def _render_header() -> None:
    st.title(":chart_with_upwards_trend: Real-time X.com Sentiment")
    st.caption(
        f"Refresh every {REFRESH_MS // 1000}s · DB: `{settings.database_url.split('@')[-1]}` · "
        f"Last render: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    st.caption(
        ":warning: **Decision-support only — not financial advice.** "
        "Paper-trades are simulated at synthetic unit prices derived from "
        "tweet engagement. Past performance ≠ future results. See "
        "`docs/trading_disclaimer.md`."
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
    cols[0].metric("Cash (units)", f"{k['cash']:,.2f}")
    cols[1].metric("Equity (units)", f"{k['equity']:,.2f}")
    cols[2].metric("Today's trades", str(k["today_trades"]))
    cols[3].metric("Realized PnL (units)", f"{k['realized_pnl']:+,.2f}")

    st.markdown("### Open positions")
    # Use the helper that picks the LATEST snapshot per symbol, then
    # filters to qty > 0. A position that was opened (qty=10) and
    # subsequently closed (qty=0) should NOT show as open, even though
    # the opening row has qty > 0.
    open_pos = db.all_open_positions()
    if not open_pos:
        positions = pd.DataFrame(columns=["symbol", "qty", "avg_price", "realized_pnl"])
    else:
        positions = pd.DataFrame(open_pos)[["symbol", "qty", "avg_price", "realized_pnl"]]
    if positions.empty:
        st.info("No open positions yet. Run `make pipeline` in another terminal to start trading.")
    else:
        # No live price feed → unrealized PnL is always 0.
        positions["mkt_value"] = positions["qty"] * positions["avg_price"]
        positions["unrealized_pnl"] = 0.0
        st.dataframe(
            positions[["symbol", "qty", "avg_price", "mkt_value", "unrealized_pnl", "realized_pnl"]]
            .round(4)
            .style.format({
                "avg_price": "{:.2f}",
                "mkt_value": "{:.2f}",
                "unrealized_pnl": "{:+.2f}",
                "realized_pnl": "{:+.2f}",
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
        st.markdown(f"### Avg sentiment by tag (last {window}m)")
        chart = avg.set_index("symbol")[["avg_sent"]]
        st.bar_chart(chart, color="#1f77b4")

    with c2:
        st.markdown("### Tweet volume by tag (last 1h)")
        tm = _top_mentions(limit=10)
        if tm.empty:
            st.info("No tweet activity yet.")
        else:
            fig = px.bar(tm, x="symbol", y="mentions", title="Top tags by mentions")
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
            yaxis="y2", line={"color": "#d62728", "width": 2},
        ))
        fig.update_layout(
            yaxis={"title": "Tweet count"},
            yaxis2={"title": "Avg sentiment", "overlaying": "y", "side": "right", "range": [-1, 1]},
            height=350, margin={"l": 40, "r": 40, "t": 30, "b": 30},
        )
        st.plotly_chart(fig, use_container_width=True)


def page_paper_pnl() -> None:
    st.subheader("Paper PnL")
    hours = st.slider("Window (hours)", 1, 168, 24, step=1)
    cutoff = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=hours)).to_pydatetime()

    # Equity curve from cash_after of paper_trades (no live mark-to-market
    # since there is no real price feed).
    trades = _query(
        "SELECT ts, side, qty, price, fee, cash_after FROM paper_trades "
        "WHERE ts > :cutoff ORDER BY ts ASC",
        {"cutoff": cutoff},
    )
    if trades.empty:
        st.info("No paper trades in the selected window. Run the pipeline for a few minutes.")
        return

    trades["ts"] = pd.to_datetime(trades["ts"], utc=True)
    eq = trades[["ts", "cash_after"]].rename(columns={"cash_after": "equity"})

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=eq["ts"], y=eq["equity"], name="Equity (units)", fill="tozeroy", line={"color": "#2ca02c"}))
    # Drawdown overlay
    running_max = eq["equity"].cummax()
    dd = running_max - eq["equity"]
    fig.add_trace(go.Scatter(x=eq["ts"], y=dd, name="Drawdown (units)", yaxis="y2", line={"color": "#d62728", "width": 1}))
    fig.update_layout(
        height=400,
        yaxis={"title": "Equity (units)"},
        yaxis2={"title": "Drawdown (units)", "overlaying": "y", "side": "right"},
        margin={"l": 40, "r": 40, "t": 30, "b": 30},
    )
    st.plotly_chart(fig, use_container_width=True)

    # Trade stats — fetch the full log then filter in pandas (the SQL filter
    # is already applied above for the equity curve; here we want all rows
    # within the window for the win-rate calculation).
    log = _trade_log(limit=500)
    if not log.empty:
        log = log[log["ts"] >= cutoff]
    if log.empty:
        st.info("No paper trades in the selected window.")
    else:
        sells = log[log["side"] == "SELL"]
        wins = 0
        if not sells.empty:
            # Approx win-rate by realized PnL on each sell row's cash_after delta
            sells_sorted = sells.sort_values("ts")
            cash_before = sells_sorted["cash_after"].shift(1, fill_value=settings.starting_units)
            pnl = sells_sorted["cash_after"] - cash_before
            wins = int((pnl > 0).sum())
        total = len(sells)
        win_rate = (wins / total) if total else 0.0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Trades", str(len(log)))
        c2.metric("Sells (closed)", str(total))
        c3.metric("Win rate", f"{win_rate:.0%}")
        c4.metric("Total fees (units)", f"{log['fee'].sum():.2f}")

        st.markdown("### Trade log (most recent 100)")
        st.dataframe(
            log.head(100).style.format({
                "qty": "{:.6f}",
                "price": "{:.2f}",
                "fee": "{:.4f}",
                "cash_after": "{:,.2f}",
            }),
            use_container_width=True,
        )


def page_trending() -> None:
    """Top-10 trending tags on X.com right now, with sentiment, sample
    tweet, and a per-vertical breakdown. Mixes AI/data + stocks +
    dating so the panel isn't single-domain.
    """
    st.subheader("🔥 Trending tags (X.com)")
    minutes = st.slider("Window (minutes)", 1, 60, settings.trending_window_minutes, step=1)
    top_n = st.slider("Top N", 5, 25, settings.trending_top_n, step=1)

    df = _trending_tags(minutes=minutes, limit=top_n)
    if df.empty:
        st.info(
            f"No trending-tag data yet. The pipeline scrapes every "
            f"{settings.scrape_interval_sec}s; give it 1-2 minutes. "
            f"You can also run `make pipeline` in another terminal."
        )
        return

    # ── Bar chart: total mentions per tag, color by kind ─────────────────
    color_map = {
        "cashtag": "#1f77b4",
        "hashtag": "#ff7f0e",
        "keyword": "#2ca02c",
    }
    fig = go.Figure()
    for kind in ["cashtag", "hashtag", "keyword"]:
        sub = df[df["kind"] == kind]
        if not sub.empty:
            fig.add_trace(go.Bar(
                x=sub["total_count"], y=sub["tag"], orientation="h",
                name=kind, marker_color=color_map[kind],
                text=sub["total_count"], textposition="outside",
            ))
    fig.update_layout(
        height=400,
        xaxis_title="mentions (last window)",
        yaxis={"autorange": "reversed"},
        barmode="group",
        margin={"l": 100, "r": 40, "t": 30, "b": 30},
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Detail table: tag, kind, count, sentiment, sample tweet ─────────
    st.markdown("### Detail")
    show = df.copy()
    show["avg_sentiment"] = show["avg_sentiment"].fillna(0.0)
    show["link"] = show["sample_url"].apply(
        lambda u: f"[tweet]({u})" if isinstance(u, str) and u else "—"
    )
    st.dataframe(
        show[["tag", "kind", "total_count", "avg_sentiment", "sample_text", "link"]]
        .rename(columns={
            "tag": "Tag", "kind": "Kind", "total_count": "Mentions",
            "avg_sentiment": "Avg sentiment", "sample_text": "Sample tweet",
            "link": "Link",
        })
        .style.format({
            "Mentions": "{:,.0f}",
            "Avg sentiment": "{:+.2f}",
            "Sample tweet": lambda s: (s[:80] + "…") if isinstance(s, str) and len(s) > 80 else s,
        })
        .bar(subset=["Mentions"], color="#7f7f7f")
        .bar(subset=["Avg sentiment"], color="#d62728", align="mid"),
        use_container_width=True,
        height=400,
    )


# ── Live tab (hourly + daily aggregates) ────────────────────────────────

@st.cache_data(ttl=30)
def _global_buckets(minutes: int, hours: int) -> pd.DataFrame:
    rows = db.global_sentiment_buckets(minutes=minutes, hours=hours)
    if not rows:
        return pd.DataFrame(columns=["bucket", "avg_sent", "n", "pos_n", "neg_n"])
    df = pd.DataFrame(rows)
    df["bucket"] = pd.to_datetime(df["bucket"], unit="s", utc=True)
    return df


@st.cache_data(ttl=30)
def _per_symbol_buckets_df(minutes: int, hours: int) -> pd.DataFrame:
    rows = db.per_symbol_buckets(minutes=minutes, hours=hours)
    if not rows:
        return pd.DataFrame(columns=["bucket", "symbol", "avg_sent", "n"])
    df = pd.DataFrame(rows)
    df["bucket"] = pd.to_datetime(df["bucket"], unit="s", utc=True)
    return df


@st.cache_data(ttl=30)
def _daily_topics(days: int = 7, limit: int = 50) -> pd.DataFrame:
    """Top topics per day (with velocity, reach, unique authors).

    Note: the SQL helper returns `day` as an integer day-number
    (epoch_seconds / 86400). Convert to a Timestamp by multiplying by 86400
    and using `unit="s"`.
    """
    rows = db.daily_topic_aggregates(days=days, limit=limit)
    if not rows:
        return pd.DataFrame(columns=[
            "day", "symbol", "tweet_count", "unique_authors", "total_likes",
            "total_retweets", "total_reach", "avg_sentiment", "pos_count",
            "neg_count", "velocity",
        ])
    df = pd.DataFrame(rows)
    df["day"] = pd.to_datetime(df["day"].astype(int) * 86400, unit="s", utc=True)
    return df


def page_live() -> None:
    """Live macro view — hourly + daily sentiment aggregated across ALL
    tracked tags. Useful for spotting regime shifts (24h mood swing,
    daily trend) rather than the noisy 5-min view on the Trending tab.
    """
    st.subheader("📡 Live aggregates (hourly + daily)")
    timeframe = st.radio(
        "Bucket size", ["Hourly (1h, last 48h)", "Daily (1d, last 30d)"],
        horizontal=True,
    )
    if timeframe.startswith("Hourly"):
        minutes, hours = 60, 48
        title_avg, title_volume = "Avg sentiment per hour (last 48h)", "Tweet volume per hour (last 48h)"
    else:
        minutes, hours = 60 * 24, 30 * 24
        title_avg, title_volume = "Avg sentiment per day (last 30d)", "Tweet volume per day (last 30d)"

    # ── Cross-tag aggregate ─────────────────────────────────────────────
    g = _global_buckets(minutes, hours)
    if g.empty:
        st.info(
            "No scored tweets in this window yet. Start the pipeline "
            "and give it a few minutes for buckets to fill."
        )
        return

    # Header KPIs from the latest bucket
    latest = g.iloc[-1]
    delta = g["avg_sent"].iloc[-1] - g["avg_sent"].iloc[-2] if len(g) > 1 else 0.0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        f"{'Latest hour' if minutes == 60 else 'Latest day'} avg sentiment",
        f"{latest['avg_sent']:+.3f}",
        delta=f"{delta:+.3f}",
    )
    c2.metric("Tweets", f"{int(latest['n']):,}")
    c3.metric("Positive", f"{int(latest['pos_n']):,}")
    c4.metric("Negative", f"{int(latest['neg_n']):,}")

    # ── Stacked bars: positive vs negative tweet volume per bucket ────
    st.markdown(f"### {title_volume}")
    g["neg_n"] = g["neg_n"].astype(float)
    g["pos_n"] = g["pos_n"].astype(float)
    g["neu_n"] = (g["n"] - g["pos_n"] - g["neg_n"]).clip(lower=0)
    bar_df = g.set_index("bucket")[["pos_n", "neu_n", "neg_n"]]
    bar_df.columns = ["Positive", "Neutral", "Negative"]
    st.bar_chart(bar_df, color=["#2ca02c", "#7f7f7f", "#d62728"], height=260)

    # ── Line: avg sentiment across all tags ─────────────────────────────
    st.markdown(f"### {title_avg}")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=g["bucket"], y=g["avg_sent"], name="Avg sentiment",
        line={"color": "#1f77b4", "width": 2.5},
        fill="tozeroy", fillcolor="rgba(31,119,180,0.15)",
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="#888")
    fig.update_layout(
        yaxis={"title": "Sentiment [-1, +1]", "range": [-1, 1]},
        xaxis={"title": "Time (UTC)"},
        height=320, margin={"l": 40, "r": 40, "t": 30, "b": 30},
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Per-tag breakdown (line chart, one trace per symbol) ───────────
    st.markdown("### Per-tag breakdown")
    sym_df = _per_symbol_buckets_df(minutes, hours)
    if not sym_df.empty:
        # Drop symbols with too few tweets in this window to avoid noisy
        # single-tweet spikes dominating the chart.
        sym_counts = sym_df.groupby("symbol")["n"].sum()
        keep = sym_counts[sym_counts >= 5].index.tolist()
        sym_df = sym_df[sym_df["symbol"].isin(keep)]
        if not sym_df.empty:
            fig2 = px.line(
                sym_df, x="bucket", y="avg_sent", color="symbol",
                title="Avg sentiment per tag",
            )
            fig2.update_layout(
                yaxis={"range": [-1, 1]},
                height=420, margin={"l": 40, "r": 40, "t": 30, "b": 30},
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Not enough tweets per tag to draw per-tag lines yet.")
    else:
        st.info("No per-tag bucketed data yet.")

    # ── Daily top-10 trending topics ───────────────────────────────────
    st.markdown("### 🏆 Top-10 trending topics (today, daily aggregate)")
    st.caption(
        "Velocity = today's tweet count − yesterday's tweet count "
        "(positive = heating up, negative = cooling). "
        "Reach = Σ followers of authors who posted — a proxy for eyeballs, "
        "since X.com impressions aren't available without the API."
    )
    days = st.slider("Lookback (days)", 1, 30, 7, step=1, key="top_topics_days")
    top_n = st.slider("Top N per day", 5, 25, 10, step=1, key="top_topics_n")
    daily = _daily_topics(days=days, limit=top_n * days)
    if daily.empty:
        st.info("Not enough tweet history to compute daily aggregates yet.")
    else:
        # ── "Today's top-N" summary table ──────────────────────────────
        latest_day = daily["day"].max()
        today = daily[daily["day"] == latest_day].copy()
        today = today.sort_values("tweet_count", ascending=False).head(top_n)
        if not today.empty:
            t = today.copy()
            t["avg_sentiment"] = t["avg_sentiment"].fillna(0.0).round(3)
            t["velocity_str"] = t["velocity"].apply(
                lambda v: f"{v:+d} ▲" if v > 0 else (f"{v:d} ▼" if v < 0 else " 0 ─")
            )
            t["reach_str"] = t["total_reach"].apply(lambda r: f"{int(r):,}")
            st.dataframe(
                t[[
                    "symbol", "tweet_count", "velocity_str", "unique_authors",
                    "total_likes", "total_retweets", "reach_str",
                    "pos_count", "neg_count", "avg_sentiment",
                ]].rename(columns={
                    "symbol": "Topic", "tweet_count": "Tweets",
                    "velocity_str": "Velocity", "unique_authors": "Authors",
                    "total_likes": "Likes", "total_retweets": "Retweets",
                    "reach_str": "Reach (Σ followers)",
                    "pos_count": "Pos", "neg_count": "Neg",
                    "avg_sentiment": "Avg sent",
                })
                .style.format({
                    "Tweets": "{:,}",
                    "Likes": "{:,}",
                    "Retweets": "{:,}",
                    "Pos": "{:,}",
                    "Neg": "{:,}",
                    "Avg sent": "{:+.3f}",
                })
                .bar(subset=["Tweets"], color="#7f7f7f")
                .bar(subset=["Avg sent"], color="#d62728", align="mid"),
                use_container_width=True,
                height=320,
            )

        # ── Per-day stacked bar: which topics are gaining / losing ─────
        st.markdown("### Topic volume over time (stacked per day)")
        pv = daily.pivot_table(
            index="day", columns="symbol", values="tweet_count", aggfunc="sum",
        ).fillna(0).astype(int)
        if not pv.empty:
            top_syms = pv.sum().sort_values(ascending=False).head(top_n).index.tolist()
            pv = pv[top_syms]
            fig3 = go.Figure()
            for sym in top_syms:
                fig3.add_trace(go.Bar(
                    x=pv.index, y=pv[sym], name=sym,
                ))
            fig3.update_layout(
                barmode="stack", height=380,
                xaxis_title="Day (UTC)", yaxis_title="Tweet count",
                margin={"l": 40, "r": 40, "t": 30, "b": 30},
            )
            st.plotly_chart(fig3, use_container_width=True)

        # ── Reach leaderboard ──────────────────────────────────────────
        st.markdown("### 👀 Reach leaderboard (Σ follower-counts per topic)")
        reach = (
            daily.groupby("symbol", as_index=False)["total_reach"]
            .sum()
            .sort_values("total_reach", ascending=False)
            .head(top_n)
        )
        if not reach.empty:
            fig4 = px.bar(
                reach, x="total_reach", y="symbol", orientation="h",
                title="Cumulative reach across selected window",
                text="total_reach",
            )
            fig4.update_layout(
                yaxis={"autorange": "reversed"}, height=380,
                xaxis_title="Reach (Σ followers)",
                margin={"l": 100, "r": 40, "t": 30, "b": 30},
            )
            st.plotly_chart(fig4, use_container_width=True)

    # ── Detail table ───────────────────────────────────────────────────
    detail = g.copy()
    detail["pos%"] = (detail["pos_n"] / detail["n"] * 100).round(1)
    detail["neg%"] = (detail["neg_n"] / detail["n"] * 100).round(1)
    detail["avg_sent"] = detail["avg_sent"].round(3)
    detail["bucket"] = detail["bucket"].dt.strftime("%Y-%m-%d %H:%M UTC")
    st.dataframe(
        detail[["bucket", "n", "pos_n", "neg_n", "pos%", "neg%", "avg_sent"]]
        .rename(columns={
            "bucket": "Bucket", "n": "Tweets", "pos_n": "Pos",
            "neg_n": "Neg", "pos%": "Pos %", "neg%": "Neg %",
            "avg_sent": "Avg sent",
        })
        .iloc[::-1],  # newest first
        use_container_width=True,
        height=300,
    )


# ── Main ─────────────────────────────────────────────────────────────────

def main() -> None:
    _render_header()
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview", "Sentiment", "Paper PnL", "🔥 Trending", "📡 Live"
    ])
    with tab1:
        page_overview()
    with tab2:
        page_sentiment()
    with tab3:
        page_paper_pnl()
    with tab4:
        page_trending()
    with tab5:
        page_live()

    with st.sidebar:
        st.markdown("### Status")
        try:
            n_tweets = int(_query("SELECT COUNT(*) AS n FROM tweets").iloc[0]["n"])
            n_signals = int(_query("SELECT COUNT(*) AS n FROM signals").iloc[0]["n"])
            n_trades = int(_query("SELECT COUNT(*) AS n FROM paper_trades").iloc[0]["n"])
            st.write(f"Tweets: **{n_tweets:,}**")
            st.write(f"Signals: **{n_signals:,}**")
            st.write(f"Paper trades: **{n_trades:,}**")
        except Exception as e:
            st.error(f"DB unreachable: {e}")
        st.markdown("---")
        st.caption("v0.3 · Twitter sentiment + paper-trading simulator")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("dashboard crashed")
        st.error("Dashboard error — see terminal logs.")