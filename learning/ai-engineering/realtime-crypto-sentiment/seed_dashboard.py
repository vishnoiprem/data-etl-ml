"""Seed a fresh SQLite DB with realistic demo data for the dashboard.

Writes ~7 days of synthetic-but-plausible data for all 5 dashboard tabs:
  - tweets (with sentiment scores) for the Sentiment + Live pages
  - signals (BUY/SELL/HOLD mix) for the 24h signal-count bar
  - paper_trades + positions (a few round-trips) for the Paper PnL page
  - trending_tags (1-min buckets) for the 🔥 Trending page
  - 7 days of sparse per-tag tweet history so the Top-10 daily
    leaderboard has velocity / reach numbers to display
"""
from __future__ import annotations

import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Make the project importable when invoked as `python seed_dashboard.py`
PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))

from src.store import db

# ── Constants ───────────────────────────────────────────────────────────

DB_PATH = "sqlite:///./dashboard_demo.db"
NOW = datetime.now(UTC).replace(microsecond=0)
random.seed(42)

TAGS = ["AI", "LLM", "data engineering", "vector database", "TSLA", "NVDA",
        "dating", "girlf", "tiktok dating", "S&P 500", "nasdaq"]

TWEET_TEMPLATES = {
    "AI": [
        ("GPT-5 just dropped and it's a serious step up", +0.85),
        ("Open-source models are closing the gap fast", +0.7),
        ("AI bubble is bursting, layoffs accelerating", -0.6),
        ("Anthropic's interpretability work is genuinely impressive", +0.8),
        ("Hallucination rates in production are still embarrassing", -0.7),
        ("Fine-tuning a 7B model just worked on our hardest eval", +0.9),
    ],
    "LLM": [
        ("Long context windows are getting absurdly long", +0.3),
        ("LLM API prices dropped another 50% this quarter", +0.6),
        ("Eval contamination is a serious problem nobody talks about", -0.5),
        ("RAG is still the right default for most teams", +0.2),
        ("GPT-4 Turbo is showing its age", -0.4),
    ],
    "data engineering": [
        ("DuckDB is unreasonably good for ad-hoc analytics", +0.8),
        ("Spark 4 is finally a real release, not a holdover", +0.4),
        ("Data quality is the real bottleneck, not the pipeline", -0.2),
        ("Modern data stack consolidation is happening fast", +0.3),
        ("dbt + Snowflake is still the default for good reason", +0.5),
    ],
    "vector database": [
        ("pgvector crushed our specialized vector DB", +0.7),
        ("HNSW index builds are OOMing on 100M+ vectors", -0.6),
        ("Qdrant 1.10 has the best retrieval benchmarks", +0.8),
        ("Pinecone serverless is overpriced for our scale", -0.3),
    ],
    "TSLA": [
        ("FSD v13 is finally usable in dense urban traffic", +0.85),
        ("Cybertruck production ramp is finally hitting targets", +0.4),
        ("TSLA deliveries missed the whisper number badly", -0.7),
        ("Energy storage margins are the real story, not cars", +0.6),
        ("Margin compression continues, competition biting", -0.5),
    ],
    "NVDA": [
        ("Hopper demand still exceeds supply by a wide margin", +0.85),
        ("Blackwell ramp is real and it's faster than Hopper", +0.9),
        ("Custom silicon from hyperscalers is the real threat", -0.4),
        ("NVDA earnings call set the bar absurdly high again", +0.6),
    ],
    "dating": [
        ("Hinge is way better than Tinder if you're serious", +0.5),
        ("The dating app fatigue is real and I felt it tonight", -0.6),
        ("Met my girlfriend on Bumble, two years strong", +0.9),
        ("Burnout from dating apps is at an all-time high", -0.7),
        ("Slow dating trend is actually a good thing", +0.4),
    ],
    "girlf": [
        ("My girlfriend surprised me with the sweetest gift", +0.9),
        ("Long-distance with my girlf is brutal honestly", -0.5),
        ("Girlf and I just hit our 3-year anniversary", +0.85),
        ("Missing my girlfriend terribly tonight", -0.4),
    ],
    "tiktok dating": [
        ("TikTok dating trends are getting unhinged", -0.3),
        ("The 'soft launch' trend is so cute honestly", +0.6),
        ("TikTok couples content is at saturation point", -0.5),
        ("Dating trends from TikTok: hit or miss honestly", +0.1),
    ],
    "S&P 500": [
        ("S&P 500 just hit another all-time high, irrational exuberance", +0.4),
        ("Concentration risk in S&P 500 is genuinely concerning", -0.6),
        ("Earnings season has been broadly better than feared", +0.7),
    ],
    "nasdaq": [
        ("Nasdaq leading the rally, tech still has the bid", +0.6),
        ("Nasdaq breadth is actually better than the index suggests", +0.5),
        ("Mag 7 can't carry the entire Nasdaq forever", -0.3),
    ],
}


