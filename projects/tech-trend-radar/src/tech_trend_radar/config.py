"""Settings, paths and the knobs the radar is tuned with.

Everything here has a default that works with no API key and no network, so
`make test` and `make demo` never depend on the environment being set up.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

#: The project root — `src/tech_trend_radar/config.py` -> up three levels.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
REPORT_DIR = PROJECT_ROOT / "reports"

#: The default feed set. Each entry is a public, credential-free feed.
#: Adding a source is a config change, not a code change.
DEFAULT_RSS_FEEDS: dict[str, str] = {
    "techcrunch": "https://techcrunch.com/feed/",
    "theverge": "https://www.theverge.com/rss/index.xml",
    "arxiv_ai": "https://export.arxiv.org/rss/cs.AI",
    "arxiv_cs": "https://export.arxiv.org/rss/cs.LG",
}

#: YouTube channels tracked as video sources. Channel ids are stable; the
#: feed needs no key.
DEFAULT_YOUTUBE_CHANNELS: dict[str, str] = {
    "google_developers": "UCBJycsmduvYEL83R_U4JriQ",
}

#: How many days back the GitHub search looks for newly-created repositories.
#: The query date has to be computed at call time — GitHub's search syntax
#: does not understand relative dates like `30-days-ago`, and silently
#: returns zero results for them.
GITHUB_LOOKBACK_DAYS = 14

#: The star floor. Low enough to catch a genuine new wave, high enough that
#: the noise floor of abandoned repositories does not swamp the signal.
GITHUB_STAR_FLOOR = 20

#: The fork floor, and the reason it exists.
#:
#: Stars are trivially gameable. A search for new repositories with
#: `stars:>20` surfaces dozens of star-farmed copies of the same project,
#: each with hundreds of stars and no forks. Forks are not gameable in the
#: same way — someone has to actually take the code and use it. Adding
#: `forks:>3` removes the spam and leaves genuine projects: in testing it
#: cut the top results from a wall of identical malware-kit repos to real
#: software with real users.
GITHUB_FORK_FLOOR = 3

#: The minimum forks-per-star ratio for a repository to be trusted.
#:
#: The fork floor alone is not enough, because a fork *farm* satisfies it:
#: a spammer who mass-stars and mass-forks their own copies reaches any
#: absolute threshold. The ratio is what separates them from real software.
#: Measured on a sample, a star-farmed copy had 5 forks against 670 stars
#: (0.0075), while a genuine project had 594 forks against 8,829 stars
#: (0.067) — roughly nine times the ratio.
#:
#: Real projects sit at or above this. Popular utility libraries sit well
#: above it. The floor is set low enough to keep genuinely niche projects
#: that a small number of people forked.
GITHUB_MIN_FORK_RATIO = 0.02

#: The maximum number of topics a repository may carry and still be trusted.
#:
#: GitHub allows up to 20 topics, and keyword-stuffing all 20 is the
#: cheapest way to game a topic-based aggregator: every one of those tags
#: becomes a mention of a different topic. Measured on a live snapshot,
#: genuine repositories clustered at 1-3 topics while the stuffed ones sat
#: at 12-21. A repository with more topics than this is advertising, not
#: describing itself.
GITHUB_MAX_TOPICS = 8

#: How many repositories may share a name *stem* before the copies are
#: treated as a farm.
#:
#: The exact-name check misses the commoner form, where the same project is
#: reposted with a different suffix: `blender-ai-copilot-studio`,
#: `blender-ai-copilot-forge`, `blender-ai-copilot-flow`. Eight such
#: repositories appeared in one snapshot with 489-498 stars each — close
#: enough that the star counts gave them away. Stripping a trailing
#: suffix word and counting the stems catches them.
GITHUB_MAX_OWNERS_PER_REPO_STEM = 2

#: The trailing words that a farm swaps to produce "the same" repository
#: under a different name.
#:
#: Kept deliberately narrow. Words like "project", "repo" and "app" are
#: too common in genuine repository names to strip — doing so merged
#: unrelated projects that happened to end in one of them.
GITHUB_REPO_SUFFIXES = frozenset(
    """
    studio forge flow assets lab hub desk
    addon plugin
    edition lite plus pro max mini nano
    v2 v3
    """.split()
)

#: StackExchange tags to watch. On the StackExchange API a semicolon means
#: OR and a comma means AND, so this is a union — a question tagged `python`
#: or `rust` counts, not one tagged with every tag at once.
STACKOVERFLOW_TAGS = "python;rust;typescript;go;kubernetes;artificial-intelligence"

#: dev.to tags to watch.
DEVTO_TAGS = ("ai", "llm", "python", "javascript", "webdev", "devops")

#: The window that counts as "recent" for a burst. Items older than this
#: are context, not evidence of a trend.
#:
#: 72 hours rather than 48: the free APIs this radar reads publish on
#: roughly a daily-to-weekly cadence for most topics, so a 48-hour window
#: collects too few mentions of anything for the burst ratio to mean
#: anything. At 72 hours the recent window holds roughly ten times the
#: baseline window's per-day rate, which is enough for the comparison to
#: separate a genuine acceleration from noise.
RECENT_WINDOW_HOURS = 72

#: The baseline window used to measure acceleration. A burst is recent
#: activity divided by the preceding background rate.
BASELINE_WINDOW_HOURS = 168

#: How many items to ask each source for.
DEFAULT_LIMIT = 100

#: Engagement normalisation. Each platform's raw counter is squashed through
#: a log so that a 5000-point story does not erase every other signal, then
#: scaled by the platform's trust weight.
PLATFORM_WEIGHT: dict[str, float] = {
    "hackernews": 1.0,
    "github": 0.9,
    "stackoverflow": 0.8,
    "devto": 0.7,
    "youtube": 0.8,
    "rss": 0.6,
    "reddit": 0.7,
}

#: The log constant for engagement normalisation. Chosen so a post with
#: ~100 engagements lands near 1.0 across platforms.
ENGAGEMENT_LOG_BASE = 100.0

#: The embedding model used by the semantic topic matcher. Small, fast on
#: CPU, and open weights — the radar does not call a hosted API, so it
#: runs without a key and without a network once the weights are cached.
SEMANTIC_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

#: The similarity a title must reach against a technology's descriptor
#: before it counts as a mention. Measured on a probe set: titles about a
#: technology the vocabulary misses scored 0.40-0.63; titles about nothing
#: technical scored 0.10-0.11. The threshold sits in the gap.
SEMANTIC_THRESHOLD = 0.35

#: How many technologies one title may contribute to through the semantic
#: signal. A title that matches five technologies is not about five
#: technologies — it is matching nothing in particular.
SEMANTIC_MAX_MATCHES = 2


@dataclass(slots=True)
class Settings:
    """Runtime settings, resolved from the environment with safe defaults."""

    #: Sources to skip even if they are configured (e.g. no Reddit credentials).
    disabled_sources: tuple[str, ...] = ()
    #: Extra RSS feeds beyond the default set, from `TREND_RADAR_FEEDS`.
    extra_feeds: dict[str, str] = field(default_factory=dict)
    #: Reddit client credentials. Absent means the Reddit adapter stays off.
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "tech-trend-radar/0.1"
    limit: int = DEFAULT_LIMIT
    recent_window_hours: int = RECENT_WINDOW_HOURS
    baseline_window_hours: int = BASELINE_WINDOW_HOURS
    timeout_seconds: float = 20.0
    #: How many times to retry a rate-limited or transiently-failing request.
    max_retries: int = 2
    user_agent: str = "tech-trend-radar/0.1 (+https://github.com/)"
    #: Where snapshots are written and read from.
    snapshot_dir: Path = field(default_factory=lambda: SNAPSHOT_DIR)
    #: Whether the semantic topic matcher runs. Off means the radar uses
    #: the lexical signals alone, which is what happens when the embedding
    #: model is unavailable.
    semantic_enabled: bool = True
    #: The embedding model. Overridable so a different local model can be
    #: dropped in without a code change.
    semantic_model: str = SEMANTIC_MODEL_NAME
    semantic_threshold: float = SEMANTIC_THRESHOLD
    semantic_max_matches: int = SEMANTIC_MAX_MATCHES

    @property
    def reddit_enabled(self) -> bool:
        return bool(self.reddit_client_id and self.reddit_client_secret)

    def platform_weight(self, platform: str) -> float:
        return PLATFORM_WEIGHT.get(platform, 0.5)


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def load_settings() -> Settings:
    """Build settings from the environment.

    Every value has a working default, so this never raises and never needs
    a key to produce something useful.
    """
    extra: dict[str, str] = {}
    raw_feeds = _env("TREND_RADAR_FEEDS")
    if raw_feeds:
        # Format: name=url,name=url
        for chunk in raw_feeds.split(","):
            if "=" not in chunk:
                continue
            name, _, url = chunk.partition("=")
            name, url = name.strip(), url.strip()
            if name and url:
                extra[name] = url

    disabled = tuple(
        s.strip() for s in _env("TREND_RADAR_DISABLE").split(",") if s.strip()
    )

    return Settings(
        disabled_sources=disabled,
        extra_feeds=extra,
        reddit_client_id=_env("REDDIT_CLIENT_ID"),
        reddit_client_secret=_env("REDDIT_CLIENT_SECRET"),
        reddit_user_agent=_env("REDDIT_USER_AGENT", "tech-trend-radar/0.1"),
        limit=int(_env("TREND_RADAR_LIMIT", str(DEFAULT_LIMIT)) or DEFAULT_LIMIT),
        recent_window_hours=int(
            _env("TREND_RADAR_RECENT_HOURS", str(RECENT_WINDOW_HOURS)) or RECENT_WINDOW_HOURS
        ),
        baseline_window_hours=int(
            _env("TREND_RADAR_BASELINE_HOURS", str(BASELINE_WINDOW_HOURS)) or BASELINE_WINDOW_HOURS
        ),
        timeout_seconds=float(_env("TREND_RADAR_TIMEOUT", "20") or 20),
        max_retries=int(_env("TREND_RADAR_RETRIES", "2") or 2),
        semantic_enabled=_env("TREND_RADAR_NO_SEMANTIC") == "",
        semantic_model=_env("TREND_RADAR_SEMANTIC_MODEL", SEMANTIC_MODEL_NAME)
        or SEMANTIC_MODEL_NAME,
        semantic_threshold=float(
            _env("TREND_RADAR_SEMANTIC_THRESHOLD", str(SEMANTIC_THRESHOLD))
            or SEMANTIC_THRESHOLD
        ),
        semantic_max_matches=int(
            _env("TREND_RADAR_SEMANTIC_MAX_MATCHES", str(SEMANTIC_MAX_MATCHES))
            or SEMANTIC_MAX_MATCHES
        ),
    )


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
