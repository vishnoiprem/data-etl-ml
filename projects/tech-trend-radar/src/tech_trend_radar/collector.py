"""Running every adapter and collecting what came back.

The collector is the only place that talks to the network. Everything
downstream — topic extraction, burst detection, ranking, the API — works off
the collected `Post` list, which is also exactly what gets written to a
snapshot so the demo and the tests can run with no network at all.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .config import Settings, load_settings
from .http import HttpClient
from .models import FetchResult, Post
from .sources import build_adapters


@dataclass(slots=True)
class Snapshot:
    """A recorded collection run: the posts, and how each source fared.

    The snapshot is the seam between "live" and "offline". `make demo` and
    the test suite read snapshots; `make fetch` writes them.
    """

    fetched_at: datetime
    results: list[FetchResult] = field(default_factory=list)

    @property
    def posts(self) -> list[Post]:
        """Every post from every source that succeeded, de-duplicated.

        The same story can arrive from two adapters — a Hacker News link to a
        GitHub repo, say. De-duplication is by post id, which is derived from
        the platform and the platform's own id, so it never collapses two
        genuinely different items that share a title.
        """
        seen: set[str] = set()
        posts: list[Post] = []
        for result in self.results:
            for post in result.posts:
                key = post.id
                if key in seen:
                    continue
                seen.add(key)
                posts.append(post)
        return posts

    @property
    def ok_platforms(self) -> list[str]:
        return [r.platform for r in self.results if r.ok]

    @property
    def failed_platforms(self) -> list[str]:
        return [r.platform for r in self.results if not r.ok]

    def to_dict(self) -> dict:
        return {
            "fetched_at": self.fetched_at.isoformat(),
            "results": [r.to_dict() for r in self.results],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Snapshot:
        return cls(
            fetched_at=datetime.fromisoformat(data["fetched_at"]),
            results=[FetchResult.from_dict(r) for r in data.get("results", [])],
        )

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: Path) -> Snapshot:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def collect(settings: Settings | None = None) -> Snapshot:
    """Run every available adapter and return what came back.

    Sources are run in order, and each one is wrapped so that a failure is
    recorded rather than raised. The result is always a usable snapshot, even
    if every source failed.
    """
    settings = settings or load_settings()
    adapters = build_adapters(settings)
    results: list[FetchResult] = []

    with HttpClient(settings) as client:
        for adapter in adapters:
            results.append(adapter.run(client, settings))

    return Snapshot(fetched_at=datetime.now(timezone.utc), results=results)


def save_snapshot(snapshot: Snapshot, settings: Settings | None = None) -> Path:
    """Write a snapshot to a timestamped file under `data/snapshots/`."""
    settings = settings or load_settings()
    stamp = snapshot.fetched_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return snapshot.save(settings.snapshot_dir / f"snapshot_{stamp}.json")


def load_latest_snapshot(settings: Settings | None = None) -> Snapshot | None:
    """The most recent snapshot on disk, or None if there is none."""
    settings = settings or load_settings()
    directory = settings.snapshot_dir
    if not directory.exists():
        return None
    candidates = sorted(directory.glob("snapshot_*.json"))
    if not candidates:
        return None
    return Snapshot.load(candidates[-1])
