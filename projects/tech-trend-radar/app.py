"""The Tech Trend Radar API.

Six endpoints over one service:

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Status, source coverage, corpus size |
| GET | `/trends` | The ranked trends, with their evidence |
| GET | `/topics/{topic}` | One topic in detail |
| GET | `/sources` | Which sources are configured and which are live |
| POST | `/refresh` | Collect fresh data and re-rank |
| GET | `/report` | The trend report as markdown |

The service is a module-level singleton so the corpus is collected once at
startup rather than once per request — a radar that re-scrapes the world
on every poll is a radar nobody can afford to run.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from tech_trend_radar.collector import (
    Snapshot,
    collect,
    load_latest_snapshot,
    save_snapshot,
)
from tech_trend_radar.config import Settings, load_settings
from tech_trend_radar.ranking import Trend, build_trends, explain
from tech_trend_radar.semantic import SemanticMatcher, build_matcher
from tech_trend_radar.sources import build_adapters

#: The snapshot directory, resolved relative to the project so the app works
#: from any working directory.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT_DIR = os.path.join(PROJECT_ROOT, "data", "snapshots")


class RadarService:
    """Holds the current snapshot and the trends computed from it."""

    #: Class-level defaults so a service built without `__init__` — the
    #: tests do this to inject a synthetic corpus — still has a usable
    #: matcher property.
    _matcher: SemanticMatcher | None = None
    _matcher_built: bool = False

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings()
        self.snapshot: Snapshot | None = None
        self.trends: list[Trend] = []
        self.collected_at: datetime | None = None
        self._matcher: SemanticMatcher | None = None
        self._matcher_built = False
        self.refresh()

    @property
    def matcher(self) -> SemanticMatcher | None:
        """The semantic matcher, built once and reused.

        None when the embedding model is unavailable, in which case the
        radar runs on the lexical signals alone. The build is lazy so that
        constructing a service does not pay for the model unless something
        actually ranks with it.
        """
        if not self._matcher_built:
            self._matcher = build_matcher(self.settings)
            self._matcher_built = True
        return self._matcher

    def refresh(self) -> None:
        """Collect from the live sources, or fall back to the last snapshot.

        The fallback matters: the API has to work in an environment with no
        network — a CI run, a laptop on a train. If the live collection
        fails entirely and a snapshot exists, the snapshot is used and the
        fact is reported through `/health`.
        """
        snapshot = collect(self.settings)
        if snapshot.posts:
            self.snapshot = snapshot
            self.collected_at = snapshot.fetched_at
            try:
                save_snapshot(snapshot, self.settings)
            except OSError:
                pass
        else:
            fallback = load_latest_snapshot(self.settings)
            if fallback is not None:
                self.snapshot = fallback
                self.collected_at = fallback.fetched_at
        self.recompute()

    def recompute(self) -> None:
        """Re-rank the current snapshot."""
        if self.snapshot is None:
            self.trends = []
            return
        self.trends = build_trends(
            self.snapshot.posts, self.settings, semantic=self.matcher
        )

    @property
    def posts(self) -> list:
        return self.snapshot.posts if self.snapshot else []

    def health(self) -> dict[str, Any]:
        snapshot = self.snapshot
        adapters = build_adapters(self.settings)
        return {
            "status": "ok" if snapshot and snapshot.posts else "no-data",
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "post_count": len(self.posts),
            "topic_count": len(self.trends),
            "sources": {
                "configured": [a.name for a in adapters],
                "live": snapshot.ok_platforms if snapshot else [],
                "failed": snapshot.failed_platforms if snapshot else [],
            },
            "windows": {
                "recent_hours": self.settings.recent_window_hours,
                "baseline_hours": self.settings.baseline_window_hours,
            },
            "semantic": {
                "enabled": self.matcher is not None,
                "model": self.settings.semantic_model,
                "threshold": self.settings.semantic_threshold,
                "reason": self.matcher.reason if self.matcher is not None else "unavailable",
            },
        }


app = FastAPI(
    title="Tech Trend Radar",
    description=(
        "Finds trending technology topics across several developer communities "
        "by measuring acceleration rather than volume."
    ),
    version="0.1.0",
)

#: The service instance. Created at import so the API has data to serve.
service = RadarService()


@app.get("/health")
def health() -> dict[str, Any]:
    """Status and coverage."""
    return service.health()


@app.get("/sources")
def sources() -> dict[str, Any]:
    """Which sources are configured, and how each fared on the last run."""
    snapshot = service.snapshot
    results = snapshot.results if snapshot else []
    return {
        "configured": [a.name for a in build_adapters(service.settings)],
        "results": [
            {
                "platform": r.platform,
                "ok": r.ok,
                "error": r.error,
                "post_count": len(r.posts),
                "duration_ms": round(r.duration_ms, 2),
                "fetched_at": r.fetched_at.isoformat(),
            }
            for r in results
        ],
    }


@app.get("/trends")
def trends(
    limit: int = Query(default=20, ge=1, le=100),
    platform: str | None = Query(default=None),
    min_score: float = Query(default=0.0, ge=0.0),
) -> dict[str, Any]:
    """The ranked trends."""
    selected = service.trends
    if platform:
        selected = [t for t in selected if platform in t.platforms]
    if min_score:
        selected = [t for t in selected if t.score >= min_score]
    selected = selected[:limit]
    return {
        "count": len(selected),
        "total_trends": len(service.trends),
        "trends": [t.to_dict() for t in selected],
    }


@app.get("/topics/{topic}")
def topic_detail(topic: str) -> dict[str, Any]:
    """One topic in detail, with the posts that support it."""
    for trend in service.trends:
        if trend.topic.lower() == topic.lower():
            posts = [
                p.to_dict()
                for p in service.posts
                if trend.topic in _topics_of(p)
            ]
            return {
                "topic": trend.to_dict(),
                "posts": posts[:20],
                "post_count": len(posts),
            }
    raise HTTPException(status_code=404, detail=f"No topic named {topic!r} in the current trends.")


@app.post("/refresh")
def refresh() -> dict[str, Any]:
    """Collect fresh data and re-rank."""
    service.refresh()
    return service.health()


@app.get("/report")
def report(limit: int = Query(default=15, ge=1, le=50)) -> dict[str, Any]:
    """The trend report, as markdown."""
    lines = [
        "# Tech Trend Radar",
        "",
        f"Collected: {service.collected_at.isoformat() if service.collected_at else 'n/a'}",
        f"Posts: {len(service.posts)}  |  Sources: "
        f"{', '.join(service.snapshot.ok_platforms) if service.snapshot else 'none'}",
        "",
    ]
    for trend in service.trends[:limit]:
        lines.append(explain(trend))
        lines.append("")
    return {"markdown": "\n".join(lines), "count": min(limit, len(service.trends))}


def _topics_of(post) -> list[str]:
    """The topics of one post, using the same extraction the radar used."""
    from tech_trend_radar.burst import attach_topics

    drafts = attach_topics([post], semantic=service.matcher)
    return drafts[0].topics if drafts else []


class RefreshRequest(BaseModel):
    """The body of a refresh request."""

    confirm: bool = Field(
        default=True,
        description="Refresh hits the live APIs. Set false for a dry run.",
    )
