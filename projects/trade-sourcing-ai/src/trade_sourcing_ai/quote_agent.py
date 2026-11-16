"""Compare supplier quotes against the margin model and recommend one supplier.

This is the business core of the project. The decision is made in plain
Python against the *real* trade-finder arithmetic — the same landed-cost
model that produced the baseline opportunity set — so the recommendation is
deterministic, testable and reproducible.

The LLM is not consulted here. It is used afterwards, in
:func:`explain_recommendation`, to turn a structured rationale into prose.

Scoring, in priority order:

1. **Margin** — the quoted FOB price is pushed through the real landed-cost
   model. A quote that erodes margin below the floor is disqualified.
2. **Risk** — a high composite risk level disqualifies a quote regardless of
   price, because a cheap quote from a risky supplier is not a cheap quote.
3. **Lead time** — a quote that cannot arrive before the deadline is
   disqualified, even if it is the cheapest.
4. **Supplier score** — among the survivors, the verified composite score
   breaks ties.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from .corpus import trade_finder_modules
from .quotes import Quote

#: Weights for the final ranking. Margin dominates because it is the thing
#: that determines whether the order makes money; the rest break ties.
SCORE_WEIGHTS = {
    "margin": 0.55,
    "supplier_score": 0.25,
    "lead_time": 0.20,
}

#: Lead time that scores full marks. Anything at or under this is fine.
IDEAL_LEAD_TIME_DAYS = 15

#: Lead time at which the lead-time score reaches zero.
MAX_LEAD_TIME_DAYS = 45


@dataclass
class QuoteEvaluation:
    """One quote, priced and scored."""

    quote: Quote
    landed_cost_usd: float = 0.0
    shipping_usd: float = 0.0
    tariff_usd: float = 0.0
    platform_fee_usd: float = 0.0
    dest_price_usd: float = 0.0
    margin_usd: float = 0.0
    margin_pct: float = 0.0
    margin_at_order_usd: float = 0.0
    baseline_fob_usd: float = 0.0
    fob_delta_usd: float = 0.0
    fob_delta_pct: float = 0.0
    supplier_score: float = 0.0
    risk_level: str = "unknown"
    risk_flags: list[str] = field(default_factory=list)
    composite_score: float = 0.0
    score: float = 0.0
    disqualified: bool = False
    disqualification_reasons: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def alibaba_id(self) -> str:
        return self.quote.alibaba_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "quote_id": self.quote.quote_id,
            "alibaba_id": self.alibaba_id,
            "supplier_name": self.quote.supplier_name,
            "product": self.quote.product,
            "dest_country": self.quote.dest_country,
            "order_units": self.quote.order_units,
            "fob_usd": self.quote.fob_usd,
            "baseline_fob_usd": self.baseline_fob_usd,
            "fob_delta_usd": round(self.fob_delta_usd, 4),
            "fob_delta_pct": round(self.fob_delta_pct, 4),
            "lead_time_days": self.quote.lead_time_days,
            "moq": self.quote.moq,
            "landed_cost_usd": round(self.landed_cost_usd, 4),
            "shipping_usd": round(self.shipping_usd, 4),
            "tariff_usd": round(self.tariff_usd, 4),
            "platform_fee_usd": round(self.platform_fee_usd, 4),
            "dest_price_usd": round(self.dest_price_usd, 4),
            "margin_usd": round(self.margin_usd, 4),
            "margin_pct": round(self.margin_pct, 4),
            "margin_at_order_usd": round(self.margin_at_order_usd, 2),
            "supplier_score": self.supplier_score,
            "composite_score": self.composite_score,
            "risk_level": self.risk_level,
            "risk_flags": list(self.risk_flags),
            "score": round(self.score, 4),
            "disqualified": self.disqualified,
            "disqualification_reasons": list(self.disqualification_reasons),
            "conflicts": list(self.conflicts),
            "notes": list(self.notes),
        }


@dataclass
class Recommendation:
    """The agent's decision, with everything needed to audit it."""

    product: str
    dest_country: str
    order_units: int
    recommended: QuoteEvaluation | None
    evaluations: list[QuoteEvaluation] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    confidence: float = 0.0
    total_latency_ms: float = 0.0
    stages: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "product": self.product,
            "dest_country": self.dest_country,
            "order_units": self.order_units,
            "recommended": self.recommended.to_dict() if self.recommended else None,
            "evaluations": [e.to_dict() for e in self.evaluations],
            "rationale": list(self.rationale),
            "conflicts": list(self.conflicts),
            "confidence": round(self.confidence, 4),
            "total_latency_ms": round(self.total_latency_ms, 3),
            "stages": self.stages,
        }


# --------------------------------------------------------------------------- #
# Lookup helpers
# --------------------------------------------------------------------------- #


