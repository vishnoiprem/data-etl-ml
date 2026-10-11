"""Tests for the SQLite path of src.store.db.

The Postgres path is exercised by the integration test; this file
covers the SQLite-specific code paths, particularly the SQL branches
that diverge from Postgres (no `ON CONFLICT`, no time_bucket, etc.)
and the queries that the production signal generator depends on.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta

import pytest

from src.store import db


@pytest.fixture
def sqlite_db(tmp_path):
    """Fresh in-memory-like SQLite (file-backed so transactions are visible)."""
    url = f"sqlite:///{tmp_path}/test.db"
    db.override_engine(url)
    db.ensure_sqlite_schema()
    yield
    # Engine is shared globally; reset for the next test
    db.override_engine(url)


# ── upsert_tweet: idempotency, dedup by (tweet_id, ts) ─────────────────


def test_upsert_tweet_inserts_new_row(sqlite_db):
    inserted = db.upsert_tweet({
        "ts": datetime(2026, 1, 1, 12, 0, 0),
        "tweet_id": 1, "symbol": "BTC", "text": "hello",
        "author": "alice", "likes": 0, "retweets": 0, "followers": 0,
        "url": "https://x/1", "source_adapter": "nitter",
    })
    assert inserted is True
    rows = db.fetch_unscored_tweets(limit=10)
    assert len(rows) == 1
    assert rows[0]["text"] == "hello"


def test_upsert_tweet_dedup_on_same_id_and_ts(sqlite_db):
    base = {
        "ts": datetime(2026, 1, 1, 12, 0, 0),
        "tweet_id": 42, "symbol": "BTC", "text": "x",
        "author": "alice", "likes": 0, "retweets": 0, "followers": 0,
        "url": "u", "source_adapter": "nitter",
    }
    first = db.upsert_tweet(base)
    second = db.upsert_tweet(base)
    third = db.upsert_tweet(base)
    assert first is True
    assert second is False
    assert third is False
    # Still exactly 1 row
    rows = db.fetch_unscored_tweets(limit=10)
    assert len(rows) == 1


def test_upsert_tweet_distinct_ts_creates_new_row(sqlite_db):
    """Same tweet_id but a different ts → treated as a separate row
    (a re-scrape that arrived with a corrected timestamp)."""
    base = {
        "tweet_id": 42, "symbol": "BTC", "text": "x",
        "author": "alice", "likes": 0, "retweets": 0, "followers": 0,
        "url": "u", "source_adapter": "nitter",
    }
    a = dict(base, ts=datetime(2026, 1, 1, 12, 0, 0))
    b = dict(base, ts=datetime(2026, 1, 1, 12, 0, 5))  # 5s later
    assert db.upsert_tweet(a) is True
    assert db.upsert_tweet(b) is True
    assert len(db.fetch_unscored_tweets(limit=10)) == 2


def test_upsert_tweet_serializes_dict_to_json(sqlite_db):
    """raw_json dict is JSON-stringified for SQLite (Text column)."""
    db.upsert_tweet({
        "ts": datetime(2026, 1, 1, 12, 0, 0),
        "tweet_id": 1, "symbol": "BTC", "text": "x",
        "author": "alice", "likes": 0, "retweets": 0, "followers": 0,
        "url": "u", "source_adapter": "nitter",
        "raw_json": {"nested": {"k": [1, 2, 3]}},
    })
    # No assertion error means JSON-encoding worked
    assert len(db.fetch_unscored_tweets(limit=10)) == 1


# ── update_tweet_sentiment: actually mutates the row ───────────────────


def test_update_tweet_sentiment_changes_unscored_to_scored(sqlite_db):
    ts = datetime(2026, 1, 1, 12, 0, 0)
    db.upsert_tweet({
        "ts": ts, "tweet_id": 1, "symbol": "BTC", "text": "x",
        "author": "alice", "likes": 0, "retweets": 0, "followers": 0,
        "url": "u", "source_adapter": "nitter",
    })
    # Before update: tweet appears in unscored fetch
    assert len(db.fetch_unscored_tweets(limit=10)) == 1
    # Update with matching (tweet_id, ts)
    n = db.update_tweet_sentiment(1, ts, 0.5)
    assert n == 1
    # After update: tweet is no longer in unscored list
    assert db.fetch_unscored_tweets(limit=10) == []


def test_update_tweet_sentiment_no_match_returns_zero(sqlite_db):
    """Updating a (tweet_id, ts) that doesn't exist returns 0 affected."""
    n = db.update_tweet_sentiment(999, datetime(2030, 1, 1), 0.5)
    assert n == 0


