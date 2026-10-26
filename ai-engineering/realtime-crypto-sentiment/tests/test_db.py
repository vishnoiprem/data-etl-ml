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
            "ts": now - timedelta(minutes=i), "symbol": "AI", "side": "BUY",
            "qty": 0.1, "price": 50.0, "fee": 5.0, "cash_after": 5_000.0,
            "reason": f"r{i}",
        })
    rows = db.fetch_paper_trades(limit=10)
    assert rows[0]["reason"] == "r0"
    assert rows[-1]["reason"] == "r2"


def test_fetch_paper_trades_uses_currency_agnostic_columns(sqlite_db):
    """After the crypto-removal refactor, paper_trades columns are `price`
    and `fee` (not `price_usd`/`fee_usd`). Verify both the insert and
    read paths use the new names."""
    now = datetime.utcnow()
    db.insert_paper_trade({
        "ts": now, "symbol": "AI", "side": "BUY", "qty": 1.0,
        "price": 100.0, "fee": 0.1, "cash_after": 9_900.0, "reason": "r0",
    })
    rows = db.fetch_paper_trades(limit=10)
    assert len(rows) == 1
    assert "price" in rows[0]
    assert "fee" in rows[0]
    assert "price_usd" not in rows[0]
    assert "fee_usd" not in rows[0]
    assert rows[0]["price"] == pytest.approx(100.0)
    assert rows[0]["fee"] == pytest.approx(0.1)


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


# ── global_sentiment_buckets: cross-tag aggregate (Live tab hourly chart) ──


def test_global_sentiment_buckets_aggregates_across_symbols(sqlite_db):
    """Different symbols in the same window roll up to one bucket with
    counts summed and sentiment averaged across ALL tags."""
    now = datetime.utcnow().replace(microsecond=0, second=0)
    base = now - timedelta(minutes=30)
    base = base - timedelta(minutes=base.minute % 5)
    # 2 tags, 2 scores each, same window → 1 bucket, n=4, avg=0.5
    for sym, scores in [("AI", [0.4, 0.6]), ("TSLA", [0.5, 0.5])]:
        for i, s in enumerate(scores):
            db.upsert_tweet({
                "ts": base + timedelta(seconds=10 * (i + 1)),
                "tweet_id": hash((sym, i)) & 0x7FFFFFFF, "symbol": sym,
                "text": "x", "author": "a", "likes": 0, "retweets": 0,
                "followers": 0, "url": "u", "source_adapter": "nitter",
                "sentiment_score": s,
            })
    rows = db.global_sentiment_buckets(minutes=5, hours=1)
    assert len(rows) == 1
    assert rows[0]["n"] == 4
    assert math.isclose(rows[0]["avg_sent"], 0.5, abs_tol=1e-6)
    assert rows[0]["pos_n"] == 4
    assert rows[0]["neg_n"] == 0


def test_global_sentiment_buckets_splits_pos_neg(sqlite_db):
    now = datetime.utcnow().replace(microsecond=0)
    base = now - timedelta(minutes=10)
    for tid, score in [(1, 0.8), (2, -0.6), (3, 0.0), (4, -0.1), (5, 0.9)]:
        db.upsert_tweet({
            "ts": base + timedelta(seconds=tid), "tweet_id": tid,
            "symbol": "AI", "text": "x", "author": "a",
            "likes": 0, "retweets": 0, "followers": 0, "url": "u",
            "source_adapter": "nitter", "sentiment_score": score,
        })
    rows = db.global_sentiment_buckets(minutes=5, hours=1)
    assert len(rows) == 1
    r = rows[0]
    assert r["n"] == 5
    # pos_n counts score > 0 (so 0.0 is neutral, not positive)
    assert r["pos_n"] == 2  # 0.8, 0.9
    assert r["neg_n"] == 2  # -0.6, -0.1
    # avg = (0.8 - 0.6 + 0.0 - 0.1 + 0.9) / 5
    assert math.isclose(r["avg_sent"], 0.2, abs_tol=1e-6)


