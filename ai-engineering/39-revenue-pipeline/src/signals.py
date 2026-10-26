"""
signals.py — 6 source-specific lead ingestion modules.

Each scraper returns a list of `Lead` dicts (raw, not yet qualified).
A `Lead` has at minimum:
  - source: str       ("hn_hiring", "github_trending", ...)
  - company: str
  - title: str        (the role or signal description)
  - url: str
  - text: str         (the JD / context — used by the qualifier)
  - posted_at: str    (ISO date or relative time)
  - contact: str | None  (email or "@handle" if known)

The default sources are pluggable — each `scrape_*` function is
independent and can be removed/swapped without touching the others.
For the demo, all scrapers use sample data so the project runs offline.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable


@dataclass
class Lead:
    source: str
    company: str
    title: str
    url: str
    text: str
    posted_at: str
    contact: str | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def fingerprint(self) -> str:
        """Stable dedup key: source + (company or domain) + lowercased title."""
        co = (self.company or "").lower().strip()
        title = re.sub(r"\W+", " ", (self.title or "").lower()).strip()[:60]
        return f"{self.source}|{co}|{title}"


# ============================================================
# Sample-data-backed scrapers. Each one is offline-safe for the
# demo. To switch to live data, replace the body of each function
# with a real scraper (requests.get + parse). The function
# signature stays the same.
# ============================================================
def scrape_hn_hiring() -> list[Lead]:
    """HN 'Who's hiring?' monthly threads + hnhiring.com."""
    # Real impl would: requests.get(hnhiring.com/locations/remote) + parse
    return _from_sample("hn_hiring")


def scrape_job_boards() -> list[Lead]:
    """WWR, RemoteOK, YC Work at a Startup, Wellfound."""
    return _from_sample("job_boards")


def scrape_github_trending() -> list[Lead]:
    """Trending repos in AI/data — companies actively shipping signal hiring intent."""
    return _from_sample("github_trending")


def scrape_funding_news() -> list[Lead]:
    """Crunchbase / TechCrunch funding rounds → company just got $, will spend on infra."""
    return _from_sample("funding_news")


def scrape_cfp_rfp() -> list[Lead]:
    """Conference CFPs (paid) and government RFPs."""
    return _from_sample("cfp_rfp")


def scrape_inbound() -> list[Lead]:
    """Anything you manually pasted into `inbox/` (LinkedIn DMs, email forwards)."""
    return _from_sample("inbound")


SCRAPERS: dict[str, Callable[[], list[Lead]]] = {
    "hn_hiring": scrape_hn_hiring,
    "job_boards": scrape_job_boards,
    "github_trending": scrape_github_trending,
    "funding_news": scrape_funding_news,
    "cfp_rfp": scrape_cfp_rfp,
    "inbound": scrape_inbound,
}


def ingest_all() -> list[Lead]:
    """Run every scraper, dedupe by fingerprint, return combined list."""
    seen: set[str] = set()
    out: list[Lead] = []
    for name, fn in SCRAPERS.items():
        try:
            for ld in fn():
                if ld.fingerprint not in seen:
                    seen.add(ld.fingerprint)
                    out.append(ld)
        except Exception as e:  # don't let one bad scraper kill the loop
            print(f"  [{name}] scrape error: {e}")
    return out


# ============================================================
# Sample-data helpers (offline-safe demo)
# ============================================================
SAMPLE_FILE = Path(__file__).resolve().parent.parent / "sample_data" / "signals.json"


def _from_sample(source: str) -> list[Lead]:
    if not SAMPLE_FILE.exists():
        return []
    data = json.loads(SAMPLE_FILE.read_text())
    raw = data.get(source, [])
    return [
        Lead(
            source=source,
            company=r.get("company", "Unknown"),
            title=r.get("title", ""),
            url=r.get("url", ""),
            text=r.get("text", ""),
            posted_at=r.get("posted_at", datetime.now(timezone.utc).isoformat()),
            contact=r.get("contact"),
            tags=r.get("tags", []),
        )
        for r in raw
    ]


def write_sample_data() -> None:
    """Idempotent: write the bundled sample_data/signals.json if missing."""
    if SAMPLE_FILE.exists():
        return
    SAMPLE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SAMPLE_FILE.write_text(json.dumps(_SAMPLE_SIGNALS, indent=2))


