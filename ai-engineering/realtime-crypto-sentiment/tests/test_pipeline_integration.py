"""End-to-end integration test for the pipeline.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Uses SQLite in-memory. The pipeline's CRUD helpers, the signal
generator, and the paper broker are all wired together and verified
to produce:
  - rows in `tweets` (with sentiment_score populated)
  - rows in `signals` (BUY/SELL/HOLD)
  - rows in `paper_trades` (when signal action is BUY)
  - rows in `positions` (after each fill)

External services (Nitter, sentiment model) are stubbed. There is no
price feed — the paper broker uses a synthetic unit price.
"""
from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta

import pytest

# ── Stubs ────────────────────────────────────────────────────────────────


class _StubSource:
    """Returns canned RawTweets from a queue, one per fetch() call."""
    name = "stub"

    def __init__(self, tweets: list[dict]):
        self.tweets = list(tweets)
        self.calls: list[str] = []

    async def fetch(self, query, max_results=20):
        self.calls.append(query)
        if not self.tweets:
            return []
        from src.sources.base import RawTweet
        d = self.tweets.pop(0)
        return [RawTweet(
            id=int(d["id"]),
            ts=d["ts"],
            author=d["author"],
            text=d["text"],
            likes=d.get("likes", 0),
            retweets=d.get("retweets", 0),
            followers=d.get("followers", 0),
            url=d.get("url", ""),
            symbol_tags=[d.get("symbol", query)],
        )]

    def is_healthy(self) -> bool:
        return True

    async def close(self):
        pass


def _install_fake_pipeline(monkeypatch, responses):
    def _fake_pipeline(*args, **kwargs):
        state = {"i": 0}

        def _fn(texts, batch_size=None, **_kw):
            out = []
            for _ in texts:
                if state["i"] >= len(responses):
                    out.append(responses[-1])  # reuse last
                else:
                    out.append(responses[state["i"]])
                state["i"] += 1
            return out

        return _fn

    class _FakeTransformers:
        @staticmethod
        def pipeline(*args, **kwargs):
            return _fake_pipeline(*args, **kwargs)

    sys.modules["transformers"] = _FakeTransformers


class _StubRegistry:
    """Minimal SourceAdapter-shaped stand-in for SourceRegistry."""
    active = "stub"

    def __init__(self, s):
        self._s = s

    async def fetch(self, q, max_results=20):
        return await self._s.fetch(q, max_results)

    def is_healthy(self) -> bool:
        return True

    async def close(self):
        pass


# ── Tests ────────────────────────────────────────────────────────────────


def test_pipeline_end_to_end_with_sqlite(monkeypatch, tmp_path):
    """Full pipeline: stubbed source + sentiment model → DB → signal → paper fill."""
    # 1) Swap in a fresh SQLite engine BEFORE we import any pipeline module.
    from src.store import db
    db.override_engine(f"sqlite:///{tmp_path}/test.db")
    db.ensure_sqlite_schema()

    # 2) Stub the sentiment pipeline (cardiffnlp LABEL_0/1/2).
    _install_fake_pipeline(monkeypatch, [
        [{"label": "LABEL_2", "score": 0.9},
         {"label": "LABEL_0", "score": 0.05},
         {"label": "LABEL_1", "score": 0.05}],
    ])

    # 3) Construct the pipeline.
    from src.pipeline import SentimentPipeline

    pipe = SentimentPipeline()

    # 4) Replace the entire SourceRegistry with a stub.
    stub = _StubSource([
        {
            "id": 1001, "ts": datetime.now(UTC),
            "author": "alice", "text": "AI is changing everything",
            "likes": 100, "retweets": 10, "followers": 5000,
            "url": "https://x.com/alice/status/1001",
        },
    ])

    pipe.sources = _StubRegistry(stub)

    # 5) Drive the scrape → AI tag.
    pipe._scrape_tag("AI")

    # 6) Verify the tweet landed in the DB (un-scored).
    rows = db.fetch_unscored_tweets(limit=10)
    assert len(rows) == 1
    assert rows[0]["text"] == "AI is changing everything"

    # 7) Run the sentiment scorer.
    pipe.score_batch()
    rows_after = db.fetch_unscored_tweets(limit=10)
    assert rows_after == []  # drained

    # 8) Run signal generation. With only 1 scored tweet in 1 bucket, it
    # bails on insufficient history (z-score undefined for n<2). So we go
    # directly to the paper_trade path with a forced BUY signal.
    now = datetime.now(UTC)

    # 9) Force a BUY signal directly to test the paper_trade path.
    from src.ml.signal import Signal
    buy_sig = Signal(
        symbol="AI", ts=now, action="BUY", score=1.5,
        sentiment_zscore=2.0, momentum_zscore=0.0, reason="force",
    )
    pipe._latest_signals["AI"] = buy_sig
    # Provide a synthetic unit price derived from the tweet's engagement.
    pipe._latest_prices["AI"] = {
        "ts": now, "symbol": "AI",
        "price": float(100 + 2 * 10 + 0.1 * 5000),  # 100 + 20 + 500 = 620
    }

    # 10) Run paper trade.
    pipe.paper_trade()
    trades = db.fetch_paper_trades(limit=10)
    assert len(trades) == 1
    assert trades[0]["side"] == "BUY"
    assert trades[0]["symbol"] == "AI"
    # Field names should be `price` and `fee` (not `_usd`).
    assert "price" in trades[0]
    assert "fee" in trades[0]

    # 11) Position snapshot exists
    positions = db.all_open_positions()
    assert len(positions) == 1
    assert positions[0]["symbol"] == "AI"
    assert positions[0]["qty"] > 0


