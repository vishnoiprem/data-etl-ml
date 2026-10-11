"""Tests for the Streamlit dashboard's read-only query functions.

Author: Prem Vishnoi <pvishnoi@avilx.com>

These verify that every dashboard query function works on SQLite, not just
on Postgres. The production dashboard uses TimescaleDB, but local dev /
CI uses SQLite via `override_engine()`. The dashboard used to silently
break on SQLite because the `_kpis` function called a Postgres-only
`DISTINCT ON (symbol)` query.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import pytest

from src.store import db


@pytest.fixture
def seeded_db(tmp_path):
    """Seed a SQLite DB with tweets + prices + signals + positions + trades."""
    url = f"sqlite:///{tmp_path}/dash.db"
    db.override_engine(url)
    db.ensure_sqlite_schema()

    now = datetime.utcnow().replace(microsecond=0)
    # Prices for BTC + ETH (multi-symbol so DISTINCT ON matters)
    for i in range(10):
        db.upsert_price({
            "ts": now - timedelta(minutes=10 - i),
            "symbol": "BTC", "price_usd": 50_000.0 + i * 10, "volume_usd": 1.0,
        })
        db.upsert_price({
            "ts": now - timedelta(minutes=10 - i),
            "symbol": "ETH", "price_usd": 3_000.0 + i, "volume_usd": 1.0,
        })
    # Tweets
    for i in range(5):
        db.upsert_tweet({
            "ts": now - timedelta(minutes=5 - i), "tweet_id": 100 + i,
            "symbol": "BTC", "text": "bullish", "author": "a",
            "likes": 0, "retweets": 0, "followers": 0, "url": "u",
            "source_adapter": "nitter", "sentiment_score": 0.5 + i * 0.1,
        })
    # Signals (separated by 1ms to avoid (ts, symbol) PK collision)
    db.insert_signal({
        "ts": now, "symbol": "BTC", "action": "BUY", "score": 1.5,
        "sentiment_zscore": 2.0, "momentum_zscore": 1.0, "reason": "demo",
    })
    db.insert_signal({
        "ts": now + timedelta(milliseconds=1), "symbol": "BTC", "action": "HOLD",
        "score": 0.0, "sentiment_zscore": 0.0, "momentum_zscore": 0.0,
        "reason": "demo",
    })
    # Position
    db.upsert_position({
        "ts": now, "symbol": "BTC", "qty": 0.01, "avg_price": 50_000.0,
        "realized_pnl": 0.0,
    })
    # Paper trade
    db.insert_paper_trade({
        "ts": now, "symbol": "BTC", "side": "BUY", "qty": 0.01,
        "price_usd": 50_000.0, "fee_usd": 0.5, "cash_after": 9_499.5,
        "reason": "demo",
    })
    yield


def _import_dashboard():
    """Lazy import — Streamlit's st.set_page_config blows up outside a run."""
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from dashboard import app
    return app


def test_kpis_runs_on_sqlite(seeded_db):
    """Regression: _kpis used `DISTINCT ON` (Postgres-only) and crashed
    on SQLite with a syntax error. This test would have failed loudly
    when the dashboard ran locally without TimescaleDB."""
    app = _import_dashboard()
    kpis = app._kpis()
    assert isinstance(kpis, dict)
    assert kpis["cash"] == pytest.approx(9_499.5)
    assert kpis["trade_count"] == 1
    assert kpis["today_trades"] == 1
    # Position is 0.01 BTC, latest BTC price = 50_090
    assert kpis["position_value"] == pytest.approx(0.01 * 50_090.0)
    assert kpis["equity"] == pytest.approx(9_499.5 + 0.01 * 50_090.0)


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
    assert "BTC" in df["symbol"].values


def test_tweet_volume_5m_runs_on_sqlite(seeded_db):
    app = _import_dashboard()
    df = app._tweet_volume_5m()
    assert isinstance(df, pd.DataFrame)


def test_top_mentions_runs_on_sqlite(seeded_db):
    app = _import_dashboard()
    df = app._top_mentions(10)
    assert isinstance(df, pd.DataFrame)
    assert df.iloc[0]["symbol"] == "BTC"
    assert df.iloc[0]["mentions"] == 5


