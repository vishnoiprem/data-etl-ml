"""
stream_seo.py — SEO content engine (Stream 1).

Pipeline:
  1. Find profitable keywords (volume, difficulty, intent).
  2. Pick the top N by expected ROI = (volume × cpc) / (1 + difficulty/10).
  3. Generate one long-form SEO article per keyword.
  4. Publish to a local `output/` dir as markdown (mock CMS).

Revenue model: pageviews × RPM / 1000. For info-niche sites, RPM
is $5–$30 with affiliate links. We don't actually traffic the pages
in the demo, but we record the *projected* monthly revenue per
article based on its target keyword's volume × a placeholder RPM,
so the ledger shows non-zero numbers end-to-end.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ledger import Ledger
from publisher import write_article
from router import LLMRouter


SEO_SYSTEM = """You are an SEO writer. Write 800-1200 word articles that:
- Open with a 1-2 sentence hook that names the reader's problem
- Use H2/H3 headings every 200-300 words
- Include at least one numbered list and one FAQ block
- End with a clear conclusion and a single CTA

Tone: direct, no fluff, no marketing speak. Target audience: smart
non-experts who want the answer in under 10 minutes."""


@dataclass
class Keyword:
    keyword: str
    volume: int             # monthly searches
    difficulty: int         # 0-100
    intent: str             # commercial | informational | comparison
    cpc_usd: float          # cost per click in USD

    @property
    def expected_monthly_usd(self) -> float:
        """Naive projection: assume we capture 5% of volume and earn
        $0.50 per click-through (between ad RPM and affiliate rev)."""
        return self.volume * 0.05 * 0.50


def discover_keywords(seed: str, router: LLMRouter, n: int = 10) -> list[Keyword]:
    prompt = (
        f"Seed: {seed}\n\n"
        f"Return {n} long-tail keyword ideas related to the seed. "
        f"Mix commercial and informational intent. Prefer low difficulty "
        f"(< 30) when possible. Include realistic monthly search volumes."
    )
    data = router.json(
        prompt,
        schema_hint='{"keywords": [{"keyword": str, "volume": int, '
                    '"difficulty": int, "intent": str, "cpc_usd": float}]}',
    )
    return [
        Keyword(
            keyword=k["keyword"],
            volume=int(k.get("volume", 0)),
            difficulty=int(k.get("difficulty", 50)),
            intent=k.get("intent", "informational"),
            cpc_usd=float(k.get("cpc_usd", 1.0)),
        )
        for k in data.get("keywords", [])
    ]


def rank_by_roi(keywords: list[Keyword], top: int = 5) -> list[Keyword]:
    """Highest expected ROI = (volume × cpc) / (1 + difficulty/10)."""
    def score(k: Keyword) -> float:
        return (k.volume * k.cpc_usd) / (1 + k.difficulty / 10)
    return sorted(keywords, key=score, reverse=True)[:top]


def write_article_for(kw: Keyword, router: LLMRouter) -> str:
    prompt = (
        f"Keyword: {kw.keyword}\n"
        f"Search intent: {kw.intent}\n"
        f"Title: The Ultimate Guide to {kw.keyword.title()}\n\n"
        f"Write the full article in markdown."
    )
    return router.complete(prompt, system=SEO_SYSTEM, max_tokens=1800)


def _slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:80] or "article"


def run(seed: str, router: LLMRouter, ledger: Ledger,
        output_dir: Path, top: int = 3, record_projected: bool = True) -> dict:
    """Run one pass of the SEO stream. Returns a small summary dict.

    Resilient to router/LLM errors: a failed keyword discovery
    returns an empty list; a failed article write skips that keyword
    rather than killing the whole pass. The 24/7 cron version relies
    on this not raising.
    """
    try:
        kws = discover_keywords(seed, router, n=max(top * 3, 10))
    except Exception as e:
        print(f"  [seo] discover_keywords failed: {e}")
        return {"stream": "seo", "seed": seed, "discovered": 0,
                "published": 0, "picks": [], "error": str(e)}
    picks = rank_by_roi(kws, top=top)

    published: list[tuple[Keyword, str]] = []
    for kw in picks:
        try:
            body = write_article_for(kw, router)
        except Exception as e:
            print(f"  [seo] article write failed for '{kw.keyword}': {e}")
            continue
        slug = _slugify(kw.keyword)
        url = write_article(output_dir, slug, kw.keyword, body)
        published.append((kw, url))
        if record_projected:
            # Project the *expected* monthly revenue from this one article.
            # The real number depends on rank; we record the optimistic case
            # (5% CTR) so the dashboard shows meaningful totals in demo mode.
            ledger.record(
                stream="seo",
                amount_usd=round(kw.expected_monthly_usd, 2),
                units=1,
                source=url,
                note=f"projected monthly — '{kw.keyword}' (vol {kw.volume}, KD {kw.difficulty})",
            )

    return {
        "stream": "seo",
        "seed": seed,
        "discovered": len(kws),
        "published": len(published),
        "picks": [
            {"keyword": k.keyword, "url": u, "expected_usd": round(k.expected_monthly_usd, 2)}
            for k, u in published
        ],
    }
