"""Tests for the Streamlit dashboard's read-only query functions.

Author: Prem Vishnoi <pvishnoi@avilx.com>

These verify that every dashboard query function works on SQLite, not just
on Postgres. The production dashboard uses TimescaleDB, but local dev /
CI uses SQLite via `override_engine()`.

After the crypto-removal refactor the dashboard has 4 tabs (no Prices
tab) and 4 page functions (Overview, Sentiment, Paper PnL, Trending).
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from src.store import db


@pytest.fixture
def seeded_db(tmp_path):
    """Seed a SQLite DB with tweets + signals + positions + trades."""
    url = f"sqlite:///{tmp_path}/dash.db"
    db.override_engine(url)
    db.ensure_sqlite_schema()

    now = datetime.utcnow().replace(microsecond=0)
    # Tweets
    for i in range(5):
        db.upsert_tweet({
            "ts": now - timedelta(minutes=5 - i), "tweet_id": 100 + i,
            "symbol": "AI", "text": "bullish", "author": "a",
            "likes": 0, "retweets": 0, "followers": 0, "url": "u",
            "source_adapter": "nitter", "sentiment_score": 0.5 + i * 0.1,
        })
    # Signals (separated by 1ms to avoid (ts, symbol) PK collision)
    db.insert_signal({
        "ts": now, "symbol": "AI", "action": "BUY", "score": 1.5,
        "sentiment_zscore": 2.0, "momentum_zscore": 0.0, "reason": "demo",
    })
    db.insert_signal({
        "ts": now + timedelta(milliseconds=1), "symbol": "AI", "action": "HOLD",
        "score": 0.0, "sentiment_zscore": 0.0, "momentum_zscore": 0.0,
        "reason": "demo",
    })
    # Position
    db.upsert_position({
        "ts": now, "symbol": "AI", "qty": 0.01, "avg_price": 50.0,
        "realized_pnl": 0.0,
    })
    # Paper trade (uses new currency-agnostic column names)
    db.insert_paper_trade({
        "ts": now, "symbol": "AI", "side": "BUY", "qty": 0.01,
        "price": 50.0, "fee": 0.5, "cash_after": 9_499.5,
        "reason": "demo",
    })
    yield


def _import_dashboard():
    """Lazy import — Streamlit's st.set_page_config blows up outside a run."""
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from dashboard import app
    return app


# ── Per-query smoke tests on SQLite ──────────────────────────────────────


def test_kpis_runs_on_sqlite(seeded_db):
    """After the crypto-removal refactor, _kpis uses cash_after + avg_price
    only (no live price join). Verify it runs on SQLite and returns a
    dict with the expected keys."""
    app = _import_dashboard()
    kpis = app._kpis()
    assert isinstance(kpis, dict)
    assert kpis["cash"] == pytest.approx(9_499.5)
    assert kpis["trade_count"] == 1
    assert kpis["today_trades"] == 1
    # Position is 0.01 units @ avg_price=50.0 → 0.5 units market value
    assert kpis["position_value"] == pytest.approx(0.5)
    assert kpis["equity"] == pytest.approx(9_499.5 + 0.5)


def test_kpis_with_no_trades_falls_back_to_starting_units(tmp_path):
    """When paper_trades is empty, the dashboard falls back to
    settings.starting_units for cash. We bypass Streamlit's @st.cache_data
    by calling the underlying function on a fresh empty DB."""
    import streamlit as st
    app = _import_dashboard()
    # Clear the Streamlit cache so the @st.cache_data(_kpis) wrapper
    # doesn't return a previous test's result.
    st.cache_data.clear()
    db.override_engine(f"sqlite:///{tmp_path}/empty_kpis.db")
    db.ensure_sqlite_schema()
    kpis = app._kpis()
    assert kpis["cash"] == pytest.approx(app.settings.starting_units)
    assert kpis["trade_count"] == 0
    assert kpis["position_value"] == 0.0