def _synthetic_price(likes: int, retweets: int, followers: int) -> float:
    return max(1.0, float(likes) + 2.0 * float(retweets) + 0.1 * float(followers))


# ── Seed tweets (6h, ~5 per tag every 5 min) ──────────────────────────

def seed_tweets() -> int:
    """Backfill ~7 days of synthetic tweets so the daily-aggregate panels
    on the Live tab have multiple days to plot. Two regimes:

    - Last 6 hours: dense, one tweet per tag per 5 min (powers the
      hourly sentiment timeline).
    - Days 1-7: sparser, one tweet per tag every 30 min, with per-day
      velocity drift so "trending up" / "trending down" looks real on
      the Top-10 panel.
    """
    n = 0
    # ── Last 6 hours, dense (5-min resolution) ─────────────────────
    for minutes_ago in range(360, -1, -5):
        ts = NOW - timedelta(minutes=minutes_ago)
        for tag in TAGS:
            templates = TWEET_TEMPLATES.get(tag, [("x", 0.0)])
            text, score = random.choice(templates)
            db.upsert_tweet({
                "ts": ts,
                "tweet_id": int(ts.timestamp() * 1_000_000) + hash(tag) % 1000,
                "symbol": tag,
                "text": text,
                "author": f"user_{random.randint(100, 9999)}",
                "likes": random.randint(0, 800),
                "retweets": random.randint(0, 200),
                "followers": random.randint(100, 50_000),
                "url": f"https://x.com/synthetic/{tag}/{int(ts.timestamp())}",
                "source_adapter": "nitter",
                "sentiment_score": score + random.uniform(-0.1, 0.1),
            })
            n += 1

    # ── Days 1-7, sparse (30-min resolution) with per-day velocity ──
    # Each tag gets a "heat" factor that ramps up or down across the
    # 7 days, so the stacked-bar and velocity leaderboards look organic.
    heat_factor: dict[str, float] = {t: random.uniform(0.4, 1.6) for t in TAGS}
    for days_ago in range(1, 8):
        # Tags heat up / cool down across the week
        for tag in TAGS:
            drift = 1.0 + 0.15 * (7 - days_ago) * (heat_factor[tag] - 1.0)
            drift = max(0.3, min(2.5, drift))
            base_n = int(48 * drift)  # 48 = 24h * 2 (one per 30 min)
            for i in range(base_n):
                ts = NOW - timedelta(days=days_ago, minutes=30 * i)
                templates = TWEET_TEMPLATES.get(tag, [("x", 0.0)])
                text, score = random.choice(templates)
                db.upsert_tweet({
                    "ts": ts,
                    "tweet_id": int(ts.timestamp() * 1_000_000) + (hash(tag) + days_ago * 7919) % 999999,
                    "symbol": tag,
                    "text": text,
                    "author": f"user_{random.randint(100, 9999)}",
                    "likes": random.randint(0, 800),
                    "retweets": random.randint(0, 200),
                    "followers": random.randint(100, 50_000),
                    "url": f"https://x.com/synthetic/{tag}/{int(ts.timestamp())}",
                    "source_adapter": "nitter",
                    "sentiment_score": score + random.uniform(-0.1, 0.1),
                })
                n += 1
    return n


# ── Seed signals (1 per tag every 15 min) ────────────────────────────

def seed_signals() -> int:
    n = 0
    # Dense signals for last 6h
    for minutes_ago in range(360, -1, -15):
        ts = NOW - timedelta(minutes=minutes_ago)
        for tag in TAGS:
            sent_z = random.gauss(0, 1.2)
            if sent_z > 1.0:
                action = "BUY"
            elif sent_z < -1.0:
                action = "SELL"
            else:
                action = "HOLD"
            db.insert_signal({
                "ts": ts,
                "symbol": tag,
                "action": action,
                "score": sent_z,
                "sentiment_zscore": sent_z,
                "momentum_zscore": 0.0,
                "reason": f"5-min sentiment {sent_z:+.2f}σ → score {sent_z:+.2f}",
            })
            n += 1
    return n


# ── Seed paper trades + positions (a few round-trips) ────────────────

