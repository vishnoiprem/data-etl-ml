"""One-shot live scrape: hit a real Nitter mirror, score with a fast
lexicon-based sentiment, write to SQLite, and print the dashboard.

Why a lexicon (not the 600MB cardiffnlp model)?
- Cold-start is instant. No 500MB download, no GPU.
- It's "good enough" for a trend monitor: the 🔥 Trending page groups
  by mention count + avg sentiment, so a ±0.3 noise floor on the
  sentiment score is fine for ranking.
- The cardiffnlp model is still the default in src.config.settings;
  this script just overrides it for the demo.

What it does:
1. Scrapes Nitter for each TRACKED_TAGS tag.
2. Runs a lexicon-based sentiment scorer on the tweet text.
3. Writes tweets + per-tag 5-min bucketed sentiment to live.db.
4. Extracts cashtags/hashtags/keywords and writes trending_tags rows.
5. Prints a text-mode rendering of all 4 dashboard tabs.
"""
from __future__ import annotations

import asyncio
import os
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))

# Load .env BEFORE importing settings
from dotenv import load_dotenv  # noqa: E402
load_dotenv(PROJECT / ".env")

from loguru import logger  # noqa: E402

from src.config import settings  # noqa: E402
from src.sources.nitter_mirror import NitterMirrorAdapter  # noqa: E402
from src.sources.trending import aggregate_tags, extract_tags_from_tweet  # noqa: E402
from src.store import db  # noqa: E402

# ── Lexicon-based sentiment (fast, no model download) ─────────────────

POSITIVE_WORDS = {
    "bullish", "moon", "pump", "rally", "surge", "soar", "breakout", "win",
    "winning", "strong", "stronger", "best", "better", "amazing", "great",
    "excellent", "love", "loved", "loves", "perfect", "incredible", "epic",
    "fire", "killer", "rocket", "🚀", "gem", "buy", "accumulate", "accumulating",
    "ath", "high", "higher", "gain", "gains", "growth", "growing", "beat",
    "beats", "outperform", "outperforms", "positive", "upgrade", "upgraded",
    "smash", "smashes", "smart", "innovative", "ship", "shipping", "launch",
    "launches", "launched", "wow", "fast", "faster", "easy", "winning",
    "revolutionary", "breakthrough", "huge", "massive", "goated", "best",
}
NEGATIVE_WORDS = {
    "bearish", "crash", "dump", "sell", "sold", "selling", "weak", "worst",
    "terrible", "bad", "awful", "horrible", "hate", "hated", "garbage",
    "trash", "scam", "rug", "rugged", "rugpull", "down", "lower", "low",
    "loss", "losses", "lose", "loses", "losing", "miss", "missed", "misses",
    "missed", "negative", "downgrade", "downgraded", "fear", "panic", "fud",
    "dump", "rekt", "rip", "dead", "dying", "fraud", "fraudulent", "broken",
    "sucks", "broken", "failing", "fail", "failed", "fails", "wrong", "hurt",
    "down", "slump", "slumping", "drop", "drops", "dropping", "tank", "tanks",
    "tanking", "tanked", "concern", "concerns", "concerning", "worried",
    "warning", "warns", "warned", "risk", "risky", "danger", "dangerous",
}


def lexicon_score(text: str) -> float:
    """Return a sentiment score in [-1, +1] for a tweet's text."""
    words = re.findall(r"[a-z']+", text.lower())
    if not words:
        return 0.0
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    raw = (pos - neg) / max(1, len(words) ** 0.5)
    # Squash into [-1, +1]
    if raw > 0:
        return min(1.0, raw)
    return max(-1.0, raw)


# ── Scrape one tag from Nitter ─────────────────────────────────────────

async def scrape_tag(source: NitterMirrorAdapter, tag: str) -> list[dict]:
    """Returns list of {ts, text, author, likes, retweets, url, tweet_id}."""
    try:
        tweets = await source.fetch(tag, max_results=20)
        return [
            {
                "ts": t.ts,
                "text": t.text,
                "author": t.author,
                "likes": t.likes,
                "retweets": t.retweets,
                "url": t.url,
                "tweet_id": t.id,
            }
            for t in tweets
        ]
    except Exception as e:
        logger.warning(f"scrape {tag!r} failed: {e}")
        return []


# ── Main ───────────────────────────────────────────────────────────────