def test_update_tweet_sentiment_wrong_ts_does_not_update(sqlite_db):
    """The (tweet_id, ts) pair must match exactly — wrong ts → 0 affected."""
    ts = datetime(2026, 1, 1, 12, 0, 0)
    db.upsert_tweet({
        "ts": ts, "tweet_id": 1, "symbol": "BTC", "text": "x",
        "author": "alice", "likes": 0, "retweets": 0, "followers": 0,
        "url": "u", "source_adapter": "nitter",
    })
    # Same tweet_id, but a *different* ts
    n = db.update_tweet_sentiment(1, ts + timedelta(seconds=1), 0.5)
    assert n == 0
    # Still unscored
    assert len(db.fetch_unscored_tweets(limit=10)) == 1


# ── fetch_unscored_tweets: ordering + limit ───────────────────────────


def test_fetch_unscored_orders_by_ts_asc(sqlite_db):
    """Oldest first — the production pipeline scores in chronological
    order so a slow FinBERT batch processes the oldest tweets first."""
    now = datetime(2026, 1, 1, 12, 0, 0)
    for offset in (5, 0, 3, 1, 4, 2):  # out-of-order inserts
        db.upsert_tweet({
            "ts": now + timedelta(minutes=offset), "tweet_id": offset + 1,
            "symbol": "BTC", "text": f"t{offset}", "author": "a",
            "likes": 0, "retweets": 0, "followers": 0, "url": "u",
            "source_adapter": "nitter",
        })
    rows = db.fetch_unscored_tweets(limit=10)
    assert [r["tweet_id"] for r in rows] == [1, 2, 3, 4, 5, 6]


def test_fetch_unscored_respects_limit(sqlite_db):
    now = datetime(2026, 1, 1, 12, 0, 0)
    for i in range(20):
        db.upsert_tweet({
            "ts": now + timedelta(seconds=i), "tweet_id": i,
            "symbol": "BTC", "text": "x", "author": "a",
            "likes": 0, "retweets": 0, "followers": 0, "url": "u",
            "source_adapter": "nitter",
        })
    assert len(db.fetch_unscored_tweets(limit=5)) == 5
    assert len(db.fetch_unscored_tweets(limit=100)) == 20


# ── upsert_price: insert AND update paths ─────────────────────────────


def test_upsert_price_inserts_new_row(sqlite_db):
    db.upsert_price({
        "ts": datetime(2026, 1, 1, 12, 0, 0),
        "symbol": "BTC", "price_usd": 50_000.0, "volume_usd": 123.4,
    })
    p = db.latest_price("BTC")
    assert p is not None
    assert p["price_usd"] == 50_000.0
    assert p["volume_usd"] == 123.4


def test_upsert_price_overwrites_on_same_ts_and_symbol(sqlite_db):
    """Same (ts, symbol) → price/volume are updated in place (not duplicated)."""
    ts = datetime(2026, 1, 1, 12, 0, 0)
    db.upsert_price({"ts": ts, "symbol": "BTC", "price_usd": 50_000.0, "volume_usd": 100.0})
    db.upsert_price({"ts": ts, "symbol": "BTC", "price_usd": 51_000.0, "volume_usd": 200.0})
    p = db.latest_price("BTC")
    assert p["price_usd"] == 51_000.0
    assert p["volume_usd"] == 200.0


def test_upsert_price_does_not_confuse_symbols(sqlite_db):
    """Same ts, different symbol → two distinct rows."""
    ts = datetime(2026, 1, 1, 12, 0, 0)
    db.upsert_price({"ts": ts, "symbol": "BTC", "price_usd": 50_000.0, "volume_usd": 1.0})
    db.upsert_price({"ts": ts, "symbol": "ETH", "price_usd": 3_000.0, "volume_usd": 2.0})
    assert db.latest_price("BTC")["price_usd"] == 50_000.0
    assert db.latest_price("ETH")["price_usd"] == 3_000.0


