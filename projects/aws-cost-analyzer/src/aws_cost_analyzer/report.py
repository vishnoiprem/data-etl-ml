"""The report — human-readable and JSON.

The report has one job beyond listing findings, and that job is
**showing the basis of every number**. A reader must never have to
guess whether a figure came off the bill, out of a rate card, or is a
ceiling on something unmeasured.

So every dollar figure is printed with its basis next to it, and the
wording is deliberately *"avoidable cost at the observed volume"* —
never *"savings"*. There is no measured saving: you cannot measure
money you did not spend.

The report also prints the things the analysis could **not** do: the
periods it excluded, the tag coverage gap, the access-log coverage
gap, and the rate card's region when it does not match the analysis
region. A report that only lists what it found is half a report.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .models import Finding

#: How each basis is described in the report.
BASIS_LABELS = {
    "measured": "measured",
    "modelled": "modelled (volume x rate card)",
    "upper_bound": "upper bound (not directly measured)",
}

#: How each savings basis is described.
SAVINGS_LABELS = {
    "modelled_from_rate_card": "modelled from the rate card",
    "not_quantified": "not quantified",
}


@dataclass(slots=True)
class ReportContext:
    """Everything the report needs to know about the run."""

    region: str = ""
    start: str = ""
    end: str = ""
    rate_card_region: str = ""
    rate_card_checked_on: str = ""
    total_spend: float = 0.0
    records_analyzed: int = 0
    excluded_periods: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    router_name: str = "stub"


def format_money(amount: float) -> str:
    """A dollar figure with a thousands separator."""
    return f"${amount:,.2f}"


def format_basis(finding: Finding) -> str:
    """The basis of a finding's cost impact."""
    return BASIS_LABELS.get(finding.cost_impact_basis, finding.cost_impact_basis)


def render_text(findings: list[Finding], context: ReportContext) -> str:
    """The human-readable report."""
    lines: list[str] = []
    lines.append("AWS Cost Analyzer — S3 root-cause report")
    lines.append("=" * 60)
    lines.append("")

    lines.append(f"Region:   {context.region}")
    lines.append(f"Window:   {context.start} .. {context.end}")
    if context.records_analyzed:
        lines.append(f"Records:  {context.records_analyzed}")
    if context.total_spend:
        lines.append(f"Spend:    {format_money(context.total_spend)} (measured)")
    lines.append("")

    # --- what this report could not do ---------------------------------- #
    caveats: list[str] = []
    if context.excluded_periods:
        caveats.append(
            f"Periods excluded from comparison: {', '.join(context.excluded_periods)}"
            + (" (partial or estimated)" if context.excluded_periods else "")
        )
    if context.rate_card_region and context.region:
        if context.rate_card_region.lower() != context.region.lower():
            caveats.append(
                f"Rate card is {context.rate_card_region} "
                f"(checked {context.rate_card_checked_on}) but the analysis region is "
                f"{context.region}. Modelled figures are indicative, not authoritative."
            )
    for note in context.notes:
        caveats.append(note)

    if caveats:
        lines.append("What this analysis could not do")
        lines.append("-" * 60)
        for caveat in caveats:
            lines.append(f"  ! {caveat}")
        lines.append("")

    # --- the findings ---------------------------------------------------- #
    lines.append(f"Findings ({len(findings)})")
    lines.append("-" * 60)
    lines.append("")

    if not findings:
        lines.append("  Nothing crossed the thresholds.")
        lines.append("")
    else:
        for finding in findings:
            lines.append(f"  [{finding.severity.upper()}] {finding.title}")
            lines.append(f"    target:   {finding.target}")
            if finding.cost_impact:
                lines.append(
                    f"    impact:   {format_money(finding.cost_impact)} ({format_basis(finding)})"
                )
            elif finding.cost_impact_basis == "upper_bound":
                # A ceiling on something unmeasured, with no measured
                # floor under it. "$0.00 (upper bound)" reads like the
                # cost is zero, which is the opposite of the truth.
                lines.append("    impact:   not quantified (the quantity could not be measured)")
            else:
                lines.append(f"    impact:   {format_money(finding.cost_impact)} ({format_basis(finding)})")
            if finding.savings_estimate:
                label = SAVINGS_LABELS.get(finding.savings_basis, finding.savings_basis)
                lines.append(
                    f"    avoidable: {format_money(finding.savings_estimate)} at the observed volume ({label})"
                )
            lines.append(f"    confidence: {finding.confidence:.2f}")
            lines.append("")
            lines.append(f"    {finding.summary}")
            lines.append("")

            if finding.narrative:
                lines.append(f"    {finding.narrative}")
                lines.append("")

            if finding.evidence:
                lines.append("    Evidence:")
                for evidence in finding.evidence:
                    detail = ""
                    if evidence.detail:
                        detail = " (" + ", ".join(f"{k}={v}" for k, v in evidence.detail.items()) + ")"
                    lines.append(
                        f"      - {evidence.metric}: {evidence.value} {evidence.unit} "
                        f"[{evidence.source}]{detail}"
                    )
                lines.append("")

            if finding.recommendation:
                lines.append(f"    Do this: {finding.recommendation}")
                lines.append("")

    lines.append(f"Model: {context.router_name} (writes prose only — it cannot change a finding)")
    return "\n".join(lines)


def to_json(findings: list[Finding], context: ReportContext) -> dict[str, Any]:
    """The machine-readable report."""
    return {
        "region": context.region,
        "start": context.start,
        "end": context.end,
        "records_analyzed": context.records_analyzed,
        "total_spend": context.total_spend,
        "total_spend_basis": "measured" if context.total_spend else "",
        "excluded_periods": list(context.excluded_periods),
        "rate_card_region": context.rate_card_region,
        "rate_card_checked_on": context.rate_card_checked_on,
        "router": context.router_name,
        "notes": list(context.notes),
        "finding_count": len(findings),
        "findings": [f.to_dict() for f in findings],
        "totals_by_detector": totals_by_detector(findings),
        "totals_by_basis": totals_by_basis(findings),
    }


def totals_by_detector(findings: list[Finding]) -> dict[str, float]:
    """The impact total per detector."""
    totals: dict[str, float] = {}
    for finding in findings:
        totals[finding.detector] = totals.get(finding.detector, 0.0) + finding.cost_impact
    return totals


def totals_by_basis(findings: list[Finding]) -> dict[str, float]:
    """The impact total per basis.

    Keeping these apart is the point: a reader who sees $10,000 of
    "impact" needs to know how much of it is a measurement and how much
    is a ceiling.
    """
    totals: dict[str, float] = {}
    for finding in findings:
        totals[finding.cost_impact_basis] = (
            totals.get(finding.cost_impact_basis, 0.0) + finding.cost_impact
        )
    return totals


def write_json_report(
    findings: list[Finding],
    context: ReportContext,
    path,
) -> None:
    """Write the JSON report to a file."""
    from pathlib import Path

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(to_json(findings, context), indent=2, sort_keys=True))


def write_text_report(findings: list[Finding], context: ReportContext, path) -> None:
    """Write the text report to a file."""
    from pathlib import Path

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(render_text(findings, context))
