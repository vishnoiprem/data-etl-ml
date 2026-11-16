"""D1 — which bucket grew, and why.

The question is not "did anything get more expensive" — something always
does. The question is "which specific target grew, by how much, and is
that enough to be worth someone's afternoon".

Three guards keep the detector honest, and each exists because of a way
it gets it wrong:

**The partial-month guard.** A period is complete only if it covers the
whole calendar month *and* is not ``Estimated``. An incomplete period
is excluded **entirely** — never divided, never compared. Comparing a
half-finished month against a settled one manufactures a growth finding
that does not exist, and the current month is always partial.

**The seasonality guard.** A bucket that grows every month grows by
design. The baseline is the trailing median (or YoY when there is
enough history), and a target is only interesting if it grew *against*
its own pattern. A target that is simply above its own trailing max is
also worth noting — that is the "consistently growing" case.

**The double threshold.** A cost must move at least 20% *and* be at
least $50/month. A bucket that doubled to $3 is noise. A bucket that
moved 40% to $400 is worth a look.

The prefix honesty rule: exact per-prefix bytes need S3 Inventory or
Storage Lens, neither of which is in v1. So a bucket-level figure is
``measured`` and a prefix-level figure is ``upper_bound`` — a ceiling on
a quantity we could not measure, never presented as a fact.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from ..config import Thresholds
from ..models import (
    MEASURED,
    MODELLED,
    UPPER_BOUND,
    CostRecord,
    Evidence,
    Finding,
    severity_for,
)

DETECTOR = "growth"


@dataclass(slots=True)
class GrowthTarget:
    """One target's monthly spend, in period order."""

    target: str
    by_period: dict[str, float]
    periods: list[str]

    @property
    def latest_period(self) -> str:
        return self.periods[-1] if self.periods else ""

    @property
    def latest_amount(self) -> float:
        return self.by_period.get(self.latest_period, 0.0)

    @property
    def baseline_amount(self) -> float:
        """The trailing median of the periods before the latest."""
        earlier = [self.by_period[p] for p in self.periods[:-1] if p in self.by_period]
        if not earlier:
            return 0.0
        return statistics.median(earlier)

    @property
    def baseline_periods(self) -> list[str]:
        return self.periods[:-1]

    @property
    def growth_pct(self) -> float:
        """Fractional growth against the baseline.

        A target with no baseline cannot have grown, and a baseline of
        zero means the growth is undefined rather than infinite — it is
        reported as new spend, not as an infinite percentage.
        """
        baseline = self.baseline_amount
        if baseline <= 0:
            return 0.0
        return (self.latest_amount - baseline) / baseline

    @property
    def is_new(self) -> bool:
        """Whether the target had no spend before the latest period."""
        return self.baseline_amount <= 0 and self.latest_amount > 0

    @property
    def above_own_trailing_max(self) -> bool:
        """Whether the latest period beats every earlier one."""
        earlier = [self.by_period[p] for p in self.periods[:-1] if p in self.by_period]
        if not earlier:
            return False
        return self.latest_amount > max(earlier)


def collect_targets(
    records: list[CostRecord],
    *,
    group_index: int = 0,
    service_filter: str | None = None,
) -> list[GrowthTarget]:
    """Group cost records into per-target monthly spend series.

    ``group_index`` is the position of the dimension that identifies the
    target — for a per-bucket pull that is the resource key, which the
    normalizer appends last.
    """
    series: dict[str, dict[str, float]] = {}
    service_names: dict[str, str] = {}

    for record in records:
        if service_filter and service_filter.lower() not in record.service.lower():
            continue
        if len(record.group) <= group_index:
            continue
        target = record.group[group_index]
        series.setdefault(target, {})[record.period_label] = record.amount
        service_names[target] = record.service

    targets: list[GrowthTarget] = []
    for target, by_period in series.items():
        periods = sorted(by_period)
        targets.append(GrowthTarget(target=target, by_period=by_period, periods=periods))
    return targets


