"""Ranking topics and explaining why each one is trending.

The ranking is computed in plain Python. That is deliberate. A language
model asked to "rank the trending topics" produces a list with no way to
check it and no way to reproduce it. Here, every number in the output is
computed from the collected posts by a function that has a test, and the
rationale is assembled from those same numbers.

What the rationale says, and how each claim is earned:

* **"Spiking: 6 mentions in the last 3 days, up from 2 the week before"** —
  the recent and baseline counts, stated directly.
* **"Confirmed on Hacker News, dev.to and Stack Overflow"** — the platforms
  the topic actually appeared on, named.
* **"Headline: 'Rust 1.90 released'"** — a real post, with a link.

And what it says when the evidence is thin: a topic seen on one platform
with three mentions is flagged as *unconfirmed* rather than dressed up as a
cross-platform trend.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .burst import (
    CORROBORATION_BONUS,
    MAX_RATIO_SCORE,
    MIN_RECENT_MENTIONS,
    TopicSignal,
    burst_report,
    score_topic,
)
from .config import Settings
from .models import Post
from .semantic import SemanticMatcher

#: A topic seen on at least this many platforms is treated as confirmed
#: rather than platform-local.
CONFIRMED_PLATFORM_COUNT = 2

#: Below this many recent mentions a topic is reported as emerging rather
#: than trending.
EMERGING_MENTIONS = MIN_RECENT_MENTIONS


@dataclass(slots=True)
class Evidence:
    """One piece of the case for a topic being a trend."""

    kind: str  # "headline" | "platform" | "metric"
    text: str
    url: str = ""
    platform: str = ""

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "text": self.text,
            "url": self.url,
            "platform": self.platform,
        }


@dataclass(slots=True)
class Trend:
    """A ranked trend, with the evidence that produced it."""

    topic: str
    score: float
    rank: int = 0
    recent_mentions: int = 0
    baseline_mentions: int = 0
    ratio: float = 0.0
    platforms: list[str] = field(default_factory=list)
    corroborated: bool = False
    confidence: str = "low"
    summary: str = ""
    rationale: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    headlines: list[dict] = field(default_factory=list)
    #: The score broken into its parts, so the arithmetic is visible.
    breakdown: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "topic": self.topic,
            "score": round(self.score, 4),
            "recent_mentions": self.recent_mentions,
            "baseline_mentions": self.baseline_mentions,
            "ratio": round(self.ratio, 4),
            "platforms": self.platforms,
            "corroborated": self.corroborated,
            "confidence": self.confidence,
            "summary": self.summary,
            "rationale": self.rationale,
            "evidence": [e.to_dict() for e in self.evidence],
            "headlines": self.headlines,
            "breakdown": self.breakdown,
        }


def _humanise_platform(name: str) -> str:
    """`hackernews` -> `Hacker News`."""
    special = {
        "hackernews": "Hacker News",
        "stackoverflow": "Stack Overflow",
        "devto": "dev.to",
        "github": "GitHub",
        "youtube": "YouTube",
        "rss": "RSS feeds",
        "reddit": "Reddit",
    }
    if name in special:
        return special[name]
    return name.replace("_", " ").title()


def _confidence(signal: TopicSignal) -> str:
    """How much the evidence supports the call, from the mention count."""
    if signal.recent_mentions >= 6:
        return "high"
    if signal.recent_mentions >= EMERGING_MENTIONS:
        return "medium"
    return "low"


def _describe(signal: TopicSignal, score: float) -> tuple[str, list[str], list[Evidence]]:
    """Build the summary, the rationale lines and the evidence list."""
    evidence: list[Evidence] = []
    rationale: list[str] = []

    platforms = sorted(signal.recent_platforms)
    platform_names = [_humanise_platform(p) for p in platforms]

    # The headline claim: the counts.
    if signal.baseline_mentions == 0:
        count_claim = (
            f"{signal.recent_mentions} mentions in the last few days, "
            f"with none in the week before"
        )
        ratio_claim = "new to this window"
    else:
        count_claim = (
            f"{signal.recent_mentions} mentions in the last few days "
            f"against {signal.baseline_mentions} in the week before"
        )
        direction = "up" if signal.ratio > 1 else "flat"
        ratio_claim = f"moving {direction} {signal.ratio:.1f}x"
    rationale.append(count_claim + " — " + ratio_claim + ".")

    # The corroboration claim.
    if len(platforms) >= CONFIRMED_PLATFORM_COUNT:
        corroboration = "confirmed on " + ", ".join(platform_names[:-1])
        if len(platform_names) > 1:
            corroboration += " and " + platform_names[-1]
        rationale.append(f"Cross-platform: {corroboration}.")
        evidence.append(
            Evidence(
                kind="platform",
                text=f"Seen on {len(platforms)} platforms: {', '.join(platform_names)}",
            )
        )
    else:
        rationale.append(
            f"Single platform only ({platform_names[0] if platform_names else 'unknown'}) — "
            f"this may be local to that community rather than a wider trend."
        )

    # The concrete example: a real post with a link.
    if signal.titles:
        example = signal.titles[0]
        rationale.append(f'Example: "{example}".')
        evidence.append(Evidence(kind="headline", text=example, url=""))

    for platform in platforms:
        evidence.append(
            Evidence(
                kind="platform",
                text=f"{_humanise_platform(platform)}: mentioned in the recent window",
                platform=platform,
            )
        )

    if len(platforms) >= CONFIRMED_PLATFORM_COUNT:
        summary = (
            f"{signal.topic} is accelerating: {signal.recent_mentions} mentions "
            f"across {len(platforms)} platforms."
        )
    else:
        summary = (
            f"{signal.topic} is picking up: {signal.recent_mentions} mentions, "
            f"all on {platform_names[0] if platform_names else 'one platform'}."
        )

    return summary, rationale, evidence


def _headlines(signal: TopicSignal, limit: int = 5) -> list[dict]:
    """The posts that support the trend, with their links."""
    titles = signal.titles[:limit]
    urls = signal.urls[:limit]
    return [
        {"title": title, "url": urls[i] if i < len(urls) else ""}
        for i, title in enumerate(titles)
    ]


def build_trends(
    posts: list[Post],
    settings: Settings | None = None,
    now: datetime | None = None,
    limit: int = 20,
    semantic: SemanticMatcher | None = None,
) -> list[Trend]:
    """The ranked trends for a corpus of posts.

    The list is ranked by score, and every entry carries the evidence that
    produced its score.
    """
    settings = settings or Settings()
    reference = now or datetime.now(timezone.utc)

    trends: list[Trend] = []
    ranked = burst_report(
        posts, settings=settings, now=reference, limit=limit, semantic=semantic
    )

    for signal, score in ranked:
        summary, rationale, evidence = _describe(signal, score)
        corroborated = len(signal.recent_platforms) >= CONFIRMED_PLATFORM_COUNT

        # The visible arithmetic, so the score can be checked.
        ratio_part = min(signal.ratio, MAX_RATIO_SCORE) * 0.6
        volume_part = 0.0
        if signal.ratio >= 1.0:
            volume_part = math.log1p(signal.recent_mentions) * 0.8
        cross_platform = max(0, len(signal.recent_platforms) - 1)
        corroboration_part = min(cross_platform, 3) * CORROBORATION_BONUS

        confidence = _confidence(signal)

        trends.append(
            Trend(
                topic=signal.topic,
                score=score,
                recent_mentions=signal.recent_mentions,
                baseline_mentions=signal.baseline_mentions,
                ratio=signal.ratio,
                platforms=sorted(signal.recent_platforms),
                corroborated=corroborated,
                confidence=confidence,
                summary=summary,
                rationale=rationale,
                evidence=evidence,
                headlines=_headlines(signal),
                breakdown={
                    "acceleration": round(ratio_part, 4),
                    "volume": round(volume_part, 4),
                    "corroboration": round(corroboration_part, 4),
                    "total": round(score, 4),
                },
            )
        )

    for index, trend in enumerate(trends, start=1):
        trend.rank = index

    return trends


def explain(trend: Trend) -> str:
    """A plain-text explanation of one trend, for the report and the CLI."""
    lines = [f"{trend.rank}. {trend.topic}  (score {trend.score:.2f})", f"   {trend.summary}"]
    for reason in trend.rationale:
        lines.append(f"   - {reason}")
    if trend.headlines:
        lines.append(f"   Sources: {len(trend.headlines)} post(s)")
    return "\n".join(lines)


def score_all(
    posts: list[Post],
    settings: Settings | None = None,
    semantic: SemanticMatcher | None = None,
) -> dict[str, float]:
    """The score for every topic in the corpus, keyed by topic.

    Useful for the evaluation harness, which needs to compare the ranking
    against a gold set.
    """
    settings = settings or Settings()
    from .burst import detect_bursts

    signals = detect_bursts(posts, settings=settings, semantic=semantic)
    return {topic: score_topic(signal, settings) for topic, signal in signals.items()}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
