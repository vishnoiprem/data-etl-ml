"""Live-data demo driver.

Runs the *real* pipeline code paths — same signal generator, same paper
broker, same DB upserts, same Twitter-sentiment scorer interface — but
feeds it synthetic tweets and engagement-derived unit prices, since
this sandbox has no outbound access to Nitter or X.com.

Watches the SQL tables + the broker fill its wallet in real time so you
can see the live state change as ticks arrive.
"""
from __future__ import annotations

import asyncio
import math
import random
import sys
import time
from datetime import UTC, datetime, timedelta

from loguru import logger

from src.config import settings
from src.ml.sentiment import TwitterSentimentScorer
from src.ml.signal import Signal, generate_signal
from src.store import db
from src.trader.paper import PaperBroker


# ── Demo knobs ────────────────────────────────────────────────────────

DURATION_SEC = 30
TICK_INTERVAL = 0.5  # one synthetic tweet every 500ms
TWEETS_PER_BATCH = 5
SCORE_BATCH_INTERVAL = 5.0
SIGNAL_INTERVAL = 5.0
TRADE_INTERVAL = 2.0

# Mock sentiment model (the real one needs ~600MB download + GPU/CPU minutes)
USE_MOCK_SENTIMENT = True

TAGS = ["AI", "LLM", "TSLA"]


# ── Synthetic price walk (geometric Brownian motion over engagement) ─

def engagement_walk(likes: int, retweets: int, followers: int, dt: float) -> tuple[int, int, int]:
    """Random walk on (likes, retweets, followers) — used to derive a
    synthetic unit price from tweet engagement."""
    new_likes = max(0, int(likes * math.exp(random.gauss(0, 0.05))))
    new_retweets = max(0, int(retweets * math.exp(random.gauss(0, 0.05))))
    new_followers = max(0, int(followers * math.exp(random.gauss(0, 0.001))))
    return new_likes, new_retweets, new_followers


def synthetic_unit_price(likes: int, retweets: int, followers: int) -> float:
    """Same formula as src/pipeline.py:_synthetic_price."""
    return max(1.0, float(likes) + 2.0 * float(retweets) + 0.1 * float(followers))


# ── Synthetic tweet generator ─────────────────────────────────────────

TWEET_TEMPLATES = {
    "AI": [
        ("New LLM is going to change everything", +0.7),
        ("AI safety research is finally getting funded", +0.6),
        ("Yet another AI hype cycle, ignore the noise", -0.3),
        ("Open-source models closing the gap fast", +0.5),
        ("AI bubble is bursting, layoffs accelerating", -0.6),
        ("GPU shortage continues, training costs ballooning", -0.4),
        ("Agentic workflows shipping in production now", +0.7),
    ],
    "LLM": [
        ("LLM eval scores are improving quarter over quarter", +0.5),
        ("Hallucination rates still unacceptably high", -0.6),
        ("Fine-tuning open models beats GPT-4 for our use case", +0.4),
        ("LLM API prices dropped 10x this year", +0.3),
        ("Context windows are getting absurdly long", +0.2),
    ],
    "TSLA": [
        ("TSLA delivery numbers missed expectations again", -0.6),
        ("FSD v13 is a huge step forward, finally usable", +0.7),
        ("TSLA valuation still disconnected from fundamentals", -0.4),
        ("Cybertruck production ramp is finally happening", +0.3),
        ("Margin compression continues, competition biting", -0.5),
    ],
}


def synth_tweet(tag: str, idx: int, spread_minutes: int = 90) -> dict:
    """Synthesize one tweet row for the given tag.

    `spread_minutes` spreads tweet timestamps back across that window so
    the sentiment_buckets aggregator has multiple populated buckets to
    z-score against.
    """
    text, score = random.choice(TWEET_TEMPLATES[tag])
    ts = datetime.now(UTC) - timedelta(minutes=random.uniform(0, spread_minutes))
    return {
        "ts": ts,
        "tweet_id": int(time.time() * 1_000_000) + idx,
        "symbol": tag,
        "text": text,
        "author": f"user_{random.randint(1000, 9999)}",
        "likes": random.randint(0, 500),
        "retweets": random.randint(0, 100),
        "followers": random.randint(50, 50_000),
        "url": f"https://x.com/synthetic/{tag}/{idx}",
        "source_adapter": "demo",
        "raw_json": None,
        "_true_sentiment": score,
    }


# ── Mock sentiment model (same interface as the real one) ────────────

class MockSentiment:
    """Stand-in for TwitterSentimentScorer — returns the score we stashed
    on the tweet."""

    def score(self, texts: list[str]) -> list[float]:
        return [getattr(self, "_next_score", 0.0)] * len(texts)


# ── Driver state ──────────────────────────────────────────────────────

