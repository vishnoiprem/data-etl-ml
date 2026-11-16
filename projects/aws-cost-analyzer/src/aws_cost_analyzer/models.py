"""The data model: cost records, evidence, and findings.

Three dataclasses, and the third is the one that matters.

``CostRecord``
    One row of spend: a period, a service, a group key tuple, an amount.

``Evidence``
    One observation that backs a number. It says where the number came
    from — the bill, CloudWatch, the S3 API, an access log, or the rate
    card — so a reader can always tell a measurement from a calculation.

``Finding``
    One root cause, with its cost impact, the evidence behind it, and —
    critically — ``cost_impact_basis``. That field *is* the honesty
    mechanism of this project. A dollar figure that came off the bill is
    ``measured``; one derived from a volume times a rate is ``modelled``;
    one for which we have no volume at all is an ``upper_bound``. A reader
    who knows the basis can trust the figure accordingly, and a report
    that printed the two identically would be lying.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any

# --------------------------------------------------------------------------- #
# The basis vocabulary
# --------------------------------------------------------------------------- #

#: The figure is a number that appeared in a cost record.
MEASURED = "measured"

#: The figure is a volume multiplied by a rate from the illustrative card.
MODELLED = "modelled"

#: The figure is a ceiling on an unmeasured quantity.
UPPER_BOUND = "upper_bound"

#: Every valid value of ``cost_impact_basis``.
BASES = (MEASURED, MODELLED, UPPER_BOUND)

#: Savings are only ever one of these two things. There is no such thing
#: as a *measured* saving — you cannot measure money you did not spend.
SAVINGS_BASIS_MODELLED = "modelled_from_rate_card"
SAVINGS_BASIS_NOT_QUANTIFIED = "not_quantified"


@dataclass(slots=True, frozen=True)
class CostRecord:
    """One row of spend.

    ``group`` is a **tuple**, not a dict, and that is deliberate. A
    ``GroupBy=[SERVICE]`` layout and a ``GroupBy=[SERVICE, TAG]`` layout
    are different dimension spaces; flattening them into one namespace
    would make a service and a tag value look like the same kind of key.
    The tuple preserves the positional relationship with
    ``GroupDefinitions``, which is the only way to know what each element
    of the tuple actually *means*.
    """

    period_start: date
    period_end: date
    granularity: str
    service: str
    region: str
    group: tuple[str, ...]
    amount: float
    unit: str = "USD"
    metric: str = "UnblendedCost"
    estimated: bool = False
    tags: dict[str, str] = field(default_factory=dict)

    @property
    def period_label(self) -> str:
        """The month label, e.g. ``2026-05``."""
        return self.period_start.strftime("%Y-%m")

    @property
    def is_complete_month(self) -> bool:
        """Whether this record covers a whole calendar month.

        A period is complete when it starts on the first of the month and
        ends on the first of the *next* month (exclusive end). Anything
        else is a partial period and is excluded from comparisons
        entirely — never divided, never compared.
        """
        if self.granularity.upper() != "MONTHLY":
            return True
        if self.period_start.day != 1:
            return False
        next_month = _next_month(self.period_start)
        return self.period_end >= next_month

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["period_start"] = self.period_start.isoformat()
        data["period_end"] = self.period_end.isoformat()
        data["group"] = list(self.group)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CostRecord:
        return cls(
            period_start=date.fromisoformat(data["period_start"]),
            period_end=date.fromisoformat(data["period_end"]),
            granularity=data.get("granularity", "MONTHLY"),
            service=data.get("service", ""),
            region=data.get("region", ""),
            group=tuple(data.get("group", ())),
            amount=float(data.get("amount", 0.0)),
            unit=data.get("unit", "USD"),
            metric=data.get("metric", "UnblendedCost"),
            estimated=bool(data.get("estimated", False)),
            tags=dict(data.get("tags", {})),
        )


@dataclass(slots=True, frozen=True)
class Evidence:
    """One observation that backs a number.

    ``source`` is the audit trail: ``cloudwatch``, ``cost_explorer``,
    ``s3_api``, ``access_log``, ``rate_card``. Every modelled figure must
    have a volume ``Evidence`` beside it, and the eval harness gates on
    exactly that.
    """

    metric: str
    value: float
    unit: str
    source: str
    period: str = ""
    detail: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Finding:
    """One root cause, with its evidence and its confidence.

    ``summary`` is deterministic prose written in Python. It is the
    authoritative description of the finding, and it is printed *before*
    any model-written narrative — a model that garbles a finding cannot
    hide it.
    """

    id: str
    detector: str
    title: str
    severity: str
    summary: str
    target: str
    cost_impact: float
    cost_impact_basis: str
    savings_estimate: float = 0.0
    savings_basis: str = ""
    evidence: list[Evidence] = field(default_factory=list)
    confidence: float = 1.0
    narrative: str = ""
    recommendation: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.cost_impact_basis not in BASES:
            raise ValueError(
                f"cost_impact_basis must be one of {BASES}, got {self.cost_impact_basis!r}"
            )
        if self.savings_estimate and self.savings_basis not in {
            SAVINGS_BASIS_MODELLED,
            SAVINGS_BASIS_NOT_QUANTIFIED,
        }:
            raise ValueError(
                f"savings_basis must be a known basis, got {self.savings_basis!r}"
            )

    @property
    def has_volume_evidence(self) -> bool:
        """Whether this finding carries the volume a modelled figure needs."""
        return any(e.source != "rate_card" for e in self.evidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "detector": self.detector,
            "title": self.title,
            "severity": self.severity,
            "summary": self.summary,
            "target": self.target,
            "cost_impact": self.cost_impact,
            "cost_impact_basis": self.cost_impact_basis,
            "savings_estimate": self.savings_estimate,
            "savings_basis": self.savings_basis,
            "evidence": [e.to_dict() for e in self.evidence],
            "confidence": self.confidence,
            "narrative": self.narrative,
            "recommendation": self.recommendation,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Finding:
        evidence = [
            Evidence(
                metric=e.get("metric", ""),
                value=float(e.get("value", 0.0)),
                unit=e.get("unit", ""),
                source=e.get("source", ""),
                period=e.get("period", ""),
                detail=dict(e.get("detail", {})),
            )
            for e in data.get("evidence", [])
        ]
        return cls(
            id=data["id"],
            detector=data.get("detector", ""),
            title=data.get("title", ""),
            severity=data.get("severity", ""),
            summary=data.get("summary", ""),
            target=data.get("target", ""),
            cost_impact=float(data.get("cost_impact", 0.0)),
            cost_impact_basis=data.get("cost_impact_basis", MEASURED),
            savings_estimate=float(data.get("savings_estimate", 0.0)),
            savings_basis=data.get("savings_basis", ""),
            evidence=evidence,
            confidence=float(data.get("confidence", 1.0)),
            narrative=data.get("narrative", ""),
            recommendation=data.get("recommendation", ""),
            details=dict(data.get("details", {})),
        )


def _next_month(day: date) -> date:
    """The first of the month after ``day``."""
    if day.month == 12:
        return date(day.year + 1, 1, 1)
    return date(day.year, day.month + 1, 1)


# --------------------------------------------------------------------------- #
# Severity
# --------------------------------------------------------------------------- #

SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"

SEVERITIES = (SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW)


def severity_for(impact: float, basis: str) -> str:
    """Severity from the impact and, more importantly, from the basis.

    An ``upper_bound`` is a ceiling on something we could not measure, so
    it can never be *high* — it might be worth nothing. Only a measured
    figure is allowed to be high severity.
    """
    if basis == UPPER_BOUND:
        return SEVERITY_LOW
    if impact >= 1000:
        return SEVERITY_HIGH
    if impact >= 100:
        return SEVERITY_MEDIUM
    return SEVERITY_LOW
