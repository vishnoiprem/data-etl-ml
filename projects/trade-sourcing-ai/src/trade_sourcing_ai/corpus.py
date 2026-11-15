"""Build a searchable corpus from the real trade-finder dataset.

The point of this module is that **every document traces back to a file in the
repo**. Each :class:`Document` carries ``source_path`` and ``source_line``, so
when the agent cites a supplier the citation can be checked against the source
file by hand. Nothing here is invented.

Three document families:

``product``
    One per product/route in the trade-finder universe, enriched with the
    India demand score when the product has one.

``supplier``
    One per candidate supplier, carrying the verified scores
    (authenticity / price / reliability) and risk flags.

``reputation``
    One per supplier that made the shortlist, carrying the 10,000-cycle
    Monte-Carlo stats from ``reports/supplier_shortlist.md``.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import TRADE_FINDER_DIR, TRADE_FINDER_MODULES

# --------------------------------------------------------------------------- #
# Document model
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Document:
    """One retrievable document with provenance."""

    doc_id: str
    doc_type: str  # "product" | "supplier" | "reputation"
    title: str
    text: str
    source_path: str
    source_line: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "doc_type": self.doc_type,
            "title": self.title,
            "text": self.text,
            "source_path": self.source_path,
            "source_line": self.source_line,
            "metadata": self.metadata,
        }


# --------------------------------------------------------------------------- #
# Loading the sibling trade-finder modules
# --------------------------------------------------------------------------- #


def _load_trade_finder_modules():
    """Import the real trade-finder modules by path.

    They sit outside this project (as siblings), so a plain package import
    will not resolve. We prepend the directory to ``sys.path`` once.
    """
    if str(TRADE_FINDER_DIR) not in sys.path:
        sys.path.insert(0, str(TRADE_FINDER_DIR))

    modules = {}
    for name in TRADE_FINDER_MODULES:
        path = TRADE_FINDER_DIR / f"{name}.py"
        if not path.exists():
            raise FileNotFoundError(
                f"Required trade-finder module not found at {path}. "
                f"This project reasons over projects/realtime-stock-pipeline/trade-finder/ "
                f"and cannot run without it."
            )
        try:
            modules[name] = __import__(name)
        except Exception as exc:  # pragma: no cover - import-time failure path
            raise ImportError(
                f"Could not import trade-finder module {name!r} from {TRADE_FINDER_DIR}: {exc}"
            ) from exc
    return modules


_MODULES: dict[str, Any] | None = None


def trade_finder_modules() -> dict[str, Any]:
    """Return the imported trade-finder modules (cached)."""
    global _MODULES
    if _MODULES is None:
        _MODULES = _load_trade_finder_modules()
    return _MODULES


def _rel(path: Path) -> str:
    """Repo-relative path for a provenance field."""
    try:
        return str(path.relative_to(TRADE_FINDER_DIR.parents[2]))
    except ValueError:
        return str(path)


# --------------------------------------------------------------------------- #
# Product documents
# --------------------------------------------------------------------------- #


def _demand_lookup() -> dict[str, dict[str, Any]]:
    """The India demand lookup from ``demand_in.py``.

    We use ``get_demand_table()`` rather than the raw ``DEMAND`` dict because
    the raw dict only holds the three sub-scores; the composite
    ``demand_score`` is derived by ``_score_product``.
    """
    di = trade_finder_modules()["demand_in"]
    return {row.product: row for row in di.get_demand_table()}


#: The source countries the shortlisted suppliers actually operate from.
#: `verify_suppliers.SUPPLIERS` is entirely Shenzhen-based, so sourcing from
#: anywhere else is not a decision this agent can make.
SOURCE_COUNTRIES = ("CN", "VN")

#: The destination markets the business targets, per the trade-finder demand
#: work and the business plan.
DEST_COUNTRIES = ("IN", "UK", "US")


def build_product_documents() -> list[Document]:
    """One document per product/route combination that clears the margin floor.

    The trade-finder model prices each product across many source and
    destination countries. We keep the routes that are actually viable
    (margin above the floor) and that a Shenzhen-based supplier could
    realistically serve, so the corpus reflects the real opportunity set
    rather than every theoretical country pair.
    """
    fo = trade_finder_modules()["find_opportunities"]
    demand = _demand_lookup()

    docs: list[Document] = []
    for product in fo.PRODUCTS:
        name = product["name"]
        demand_entry = demand.get(name)
        for source_cc in SOURCE_COUNTRIES:
            source_cost = product["src"].get(source_cc)
            if source_cost is None:
                continue
            for dest_cc in DEST_COUNTRIES:
                dest_price = product["dst"].get(dest_cc)
                if dest_price is None:
                    continue
                landed = _landed_cost(
                    fo=fo,
                    product=product,
                    source_cc=source_cc,
                    dest_cc=dest_cc,
                    source_cost=source_cost,
                )
                if landed is None:
                    continue
                margin_pct = (dest_price - landed["landed_cost_usd"]) / dest_price
                if margin_pct < 0.05:
                    continue

                parts = [
                    f"Product: {name}.",
                    f"Category: {product['cat']}.",
                    f"Route: {source_cc} to {dest_cc}.",
                    f"Weight: {product['kg']} kg per unit.",
                    f"Source unit cost: ${source_cost:.2f}.",
                    f"Destination retail price: ${dest_price:.2f}.",
                    f"Landed cost: ${landed['landed_cost_usd']:.2f} "
                    f"(shipping ${landed['shipping_usd']:.2f}, "
                    f"tariff ${landed['tariff_usd']:.2f}, "
                    f"platform fee ${landed['platform_fee_usd']:.2f}).",
                    f"Margin: {margin_pct * 100:.1f}% "
                    f"(${dest_price - landed['landed_cost_usd']:.2f} per unit).",
                ]
                if demand_entry:
                    parts.append(
                        f"India demand score: {demand_entry.demand_score}. "
                        f"Category volume {demand_entry.category_volume}/50, "
                        f"price fit {demand_entry.price_fit}/30, "
                        f"import dependency {demand_entry.import_dependency}/20."
                    )
                    hint = demand_entry.bsr_hint
                    if hint:
                        parts.append(f"Market position: {hint}.")

                docs.append(
                    Document(
                        doc_id=f"product:{name}:{source_cc}->{dest_cc}",
                        doc_type="product",
                        title=f"{name} — {source_cc} to {dest_cc}",
                        text=" ".join(parts),
                        source_path=_rel(TRADE_FINDER_DIR / "find_opportunities.py"),
                        source_line=_line_of(fo, "PRODUCTS"),
                        metadata={
                            "product": name,
                            "category": product["cat"],
                            "source_country": source_cc,
                            "dest_country": dest_cc,
                            "margin_pct": round(margin_pct, 4),
                            "dest_price_usd": dest_price,
                            "landed_cost_usd": round(landed["landed_cost_usd"], 4),
                            "weight_kg": product["kg"],
                            "demand_score": (
                                demand_entry.demand_score if demand_entry else None
                            ),
                        },
                    )
                )
    return docs


def _landed_cost(
    *,
    fo: Any,
    product: dict[str, Any],
    source_cc: str,
    dest_cc: str,
    source_cost: float,
) -> dict[str, float] | None:
    """Recompute landed cost with the trade-finder's own fee logic.

    This mirrors ``find_opportunities._build_opportunities`` but takes the
    source cost as a parameter, so a *quoted* price can be pushed through the
    exact same arithmetic as the baseline model.
    """
    meta = fo.COUNTRY_META.get(dest_cc)
    if meta is None:
        return None
    platform = fo._platform_for(dest_cc, product["cat"])
    fee_rate = fo.PLATFORM_FEES.get(platform, 0.0)

    weight = product["kg"]
    shipping = meta["ship_per_kg"] * weight
    tariff = source_cost * meta["tariff_avg"]
    platform_fee = dest_price_of(product, dest_cc) * fee_rate
    return {
        "shipping_usd": shipping,
        "tariff_usd": tariff,
        "platform_fee_usd": platform_fee,
        "landed_cost_usd": source_cost + shipping + tariff + platform_fee,
        "platform": platform,
    }


def dest_price_of(product: dict[str, Any], dest_cc: str) -> float:
    return float(product["dst"].get(dest_cc, 0.0))


def _line_of(module: Any, symbol: str) -> int:
    """Best-effort source line for a module-level symbol."""
    import inspect

    try:
        source = inspect.getsource(module)
    except (OSError, TypeError):  # pragma: no cover
        return 0
    for idx, line in enumerate(source.splitlines(), start=1):
        if line.startswith(f"{symbol}") or line.startswith(f"{symbol} "):
            return idx
    return 0


# --------------------------------------------------------------------------- #
# Supplier documents
# --------------------------------------------------------------------------- #


def build_supplier_documents() -> list[Document]:
    """One document per candidate supplier, with verified scores."""
    vs = trade_finder_modules()["verify_suppliers"]

    docs: list[Document] = []
    for raw in vs.SUPPLIERS:
        # noise_pct=0 and a fixed seed so the scores are deterministic and
        # match the shortlist report.
        scored = vs._score_one(raw, noise_pct=0.0, rng_seed=0)

        parts = [
            f"Supplier: {raw['name']}.",
            f"Alibaba ID: {raw['alibaba_id']}.",
            f"Location: {raw['city']}, China.",
            f"Years on Alibaba: {raw['years_on_alibaba']}.",
            f"12-month transaction volume: ${raw['transaction_12mo_usd']:,}.",
            f"Response rate: {raw['response_rate'] * 100:.0f}% "
            f"(median {raw['response_time_h']}h).",
            f"Trade Assurance: {'yes' if raw['trade_assurance'] else 'no'}.",
            f"Gold supplier: {'yes' if raw['gold_supplier'] else 'no'}. "
            f"Verified supplier: {'yes' if raw['verified_supplier'] else 'no'}.",
            f"Factory size: {raw['factory_size_m2']:,} m2, {raw['staff_count']} staff.",
            f"OEM/ODM: {'yes' if raw['oem_odm'] else 'no'}.",
            f"CE/RoHS certified: {'yes' if raw['has_ce_rohs'] else 'no'}.",
            f"Minimum order: {raw['min_order_qty']} units.",
            f"FOB price: ${scored.fob_price_usd_500u:.2f} at 500 units, "
            f"${scored.fob_price_usd_1000u:.2f} at 1000 units.",
            f"Lead time: {scored.lead_time_days} days.",
            f"Sample policy: {raw['sample_policy']}.",
            f"Main products: {raw['main_products']}.",
            f"Composite score: {scored.composite_score}/10 "
            f"(authenticity {scored.authenticity_score}, price {scored.price_score}, "
            f"reliability {scored.reliability_score}).",
            f"Risk level: {scored.risk_level}.",
            f"Supplier notes: {raw['notes']}.",
        ]
        if scored.flags:
            parts.append(f"Risk flags: {', '.join(scored.flags)}.")

        docs.append(
            Document(
                doc_id=f"supplier:{raw['alibaba_id']}",
                doc_type="supplier",
                title=raw["name"],
                text=" ".join(parts),
                source_path=_rel(TRADE_FINDER_DIR / "verify_suppliers.py"),
                source_line=_line_of(vs, "SUPPLIERS"),
                metadata={
                    "alibaba_id": raw["alibaba_id"],
                    "name": raw["name"],
                    "city": raw["city"],
                    "fob_price_usd_500u": scored.fob_price_usd_500u,
                    "fob_price_usd_1000u": scored.fob_price_usd_1000u,
                    "lead_time_days": scored.lead_time_days,
                    "min_order_qty": raw["min_order_qty"],
                    "composite_score": scored.composite_score,
                    "authenticity_score": scored.authenticity_score,
                    "price_score": scored.price_score,
                    "reliability_score": scored.reliability_score,
                    "risk_level": scored.risk_level,
                    "flags": list(scored.flags),
                    "response_rate": raw["response_rate"],
                    "response_time_h": raw["response_time_h"],
                    "trade_assurance": raw["trade_assurance"],
                    "has_ce_rohs": raw["has_ce_rohs"],
                    "sample_policy": raw["sample_policy"],
                    "main_products": raw["main_products"],
                    "notes": raw["notes"],
                },
            )
        )
    return docs


# --------------------------------------------------------------------------- #
# Reputation documents (from the shortlist report)
# --------------------------------------------------------------------------- #

_HEADING_RE = re.compile(r"^###\s+\d+\.\s+(.+?)\s*$", re.MULTILINE)
_FIELD_RE = re.compile(r"^-\s+\*\*(.+?):\*\*\s*(.+?)\s*$", re.MULTILINE)


def build_reputation_documents() -> list[Document]:
    """One document per shortlisted supplier, parsed from the shortlist report.

    The shortlist report carries the 10,000-cycle Monte-Carlo statistics
    (average rank, sigma, top-1 finish rate) which the supplier records do
    not have. We parse it rather than hard-coding the numbers, so the document
    stays true to the report if the report changes.
    """
    report = TRADE_FINDER_DIR / "reports" / "supplier_shortlist.md"
    if not report.exists():
        return []

    text = report.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Split on "### N. <Name>" headings, keeping the heading line numbers.
    starts: list[tuple[int, str]] = []
    for idx, line in enumerate(lines, start=1):
        match = _HEADING_RE.match(line)
        if match:
            starts.append((idx, match.group(1)))

    docs: list[Document] = []
    for pos, (line_no, heading) in enumerate(starts):
        end = starts[pos + 1][0] if pos + 1 < len(starts) else len(lines) + 1
        block = "\n".join(lines[line_no - 1 : end - 1])

        fields = {k.strip(): v.strip() for k, v in _FIELD_RE.findall(block)}
        alibaba_id = fields.get("Alibaba ID", "").strip("`")

        parts = [f"Supplier reputation history for {heading}."]
        for key in (
            "Alibaba ID",
            "FOB price (500u)",
            "Lead time",
            "Min order",
            "Sample policy",
            "Main products",
            "Risk level",
            "Avg rank across 10K cycles",
            "Composite score",
            "Top-1 finishes",
            "Notes",
        ):
            if key in fields:
                parts.append(f"{key}: {fields[key]}.")

        docs.append(
            Document(
                doc_id=f"reputation:{alibaba_id or heading}",
                doc_type="reputation",
                title=f"Reputation — {heading}",
                text=" ".join(parts),
                source_path=_rel(report),
                source_line=line_no,
                metadata={
                    "alibaba_id": alibaba_id,
                    "name": heading,
                    "composite_score": _to_float(fields.get("Composite score")),
                    "risk_level": fields.get("Risk level"),
                    "lead_time_days": _to_int(fields.get("Lead time")),
                    "avg_rank": _to_float(fields.get("Avg rank across 10K cycles")),
                    "top1_finishes": fields.get("Top-1 finishes"),
                    "notes": fields.get("Notes"),
                },
            )
        )
    return docs


def _to_float(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", value)
    return float(match.group(0)) if match else None


def _to_int(value: str | None) -> int | None:
    result = _to_float(value)
    return int(result) if result is not None else None


# --------------------------------------------------------------------------- #
# Corpus assembly
# --------------------------------------------------------------------------- #


def build_corpus() -> list[Document]:
    """The full document corpus: products + suppliers + reputation."""
    return (
        build_product_documents()
        + build_supplier_documents()
        + build_reputation_documents()
    )


def corpus_summary(documents: list[Document] | None = None) -> dict[str, Any]:
    """Counts by type, for the health endpoint and the README."""
    docs = documents if documents is not None else build_corpus()
    by_type: dict[str, int] = {}
    for doc in docs:
        by_type[doc.doc_type] = by_type.get(doc.doc_type, 0) + 1
    return {
        "total_documents": len(docs),
        "by_type": by_type,
        "source_paths": sorted({doc.source_path for doc in docs}),
    }