def seed_paper_trades() -> int:
    """3 round-trips + 1 open position. Realized PnL mix (wins + losses)."""
    n = 0
    # Round 1: BUY @ 50, SELL @ 53 (win) for AI
    for i, (sym, buy, sell) in enumerate([
        ("AI", 50.0, 53.0),
        ("TSLA", 100.0, 96.0),
        ("LLM", 30.0, 35.0),
    ]):
        ts_buy = NOW - timedelta(hours=4) + timedelta(minutes=i * 30)
        # qty = (5% of 10k) / price
        qty = (10_000.0 * 0.05) / buy
        cash_after_buy = 10_000.0 - qty * buy * 1.001
        db.insert_paper_trade({
            "ts": ts_buy, "symbol": sym, "side": "BUY",
            "qty": qty, "price": buy, "fee": qty * buy * 0.001,
            "cash_after": cash_after_buy, "reason": f"z=+1.{i+1}",
        })
        n += 1
        # position snapshot after BUY
        db.upsert_position({
            "ts": ts_buy, "symbol": sym, "qty": qty, "avg_price": buy,
            "realized_pnl": 0.0,
        })
        # SELL 1 min later
        ts_sell = ts_buy + timedelta(minutes=1)
        proceeds = qty * sell
        sell_fee = proceeds * 0.001
        cash_after_sell = cash_after_buy + proceeds - sell_fee
        realized = (sell - buy) * qty - sell_fee
        db.insert_paper_trade({
            "ts": ts_sell, "symbol": sym, "side": "SELL",
            "qty": qty, "price": sell, "fee": sell_fee,
            "cash_after": cash_after_sell, "reason": f"z=-1.{i+1}",
        })
        n += 1
        db.upsert_position({
            "ts": ts_sell, "symbol": sym, "qty": 0.0, "avg_price": 0.0,
            "realized_pnl": realized,
        })
    # Open position in NVDA (BUY only, no SELL yet)
    ts_buy = NOW - timedelta(hours=1)
    qty = (10_000.0 * 0.05) / 200.0
    db.insert_paper_trade({
        "ts": ts_buy, "symbol": "NVDA", "side": "BUY",
        "qty": qty, "price": 200.0, "fee": qty * 200.0 * 0.001,
        "cash_after": 10_000.0 - qty * 200.0 * 1.001, "reason": "z=+1.5",
    })
    n += 1
    db.upsert_position({
        "ts": ts_buy, "symbol": "NVDA", "qty": qty, "avg_price": 200.0,
        "realized_pnl": 0.0,
    })
    return n


# ── Seed trending tags (1-min buckets for the last 30 min) ───────────

def seed_trending() -> int:
    n = 0
    tag_universe = [
        ("$NVDA", "cashtag", 25), ("$TSLA", "cashtag", 18), ("$AAPL", "cashtag", 14),
        ("#AI", "hashtag", 40), ("#LLM", "hashtag", 22), ("#dating", "hashtag", 15),
        ("#girlf", "hashtag", 8), ("#tiktokdating", "hashtag", 11),
        ("#datascience", "hashtag", 12), ("#OpenAI", "hashtag", 19),
        ("artificial intelligence", "keyword", 28),
        ("earnings", "keyword", 17), ("rate cut", "keyword", 9),
        ("tinder", "keyword", 6), ("hinge", "keyword", 4),
    ]
    for minutes_ago in range(30, -1, -1):
        ts = NOW - timedelta(minutes=minutes_ago)
        bucket = ts.replace(second=0, microsecond=0)
        for tag, kind, base_count in tag_universe:
            count = max(0, int(base_count / 30 * random.uniform(0.5, 1.5)))
            if count == 0:
                continue
            sentiment = random.uniform(-0.5, 0.8) if kind != "cashtag" else random.uniform(-0.3, 0.7)
            db.upsert_trending_tag({
                "ts": ts,
                "bucket": bucket,
                "tag": tag,
                "tag_kind": kind,
                "count": count,
                "avg_sentiment": sentiment,
                "sample_text": f"Sample tweet mentioning {tag}",
                "sample_url": f"https://x.com/sample/{tag}/{int(ts.timestamp())}",
            })
            n += 1
    return n


# ── Main ──────────────────────────────────────────────────────────────

def main() -> int:
    db.override_engine(DB_PATH)
    db.ensure_sqlite_schema()
    print(f"Seeding {DB_PATH}…")
    n_tweets = seed_tweets()
    n_signals = seed_signals()
    n_trades = seed_paper_trades()
    n_trending = seed_trending()
    print(f"  tweets:      {n_tweets}")
    print(f"  signals:     {n_signals}")
    print(f"  paper_trades: {n_trades}")
    print(f"  trending:    {n_trending}")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
