"""Pipeline orchestrator.

Author: Prem Vishnoi <pvishnoi@avilx.com>

APScheduler jobs:
- scrape_tweets: every 60s, rotating topic set
- score_batch: every 60s, drains unscored tweets, runs FinBERT
- binance_stream: long-running asyncio task
- generate_signals: every 60s, per-symbol z-score + signal
- paper_trade: every 5s, consumes latest signals & ticks
"""
from __future__ import annotations

import asyncio
import signal
import sys
from datetime import datetime, timezone
from statistics import mean
from typing import Dict, List, Optional

from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger

from src.config import settings
from src.metrics import (
    PAPER_TRADES, PIPELINE_ERRORS, SCORE_LATENCY, SCRAPE_LATENCY,
    SIGNALS_GENERATED, SIGNAL_LATENCY, TWEETS_SCORED, TWEETS_SCRAPED,
    start_metrics_server,
)
from src.ml.finbert import FinBERTScorer
from src.ml.signal import generate_signal
from src.prices.binance_ws import stream_prices
from src.sources.registry import SourceRegistry
from src.store import db
from src.trader.paper import PaperBroker


class CryptoPipeline:
    def __init__(self):
        self.sources = SourceRegistry.from_settings()
        self.scorer: Optional[FinBERTScorer] = None  # lazy
        self.broker = PaperBroker()
        # Latest tick per symbol (used by signal generator)
        self._latest_prices: Dict[str, dict] = {}
        # Latest signal per symbol (used by paper_trade)
        self._latest_signals: Dict[str, object] = {}
        self._stop = asyncio.Event()
        self.scheduler = BlockingScheduler(timezone="UTC")

    # ── Jobs ─────────────────────────────────────────────────────────

    def scrape_tweets(self) -> None:
        """Pull tweets for one topic per cycle; rotates through the topic list."""
        topics = settings.all_topics
        if not topics:
            return
        # Use a stable rotating index based on minutes since epoch
        idx = int(datetime.utcnow().timestamp() // settings.scrape_interval_sec) % len(topics)
        topic = topics[idx]
        self._scrape_topic(topic)

    def _scrape_topic(self, topic: str) -> None:
        asyncio.run(self._scrape_topic_async(topic))

    async def _scrape_topic_async(self, topic: str) -> None:
        # Determine the symbol(s) the topic maps to (cashtag/hashtag → symbols)
        symbols = self._symbols_for_topic(topic)
        if not symbols:
            return
        with SCRAPE_LATENCY.labels(adapter=self.sources.active).time():
            try:
                tweets = await self.sources.fetch(topic, max_results=20)
            except Exception as e:
                PIPELINE_ERRORS.labels(stage="scrape").inc()
                logger.error(f"scrape error for {topic!r}: {e}")
                return
        TWEETS_SCRAPED.labels(adapter=self.sources.active).inc(len(tweets))
        # Insert one row per (tweet, symbol) — multi-tag if multiple symbols match
        for t in tweets:
            for sym in symbols:
                row = {
                    "ts": t.ts,
                    "tweet_id": t.id,
                    "symbol": sym,
                    "text": t.text,
                    "author": t.author,
                    "likes": t.likes,
                    "retweets": t.retweets,
                    "followers": t.followers,
                    "url": t.url,
                    "source_adapter": self.sources.active,
                    "raw_json": None,
                }
                try:
                    db.upsert_tweet(row)
                except Exception as e:
                    PIPELINE_ERRORS.labels(stage="upsert_tweet").inc()
                    logger.debug(f"upsert_tweet error: {e}")

    @staticmethod
    def _symbols_for_topic(topic: str) -> List[str]:
        """Map a topic to one or more symbols.

        `$BTC` → `BTC`; `#memecoin` → none; `bitcoin` → `BTC`; etc.
        """
        t = topic.strip().lower().lstrip("$").lstrip("#")
        alias = {
            "bitcoin": "BTC", "btc": "BTC",
            "ethereum": "ETH", "eth": "ETH",
            "solana": "SOL", "sol": "SOL",
            "binance coin": "BNB", "bnb": "BNB",
            "ripple": "XRP", "xrp": "XRP",
            "dogecoin": "DOGE", "doge": "DOGE",
            "cardano": "ADA", "ada": "ADA",
            "avalanche": "AVAX", "avax": "AVAX",
            "chainlink": "LINK", "link": "LINK",
            "polygon": "MATIC", "matic": "MATIC",
            "memecoin": "", "altcoin": "",  # no single symbol
        }
        out = alias.get(t, "")
        return [out] if out else []

    def score_batch(self) -> None:
        """Drain unscored tweets, run FinBERT, write back sentiment_score."""
        if self.scorer is None:
            try:
                self.scorer = FinBERTScorer(
                    model_name=settings.finbert_model,
                    batch_size=settings.finbert_batch_size,
                )
            except Exception as e:
                PIPELINE_ERRORS.labels(stage="scorer_init").inc()
                logger.error(f"FinBERT init failed: {e}")
                return

        rows = db.fetch_unscored_tweets(limit=128)
        if not rows:
            return
        with SCORE_LATENCY.time():
            try:
                scores = self.scorer.score([r["text"] for r in rows])
            except Exception as e:
                PIPELINE_ERRORS.labels(stage="score").inc()
                logger.error(f"FinBERT score failed: {e}")
                return
        TWEETS_SCORED.inc(len(rows))
        for r, s in zip(rows, scores):
            try:
                db.update_tweet_sentiment(r["tweet_id"], r["ts"], float(s))
            except Exception as e:
                PIPELINE_ERRORS.labels(stage="update_sentiment").inc()
                logger.debug(f"update sentiment error: {e}")

    def generate_signals(self) -> None:
        """For each symbol, compute z-score sentiment + momentum and emit a signal."""
        for sym in settings.symbols:
            try:
                self._generate_signal_for(sym)
            except Exception as e:
                PIPELINE_ERRORS.labels(stage="signal").inc()
                logger.error(f"signal error for {sym}: {e}")

    def _generate_signal_for(self, sym: str) -> None:
        # 5-min sentiment value (mean of last 5m of scored tweets) and history (24h)
        tweets_5m = db.fetch_recent_tweets(sym, minutes=5)
        scored_5m = [t["sentiment_score"] for t in tweets_5m if t["sentiment_score"] is not None]
        if not scored_5m:
            return
        sentiment_value = mean(scored_5m)
        # History: average sentiment per minute over the lookback (24h)
        from src.store.db import fetch_recent_tweets as _frt
        history_rows = _frt(sym, minutes=settings.signal_lookback_hours * 60)
        history_scores = [r["sentiment_score"] for r in history_rows if r["sentiment_score"] is not None]
        if len(history_scores) < 2:
            return

        # Momentum: 5-min price return vs history of minute-returns over lookback
        rets_5m = db.recent_price_returns(sym, minutes=5)
        if not rets_5m:
            return
        momentum_value = sum(rets_5m)  # net 5-min return
        from src.store.db import recent_price_returns as _rpr
        history_returns: List[float] = []
        # Sample 5-min-return windows over the lookback
        # Cheap implementation: minute returns then aggregate every 5
        minute_returns = _rpr(sym, minutes=settings.signal_lookback_hours * 60)
        for i in range(0, len(minute_returns) - 4, 5):
            history_returns.append(sum(minute_returns[i : i + 5]))
        if len(history_returns) < 2:
            return

        sig = generate_signal(
            symbol=sym,
            sentiment_value=sentiment_value,
            sentiment_history=history_scores,
            momentum_value=momentum_value,
            momentum_history=history_returns,
        )
        SIGNAL_LATENCY.observe(0.0)  # placeholder; full e2e latency not tracked here
        SIGNALS_GENERATED.labels(action=sig.action).inc()
        try:
            db.insert_signal(sig.to_row())
        except Exception as e:
            PIPELINE_ERRORS.labels(stage="insert_signal").inc()
            logger.debug(f"insert_signal error: {e}")
        # Hand to broker
        self._latest_signals[sym] = sig

    def paper_trade(self) -> None:
        """Consume latest signals + latest prices; fill via PaperBroker."""
        for sym, sig in list(self._latest_signals.items()):
            tick = self._latest_prices.get(sym)
            if tick is None:
                continue
            try:
                fill = self.broker.on_signal(sig, float(tick["price_usd"]))
            except Exception as e:
                PIPELINE_ERRORS.labels(stage="paper_trade").inc()
                logger.error(f"paper_trade error for {sym}: {e}")
                continue
            if fill is not None:
                PAPER_TRADES.labels(side=fill.side).inc()
                try:
                    db.insert_paper_trade({
                        "ts": fill.ts,
                        "symbol": fill.symbol,
                        "side": fill.side,
                        "qty": fill.qty,
                        "price_usd": fill.price_usd,
                        "fee_usd": fill.fee_usd,
                        "cash_after": fill.cash_after,
                        "reason": fill.reason,
                    })
                except Exception as e:
                    PIPELINE_ERRORS.labels(stage="insert_paper_trade").inc()
                    logger.debug(f"insert_paper_trade error: {e}")
                # Snapshot the position
                pos = self.broker.positions.get(sym)
                if pos is not None:
                    db.upsert_position({
                        "ts": fill.ts,
                        "symbol": sym,
                        "qty": pos.qty,
                        "avg_price": pos.avg_price,
                        "realized_pnl": pos.realized_pnl,
                    })

    # ── Lifecycle ─────────────────────────────────────────────────────

    async def _on_tick(self, tick: dict) -> None:
        self._latest_prices[tick["symbol"]] = tick
        self.broker.on_price_tick(tick)
        try:
            db.upsert_price(tick)
        except Exception as e:
            PIPELINE_ERRORS.labels(stage="upsert_price").inc()
            logger.debug(f"upsert_price error: {e}")

    async def _run_ws(self) -> None:
        await stream_prices(self._on_tick, stop_event=self._stop)

    def start(self) -> None:
        """Boot the pipeline; blocks until SIGINT."""
        logger.info("pipeline: init schema")
        try:
            db.init_schema()
        except Exception as e:
            logger.warning(f"init_schema failed (non-fatal): {e}")

        logger.info("pipeline: starting metrics server")
        start_metrics_server()

        logger.info("pipeline: scheduling jobs")
        self.scheduler.add_job(self.scrape_tweets, "interval",
                              seconds=settings.scrape_interval_sec, id="scrape",
                              next_run_time=datetime.utcnow())
        self.scheduler.add_job(self.score_batch, "interval",
                              seconds=settings.score_interval_sec, id="score",
                              next_run_time=datetime.utcnow() + __import__("datetime").timedelta(seconds=5))
        self.scheduler.add_job(self.generate_signals, "interval",
                              seconds=settings.signal_interval_sec, id="signals",
                              next_run_time=datetime.utcnow() + __import__("datetime").timedelta(seconds=10))
        self.scheduler.add_job(self.paper_trade, "interval",
                              seconds=settings.trade_interval_sec, id="trader",
                              next_run_time=datetime.utcnow() + __import__("datetime").timedelta(seconds=15))

        # Start the WS task in the background
        loop = asyncio.new_event_loop()
        def _kick_ws():
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._run_ws())
        import threading
        ws_thread = threading.Thread(target=_kick_ws, daemon=True)
        ws_thread.start()

        def _handle_signal(signum, frame):
            logger.info("pipeline: SIGINT, shutting down")
            self._stop.set()
            self.scheduler.shutdown(wait=False)
            try:
                loop.call_soon_threadsafe(loop.stop)
            except Exception:
                pass
            sys.exit(0)
        signal.signal(signal.SIGINT, _handle_signal)
        signal.signal(signal.SIGTERM, _handle_signal)

        logger.info("pipeline: running. Ctrl-C to stop.")
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            pass


def main() -> int:
    CryptoPipeline().start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