def test_latest_price_returns_none_when_no_data(sqlite_db):
    assert db.latest_price("NOPE") is None


def test_latest_price_picks_most_recent_ts(sqlite_db):
    """When there are multiple price rows for the same symbol, the
    most recent ts is returned (not the first-inserted)."""
    db.upsert_price({"ts": datetime(2026, 1, 1, 10, 0, 0), "symbol": "BTC", "price_usd": 49_000.0, "volume_usd": 1.0})
    db.upsert_price({"ts": datetime(2026, 1, 1, 12, 0, 0), "symbol": "BTC", "price_usd": 50_000.0, "volume_usd": 1.0})
    db.upsert_price({"ts": datetime(2026, 1, 1, 11, 0, 0), "symbol": "BTC", "price_usd": 49_500.0, "volume_usd": 1.0})
    assert db.latest_price("BTC")["price_usd"] == 50_000.0


# ── sentiment_buckets: the production signal depends on this ─────────


def test_sentiment_buckets_aggregates_by_5min(sqlite_db):
    """Tweets in the same 5-min window are averaged together; different
    windows are separate buckets. This is the core of the z-score math.

    We anchor the test data relative to `datetime.utcnow()` so the
    `ts > datetime('now', -1h)` filter always includes them, regardless
    of the host machine's timezone. Two clearly distinct 5-min windows
    are used so the 5-min bucket boundary is observable.
    """
    # 30 min ago is well inside the 1h lookback. Floor to a 5-min boundary
    # so Group A's tweets (10s, 20s, 30s offsets) are guaranteed to land
    # in the same bucket — otherwise an unlucky `base` straddles the
    # boundary and the test becomes order-dependent on the wall clock.
    now = datetime.utcnow().replace(microsecond=0, second=0)
    base = now - timedelta(minutes=30)
    base = base - timedelta(minutes=base.minute % 5)
    # Group A: 3 tweets in the 5-min window starting at `base`.
    # 0.4, 0.6, 0.5 → mean 0.5.
    for i, score in enumerate([0.4, 0.6, 0.5]):
        db.upsert_tweet({
            "ts": base + timedelta(seconds=10 + i * 10), "tweet_id": i,
            "symbol": "BTC", "text": "x", "author": "a",
            "likes": 0, "retweets": 0, "followers": 0, "url": "u",
            "source_adapter": "nitter", "sentiment_score": score,
        })
    # Group B: 2 tweets in a *different* 5-min window 10 min later.
    # -0.5, -0.7 → mean -0.6.
    base_b = base + timedelta(minutes=10)
    for i, score in enumerate([-0.5, -0.7]):
        db.upsert_tweet({
            "ts": base_b + timedelta(seconds=i * 10), "tweet_id": 10 + i,
            "symbol": "BTC", "text": "x", "author": "a",
            "likes": 0, "retweets": 0, "followers": 0, "url": "u",
            "source_adapter": "nitter", "sentiment_score": score,
        })
    buckets = db.sentiment_buckets("BTC", minutes=5, hours=1)
    assert len(buckets) == 2, f"expected 2 buckets, got {len(buckets)}: {buckets}"
    # ASC order: first bucket is the earlier one
    assert math.isclose(buckets[0]["avg_sent"], 0.5, abs_tol=1e-6)
    assert buckets[0]["n"] == 3
    assert math.isclose(buckets[1]["avg_sent"], -0.6, abs_tol=1e-6)
    assert buckets[1]["n"] == 2


