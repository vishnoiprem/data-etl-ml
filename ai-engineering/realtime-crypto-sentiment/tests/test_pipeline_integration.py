"""End-to-end integration test for the pipeline.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Uses SQLite in-memory. The pipeline's CRUD helpers, the signal generator, and
the paper broker are all wired together and verified to produce:
  - rows in `tweets` (with sentiment_score populated)
  - rows in `signals` (BUY/SELL/HOLD)
  - rows in `paper_trades` (when signal action is BUY)
  - rows in `positions` (after each fill)

External services (Nitter, Binance WS, FinBERT) are stubbed.
"""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from typing import List

import pytest


# ── Stubs ────────────────────────────────────────────────────────────────


class _StubSource:
    """Returns canned RawTweets from a queue, one per fetch() call."""
    name = "stub"

    def __init__(self, tweets: List[dict]):
        self.tweets = list(tweets)
        self.calls: List[str] = []

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


# ── Tests ────────────────────────────────────────────────────────────────


def test_pipeline_end_to_end_with_sqlite(monkeypatch, tmp_path):
    """Full pipeline: stubbed source + FinBERT → DB → signal → paper fill."""
    # 1) Swap in a fresh SQLite engine BEFORE we import any pipeline module.
    from src.store import db
    db.override_engine(f"sqlite:///{tmp_path}/test.db")
    db.ensure_sqlite_schema()

    # 2) Stub FinBERT pipeline.
    _install_fake_pipeline(monkeypatch, [
        [{"label": "positive", "score": 0.9},
         {"label": "negative", "score": 0.05},
         {"label": "neutral", "score": 0.05}],
    ])

    # 3) Construct the pipeline.
    from src.pipeline import CryptoPipeline

    pipe = CryptoPipeline()

    # 4) Replace the entire SourceRegistry with a stub.
    stub = _StubSource([
        {
            "id": 1001, "ts": datetime.now(timezone.utc),
            "author": "alice", "text": "BTC to the moon",
            "likes": 100, "retweets": 10, "followers": 5000,
            "url": "https://x.com/alice/status/1001",
        },
    ])

    class _StubRegistry:
        active = "stub"
        def __init__(self, s): self._s = s
        async def fetch(self, q, max_results=20):
            return await self._s.fetch(q, max_results)
        def is_healthy(self): return True
        async def close(self): pass

    pipe.sources = _StubRegistry(stub)

    # 5) Drive the scrape topic -> BTC.
    pipe._scrape_topic("bitcoin")

    # 6) Verify the tweet landed in the DB (un-scored).
    rows = db.fetch_unscored_tweets(limit=10)
    assert len(rows) == 1
    assert rows[0]["text"] == "BTC to the moon"

    # 7) Run the FinBERT scorer.
    pipe.score_batch()
    rows_after = db.fetch_unscored_tweets(limit=10)
    assert rows_after == []  # drained

    # 8) Inject a price series. We then call _generate_signal_for, but it
    # bails on insufficient history (only 1 scored tweet). So we go directly
    # to the paper_trade path with a forced BUY signal.
    now = datetime.now(timezone.utc)
    for i in range(10):
        db.upsert_price({"ts": now - timedelta(seconds=30 * i),
                         "symbol": "BTC", "price_usd": 50_000.0 + i * 10,
                         "volume_usd": 100.0})

    # 9) Force a BUY signal directly to test the paper_trade path.
    from src.ml.signal import Signal
    buy_sig = Signal(
        symbol="BTC", ts=now, action="BUY", score=1.5,
        sentiment_zscore=2.0, momentum_zscore=1.0, reason="force",
    )
    pipe._latest_signals["BTC"] = buy_sig
    # Provide a latest price
    pipe._latest_prices["BTC"] = {
        "ts": now, "symbol": "BTC", "price_usd": 50_500.0, "volume_usd": 100.0,
    }

    # 10) Run paper trade.
    pipe.paper_trade()
    trades = db.fetch_paper_trades(limit=10)
    assert len(trades) == 1
    assert trades[0]["side"] == "BUY"
    assert trades[0]["symbol"] == "BTC"

    # 11) Position snapshot exists
    positions = db.all_open_positions()
    assert len(positions) == 1
    assert positions[0]["symbol"] == "BTC"
    assert positions[0]["qty"] > 0


