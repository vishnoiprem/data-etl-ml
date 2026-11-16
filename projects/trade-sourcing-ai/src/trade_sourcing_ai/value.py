"""Turn agent activity into a business number.

This is the module that separates a sourcing agent from a sourcing demo. It
answers three questions, and is explicit about which answers are measured
and which are assumed:

**What did the decision cost?** Local compute seconds plus any model spend.
In the default offline mode the model spend is genuinely $0.

**What did it save?** The manual baseline is a human reading a shortlist,
waiting on supplier replies, and hand-comparing quotes.

**Was it worth it?** The margin the agent's pick captures versus two
baselines: the cheapest quote (the naive "just pick the lowest price"
strategy) and the supplier the existing shortlist already ranks first (the
status quo).

Every assumption is carried in the report so a reader can disagree with a
specific number rather than with the whole thing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import ValueConfig
from .quote_agent import Recommendation


@dataclass
class DecisionCost:
    """What one decision cost to make."""

    compute_seconds: float
    compute_cost_usd: float
    model_cost_usd: float
    total_cost_usd: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "compute_seconds": round(self.compute_seconds, 4),
            "compute_cost_usd": round(self.compute_cost_usd, 4),
            "model_cost_usd": round(self.model_cost_usd, 4),
            "total_cost_usd": round(self.total_cost_usd, 4),
        }


@dataclass
class ValueReport:
    """The business case for one sourcing decision."""

    product: str
    dest_country: str
    order_units: int
    cost: DecisionCost
    agent_seconds: float
    manual_minutes: float
    manual_cost_usd: float
    time_saved_minutes: float
    time_saved_cost_usd: float
    recommended_supplier: str | None
    recommended_margin_usd: float
    naive_margin_usd: float
    status_quo_margin_usd: float
    margin_captured_vs_naive_usd: float
    margin_captured_vs_status_quo_usd: float
    payback_decisions: float | None
    scenarios: list[dict[str, Any]] = field(default_factory=list)
    assumptions: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "product": self.product,
            "dest_country": self.dest_country,
            "order_units": self.order_units,
            "cost": self.cost.to_dict(),
            "agent_seconds": round(self.agent_seconds, 4),
            "manual_minutes": round(self.manual_minutes, 2),
            "manual_cost_usd": round(self.manual_cost_usd, 2),
            "time_saved_minutes": round(self.time_saved_minutes, 2),
            "time_saved_cost_usd": round(self.time_saved_cost_usd, 2),
            "recommended_supplier": self.recommended_supplier,
            "recommended_margin_usd": round(self.recommended_margin_usd, 2),
            "naive_margin_usd": round(self.naive_margin_usd, 2),
            "status_quo_margin_usd": round(self.status_quo_margin_usd, 2),
            "margin_captured_vs_naive_usd": round(self.margin_captured_vs_naive_usd, 2),
            "margin_captured_vs_status_quo_usd": round(
                self.margin_captured_vs_status_quo_usd, 2
            ),
            "payback_decisions": (
                round(self.payback_decisions, 2)
                if self.payback_decisions is not None
                else None
            ),
            "scenarios": self.scenarios,
            "assumptions": self.assumptions,
        }


def compute_cost(
    *,
    compute_seconds: float,
    tokens_used: int,
    config: ValueConfig,
) -> DecisionCost:
    """Cost of one decision: compute time plus any model spend."""
    compute_cost_usd = (compute_seconds / 3600.0) * config.operator_hourly_usd
    model_cost_usd = (
        tokens_used / 1000.0 * config.hosted_cost_per_1k_tokens_usd
    )
    return DecisionCost(
        compute_seconds=compute_seconds,
        compute_cost_usd=compute_cost_usd,
        model_cost_usd=model_cost_usd,
        total_cost_usd=compute_cost_usd + model_cost_usd,
    )


def build_value_report(
    recommendation: Recommendation,
    *,
    config: ValueConfig,
    tokens_used: int = 0,
    agent_seconds: float | None = None,
    status_quo_alibaba_id: str | None = None,
) -> ValueReport:
    """Build the value report for one decision.

    ``status_quo_alibaba_id`` is the supplier the current shortlist ranks
    first. Leaving it ``None`` means "no status-quo comparison available",
    which is different from "the status quo captured zero margin".
    """
    seconds = (
        agent_seconds
        if agent_seconds is not None
        else recommendation.total_latency_ms / 1000.0
    )
    cost = compute_cost(
        compute_seconds=seconds, tokens_used=tokens_used, config=config
    )

    recommended = recommendation.recommended
    recommended_margin = recommended.margin_usd if recommended else 0.0

    # Naive baseline: the cheapest quote wins, whatever else it scores on.
    viable = [e for e in recommendation.evaluations if not e.disqualified]
    naive = min(viable, key=lambda e: e.quote.fob_usd) if viable else None
    naive_margin = naive.margin_usd if naive else 0.0

    # Status quo: whichever supplier the existing shortlist ranks first.
    status_quo_margin = 0.0
    status_quo_id = status_quo_alibaba_id
    if status_quo_id:
        match = next(
            (e for e in recommendation.evaluations if e.alibaba_id == status_quo_id), None
        )
        if match:
            status_quo_margin = match.margin_usd

    time_saved_minutes = max(
        0.0, config.manual_minutes_per_decision - (seconds * 60.0)
    )
    time_saved_cost_usd = (time_saved_minutes / 60.0) * config.operator_hourly_usd

    margin_vs_naive = recommended_margin - naive_margin
    margin_vs_status_quo = recommended_margin - status_quo_margin

    # Payback: how many decisions it takes for the agent's own cost to be
    # repaid by the margin it captures over the *stronger* baseline. Using
    # the stronger one is the conservative choice.
    captured = max(margin_vs_naive, margin_vs_status_quo)
    payback: float | None = None
    if captured > 0 and cost.total_cost_usd > 0:
        payback = cost.total_cost_usd / captured

    report = ValueReport(
        product=recommendation.product,
        dest_country=recommendation.dest_country,
        order_units=recommendation.order_units,
        cost=cost,
        agent_seconds=seconds,
        manual_minutes=config.manual_minutes_per_decision,
        manual_cost_usd=config.manual_cost_per_decision_usd,
        time_saved_minutes=time_saved_minutes,
        time_saved_cost_usd=time_saved_cost_usd,
        recommended_supplier=recommended.quote.supplier_name if recommended else None,
        recommended_margin_usd=recommended_margin,
        naive_margin_usd=naive_margin,
        status_quo_margin_usd=status_quo_margin,
        margin_captured_vs_naive_usd=margin_vs_naive,
        margin_captured_vs_status_quo_usd=margin_vs_status_quo,
        payback_decisions=payback,
        assumptions={
            "operator_hourly_usd": config.operator_hourly_usd,
            "manual_minutes_per_decision": config.manual_minutes_per_decision,
            "model_cost_per_1k_tokens_usd": config.hosted_cost_per_1k_tokens_usd,
            "compute_priced_at_operator_rate": True,
            "status_quo_alibaba_id": status_quo_id,
            "margin_is_per_order": True,
            "order_units": recommendation.order_units,
            "notes": (
                "The manual baseline is an assumption, not a measurement. "
                "Time saved is capped at the manual baseline."
            ),
        },
    )
    report.scenarios = build_scenarios(report, config)
    return report


def build_scenarios(report: ValueReport, config: ValueConfig) -> list[dict[str, Any]]:
    """Base / pessimistic / optimistic projections.

    The captured margin is measured against the *stronger* of the two
    baselines. If the agent happened to pick the cheapest quote, then the
    naive baseline captures nothing and the status quo is the only
    interesting comparison — reporting a $0 case because the agent matched
    the naive strategy would understate what the agent actually did.

    Each scenario states the assumption that produced it, because a
    projection without its assumptions is just a number.
    """
    captures = max(
        report.margin_captured_vs_naive_usd, report.margin_captured_vs_status_quo_usd
    )
    baseline_name = (
        "cheapest quote"
        if report.margin_captured_vs_naive_usd >= report.margin_captured_vs_status_quo_usd
        else "status quo shortlist"
    )

    scenarios = [
        {
            "name": "pessimistic",
            "margin_captured_usd": captures * 0.5,
            "payback_decisions": (
                report.cost.total_cost_usd / (captures * 0.5) if captures > 0 else None
            ),
            "assumption": (
                "Half the modelled margin gap is realised. The competing quote "
                "turns out to be a genuine price, not a one-off, and the "
                "margin gap narrows before the order is placed."
            ),
        },
        {
            "name": "base",
            "margin_captured_usd": captures,
            "payback_decisions": report.payback_decisions,
            "assumption": (
                f"The modelled margin holds as priced, measured against the "
                f"{baseline_name}. The competing quote was either a one-off "
                f"or was going to be discovered late anyway."
            ),
        },
        {
            "name": "optimistic",
            "margin_captured_usd": captures * 1.5,
            "payback_decisions": (
                report.cost.total_cost_usd / (captures * 1.5) if captures > 0 else None
            ),
            "assumption": (
                "The margin gap holds and the agent's time saving is spent on "
                "additional sourcing decisions rather than idle time."
            ),
        },
    ]
    for scenario in scenarios:
        if scenario["payback_decisions"] is not None:
            scenario["payback_decisions"] = round(scenario["payback_decisions"], 2)
        scenario["margin_captured_usd"] = round(scenario["margin_captured_usd"], 2)
    scenarios[0]["measured_against"] = baseline_name
    scenarios[1]["measured_against"] = baseline_name
    scenarios[2]["measured_against"] = baseline_name
    return scenarios


def summarise_reports(reports: list[ValueReport]) -> dict[str, Any]:
    """Aggregate several decisions into one summary."""
    if not reports:
        return {"decisions": 0}

    total_cost = sum(r.cost.total_cost_usd for r in reports)
    total_captured = sum(r.margin_captured_vs_naive_usd for r in reports)
    total_saved = sum(r.time_saved_cost_usd for r in reports)
    successful = [r for r in reports if r.recommended_supplier]

    return {
        "decisions": len(reports),
        "decisions_with_recommendation": len(successful),
        "total_cost_usd": round(total_cost, 2),
        "total_margin_captured_usd": round(total_captured, 2),
        "total_time_saved_usd": round(total_saved, 2),
        "net_value_usd": round(total_captured + total_saved - total_cost, 2),
        "mean_agent_seconds": round(
            sum(r.agent_seconds for r in reports) / len(reports), 4
        ),
        "margin_captured_per_decision_usd": round(total_captured / len(reports), 2),
    }