class Demo:
    def __init__(self):
        # Per-tag synthetic "engagement state" — used to derive a unit
        # price for the paper broker.
        self.engagement: dict[str, tuple[int, int, int]] = {
            t: (random.randint(10, 100), random.randint(1, 10), random.randint(1000, 10000))
            for t in TAGS
        }
        self.history_prices: dict[str, list[tuple[datetime, float]]] = {t: [] for t in TAGS}
        self.scored_tweets: list[dict] = []
        self.signals_emitted: list[dict] = []
        self.fills: list[dict] = []

        # Real DB on SQLite
        db.override_engine("sqlite:///./demo.db")
        db.ensure_sqlite_schema()
        # Real broker
        self.broker = PaperBroker(starting_units=10_000.0)
        # Real scorer, mocked
        if USE_MOCK_SENTIMENT:
            self.scorer = MockSentiment()
        else:
            self.scorer = TwitterSentimentScorer(
                model_name=settings.sentiment_model,
                batch_size=settings.sentiment_batch_size,
            )

        self.tick_count = 0
        self.tweet_count = 0
        self._traded_signal_keys: set[tuple[str, str, str]] = set()

    def seed_history(self) -> None:
        """Backfill 90 min of engagement-derived price history + scored
        tweets so signal generation has a real history to z-score against
        (matches production behavior ~90 min after boot)."""
        now = datetime.now(UTC)
        rng = random.Random(7)
        # 90 min × 1 tick/min = 90 price rows per tag
        for tag in TAGS:
            for m in range(90, 0, -1):
                ts = (now - timedelta(minutes=m)).replace(microsecond=0)
                # Random engagement, derive price
                likes, retweets, followers = self.engagement[tag]
                likes += rng.randint(-5, 5)
                retweets += rng.randint(-1, 1)
                price = synthetic_unit_price(likes, retweets, followers)
                tick = {"ts": ts, "symbol": tag, "price": price}
                self.broker.on_price_tick(tick)
                self.history_prices[tag].append((ts, price))
        # ~3 scored tweets per 5-min bucket × 18 buckets × 3 tags = ~162 rows
        for tag in TAGS:
            for m in range(90, 0, -1):
                ts = (now - timedelta(minutes=m)).replace(microsecond=0)
                for k in range(3):
                    t = synth_tweet(tag, m * 100 + k, spread_minutes=0)
                    t["ts"] = ts - timedelta(seconds=k * 30)
                    row = {kk: v for kk, v in t.items() if not kk.startswith("_")}
                    if db.upsert_tweet(row):
                        self.tweet_count += 1
                    db.update_tweet_sentiment(t["tweet_id"], t["ts"], t["_true_sentiment"])
        logger.info(f"seeded history: {self.tick_count} ticks, {self.tweet_count} tweets")

    # ── Pipeline stage 1: synthetic engagement tick → broker ─────────

    def on_engagement_tick(self, tag: str, ts: datetime) -> None:
        likes, retweets, followers = engagement_walk(*self.engagement[tag], TICK_INTERVAL)
        self.engagement[tag] = (likes, retweets, followers)
        price = synthetic_unit_price(likes, retweets, followers)
        tick = {"ts": ts, "symbol": tag, "price": price}
        self.broker.on_price_tick(tick)
        self.history_prices[tag].append((ts, price))
        if len(self.history_prices[tag]) > 600:
            self.history_prices[tag].pop(0)
        self.tick_count += 1

    # ── Pipeline stage 2: synth tweets → DB → score ────────────────

    def scrape_and_score(self) -> int:
        new_rows = []
        for tag in TAGS:
            for i in range(TWEETS_PER_BATCH):
                t = synth_tweet(tag, i)
                inserted = db.upsert_tweet({k: v for k, v in t.items() if not k.startswith("_")})
                if inserted:
                    self.tweet_count += 1
                new_rows.append(t)
        # Score
        texts = [t["text"] for t in new_rows]
        if USE_MOCK_SENTIMENT:
            scores = [t["_true_sentiment"] for t in new_rows]
        else:
            scores = self.scorer.score(texts)
        for t, s in zip(new_rows, scores):
            db.update_tweet_sentiment(t["tweet_id"], t["ts"], float(s))
        return len(new_rows)

    # ── Pipeline stage 3: generate signal → DB → broker ─────────────

    def generate_signal_for(self, tag: str) -> str | None:
        # Aggregate sentiment history (5-min bucket means)
        buckets = db.sentiment_buckets(tag, minutes=5, hours=2)
        if len(buckets) < 3:
            return None
        sentiment_value = float(buckets[-1]["avg_sent"])
        sent_hist = [float(b["avg_sent"]) for b in buckets]

        sig = generate_signal(
            symbol=tag,
            sentiment_value=sentiment_value,
            sentiment_history=sent_hist,
        )
        db.insert_signal(sig.to_row())
        self.signals_emitted.append({
            "ts": sig.ts,
            "symbol": sig.symbol,
            "action": sig.action,
            "score": sig.score,
            "reason": sig.reason,
        })
        return sig.action

    def paper_trade_for(self, tag: str) -> None:
        last = db.fetch_recent_signals(tag, hours=2, limit=1)
        if not last:
            return
        sig_row = last[0]
        key = (str(sig_row["ts"]), tag, sig_row["action"])
        if key in self._traded_signal_keys:
            return
        sig = Signal(
            symbol=sig_row["symbol"],
            ts=sig_row["ts"],
            action=sig_row["action"],
            score=sig_row["score"],
            sentiment_zscore=sig_row["sentiment_zscore"],
            momentum_zscore=sig_row["momentum_zscore"],
            reason=sig_row["reason"],
        )
        # Use the latest engagement-derived unit price for this tag
        price = self.history_prices[tag][-1][1] if self.history_prices[tag] else 50.0
        fill = self.broker.on_signal(sig, float(price))
        if fill is None:
            return
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
        pos = self.broker.positions.get(tag)
        if pos is not None:
            db.upsert_position({
                "ts": fill.ts,
                "symbol": tag,
                "qty": pos.qty,
                "avg_price": pos.avg_price,
                "realized_pnl": pos.realized_pnl,
            })
        self.fills.append({
            "ts": fill.ts,
            "symbol": fill.symbol,
            "side": fill.side,
            "qty": fill.qty,
            "price": fill.price,
            "fee": fill.fee,
            "cash": fill.cash_after,
        })
        self._traded_signal_keys.add(key)

    # ── Live status table ──────────────────────────────────────────

    def render_status(self, elapsed: float) -> None:
        eq = self.broker.equity()
        m = self.broker.metrics()
        print("\n" + "─" * 78)
        print(f"  ⏱  t={elapsed:5.1f}s   ticks={self.tick_count:4d}   "
              f"tweets={self.tweet_count:4d}   signals={len(self.signals_emitted):3d}   "
              f"fills={len(self.fills):3d}")
        print(f"  💰  cash={self.broker.cash:>10,.2f}u   "
              f"equity={eq:>10,.2f}u   "
              f"realized PnL={m['pnl']:+,.2f}u   "
              f"win-rate={m['win_rate']:.0%}   "
              f"max DD={m['max_drawdown']:.2f}u")
        print(f"  📈  ", end="")
        for t in TAGS:
            likes, retweets, followers = self.engagement[t]
            p = synthetic_unit_price(likes, retweets, followers)
            n = len(self.history_prices[t])
            print(f"{t}={p:>6.2f}u ({n} ticks)  ", end="")
        print()
        if self.fills:
            print(f"  📋  Last fills:")
            for f in self.fills[-3:]:
                ts = f['ts']
                if isinstance(ts, str):
                    ts = ts[:19]  # trim 'YYYY-MM-DD HH:MM:SS' from a longer ISO string
                print(f"        {ts}  {f['side']}  "
                      f"{f['qty']:.6f} {f['symbol']} @ {f['price']:,.2f}u  "
                      f"cash={f['cash']:,.2f}u")
        if self.signals_emitted:
            print(f"  🎯  Last signals:")
            for s in self.signals_emitted[-3:]:
                ts = s['ts']
                if isinstance(ts, str):
                    ts = ts[:19]
                print(f"        {ts}  {s['action']:5s}  "
                      f"{s['symbol']:5s}  score={s['score']:+.2f}  {s['reason']}")