def test_global_sentiment_buckets_excludes_null(sqlite_db):
    """Unscored tweets (sentiment_score IS NULL) must not contribute."""
    now = datetime.utcnow().replace(microsecond=0)
    base = now - timedelta(minutes=5)
    db.upsert_tweet({
        "ts": base, "tweet_id": 1, "symbol": "AI", "text": "x",
        "author": "a", "likes": 0, "retweets": 0, "followers": 0,
        "url": "u", "source_adapter": "nitter", "sentiment_score": None,
    })
    db.upsert_tweet({
        "ts": base + timedelta(seconds=1), "tweet_id": 2, "symbol": "AI",
        "text": "x", "author": "a", "likes": 0, "retweets": 0, "followers": 0,
        "url": "u", "source_adapter": "nitter", "sentiment_score": 0.7,
    })
    rows = db.global_sentiment_buckets(minutes=5, hours=1)
    assert len(rows) == 1
    assert rows[0]["n"] == 1


# ── per_symbol_buckets: per-tag breakdown for the Live tab ─────────────


def test_per_symbol_buckets_breaks_out_by_symbol(sqlite_db):
    """The same time window contains 2 symbols — each gets its own row."""
    now = datetime.utcnow().replace(microsecond=0, second=0)
    base = now - timedelta(minutes=30)
    base = base - timedelta(minutes=base.minute % 5)
    for sym, score in [("AI", 0.5), ("TSLA", -0.5), ("AI", 0.7), ("TSLA", -0.3)]:
        tid = abs(hash((sym, score, base.timestamp()))) & 0x7FFFFFFF
        db.upsert_tweet({
            "ts": base + timedelta(seconds=tid % 60), "tweet_id": tid,
            "symbol": sym, "text": "x", "author": "a",
            "likes": 0, "retweets": 0, "followers": 0, "url": "u",
            "source_adapter": "nitter", "sentiment_score": score,
        })
    rows = db.per_symbol_buckets(minutes=5, hours=1)
    # 1 bucket × 2 symbols = 2 rows
    assert len(rows) == 2
    syms = {r["symbol"] for r in rows}
    assert syms == {"AI", "TSLA"}


# ── daily_topic_aggregates: velocity + reach for the top-10 leaderboard ──


def test_daily_topic_aggregates_groups_by_day_and_symbol(sqlite_db):
    """Two symbols, two days → 4 rows. Velocity = today - yesterday
    (tweet_count delta) for the same symbol."""
    now = datetime.utcnow()
    # Day 0 (today) — 5 tweets for AI, 2 for TSLA
    for tid, sym in [
        (1, "AI"), (2, "AI"), (3, "AI"), (4, "AI"), (5, "AI"),
        (6, "TSLA"), (7, "TSLA"),
    ]:
        db.upsert_tweet({
            "ts": now - timedelta(minutes=tid), "tweet_id": tid,
            "symbol": sym, "text": "x", "author": f"u{tid}",
            "likes": tid * 10, "retweets": tid, "followers": tid * 100,
            "url": "u", "source_adapter": "nitter",
            "sentiment_score": 0.3,
        })
    # Day -1 (yesterday) — 1 tweet for AI, 4 for TSLA
    for tid, sym in [
        (100, "AI"),
        (101, "TSLA"), (102, "TSLA"), (103, "TSLA"), (104, "TSLA"),
    ]:
        db.upsert_tweet({
            "ts": now - timedelta(days=1, minutes=tid),
            "tweet_id": tid, "symbol": sym, "text": "x",
            "author": f"u{tid}", "likes": 0, "retweets": 0,
            "followers": 0, "url": "u", "source_adapter": "nitter",
            "sentiment_score": -0.3,
        })
    rows = db.daily_topic_aggregates(days=3, limit=20)
    by_key = {(r["day"], r["symbol"]): r for r in rows}
    # Velocity for AI: today(5) - yesterday(1) = +4
    ai_today = max(d for d, s in by_key if s == "AI")
    assert by_key[(ai_today, "AI")]["velocity"] == 4
    assert by_key[(ai_today, "AI")]["tweet_count"] == 5
    # Velocity for TSLA: today(2) - yesterday(4) = -2
    assert by_key[(ai_today, "TSLA")]["velocity"] == -2