def _product_record(product: str) -> dict[str, Any] | None:
    """Find a product in the trade-finder universe, tolerating naming drift."""
    fo = trade_finder_modules()["find_opportunities"]
    for record in fo.PRODUCTS:
        if record["name"] == product:
            return record
    # Fall back to a fuzzy match so "smartwatch fitness band" finds
    # "smartwatch fitness band" written slightly differently by the user.
    normalised = product.lower().strip()
    for record in fo.PRODUCTS:
        if normalised in record["name"].lower() or record["name"].lower() in normalised:
            return record
    return None


def _supplier_record(alibaba_id: str) -> dict[str, Any] | None:
    vs = trade_finder_modules()["verify_suppliers"]
    for raw in vs.SUPPLIERS:
        if raw["alibaba_id"] == alibaba_id:
            return raw
    return None


def _source_country_for(product: dict[str, Any], dest_country: str) -> str:
    """Pick the source country for a product/destination pair.

    China is the default because every shortlisted supplier is Shenzhen-based.
    Vietnam is used when the product is sourced there in the trade-finder
    model and the China route is not viable.
    """
    for candidate in ("CN", "VN"):
        if candidate in product["src"] and candidate in product["dst"]:
            return candidate
    return next(iter(product["src"]))


# --------------------------------------------------------------------------- #
# Pricing
# --------------------------------------------------------------------------- #


def price_quote(
    quote: Quote,
    *,
    min_margin_pct: float,
) -> QuoteEvaluation:
    """Push one quote through the real landed-cost model."""
    fo = trade_finder_modules()["find_opportunities"]
    vs = trade_finder_modules()["verify_suppliers"]

    evaluation = QuoteEvaluation(quote=quote)

    product = _product_record(quote.product)
    if product is None:
        evaluation.disqualified = True
        evaluation.disqualification_reasons.append(
            f"Product {quote.product!r} is not in the trade-finder product universe, "
            f"so its margin cannot be modelled."
        )
        return evaluation

    dest_cc = quote.dest_country
    dest_price = product["dst"].get(dest_cc)
    if dest_price is None:
        evaluation.disqualified = True
        available = ", ".join(sorted(product["dst"]))
        evaluation.disqualification_reasons.append(
            f"The trade-finder model has no {dest_cc} price for {product['name']!r}. "
            f"It is priced for: {available}. A destination price is required to "
            f"compute margin, so this quote cannot be priced."
        )
        return evaluation

    source_cc = _source_country_for(product, dest_cc)
    meta = fo.COUNTRY_META.get(dest_cc)
    if meta is None:
        evaluation.disqualified = True
        evaluation.disqualification_reasons.append(f"Unknown destination country {dest_cc}.")
        return evaluation

    platform = fo._platform_for(dest_cc, product["cat"])
    fee_rate = fo.PLATFORM_FEES.get(platform, 0.0)

    shipping = meta["ship_per_kg"] * product["kg"]
    tariff = quote.fob_usd * meta["tariff_avg"]
    platform_fee = dest_price * fee_rate
    landed = quote.fob_usd + shipping + tariff + platform_fee

    evaluation.landed_cost_usd = landed
    evaluation.shipping_usd = shipping
    evaluation.tariff_usd = tariff
    evaluation.platform_fee_usd = platform_fee
    evaluation.dest_price_usd = dest_price
    evaluation.margin_usd = dest_price - landed
    evaluation.margin_pct = (dest_price - landed) / dest_price
    evaluation.margin_at_order_usd = evaluation.margin_usd * quote.order_units

    # Baseline: the trade-finder model's baseline source cost for this
    # product on this route. This is the right comparison: the supplier's
    # list FOB in `verify_suppliers.py` is quoted for their watch/band line,
    # so comparing a phone-case quote against it would be meaningless.
    baseline_fob = product["src"].get(source_cc)
    if baseline_fob:
        evaluation.baseline_fob_usd = baseline_fob
        evaluation.fob_delta_usd = quote.fob_usd - baseline_fob
        evaluation.fob_delta_pct = (
            (quote.fob_usd - baseline_fob) / baseline_fob if baseline_fob else 0.0
        )

    raw_supplier = _supplier_record(quote.alibaba_id)
    if raw_supplier:
        scored = vs._score_one(raw_supplier, noise_pct=0.0, rng_seed=0)
        evaluation.supplier_score = scored.composite_score
        evaluation.composite_score = scored.composite_score
        evaluation.risk_level = scored.risk_level
        evaluation.risk_flags = list(scored.flags)
    else:
        evaluation.notes.append(
            f"Supplier {quote.alibaba_id!r} is not in the verified supplier pool, "
            f"so it carries no verification score."
        )

    # --- disqualification ------------------------------------------------- #
    if evaluation.margin_pct < min_margin_pct:
        evaluation.disqualified = True
        evaluation.disqualification_reasons.append(
            f"Margin {evaluation.margin_pct * 100:.1f}% is below the "
            f"{min_margin_pct * 100:.1f}% floor at the quoted FOB of ${quote.fob_usd:.2f}."
        )

    if evaluation.risk_level in ("HIGH", "UNKNOWN"):
        evaluation.disqualified = True
        evaluation.disqualification_reasons.append(
            f"Risk level is {evaluation.risk_level}"
            + (f" ({', '.join(evaluation.risk_flags)})" if evaluation.risk_flags else "")
            + ". A cheap quote from a risky supplier is not a cheap quote."
        )

    if quote.order_units < quote.moq:
        evaluation.disqualified = True
        evaluation.disqualification_reasons.append(
            f"Order of {quote.order_units} units is below this supplier's MOQ of {quote.moq}."
        )

    # --- conflicts --------------------------------------------------------- #
    if evaluation.risk_flags and evaluation.risk_level == "MEDIUM":
        evaluation.conflicts.append(
            f"{quote.supplier_name} quotes ${quote.fob_usd:.2f} but carries "
            f"{evaluation.risk_level} risk: {', '.join(evaluation.risk_flags)}."
        )
    if evaluation.fob_delta_pct < -0.05:
        evaluation.notes.append(
            f"Quoted FOB is {abs(evaluation.fob_delta_pct) * 100:.1f}% below the "
            f"${evaluation.baseline_fob_usd:.2f} baseline source cost for this "
            f"product — confirm the specification is unchanged before trusting this price."
        )
    if evaluation.fob_delta_pct > 0.05:
        evaluation.notes.append(
            f"Quoted FOB is {evaluation.fob_delta_pct * 100:.1f}% above the "
            f"${evaluation.baseline_fob_usd:.2f} baseline source cost for this product."
        )
    if "100% before shipment" in quote.payment_terms.lower():
        evaluation.notes.append(
            "Payment terms are 100% upfront. Prefer deposit + balance against "
            "the bill of lading for a first order."
        )

    return evaluation