def test_sentiment_buckets_excludes_null_sentiment(sqlite_db):
    """Tweets with sentiment_score IS NULL are not aggregated into buckets
    (they're still unscored, so we shouldn't pollute the distribution)."""
    now = datetime.utcnow().replace(microsecond=0)
    db.upsert_tweet({
        "ts": now - timedelta(minutes=5), "tweet_id": 1, "symbol": "BTC", "text": "x", "author": "a",
        "likes": 0, "retweets": 0, "followers": 0, "url": "u",
        "source_adapter": "nitter", "sentiment_score": None,
    })
    db.upsert_tweet({
        "ts": now - timedelta(minutes=4), "tweet_id": 2, "symbol": "BTC", "text": "x", "author": "a",
        "likes": 0, "retweets": 0, "followers": 0, "url": "u",
        "source_adapter": "nitter", "sentiment_score": 0.8,
    })
    buckets = db.sentiment_buckets("BTC", minutes=5, hours=1)
    assert len(buckets) == 1
    assert buckets[0]["n"] == 1  # only the scored one counts
    assert math.isclose(buckets[0]["avg_sent"], 0.8, abs_tol=1e-6)


def test_sentiment_buckets_filters_by_symbol(sqlite_db):
    """BTC and ETH buckets are independent."""
    now = datetime.utcnow().replace(microsecond=0)
    db.upsert_tweet({
        "ts": now - timedelta(minutes=5), "tweet_id": 1, "symbol": "BTC", "text": "x", "author": "a",
        "likes": 0, "retweets": 0, "followers": 0, "url": "u",
        "source_adapter": "nitter", "sentiment_score": 0.9,
    })
    db.upsert_tweet({
        "ts": now - timedelta(minutes=5), "tweet_id": 2, "symbol": "ETH", "text": "x", "author": "a",
        "likes": 0, "retweets": 0, "followers": 0, "url": "u",
        "source_adapter": "nitter", "sentiment_score": -0.9,
    })
    btc = db.sentiment_buckets("BTC", minutes=5, hours=1)
    eth = db.sentiment_buckets("ETH", minutes=5, hours=1)
    assert math.isclose(btc[0]["avg_sent"], 0.9, abs_tol=1e-6)
    assert math.isclose(eth[0]["avg_sent"], -0.9, abs_tol=1e-6)


# ── recent_price_returns: per-minute returns ──────────────────────────


def test_recent_price_returns_computes_per_minute_diffs(sqlite_db):
    """(p1-p0)/p0, (p2-p1)/p1, ... — len = N-1 for N prices."""
    now = datetime.utcnow().replace(microsecond=0)
    prices = [100.0, 110.0, 99.0, 100.0]
    for i, p in enumerate(prices):
        db.upsert_price({"ts": now - timedelta(minutes=10 - i),
                         "symbol": "BTC", "price_usd": p, "volume_usd": 1.0})
    rets = db.recent_price_returns("BTC", minutes=15)
    assert rets == pytest.approx([0.10, -0.10, 1/99.0], rel=1e-6)


def test_recent_price_returns_empty_for_one_point(sqlite_db):
    """Need at least 2 points to compute a return."""
    db.upsert_price({"ts": datetime.utcnow(),
                     "symbol": "BTC", "price_usd": 100.0, "volume_usd": 1.0})
    assert db.recent_price_returns("BTC", minutes=10) == []


def test_recent_price_returns_handles_zero_prices_without_division_error(sqlite_db):
    """The implementation guards against division by zero. A price going
    to 0 would produce an inf/nan return; ensure the test still runs."""
    now = datetime.utcnow().replace(microsecond=0)
    db.upsert_price({"ts": now, "symbol": "BTC", "price_usd": 100.0, "volume_usd": 1.0})
    db.upsert_price({"ts": now + timedelta(minutes=1), "symbol": "BTC", "price_usd": 0.0, "volume_usd": 1.0})
    rets = db.recent_price_returns("BTC", minutes=10)
    assert len(rets) == 1
    assert rets[0] in (float("inf"), float("-inf")) or math.isfinite(rets[0])


# ── fetch_recent_signals: SQLite hour offset ──────────────────────────


