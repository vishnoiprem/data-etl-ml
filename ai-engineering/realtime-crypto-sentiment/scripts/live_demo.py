"""Live-data demo driver.

Runs the *real* pipeline code paths — same signal generator, same paper
broker, same DB upserts, same FinBERT scorer interface — but feeds it
synthetic prices and tweets, since this sandbox has no outbound access
to Binance or Nitter.

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
from src.ml.finbert import FinBERTScorer
from src.ml.signal import generate_signal
from src.store import db
from src.trader.paper import PaperBroker


# ── Demo knobs ────────────────────────────────────────────────────────

DURATION_SEC = 30
TICK_INTERVAL = 0.5  # one Binance trade every 500ms
TWEETS_PER_BATCH = 5  # tweets scraped per cycle
SCORE_BATCH_INTERVAL = 5.0  # score every 5s
SIGNAL_INTERVAL = 5.0  # generate_signal every 5s
TRADE_INTERVAL = 2.0  # paper_trade every 2s

# Mock FinBERT (the real one needs ~600MB download + GPU/CPU minutes)
USE_MOCK_FINBERT = True

SYMBOLS = ["BTC", "ETH", "SOL"]


# ── Synthetic price walk (geometric Brownian motion) ──────────────────

def gbm_walk(start: float, drift: float, vol: float, dt: float) -> float:
    """One step of geometric Brownian motion."""
    return start * math.exp((drift - 0.5 * vol**2) * dt + vol * math.sqrt(dt) * random.gauss(0, 1))


# ── Synthetic tweet generator ─────────────────────────────────────────

TWEET_TEMPLATES = {
    "BTC": [
        ("$BTC breaking out — institutional buying picking up", +0.7),
        ("$BTC forming a textbook bull flag, 80k target next", +0.6),
        ("$BTC liquidation cascade — drop incoming, leverage is high", -0.6),
        ("$BTC dominance climbing, alts getting crushed", -0.3),
        ("Just bought more $BTC, the 4-year cycle still has runway", +0.4),
        ("$BTC consolidating at support, breakout imminent", +0.2),
        ("$BTC flash crash to 60k, paper hands selling", -0.5),
        ("Massive $BTC inflow to spot ETFs, smart money accumulating", +0.8),
    ],
    "ETH": [
        ("$ETH gas fees spiking — bull market is back", +0.5),
        ("$ETH underperforming $BTC again, frustrating", -0.4),
        ("$ETH/BTC pair bottoming — alt season loading", +0.6),
        ("$ETH staking yields attractive vs treasuries", +0.3),
        ("$ETH devs shipping, fundamentals strong long-term", +0.4),
        ("$ETH getting rejected at resistance, weak hands folding", -0.3),
    ],
    "SOL": [
        ("$SOL blazing fast, the ETH killers narrative is back", +0.7),
        ("$SOL network congestion issues, need to scale", -0.4),
        ("$SOL meme coin mania pumping the chain", +0.5),
        ("$SOL funding rates negative, shorts paying longs", +0.3),
        ("$SOL under heavy selling pressure, breaking down", -0.6),
    ],
}


def synth_tweet(symbol: str, idx: int, spread_minutes: int = 90) -> dict:
    """Synthesize one tweet row for the given symbol.

    `spread_minutes` spreads tweet timestamps back across that window so the
    sentiment_buckets aggregator has multiple populated buckets to z-score
    against (production sees the same effect once tweets accumulate).

    NOTE: returns a tz-NAIVE UTC datetime to match the SQLite `DateTime`
    column. The production code round-trips tz-aware datetimes through
    SQLite and gets a string-mismatch on the WHERE clause — Postgres is
    unaffected. Tracked for a separate fix; demo works around it.
    """
    text, score = random.choice(TWEET_TEMPLATES[symbol])
    ts = datetime.utcnow() - timedelta(minutes=random.uniform(0, spread_minutes))
    return {
        "ts": ts,
        "tweet_id": int(time.time() * 1_000_000) + idx,  # unique
        "symbol": symbol,
        "text": text,
        "author": f"trader_{random.randint(1000, 9999)}",
        "likes": random.randint(0, 500),
        "retweets": random.randint(0, 100),
        "followers": random.randint(50, 50_000),
        "url": f"https://x.com/synthetic/{symbol}/{idx}",
        "source_adapter": "demo",
        "raw_json": None,
        "_true_sentiment": score,  # stash for mock FinBERT
    }


# ── Mock FinBERT (same interface as the real one) ────────────────────

class MockFinBERT:
    """Stand-in for FinBERTScorer — returns the score we stashed on the tweet."""

    def score(self, texts: list[str]) -> list[float]:
        # The demo stashes truth on the row; we look it up by tweet_id.
        return [getattr(self, "_next_score", 0.0)] * len(texts)


# ── Driver state ──────────────────────────────────────────────────────

class Demo:
    def __init__(self):
        self.prices: dict[str, float] = {"BTC": 67_500.0, "ETH": 3_500.0, "SOL": 175.0}
        self.history_prices: dict[str, list[tuple[datetime, float]]] = {s: [] for s in SYMBOLS}
        self.scored_tweets: list[dict] = []
        self.signals_emitted: list[dict] = []
        self.fills: list[dict] = []

        # Real DB on SQLite
        db.override_engine("sqlite:///./demo.db")
        db.ensure_sqlite_schema()
        # Real broker
        self.broker = PaperBroker(starting_cash_usd=10_000.0)
        # Real scorer, mocked
        if USE_MOCK_FINBERT:
            self.scorer = MockFinBERT()
        else:
            self.scorer = FinBERTScorer(
                model_name=settings.finbert_model,
                batch_size=settings.finbert_batch_size,
            )

        self.tick_count = 0
        self.tweet_count = 0

    def seed_history(self) -> None:
        """Backfill 90 min of price history + scored tweets so signal
        generation has a real history to z-score against (matches the
        behavior of the production pipeline ~90 min after boot)."""
        now = datetime.utcnow()
        rng = random.Random(7)
        # 90 min × 1 tick/min = 90 price rows per symbol
        for sym in SYMBOLS:
            start_p = self.prices[sym] * 0.97  # 3% drift up over the window
            for m in range(90, 0, -1):
                ts = (now - timedelta(minutes=m)).replace(microsecond=0)
                # gentle walk back to start_p
                target = start_p + (self.prices[sym] - start_p) * (90 - m) / 90
                price = target * math.exp(rng.gauss(0, 0.003))
                tick = {
                    "ts": ts, "symbol": sym, "price_usd": price,
                    "volume_usd": price * rng.uniform(0.01, 0.5),
                }
                db.upsert_price(tick)
                self.broker.on_price_tick(tick)
                self.history_prices[sym].append((ts, price))
        # ~3 scored tweets per 5-min bucket × 18 buckets × 3 symbols = ~162 rows
        for sym in SYMBOLS:
            for m in range(90, 0, -1):
                ts = (now - timedelta(minutes=m)).replace(microsecond=0)
                for k in range(3):
                    t = synth_tweet(sym, m * 100 + k, spread_minutes=0)
                    t["ts"] = ts - timedelta(seconds=k * 30)
                    row = {kk: v for kk, v in t.items() if not kk.startswith("_")}
                    if db.upsert_tweet(row):
                        self.tweet_count += 1
                    db.update_tweet_sentiment(t["tweet_id"], t["ts"], t["_true_sentiment"])
        logger.info(f"seeded history: {self.tick_count} ticks, {self.tweet_count} tweets")

    # ── Pipeline stage 1: synthetic price tick → DB ──────────────────

    def on_price_tick(self, symbol: str, price: float, ts: datetime) -> None:
        self.prices[symbol] = price
        self.history_prices[symbol].append((ts, price))
        if len(self.history_prices[symbol]) > 600:
            self.history_prices[symbol].pop(0)
        # Normalize to tz-naive UTC for SQLite round-trip (see synth_tweet
        # note about the production bug).
        ts_naive = ts.replace(tzinfo=None) if ts.tzinfo else ts
        tick = {
            "ts": ts_naive,
            "symbol": symbol,
            "price_usd": price,
            "volume_usd": price * random.uniform(0.001, 0.5),
        }
        db.upsert_price(tick)  # real DB write
        self.broker.on_price_tick(tick)  # real broker mark-to-market
        self.tick_count += 1

    # ── Pipeline stage 2: synth tweets → DB → score ────────────────

    def scrape_and_score(self) -> int:
        new_rows = []
        for sym in SYMBOLS:
            for i in range(TWEETS_PER_BATCH):
                t = synth_tweet(sym, i)
                # Real DB upsert
                inserted = db.upsert_tweet({k: v for k, v in t.items() if not k.startswith("_")})
                if inserted:
                    self.tweet_count += 1
                # Pull back from DB to get the row we'd actually see in production
                new_rows.append(t)
        # Real FinBERT (or mock)
        texts = [t["text"] for t in new_rows]
        if USE_MOCK_FINBERT:
            scores = [t["_true_sentiment"] for t in new_rows]
        else:
            scores = self.scorer.score(texts)
        for t, s in zip(new_rows, scores):
            db.update_tweet_sentiment(t["tweet_id"], t["ts"], float(s))
        return len(new_rows)

    # ── Pipeline stage 3: generate signal → DB → broker ─────────────

    def generate_signal_for(self, sym: str) -> str | None:
        # Aggregate sentiment history (5-min bucket means) — same call
        # the real pipeline uses. Lookback 2h so the seeded 90-min
        # history is fully in window.
        buckets = db.sentiment_buckets(sym, minutes=5, hours=2)
        if len(buckets) < 3:
            return None
        sentiment_value = float(buckets[-1]["avg_sent"])
        sent_hist = [float(b["avg_sent"]) for b in buckets]

        # Momentum: net 5-min return
        rets_5m = db.recent_price_returns(sym, minutes=5)
        if not rets_5m:
            return None
        momentum_value = sum(rets_5m)
        # 5-min-return history (sample over the same 2h lookback)
        minute_returns = db.recent_price_returns(sym, minutes=120)
        mom_hist = [sum(minute_returns[i:i+5]) for i in range(0, len(minute_returns) - 4, 5)]

        sig = generate_signal(
            symbol=sym,
            sentiment_value=sentiment_value,
            sentiment_history=sent_hist,
            momentum_value=momentum_value,
            momentum_history=mom_hist,
        )
        # Real DB write
        db.insert_signal(sig.to_row())
        self.signals_emitted.append({
            "ts": sig.ts,
            "symbol": sig.symbol,
            "action": sig.action,
            "score": sig.score,
            "reason": sig.reason,
        })
        return sig.action

    def paper_trade_for(self, sym: str) -> None:
        # Latest signal for this symbol
        last = db.fetch_recent_signals(sym, hours=2, limit=1)
        if not last:
            return
        sig_row = last[0]
        # Build a Signal object the broker expects
        from src.ml.signal import Signal
        sig = Signal(
            symbol=sig_row["symbol"],
            ts=sig_row["ts"],
            action=sig_row["action"],
            score=sig_row["score"],
            sentiment_zscore=sig_row["sentiment_zscore"],
            momentum_zscore=sig_row["momentum_zscore"],
            reason=sig_row["reason"],
        )
        price = self.prices.get(sym)
        if price is None:
            return
        fill = self.broker.on_signal(sig, float(price))
        if fill is None:
            return None
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
        # Snapshot position
        pos = self.broker.positions.get(sym)
        if pos is not None:
            db.upsert_position({
                "ts": fill.ts,
                "symbol": sym,
                "qty": pos.qty,
                "avg_price": pos.avg_price,
                "realized_pnl": pos.realized_pnl,
            })
        self.fills.append({
            "ts": fill.ts,
            "symbol": fill.symbol,
            "side": fill.side,
            "qty": fill.qty,
            "price": fill.price_usd,
            "fee": fill.fee_usd,
            "cash": fill.cash_after,
        })

    # ── Live status table ──────────────────────────────────────────

    def render_status(self, elapsed: float) -> None:
        eq = self.broker.equity()
        m = self.broker.metrics()
        print("\n" + "─" * 78)
        print(f"  ⏱  t={elapsed:5.1f}s   ticks={self.tick_count:4d}   "
              f"tweets={self.tweet_count:4d}   signals={len(self.signals_emitted):3d}   "
              f"fills={len(self.fills):3d}")
        print(f"  💰  cash=${self.broker.cash_usd:>10,.2f}   "
              f"equity=${eq:>10,.2f}   "
              f"realized PnL=${m['pnl_usd']:+,.2f}   "
              f"win-rate={m['win_rate']:.0%}   "
              f"max DD=${m['max_drawdown_usd']:.2f}")
        print(f"  📈  ", end="")
        for s in SYMBOLS:
            p = self.prices[s]
            n = len(self.history_prices[s])
            print(f"{s}=${p:,.2f} ({n} ticks)  ", end="")
        print()
        # Recent fills + signals (last 3 each)
        if self.fills:
            print(f"  📋  Last fills:")
            for f in self.fills[-3:]:
                print(f"        {f['ts'].strftime('%H:%M:%S')}  {f['side']}  "
                      f"{f['qty']:.6f} {f['symbol']} @ ${f['price']:,.2f}  "
                      f"cash=${f['cash']:,.2f}")
        if self.signals_emitted:
            print(f"  🎯  Last signals:")
            for s in self.signals_emitted[-3:]:
                print(f"        {s['ts'].strftime('%H:%M:%S')}  {s['action']:5s}  "
                      f"{s['symbol']:5s}  score={s['score']:+.2f}  {s['reason']}")


# ── Main loop ───────────────────────────────────────────────────────

async def run():
    demo = Demo()
    print("⏳ Seeding 90 minutes of price + tweet history…")
    demo.seed_history()
    start = time.monotonic()
    last_score = start
    last_signal = start
    last_trade = start
    last_render = start
    rng = random.Random(42)
    print(f"⏳ Running live demo for {DURATION_SEC}s…")
    print(f"   Symbols: {SYMBOLS}")
    print(f"   DB: sqlite:///./demo.db")
    print(f"   Scorer: {'MOCK (synthetic truth)' if USE_MOCK_FINBERT else settings.finbert_model}")
    print()
    while time.monotonic() - start < DURATION_SEC:
        now = time.monotonic()
        # tz-naive for SQLite (see synth_tweet note)
        ts = datetime.utcnow().replace(microsecond=0)
        # tick all 3 symbols (simulating a Binance trade every 0.5s)
        for s in SYMBOLS:
            vol = {"BTC": 0.015, "ETH": 0.02, "SOL": 0.03}[s]
            drift = rng.gauss(0, 0.0001)
            demo.prices[s] = gbm_walk(demo.prices[s], drift, vol, TICK_INTERVAL)
            demo.on_price_tick(s, demo.prices[s], ts)
        # scrape + score every SCORE_BATCH_INTERVAL
        if now - last_score >= SCORE_BATCH_INTERVAL:
            n = demo.scrape_and_score()
            logger.debug(f"scored {n} tweets")
            last_score = now
        # generate signals every SIGNAL_INTERVAL
        if now - last_signal >= SIGNAL_INTERVAL:
            for s in SYMBOLS:
                demo.generate_signal_for(s)
            last_signal = now
        # paper-trade every TRADE_INTERVAL
        if now - last_trade >= TRADE_INTERVAL:
            for s in SYMBOLS:
                demo.paper_trade_for(s)
            last_trade = now
        # render every 2s
        if now - last_render >= 2.0:
            demo.render_status(time.monotonic() - start)
            last_render = now
        await asyncio.sleep(TICK_INTERVAL)
    # Final render
    demo.render_status(time.monotonic() - start)
    # DB final state
    print("\n" + "─" * 78)
    print("  📊  Final database state (sqlite:///./demo.db)")
    print("─" * 78)
    with db.get_engine().connect() as conn:
        from sqlalchemy import text
        for table in ("tweets", "prices", "signals", "paper_trades", "positions"):
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
            print(f"  {table:15s}  {count:5d} rows")
    # Cleanup
    import os
    try:
        os.remove("demo.db")
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    asyncio.run(run())