"""D4 — which tag or squad is spending.

This detector reproduces the console view offline: six months of
unblended cost, grouped by service, filtered to the cost-allocation
tags named in the URL.

Two guards:

**The double threshold.** A squad must have grown at least 20% *and*
be spending at least $50/month. A squad that doubled from $12 to $36
is not a story.

**The untagged-gap guard.** The tagged total is compared against the
*unfiltered* service total. If the tagged spend covers less than 90% of
the service's spend, then a meaningful slice of the bill is untagged,
and the per-tag figures do not add up to the whole. The gap is stated
and the confidence is capped at 0.6 — the tool does not present a
partial attribution as a complete one.
"""

from __future__ import annotations

import statistics

from ..config import Thresholds
from ..models import (
    MEASURED,
    Evidence,
    Finding,
    severity_for,
)

DETECTOR = "allocation"

#: The value Cost Explorer uses for spend with no matching tag.
UNTAGGED = "Untagged"


def detect_allocation(
    tagged_records,
    untagged_service_total: float,
    thresholds: Thresholds,
    *,
    region: str = "",
    service: str = "Amazon Simple Storage Service",
) -> list[Finding]:
    """Find the tags whose spend grew, and report the untagged gap.

    ``tagged_records`` are cost records grouped by tag value —
    ``record.group[1]`` is the tag value when the group is
    ``[SERVICE, TAG]``.
    """
    series: dict[str, dict[str, float]] = {}
    for record in tagged_records:
        if len(record.group) < 2:
            continue
        tag_value = record.group[1]
        series.setdefault(tag_value, {})[record.period_label] = record.amount

    if not series:
        return []

    all_periods = sorted({p for by_period in series.values() for p in by_period})
    if not all_periods:
        return []

    latest_period = all_periods[-1]

    # The untagged gap.
    tagged_total = sum(
        amount for by_period in series.values() for amount in by_period.values()
    )
    coverage = tagged_total / untagged_service_total if untagged_service_total > 0 else 1.0
    coverage_complete = coverage >= thresholds.min_tag_coverage
    confidence_cap = 1.0 if coverage_complete else thresholds.untagged_confidence_cap

    findings: list[Finding] = []

    for tag_value, by_period in series.items():
        if latest_period not in by_period:
            continue

        latest = by_period[latest_period]
        if latest <= 0:
            continue

        earlier_periods = [p for p in all_periods if p < latest_period]
        baseline_series = [by_period[p] for p in earlier_periods if p in by_period]
        baseline = statistics.median(baseline_series) if baseline_series else 0.0

        if baseline <= 0:
            if latest < thresholds.min_allocation_usd:
                continue
            growth = 0.0
            is_new = True
        else:
            growth = (latest - baseline) / baseline
            is_new = False
            if growth < thresholds.min_allocation_growth_pct:
                continue
            if latest < thresholds.min_allocation_usd:
                continue

        cost_impact = latest - baseline if baseline > 0 else latest

        evidence: list[Evidence] = [
            Evidence(
                metric="monthly_spend",
                value=latest,
                unit="USD",
                source="cost_explorer",
                period=latest_period,
                detail={"tag": tag_value},
            ),
            Evidence(
                metric="baseline_monthly_spend",
                value=baseline,
                unit="USD",
                source="cost_explorer",
                period=", ".join(earlier_periods),
                detail={"tag": tag_value, "basis": "trailing median"},
            ),
            Evidence(
                metric="growth_pct",
                value=round(growth * 100, 2),
                unit="percent",
                source="cost_explorer",
                period=latest_period,
                detail={"tag": tag_value},
            ),
            Evidence(
                metric="tag_coverage",
                value=round(coverage, 3),
                unit="ratio",
                source="cost_explorer",
                period=latest_period,
                detail={
                    "tagged_total": str(tagged_total),
                    "service_total": str(untagged_service_total),
                    "service": service,
                },
            ),
        ]

        if is_new:
            summary = (
                f"Tag '{tag_value}' had no recorded spend before {latest_period} and "
                f"cost ${latest:,.2f} in {latest_period}."
            )
            title = f"{tag_value} is new spend"
        else:
            summary = (
                f"Tag '{tag_value}' cost ${latest:,.2f} in {latest_period}, up "
                f"{growth * 100:.0f}% from a trailing median of ${baseline:,.2f}."
            )
            title = f"{tag_value} grew {growth * 100:.0f}%"

        if not coverage_complete:
            summary += (
                f" Note that tagged spend covers only {coverage * 100:.0f}% of "
                f"{service} spend, so some of this bill is untagged."
            )

        findings.append(
            Finding(
                id=f"allocation:{tag_value}:{latest_period}",
                detector=DETECTOR,
                title=title,
                severity=severity_for(abs(cost_impact), MEASURED),
                summary=summary,
                target=tag_value,
                cost_impact=abs(cost_impact),
                cost_impact_basis=MEASURED,
                confidence=confidence_cap,
                evidence=evidence,
                details={
                    "growth_pct": growth,
                    "baseline": baseline,
                    "latest": latest,
                    "period": latest_period,
                    "is_new": is_new,
                    "tag_coverage": coverage,
                    "coverage_complete": coverage_complete,
                    "service": service,
                },
                recommendation=(
                    "Ask which workload the tag belongs to. The cost record "
                    "knows the amount and the tag, but not what produced them."
                ),
            )
        )

    findings.sort(key=lambda f: f.cost_impact, reverse=True)

    # The untagged gap is part of the allocation answer, not a separate
    # concern: a quarter where the bill rose and no squad "grew" would
    # otherwise look like nothing happened.
    gap = untagged_gap_finding(
        tagged_total,
        untagged_service_total,
        thresholds,
        service=service,
        region=region,
    )
    if gap is not None:
        findings.append(gap)

    return findings