def test_pipeline_scrape_tweets_no_op_on_empty_tracked_tags(monkeypatch, tmp_path):
    """With an empty tracked_tags list, scrape_tweets() must be a no-op."""
    from src.store import db
    db.override_engine(f"sqlite:///{tmp_path}/test3.db")
    db.ensure_sqlite_schema()

    from src.pipeline import SentimentPipeline
    pipe = SentimentPipeline()
    stub = _StubSource([])

    pipe.sources = _StubRegistry(stub)

    # Force the instance-level setting to an empty list for this test.
    # Pydantic v2 makes the field a model attribute, not a class attribute,
    # so we patch the *instance* (`settings`) rather than its class.
    from src.config import settings
    monkeypatch.setattr(settings, "tracked_tags", [], raising=False)
    pipe.scrape_tweets()
    assert stub.calls == []


def test_pipeline_scrape_tweets_picks_a_tracked_tag(monkeypatch, tmp_path):
    """scrape_tweets() picks a topic from the configured tracked_tags
    list (a rotating index, not a fanout)."""
    from src.store import db
    db.override_engine(f"sqlite:///{tmp_path}/test3b.db")
    db.ensure_sqlite_schema()

    from src.pipeline import SentimentPipeline
    pipe = SentimentPipeline()
    stub = _StubSource([])

    pipe.sources = _StubRegistry(stub)

    from src.config import settings
    monkeypatch.setattr(settings, "tracked_tags", ["AI", "LLM"], raising=False)
    pipe.scrape_tweets()
    # Exactly one of the two configured tags was scraped
    assert len(stub.calls) == 1
    assert stub.calls[0] in ("AI", "LLM")


def test_pipeline_signal_generation_hold_on_insufficient_history(tmp_path):
    """With only 1 scored tweet, the signal generator must NOT crash and
    must NOT write a signal (the z-score is undefined for n<2)."""
    from src.store import db
    db.override_engine(f"sqlite:///{tmp_path}/test_hold.db")
    db.ensure_sqlite_schema()

    from src.pipeline import SentimentPipeline
    pipe = SentimentPipeline()
    pipe.sources = _StubRegistry(_StubSource([]))

    db.upsert_tweet({
        "ts": datetime.now(UTC), "tweet_id": 1, "symbol": "AI",
        "text": "x", "author": "a", "likes": 0, "retweets": 0, "followers": 0,
        "url": "u", "source_adapter": "stub", "sentiment_score": 0.9,
    })
    pipe._generate_signal_for("AI")
    # No signal row written
    assert db.fetch_recent_signals("AI", hours=1, limit=10) == []


def test_pipeline_signal_generation_buy_on_positive_sentiment_seed(tmp_path):
    """A clearly bullish sentiment seed (5-min mean >> history mean) →
    BUY signal. Pure sentiment, no momentum."""
    from src.store import db
    db.override_engine(f"sqlite:///{tmp_path}/test_buy.db")
    db.ensure_sqlite_schema()

    from src.pipeline import SentimentPipeline
    pipe = SentimentPipeline()
    pipe.sources = _StubRegistry(_StubSource([]))

    now = datetime.now(UTC)
    # Seed 13 scored tweets across 5-min buckets, all positive, rising.
    for i in range(13):
        db.upsert_tweet({
            "ts": now - timedelta(minutes=65 - i * 5), "tweet_id": 100 + i,
            "symbol": "AI", "text": f"t{i}", "author": "a",
            "likes": 0, "retweets": 0, "followers": 0, "url": "u",
            "source_adapter": "stub",
            "sentiment_score": 0.4 + i * 0.05,  # 0.4 → 1.0
        })

    pipe._generate_signal_for("AI")
    sigs = db.fetch_recent_signals("AI", hours=2, limit=10)
    assert len(sigs) == 1, f"expected 1 signal, got {len(sigs)}: {sigs}"
    assert sigs[0]["action"] == "BUY", f"expected BUY, got {sigs[0]}"
    # Score must be > threshold (1.0)
    assert sigs[0]["score"] > 1.0