# --------------------------------------------------------------------------- #
# Scoring and selection
# --------------------------------------------------------------------------- #


def _lead_time_score(lead_time_days: int) -> float:
    if lead_time_days <= IDEAL_LEAD_TIME_DAYS:
        return 1.0
    if lead_time_days >= MAX_LEAD_TIME_DAYS:
        return 0.0
    return (MAX_LEAD_TIME_DAYS - lead_time_days) / (
        MAX_LEAD_TIME_DAYS - IDEAL_LEAD_TIME_DAYS
    )


def score_evaluation(evaluation: QuoteEvaluation, *, margin_ceiling: float) -> float:
    """Weighted score for a quote, used to rank the survivors."""
    margin_component = max(0.0, min(evaluation.margin_pct / margin_ceiling, 1.0))
    supplier_component = min(evaluation.composite_score / 10.0, 1.0)
    lead_component = _lead_time_score(evaluation.quote.lead_time_days)
    return round(
        SCORE_WEIGHTS["margin"] * margin_component
        + SCORE_WEIGHTS["supplier_score"] * supplier_component
        + SCORE_WEIGHTS["lead_time"] * lead_component,
        4,
    )


def recommend(
    quotes: Sequence[Quote],
    *,
    min_margin_pct: float = 0.15,
    deadline_days: int | None = None,
) -> Recommendation:
    """Compare quotes and recommend one supplier.

    ``deadline_days`` is the number of days from today until the goods must
    arrive. A quote whose lead time cannot fit is disqualified.
    """
    started = time.perf_counter()
    stages: list[dict[str, Any]] = []

    step_started = time.perf_counter()
    evaluations = [
        price_quote(quote, min_margin_pct=min_margin_pct) for quote in quotes
    ]
    stages.append(
        {
            "name": "price",
            "status": "success",
            "latency_ms": round((time.perf_counter() - step_started) * 1000, 3),
            "details": {"quotes_priced": len(evaluations)},
        }
    )

    # Lead-time feasibility against the deadline.
    if deadline_days is not None:
        step_started = time.perf_counter()
        for evaluation in evaluations:
            if evaluation.quote.lead_time_days > deadline_days:
                evaluation.disqualified = True
                evaluation.disqualification_reasons.append(
                    f"Lead time of {evaluation.quote.lead_time_days} days cannot meet a "
                    f"{deadline_days}-day deadline."
                )
        stages.append(
            {
                "name": "deadline",
                "status": "success",
                "latency_ms": round((time.perf_counter() - step_started) * 1000, 3),
                "details": {"deadline_days": deadline_days},
            }
        )

    survivors = [e for e in evaluations if not e.disqualified]

    step_started = time.perf_counter()
    margin_ceiling = max((e.margin_pct for e in survivors), default=1.0) or 1.0
    for evaluation in survivors:
        evaluation.score = score_evaluation(evaluation, margin_ceiling=margin_ceiling)
    survivors.sort(key=lambda e: (-e.score, e.margin_pct, e.quote.lead_time_days))
    stages.append(
        {
            "name": "score",
            "status": "success",
            "latency_ms": round((time.perf_counter() - step_started) * 1000, 3),
            "details": {"survivors": len(survivors), "margin_ceiling": round(margin_ceiling, 4)},
        }
    )

    recommended = survivors[0] if survivors else None
    conflicts = [c for e in evaluations for c in e.conflicts]
    rationale = _build_rationale(recommended, survivors, evaluations, min_margin_pct)
    confidence = _confidence(survivors, evaluations)

    recommendation = Recommendation(
        product=quotes[0].product if quotes else "",
        dest_country=quotes[0].dest_country if quotes else "",
        order_units=quotes[0].order_units if quotes else 0,
        recommended=recommended,
        evaluations=evaluations,
        rationale=rationale,
        conflicts=conflicts,
        confidence=confidence,
        stages=stages,
    )
    recommendation.total_latency_ms = (time.perf_counter() - started) * 1000
    return recommendation