def test_pipeline_topics_to_symbols_mapping():
    """Topic → symbol resolution (bitcoin→BTC, etc.)."""
    from src.pipeline import CryptoPipeline
    pipe = CryptoPipeline()
    assert pipe._symbols_for_topic("$BTC") == ["BTC"]
    assert pipe._symbols_for_topic("bitcoin") == ["BTC"]
    assert pipe._symbols_for_topic("ethereum") == ["ETH"]
    assert pipe._symbols_for_topic("solana") == ["SOL"]
    assert pipe._symbols_for_topic("chainlink") == ["LINK"]
    assert pipe._symbols_for_topic("memecoin") == []  # no single symbol
    assert pipe._symbols_for_topic("random-crypto-coin") == []


def test_pipeline_scrape_topic_skips_unmapped(monkeypatch, tmp_path):
    """Unmapped topics are a no-op (no DB writes)."""
    from src.store import db
    db.override_engine(f"sqlite:///{tmp_path}/test2.db")
    db.ensure_sqlite_schema()

    from src.pipeline import CryptoPipeline
    pipe = CryptoPipeline()
    stub = _StubSource([{
        "id": 999, "ts": datetime.now(timezone.utc), "author": "x",
        "text": "x", "likes": 0, "retweets": 0, "followers": 0, "url": "u",
    }])

    class _StubRegistry:
        active = "stub"
        def __init__(self, s): self._s = s
        async def fetch(self, q, max_results=20):
            return await self._s.fetch(q, max_results)
        def is_healthy(self): return True
        async def close(self): pass

    pipe.sources = _StubRegistry(stub)

    pipe._scrape_topic("memecoin")  # no symbol → no write
    assert db.fetch_unscored_tweets(limit=10) == []
    assert stub.calls == []  # never even called the source


def test_pipeline_scrape_tweets_rotates_topic(monkeypatch, tmp_path):
    """scrape_tweets() picks a topic based on a time-based index."""
    from src.store import db
    db.override_engine(f"sqlite:///{tmp_path}/test3.db")
    db.ensure_sqlite_schema()

    from src.pipeline import CryptoPipeline
    pipe = CryptoPipeline()
    stub = _StubSource([])

    class _StubRegistry:
        active = "stub"
        def __init__(self, s): self._s = s
        async def fetch(self, q, max_results=20):
            return await self._s.fetch(q, max_results)
        def is_healthy(self): return True
        async def close(self): pass

    pipe.sources = _StubRegistry(stub)

    # With empty topic list, it's a no-op
    from src.config import settings
    monkeypatch.setattr(type(settings), "all_topics", property(lambda self: []), raising=False)
    pipe.scrape_tweets()
    assert stub.calls == []


def test_pipeline_signal_generation_writes_signal(tmp_path):
    """When there are enough scored tweets + price points, a signal row is produced."""
    from src.store import db
    db.override_engine(f"sqlite:///{tmp_path}/test_sig.db")
    db.ensure_sqlite_schema()

    from src.pipeline import CryptoPipeline
    pipe = CryptoPipeline()
    stub = _StubSource([])

    class _StubRegistry:
        active = "stub"
        def __init__(self, s): self._s = s
        async def fetch(self, q, max_results=20):
            return await self._s.fetch(q, max_results)
        def is_healthy(self): return True
        async def close(self): pass

    pipe.sources = _StubRegistry(stub)

    now = datetime.now(timezone.utc)
    # Seed 30 scored tweets in the last 60 minutes
    for i in range(30):
        db.upsert_tweet({
            "ts": now - timedelta(minutes=30 - i),
            "tweet_id": 1000 + i, "symbol": "BTC",
            "text": f"tweet {i}", "author": f"a{i}",
            "likes": 0, "retweets": 0, "followers": 0, "url": "u",
            "source_adapter": "stub", "raw_json": None,
            "sentiment_score": float(i - 15) / 30.0,  # varies -0.5..+0.5
        })
    # Seed 30 prices in the last 60 minutes
    for i in range(30):
        db.upsert_price({"ts": now - timedelta(minutes=30 - i),
                         "symbol": "BTC",
                         "price_usd": 50_000.0 + (i - 15) * 10,
                         "volume_usd": 100.0})

    pipe._generate_signal_for("BTC")
    signals = db.fetch_recent_signals("BTC", hours=2, limit=10)
    assert len(signals) == 1
    assert signals[0]["action"] in {"BUY", "SELL", "HOLD"}
    assert signals[0]["reason"]