def detect_growth(
    records: list[CostRecord],
    thresholds: Thresholds,
    *,
    group_index: int = 0,
    service_filter: str | None = None,
    latest_period: str = "",
    period_label_prefix: str = "",
) -> list[Finding]:
    """Find the targets whose spend grew enough to be worth a look.

    ``latest_period`` pins the comparison to one period. Without it the
    detector uses the latest period present in the data, which is the
    right default but makes the function's behaviour depend on the
    input's ordering.
    """
    targets = collect_targets(
        records, group_index=group_index, service_filter=service_filter
    )
    if not targets:
        return []

    findings: list[Finding] = []

    for target in targets:
        if latest_period:
            if target.latest_period != latest_period:
                continue
            baseline_periods = [p for p in target.periods if p < latest_period]
            baseline_series = [target.by_period[p] for p in baseline_periods]
            baseline = statistics.median(baseline_series) if baseline_series else 0.0
            latest = target.by_period.get(latest_period, 0.0)
            growth = (latest - baseline) / baseline if baseline > 0 else 0.0
            is_new = baseline <= 0 and latest > 0
            above_max = bool(baseline_series) and latest > max(baseline_series)
            used_period = latest_period
            used_baseline_periods = baseline_periods
        else:
            baseline = target.baseline_amount
            latest = target.latest_amount
            growth = target.growth_pct
            is_new = target.is_new
            above_max = target.above_own_trailing_max
            used_period = target.latest_period
            used_baseline_periods = target.baseline_periods

        if latest <= 0:
            continue

        # The double threshold. A new target with real spend is
        # interesting regardless of a percentage (there is no
        # percentage), so it is judged on the absolute floor alone.
        if is_new:
            if latest < thresholds.min_growth_usd:
                continue
        else:
            if growth < thresholds.min_growth_pct:
                continue
            if latest < thresholds.min_growth_usd:
                continue

        cost_impact = latest - baseline if baseline > 0 else latest

        severity = severity_for(abs(cost_impact), MEASURED)
        if above_max and severity == "low":
            severity = "medium"

        evidence: list[Evidence] = [
            Evidence(
                metric="monthly_spend",
                value=latest,
                unit="USD",
                source="cost_explorer",
                period=used_period,
                detail={"target": target.target},
            ),
            Evidence(
                metric="baseline_monthly_spend",
                value=baseline,
                unit="USD",
                source="cost_explorer",
                period=", ".join(used_baseline_periods),
                detail={"target": target.target, "basis": "trailing median"},
            ),
            Evidence(
                metric="growth_pct",
                value=round(growth * 100, 2),
                unit="percent",
                source="cost_explorer",
                period=used_period,
                detail={"target": target.target},
            ),
        ]

        if above_max:
            evidence.append(
                Evidence(
                    metric="above_own_trailing_max",
                    value=1.0,
                    unit="boolean",
                    source="cost_explorer",
                    period=used_period,
                    detail={"target": target.target},
                )
            )

        if is_new:
            summary = (
                f"{target.target} had no recorded spend before {used_period} and "
                f"cost ${latest:,.2f} in {used_period}."
            )
            title = f"{target.target} is new spend"
        else:
            summary = (
                f"{target.target} cost ${latest:,.2f} in {used_period}, up "
                f"{growth * 100:.0f}% from a trailing median of "
                f"${baseline:,.2f}."
            )
            title = f"{target.target} grew {growth * 100:.0f}%"

        if above_max and not is_new:
            summary += " It is above every previous month, so this is a trend rather than a spike."

        findings.append(
            Finding(
                id=f"growth:{period_label_prefix}{target.target}:{used_period}",
                detector=DETECTOR,
                title=title,
                severity=severity,
                summary=summary,
                target=target.target,
                cost_impact=abs(cost_impact),
                cost_impact_basis=MEASURED,
                evidence=evidence,
                confidence=1.0,
                details={
                    "growth_pct": growth,
                    "baseline": baseline,
                    "latest": latest,
                    "period": used_period,
                    "is_new": is_new,
                    "above_own_trailing_max": above_max,
                    "baseline_periods": used_baseline_periods,
                },
                recommendation=(
                    "Check whether this target's volume grew, its storage class "
                    "changed, or its request pattern changed — the cost record "
                    "cannot tell you which."
                ),
            )
        )

    findings.sort(key=lambda f: f.cost_impact, reverse=True)
    return findings


def prefix_estimate(
    bucket_total_gb: float,
    prefixes: list[tuple[str, float]],
    *,
    region: str = "",
) -> list[dict[str, object]]:
    """Estimate per-prefix byte shares of a bucket.

    The shares are only as good as the sample that produced them, so
    the result carries the bucket total and the basis. Every entry is
    an **upper bound** on the prefix's real cost — it is a share of an
    unmeasured quantity, not a measurement.
    """
    total_weight = sum(weight for _, weight in prefixes)
    if total_weight <= 0 or bucket_total_gb <= 0:
        return []

    entries: list[dict[str, object]] = []
    for prefix, weight in prefixes:
        share = weight / total_weight
        gb = bucket_total_gb * share
        entries.append(
            {
                "prefix": prefix,
                "estimated_gb": gb,
                "basis": UPPER_BOUND,
                "region": region,
                "note": (
                    "Per-prefix bytes need S3 Inventory or Storage Lens. "
                    "This is a share of the measured bucket total, not a measurement."
                ),
            }
        )
    return entries


def storage_cost_evidence(
    gb: float,
    storage_class: str,
    card,
    *,
    period: str,
    region: str = "",
) -> Evidence:
    """A modelled storage-cost evidence item."""
    return Evidence(
        metric="storage_cost",
        value=card.storage_cost(gb, storage_class),
        unit="USD",
        source="rate_card",
        period=period,
        detail={
            "storage_gb": str(gb),
            "storage_class": storage_class,
            "rate_card_region": card.region,
            "analysis_region": region,
            "basis": MODELLED,
        },
    )