async def main() -> int:
    db.override_engine(settings.database_url)
    db.ensure_sqlite_schema()
    db.init_schema()

    # Make sure we don't accidentally trigger a 500MB model download.
    settings.sentiment_model = "lexicon-fast"  # not used; we use lexicon_score()

    source = NitterMirrorAdapter(
        mirrors=settings.mirrors,
        user_agent=settings.user_agent,
    )
    if not source.is_healthy():
        logger.error("no healthy Nitter mirror — abort")
        return 1

    # 1) Scrape each tracked tag
    all_tweets: list[dict] = []
    per_tag_counts: dict[str, int] = {}
    for tag in settings.tracked_tags:
        tweets = await scrape_tag(source, tag)
        per_tag_counts[tag] = len(tweets)
        for t in tweets:
            t["tag"] = tag
            t["sentiment_score"] = lexicon_score(t["text"])
        all_tweets.extend(tweets)
        logger.info(f"  scraped {tag!r:20s} → {len(tweets)} tweets")
        await asyncio.sleep(1.0)  # politeness: 1 req/sec per mirror

    await source.close()

    # 2) Insert into tweets table
    for t in all_tweets:
        db.upsert_tweet({
            "ts": t["ts"],
            "tweet_id": t["tweet_id"],
            "symbol": t["tag"],
            "text": t["text"],
            "author": t["author"],
            "likes": t["likes"],
            "retweets": t["retweets"],
            "followers": 0,
            "url": t["url"],
            "source_adapter": "nitter",
            "sentiment_score": t["sentiment_score"],
        })

    # 3) Generate signals (sentiment-only)
    for tag in settings.tracked_tags:
        buckets = db.sentiment_buckets(tag, minutes=5, hours=2)
        if len(buckets) < 2:
            continue
        from src.ml.signal import generate_signal
        sent_value = float(buckets[-1]["avg_sent"])
        sent_hist = [float(b["avg_sent"]) for b in buckets]
        sig = generate_signal(symbol=tag, sentiment_value=sent_value,
                              sentiment_history=sent_hist, threshold=settings.signal_threshold)
        db.insert_signal(sig.to_row())

    # 4) Trending tags: extract cashtags/hashtags/keywords from scraped
    #    tweets and write 1-min bucketed counts to trending_tags.
    from src.sources.trending import TagHit
    tag_hits: list[TagHit] = []
    for t in all_tweets:
        # Build a minimal "tweet" object for extract_tags_from_tweet
        class _T:
            pass
        obj = _T()
        obj.text = t["text"]
        obj.symbol_tags = [t["tag"]]
        obj.ts = t["ts"]
        for hit in extract_tags_from_tweet(obj, kind=None):
            tag_hits.append(hit)
    # Aggregate
    if tag_hits:
        aggregated = aggregate_tags(tag_hits)
        now = datetime.now(UTC).replace(second=0, microsecond=0)
        for row in aggregated:
            db.upsert_trending_tag({
                "ts": now,
                "bucket": now,
                "tag": row.tag,
                "tag_kind": row.tag_kind,
                "count": row.count,
                "avg_sentiment": row.avg_sentiment,
                "sample_text": row.sample_text,
                "sample_url": row.sample_url,
            })

    # 5) Print a text-mode dashboard
    print_dashboard(per_tag_counts, len(all_tweets))
    return 0


def print_dashboard(per_tag_counts: dict[str, int], total_tweets: int) -> None:
    import streamlit as st
    st.cache_data.clear()
    from dashboard import app

    def banner(title: str, emoji: str) -> None:
        print()
        print("=" * 78)
        print(f"  {emoji}  {title}")
        print("=" * 78)

    banner("LIVE DASHBOARD", "📡")
    print(f"  Scrape time:    {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  DB:             {settings.database_url}")
    print(f"  Tags scraped:   {len(per_tag_counts)}")
    print(f"  Tweets fetched: {total_tweets}")
    print(f"  Source:         Nitter (real)")

    banner("TAB 1 — OVERVIEW (KPIs)", "📊")
    k = app._kpis()
    print(f"  Cash (units):            {k['cash']:>12,.2f}")
    print(f"  Position value (units):  {k['position_value']:>12,.2f}")
    print(f"  Equity (units):          {k['equity']:>12,.2f}")
    print(f"  Realized PnL (units):    {k['realized_pnl']:>+12,.2f}")
    print(f"  Trades total / today:    {k['trade_count']:>6d} / {k['today_trades']}")
    print()
    open_pos = db.all_open_positions()
    if open_pos:
        print("  Open positions:")
        for p in open_pos:
            mkt = p["qty"] * p["avg_price"]
            print(f"    {p['symbol']:8s}  qty={p['qty']:>8.4f}  avg={p['avg_price']:>7.2f}u  "
                  f"mkt_val={mkt:>8.2f}u")
    else:
        print("  Open positions: (none — no BUY signals fired yet)")
    print()
    print("  24h signal mix:")
    sc = app._signal_counts()
    if not sc.empty:
        max_n = sc["n"].max()
        for _, row in sc.iterrows():
            bar = "█" * int(row["n"] / max_n * 40)
            print(f"    {row['action']:5s} {row['n']:4d}  {bar}")

    banner("TAB 2 — SENTIMENT (last 60 min, by tag)", "💬")
    avg = app._sentiment_per_symbol(minutes=60)
    if avg.empty:
        print("  (no scored tweets yet)")
    else:
        avg = avg.sort_values("avg_sent", ascending=False)
        for _, r in avg.iterrows():
            sign = "+" if r["avg_sent"] >= 0 else "-"
            bar = sign * int(abs(r["avg_sent"]) * 30)
            print(f"    {r['symbol']:20s} {r['avg_sent']:+.3f}  n={r['n']:3d}  {bar}")
    print()
    print("  Tweet volume by tag (last 1h):")
    tm = app._top_mentions(limit=15)
    if not tm.empty:
        max_m = tm["mentions"].max()
        for _, r in tm.iterrows():
            bar = "▮" * int(r["mentions"] / max_m * 30)
            print(f"    {r['symbol']:20s} {r['mentions']:>4d}  {bar}")

    banner("TAB 4 — 🔥 TRENDING TAGS (last 5 min)", "🔥")
    df = app._trending_tags(minutes=5, limit=15)
    if df.empty:
        print("  (no trending data yet — needs more tweets)")
    else:
        print(f"  {'tag':30s}  {'kind':10s}  {'mentions':>8s}  {'avg_sent':>8s}")
        print("  " + "-" * 64)
        for _, r in df.iterrows():
            sent_str = f"{r['avg_sentiment']:+.2f}" if r['avg_sentiment'] is not None else "  —  "
            print(f"  {r['tag']:30s}  {r['kind']:10s}  {r['total_count']:>8,}  {sent_str:>8s}")

    print()
    print("=" * 78)
    print(f"  ✓ Live data captured at {datetime.now(UTC).strftime('%H:%M:%S UTC')}")
    print(f"    Re-run: python live_scrape_once.py")
    print(f"    Or:     make pipeline (continuous, every 60s)")
    print("=" * 78)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