def _build_rationale(
    recommended: QuoteEvaluation | None,
    survivors: list[QuoteEvaluation],
    evaluations: list[QuoteEvaluation],
    min_margin_pct: float,
) -> list[str]:
    """The structured 'why', in plain sentences."""
    if recommended is None:
        rejected = "; ".join(
            f"{e.quote.supplier_name}: {e.disqualification_reasons[0]}"
            for e in evaluations
            if e.disqualification_reasons
        )
        return [
            "No quote cleared the bar. Every quote was disqualified.",
            rejected,
            "The next step is to widen the supplier pool or renegotiate the "
            "terms that caused the disqualification.",
        ]

    lines = [
        f"Recommend {recommended.quote.supplier_name} "
        f"({recommended.quote.alibaba_id}) at ${recommended.quote.fob_usd:.2f} FOB "
        f"for {recommended.quote.order_units} units.",
        f"Modelled margin is {recommended.margin_pct * 100:.1f}% "
        f"(${recommended.margin_usd:.2f}/unit, "
        f"${recommended.margin_at_order_usd:,.0f} on this order), "
        f"clearing the {min_margin_pct * 100:.1f}% floor.",
        f"Landed cost is ${recommended.landed_cost_usd:.2f} "
        f"(${recommended.quote.fob_usd:.2f} FOB + ${recommended.shipping_usd:.2f} shipping "
        f"+ ${recommended.tariff_usd:.2f} tariff + ${recommended.platform_fee_usd:.2f} platform fee) "
        f"against a ${recommended.dest_price_usd:.2f} destination price.",
        f"Supplier composite score is {recommended.composite_score}/10 with risk level "
        f"{recommended.risk_level}, on a {recommended.quote.lead_time_days}-day lead time.",
    ]

    if len(survivors) > 1:
        runner_up = survivors[1]
        margin_gap = recommended.margin_usd - runner_up.margin_usd
        lines.append(
            f"Ran against {runner_up.quote.supplier_name} "
            f"(score {runner_up.score} vs {recommended.score}); the margin gap is "
            f"${margin_gap:.2f}/unit, or ${margin_gap * recommended.quote.order_units:,.0f} "
            f"on this order."
        )
    else:
        rejected = [
            f"{e.quote.supplier_name} ({e.disqualification_reasons[0]})"
            for e in evaluations
            if e.disqualified
        ]
        if rejected:
            lines.append("All other quotes were disqualified: " + "; ".join(rejected) + ".")

    for note in recommended.notes:
        lines.append(f"Note: {note}")

    return lines


def _confidence(
    survivors: list[QuoteEvaluation], evaluations: list[QuoteEvaluation]
) -> float:
    """How much to trust the recommendation, in 0..1.

    High when one quote is clearly ahead of the field and nothing was
    disqualified for risk. Low when the decision hinged on a close call or a
    risk flag.
    """
    if not survivors:
        return 0.0
    if len(survivors) == 1:
        base = 0.75
    else:
        gap = survivors[0].score - survivors[1].score
        base = min(0.95, 0.60 + gap * 3.0)
    if any(e.disqualified for e in evaluations):
        base -= 0.05
    if survivors[0].conflicts:
        base -= 0.15
    return round(max(0.0, min(1.0, base)), 4)