# ============================================================
# Bundled sample data — 12 leads, mix of high/low quality signals.
# Used by `make demo` and the test suite.
# ============================================================
_SAMPLE_SIGNALS: dict[str, list[dict]] = {
    "hn_hiring": [
        {
            "company": "Series B fintech",
            "title": "Senior AI Engineer — LLM agents for KYC automation",
            "url": "https://hnhiring.com/locations/remote",
            "text": (
                "Series B fintech (well-funded, $40M raised) hiring a senior "
                "AI engineer for LLM agent work — KYC document parsing, "
                "compliance Q&A. Need someone ASAP for a 3-month engagement. "
                "Budget approved. Stack: Python, LangChain, Postgres, AWS."
            ),
            "posted_at": "2026-10-12",
            "tags": ["ai", "llm", "rag", "agent", "urgent", "budget"],
        },
        {
            "company": "Mid-stage healthtech",
            "title": "ML platform engineer — feature store + MLflow",
            "url": "https://hnhiring.com/locations/remote",
            "text": (
                "Hiring an ML platform engineer to set up our feature store "
                "and migrate off a hacky Airflow setup. Series A, 80 people, "
                "remote US. Not urgent, this quarter."
            ),
            "posted_at": "2026-10-10",
            "tags": ["data", "mlops", "feature-store"],
        },
        {
            "company": "Pre-seed startup",
            "title": "Junior data scientist",
            "url": "https://hnhiring.com/locations/remote",
            "text": (
                "Pre-seed, looking for a junior data scientist to help with "
                "basic analytics and dashboards. Equity-only at this stage."
            ),
            "posted_at": "2026-10-09",
            "tags": ["junior", "entry", "no-budget"],
        },
    ],
    "job_boards": [
        {
            "company": "Stripe",
            "title": "Staff ML Engineer — Fraud ML",
            "url": "https://stripe.com/jobs",
            "text": (
                "Staff-level ML engineer for our fraud detection team. "
                "Permanent role, but we've also engaged consultants for "
                "specific Q4 projects. Series-stage equivalent comp. Approved "
                "budget, looking to start in 4 weeks."
            ),
            "posted_at": "2026-10-11",
            "tags": ["ai", "ml", "budget"],
        },
    ],
    "github_trending": [
        {
            "company": "Anthropic",
            "title": "Repo 'computer-use-agents' trending — they're staffing",
            "url": "https://github.com/anthropics/computer-use-agents",
            "text": (
                "New public repo from a well-funded AI lab, trending on HN. "
                "Strong signal they're building an internal team — a "
                "consultant with eval harness experience would be relevant."
            ),
            "posted_at": "2026-10-12",
            "tags": ["ai", "agent", "eval"],
        },
    ],
    "funding_news": [
        {
            "company": "Robust Intelligence",
            "title": "Raised $30M Series B — will spend on AI infra",
            "url": "https://news.example/robust-raised",
            "text": (
                "AI safety startup just closed $30M Series B. Typically "
                "allocate 10-20% to consulting/contractor spend in Y2. Strong "
                "intent signal — they need to ship fast to hit milestones."
            ),
            "posted_at": "2026-10-08",
            "tags": ["ai", "budget", "funded"],
        },
    ],
    "cfp_rfp": [
        {
            "company": "Strata Data Conference",
            "title": "Paid speaking slot — 'Production RAG' talk",
            "url": "https://strata.example/cfp",
            "text": (
                "Conference CFP for Strata 2027 — paid speaking slots for "
                "production-ready AI/data talks. $5k honorarium + travel. "
                "Good for building public profile + inbound leads."
            ),
            "posted_at": "2026-10-05",
            "tags": ["speaking", "profile"],
        },
    ],
    "inbound": [
        {
            "company": "Acme Pharma",
            "title": "DM from founder — needs help with RAG over FDA docs",
            "url": "https://linkedin.com/in/example",
            "text": (
                "Inbound DM from founder: 'Saw your RAG write-up, need help "
                "standing up a RAG system over our 50k FDA documents for an "
                "audit next month. Series A, $8M raised. Budget approved, "
                "ASAP start.'"
            ),
            "posted_at": "2026-10-12",
            "contact": "@founder-acme",
            "tags": ["ai", "rag", "urgent", "budget", "funded"],
        },
    ],
}