def test_daily_topic_aggregates_reach_is_sum_of_followers(sqlite_db):
    """`total_reach` is SUM(followers) — proxy for impressions."""
    now = datetime.utcnow()
    db.upsert_tweet({
        "ts": now, "tweet_id": 1, "symbol": "AI", "text": "x", "author": "u1",
        "likes": 0, "retweets": 0, "followers": 1500, "url": "u",
        "source_adapter": "nitter", "sentiment_score": 0.1,
    })
    db.upsert_tweet({
        "ts": now, "tweet_id": 2, "symbol": "AI", "text": "x", "author": "u2",
        "likes": 0, "retweets": 0, "followers": 2500, "url": "u",
        "source_adapter": "nitter", "sentiment_score": 0.2,
    })
    rows = db.daily_topic_aggregates(days=1, limit=10)
    assert len(rows) == 1
    assert rows[0]["total_reach"] == 4000
    assert rows[0]["unique_authors"] == 2


def test_daily_topic_aggregates_first_day_has_velocity_eq_today(sqlite_db):
    """If a symbol has no row for yesterday, velocity = today's count
    (not 0; a brand-new topic is "all new", which is the max-velocity
    case for the leaderboard)."""
    now = datetime.utcnow()
    for tid in range(3):
        db.upsert_tweet({
            "ts": now - timedelta(minutes=tid), "tweet_id": tid,
            "symbol": "FRESH", "text": "x", "author": f"u{tid}",
            "likes": 0, "retweets": 0, "followers": 0, "url": "u",
            "source_adapter": "nitter", "sentiment_score": 0.0,
        })
    rows = db.daily_topic_aggregates(days=1, limit=10)
    fresh = next(r for r in rows if r["symbol"] == "FRESH")
    assert fresh["velocity"] == 3  # = today's count, no yesterday


def test_daily_topic_aggregates_empty_when_no_data(sqlite_db):
    """No tweets → empty list, no error."""
    assert db.daily_topic_aggregates(days=1, limit=10) == []


# ── _agg_table_for_minutes: continuous-aggregate fast-path routing ──────


def test_agg_table_for_minutes_maps_known_widths_to_aggregates():
    """The Live tab's per-tag chart reads from pre-aggregated
    `tweets_1h` / `tweets_1d` continuous aggregates when the
    requested bucket width matches. Verify the routing helper."""
    assert db._agg_table_for_minutes(60) == "tweets_1h"
    assert db._agg_table_for_minutes(60 * 24) == "tweets_1d"


def test_agg_table_for_minutes_falls_back_for_other_widths():
    """5-min, 15-min, 30-min, 1-min, 12-hour widths don't have a
    matching pre-aggregate — the helper should return None so the
    query falls back to a live `time_bucket` scan on `tweets`."""
    for minutes in (1, 5, 15, 30, 60 * 12):
        assert db._agg_table_for_minutes(minutes) is None, minutes


def test_per_symbol_buckets_sqlite_uses_live_scan_path(sqlite_db):
    """SQLite doesn't have the pre-aggregates — `per_symbol_buckets`
    must use the live `time_bucket`-equivalent scan and still return
    the right shape."""
    now = datetime.utcnow().replace(microsecond=0)
    for i, sym in enumerate(["AI", "AI", "TSLA"]):
        db.upsert_tweet({
            "ts": now - timedelta(minutes=10 - i), "tweet_id": 1000 + i,
            "symbol": sym, "text": "x", "author": "a",
            "likes": 0, "retweets": 0, "followers": 0, "url": "u",
            "source_adapter": "nitter", "sentiment_score": 0.5 + i * 0.1,
        })
    rows = db.per_symbol_buckets(minutes=5, hours=1)
    assert len(rows) >= 1
    for r in rows:
        assert set(r.keys()) == {"bucket", "symbol", "avg_sent", "n"}
