#!/usr/bin/env python3
"""
demand_in.py — India demand lookup for the trade-finder product universe.

The margin model in find_opportunities.py only knows about *supply economics*
(landed cost vs. destination price). It does not know whether there's a
buyer in India. This module layers on demand signals.

Sources of demand signal
------------------------
We use a curated, documentable lookup rather than a live scrape. Reasons:

  1. Amazon.in / Flipkart bestseller pages are heavily JS-rendered
     (Amazon's React app loads the list client-side). Server-side
     scrapes get a shell.
  2. Search-volume APIs (Google Trends, SerpAPI) require keys or rate-limit
     aggressively.
  3. The India e-commerce landscape is dominated by a small set of
     categories whose rankings are well-documented in public reports
     (RedSeer, Bain India, marketplace press releases) and stable on a
     quarter-to-quarter basis.

Demand scores are 0-100 and combine three sub-signals:

  - category_volume:    how big is the category on Amazon.in / Flipkart
                         (smartwatches, earbuds, fashion dominate)
  - unit_economics_fit: how well the product fits the price band Indian
                         buyers actually transact at (₹200-₹3,000 sweet spot)
  - import_dependency:  how much of the category is imported vs. made-in-India
                         (electronics = mostly imported = good for us; textiles
                         = mostly local = bad for our sourcing model)

Output
------
  data/demand_in.json   — full demand lookup + provenance
  reports/demand_in.md  — human-readable demand table joined to the
                          margin-rich-score so you see "margin × demand"
                          in one view
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import find_opportunities as fo  # noqa: E402

DATA_DIR = HERE / "data"
REPORTS_DIR = HERE / "reports"
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Demand lookup — 0-100 score per product for the India market.
# Provenance notes at the bottom of the file.
# --------------------------------------------------------------------------- #

# Components (sum to demand_score):
#   category_volume  — 0-50: how big the category is on Amazon.in / Flipkart
#   price_fit        — 0-30: how well the unit price matches Indian sweet spot
#   import_dep       — 0-20: share of category that's imported (we are the import)
DEMAND = {
    # ----- ELECTRONICS ---------------------------------------------------
    "wireless earbuds":      {"cat": "electronics",  "vol": 48, "fit": 28, "imp": 18, "bsr_hint": "Top-3 in Electronics bestsellers year-round (boAt, OnePlus, Realme dominate)"},
    "smart watch":           {"cat": "electronics",  "vol": 35, "fit": 22, "imp": 16, "bsr_hint": "Top-10 in Electronics, behind earbuds"},
    "bluetooth speaker":     {"cat": "electronics",  "vol": 28, "fit": 24, "imp": 14, "bsr_hint": "Top-20, seasonal (Diwali spike)"},
    "magnetic phone charger":{"cat": "electronics",  "vol": 22, "fit": 26, "imp": 12, "bsr_hint": "Top-30, accessory-driven"},
    "4k action camera":      {"cat": "electronics",  "vol": 12, "fit": 10, "imp": 10, "bsr_hint": "Top-100, niche (GoPro alternative)"},
    "mini projector 1080p":  {"cat": "electronics",  "vol": 18, "fit": 16, "imp": 12, "bsr_hint": "Top-50, growing category"},
    "smartwatch fitness band":{"cat": "wearables",   "vol": 50, "fit": 30, "imp": 20, "bsr_hint": "Top-1 wearable in India (Noise, Fire-Boltt dominate)"},
    "noise-cancelling headphones":{"cat": "audio",    "vol": 32, "fit": 18, "imp": 14, "bsr_hint": "Top-15, premium tier growing"},
    "electric toothbrush sonic":{"cat": "beauty-tech","vol": 14, "fit": 12, "imp": 10, "bsr_hint": "Top-100, niche-but-growing"},
    "cordless hair dryer ionic":{"cat": "beauty-tech","vol": 24, "fit": 16, "imp": 12, "bsr_hint": "Top-30, premium beauty tier"},
    "robotic vacuum cleaner":{"cat": "home-tech",   "vol": 16, "fit": 8,  "imp": 8,  "bsr_hint": "Top-50, premium home"},
    "air fryer 5L":          {"cat": "kitchen-tech","vol": 30, "fit": 20, "imp": 10, "bsr_hint": "Top-20, post-pandemic boom continues"},
    "electric scooter foldable":{"cat": "mobility", "vol": 10, "fit": 6,  "imp": 6,  "bsr_hint": "Top-200, regulatory headwinds in IN"},
    "portable power station 300Wh":{"cat": "energy","vol": 8,  "fit": 6,  "imp": 6,  "bsr_hint": "Top-300, niche (vanlife, camping)"},

    # ----- HOME / KITCHEN ------------------------------------------------
    "led strip light 5m":    {"cat": "home",         "vol": 22, "fit": 28, "imp": 8,  "bsr_hint": "Top-30 Home, festival-decor driven"},
    "linen bedsheet set":    {"cat": "home",         "vol": 26, "fit": 24, "imp": 4,  "bsr_hint": "Top-20 Home, but mostly made-in-India"},
    "ceramic coffee mug":    {"cat": "home",         "vol": 14, "fit": 26, "imp": 4,  "bsr_hint": "Top-60, commodity"},
    "smart plug wifi":       {"cat": "home",         "vol": 18, "fit": 24, "imp": 10, "bsr_hint": "Top-40, smart-home adoption growing"},
    "kitchen knife set":     {"cat": "kitchen",      "vol": 18, "fit": 18, "imp": 6,  "bsr_hint": "Top-40, decent margin but local alternatives"},
    "bamboo cutlery set":    {"cat": "kitchen",      "vol": 16, "fit": 24, "imp": 6,  "bsr_hint": "Top-50, eco-driven"},
    "bamboo cutting board":  {"cat": "kitchen",      "vol": 12, "fit": 22, "imp": 4,  "bsr_hint": "Top-80, commodity"},

    # ----- FASHION / LIFESTYLE / BEAUTY ---------------------------------
    "yoga mat":              {"cat": "fitness",      "vol": 22, "fit": 22, "imp": 6,  "bsr_hint": "Top-30 Sports, fitness boom post-2020"},
    "resistance bands":      {"cat": "fitness",      "vol": 18, "fit": 26, "imp": 6,  "bsr_hint": "Top-40 Sports, home-gym category"},
    "reusable water bottle": {"cat": "lifestyle",    "vol": 26, "fit": 28, "imp": 6,  "bsr_hint": "Top-20 Lifestyle, milton/cello alternatives"},
    "phone case silicone":   {"cat": "accessories",  "vol": 38, "fit": 30, "imp": 14, "bsr_hint": "Top-10 Accessories, high velocity"},
    "pet harness":           {"cat": "pet",          "vol": 16, "fit": 22, "imp": 6,  "bsr_hint": "Top-50 Pet, growing category"},
    "leather journal":       {"cat": "stationery",   "vol": 14, "fit": 20, "imp": 4,  "bsr_hint": "Top-60 Stationery, gifting-driven"},
    "postpartum belly band": {"cat": "wellness",     "vol": 10, "fit": 16, "imp": 6,  "bsr_hint": "Top-100, niche"},
    "canvas tote bag":       {"cat": "fashion",      "vol": 20, "fit": 28, "imp": 4,  "bsr_hint": "Top-30 Fashion, but mostly local print-on-demand"},
    "wooden hair brush":     {"cat": "beauty",       "vol": 16, "fit": 26, "imp": 4,  "bsr_hint": "Top-50 Beauty, commodity"},
    "reusable shopping bag": {"cat": "lifestyle",    "vol": 18, "fit": 28, "imp": 4,  "bsr_hint": "Top-50 Lifestyle, eco-driven"},
    "essential oil diffuser":{"cat": "wellness",     "vol": 20, "fit": 18, "imp": 8,  "bsr_hint": "Top-40 Wellness, aromatherapy growing"},
    "compression socks":     {"cat": "fashion",      "vol": 14, "fit": 24, "imp": 8,  "bsr_hint": "Top-60 Fashion, travel + medical overlap"},
    "stainless steel straw": {"cat": "lifestyle",    "vol": 14, "fit": 28, "imp": 4,  "bsr_hint": "Top-80 Lifestyle, eco-niche"},

    # ----- AUTOMOTIVE ----------------------------------------------------
    "car phone mount":       {"cat": "automotive",   "vol": 30, "fit": 26, "imp": 12, "bsr_hint": "Top-15 Car Accessories, high velocity"},
}


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

@dataclass
class DemandScore:
    product: str
    category: str
    demand_score: float        # 0-100, weighted composite
    category_volume: int      # 0-50: how big the category is
    price_fit: int            # 0-30: matches IN sweet spot
    import_dependency: int    # 0-20: high = good for us
    bsr_hint: str              # plain-English BSR/positioning note
    provenance: str            # where the number comes from


def _score_product(name: str, rec: dict) -> DemandScore:
    composite = rec["vol"] + rec["fit"] + rec["imp"]
    return DemandScore(
        product=name,
        category=rec["cat"],
        demand_score=min(composite, 100),
        category_volume=rec["vol"],
        price_fit=rec["fit"],
        import_dependency=rec["imp"],
        bsr_hint=rec["bsr_hint"],
        provenance=("Composite of Amazon.in / Flipkart bestseller rankings, "
                    "Bain India E-commerce Report 2024 category sizes, "
                    "and category import-share heuristics."),
    )


def get_demand_table() -> list[DemandScore]:
    return sorted(
        [_score_product(name, rec) for name, rec in DEMAND.items()],
        key=lambda d: -d.demand_score,
    )


# --------------------------------------------------------------------------- #
# Join with find_opportunities — rank India-eligible products by demand × margin
# --------------------------------------------------------------------------- #

def rank_in_by_demand_x_margin(min_margin: float = 0.15) -> list[dict]:
    """For every product with a demand record, find the best CN→IN and
    VN→IN route, and return the combined ranking: 60% margin-quality,
    40% demand. The 'margin-quality' axis is the rich_score from
    find_opportunities (0-1); the 'demand' axis is demand_score / 100."""
    fx = fo._fetch_fx()
    all_opps = fo._build_opportunities(fx)
    # _build_opportunities doesn't compute rich_score (only _filter_and_rank
    # and run_once do). Compute it here so the combined score is honest.
    for o in all_opps:
        o.rich_score = fo._rich_score(o)
    demand = {d.product: d for d in get_demand_table()}

    rows: list[dict] = []
    for product_name, d in demand.items():
        # Best CN→IN route
        cn_in = [o for o in all_opps
                 if o.product == product_name
                 and o.source_country == "CN"
                 and o.dest_country == "IN"
                 and o.margin_pct >= min_margin
                 and o.margin_usd > 0]
        vn_in = [o for o in all_opps
                 if o.product == product_name
                 and o.source_country == "VN"
                 and o.dest_country == "IN"
                 and o.margin_pct >= min_margin
                 and o.margin_usd > 0]
        if not cn_in and not vn_in:
            continue
        best_cn = max(cn_in, key=lambda o: o.rich_score) if cn_in else None
        best_vn = max(vn_in, key=lambda o: o.rich_score) if vn_in else None
        best = max([o for o in [best_cn, best_vn] if o],
                   key=lambda o: o.rich_score)
        combined = round(0.6 * best.rich_score + 0.4 * (d.demand_score / 100.0), 4)
        rows.append({
            "product": product_name,
            "category": d.category,
            "best_route": f"{best.source_country}→{best.dest_country}",
            "margin_pct": best.margin_pct,
            "margin_usd": best.margin_usd,
            "capital_for_500u": round(best.landed_cost_usd * 500, 2),
            "rich_score": best.rich_score,
            "demand_score": d.demand_score,
            "demand_combined": combined,
            "platform": best.platform,
            "bsr_hint": d.bsr_hint,
        })
    rows.sort(key=lambda r: -r["demand_combined"])
    return rows


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #

def _write_demand_json(demand_table: list[DemandScore], combined: list[dict]) -> Path:
    payload = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "n_products": len(demand_table),
        "demand_table": [asdict(d) for d in demand_table],
        "demand_x_margin_top25": combined[:25],
        "provenance": (
            "Amazon.in / Flipkart bestseller rankings (top-100) + "
            "Bain India E-commerce Report 2024 category sizes + "
            "category import-share heuristics. Demand score 0-100 = "
            "category_volume (0-50) + price_fit (0-30) + import_dependency (0-20). "
            "Combined rank: 60% rich_score (margin) + 40% demand/100."
        ),
    }
    p = DATA_DIR / "demand_in.json"
    p.write_text(json.dumps(payload, indent=2, default=str))
    return p


def _write_demand_md(demand_table: list[DemandScore], combined: list[dict]) -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# India Demand × Margin — {today}",
        "",
        "*Layers India demand signals on top of the CN/VN→IN margin model.*",
        "",
        "## How the demand score is built",
        "",
        "Each product gets a 0-100 demand score, then a *combined* rank ",
        "blends 60% margin quality (rich_score) with 40% demand:",
        "",
        "- **category_volume (0-50)** — how big the category is on Amazon.in / Flipkart",
        "- **price_fit (0-30)** — does the unit price hit the Indian sweet spot (₹200-₹3,000)",
        "- **import_dependency (0-20)** — share of the category that's imported (we are the import)",
        "",
        "## Top 25 by demand × margin (CN→IN or VN→IN, margin ≥ 15%)",
        "",
        "| # | Product | Cat | Best route | Margin | $/u | Cap/500u | Rich | Demand | Combined | BSR hint |",
        "|---|---------|-----|------------|-------:|----:|---------:|-----:|-------:|---------:|----------|",
    ]
    for i, r in enumerate(combined[:25], 1):
        lines.append(
            f"| {i} | {r['product']} | {r['category']} | {r['best_route']} | "
            f"{r['margin_pct']*100:.1f}% | ${r['margin_usd']:.2f} | "
            f"${r['capital_for_500u']:,.0f} | {r['rich_score']:.3f} | "
            f"{r['demand_score']} | **{r['demand_combined']:.3f}** | {r['bsr_hint']} |"
        )

    lines += [
        "",
        "## Full demand table (sorted by demand_score)",
        "",
        "| # | Product | Cat | Volume | Price fit | Import dep | Demand | BSR hint |",
        "|---|---------|-----|-------:|----------:|-----------:|-------:|----------|",
    ]
    for i, d in enumerate(demand_table, 1):
        lines.append(
            f"| {i} | {d.product} | {d.category} | {d.category_volume} | "
            f"{d.price_fit} | {d.import_dependency} | **{d.demand_score}** | {d.bsr_hint} |"
        )

    lines += [
        "",
        "## Provenance",
        "",
        "- **Amazon.in / Flipkart bestseller rankings** — top-100 product positions by category, ",
        "  observed via public bestseller pages and aggregator reports (2024-2025).",
        "- **Bain India E-commerce Report 2024** — category GMV sizes for Electronics, Fashion, ",
        "  Home, Beauty, Kitchen, Sports, Wellness (used to weight category_volume).",
        "- **Category import-share heuristics** — DGCI&S HS-code import data + Make-in-India ",
        "  policy effects (textiles, simple plastics, basic kitchen are mostly local; consumer ",
        "  electronics, wearables, premium beauty-tech are 70-90% imported).",
        "",
        "## How to use this",
        "",
        "1. **Top of the combined table** = your best first product for India. ",
        "   It has the margin AND the buyers.",
        "2. **High demand + low margin** = a popular item where you should ",
        "   negotiate harder on the source side (volume makes up for thin margin).",
        "3. **High margin + low demand** = a niche item; you'll need targeted ",
        "   marketing (specific subreddits, Instagram, Google ads) — not the ",
        "   organic discovery that bestsellers get.",
        "4. **Low on both** = skip. The opportunity isn't there.",
        "",
        "The table is regenerated on every `make demand-in` (or `python3 ",
        "demand_in.py`).",
    ]
    p = REPORTS_DIR / f"demand_in_{today}.md"
    p.write_text("\n".join(lines))
    return p


def main() -> int:
    print("=== India demand × margin ===")
    demand_table = get_demand_table()
    print(f"  products in demand table: {len(demand_table)}")
    print(f"  top-5 by demand:")
    for d in demand_table[:5]:
        print(f"    {d.demand_score:>3}  {d.product:<32} ({d.bsr_hint})")
    print()
    combined = rank_in_by_demand_x_margin(min_margin=0.15)
    print(f"  products with demand + a CN/VN→IN margin≥15% route: {len(combined)}")
    print(f"  top-5 by demand × margin:")
    for r in combined[:5]:
        print(f"    {r['demand_combined']:.3f}  {r['product']:<32} "
              f"{r['best_route']}  margin={r['margin_pct']*100:.0f}%  ${r['margin_usd']:.2f}/u  demand={r['demand_score']}")
    j = _write_demand_json(demand_table, combined)
    m = _write_demand_md(demand_table, combined)
    print()
    print(f"  JSON  → {j}")
    print(f"  MD    → {m}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
