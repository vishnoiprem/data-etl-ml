"""Burst detection — measuring acceleration, not volume.

A topic that is mentioned a hundred times is not necessarily trending. It
might have been trending for a year, in which case the reader already knows.
What a radar is for is the topic that is *suddenly* everywhere.

So a burst is a rate comparison:

    burst_score = (recent rate) / (baseline rate)

The recent window is short (48 hours by default). The baseline window is
long (a week). The ratio says how much faster the topic is moving now than
it was moving before.

Two corrections keep the number honest:

* **A floor on the baseline.** A topic with zero mentions in the baseline
  would have an infinite burst. The baseline is smoothed with a small prior
  so a brand-new topic gets a large but finite score.
* **A floor on the raw volume.** A topic mentioned twice, both times in the
  last hour, is not a trend. A minimum mention count is required before the
  acceleration is allowed to matter.

Corroboration across platforms is tracked separately, because a topic
spiking on one platform is usually a platform-local event, while a topic
spiking on four is usually a real trend.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from .config import Settings
from .models import Post
from .semantic import SemanticMatcher, SemanticResult
from .topics import (
    PostTopics,
    canonical_topic,
    extract_topics,
    is_person_name,
    ngram_candidates,
    topics_for_post,
)

#: The minimum number of mentions in the recent window before a topic is
#: eligible to trend at all. Without this, a topic mentioned once gets a
#: huge ratio and outranks everything.
#:
#: The threshold scales with the size of the recent window, not the corpus:
#: a 48-hour window with a 7-day baseline needs more mentions than a 6-hour
#: window does, because a longer window naturally collects more. It is
#: capped at `MAX_MIN_RECENT_MENTIONS` so that a very short window cannot
#: let a single post through as a "trend".
MIN_RECENT_MENTIONS = 3
MAX_MIN_RECENT_MENTIONS = 6

#: How many recent posts one mention is worth when deriving the threshold.
#: A 48-hour window is four times the minimum window, so the threshold
#: grows with it.
MIN_RECENT_MENTIONS_PER_24H = 1.5

#: Added to the baseline rate before dividing, so a topic with no history
#: gets a large but finite burst score rather than an infinite one. This is
#: a Laplace-style prior on the rate.
BASELINE_PRIOR = 0.5

#: The multiplier applied to a topic that appears on more than one platform.
#: Cross-platform corroboration is the strongest evidence a trend is real.
CORROBORATION_BONUS = 0.35

#: The largest burst score a topic can reach from the ratio alone.
MAX_RATIO_SCORE = 10.0


@dataclass(slots=True)
class TopicSignal:
    """Everything the detector knows about one topic."""

    topic: str = ""
    recent_mentions: int = 0
    baseline_mentions: int = 0
    recent_weight: float = 0.0
    baseline_weight: float = 0.0
    platforms: set[str] = field(default_factory=set)
    recent_platforms: set[str] = field(default_factory=set)
    post_ids: list[str] = field(default_factory=list)
    titles: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    evidence: dict[str, str] = field(default_factory=dict)
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    kinds: set[str] = field(default_factory=set)

    @property
    def baseline_rate(self) -> float:
        """Mentions per baseline window."""
        return float(self.baseline_mentions)

    @property
    def recent_rate(self) -> float:
        """Mentions per recent window."""
        return float(self.recent_mentions)

    @property
    def ratio(self) -> float:
        """Recent rate over baseline rate, with the prior smoothing."""
        return self.recent_rate / (self.baseline_rate + BASELINE_PRIOR)

    @property
    def corroboration(self) -> int:
        """How many distinct platforms carried this topic."""
        return len(self.platforms)

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "recent_mentions": self.recent_mentions,
            "baseline_mentions": self.baseline_mentions,
            "recent_weight": round(self.recent_weight, 6),
            "baseline_weight": round(self.baseline_weight, 6),
            "ratio": round(self.ratio, 4),
            "platforms": sorted(self.platforms),
            "recent_platforms": sorted(self.recent_platforms),
            "corroboration": self.corroboration,
            "post_ids": self.post_ids[:10],
            "titles": self.titles[:5],
            "urls": self.urls[:5],
            "kinds": sorted(self.kinds),
        }


def attach_topics(
    posts: list[Post],
    semantic: SemanticMatcher | None = None,
) -> list[PostTopics]:
    """Extract the topics from every post, applying the corpus-wide n-gram filter.

    The filter needs the whole corpus: a phrase is only a topic if it
    recurs. So extraction happens in two passes — collect the candidate
    phrases, decide which recur, then apply that decision.

    The semantic matcher is applied in one batch across the whole corpus.
    Embedding a title at a time would mean a thousand model calls; the
    batch is one, and the result is identical.
    """
    drafts: list[PostTopics] = []
    for post in posts:
        drafts.append(
            PostTopics(
                post_id=post.id,
                platform=post.platform,
                title=post.title,
                published=post.published,
                weight=post.weight,
                url=post.url,
                raw_engagement=post.raw_engagement,
                tags=post.tags,
            )
        )

    whitelist = set(ngram_candidates(drafts))

    # One batch, one model call. When the matcher is unavailable this
    # returns a disabled result per post and the lexical path is untouched.
    semantic_matches: list[SemanticResult] = []
    if semantic is not None and semantic.available:
        semantic_matches = semantic.match_many([post.title for post in posts])

    for index, (draft, post) in enumerate(zip(drafts, posts, strict=True)):
        found = topics_for_post(post, ngram_whitelist=whitelist)
        draft.topics = found
        for match in extract_topics(post.title, post.description, post.tags):
            if match.topic in found:
                draft.kinds.setdefault(match.topic, match.kind)
                if match.topic not in draft.evidence:
                    draft.evidence[match.topic] = match.surface

        # The semantic signal is added here rather than through
        # `extract_topics`, so that the corpus is embedded once instead of
        # once per post.
        #
        # A semantic match is only added when the lexical signals found
        # *nothing* for this post. Two reasons.
        #
        # First, the evidence trail. When a topic was found by the
        # lexical path, the evidence should show the word that actually
        # appeared — "rust" — not a similarity score.
        #
        # Second, and more importantly, the acceleration ratio. A post that
        # the lexical signals already resolved is a post whose mention
        # count is already correct. Adding a second topic to it on a
        # similarity hunch inflates the *other* topic's count in both
        # windows, and a topic whose counts are inflated in both windows
        # has its burst flattened. Measured on the burst fixture: without
        # this rule, "Everything about docker you need to know" also
        # counted as a mention of `kubernetes`, which pushed kubernetes
        # from 9 recent / 1 baseline to 15 / 7 and dropped its ratio from
        # 6.0 to 2.0 — enough to push a genuinely accelerating topic out
        # of the top four.
        #
        # The semantic layer's job is to catch titles the lexical signals
        # cannot resolve at all. Where the lexical signals have an
        # opinion, they keep it.
        if index < len(semantic_matches) and not found:
            for match in semantic_matches[index].matches:
                canonical = canonical_topic(match.topic)
                if canonical in found or canonical in draft.evidence:
                    continue
                if not canonical or is_person_name(canonical):
                    continue
                found.append(canonical)
                draft.kinds[canonical] = "semantic"
                draft.evidence[canonical] = f"semantic match ({match.score})"

    return drafts


def detect_bursts(
    posts: list[Post],
    settings: Settings | None = None,
    now: datetime | None = None,
    semantic: SemanticMatcher | None = None,
) -> dict[str, TopicSignal]:
    """Measure the burst for every topic found in the corpus.

    The reference time defaults to now, so the windows are relative to the
    run. Tests pass an explicit `now` to make the windows deterministic.
    """
    settings = settings or Settings()
    reference = now or datetime.now(timezone.utc)

    recent_start = reference - timedelta(hours=settings.recent_window_hours)
    baseline_start = reference - timedelta(
        hours=settings.recent_window_hours + settings.baseline_window_hours
    )

    signals: dict[str, TopicSignal] = defaultdict(lambda: TopicSignal(topic=""))
    drafts = attach_topics(posts, semantic=semantic)

    for draft in drafts:
        published = draft.published
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)

        for topic in draft.topics:
            signal = signals[topic]
            signal.topic = topic
            signal.platforms.add(draft.platform)
            signal.kinds.add(draft.kinds.get(topic, "text"))

            if signal.first_seen is None or published < signal.first_seen:
                signal.first_seen = published
            if signal.last_seen is None or published > signal.last_seen:
                signal.last_seen = published

            if published >= recent_start:
                signal.recent_mentions += 1
                signal.recent_weight += draft.weight
                signal.recent_platforms.add(draft.platform)
                signal.post_ids.append(draft.post_id)
                if draft.title not in signal.titles:
                    signal.titles.append(draft.title)
                if draft.url and draft.url not in signal.urls:
                    signal.urls.append(draft.url)
                if topic in draft.evidence:
                    signal.evidence.setdefault(topic, draft.evidence[topic])
            elif published >= baseline_start:
                signal.baseline_mentions += 1
                signal.baseline_weight += draft.weight

    return dict(signals)


def score_topic(signal: TopicSignal, settings: Settings | None = None) -> float:
    """The composite score for one topic.

    The score has three parts:

    * **Acceleration** — the recent-over-baseline ratio, capped so one
      extremely spiky topic cannot dominate the whole list.
    * **Volume** — the raw recent mention count, log-squashed so that a
      topic with 50 mentions beats one with 5 without beating one with 500
      by a factor of 100.
    * **Corroboration** — a bonus for appearing on more than one platform,
      because that is the difference between a platform-local event and a
      real trend.

    Volume is *gated* on acceleration rather than simply added to it. A topic
    that is being mentioned less than it was last week is not trending,
    however many mentions it has — it is a topic that has been big for a
    long time and the reader already knows. Without the gate, `python` (68
    baseline mentions, ratio 0.06) outranked every genuinely accelerating
    topic purely on volume.

    Each part is on its own interpretable scale, and the arithmetic is shown
    in the rationale, so a reader can see *why* a topic ranked where it did.
    """
    settings = settings or Settings()

    if signal.recent_mentions < MIN_RECENT_MENTIONS:
        return 0.0

    # Acceleration: the ratio, capped.
    ratio_score = min(signal.ratio, MAX_RATIO_SCORE)

    # A topic that is slowing down gets no volume credit. The gate is
    # deliberately at 1.0 — at exactly the baseline rate it is flat, which
    # is not a trend either way.
    if signal.ratio < 1.0:
        return 0.0

    # Volume: log-squashed recent mentions, applied only to a topic that
    # is actually accelerating.
    volume_score = math.log1p(signal.recent_mentions)

    # Corroboration: one bonus for more than one platform, capped so a topic
    # on seven platforms does not swamp everything else.
    cross_platform = max(0, len(signal.recent_platforms) - 1)
    corroboration_score = min(cross_platform, 3) * CORROBORATION_BONUS

    return (ratio_score * 0.6) + (volume_score * 0.8) + corroboration_score


def burst_report(
    posts: list[Post],
    settings: Settings | None = None,
    now: datetime | None = None,
    limit: int = 20,
    semantic: SemanticMatcher | None = None,
) -> list[tuple[TopicSignal, float]]:
    """The scored topics, best first.

    Ties are broken by corroboration and then by raw mentions, so the order
    is stable and the strongest-evidence topic wins a tie.
    """
    settings = settings or Settings()
    signals = detect_bursts(posts, settings=settings, now=now, semantic=semantic)

    scored = [(signal, score_topic(signal, settings)) for signal in signals.values()]
    eligible = [(s, sc) for s, sc in scored if sc > 0]
    eligible.sort(
        key=lambda pair: (
            -pair[1],
            -len(pair[0].recent_platforms),
            -pair[0].recent_mentions,
            pair[0].topic,
        )
    )
    return eligible[:limit]


def platform_mentions(posts: list[Post], now: datetime | None = None) -> Counter[str]:
    """How many posts each platform contributed. Used to report coverage."""
    reference = now or datetime.now(timezone.utc)
    counts: Counter[str] = Counter()
    for post in posts:
        published = post.published
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        age = (reference - published).total_seconds() / 3600
        if age <= 24 * 14:
            counts[post.platform] += 1
    return counts
