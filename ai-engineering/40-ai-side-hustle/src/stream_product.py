"""
stream_product.py — Digital product factory (Stream 3).

Pipeline:
  1. Generate 3 product ideas for a topic (eBook, template, printable).
  2. For each, draft the actual content (a 4-chapter eBook body,
     a Notion-style template spec, a one-page printable PDF stub).
  3. Write the deliverable to `output/products/<slug>/`.
  4. Record a "first month" sales projection (10 sales × price).

This stream has the fastest time-to-first-dollar: list the eBook on
Gumroad this afternoon, share the link on Twitter, expect a sale
within 24-72 hours if the topic has any audience demand.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ledger import Ledger
from publisher import write_file
from router import LLMRouter


EBOOK_SYSTEM = """You are a non-fiction author. Write 3-chapter eBooks that:
- Open with a 1-paragraph problem statement
- Each chapter is 200-300 words and ends with a checklist or action step
- Use plain language, no jargon, no academic tone
- Include a short "Resources" section at the end

Tone: friendly, direct, slightly opinionated. The reader should
finish it in 15 minutes and have 3 things to do this week."""


@dataclass
class Product:
    title: str
    format: str             # ebook | template | printable
    price_usd: int
    page_count: int
    hook: str

    @property
    def expected_month1_usd(self) -> float:
        # Realistic month-1: 10 sales for a fresh listing
        return 10 * self.price_usd

    @property
    def slug(self) -> str:
        s = re.sub(r"[^a-z0-9]+", "-", self.title.lower()).strip("-")
        return s[:60] or "product"


def discover_products(topic: str, router: LLMRouter, n: int = 3) -> list[Product]:
    prompt = (
        f"Topic: {topic}\n\n"
        f"Generate {n} digital product ideas for this topic. Mix formats: "
        f"at least one eBook, one template/Notion bundle, one printable. "
        f"Price range $7–$49. Each must have a clear hook (one sentence)."
    )
    data = router.json(
        prompt,
        schema_hint='{"products": [{"title": str, "format": str, '
                    '"price_usd": int, "page_count": int, "hook": str}]}',
    )
    return [
        Product(
            title=p["title"],
            format=p.get("format", "ebook"),
            price_usd=int(p.get("price_usd", 19)),
            page_count=int(p.get("page_count", 25)),
            hook=p.get("hook", ""),
        )
        for p in data.get("products", [])
    ]


def write_ebook(product: Product, router: LLMRouter) -> str:
    prompt = (
        f"Title: {product.title}\n"
        f"Hook: {product.hook}\n"
        f"Target: {product.page_count} pages\n\n"
        f"Write the full eBook body in markdown (3 chapters + intro + resources)."
    )
    return router.complete(prompt, system=EBOOK_SYSTEM, max_tokens=1400)


def write_template_spec(product: Product) -> str:
    """Notion/Sheets templates don't need LLM generation; we describe
    the template structure as YAML so a human can build it in 30 min."""
    return (
        f"# {product.title}\n\n"
        f"> {product.hook}\n\n"
        f"## Includes\n"
        f"- 1 master dashboard (Notion database)\n"
        f"- 3 sub-pages (weekly review, monthly goals, archive)\n"
        f"- 12 pre-filled example entries\n"
        f"- 1 quick-start video (link TBD)\n\n"
        f"## How to use\n"
        f"1. Duplicate the Notion template into your workspace.\n"
        f"2. Fill in the 12 example entries with your own data.\n"
        f"3. Use the weekly review page every Friday.\n"
    )


def write_printable(product: Product) -> str:
    """Printables are designed to be exported as PDF; here we just
    write the visual spec so a designer can drop it into Canva."""
    return (
        f"# {product.title} (Printable)\n\n"
        f"> {product.hook}\n\n"
        f"## Layout\n"
        f"- 1 page, US Letter (8.5\" x 11\")\n"
        f"- Top half: large 1-line action prompt\n"
        f"- Middle: 7-day tracker grid\n"
        f"- Bottom: 1-paragraph motivational note\n\n"
        f"## Color palette\n"
        f"- Background: #FAFAF7 (warm off-white)\n"
        f"- Accent: #2E5A4C (forest green)\n"
        f"- Text: #1A1A1A (near-black)\n"
    )


def build_product(product: Product, router: LLMRouter, output_dir: Path) -> Path:
    root = output_dir / "products" / product.slug
    root.mkdir(parents=True, exist_ok=True)

    if product.format == "ebook":
        body = write_ebook(product, router)
        write_file(root, "ebook.md", body)
    elif product.format == "template":
        write_file(root, "template.md", write_template_spec(product))
    else:  # printable
        write_file(root, "printable.md", write_printable(product))

    # Always include a Gumroad-ready listing description
    write_file(root, "listing.md", _listing(product))
    return root


def _listing(p: Product) -> str:
    return (
        f"# {p.title}\n\n"
        f"**${p.price_usd}**\n\n"
        f"{p.hook}\n\n"
        f"## What you get\n"
        f"- The {p.format} itself ({p.page_count} pages or equivalent)\n"
        f"- A 1-page quick-start guide\n"
        f"- Lifetime updates\n\n"
        f"## Who this is for\n"
        f"You, if you've been thinking about this for more than 30 seconds.\n"
    )


def run(topic: str, router: LLMRouter, ledger: Ledger,
        output_dir: Path, record_projected: bool = True) -> dict:
    try:
        products = discover_products(topic, router, n=3)
    except Exception as e:
        print(f"  [product] discover_products failed: {e}")
        return {"stream": "product", "topic": topic, "products": [],
                "error": str(e)}
    built: list[dict] = []
    for p in products:
        try:
            path = build_product(p, router, output_dir)
        except Exception as e:
            print(f"  [product] build failed for {p.title}: {e}")
            continue
        if record_projected:
            ledger.record(
                stream="product",
                amount_usd=round(p.expected_month1_usd, 2),
                units=10,
                source=str(path),
                note=f"projected month-1 — {p.title} @ ${p.price_usd}",
            )
        built.append({
            "title": p.title,
            "format": p.format,
            "price_usd": p.price_usd,
            "expected_month1_usd": round(p.expected_month1_usd, 2),
            "path": str(path),
        })

    return {
        "stream": "product",
        "topic": topic,
        "products": built,
    }
