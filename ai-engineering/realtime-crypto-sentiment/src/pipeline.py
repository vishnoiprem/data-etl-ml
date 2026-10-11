"""Pipeline orchestrator.

Author: Prem Vishnoi <pvishnoi@avilx.com>

APScheduler jobs:
- scrape_tweets: every 60s, rotating tracked_tags set
- score_batch: every 60s, drains unscored tweets, runs sentiment model
- generate_signals: every 60s, per-tag sentiment z-score → signal
- paper_trade: every 5s, consumes latest signals + synthetic prices
- scrape_trending: every 60s, runs trending-tag discovery

Note: there is no live price feed. The paper broker uses a synthetic
unit price derived from the most recent tweet's engagement for that
tag (likes + 2×retweets + 0.1×followers, floored to ≥1). This is a
toy signal for the simulator — not a production price proxy.
"""
from __future__ import annotations

import signal
import sys
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger

from src.config import settings
from src.metrics import (
    PAPER_TRADES,
    PIPELINE_ERRORS,
    SCORE_LATENCY,
    SCRAPE_LATENCY,
    SIGNAL_LATENCY,
    SIGNALS_GENERATED,
    TWEETS_SCORED,
    TWEETS_SCRAPED,
    start_metrics_server,
)
from src.ml.sentiment import TwitterSentimentScorer
from src.ml.signal import generate_signal
from src.sources.registry import SourceRegistry
from src.sources.trending import (
    aggregate_tags,
    extract_tags_from_tweet,
)
from src.store import db
from src.trader.paper import PaperBroker


