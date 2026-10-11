"""Tests for the trending-tags extractor + DB CRUD + dashboard query.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from src.sources.trending import (
    _floor_to_bucket,
    aggregate_tags,
    extract_tags_from_tweet,
    top_n_over_window,
)
from src.store import db

# ── Tag extraction ──────────────────────────────────────────────────────


def test_extract_cashtags():
    hits = extract_tags_from_tweet(
        tweet_text="$BTC breakout confirmed, $ETH looking weak",
        tweet_id=1, ts=datetime(2026, 1, 1, 12, 0, 0),
    )
    assert len(hits) == 2
    cashtags = {h.tag for h in hits if h.kind == "cashtag"}
    assert cashtags == {"$BTC", "$ETH"}


def test_extract_hashtags():
    hits = extract_tags_from_tweet(
        tweet_text="#memecoin to the moon #fintok",
        tweet_id=1, ts=datetime(2026, 1, 1, 12, 0, 0),
    )
    hashtags = {h.tag for h in hits if h.kind == "hashtag"}
    assert hashtags == {"#memecoin", "#fintok"}


def test_extract_keywords_case_insensitive():
    hits = extract_tags_from_tweet(
        tweet_text="GirlF and AI startups are heating up",
        tweet_id=1, ts=datetime(2026, 1, 1, 12, 0, 0),
        keywords=["girlf", "ai"],
    )
    kinds = {h.tag: h.kind for h in hits}
    assert "girlf" in kinds
    assert "ai" in kinds
    assert all(kinds[k] == "keyword" for k in ("girlf", "ai"))


def test_extract_does_not_match_lowercase_cashtags():
    """The regex requires uppercase — `$btc` is not a cashtag, only `$BTC` is."""
    hits = extract_tags_from_tweet(
        tweet_text="lowercase $btc should not match",
        tweet_id=1, ts=datetime(2026, 1, 1, 12, 0, 0),
    )
    cashtags = [h for h in hits if h.kind == "cashtag"]
    assert cashtags == []


def test_extract_skips_short_hashtags():
    """Hashtag regex requires 1 leading letter + 2+ more chars (3+ total)."""
    hits = extract_tags_from_tweet(
        tweet_text="#ab #a #really_long_hashtag",
        tweet_id=1, ts=datetime(2026, 1, 1, 12, 0, 0),
    )
    hashtags = {h.tag for h in hits if h.kind == "hashtag"}
    # "#ab" (2 chars) — too short, rejected by {2,}
    # "#a" (1 char) — too short, rejected
    # "#really_long_hashtag" (19 chars) — accepted
    assert hashtags == {"#really_long_hashtag"}


def test_extract_preserves_sentiment_and_url():
    hits = extract_tags_from_tweet(
        tweet_text="$SOL is pumping",
        tweet_id=42, ts=datetime(2026, 1, 1, 12, 0, 0),
        sentiment=0.7, url="https://x.com/alice/status/42",
    )
    assert len(hits) == 1
    assert hits[0].sentiment == 0.7
    assert hits[0].url == "https://x.com/alice/status/42"
    assert hits[0].tweet_id == 42


# ── Aggregation ─────────────────────────────────────────────────────────


def test_floor_to_bucket_floors_to_minute():
    """Use UTC so the test doesn't depend on the host's local timezone."""
    ts = datetime(2026, 1, 1, 12, 0, 47, tzinfo=UTC)
    floored = _floor_to_bucket(ts, 60)
    assert floored == datetime(2026, 1, 1, 12, 0, 0)


def test_aggregate_groups_same_tag_in_same_bucket():
    base = datetime(2026, 1, 1, 12, 0, 10)
    hits = [
        extract_tags_from_tweet("$BTC up", 1, base)[0],
        extract_tags_from_tweet("$BTC to the moon", 2, base + timedelta(seconds=20))[0],
    ]
    grouped = aggregate_tags(hits, bucket_seconds=60)
    # 1 key, 1 tag, 2 hits
    assert len(grouped) == 1
    row = next(iter(grouped.values()))
    assert row["tag"] == "$BTC"
    assert row["count"] == 2


def test_aggregate_separates_buckets():
    base = datetime(2026, 1, 1, 12, 0, 10)
    later = base + timedelta(minutes=2)
    hits = [
        extract_tags_from_tweet("$BTC up", 1, base)[0],
        extract_tags_from_tweet("$BTC to the moon", 2, later)[0],
    ]
    grouped = aggregate_tags(hits, bucket_seconds=60)
    assert len(grouped) == 2  # 2 different buckets
    for row in grouped.values():
        assert row["count"] == 1


def test_aggregate_computes_avg_sentiment():
    base = datetime(2026, 1, 1, 12, 0, 10)
    hits = [
        extract_tags_from_tweet("$BTC up", 1, base, sentiment=0.5)[0],
        extract_tags_from_tweet("$BTC up", 2, base + timedelta(seconds=10), sentiment=0.9)[0],
    ]
    grouped = aggregate_tags(hits, bucket_seconds=60)
    row = next(iter(grouped.values()))
    assert row["avg_sentiment"] == pytest.approx(0.7)


def test_aggregate_keeps_latest_sample():
    base = datetime(2026, 1, 1, 12, 0, 10)
    later = base + timedelta(seconds=30)
    hits = [
        extract_tags_from_tweet("$BTC first tweet", 1, base, url="https://x/1")[0],
        extract_tags_from_tweet("$BTC second tweet", 2, later, url="https://x/2")[0],
    ]
    grouped = aggregate_tags(hits, bucket_seconds=60)
    row = next(iter(grouped.values()))
    assert "second" in row["sample_text"]
    assert row["sample_url"] == "https://x/2"


def test_top_n_orders_by_count_desc():
    base = datetime(2026, 1, 1, 12, 0, 0)
    hits = []
    for i in range(5):
        hits.extend(extract_tags_from_tweet("$BTC up", 100 + i, base + timedelta(seconds=i)))
    for i in range(3):
        hits.extend(extract_tags_from_tweet("$ETH up", 200 + i, base + timedelta(seconds=i)))
    for i in range(7):
        hits.extend(extract_tags_from_tweet("#memecoin up", 300 + i, base + timedelta(seconds=i)))
    top = top_n_over_window(hits, window_minutes=5, top_n=3)
    assert [r["tag"] for r in top] == ["#memecoin", "$BTC", "$ETH"]
    assert top[0]["total_count"] == 7
    assert top[1]["total_count"] == 5
    assert top[2]["total_count"] == 3


def test_top_n_respects_limit():
    base = datetime(2026, 1, 1, 12, 0, 0)
    hits = []
    for tag, n in [("$BTC", 5), ("$ETH", 3), ("$SOL", 2), ("#memecoin", 4), ("#altcoin", 1)]:
        body = f"{tag} up"
        for i in range(n):
            hits.extend(extract_tags_from_tweet(body, 1000 + i, base + timedelta(seconds=i)))
    top = top_n_over_window(hits, window_minutes=5, top_n=2)
    assert len(top) == 2
    # Top 2 by count: $BTC=5, #memecoin=4
    counts = {r["tag"]: r["total_count"] for r in top}
    assert counts == {"$BTC": 5, "#memecoin": 4}


# ── DB CRUD ─────────────────────────────────────────────────────────────


@pytest.fixture
def trending_db(tmp_path):
    url = f"sqlite:///{tmp_path}/trending.db"
    db.override_engine(url)
    db.ensure_sqlite_schema()
    yield


def test_upsert_and_fetch_trending_tag(trending_db):
    bucket = datetime.utcnow().replace(second=0, microsecond=0)
    db.upsert_trending_tag({
        "ts": bucket, "bucket": bucket,
        "tag": "$BTC", "tag_kind": "cashtag",
        "count": 5, "avg_sentiment": 0.42,
        "sample_text": "BTC breakout", "sample_url": "https://x/123",
    })
    rows = db.fetch_trending_tags(minutes=5, limit=10)
    assert len(rows) == 1
    assert rows[0]["tag"] == "$BTC"
    assert rows[0]["total_count"] == 5
    assert rows[0]["avg_sent"] == pytest.approx(0.42, abs=1e-6)
    assert rows[0]["sample_text"] == "BTC breakout"


def test_upsert_overwrites_count_on_same_bucket_tag(trending_db):
    bucket = datetime.utcnow().replace(second=0, microsecond=0)
    for n in (1, 2, 3):
        db.upsert_trending_tag({
            "ts": bucket, "bucket": bucket,
            "tag": "$ETH", "tag_kind": "cashtag",
            "count": n,
        })
    rows = db.fetch_trending_tags(minutes=5, limit=10)
    assert len(rows) == 1
    assert rows[0]["total_count"] == 3  # last write wins


def test_fetch_aggregates_across_buckets(trending_db):
    """If $BTC appears in 2 different 1-min buckets, fetch_trending_tags
    should sum them into a single row with total_count=sum."""
    now = datetime.utcnow().replace(second=0, microsecond=0)
    b1 = now - timedelta(minutes=2)
    b2 = now - timedelta(minutes=1)
    for b, n in [(b1, 3), (b2, 4)]:
        db.upsert_trending_tag({
            "ts": b, "bucket": b,
            "tag": "$BTC", "tag_kind": "cashtag",
            "count": n,
        })
    rows = db.fetch_trending_tags(minutes=5, limit=10)
    assert len(rows) == 1
    assert rows[0]["total_count"] == 7


def test_fetch_orders_by_count_desc(trending_db):
    now = datetime.utcnow().replace(second=0, microsecond=0)
    for tag, n in [("$BTC", 10), ("$ETH", 3), ("#x", 7)]:
        db.upsert_trending_tag({
            "ts": now, "bucket": now,
            "tag": tag, "tag_kind": "cashtag" if tag.startswith("$") else "hashtag",
            "count": n,
        })
    rows = db.fetch_trending_tags(minutes=5, limit=10)
    assert [r["tag"] for r in rows] == ["$BTC", "#x", "$ETH"]


def test_fetch_respects_limit(trending_db):
    now = datetime.utcnow().replace(second=0, microsecond=0)
    for i in range(20):
        db.upsert_trending_tag({
            "ts": now, "bucket": now,
            "tag": f"$T{i}", "tag_kind": "cashtag",
            "count": 20 - i,
        })
    rows = db.fetch_trending_tags(minutes=5, limit=5)
    assert len(rows) == 5


def test_bulk_upsert_trending_tags_returns_count(trending_db):
    base = datetime.utcnow().replace(second=0, microsecond=0)
    rows = [
        {"ts": base, "bucket": base, "tag": f"$T{i}", "tag_kind": "cashtag", "count": 1}
        for i in range(7)
    ]
    assert db.bulk_upsert_trending_tags(rows) == 7
    # Re-bulk should also be 7 (overwrites)
    assert db.bulk_upsert_trending_tags(rows) == 7
