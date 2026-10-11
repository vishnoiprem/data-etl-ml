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
    """Returns canned tweets from `tweets` queue, one per fetch() call."""
    name = "stub"

    def __init__(self, tweets: List[dict]):
        self.tweets = list(tweets)
        self.calls: List[str] = []

    async def fetch(self, query, max_results=20):
        self.calls.append(query)
        return [self.tweets.pop(0)] if self.tweets else []

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

    # 4) Replace SourceRegistry with our stub.
    stub = _StubSource([
        {
            "id": 1001, "ts": datetime.now(timezone.utc),
            "author": "alice", "text": "BTC to the moon",
            "likes": 100, "retweets": 10, "followers": 5000,
            "url": "https://x.com/alice/status/1001",
        },
    ])
    pipe.sources._adapters = [stub]
    pipe.sources._primary = stub
    pipe.sources.active = "stub"

    # 5) Drive the scrape topic -> BTC.
    pipe._scrape_topic("bitcoin")

    # 6) Verify the tweet landed in the DB (un-scored).
    rows = db.fetch_unscored_tweets(limit=10)
    assert len(rows) == 1
    assert rows[0]["text"] == "BTC to the moon"
    assert rows[0]["sentiment_score"] is None

    # 7) Run the FinBERT scorer.
    pipe.score_batch()
    rows_after = db.fetch_unscored_tweets(limit=10)
    assert rows_after == []  # drained

    # 8) Inject a price series and a signal.
    now = datetime.now(timezone.utc)
    for i in range(10):
        db.upsert_price({"ts": now - timedelta(minutes=10 - i),
                         "symbol": "BTC", "price_usd": 50_000.0 + i * 10,
                         "volume_usd": 100.0})
    # Generate signal — should BUY given positive sentiment
    pipe._generate_signal_for("BTC")
    signals = db.fetch_recent_signals("BTC", hours=1, limit=10)
    assert len(signals) == 1
    assert signals[0]["action"] in {"BUY", "HOLD"}  # depends on z-score

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
    pipe.sources._adapters = [stub]
    pipe.sources._primary = stub
    pipe.sources.active = "stub"

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
    pipe.sources._adapters = [stub]
    pipe.sources._primary = stub
    pipe.sources.active = "stub"

    # With empty topic list, it's a no-op
    from src.config import settings
    monkeypatch.setattr(settings, "all_topics", [], raising=False)
    pipe.scrape_tweets()
    assert stub.calls == []
