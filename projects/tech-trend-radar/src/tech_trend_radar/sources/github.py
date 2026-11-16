"""GitHub, via the public repository search API.

Search, not the events stream: the query is bounded by `created:` (recent
repositories only) and `stars:` (a noise floor). A topic that suddenly starts
producing heavily-starred new repositories is a burst. A topic that has been
big for years produces none, because its repositories were created long ago.

**The spam problem, and what this adapter does about it.**

GitHub stars are trivially gameable. A search for new repositories with
`stars:>20` returns dozens of star-farmed copies of the same project, each
with hundreds of stars, each carrying a spray of popular technology names
(`copilot`, `chatgpt`, `vue`, `openai`) in its topic list. Left alone, those
copies dominate the radar: they are numerous, they are recent, and they are
individually loud.

Three filters, in increasing cost:

1. **`stars:>20`** — the API-side noise floor.
2. **`forks:>3`** — an absolute fork floor. A spam repo that mass-stars but
   never gets forked drops out. This is free: it is part of the same query.
3. **Fork diversity** — the real filter. A genuine project is forked by many
   *different* people; a fork farm forks its own copies. So the top
   candidates are checked against the `/forks` endpoint and a repository
   whose forks all come from the same few accounts is dropped.

Filter 3 costs one request per candidate, so it runs only on the top of the
ranking — the repositories that would actually drive the trend list — rather
than on every result. Unauthenticated GitHub allows 60 core requests per
hour, which is enough for this and leaves the budget for the rest of the
project.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from ..config import (
    GITHUB_FORK_FLOOR,
    GITHUB_LOOKBACK_DAYS,
    GITHUB_MAX_OWNERS_PER_REPO_STEM,
    GITHUB_MAX_TOPICS,
    GITHUB_MIN_FORK_RATIO,
    GITHUB_REPO_SUFFIXES,
    GITHUB_STAR_FLOOR,
    Settings,
)
from ..http import HttpClient, normalise_engagement
from ..models import Post
from .base import BaseAdapter

SEARCH_URL = "https://api.github.com/search/repositories"
FORKS_URL = "https://api.github.com/repos/{full_name}/forks"

#: How many top candidates get the fork-diversity check. The check is one
#: request each, so this bounds the cost of the adapter.
FORK_CHECK_LIMIT = 25

#: How many forks to look at per repository when checking diversity.
FORK_SAMPLE_SIZE = 100

#: The minimum number of distinct accounts that must have forked a
#: repository for it to be considered genuine. Below this, the forks are a
#: farm.
MIN_FORK_OWNERS = 3

#: How many owners may publish the same repository name before the copies
#: are treated as a farm. A genuine project has one home, so more than a
#: couple of owners for the same name is a mass-repost operation.
MAX_OWNERS_PER_REPO_NAME = 2


def repo_stem(name: str) -> str:
    """The repository name with a swap-in-suffix word removed.

    A farm reposts one project under many names by swapping the last word:
    `blender-ai-copilot-studio`, `-forge`, `-flow`, `-hub`. The names
    differ, so an exact-name check misses them, but the stem is the same.

    Only the *trailing* word is stripped, and only when it is one of the
    known filler words. Stripping anything else would merge genuinely
    different projects that happen to share a prefix.
    """
    parts = [p for p in re.split(r"[-_.\s]+", name.strip().lower()) if p]
    if len(parts) > 1 and parts[-1] in GITHUB_REPO_SUFFIXES:
        parts = parts[:-1]
    return "-".join(parts)


def build_query(now: datetime | None = None) -> str:
    """The GitHub search query for newly-created, already-starred repos.

    The date has to be absolute. GitHub's search syntax accepts
    `created:>YYYY-MM-DD` but silently returns zero results for relative
    dates such as `created:>30-days-ago` — which looks like "no trends
    right now" rather than "your query was wrong".

    The fork floor is there to filter out the cheapest spam. See
    `GITHUB_FORK_FLOOR` for the reasoning.
    """
    reference = now or datetime.now(timezone.utc)
    since = (reference - timedelta(days=GITHUB_LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    return f"created:>{since} stars:>{GITHUB_STAR_FLOOR} forks:>{GITHUB_FORK_FLOOR}"


class GitHubAdapter(BaseAdapter):
    """Newly-created repositories that are already getting attention."""

    name = "github"

    def fetch(self, client: HttpClient, settings: Settings) -> list[Post]:
        data = client.get_json(
            SEARCH_URL,
            params={
                "q": build_query(),
                "sort": "stars",
                "order": "desc",
                "per_page": min(settings.limit, 100),
            },
            headers={"Accept": "application/vnd.github+json"},
        )

        repos = data.get("items", [])
        candidates = self._prefilter(repos)
        verified = self._verify_fork_diversity(client, candidates)

        weight = settings.platform_weight(self.name)
        posts: list[Post] = []

        for repo in verified:
            post = self._to_post(repo, weight)
            if post is not None:
                posts.append(post)
        return posts

    @staticmethod
    def _prefilter(repos: list[dict]) -> list[dict]:
        """Drop the obvious spam before spending requests on fork checks.

        Two signals, both free — they read from data the search response
        already contains.

        **Duplicate repository names.** The clearest tell in this dataset:
        `GitHub-Copilot-app`, `ai--manus2.0` and `IPTV_Player_2.0` each
        appear twenty or more times under different owner accounts, each
        with ~660 stars. A genuine project has one home. When the same
        repository name shows up under several owners, the copies are a
        farm, and only one of them can be the real project — so all of them
        go, rather than letting twenty copies each contribute a mention.

        **Star-to-fork ratio.** A repository with a lot of stars and almost
        no forks is being star-farmed. Genuine projects accumulate forks at
        a much higher rate, because a fork means someone took the code and
        used it. Measured on a sample, a star-farmed copy had 5 forks
        against 670 stars while a genuine project had 594 forks against
        8,829 stars.

        Repositories with few stars skip the ratio test — at that scale the
        ratio is noisy and the API-side star floor already did the work.

        **Name stems.** The exact-name check misses the commoner form,
        where one project is reposted under many names by swapping the
        last word. A live snapshot held nine `blender-ai-copilot-*`
        repositories with 489-498 stars each — the same project, nine
        times. Stripping a known filler suffix and counting the stems
        catches them.

        **Topic stuffing.** GitHub allows 20 topics, and filling them is
        the cheapest way to game a topic aggregator: every tag becomes a
        mention of a different topic, so one stuffed repository reports
        itself as twenty different trends. Genuine repositories in the
        same snapshot carried 1-3 topics; the stuffed ones carried 12-21.
        A repository over the topic cap is advertising, not describing
        itself, and is dropped outright.
        """
        name_counts: dict[str, int] = {}
        stem_counts: dict[str, int] = {}
        for repo in repos:
            name = (repo.get("name") or "").strip().lower()
            if name:
                name_counts[name] = name_counts.get(name, 0) + 1
                stem = repo_stem(name)
                stem_counts[stem] = stem_counts.get(stem, 0) + 1

        kept: list[dict] = []
        for repo in repos:
            name = (repo.get("name") or "").strip().lower()
            if name and name_counts.get(name, 0) > MAX_OWNERS_PER_REPO_NAME:
                continue

            stem = repo_stem(name) if name else ""
            if stem and stem_counts.get(stem, 0) > GITHUB_MAX_OWNERS_PER_REPO_STEM:
                continue

            topics = repo.get("topics") or []
            if len(topics) > GITHUB_MAX_TOPICS:
                continue

            stars = float(repo.get("stargazers_count") or 0)
            forks = float(repo.get("forks_count") or 0)
            if stars >= 100 and (forks / stars) < GITHUB_MIN_FORK_RATIO:
                continue
            kept.append(repo)
        return kept

    def _verify_fork_diversity(self, client: HttpClient, repos: list[dict]) -> list[dict]:
        """Check that the top candidates are forked by many different people.

        A repository whose forks all come from the same handful of accounts
        is a fork farm. A repository forked by dozens of distinct accounts
        is real software.

        The check is skipped for repositories with too few forks to judge:
        at that scale there is not enough evidence either way, and the
        repository might legitimately be new.
        """
        verified: list[dict] = []

        for index, repo in enumerate(repos):
            if index >= FORK_CHECK_LIMIT:
                verified.extend(repos[index:])
                break

            full_name = repo.get("full_name") or ""
            fork_count = int(repo.get("forks_count") or 0)
            if fork_count < 5 or not full_name:
                verified.append(repo)
                continue

            try:
                forks = client.get_json(
                    FORKS_URL.format(full_name=full_name),
                    params={"per_page": FORK_SAMPLE_SIZE, "sort": "newest"},
                    headers={"Accept": "application/vnd.github+json"},
                )
            except Exception:  # noqa: BLE001 - a failed check must not drop a real repo
                verified.append(repo)
                continue

            if not isinstance(forks, list):
                verified.append(repo)
                continue

            owners = {
                (fork.get("owner") or {}).get("login")
                for fork in forks
                if (fork.get("owner") or {}).get("login")
            }
            if len(owners) >= MIN_FORK_OWNERS:
                verified.append(repo)
            else:
                repo = dict(repo)
                repo["_fork_farm"] = True

        return verified

    def _to_post(self, repo: dict, weight: float) -> Post | None:
        title = (repo.get("name") or "").strip()
        description = (repo.get("description") or "").strip()
        if not title:
            return None

        created = repo.get("created_at")
        published = (
            datetime.fromisoformat(created.replace("Z", "+00:00"))
            if created
            else datetime.now(timezone.utc)
        )

        stars = float(repo.get("stargazers_count") or 0)
        forks = float(repo.get("forks_count") or 0)
        raw = stars + forks * 2.0

        owner = repo.get("owner") or {}
        tags = tuple(repo.get("topics") or [])
        language = repo.get("language")
        if language:
            tags = tags + (language.lower(),)

        return Post(
            platform=self.name,
            native_id=str(repo.get("full_name") or repo.get("id")),
            title=title,
            published=published,
            weight=normalise_engagement(raw, weight),
            raw_engagement=raw,
            url=repo.get("html_url") or "",
            author=owner.get("login") or "",
            tags=tags,
            description=description,
            extra={
                "stars": int(stars),
                "forks": int(forks),
                "fork_ratio": round(forks / stars, 5) if stars else 0.0,
                "language": language,
                "topics": list(repo.get("topics") or []),
                "fork_farm": bool(repo.get("_fork_farm")),
            },
        )