def untagged_gap_finding(
    tagged_total: float,
    service_total: float,
    thresholds: Thresholds,
    *,
    service: str = "Amazon Simple Storage Service",
    region: str = "",
) -> Finding | None:
    """The finding for spend that carries no tag at all.

    This exists so the gap is reported even when no individual tag
    grew — otherwise a quarter where the bill rose and no squad
    "grew" would look like nothing happened.
    """
    if service_total <= 0:
        return None

    untagged = service_total - tagged_total
    if untagged <= 0:
        return None

    coverage = tagged_total / service_total
    if coverage >= thresholds.min_tag_coverage:
        return None

    return Finding(
        id=f"allocation:untagged-gap:{service}",
        detector=DETECTOR,
        title=f"{untagged:,.0f} USD of {service} spend carries no tag",
        severity="medium",
        summary=(
            f"Tagged spend accounts for {coverage * 100:.0f}% of {service} spend. "
            f"The remaining ${untagged:,.2f} cannot be attributed to any team, "
            f"so the per-team figures do not add up to the bill."
        ),
        target=UNTAGGED,
        cost_impact=untagged,
        cost_impact_basis=MEASURED,
        confidence=thresholds.untagged_confidence_cap,
        evidence=[
            Evidence(
                metric="untagged_spend",
                value=untagged,
                unit="USD",
                source="cost_explorer",
                period="",
                detail={"service": service},
            ),
            Evidence(
                metric="tag_coverage",
                value=round(coverage, 3),
                unit="ratio",
                source="cost_explorer",
                period="",
                detail={
                    "tagged_total": str(tagged_total),
                    "service_total": str(service_total),
                },
            ),
        ],
        details={
            "problem": "untagged_gap",
            "tag_coverage": coverage,
            "service": service,
        },
        recommendation=(
            "Tag the untagged resources, or find out which team owns them. "
            "Without that, no per-team number here is the whole story."
        ),
    )