# ── Main loop ───────────────────────────────────────────────────────

async def run():
    demo = Demo()
    print("⏳ Seeding 90 minutes of engagement + tweet history…")
    demo.seed_history()
    start = time.monotonic()
    last_score = start
    last_signal = start
    last_trade = start
    last_render = start
    rng = random.Random(42)
    print(f"⏳ Running live demo for {DURATION_SEC}s…")
    print(f"   Tags: {TAGS}")
    print(f"   DB: sqlite:///./demo.db")
    print(f"   Scorer: {'MOCK (synthetic truth)' if USE_MOCK_SENTIMENT else settings.sentiment_model}")
    print()
    while time.monotonic() - start < DURATION_SEC:
        now = time.monotonic()
        ts = datetime.now(UTC).replace(microsecond=0)
        for t in TAGS:
            demo.on_engagement_tick(t, ts)
        if now - last_score >= SCORE_BATCH_INTERVAL:
            n = demo.scrape_and_score()
            logger.debug(f"scored {n} tweets")
            last_score = now
        if now - last_signal >= SIGNAL_INTERVAL:
            for t in TAGS:
                demo.generate_signal_for(t)
            last_signal = now
        if now - last_trade >= TRADE_INTERVAL:
            for t in TAGS:
                demo.paper_trade_for(t)
            last_trade = now
        if now - last_render >= 2.0:
            demo.render_status(time.monotonic() - start)
            last_render = now
        await asyncio.sleep(TICK_INTERVAL)
    demo.render_status(time.monotonic() - start)
    print("\n" + "─" * 78)
    print("  📊  Final database state (sqlite:///./demo.db)")
    print("─" * 78)
    with db.get_engine().connect() as conn:
        from sqlalchemy import text
        for table in ("tweets", "signals", "paper_trades", "positions", "trending_tags"):
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
            print(f"  {table:15s}  {count:5d} rows")
    import os
    try:
        os.remove("demo.db")
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    asyncio.run(run())
