"""Find suppliers for a product — the step before the quotes come back.

The trade-finder's verified supplier pool covers exactly one product line:
smart watches and fitness bands from Shenzhen. Every other viable route in
the dataset has **no verified supplier**, which means the RFQ has to go out
before a decision can be made.

This module does the part that can be done without a supplier database:
work out *who to contact* for a product, *what to ask them*, and *whether
the numbers would work* if they quote the target price.

Three things live here:

``SearchStrategy``
    The Alibaba search that will find candidate suppliers: the query
    terms, the platform filters, the city cluster, and the MOQ band that
    matches the order you actually intend to place.

``RfqDraft``
    A ready-to-send RFQ for one product, built from the trade-finder's
    own numbers — the target FOB is the modelled source cost, and the
    quote ladder asks for the volumes the business plan expects.

``coverage_gaps()``
    The honest audit of the whole pool: for every product that clears the
    margin floor, is there a verified supplier who makes it? This is the
    report that says "you have to go source this yourself".

Nothing here contacts a supplier or scrapes Alibaba. The module produces
the *plan*; a human sends the RFQ; the quotes come back and go into
``quote_agent.recommend()``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .corpus import trade_finder_modules

# --------------------------------------------------------------------------- #
# Alibaba search vocabulary
# --------------------------------------------------------------------------- #

#: Category paths on Alibaba that carry each trade-finder category. These
#: are the browse paths a buyer actually navigates, not the trade-finder's
#: internal category names.
ALIBABA_CATEGORY_PATHS: dict[str, str] = {
    "accessories": "Consumer Electronics > Mobile Phone Accessories > Phone Cases",
    "electronics": "Consumer Electronics > Mobile Phone Accessories",
    "home": "Home & Garden > Home Improvement",
    "home-tech": "Home & Garden > Home Appliances",
    "kitchen": "Home & Garden > Kitchen & Tableware",
    "kitchen-tech": "Home & Garden > Kitchen Appliances",
    "beauty": "Personal Care & Beauty > Beauty Tools",
    "beauty-tech": "Personal Care & Beauty > Beauty Equipment",
    "fashion": "Luggage & Bags > Bags & Cases",
    "lifestyle": "Home & Garden > Houseware",
    "fitness": "Sports & Entertainment > Fitness & Exercise",
    "pet": "Pet Supplies > Pet Apparel & Accessories",
    "toys": "Toys, Games & Hobbies > Educational Toys",
    "stationery": "Office & School Supplies > Notebooks",
    "wearables": "Consumer Electronics > Wearable Technology",
    "automotive": "Auto & Transportation > Car Electronics",
    "audio": "Consumer Electronics > Audio & Video",
    "mobility": "Sports & Entertainment > Electric Vehicles",
    "energy": "Consumer Electronics > Power Stations",
}

#: The industrial clusters that actually make each category. Searching
#: "phone case" without a city filter returns trading companies in Yiwu
#: and trading offices in Hong Kong, not factories.
CATEGORY_CITIES: dict[str, tuple[str, ...]] = {
    "accessories": ("Shenzhen", "Dongguan", "Guangzhou"),
    "electronics": ("Shenzhen", "Dongguan", "Huizhou"),
    "home": ("Ningbo", "Yongkang", "Shenzhen"),
    "home-tech": ("Shenzhen", "Ningbo", "Zhongshan"),
    "kitchen": ("Yongkang", "Ningbo", "Shenzhen"),
    "kitchen-tech": ("Shenzhen", "Ningbo", "Guangzhou"),
    "beauty": ("Shenzhen", "Ningbo", "Guangzhou"),
    "beauty-tech": ("Shenzhen", "Ningbo", "Dongguan"),
    "fashion": ("Guangzhou", "Xiamen", "Shenzhen"),
    "lifestyle": ("Yongkang", "Ningbo", "Shenzhen"),
    "fitness": ("Shenzhen", "Ningbo", "Yongkang"),
    "pet": ("Shenzhen", "Suzhou", "Yongkang"),
    "toys": ("Shenzhen", "Shantou", "Yongkang"),
    "stationery": ("Yongkang", "Shenzhen", "Ningbo"),
    "wearables": ("Shenzhen", "Dongguan", "Huizhou"),
    "automotive": ("Shenzhen", "Guangzhou", "Zhongshan"),
    "audio": ("Shenzhen", "Dongguan", "Huizhou"),
    "mobility": ("Shenzhen", "Ningbo", "Tianjin"),
    "energy": ("Shenzhen", "Ningbo", "Dongguan"),
}

#: Extra search terms per category. The trade-finder product name is often
#: a category phrase ("phone case silicone"), and the words a buyer would
#: actually type are the material and the buyer jargon, not the model name.
CATEGORY_SEARCH_TERMS: dict[str, tuple[str, ...]] = {
    "accessories": ("silicone phone case", "TPU soft case", "phone cover"),
    "electronics": ("mobile phone accessory", "charger", "power bank"),
    "home": ("LED strip light", "home improvement"),
    "home-tech": ("smart home device", "robot vacuum"),
    "kitchen": ("kitchenware set", "knife set"),
    "kitchen-tech": ("air fryer", "small appliance"),
    "beauty": ("hair brush", "wooden comb"),
    "beauty-tech": ("hair dryer", "electric toothbrush"),
    "fashion": ("tote bag", "sock", "compression"),
    "lifestyle": ("water bottle", "shopping bag", "straw"),
    "fitness": ("yoga mat", "resistance band"),
    "pet": ("pet harness", "dog leash"),
    "toys": ("educational toy", "stem toy"),
    "stationery": ("notebook", "journal"),
    "wearables": ("smart watch", "fitness tracker"),
    "automotive": ("car phone mount", "car charger"),
    "audio": ("bluetooth speaker", "headphones"),
    "mobility": ("electric scooter", "foldable"),
    "energy": ("portable power station"),
}

#: Product-level search terms, where the category term would send the buyer
#: to the wrong factory cluster. "compression socks" sits in the fashion
#: category, which also holds canvas tote bags — so the category terms
#: ("tote bag", "sock", "compression") put three unrelated products in one
#: search. The override wins for these products.
PRODUCT_SEARCH_TERMS: dict[str, tuple[str, ...]] = {
    "phone case silicone": ("silicone phone case", "TPU soft phone case"),
    "compression socks": ("compression socks", "graduated compression hosiery"),
    "reusable shopping bag": ("reusable shopping bag", "non-woven carry bag"),
    "reusable water bottle": ("stainless steel water bottle", "vacuum flask"),
    "canvas tote bag": ("canvas tote bag", "cotton shopper bag"),
    "wooden hair brush": ("wooden hair brush", "beech wood hair brush"),
    "pet harness": ("dog harness", "pet harness"),
    "led strip light 5m": ("LED strip light 5m", "5050 LED strip"),
    "smart plug wifi": ("WiFi smart plug", "smart socket"),
    "wireless earbuds": ("wireless earbuds", "true wireless earphones"),
    "car phone mount": ("car phone mount", "magnetic phone holder car"),
    "magnetic phone charger": ("magnetic phone charger", "wireless charging pad"),
    "smart watch": ("smart watch", "fitness tracker watch"),
    "bluetooth speaker": ("bluetooth speaker", "portable speaker"),
}

#: The filter set the repo already uses for supplier verification, taken
#: from `business-plan/04_90day_launch_checklist.md`. Same filters, applied
#: to the right category.
ALIBABA_FILTERS: tuple[str, ...] = (
    "Trade Assurance",
    "Gold Supplier",
    "Verified Supplier",
    "3+ years on Alibaba",
)

#: The smallest credible ceiling, as a fraction of the modelled source
#: cost. A route whose price ceiling falls below this cannot be sourced
#: at a price that would make the order worth placing — a yoga mat needs
#: a FOB of $0.02 to hit a 15% margin, which no factory will quote.
MIN_VIABLE_CEILING_RATIO = 0.25

#: MOQ bands. A supplier whose MOQ exceeds the order you intend to place
#: is not a candidate, whatever its prices look like.
MOQ_BANDS: tuple[tuple[str, int, int], ...] = (
    ("sample", 1, 100),
    ("small batch", 100, 300),
    ("standard", 300, 1000),
    ("bulk", 1000, 5000),
)

#: The payment terms the business plan asks for, used verbatim in the RFQ.
PREFERRED_PAYMENT_TERMS = "T/T 30% deposit, 70% against B/L copy"

#: Quote ladder. The volumes the business plan expects, plus a sample
#: order to check quality. The label is what the buyer calls that volume.
QUOTE_LADDER: tuple[tuple[str, int], ...] = (
    ("sample order", 100),
    ("first bulk", 500),
    ("first reorder", 1000),
    ("annual level", 5000),
)


# --------------------------------------------------------------------------- #
# Search strategy
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class SearchStrategy:
    """How to find candidate suppliers for one product."""

    product: str
    category: str
    dest_country: str
    search_terms: tuple[str, ...]
    alibaba_category_path: str
    cities: tuple[str, ...]
    filters: tuple[str, ...]
    order_units: int
    target_fob_usd: float
    moq_band: str
    max_moq: int
    search_queries: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "product": self.product,
            "category": self.category,
            "dest_country": self.dest_country,
            "search_terms": list(self.search_terms),
            "alibaba_category_path": self.alibaba_category_path,
            "cities": list(self.cities),
            "filters": list(self.filters),
            "order_units": self.order_units,
            "target_fob_usd": self.target_fob_usd,
            "moq_band": self.moq_band,
            "max_moq": self.max_moq,
            "search_queries": list(self.search_queries),
        }


def _moq_band(order_units: int) -> tuple[str, int]:
    """The MOQ band an order of this size can accept."""
    for label, low, high in MOQ_BANDS:
        if low <= order_units < high:
            return label, high
    return MOQ_BANDS[-1][0], MOQ_BANDS[-1][2]


def _search_queries(product: str, terms: tuple[str, ...], cities: tuple[str, ...]) -> tuple[str, ...]:
    """The literal strings to paste into the Alibaba search box."""
    queries: list[str] = []
    for term in terms:
        queries.append(term)
    # The product name itself is usually a better query than the category
    # term, but only when it adds something the terms do not.
    name = product.lower()
    if not any(name in q for q in queries):
        queries.insert(0, product)
    # City-qualified queries surface factories rather than trading offices.
    queries.append(f"{terms[0]} {cities[0]}" if terms else f"{product} {cities[0]}")
    return tuple(dict.fromkeys(queries))


def build_search_strategy(
    product: str,
    *,
    dest_country: str = "IN",
    order_units: int = 500,
) -> SearchStrategy | None:
    """Build the supplier-search plan for one product.

    Returns ``None`` if the product is not in the trade-finder universe or
    has no price for the destination — there is nothing to source towards.
    """
    fo = trade_finder_modules()["find_opportunities"]

    record = None
    for candidate in fo.PRODUCTS:
        if candidate["name"] == product:
            record = candidate
            break
    if record is None:
        return None
    if record["dst"].get(dest_country) is None:
        return None

    category = record["cat"]
    source_cost = record["src"].get("CN")
    if source_cost is None:
        return None

    terms = PRODUCT_SEARCH_TERMS.get(
        product, CATEGORY_SEARCH_TERMS.get(category, (product,))
    )
    cities = CATEGORY_CITIES.get(category, ("Shenzhen", "Guangzhou", "Ningbo"))
    band, max_moq = _moq_band(order_units)

    return SearchStrategy(
        product=product,
        category=category,
        dest_country=dest_country,
        search_terms=terms,
        alibaba_category_path=ALIBABA_CATEGORY_PATHS.get(category, "Consumer Electronics"),
        cities=cities,
        filters=ALIBABA_FILTERS,
        order_units=order_units,
        target_fob_usd=source_cost,
        moq_band=band,
        max_moq=max_moq,
        search_queries=_search_queries(product, terms, cities),
    )


# --------------------------------------------------------------------------- #
# RFQ draft
# --------------------------------------------------------------------------- #


@dataclass
class RfqDraft:
    """A ready-to-send RFQ for one product."""

    product: str
    dest_country: str
    subject: str
    body: str
    target_fob_usd: float
    order_units: int
    max_moq: int
    search_queries: tuple[str, ...]
    cities: tuple[str, ...]
    filters: tuple[str, ...]
    questions: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "product": self.product,
            "dest_country": self.dest_country,
            "subject": self.subject,
            "body": self.body,
            "target_fob_usd": self.target_fob_usd,
            "order_units": self.order_units,
            "max_moq": self.max_moq,
            "search_queries": list(self.search_queries),
            "cities": list(self.cities),
            "filters": list(self.filters),
            "questions": list(self.questions),
        }


#: Questions worth asking every supplier. Some are generic; the product
#: specific ones are appended by :func:`_product_questions`.
_COMMON_QUESTIONS: tuple[str, ...] = (
    "FOB {city} price per unit (USD) at: {ladder}",
    "Sample cost (2-3 units) + DHL, refundable against the bulk PO?",
    "Lead time from PO + deposit to FOB, in business days, for {order} units",
    "Payment terms — {terms}?",
    "Custom branding: MOQ, one-time tooling cost, lead-time impact?",
    "Certifications (PDF, recent batch) and 2-3 export references",
    "Pre-shipment inspection — can a third party inspect at your factory?",
)

#: Product-specific questions. The generic ladder asks for a price; these
#: ask whether the price is for the thing you actually want.
_PRODUCT_QUESTIONS: dict[str, tuple[str, ...]] = {
    "phone case silicone": (
        "Is the $0.45 target for soft-touch silicone, or hard TPU?",
        "Per-SKU pricing — is that the generic case or a specific model "
        "(iPhone 15/16, Samsung S24/S25)? A fitted case costs more.",
        "Camera cutout: raised lip protection, 1.5mm?",
        "Inner microfibre lining?",
        "Non-yellowing tested to 6 months?",
        "Does the price include the retail box and a barcode label on the "
        "outer box (needed for marketplace fulfilment)?",
    ),
    "compression socks": (
        "Compression level in mmHg, and the size range (EU 36-46)?",
        "Is the price per pair or per unit?",
        "Material: nylon/spandex percentage?",
    ),
    "reusable shopping bag": (
        "Material and GSM — is this non-woven, canvas, or recycled PET?",
        "Does the price include the printed logo?",
    ),
    "wooden hair brush": (
        "Bristle material — boar, nylon, or mixed?",
        "Is the price for a packed retail unit with a hang tag?",
    ),
    "reusable water bottle": (
        "Capacity in ml, and is it single-wall or double-wall vacuum?",
        "BPA-free and food-grade certification?",
    ),
    "canvas tote bag": (
        "Is the price for a blank bag or a printed one?",
    ),
    "pet harness": (
        "Does the price cover the harness alone or the set?",
        "Size range and the hardware (buckles, D-rings) included?",
    ),
}


def _product_questions(product: str) -> tuple[str, ...]:
    """Product-specific questions, with a generic fallback."""
    specific = _PRODUCT_QUESTIONS.get(product)
    if specific:
        return specific
    return (
        "What exactly is included in the quoted unit (contents of the "
        "package, not just the outer box)?",
        "Is the quoted price the same across every SKU, or cheapest-SKU only?",
    )


def _ladder_text() -> str:
    return ", ".join(f"{units} units ({label})" for label, units in QUOTE_LADDER)


def build_rfq(
    product: str,
    *,
    dest_country: str = "IN",
    order_units: int = 500,
    buyer_name: str = "",
    company: str = "",
) -> RfqDraft | None:
    """Draft the RFQ email for a product, with the real numbers in it.

    The target price is the trade-finder's modelled source cost, so the RFQ
    asks for a price the margin model can actually support.
    """
    strategy = build_search_strategy(
        product, dest_country=dest_country, order_units=order_units
    )
    if strategy is None:
        return None

    fo = trade_finder_modules()["find_opportunities"]
    record = next(p for p in fo.PRODUCTS if p["name"] == product)
    dest_price = record["dst"][dest_country]

    subject = (
        f"RFQ — {product} {order_units}u FOB {strategy.cities[0]} "
        f"→ {dest_country} marketplace"
    )

    questions = tuple(
        q.format(
            city=strategy.cities[0],
            ladder=_ladder_text(),
            order=order_units,
            terms=PREFERRED_PAYMENT_TERMS,
        )
        for q in _COMMON_QUESTIONS
    )
    questions = questions + _product_questions(product)

    target = strategy.target_fob_usd
    # The most the margin model can absorb. Push past it and the route dies.
    max_fob = _max_affordable_fob(record, dest_country, target)

    body_lines = [
        "Hi,",
        "",
        f"I'm sourcing a long-term supplier for {product}, sold on "
        f"{dest_country} marketplaces. This is a repeat-order product "
        f"category, so I'm looking for a manufacturing partner rather than "
        f"a trading company.",
        "",
        "WHY THIS PRODUCT",
        f"- Destination price point: ${dest_price:.2f} retail",
        f"- Target FOB: ${target:.2f}/unit at {order_units} units",
        f"- Landed cost to me (shipping + tariff + marketplace fee): "
        f"depends on final FOB, but the route works at ${target:.2f}",
        f"- Maximum FOB that still leaves a workable margin: ${max_fob:.2f}",
        f"- First order: {order_units} units, with reorders at 1,000-2,000 "
        f"units if quality holds",
        "",
        "PLEASE QUOTE",
    ]
    body_lines.extend(f"{i}. {q}" for i, q in enumerate(questions, start=1))
    body_lines.extend(
        [
            "",
            "ALSO CONFIRM",
            "- Factory or trading company? Which city is the factory in?",
            f"- Do you accept {PREFERRED_PAYMENT_TERMS}?",
            "- Sample lead time, and sample cost refunded against the bulk PO?",
            "",
            f"If the quote lands at or below ${target:.2f} FOB we can move "
            f"to samples immediately. Please reply in English.",
            "",
            "Best regards,",
            buyer_name or "[Your Name]",
            company or "[Company]",
        ]
    )

    return RfqDraft(
        product=product,
        dest_country=dest_country,
        subject=subject,
        body="\n".join(body_lines),
        target_fob_usd=target,
        order_units=order_units,
        max_moq=strategy.max_moq,
        search_queries=strategy.search_queries,
        cities=strategy.cities,
        filters=strategy.filters,
        questions=questions,
    )


def _candidate_platforms(dest_country: str) -> tuple[str, ...]:
    """The marketplaces worth modelling for a destination.

    For India the repo's ``_platform_for`` picks the highest-*volume*
    marketplace per category, which is the right call when you only care
    about reach. It is not the right call when you care about margin: a
    4-point fee difference decides whether a route clears the floor at all.

    So the trade-finder default is tried first, and the other Indian
    marketplaces are offered as alternatives. The best-margin one wins.

    Only Amazon.in and Flipkart are considered for India, because those
    are the two the repo documents ("the dominant marketplaces are
    Amazon.in and Flipkart, not the Western ones"). Etsy's 12% fee is a
    Western rate — Etsy does not sell in India, so a margin computed
    with it would be fiction.
    """
    fo = trade_finder_modules()["find_opportunities"]
    if dest_country == "IN":
        return ("amazon_in", "flipkart")
    return (fo._platform_for(dest_country, "electronics"),)


def _best_platform(
    record: dict[str, Any], dest_country: str
) -> tuple[str, float]:
    """The marketplace with the best margin for this route, and that margin.

    Returns the platform name and the margin percentage at the modelled
    source cost.
    """
    fo = trade_finder_modules()["find_opportunities"]
    meta = fo.COUNTRY_META[dest_country]
    dest_price = record["dst"][dest_country]
    shipping = meta["ship_per_kg"] * record["kg"]

    best_platform = fo._platform_for(dest_country, record["cat"])
    best_margin = -1.0
    for platform in _candidate_platforms(dest_country):
        fee_rate = fo.PLATFORM_FEES.get(platform, 0.0)
        landed = (
            record["src"].get("CN", 0.0)
            + shipping
            + record["src"].get("CN", 0.0) * meta["tariff_avg"]
            + dest_price * fee_rate
        )
        margin = (dest_price - landed) / dest_price
        if margin > best_margin:
            best_platform, best_margin = platform, margin
    return best_platform, best_margin


def _marketplaces_for(
    record: dict[str, Any], dest_country: str
) -> list[dict[str, Any]]:
    """Every marketplace this product can be sold on, and what each earns.

    The marketplace is a decision, so the plan shows all of them with
    their margins rather than only the winner — the runner-up is a
    genuine second option, and its absence would hide a route that
    clears the floor when the best one does not.
    """
    fo = trade_finder_modules()["find_opportunities"]
    meta = fo.COUNTRY_META[dest_country]
    dest_price = record["dst"][dest_country]
    source_cost = record["src"].get("CN", 0.0)
    shipping = meta["ship_per_kg"] * record["kg"]

    out: list[dict[str, Any]] = []
    for platform in _candidate_platforms(dest_country):
        fee_rate = fo.PLATFORM_FEES.get(platform, 0.0)
        landed = (
            source_cost
            + shipping
            + source_cost * meta["tariff_avg"]
            + dest_price * fee_rate
        )
        margin = (dest_price - landed) / dest_price
        out.append(
            {
                "platform": platform,
                "fee_pct": round(fee_rate * 100, 1),
                "landed_cost_usd": round(landed, 2),
                "margin_pct": round(margin, 4),
                "clears_floor": margin >= 0.15,
            }
        )
    out.sort(key=lambda m: -m["margin_pct"])
    return out


def _max_affordable_fob(
    record: dict[str, Any], dest_country: str, target_fob: float
) -> float:
    """The highest FOB that still clears the margin floor.

    Landed cost is FOB + shipping + tariff + platform fee, and the tariff
    is a percentage of FOB, so this is solved rather than searched:
    ``margin_floor * price = FOB*(1+tariff) + shipping + fee``.

    Returns 0.0 when *no* price clears the floor — for some products the
    destination price cannot support the floor at any FOB, and that is a
    fact about the route, not a missing number.
    """
    fo = trade_finder_modules()["find_opportunities"]
    meta = fo.COUNTRY_META[dest_country]
    dest_price = record["dst"][dest_country]
    platform, _ = _best_platform(record, dest_country)
    fee_rate = fo.PLATFORM_FEES.get(platform, 0.0)

    shipping = meta["ship_per_kg"] * record["kg"]
    platform_fee = dest_price * fee_rate
    floor = 0.15

    # A ceiling is only meaningful if the route clears the floor at some
    # price. When it does not, the algebraic solution is a small positive
    # number rather than zero, which would read as "buy it for 2 cents".
    if not _route_is_viable(record, dest_country):
        return 0.0

    # price - floor*price = FOB*(1+tariff) + shipping + fee
    contribution = dest_price * (1 - floor) - shipping - platform_fee
    if contribution <= 0:
        return 0.0
    return contribution / (1 + meta["tariff_avg"])


def _route_is_viable(record: dict[str, Any], dest_country: str) -> bool:
    """Can this route clear the margin floor at a price that makes sense?

    Two ways a route fails:

    1. Shipping and the marketplace fee alone eat the whole contribution.
       The route is unsourceable at any price.
    2. The route only clears the floor at an absurdly low FOB — a yoga mat
       needs a FOB of $0.02 to hit 15% margin, which no factory will
       quote and which would not cover the buyer's own costs.

    Both are worth saying plainly rather than sending an RFQ that cannot
    work, so the threshold is a fraction of the modelled source cost
    rather than a hard-coded dollar amount.
    """
    fo = trade_finder_modules()["find_opportunities"]
    meta = fo.COUNTRY_META[dest_country]
    dest_price = record["dst"][dest_country]
    platform, _ = _best_platform(record, dest_country)
    fee_rate = fo.PLATFORM_FEES.get(platform, 0.0)

    shipping = meta["ship_per_kg"] * record["kg"]
    platform_fee = dest_price * fee_rate
    contribution = dest_price * (1 - 0.15) - shipping - platform_fee
    if contribution <= 0:
        return False

    # The implied ceiling must be a credible fraction of the source cost.
    source_cost = record["src"].get("CN", 0.0)
    implied_ceiling = contribution / (1 + meta["tariff_avg"])
    return implied_ceiling >= source_cost * MIN_VIABLE_CEILING_RATIO


# --------------------------------------------------------------------------- #
# Coverage — the audit of what the verified pool actually covers
# --------------------------------------------------------------------------- #


@dataclass
class CoverageGap:
    """One product that clears the margin floor but has no verified supplier."""

    product: str
    category: str
    dest_country: str
    margin_pct: float
    demand_score: int | None
    target_fob_usd: float
    order_units: int
    platform: str = "amazon_in"
    verified_suppliers: list[str] = field(default_factory=list)
    adjacent_suppliers: list[str] = field(default_factory=list)
    needs_sourcing: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "product": self.product,
            "category": self.category,
            "dest_country": self.dest_country,
            "margin_pct": round(self.margin_pct, 4),
            "demand_score": self.demand_score,
            "target_fob_usd": self.target_fob_usd,
            "order_units": self.order_units,
            "platform": self.platform,
            "verified_suppliers": list(self.verified_suppliers),
            "adjacent_suppliers": list(self.adjacent_suppliers),
            "needs_sourcing": self.needs_sourcing,
        }


def _supplier_makes(supplier_products: str, product: str) -> bool:
    """Does a supplier's stated product line cover this product?

    Matching is on the meaningful words only — "smart watch" should not
    match "watch band", and "bag" should match "tote bag" but not
    "baggage". Short words are kept when they carry the category on their
    own ("pet tracker" is a pet product); common filler words are not.

    The match has to land on a *distinguishing* word. Every wearable
    supplier in the pool lists something with "smart" in it, so matching
    on "smart" would claim that all of them make "smart plug wifi" —
    which none of them do.
    """
    products = {p.strip().lower() for p in supplier_products.split(",")}
    product_words = _distinguishing_words(product)
    if not product_words:
        # The product name is made entirely of generic modifiers, so fall
        # back to the significant words — better a loose match than none.
        product_words = _significant_words(product)
    if not product_words:
        return False
    for entry in products:
        if product_words & _distinguishing_words(entry):
            return True
    return False


#: Words that never identify a product category on their own.
_FILLER_WORDS = frozenset(
    """
    with case cover pack set sets piece pieces pair pairs unit units
    reusable silicone soft hard premium quality type style new
    """.split()
)

#: Words that are too generic to identify a product on their own.
#:
#: "smart watch", "smart ring" and "kids smartwatch" all contain "smart",
#: so a product called "smart plug wifi" would match every wearable
#: supplier in the pool on that word alone — and none of them make smart
#: plugs. A match has to be on a word that actually distinguishes the
#: product, not on a modifier that happens to be shared.
_GENERIC_WORDS = frozenset(
    """
    smart wireless portable electric bluetooth digital premium pro
    basic classic original quality professional mini ultra
    """.split()
)


def _significant_words(text: str) -> set[str]:
    """The words in a product name that actually identify what it is."""
    words = {w for w in re.findall(r"[a-z]+", text.lower()) if len(w) > 2}
    return words - _FILLER_WORDS


def _distinguishing_words(text: str) -> set[str]:
    """The words in a product name that name the thing, not its modifiers.

    Used for supplier matching, where a shared modifier ("smart") must
    not be enough to claim a supplier makes the product.
    """
    return _significant_words(text) - _GENERIC_WORDS


def coverage_gaps(
    *,
    dest_country: str = "IN",
    order_units: int = 500,
    min_margin_pct: float = 0.15,
) -> list[CoverageGap]:
    """Every viable route, and whether a verified supplier covers it.

    This is the report that says, honestly, "for this product you have to
    go and find a supplier yourself" — which is true for most of the
    India opportunity set.
    """
    from .corpus import build_supplier_documents

    fo = trade_finder_modules()["find_opportunities"]
    di = trade_finder_modules()["demand_in"]
    demand = {r.product: r for r in di.get_demand_table()}

    suppliers = build_supplier_documents()

    gaps: list[CoverageGap] = []
    for record in fo.PRODUCTS:
        dest_price = record["dst"].get(dest_country)
        source_cost = record["src"].get("CN")
        if dest_price is None or source_cost is None:
            continue

        # Always price the route against the best-margin marketplace. The
        # category default is the highest-*volume* one, which is a
        # different question, and using both would mean the reported
        # margin and the price ceiling were computed on different
        # marketplaces.
        platform, margin = _best_platform(record, dest_country)
        if margin < min_margin_pct:
            continue

        matches = [
            d.metadata["name"]
            for d in suppliers
            if _supplier_makes(d.metadata["main_products"], record["name"])
        ]
        de = demand.get(record["name"])

        gaps.append(
            CoverageGap(
                product=record["name"],
                category=record["cat"],
                dest_country=dest_country,
                margin_pct=margin,
                demand_score=de.demand_score if de else None,
                target_fob_usd=source_cost,
                order_units=order_units,
                platform=platform,
                verified_suppliers=matches,
                needs_sourcing=not matches,
            )
        )

    gaps.sort(key=lambda g: (-(g.demand_score or 0), -g.margin_pct))
    return gaps


def sourcing_plan(
    product: str,
    *,
    dest_country: str = "IN",
    order_units: int = 500,
) -> dict[str, Any]:
    """The complete plan for sourcing one product.

    Search strategy, RFQ draft, and the margin the target price supports —
    everything needed to go and find a supplier, in one call.
    """
    strategy = build_search_strategy(
        product, dest_country=dest_country, order_units=order_units
    )
    if strategy is None:
        return {
            "ok": False,
            "product": product,
            "error": (
                f"Product {product!r} is not in the trade-finder universe or "
                f"has no {dest_country} destination price, so there is nothing "
                f"to source towards."
            ),
        }

    rfq = build_rfq(
        product, dest_country=dest_country, order_units=order_units
    )

    fo = trade_finder_modules()["find_opportunities"]
    record = next(p for p in fo.PRODUCTS if p["name"] == product)
    max_fob = _max_affordable_fob(record, dest_country, strategy.target_fob_usd)

    gaps = coverage_gaps(dest_country=dest_country, order_units=order_units)
    gap = next((g for g in gaps if g.product == product), None)
    viable = _route_is_viable(record, dest_country)

    warnings: list[str] = []
    if not viable:
        warnings.append(
            "This route cannot clear the 15% margin floor at any FOB — the "
            "shipping and marketplace fee alone exceed the contribution. Do "
            "not send an RFQ for it."
        )
    elif gap is None:
        warnings.append(
            "This product does not clear the margin floor at the modelled "
            "source cost. An RFQ is only worth sending if the supplier "
            "quotes materially below the target."
        )
    if gap is not None and gap.needs_sourcing:
        warnings.append(
            "No verified supplier in the pool makes this product. The RFQ "
            "has to go to a newly sourced supplier."
        )
    room = max_fob - strategy.target_fob_usd
    if viable and room < 0.01:
        warnings.append(
            "No negotiation room: the target FOB already sits on the margin "
            "floor, so any price above it fails. A supplier who quotes over "
            f"${strategy.target_fob_usd:.2f} is not viable, and there is no "
            "headroom to concede on anything else."
        )
    elif viable and room < 0.10:
        warnings.append(
            f"Thin margin of ${room:.2f}/unit "
            "between the target and the ceiling. A small price move or a "
            "tariff change wipes this route out, so get a firm quote "
            "before committing."
        )

    return {
        "ok": True,
        "product": product,
        "dest_country": dest_country,
        "strategy": strategy.to_dict(),
        "rfq": rfq.to_dict() if rfq else None,
        "economics": {
            "target_fob_usd": strategy.target_fob_usd,
            "max_fob_usd": round(max_fob, 2),
            "negotiation_room_usd": round(max_fob - strategy.target_fob_usd, 2),
            "route_viable_at_any_price": viable,
            "platform": gap.platform if gap else _best_platform(record, dest_country)[0],
            "destination_price_usd": record["dst"].get(dest_country),
        },
        "verified_suppliers": gap.verified_suppliers if gap else [],
        "needs_sourcing": gap.needs_sourcing if gap else True,
        "margin_pct": round(gap.margin_pct, 4) if gap else None,
        "demand_score": gap.demand_score if gap else None,
        "marketplaces": _marketplaces_for(record, dest_country),
        "warnings": warnings,
    }