def test_fetch_recent_signals_filters_by_symbol(sqlite_db):
    """BTC signals must not leak into ETH's fetch."""
    now = datetime.utcnow()
    db.insert_signal({
        "ts": now, "symbol": "BTC", "action": "BUY", "score": 1.0,
        "sentiment_zscore": 0.5, "momentum_zscore": 0.5, "reason": "r",
    })
    db.insert_signal({
        "ts": now, "symbol": "ETH", "action": "SELL", "score": -1.0,
        "sentiment_zscore": -0.5, "momentum_zscore": -0.5, "reason": "r",
    })
    btc = db.fetch_recent_signals("BTC", hours=1)
    assert all(s["symbol"] == "BTC" for s in btc)
    assert len(btc) == 1
    assert btc[0]["action"] == "BUY"


def test_fetch_recent_signals_orders_desc(sqlite_db):
    """Most recent first — the dashboard's _signals() expects DESC."""
    now = datetime.utcnow()
    for i in range(5):
        db.insert_signal({
            "ts": now - timedelta(minutes=i), "symbol": "BTC", "action": "HOLD",
            "score": 0.0, "sentiment_zscore": 0.0, "momentum_zscore": 0.0,
            "reason": f"r{i}",
        })
    rows = db.fetch_recent_signals("BTC", hours=1)
    # The most recently inserted (smallest i) has the largest ts
    assert rows[0]["reason"] == "r0"
    assert rows[-1]["reason"] == "r4"


# ── fetch_paper_trades: ordering + content ────────────────────────────


def test_fetch_paper_trades_orders_desc(sqlite_db):
    now = datetime.utcnow()
    for i in range(3):
        db.insert_paper_trade({
            "ts": now - timedelta(minutes=i), "symbol": "BTC", "side": "BUY",
            "qty": 0.1, "price_usd": 50_000.0, "fee_usd": 5.0, "cash_after": 5_000.0,
            "reason": f"r{i}",
        })
    rows = db.fetch_paper_trades(limit=10)
    assert rows[0]["reason"] == "r0"
    assert rows[-1]["reason"] == "r2"


# ── all_open_positions: only qty>0, latest snapshot ───────────────────


def test_all_open_positions_returns_only_open(sqlite_db):
    now = datetime.utcnow()
    # Open position for BTC
    db.upsert_position({"ts": now, "symbol": "BTC", "qty": 0.1, "avg_price": 50_000.0})
    # Closed position (qty=0) for ETH
    db.upsert_position({"ts": now, "symbol": "ETH", "qty": 0.0, "avg_price": 0.0})
    open_pos = db.all_open_positions()
    assert len(open_pos) == 1
    assert open_pos[0]["symbol"] == "BTC"
    assert open_pos[0]["qty"] == 0.1


def test_all_open_positions_returns_latest_snapshot_per_symbol(sqlite_db):
    """If a symbol has multiple snapshots, only the most recent is returned."""
    now = datetime.utcnow()
    db.upsert_position({"ts": now - timedelta(minutes=5), "symbol": "BTC",
                        "qty": 0.1, "avg_price": 50_000.0})
    db.upsert_position({"ts": now, "symbol": "BTC",
                        "qty": 0.3, "avg_price": 55_000.0})
    open_pos = db.all_open_positions()
    assert len(open_pos) == 1
    assert open_pos[0]["qty"] == 0.3  # the more recent snapshot


# ── bulk helpers ──────────────────────────────────────────────────────


def test_bulk_upsert_tweets_returns_new_count(sqlite_db):
    base = datetime(2026, 1, 1, 12, 0, 0)
    rows = [
        {"ts": base + timedelta(seconds=i), "tweet_id": i, "symbol": "BTC",
         "text": f"t{i}", "author": "a", "likes": 0, "retweets": 0, "followers": 0,
         "url": "u", "source_adapter": "nitter"}
        for i in range(5)
    ]
    n = db.bulk_upsert_tweets(rows)
    assert n == 5
    # Re-bulk same rows → all duplicates
    n2 = db.bulk_upsert_tweets(rows)
    assert n2 == 0


def test_bulk_upsert_prices_returns_call_count(sqlite_db):
    rows = [
        {"ts": datetime(2026, 1, 1, 12, 0, i), "symbol": "BTC",
         "price_usd": 100.0 + i, "volume_usd": 1.0}
        for i in range(3)
    ]
    assert db.bulk_upsert_prices(rows) == 3