class SentimentPipeline:
    def __init__(self):
        self.sources = SourceRegistry.from_settings()
        self.scorer: TwitterSentimentScorer | None = None  # lazy
        self.broker = PaperBroker()
        # Latest synthetic unit price per tag (used by paper_trade)
        self._latest_prices: dict[str, dict] = {}
        # Latest signal per tag (used by paper_trade)
        self._latest_signals: dict[str, object] = {}
        self.scheduler = BlockingScheduler(timezone="UTC")

    # ── Jobs ─────────────────────────────────────────────────────────

    def scrape_tweets(self) -> None:
        """Pull tweets for one tracked_tag per cycle; rotates through the list."""
        tags = settings.tracked_tags
        if not tags:
            return
        # Use a stable rotating index based on minutes since epoch
        idx = int(datetime.utcnow().timestamp() // settings.scrape_interval_sec) % len(tags)
        tag = tags[idx]
        self._scrape_tag(tag)

    def _scrape_tag(self, tag: str) -> None:
        import asyncio
        asyncio.run(self._scrape_tag_async(tag))

    async def _scrape_tag_async(self, tag: str) -> None:
        with SCRAPE_LATENCY.labels(adapter=self.sources.active).time():
            try:
                tweets = await self.sources.fetch(tag, max_results=20)
            except Exception as e:
                PIPELINE_ERRORS.labels(stage="scrape").inc()
                logger.error(f"scrape error for {tag!r}: {e}")
                return
        TWEETS_SCRAPED.labels(adapter=self.sources.active).inc(len(tweets))
        # Insert one row per tweet. No per-symbol fanout — we use the tag
        # itself as the symbol so the dashboard can group by topic.
        for t in tweets:
            row = {
                "ts": t.ts,
                "tweet_id": t.id,
                "symbol": tag,
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
            # Compute a synthetic unit price from this tweet's engagement
            # for the paper broker. This is a stand-in; there is no live
            # market price.
            self._latest_prices[tag] = {
                "ts": t.ts,
                "symbol": tag,
                "price": _synthetic_price(t.likes, t.retweets, t.followers),
            }

    def score_batch(self) -> None:
        """Drain unscored tweets, run sentiment model, write back sentiment_score."""
        if self.scorer is None:
            try:
                self.scorer = TwitterSentimentScorer(
                    model_name=settings.sentiment_model,
                    batch_size=settings.sentiment_batch_size,
                )
            except Exception as e:
                PIPELINE_ERRORS.labels(stage="scorer_init").inc()
                logger.error(f"sentiment model init failed: {e}")
                return

        rows = db.fetch_unscored_tweets(limit=128)
        if not rows:
            return
        with SCORE_LATENCY.time():
            try:
                scores = self.scorer.score([r["text"] for r in rows])
            except Exception as e:
                PIPELINE_ERRORS.labels(stage="score").inc()
                logger.error(f"sentiment score failed: {e}")
                return
        TWEETS_SCORED.inc(len(rows))
        for r, s in zip(rows, scores):
            try:
                db.update_tweet_sentiment(r["tweet_id"], r["ts"], float(s))
            except Exception as e:
                PIPELINE_ERRORS.labels(stage="update_sentiment").inc()
                logger.debug(f"update sentiment error: {e}")

    def generate_signals(self) -> None:
        """For each tracked tag, compute sentiment z-score and emit a signal."""
        for tag in settings.tracked_tags:
            try:
                self._generate_signal_for(tag)
            except Exception as e:
                PIPELINE_ERRORS.labels(stage="signal").inc()
                logger.error(f"signal error for {tag}: {e}")

    def scrape_trending(self) -> None:
        """Scrape the trending_queries list (AI/data + stocks + dating),
        extract every cashtag/hashtag/keyword, and write 1-min-bucketed counts
        to `trending_tags`. Powers the dashboard's top-10 panel.
        """
        import asyncio
        queries = settings.trending_queries
        if not queries:
            return
        all_hits: list = []
        for q in queries:
            try:
                tweets = asyncio.run(self._scrape_tag_async(q))
            except Exception as e:
                PIPELINE_ERRORS.labels(stage="trending_scrape").inc()
                logger.debug(f"trending scrape error for {q!r}: {e}")
                continue
            # Score sentiment with the scorer if available; else skip
            for t in tweets:
                sentiment = None
                if self.scorer is not None:
                    try:
                        sentiment = float(self.scorer.score([t.text])[0])
                    except Exception:
                        sentiment = None
                hits = extract_tags_from_tweet(
                    tweet_text=t.text,
                    tweet_id=t.id,
                    ts=t.ts,
                    sentiment=sentiment,
                    url=t.url,
                    keywords=None,  # cashtags + hashtags only for trending
                )
                all_hits.extend(hits)

        if not all_hits:
            return

        grouped = aggregate_tags(all_hits)
        rows_written = 0
        for val in grouped.values():
            try:
                db.upsert_trending_tag({
                    "ts": val["ts"],
                    "bucket": val["bucket"],
                    "tag": val["tag"],
                    "tag_kind": val["tag_kind"],
                    "count": val["count"],
                    "avg_sentiment": val.get("avg_sentiment"),
                    "sample_text": val.get("sample_text"),
                    "sample_url": val.get("sample_url"),
                })
                rows_written += 1
            except Exception as e:
                PIPELINE_ERRORS.labels(stage="upsert_trending_tag").inc()
                logger.debug(f"upsert_trending_tag error: {e}")
        if rows_written:
            logger.info(f"trending: {len(all_hits)} tag hits → {rows_written} bucketed rows")

    def _generate_signal_for(self, tag: str) -> None:
        # Z-score the current 5-min sentiment mean against a history of
        # 5-min-bucket means (not raw per-tweet scores), so the std isn't
        # dominated by per-tweet noise.
        from src.store.db import sentiment_buckets
        buckets = sentiment_buckets(
            tag, minutes=5, hours=settings.signal_lookback_hours,
        )
        if len(buckets) < 2:
            return
        sentiment_value = float(buckets[-1]["avg_sent"])
        history_scores = [float(b["avg_sent"]) for b in buckets]

        sig = generate_signal(
            symbol=tag,
            sentiment_value=sentiment_value,
            sentiment_history=history_scores,
        )
        SIGNAL_LATENCY.observe(0.0)  # placeholder; full e2e latency not tracked here
        SIGNALS_GENERATED.labels(action=sig.action).inc()
        try:
            db.insert_signal(sig.to_row())
        except Exception as e:
            PIPELINE_ERRORS.labels(stage="insert_signal").inc()
            logger.debug(f"insert_signal error: {e}")
        # Hand to broker
        self._latest_signals[tag] = sig

    def paper_trade(self) -> None:
        """Consume latest signals + latest synthetic prices; fill via PaperBroker."""
        for sym, sig in list(self._latest_signals.items()):
            tick = self._latest_prices.get(sym)
            if tick is None:
                continue
            try:
                fill = self.broker.on_signal(sig, float(tick["price"]))
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
                        "price": fill.price,
                        "fee": fill.fee,
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

    def start(self) -> None:
        """Boot the pipeline; blocks until SIGINT."""
        logger.info("pipeline: init schema")
        try:
            db.init_schema()
        except Exception as e:
            # Fatal at boot — running without the schema would silently break every
            # insert, and the user would see an empty dashboard with no clue why.
            logger.error(f"init_schema failed (fatal): {e}")
            raise SystemExit(1) from e

        logger.info("pipeline: starting metrics server")
        start_metrics_server()

        logger.info("pipeline: scheduling jobs")
        # max_instances=1, coalesce=True: never run two cycles in parallel.
        # Without these, a slow sentiment batch can overlap the next scrape and
        # double-score the same unscored rows.
        self.scheduler.add_job(self.scrape_tweets, "interval",
                              seconds=settings.scrape_interval_sec, id="scrape",
                              next_run_time=datetime.utcnow(),
                              max_instances=1, coalesce=True)
        self.scheduler.add_job(self.score_batch, "interval",
                              seconds=settings.score_interval_sec, id="score",
                              next_run_time=datetime.utcnow() + __import__("datetime").timedelta(seconds=5),
                              max_instances=1, coalesce=True)
        self.scheduler.add_job(self.generate_signals, "interval",
                              seconds=settings.signal_interval_sec, id="signals",
                              next_run_time=datetime.utcnow() + __import__("datetime").timedelta(seconds=10),
                              max_instances=1, coalesce=True)
        self.scheduler.add_job(self.paper_trade, "interval",
                              seconds=settings.trade_interval_sec, id="trader",
                              next_run_time=datetime.utcnow() + __import__("datetime").timedelta(seconds=15),
                              max_instances=1, coalesce=True)
        self.scheduler.add_job(self.scrape_trending, "interval",
                              seconds=settings.scrape_interval_sec, id="trending",
                              next_run_time=datetime.utcnow() + __import__("datetime").timedelta(seconds=20),
                              max_instances=1, coalesce=True)

        def _handle_signal(signum, frame):
            logger.info("pipeline: SIGINT/SIGTERM, shutting down")
            try:
                self.scheduler.shutdown(wait=False)
            except Exception:
                pass
        signal.signal(signal.SIGINT, _handle_signal)
        signal.signal(signal.SIGTERM, _handle_signal)

        logger.info("pipeline: running. Ctrl-C to stop.")
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            pass
        logger.info("pipeline: stopped")


# Backwards-compat alias so old imports / tests still work.
CryptoPipeline = SentimentPipeline


def _synthetic_price(likes: int, retweets: int, followers: int) -> float:
    """Stand-in unit price derived from tweet engagement.

    The paper broker needs a numeric fill price to compute PnL, but there
    is no live market feed. This heuristic treats a tweet's reach as a
    rough proxy for "how much attention is on this topic" and floors at
    1.0 to avoid zero-qty fills.

    floors at 1.0 to avoid zero-qty fills.
    """
    return max(1.0, float(likes) + 2.0 * float(retweets) + 0.1 * float(followers))


def main() -> int:
    SentimentPipeline().start()
    return 0


if __name__ == "__main__":
    sys.exit(main())