def test_price_series_runs_on_sqlite(seeded_db):
    app = _import_dashboard()
    df = app._price_series("BTC", hours=1)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 10
    # ASC order, so the last row is the most recent price
    assert df["close"].iloc[-1] == pytest.approx(50_090.0)


def test_signals_query_runs_on_sqlite(seeded_db):
    app = _import_dashboard()
    df = app._signals("BTC", hours=1)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2


def test_trade_log_runs_on_sqlite(seeded_db):
    app = _import_dashboard()
    df = app._trade_log(10)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["side"] == "BUY"


def test_equity_curve_runs_on_sqlite(seeded_db):
    app = _import_dashboard()
    df = app._equity_curve(24)
    assert isinstance(df, pd.DataFrame)
    # The replayed equity curve should have a row for each price bucket
    assert "ts" in df.columns
    assert "equity" in df.columns
    # Starting cash is 10k; after the BUY at $50k, cash drops to 9.5k
    # but the position is 0.01 BTC so equity ≈ 9.5k + 0.01 * price
    assert df["equity"].iloc[0] == pytest.approx(10_000.0)


def test_open_positions_query_latest_price_per_symbol(seeded_db):
    """The page_overview() open-positions block runs another DISTINCT ON
    query. Verify it works on SQLite AND returns the *latest* price per
    symbol (not the first-inserted)."""
    from datetime import datetime, timedelta
    app = _import_dashboard()
    # Add an older ETH price to verify "latest" wins
    older = datetime.utcnow() - timedelta(minutes=20)
    db.upsert_price({"ts": older, "symbol": "ETH", "price_usd": 2_500.0, "volume_usd": 1.0})
    # Direct mirror of the page_overview block:
    if db.get_engine().dialect.name == "postgresql":
        latest = app._query(
            "SELECT DISTINCT ON (symbol) symbol, price_usd FROM prices "
            "ORDER BY symbol, ts DESC"
        )
    else:
        latest = app._query(
            "SELECT symbol, price_usd FROM prices p1 "
            "WHERE ts = (SELECT MAX(ts) FROM prices p2 WHERE p2.symbol = p1.symbol)"
        )
    eth_price = latest[latest["symbol"] == "ETH"]["price_usd"].iloc[0]
    # Must be the recent one (3000+), not the old one (2500)
    assert eth_price > 2_900.0, f"expected latest ETH price ~3009, got {eth_price}"


# ── End-to-end page-render regression tests ────────────────────────────────
# These would have caught the pyarrow + datetime-string bugs that broke
# the deployed dashboard.

def test_dashboard_import_does_not_crash(seeded_db):
    """The dashboard imports pyarrow via streamlit's st.dataframe. With
    pyarrow pinned to <=18 for numpy 1.x compat, this must work."""
    app = _import_dashboard()
    assert hasattr(app, "page_overview")
    assert hasattr(app, "page_sentiment")
    assert hasattr(app, "page_prices_signals")
    assert hasattr(app, "page_paper_pnl")


def test_price_series_returns_datetime_indexed_bucket(seeded_db):
    """Regression: reindex(method='nearest') requires a real datetime
    dtype, not strings. SQLAlchemy returns SQLite datetime columns as
    `object`; the dashboard must coerce them."""
    app = _import_dashboard()
    df = app._price_series("BTC", hours=1)
    assert not df.empty
    assert pd.api.types.is_datetime64_any_dtype(df["bucket"]), (
        f"expected datetime dtype, got {df['bucket'].dtype}"
    )


def test_signals_returns_datetime_indexed_ts(seeded_db):
    app = _import_dashboard()
    df = app._signals("BTC", hours=1)
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
    """The pyarrow + DISTINCT ON bug crashed this page in production.
    Now all 4 pages must render without traceback."""
    app = _import_dashboard()
    app.page_overview()  # must not raise


def test_page_sentiment_renders_end_to_end(seeded_db):
    app = _import_dashboard()
    app.page_sentiment()


def test_page_prices_signals_renders_end_to_end(seeded_db):
    """This page was the second casualty — the reindex(method='nearest')
    on string bucket crashed with TypeError on every render."""
    app = _import_dashboard()
    app.page_prices_signals()


def test_page_paper_pnl_renders_end_to_end(seeded_db):
    app = _import_dashboard()
    app.page_paper_pnl()
