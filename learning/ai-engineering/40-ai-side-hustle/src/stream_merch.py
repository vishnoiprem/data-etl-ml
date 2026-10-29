"""
stream_merch.py — Print-on-demand merch stream (Stream 4).

Pipeline:
  1. Pick a trending topic (e.g. "ai agents").
  2. Generate 3 niche merch ideas (t-shirt slogans, mug designs,
     sticker packs) that a designer could ship to Redbubble/Merch
     by Amazon in under an hour.
  3. Write the listing copy for each.
  4. Record a projected revenue based on Merch-by-Amazon royalty
     rates (~$4–$7 per shirt sale, ~200 organic impressions/day).

Why merch?  It's the lowest-effort stream of the four:
  - No inventory (print-on-demand)
  - No audience required (Amazon's organic traffic is the audience)
  - Royalty is a check every month
  - 5–10 minutes of design time per product

The catch: you need a designer to make the actual artwork. The
stream here generates the *concept* + *listing copy* + *projected
royalty*, which is the part the AI can do.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ledger import Ledger
from projections import StreamProjection, project_product
from publisher import write_file
from router import LLMRouter


MERCH_SYSTEM = """You are a merch copywriter for print-on-demand stores
(Redbubble, Merch by Amazon, TeePublic). Generate catchy slogans +
short design briefs that designers can execute in 30 minutes.

Constraints:
- No copyrighted characters, brands, or trademarks
- 4–8 words for the slogan (fits on a t-shirt)
- Audience: tech workers / indie hackers / data scientists
- Tone: clever, slightly self-deprecating, not corny"""


@dataclass
class MerchIdea:
    slogan: str
    format: str             # t-shirt | mug | sticker | poster
    audience: str
    designer_brief: str

    @property
    def slug(self) -> str:
        s = re.sub(r"[^a-z0-9]+", "-", self.slogan.lower()).strip("-")
        return s[:50] or "merch"

    @property
    def projection(self) -> StreamProjection:
        # Merch-by-Amazon royalty: ~$4.50 per shirt. 1.5% conversion
        # on 200 impressions/day for a fresh listing.
        royalty = 4.50 if self.format == "t-shirt" else 2.50
        return project_product(price_usd=int(royalty),
                                impressions_per_day=200, conversion_rate=0.015)


def discover_merch(topic: str, router: LLMRouter, n: int = 3) -> list[MerchIdea]:
    prompt = (
        f"Topic: {topic}\n\n"
        f"Generate {n} merch ideas. Each must have a catchy slogan, a "
        f"format (t-shirt / mug / sticker / poster), a 1-sentence "
        f"audience description, and a 1-paragraph designer brief."
    )
    data = router.json(
        prompt,
        schema_hint='{"merch": [{"slogan": str, "format": str, '
                    '"audience": str, "designer_brief": str}]}',
    )
    return [
        MerchIdea(
            slogan=m["slogan"],
            format=m.get("format", "t-shirt"),
            audience=m.get("audience", ""),
            designer_brief=m.get("designer_brief", ""),
        )
        for m in data.get("merch", [])
    ]


def build_listing(idea: MerchIdea) -> str:
    return (
        f"# {idea.slogan}\n\n"
        f"**Format:** {idea.format}\n"
        f"**Audience:** {idea.audience}\n\n"
        f"## Design brief\n\n{idea.designer_brief}\n\n"
        f"## Tags\n"
        f"`{idea.format}`, `indie hacker`, `data nerd`, `programmer humor`\n"
    )


def run(topic: str, router: LLMRouter, ledger: Ledger,
        output_dir: Path, record_projected: bool = True) -> dict:
    try:
        ideas = discover_merch(topic, router, n=3)
    except Exception as e:
        print(f"  [merch] discover_merch failed: {e}")
        return {"stream": "merch", "topic": topic, "ideas": [],
                "error": str(e)}

    built: list[dict] = []
    for idea in ideas:
        try:
            root = output_dir / "merch" / idea.slug
            root.mkdir(parents=True, exist_ok=True)
            write_file(root, "listing.md", build_listing(idea))
        except Exception as e:
            print(f"  [merch] build failed for {idea.slogan}: {e}")
            continue
        if record_projected:
            ledger.record(
                stream="merch",
                amount_usd=round(idea.projection.base, 2),
                units=int(idea.projection.assumptions["expected_sales"]),
                source=str(root),
                note=f"projected month-1 — '{idea.slogan}' ({idea.format})",
            )
        built.append({
            "slogan": idea.slogan,
            "format": idea.format,
            "expected_month1_usd": round(idea.projection.base, 2),
            "path": str(root),
        })

    return {
        "stream": "merch",
        "topic": topic,
        "ideas": built,
    }
