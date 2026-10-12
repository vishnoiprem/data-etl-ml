#!/usr/bin/env python3
"""
find_opportunities.py — global trade opportunity finder.

Finds cheap-source ↔ expensive-destination product pairs, computes landed
cost + margin, ranks opportunities, and writes outreach email drafts.

Pipeline
--------
1. Source-side candidates — what products are cheap to source globally?
   (CN wholesale, IN wholesale, VN factory, TR wholesale, MX wholesale).
2. Destination-side price discovery — what are these products selling
   for in target markets (US, EU, AU, JP, etc.)?
3. Margin model — landed cost = unit + shipping + tariff + platform fee
                   vs. destination price. Filter to margin >= 35%.
4. Lead gen — for the top opportunities, draft an outreach email to
   either (a) the buyer in the destination market (services lead) or
   (b) the seller in the source market (sourcing lead).

Two run modes
------------
  --once      : single pass, print + write to data/
  --loop      : re-run every --interval-min minutes (default 60)

Data sources (free, no API key needed)
--------------------------------------
- exchange-rates.host  — daily FX rates
- restcountries.com    — country / region / currency metadata
- Wikipedia / static   — HS code → tariff heuristics (built-in)
- Built-in price list  — demonstrative source + destination prices
  (replace with your own scrapers when you have them)

Output
------
  data/products.csv          — current source + destination price snapshots
  data/latest_ranked.json    — top N opportunities with full economics
  reports/YYYY-MM-DD.md      — human-readable report
  reports/email_<ts>.txt     — outreach drafts for the top 3 leads

Run
---
  python3 trade-finder/find_opportunities.py --once
  python3 trade-finder/find_opportunities.py --loop --interval-min 60
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
REPORTS_DIR = HERE / "reports"
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

PRODUCTS_CSV = DATA_DIR / "products.csv"
RANKED_JSON = DATA_DIR / "latest_ranked.json"

# --------------------------------------------------------------------------- #
# Static data: 26 hot products × source + destination prices.
# In production, replace with live scrapers (Alibaba, Amazon, eBay sold,
# MercadoLibre, etc.). The shape is the same.
# --------------------------------------------------------------------------- #

# Country-level economics: tariff rate (avg MFN), shipping $ per kg,
# platform fee (Amazon FBA, eBay final-value, Etsy, etc.).
COUNTRY_META = {
    "CN": {"name": "China",     "currency": "CNY", "tariff_avg": 0.075, "ship_per_kg": 4.5},
    "IN": {"name": "India",     "currency": "INR", "tariff_avg": 0.10,  "ship_per_kg": 5.0},
    "VN": {"name": "Vietnam",   "currency": "VND", "tariff_avg": 0.08,  "ship_per_kg": 4.8},
    "TR": {"name": "Türkiye",   "currency": "TRY", "tariff_avg": 0.06,  "ship_per_kg": 3.5},
    "MX": {"name": "Mexico",    "currency": "MXN", "tariff_avg": 0.05,  "ship_per_kg": 2.8},
    "BD": {"name": "Bangladesh","currency": "BDT", "tariff_avg": 0.09,  "ship_per_kg": 5.2},
    "ID": {"name": "Indonesia", "currency": "IDR", "tariff_avg": 0.08,  "ship_per_kg": 4.6},
    "TH": {"name": "Thailand",  "currency": "THB", "tariff_avg": 0.07,  "ship_per_kg": 4.4},
    "US": {"name": "USA",       "currency": "USD", "tariff_avg": 0.025, "ship_per_kg": 1.5},
    "DE": {"name": "Germany",   "currency": "EUR", "tariff_avg": 0.045, "ship_per_kg": 1.8},
    "UK": {"name": "UK",        "currency": "GBP", "tariff_avg": 0.03,  "ship_per_kg": 1.9},
    "AU": {"name": "Australia", "currency": "AUD", "tariff_avg": 0.05,  "ship_per_kg": 3.0},
    "JP": {"name": "Japan",     "currency": "JPY", "tariff_avg": 0.04,  "ship_per_kg": 2.5},
    "CA": {"name": "Canada",    "currency": "CAD", "tariff_avg": 0.04,  "ship_per_kg": 1.7},
    "AE": {"name": "UAE",       "currency": "AED", "tariff_avg": 0.05,  "ship_per_kg": 2.6},
}

# Platform fee schedules (destination marketplace)
PLATFORM_FEES = {
    "amazon_fba": 0.33,  # referral + FBA pick & pack (avg)
    "ebay":       0.13,  # final-value fee avg
    "etsy":       0.12,  # transaction + listing
    "shopify":    0.029, # Shopify Payments
    "tiktok":     0.08,  # TikTok Shop seller fee
}

# Product universe. Each row: name, category, weight (kg/unit),
# base unit cost (USD) per source country, and a destination price (USD)
# per destination country. These are baseline numbers — we add ±noise
# each cycle to simulate market drift.
PRODUCTS: list[dict] = [
    # name, category, kg/unit, source prices (CN/IN/VN/TR/MX/BD/ID/TH), dest prices (US/DE/UK/AU/JP/CA/AE)
    {"name": "wireless earbuds",      "cat": "electronics", "kg": 0.10,
     "src": {"CN": 3.50, "IN": 4.20, "VN": 3.80, "TR": 4.50, "MX": 5.10, "BD": 4.00, "ID": 4.10, "TH": 4.30},
     "dst": {"US": 18.0, "DE": 22.0, "UK": 21.0, "AU": 26.0, "JP": 24.0, "CA": 23.0, "AE": 20.0}},
    {"name": "smart watch",           "cat": "electronics", "kg": 0.12,
     "src": {"CN": 7.20, "IN": 8.50, "VN": 7.80, "TR": 9.00, "MX": 9.50, "BD": 8.00, "ID": 8.20, "TH": 8.40},
     "dst": {"US": 32.0, "DE": 38.0, "UK": 36.0, "AU": 44.0, "JP": 40.0, "CA": 38.0, "AE": 34.0}},
    {"name": "led strip light 5m",    "cat": "home",        "kg": 0.20,
     "src": {"CN": 1.20, "IN": 1.50, "VN": 1.30, "TR": 1.60, "MX": 1.80, "BD": 1.40, "ID": 1.45, "TH": 1.50},
     "dst": {"US": 9.0, "DE": 11.0, "UK": 10.0, "AU": 13.0, "JP": 12.0, "CA": 11.0, "AE": 10.0}},
    {"name": "yoga mat",              "cat": "fitness",     "kg": 1.20,
     "src": {"CN": 3.80, "IN": 4.20, "VN": 4.00, "TR": 4.50, "MX": 4.80, "BD": 3.90, "ID": 4.00, "TH": 4.10},
     "dst": {"US": 18.0, "DE": 22.0, "UK": 21.0, "AU": 26.0, "JP": 24.0, "CA": 23.0, "AE": 20.0}},
    {"name": "reusable water bottle", "cat": "lifestyle",   "kg": 0.30,
     "src": {"CN": 1.50, "IN": 1.80, "VN": 1.60, "TR": 1.90, "MX": 2.00, "BD": 1.70, "ID": 1.75, "TH": 1.80},
     "dst": {"US": 12.0, "DE": 14.0, "UK": 13.0, "AU": 16.0, "JP": 15.0, "CA": 14.0, "AE": 13.0}},
    {"name": "phone case silicone",   "cat": "accessories", "kg": 0.05,
     "src": {"CN": 0.45, "IN": 0.55, "VN": 0.50, "TR": 0.60, "MX": 0.65, "BD": 0.50, "ID": 0.52, "TH": 0.55},
     "dst": {"US": 4.5, "DE": 5.5, "UK": 5.0, "AU": 6.5, "JP": 6.0, "CA": 5.5, "AE": 5.0}},
    {"name": "bluetooth speaker",     "cat": "electronics", "kg": 0.40,
     "src": {"CN": 5.20, "IN": 6.00, "VN": 5.50, "TR": 6.20, "MX": 6.50, "BD": 5.60, "ID": 5.80, "TH": 5.90},
     "dst": {"US": 24.0, "DE": 28.0, "UK": 27.0, "AU": 32.0, "JP": 30.0, "CA": 28.0, "AE": 26.0}},
    {"name": "linen bedsheet set",    "cat": "home",        "kg": 1.50,
     "src": {"CN": 8.50, "IN": 7.80, "VN": 8.20, "TR": 9.20, "MX": 9.80, "BD": 7.20, "ID": 8.00, "TH": 8.40},
     "dst": {"US": 38.0, "DE": 44.0, "UK": 42.0, "AU": 50.0, "JP": 46.0, "CA": 44.0, "AE": 40.0}},
    {"name": "kids educational toy",  "cat": "toys",        "kg": 0.50,
     "src": {"CN": 2.80, "IN": 3.20, "VN": 2.90, "TR": 3.40, "MX": 3.70, "BD": 2.90, "ID": 3.00, "TH": 3.10},
     "dst": {"US": 14.0, "DE": 17.0, "UK": 16.0, "AU": 20.0, "JP": 18.0, "CA": 17.0, "AE": 15.0}},
    {"name": "pet harness",            "cat": "pet",         "kg": 0.20,
     "src": {"CN": 1.80, "IN": 2.10, "VN": 1.90, "TR": 2.20, "MX": 2.40, "BD": 2.00, "ID": 2.05, "TH": 2.10},
     "dst": {"US": 11.0, "DE": 13.0, "UK": 12.0, "AU": 15.0, "JP": 14.0, "CA": 13.0, "AE": 12.0}},
    {"name": "ceramic coffee mug",     "cat": "home",        "kg": 0.45,
     "src": {"CN": 1.20, "IN": 1.40, "VN": 1.25, "TR": 1.50, "MX": 1.65, "BD": 1.30, "ID": 1.35, "TH": 1.40},
     "dst": {"US": 8.0, "DE": 10.0, "UK": 9.0, "AU": 12.0, "JP": 11.0, "CA": 10.0, "AE": 9.0}},
    {"name": "kitchen knife set",      "cat": "kitchen",     "kg": 0.80,
     "src": {"CN": 6.50, "IN": 7.20, "VN": 6.80, "TR": 7.60, "MX": 8.20, "BD": 6.70, "ID": 7.00, "TH": 7.20},
     "dst": {"US": 32.0, "DE": 38.0, "UK": 36.0, "AU": 44.0, "JP": 40.0, "CA": 38.0, "AE": 34.0}},
    {"name": "bamboo cutlery set",     "cat": "kitchen",     "kg": 0.30,
     "src": {"CN": 1.10, "IN": 1.30, "VN": 1.15, "TR": 1.40, "MX": 1.55, "BD": 1.20, "ID": 1.25, "TH": 1.30},
     "dst": {"US": 7.0, "DE": 9.0, "UK": 8.0, "AU": 11.0, "JP": 10.0, "CA": 9.0, "AE": 8.0}},
    {"name": "resistance bands",       "cat": "fitness",     "kg": 0.40,
     "src": {"CN": 1.40, "IN": 1.70, "VN": 1.50, "TR": 1.80, "MX": 1.95, "BD": 1.55, "ID": 1.60, "TH": 1.65},
     "dst": {"US": 9.0, "DE": 11.0, "UK": 10.0, "AU": 13.0, "JP": 12.0, "CA": 11.0, "AE": 10.0}},
    {"name": "car phone mount",        "cat": "automotive",  "kg": 0.25,
     "src": {"CN": 1.80, "IN": 2.10, "VN": 1.90, "TR": 2.20, "MX": 2.40, "BD": 2.00, "ID": 2.05, "TH": 2.10},
     "dst": {"US": 11.0, "DE": 13.0, "UK": 12.0, "AU": 15.0, "JP": 14.0, "CA": 13.0, "AE": 12.0}},
    {"name": "smart plug wifi",        "cat": "home",        "kg": 0.10,
     "src": {"CN": 1.50, "IN": 1.80, "VN": 1.60, "TR": 1.90, "MX": 2.00, "BD": 1.70, "ID": 1.75, "TH": 1.80},
     "dst": {"US": 8.5, "DE": 10.0, "UK": 9.5, "AU": 12.0, "JP": 11.0, "CA": 10.0, "AE": 9.0}},
    {"name": "leather journal",        "cat": "stationery",  "kg": 0.30,
     "src": {"IN": 3.50, "CN": 3.80, "VN": 3.60, "TR": 3.90, "MX": 4.20, "BD": 3.30, "ID": 3.60, "TH": 3.70},
     "dst": {"US": 14.0, "DE": 17.0, "UK": 16.0, "AU": 20.0, "JP": 18.0, "CA": 17.0, "AE": 15.0}},
    {"name": "magnetic phone charger", "cat": "electronics", "kg": 0.10,
     "src": {"CN": 2.20, "IN": 2.60, "VN": 2.35, "TR": 2.80, "MX": 3.00, "BD": 2.50, "ID": 2.55, "TH": 2.60},
     "dst": {"US": 13.0, "DE": 15.0, "UK": 14.0, "AU": 17.0, "JP": 16.0, "CA": 15.0, "AE": 14.0}},
    {"name": "postpartum belly band",  "cat": "wellness",    "kg": 0.25,
     "src": {"CN": 2.80, "IN": 3.20, "VN": 2.90, "TR": 3.40, "MX": 3.70, "BD": 3.00, "ID": 3.10, "TH": 3.20},
     "dst": {"US": 14.0, "DE": 17.0, "UK": 16.0, "AU": 20.0, "JP": 18.0, "CA": 17.0, "AE": 15.0}},
    {"name": "bamboo cutting board",   "cat": "kitchen",     "kg": 0.90,
     "src": {"CN": 3.20, "IN": 3.60, "VN": 3.30, "TR": 3.80, "MX": 4.10, "BD": 3.40, "ID": 3.50, "TH": 3.60},
     "dst": {"US": 16.0, "DE": 19.0, "UK": 18.0, "AU": 22.0, "JP": 20.0, "CA": 19.0, "AE": 17.0}},
    {"name": "canvas tote bag",        "cat": "fashion",     "kg": 0.20,
     "src": {"CN": 1.40, "IN": 1.60, "VN": 1.45, "TR": 1.70, "MX": 1.85, "BD": 1.50, "ID": 1.55, "TH": 1.60},
     "dst": {"US": 9.0, "DE": 11.0, "UK": 10.0, "AU": 13.0, "JP": 12.0, "CA": 11.0, "AE": 10.0}},
    {"name": "wooden hair brush",      "cat": "beauty",      "kg": 0.15,
     "src": {"CN": 1.20, "IN": 1.40, "VN": 1.25, "TR": 1.50, "MX": 1.65, "BD": 1.30, "ID": 1.35, "TH": 1.40},
     "dst": {"US": 8.0, "DE": 10.0, "UK": 9.0, "AU": 12.0, "JP": 11.0, "CA": 10.0, "AE": 9.0}},
    {"name": "reusable shopping bag",  "cat": "lifestyle",   "kg": 0.10,
     "src": {"CN": 0.60, "IN": 0.75, "VN": 0.65, "TR": 0.80, "MX": 0.90, "BD": 0.70, "ID": 0.75, "TH": 0.78},
     "dst": {"US": 5.0, "DE": 6.0, "UK": 5.5, "AU": 7.0, "JP": 6.5, "CA": 6.0, "AE": 5.5}},
    {"name": "essential oil diffuser", "cat": "wellness",    "kg": 0.50,
     "src": {"CN": 4.50, "IN": 5.20, "VN": 4.80, "TR": 5.40, "MX": 5.80, "BD": 4.90, "ID": 5.00, "TH": 5.10},
     "dst": {"US": 22.0, "DE": 26.0, "UK": 25.0, "AU": 30.0, "JP": 28.0, "CA": 26.0, "AE": 24.0}},
    {"name": "compression socks",      "cat": "fashion",     "kg": 0.10,
     "src": {"CN": 1.10, "IN": 1.30, "VN": 1.15, "TR": 1.40, "MX": 1.55, "BD": 1.20, "ID": 1.25, "TH": 1.30},
     "dst": {"US": 8.0, "DE": 10.0, "UK": 9.0, "AU": 12.0, "JP": 11.0, "CA": 10.0, "AE": 9.0}},
    {"name": "stainless steel straw",  "cat": "lifestyle",   "kg": 0.05,
     "src": {"CN": 0.40, "IN": 0.50, "VN": 0.42, "TR": 0.55, "MX": 0.60, "BD": 0.45, "ID": 0.48, "TH": 0.50},
     "dst": {"US": 4.0, "DE": 5.0, "UK": 4.5, "AU": 6.0, "JP": 5.5, "CA": 5.0, "AE": 4.5}},
]


# --------------------------------------------------------------------------- #
# FX rates
# --------------------------------------------------------------------------- #

def _fetch_fx() -> dict[str, float]:
    """Pull USD-based FX rates. Returns {"USD": 1.0, "EUR": 0.92, ...}.
    Falls back to a small static table if the network is down.
    """
    fallback = {"USD": 1.0, "CNY": 7.20, "INR": 83.0, "VND": 25000, "TRY": 32.0,
                "MXN": 17.5, "BDT": 110.0, "IDR": 16000, "THB": 36.0, "EUR": 0.92,
                "GBP": 0.78, "AUD": 1.52, "JPY": 152.0, "CAD": 1.36, "AED": 3.67}
    try:
        url = "https://api.exchangerate.host/latest?base=USD"
        with urllib.request.urlopen(url, timeout=8) as r:
            data = json.load(r)
        if data.get("rates"):
            return {"USD": 1.0, **{k: float(v) for k, v in data["rates"].items()}}
    except Exception as exc:
        print(f"[fx] live fetch failed ({exc}) — using fallback table", file=sys.stderr)
    return fallback


# --------------------------------------------------------------------------- #
# Pricing model
# --------------------------------------------------------------------------- #

@dataclass
class Opportunity:
    product: str
    category: str
    source_country: str
    dest_country: str
    source_unit_usd: float
    dest_price_usd: float
    weight_kg: float
    shipping_usd: float
    tariff_usd: float
    platform_fee_usd: float
    landed_cost_usd: float
    margin_usd: float
    margin_pct: float
    markup_x: float
    platform: str
    # scoring
    score: float = 0.0
    # "service lead" — angle: you're offering to source this for the
    # destination-side seller, or to broker a deal.
    lead_angle: str = "sourcing"
    notes: str = ""


def _platform_for(dest: str, category: str) -> str:
    """Pick the highest-volume destination platform by category."""
    if category in ("electronics", "home", "kitchen", "automotive", "accessories"):
        return "amazon_fba"
    if category in ("fashion", "beauty"):
        return "tiktok"
    if category in ("toys", "pet", "lifestyle"):
        return "amazon_fba"
    if category in ("stationery", "fitness", "wellness"):
        return "etsy"
    return "ebay"


def _jitter(value: float, pct: float = 0.05) -> float:
    """Simulate live market drift on a static price list."""
    return round(value * (1.0 + random.uniform(-pct, pct)), 3)


def _build_opportunities(fx: dict[str, float]) -> list[Opportunity]:
    out: list[Opportunity] = []
    for p in PRODUCTS:
        for src, src_price in p["src"].items():
            # The product table is already USD-equivalent wholesale; jitter for market drift.
            src_usd = _jitter(src_price, 0.07)
            for dst, dst_price in p["dst"].items():
                # The destination price is in destination-country currency on
                # the local marketplace. Convert via FX to USD.
                dst_currency = COUNTRY_META[dst]["currency"]
                dst_usd = _jitter(dst_price / fx.get(dst_currency, 1.0), 0.05)
                weight = p["kg"]
                # Shipping: source-country rate × weight
                ship = round(COUNTRY_META[src]["ship_per_kg"] * weight * random.uniform(0.95, 1.10), 2)
                # Tariff: destination MFN × landed (use src + ship for simplicity)
                tariff_rate = COUNTRY_META[dst]["tariff_avg"] * random.uniform(0.8, 1.2)
                tariff = round((src_usd + ship) * tariff_rate, 2)
                platform = _platform_for(dst, p["cat"])
                fee_rate = PLATFORM_FEES[platform]
                platform_fee = round(dst_usd * fee_rate, 2)
                landed = round(src_usd + ship + tariff, 2)
                margin = round(dst_usd - landed - platform_fee, 2)
                margin_pct = round(margin / dst_usd, 4) if dst_usd else 0.0
                markup = round(dst_usd / landed, 2) if landed else 0.0
                opp = Opportunity(
                    product=p["name"],
                    category=p["cat"],
                    source_country=src,
                    dest_country=dst,
                    source_unit_usd=round(src_usd, 3),
                    dest_price_usd=round(dst_usd, 2),
                    weight_kg=weight,
                    shipping_usd=ship,
                    tariff_usd=tariff,
                    platform_fee_usd=platform_fee,
                    landed_cost_usd=landed,
                    margin_usd=margin,
                    margin_pct=margin_pct,
                    markup_x=markup,
                    platform=platform,
                )
                out.append(opp)
    return out


def _score(o: Opportunity) -> float:
    """Composite score: 60% margin, 25% markup, 15% lightweight (cheap to ship)."""
    margin_component = max(0.0, o.margin_pct)  # negative margins get 0
    markup_component = min(o.markup_x / 5.0, 1.0)  # 5x markup is excellent
    weight_penalty = max(0.0, 1.0 - (o.weight_kg / 5.0))  # <5kg is OK
    return round(0.60 * margin_component + 0.25 * markup_component + 0.15 * weight_penalty, 4)


def _filter_and_rank(opps: list[Opportunity], min_margin: float = 0.35) -> list[Opportunity]:
    """Keep only profitable routes (margin >= min_margin)."""
    for o in opps:
        o.score = _score(o)
    qualified = [o for o in opps if o.margin_pct >= min_margin and o.margin_usd > 0]
    qualified.sort(key=lambda o: -o.score)
    return qualified


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #

def _write_products_csv(opps: list[Opportunity]) -> None:
    fields = list(asdict(opps[0]).keys()) if opps else [
        "product", "category", "source_country", "dest_country",
        "source_unit_usd", "dest_price_usd", "weight_kg",
        "shipping_usd", "tariff_usd", "platform_fee_usd",
        "landed_cost_usd", "margin_usd", "margin_pct", "markup_x",
        "platform", "score", "lead_angle", "notes",
    ]
    with PRODUCTS_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for o in opps:
            w.writerow(asdict(o))


def _write_ranked_json(opps: list[Opportunity], fx: dict[str, float]) -> None:
    payload = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "n_qualified": len(opps),
        "fx_base": "USD",
        "fx_rates": {k: round(v, 4) for k, v in fx.items()},
        "top_opportunities": [asdict(o) for o in opps[:30]],
    }
    RANKED_JSON.write_text(json.dumps(payload, indent=2, default=str))


def _write_markdown_report(opps: list[Opportunity], fx: dict[str, float]) -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    path = REPORTS_DIR / f"{today}.md"
    n_total = len(PRODUCTS) * 8 * 7  # rough upper bound
    lines = [
        f"# Trade Opportunities — {today}",
        "",
        f"- **Qualified routes (margin ≥ 35%):** {len(opps)} of ~{n_total} total combinations",
        f"- **FX base:** USD",
        f"- **Source:** live static + 5% drift simulation (replace with scraper for production)",
        "",
        "## Top 20 by composite score",
        "",
        "| # | Product | Cat | Route | Src $ | Dst $ | Ship | Tariff | Fee | Landed | Margin | Markup | Score |",
        "|---|---------|-----|-------|-------|-------|------|--------|-----|--------|--------|--------|-------|",
    ]
    for i, o in enumerate(opps[:20], 1):
        lines.append(
            f"| {i} | {o.product} | {o.category} | {o.source_country}→{o.dest_country} | "
            f"{o.source_unit_usd:.2f} | {o.dest_price_usd:.2f} | {o.shipping_usd:.2f} | "
            f"{o.tariff_usd:.2f} | {o.platform_fee_usd:.2f} | {o.landed_cost_usd:.2f} | "
            f"{o.margin_pct*100:.1f}% | {o.markup_x:.2f}x | {o.score:.3f} |"
        )
    lines += [
        "",
        "## By category",
        "",
        "| Category | n | avg margin | best route |",
        "|----------|---|-----------|-----------|",
    ]
    by_cat: dict[str, list[Opportunity]] = {}
    for o in opps:
        by_cat.setdefault(o.category, []).append(o)
    for cat, items in sorted(by_cat.items(), key=lambda kv: -len(kv[1])):
        avg = sum(o.margin_pct for o in items) / len(items)
        best = max(items, key=lambda o: o.score)
        lines.append(
            f"| {cat} | {len(items)} | {avg*100:.1f}% | {best.product} {best.source_country}→{best.dest_country} ({best.margin_pct*100:.1f}%) |"
        )
    path.write_text("\n".join(lines))
    return path


def _write_outreach_emails(opps: list[Opportunity]) -> list[Path]:
    """For the top 3, write a 'sourcing services' outreach draft."""
    out: list[Path] = []
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    for i, o in enumerate(opps[:3]):
        src_name = COUNTRY_META[o.source_country]["name"]
        dst_name = COUNTRY_META[o.dest_country]["name"]
        body = (
            f"Subject: {o.product.title()} sourcing — {o.margin_pct*100:.0f}% margin, {src_name} → {dst_name}\n"
            f"\n"
            f"Hi [First Name],\n"
            f"\n"
            f"I noticed you sell {o.product} on {o.platform.replace('_',' ').title()} "
            f"in the {dst_name} market. I run a sourcing service out of {src_name} and "
            f"can land this SKU to your warehouse for ${o.landed_cost_usd:.2f}/unit "
            f"(including shipping + {o.tariff_usd:.2f} tariff).\n"
            f"\n"
            f"The math:\n"
            f"  • Your current selling price:  ${o.dest_price_usd:.2f}\n"
            f"  • My landed cost:               ${o.landed_cost_usd:.2f}\n"
            f"  • Platform fees (~{(o.platform_fee_usd/o.dest_price_usd)*100:.0f}%):    -${o.platform_fee_usd:.2f}\n"
            f"  • Net margin per unit:         ${o.margin_usd:.2f} ({o.margin_pct*100:.0f}%)\n"
            f"\n"
            f"  • Min order: 200 units (sample) / 1000+ units (production)\n"
            f"  • Lead time: 14-21 days door-to-door\n"
            f"  • Payment: 30% deposit, 70% on B/L copy\n"
            f"\n"
            f"I can send a free sample of the exact SKU + a one-page cost breakdown for "
            f"your top 3 {o.category} products if you'd like.\n"
            f"\n"
            f"Best,\n[Your name]\n"
        )
        p = REPORTS_DIR / f"email_{ts}_{i+1:02d}_{o.product.replace(' ','_')}_{o.source_country}to{o.dest_country}.txt"
        p.write_text(body)
        out.append(p)
    return out


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def run_once(verbose: bool = True) -> list[Opportunity]:
    if verbose:
        print(f"\n=== Trade-finder run @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    fx = _fetch_fx()
    if verbose:
        print(f"FX rates loaded: {len(fx)} currencies")
    all_opps = _build_opportunities(fx)
    qualified = _filter_and_rank(all_opps)
    if verbose:
        print(f"Routes evaluated: {len(all_opps)}")
        print(f"Qualified (margin≥35%): {len(qualified)}")
    _write_products_csv(all_opps)
    _write_ranked_json(qualified, fx)
    md = _write_markdown_report(qualified, fx)
    emails = _write_outreach_emails(qualified)
    if verbose:
        print(f"\nReport:   {md}")
        print(f"CSV:      {PRODUCTS_CSV}")
        print(f"JSON:     {RANKED_JSON}")
        print(f"Emails:   {len(emails)} drafts in {REPORTS_DIR}/")
        if qualified:
            top = qualified[0]
            print(
                f"\nTOP OPPORTUNITY: {top.product}  {top.source_country}→{top.dest_country}  "
                f"margin={top.margin_pct*100:.1f}%  score={top.score:.3f}"
            )
    return qualified


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Global trade opportunity finder.")
    p.add_argument("--once", action="store_true",
                   help="Single pass (default; falls back to --loop if absent).")
    p.add_argument("--loop", action="store_true",
                   help="Re-run every --interval-min minutes.")
    p.add_argument("--interval-min", type=int, default=60)
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)

    if not args.loop:
        run_once(verbose=not args.quiet)
        return 0

    print(f"=== Trade-finder LOOP @ {datetime.now().isoformat()} ===")
    print(f"    interval: {args.interval_min} min")
    try:
        while True:
            run_once(verbose=not args.quiet)
            print(f"next pass in {args.interval_min} min… (Ctrl-C to stop)")
            time.sleep(args.interval_min * 60)
    except KeyboardInterrupt:
        print("\nstopped.", flush=True)
        return 0


if __name__ == "__main__":
    sys.exit(main())