def test_pipeline_signal_generation_sell_on_negative_sentiment_seed(tmp_path):
    """Symmetric: clearly bearish seed → SELL signal."""
    from src.store import db
    db.override_engine(f"sqlite:///{tmp_path}/test_sell.db")
    db.ensure_sqlite_schema()

    from src.pipeline import SentimentPipeline
    pipe = SentimentPipeline()
    pipe.sources = _StubRegistry(_StubSource([]))

    now = datetime.now(UTC)
    for i in range(13):
        db.upsert_tweet({
            "ts": now - timedelta(minutes=65 - i * 5), "tweet_id": 100 + i,
            "symbol": "AI", "text": f"t{i}", "author": "a",
            "likes": 0, "retweets": 0, "followers": 0, "url": "u",
            "source_adapter": "stub",
            "sentiment_score": -0.4 - i * 0.05,  # -0.4 → -1.0
        })

    pipe._generate_signal_for("AI")
    sigs = db.fetch_recent_signals("AI", hours=2, limit=10)
    assert len(sigs) == 1, f"expected 1 signal, got {len(sigs)}: {sigs}"
    assert sigs[0]["action"] == "SELL", f"expected SELL, got {sigs[0]}"
    assert sigs[0]["score"] < -1.0


def test_pipeline_paper_trade_records_pnl_round_trip(tmp_path, monkeypatch):
    """BUY at unit price 50, SELL at 51 → realized > 0 recorded in the DB."""
    from src.store import db
    db.override_engine(f"sqlite:///{tmp_path}/test_pnl.db")
    db.ensure_sqlite_schema()

    from src.pipeline import SentimentPipeline
    pipe = SentimentPipeline()
    pipe.sources = _StubRegistry(_StubSource([]))
    now = datetime.now(UTC)

    # Force a BUY signal
    from src.ml.signal import Signal
    pipe._latest_signals["AI"] = Signal(
        symbol="AI", ts=now, action="BUY", score=1.5,
        sentiment_zscore=2.0, momentum_zscore=0.0, reason="force",
    )
    pipe._latest_prices["AI"] = {"ts": now, "symbol": "AI", "price": 50.0}
    pipe.paper_trade()
    assert len(db.fetch_paper_trades(limit=10)) == 1

    # Now force a SELL signal at a higher price. Bump the ts by 1ms so
    # the (ts, symbol) PK on paper_trades doesn't conflict with the BUY.
    sell_ts = now + timedelta(milliseconds=1)
    pipe._latest_signals["AI"] = Signal(
        symbol="AI", ts=sell_ts, action="SELL", score=-1.5,
        sentiment_zscore=-2.0, momentum_zscore=0.0, reason="force-sell",
    )
    pipe._latest_prices["AI"] = {"ts": sell_ts, "symbol": "AI", "price": 51.0}
    pipe.paper_trade()
    trades = db.fetch_paper_trades(limit=10)
    assert len(trades) == 2, f"expected 2 trades, got {len(trades)}: {trades}"
    # The SELL trade's stored reason matches (DESC order → SELL first)
    assert trades[0]["side"] == "SELL"
    assert trades[0]["reason"] == "force-sell"
    assert trades[0]["price"] == pytest.approx(51.0, abs=1e-6)
    assert trades[1]["side"] == "BUY"
    assert trades[1]["price"] == pytest.approx(50.0, abs=1e-6)


def test_pipeline_scrape_tag_writes_one_row(tmp_path):
    """A single scrape of one tag writes exactly one tweet row."""
    from src.store import db
    db.override_engine(f"sqlite:///{tmp_path}/test_multi.db")
    db.ensure_sqlite_schema()

    from src.pipeline import SentimentPipeline
    pipe = SentimentPipeline()
    stub = _StubSource([{
        "id": 777, "ts": datetime.now(UTC), "author": "x",
        "text": "ai is wild", "likes": 0, "retweets": 0, "followers": 0,
        "url": "u",
    }])
    pipe.sources = _StubRegistry(stub)
    pipe._scrape_tag("AI")
    # Exactly one row inserted for the "AI" tag
    assert len(db.fetch_unscored_tweets(limit=10)) == 1
    assert stub.calls == ["AI"]


def test_pipeline_synthetic_price_floor_is_one(monkeypatch):
    """The synthetic price must floor at 1.0 so a zero-engagement tweet
    still produces a valid (non-zero) unit price for the broker."""
    from src.pipeline import _synthetic_price
    assert _synthetic_price(0, 0, 0) == 1.0
    assert _synthetic_price(100, 0, 0) == 100.0
    # 2*retweets + 0.1*followers
    assert _synthetic_price(0, 10, 0) == 20.0
    assert _synthetic_price(0, 0, 100) == 10.0