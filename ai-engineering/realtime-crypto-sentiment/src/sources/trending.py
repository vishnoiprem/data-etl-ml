"""Tag extraction + aggregation for trending-tags dashboard.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Given a list of RawTweet objects, extract:
- cashtags  ($BTC, $ETH, ...)
- hashtags  (#memecoin, #fintok, ...)
- keywords  (lowercased; matched case-insensitively in the tweet body)

Then bucket them by 1-min window and count occurrences so the dashboard
can show "top 10 tags in the last 5 min" with a real-time sparkline.

This module is pure-Python (no DB) so it's unit-testable in isolation;
the pipeline wires the output into db.upsert_trending_tag.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

# ── Regexes ────────────────────────────────────────────────────────────

# Cashtags: $ followed by 2-5 uppercase letters (BTC, ETH, SOL, etc.)
_CASHTAG_RE = re.compile(r"\$([A-Z]{2,5})\b")
# Hashtags: # followed by letters/digits/underscore (3+ chars, not just #)
_HASHTAG_RE = re.compile(r"#([A-Za-z][A-Za-z0-9_]{2,})\b")


@dataclass
class TagHit:
    """One occurrence of a tag in a tweet."""
    tag: str
    kind: str  # "cashtag" | "hashtag" | "keyword"
    tweet_id: int
    ts: datetime
    sentiment: float | None = None
    text: str = ""
    url: str = ""


def extract_tags_from_tweet(
    tweet_text: str,
    tweet_id: int,
    ts: datetime,
    sentiment: float | None = None,
    url: str = "",
    keywords: list[str] | None = None,
) -> list[TagHit]:
    """Return all tags found in a single tweet.

    `keywords` is a list of lowercase words to match in the body
    (e.g. ["ai", "llm", "data engineering"]).
    """
    hits: list[TagHit] = []
    # Cashtags — preserve the $ so the dashboard can render $BTC verbatim
    for m in _CASHTAG_RE.finditer(tweet_text):
        hits.append(TagHit(
            tag=f"${m.group(1)}", kind="cashtag",
            tweet_id=tweet_id, ts=ts, sentiment=sentiment, text=tweet_text, url=url,
        ))
    # Hashtags — strip the # from the tag, dashboard re-prefixes on render
    for m in _HASHTAG_RE.finditer(tweet_text):
        hits.append(TagHit(
            tag=f"#{m.group(1)}", kind="hashtag",
            tweet_id=tweet_id, ts=ts, sentiment=sentiment, text=tweet_text, url=url,
        ))
    # Keywords — case-insensitive substring match
    if keywords:
        lower = tweet_text.lower()
        for kw in keywords:
            if kw and kw.lower() in lower:
                hits.append(TagHit(
                    tag=kw.lower(), kind="keyword",
                    tweet_id=tweet_id, ts=ts, sentiment=sentiment, text=tweet_text, url=url,
                ))
    return hits


def aggregate_tags(
    hits: list[TagHit],
    bucket_seconds: int = 60,
) -> dict[tuple[datetime, str], dict]:
    """Group tag hits into time buckets.

    Returns: {(bucket_ts, tag): {tag, tag_kind, count, avg_sentiment,
                                  sample_text, sample_url}}
    The first hit's text is used as the sample (later ones are skipped
    so we don't waste memory storing every tweet).
    """
    grouped: dict[tuple[datetime, str], dict] = {}
    sentiment_sums: dict[tuple[datetime, str], list[float]] = defaultdict(list)

    for h in hits:
        bucket_ts = _floor_to_bucket(h.ts, bucket_seconds)
        key = (bucket_ts, h.tag)
        if key not in grouped:
            grouped[key] = {
                "bucket": bucket_ts,
                "tag": h.tag,
                "tag_kind": h.kind,
                "count": 0,
                "sample_text": h.text[:280],
                "sample_url": h.url,
                "ts": h.ts,
            }
        grouped[key]["count"] += 1
        # Keep the most recent sample (so the dashboard shows fresh content)
        if h.ts >= grouped[key]["ts"]:
            grouped[key]["sample_text"] = h.text[:280]
            grouped[key]["sample_url"] = h.url
            grouped[key]["ts"] = h.ts
        if h.sentiment is not None:
            sentiment_sums[key].append(h.sentiment)

    # Compute per-bucket average sentiment
    for key, vals in sentiment_sums.items():
        if key in grouped:
            grouped[key]["avg_sentiment"] = sum(vals) / len(vals)
    return grouped


def _floor_to_bucket(ts: datetime, bucket_seconds: int) -> datetime:
    """Floor `ts` down to the nearest `bucket_seconds` boundary."""
    epoch = int(ts.timestamp())
    floored = epoch - (epoch % bucket_seconds)
    return datetime.utcfromtimestamp(floored)


def top_n_over_window(
    hits: list[TagHit],
    window_minutes: int = 5,
    top_n: int = 10,
) -> list[dict]:
    """Convenience: aggregate, then sum counts across buckets within
    the window. Returns [{tag, kind, total_count, avg_sentiment,
    sample_text, sample_url}] sorted by total_count DESC.
    """
    grouped = aggregate_tags(hits)
    by_tag: dict[str, dict] = {}
    for key, val in grouped.items():
        tag = val["tag"]
        if tag not in by_tag:
            by_tag[tag] = {
                "tag": tag, "kind": val["tag_kind"],
                "total_count": 0, "sentiment_sum": 0.0, "sentiment_n": 0,
                "sample_text": val["sample_text"], "sample_url": val["sample_url"],
            }
        by_tag[tag]["total_count"] += val["count"]
        if val.get("avg_sentiment") is not None:
            by_tag[tag]["sentiment_sum"] += val["avg_sentiment"] * val["count"]
            by_tag[tag]["sentiment_n"] += val["count"]

    out = []
    for tag, v in by_tag.items():
        avg_sent = v["sentiment_sum"] / v["sentiment_n"] if v["sentiment_n"] else None
        out.append({
            "tag": tag,
            "kind": v["kind"],
            "total_count": v["total_count"],
            "avg_sentiment": avg_sent,
            "sample_text": v["sample_text"],
            "sample_url": v["sample_url"],
        })
    out.sort(key=lambda r: r["total_count"], reverse=True)
    return out[:top_n]