def test_signal_counts_runs_on_sqlite(seeded_db):
    app = _import_dashboard()
    df = app._signal_counts()
    assert isinstance(df, pd.DataFrame)
    assert set(df["action"]) == {"BUY", "HOLD"}
    counts = dict(zip(df["action"], df["n"]))
    assert counts["BUY"] == 1
    assert counts["HOLD"] == 1


def test_sentiment_per_symbol_runs_on_sqlite(seeded_db):
    app = _import_dashboard()
    df = app._sentiment_per_symbol(60)
    assert isinstance(df, pd.DataFrame)
    assert "AI" in df["symbol"].values


def test_tweet_volume_5m_runs_on_sqlite(seeded_db):
    app = _import_dashboard()
    df = app._tweet_volume_5m()
    assert isinstance(df, pd.DataFrame)


def test_top_mentions_runs_on_sqlite(seeded_db):
    app = _import_dashboard()
    df = app._top_mentions(10)
    assert isinstance(df, pd.DataFrame)
    assert df.iloc[0]["symbol"] == "AI"
    assert df.iloc[0]["mentions"] == 5


def test_signals_query_runs_on_sqlite(seeded_db):
    app = _import_dashboard()
    df = app._signals("AI", hours=1)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2


def test_trade_log_runs_on_sqlite(seeded_db):
    app = _import_dashboard()
    df = app._trade_log(10)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["side"] == "BUY"
    # The new column names are `price` and `fee` (not `_usd`).
    assert "price" in df.columns
    assert "fee" in df.columns
    assert "price_usd" not in df.columns
    assert "fee_usd" not in df.columns


def test_trending_tags_runs_on_sqlite(seeded_db):
    app = _import_dashboard()
    df = app._trending_tags(minutes=5, limit=10)
    # Empty is fine — we just need the query to not crash on SQLite.
    assert isinstance(df, pd.DataFrame)


# ── End-to-end page-render regression tests ──────────────────────────────
# These would have caught the pyarrow + datetime-string bugs that broke
# the deployed dashboard. After the refactor there are 4 pages.


def test_dashboard_import_does_not_crash(seeded_db):
    """The dashboard imports pyarrow via streamlit's st.dataframe. With
    pyarrow pinned to <=18 for numpy 1.x compat, this must work."""
    app = _import_dashboard()
    assert hasattr(app, "page_overview")
    assert hasattr(app, "page_sentiment")
    assert hasattr(app, "page_paper_pnl")
    assert hasattr(app, "page_trending")
    # The Prices tab is gone
    assert not hasattr(app, "page_prices_signals")


def test_signals_returns_datetime_indexed_ts(seeded_db):
    app = _import_dashboard()
    df = app._signals("AI", hours=1)
    assert not df.empty
    assert pd.api.types.is_datetime64_any_dtype(df["ts"])


def test_trade_log_returns_datetime_indexed_ts(seeded_db):
    app = _import_dashboard()
    df = app._trade_log(10)
    assert not df.empty
    assert pd.api.types.is_datetime64_any_dtype(df["ts"])


def test_tweet_volume_5m_returns_datetime_indexed_bucket(seeded_db):
    app = _import_dashboard()
    df = app._tweet_volume_5m()
    # Empty seeded DB for tweets_5m is OK; just verify dtype if not empty
    if not df.empty:
        assert pd.api.types.is_datetime64_any_dtype(df["bucket"])


def test_page_overview_renders_end_to_end(seeded_db):
    """The pyarrow bug crashed this page in production. After the
    refactor it must render without traceback on SQLite."""
    app = _import_dashboard()
    app.page_overview()  # must not raise


def test_page_sentiment_renders_end_to_end(seeded_db):
    app = _import_dashboard()
    app.page_sentiment()


def test_page_paper_pnl_renders_end_to_end(seeded_db):
    """After the refactor, the paper-PnL page uses cash_after of
    paper_trades (no live mark-to-market). Must render on SQLite."""
    app = _import_dashboard()
    app.page_paper_pnl()


def test_page_trending_renders_end_to_end(seeded_db):
    """The Trending page calls db.fetch_trending_tags() — must work
    on SQLite (no TimescaleDB-only syntax)."""
    app = _import_dashboard()
    app.page_trending()
