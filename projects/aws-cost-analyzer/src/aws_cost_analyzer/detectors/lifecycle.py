"""D3 — which storage class is wrong.

Three findings live here, and they are genuinely different problems:

**No lifecycle rule at all.** The bucket has no lifecycle configuration
(the S3 API raises ``NoSuchLifecycleConfiguration``). "Forgot the rule"
is the finding — not an error to swallow.

**A rule that does not cover the target.** The rule exists but its
prefix filter does not match the objects in question. This is a
*different* problem from having no rule, and it is the more common one:
a team adds a lifecycle rule for ``logs/`` and then wonders why
``events/`` is still expensive. A mis-scoped rule is its own finding.

**A rule that transitions too early.** AWS enforces a 30-day minimum on
Standard→Standard-IA and 90 days on Standard→Glacier, and objects under
128 KB are billed at the 128 KB tier minimum regardless — so moving
them to IA saves nothing and costs a retrieval charge later. A rule
that ignores those is a finding.

Every proposed move is costed with the retrieval charge subtracted. A
transition whose net effect is zero or negative is **not** proposed:
glacier on data that is read every month is a cost, not a saving, and
the arithmetic here is what makes that visible rather than a footnote.

Age comes from a *sampled* ``list_objects_v2``. When the sample is too
small to be representative, the finding says "insufficient sample"
rather than guessing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from ..config import Thresholds
from ..models import (
    MODELLED,
    SAVINGS_BASIS_MODELLED,
    SAVINGS_BASIS_NOT_QUANTIFIED,
    UPPER_BOUND,
    Evidence,
    Finding,
    severity_for,
)

DETECTOR = "lifecycle"

#: The minimum ages AWS itself enforces on a transition.
AWS_MIN_TRANSITION_DAYS = {
    "STANDARD_IA": 30,
    "ONEZONE_IA": 30,
    "GLACIER_IR": 90,
    "GLACIER": 90,
    "DEEP_ARCHIVE": 180,
}


@dataclass(slots=True)
class LifecycleRule:
    """One rule from ``GetBucketLifecycleConfiguration``."""

    id: str = ""
    prefix: str = ""
    status: str = "Enabled"
    transitions: list[tuple[str, int]] = field(default_factory=list)
    expiration_days: int | None = None

    def covers(self, key: str) -> bool:
        """Whether this rule's prefix filter matches an object key."""
        if not self.prefix:
            return True
        return key.startswith(self.prefix)

    def transition_to(self, storage_class: str) -> int | None:
        """The day count of a transition to a class, or ``None``."""
        for target, days in self.transitions:
            if target.upper() == storage_class.upper():
                return days
        return None


@dataclass(slots=True)
class ObjectSample:
    """One sampled object's age and size."""

    key: str
    size_bytes: int
    last_modified: date


def parse_lifecycle_rules(response: dict | None) -> list[LifecycleRule]:
    """Parse an S3 lifecycle configuration into rules.

    ``None`` means the bucket has no lifecycle configuration at all.
    """
    if not response:
        return []

    rules: list[LifecycleRule] = []
    for raw in response.get("Rules", []) or []:
        prefix = raw.get("Filter", {}).get("Prefix", "")
        if not prefix:
            prefix = raw.get("Prefix", "") or ""
        if not prefix and raw.get("Filter", {}).get("And", {}).get("Prefix"):
            prefix = raw["Filter"]["And"]["Prefix"]

        transitions: list[tuple[str, int]] = []
        for transition in raw.get("Transitions", []) or []:
            days = transition.get("Days")
            if days is None:
                continue
            transitions.append((transition.get("StorageClass", ""), int(days)))

        expiration = None
        expiration_raw = raw.get("Expiration", {}) or {}
        if "Days" in expiration_raw:
            expiration = int(expiration_raw["Days"])

        rules.append(
            LifecycleRule(
                id=raw.get("ID", ""),
                prefix=prefix,
                status=raw.get("Status", "Enabled"),
                transitions=transitions,
                expiration_days=expiration,
            )
        )
    return rules


def object_age_days(last_modified: date, today: date) -> int:
    """How old an object is, in days."""
    return (today - last_modified).days


def detect_lifecycle(
    bucket: str,
    rules: list[LifecycleRule],
    samples: list[ObjectSample],
    bucket_size_gb: float,
    thresholds: Thresholds,
    card,
    *,
    today: date,
    region: str = "",
    monthly_retrieval_gb: float = 0.0,
) -> list[Finding]:
    """Find lifecycle problems for one bucket.

    Returns a list because a bucket can have more than one problem: no
    rule *and* a mis-scoped rule are different findings about different
    objects.
    """
    findings: list[Finding] = []

    if not rules:
        findings.append(
            Finding(
                id=f"lifecycle:{bucket}:no-rules",
                detector=DETECTOR,
                title=f"{bucket} has no lifecycle rule",
                severity="medium",
                summary=(
                    f"{bucket} has no lifecycle configuration at all. "
                    f"Every object in it is billed at its current storage class "
                    f"forever, whether or not it is ever read again."
                ),
                target=bucket,
                cost_impact=0.0,
                cost_impact_basis=UPPER_BOUND,
                confidence=1.0,
                savings_basis=SAVINGS_BASIS_NOT_QUANTIFIED,
                evidence=[
                    Evidence(
                        metric="lifecycle_rule_count",
                        value=0.0,
                        unit="rules",
                        source="s3_api",
                        period=today.isoformat(),
                        detail={"bucket": bucket},
                    ),
                    Evidence(
                        metric="bucket_size",
                        value=bucket_size_gb,
                        unit="GB",
                        source="cloudwatch",
                        period=today.isoformat(),
                        detail={"bucket": bucket},
                    ),
                ],
                details={
                    "problem": "no_lifecycle_configuration",
                    "note": (
                        "The S3 API raised NoSuchLifecycleConfiguration. "
                        "The saving depends on object age and read frequency, "
                        "neither of which is measured here."
                    ),
                },
                recommendation=(
                    "Add a lifecycle rule that moves objects older than 90 days "
                    "to a colder class, and check how often they are read first."
                ),
            )
        )
        return findings

    if not samples:
        findings.append(
            Finding(
                id=f"lifecycle:{bucket}:insufficient-sample",
                detector=DETECTOR,
                title=f"{bucket} could not be age-checked",
                severity="low",
                summary=(
                    f"{bucket} has {len(rules)} lifecycle rule(s), but there were too "
                    f"few sampled objects to check whether they fire early."
                ),
                target=bucket,
                cost_impact=0.0,
                cost_impact_basis=UPPER_BOUND,
                confidence=0.3,
                savings_basis=SAVINGS_BASIS_NOT_QUANTIFIED,
                evidence=[
                    Evidence(
                        metric="sampled_object_count",
                        value=float(len(samples)),
                        unit="objects",
                        source="s3_api",
                        period=today.isoformat(),
                        detail={"bucket": bucket},
                    )
                ],
                details={"problem": "insufficient_sample"},
                recommendation=(
                    "Sample more objects, or check the rule's transition days "
                    "against the bucket's actual object ages."
                ),
            )
        )
        return findings

    # --- which objects are not covered by any rule? ------------------------ #
    uncovered = [s for s in samples if not any(rule.covers(s.key) for rule in rules)]
    if uncovered:
        uncovered_gb = sum(s.size_bytes for s in uncovered) / (1024**3)
        covered_gb = bucket_size_gb - uncovered_gb
        findings.append(
            Finding(
                id=f"lifecycle:{bucket}:mis-scoped",
                detector=DETECTOR,
                title=f"{bucket} has objects no rule covers",
                severity="medium",
                summary=(
                    f"{len(uncovered)} of {len(samples)} sampled objects in {bucket} "
                    f"are outside the prefix of every lifecycle rule "
                    f"(about {uncovered_gb:,.1f} GB of the bucket). They keep their "
                    f"current storage class indefinitely."
                ),
                target=bucket,
                cost_impact=0.0,
                cost_impact_basis=UPPER_BOUND,
                confidence=0.7,
                savings_basis=SAVINGS_BASIS_NOT_QUANTIFIED,
                evidence=[
                    Evidence(
                        metric="uncovered_object_count",
                        value=float(len(uncovered)),
                        unit="objects",
                        source="s3_api",
                        period=today.isoformat(),
                        detail={"bucket": bucket},
                    ),
                    Evidence(
                        metric="uncovered_bytes",
                        value=uncovered_gb,
                        unit="GB",
                        source="s3_api",
                        period=today.isoformat(),
                        detail={
                            "bucket": bucket,
                            "basis": "sample",
                            "example_keys": ", ".join(s.key for s in uncovered[:3]),
                        },
                    ),
                    Evidence(
                        metric="covered_bytes",
                        value=max(covered_gb, 0.0),
                        unit="GB",
                        source="cloudwatch",
                        period=today.isoformat(),
                        detail={"bucket": bucket},
                    ),
                ],
                details={
                    "problem": "mis_scoped_rule",
                    "rule_prefixes": [rule.prefix for rule in rules],
                    "example_uncovered_keys": [s.key for s in uncovered[:5]],
                    "note": (
                        "The rule exists but its prefix filter does not match these "
                        "objects. This is a different problem from having no rule."
                    ),
                },
                recommendation=(
                    "Widen the rule's prefix filter to cover these keys, or add a "
                    "second rule for the prefix they live under."
                ),
            )
        )

    # --- do any rules transition earlier than AWS allows? ------------------ #
    for rule in rules:
        for target_class, days in rule.transitions:
            aws_minimum = AWS_MIN_TRANSITION_DAYS.get(target_class.upper())
            if aws_minimum is None:
                continue
            if days >= aws_minimum:
                continue

            findings.append(
                Finding(
                    id=f"lifecycle:{bucket}:early-transition:{rule.id}:{target_class}",
                    detector=DETECTOR,
                    title=f"{bucket} transitions to {target_class} after {days} days",
                    severity="medium",
                    summary=(
                        f"Lifecycle rule {rule.id or '(unnamed)'} in {bucket} moves objects "
                        f"to {target_class} after {days} days. AWS requires at least "
                        f"{aws_minimum} days for this transition, and objects younger "
                        f"than {thresholds.min_age_days_for_glacier} days are not worth "
                        f"moving."
                    ),
                    target=bucket,
                    cost_impact=0.0,
                    cost_impact_basis=UPPER_BOUND,
                    confidence=1.0,
                    savings_basis=SAVINGS_BASIS_NOT_QUANTIFIED,
                    evidence=[
                        Evidence(
                            metric="configured_transition_days",
                            value=float(days),
                            unit="days",
                            source="s3_api",
                            period=today.isoformat(),
                            detail={"bucket": bucket, "rule_id": rule.id},
                        ),
                        Evidence(
                            metric="aws_minimum_transition_days",
                            value=float(aws_minimum),
                            unit="days",
                            source="s3_api",
                            period=today.isoformat(),
                            detail={"bucket": bucket, "storage_class": target_class},
                        ),
                    ],
                    details={
                        "problem": "early_transition",
                        "rule_id": rule.id,
                        "storage_class": target_class,
                        "configured_days": days,
                        "aws_minimum_days": aws_minimum,
                    },
                    recommendation=(
                        f"Raise the transition to at least {aws_minimum} days. "
                        f"An early transition can be rejected by AWS, and the objects "
                        f"it covers are too young for a colder class to pay off."
                    ),
                )
            )

    # --- is there a cold-class opportunity that actually pays? ------------- #
    cold = _cold_class_opportunity(samples, rules, thresholds, card, today, region)
    if cold is not None:
        findings.append(cold)

    return findings


def _cold_class_opportunity(
    samples: list[ObjectSample],
    rules: list[LifecycleRule],
    thresholds: Thresholds,
    card,
    today: date,
    region: str,
) -> Finding | None:
    """Find objects old enough to move, and cost the move honestly."""
    eligible = [
        s
        for s in samples
        if object_age_days(s.last_modified, today) >= thresholds.min_age_days_for_glacier
        and s.size_bytes >= thresholds.min_size_kb_for_ia * 1024
    ]
    if not eligible:
        return None

    eligible_gb = sum(s.size_bytes for s in eligible) / (1024**3)
    if eligible_gb <= 0:
        return None

    target_class = "GLACIER_IR"
    monthly_saving = card.transition_saving(eligible_gb, "STANDARD", target_class)

    evidence = [
        Evidence(
            metric="eligible_bytes",
            value=eligible_gb,
            unit="GB",
            source="s3_api",
            period=today.isoformat(),
            detail={
                "object_count": str(len(eligible)),
                "basis": "sample",
                "min_age_days": str(thresholds.min_age_days_for_glacier),
                "min_size_kb": str(thresholds.min_size_kb_for_ia),
            },
        ),
    ]

    if monthly_saving <= 0:
        # The move would cost more than it saves. Say so, and say why,
        # rather than proposing it anyway.
        return Finding(
            id="lifecycle:cold-class-not-worth-it",
            detector=DETECTOR,
            title="Moving the cold objects would not pay for itself",
            severity="low",
            summary=(
                f"{eligible_gb:,.1f} GB in the sample is old enough to move to "
                f"{target_class}, but the storage saving does not cover the retrieval "
                f"charge. These objects are read often enough that a colder class "
                f"would cost more than it saves."
            ),
            target="(sample)",
            cost_impact=0.0,
            cost_impact_basis=MODELLED,
            confidence=0.6,
            savings_basis=SAVINGS_BASIS_NOT_QUANTIFIED,
            evidence=evidence,
            details={
                "problem": "cold_class_not_worth_it",
                "storage_class": target_class,
                "monthly_saving_if_moved": monthly_saving,
                "note": (
                    "The net saving is at most zero after the retrieval charge, so no "
                    "move is proposed."
                ),
            },
            recommendation=(
                "Leave these objects where they are, or use Standard-IA — which has "
                "no retrieval charge — if the storage saving alone is enough."
            ),
        )

    return Finding(
        id="lifecycle:cold-class-opportunity",
        detector=DETECTOR,
        title=f"{eligible_gb:,.0f} GB could move to {target_class}",
        severity=severity_for(monthly_saving, MODELLED),
        summary=(
            f"About {eligible_gb:,.1f} GB of the sample is older than "
            f"{thresholds.min_age_days_for_glacier} days and larger than "
            f"{thresholds.min_size_kb_for_ia} KB. Moving it to {target_class} would "
            f"avoid about ${monthly_saving:,.2f} a month at the observed volume."
        ),
        target="(sample)",
        cost_impact=monthly_saving,
        cost_impact_basis=MODELLED,
        savings_estimate=monthly_saving,
        savings_basis=SAVINGS_BASIS_MODELLED,
        confidence=0.6,
        evidence=[
            *evidence,
            Evidence(
                metric="monthly_saving",
                value=monthly_saving,
                unit="USD",
                source="rate_card",
                period=today.isoformat(),
                detail={
                    "from_class": "STANDARD",
                    "to_class": target_class,
                    "rate_card_region": card.region,
                    "analysis_region": region,
                },
            ),
        ],
        details={
            "problem": "cold_class_opportunity",
            "storage_class": target_class,
            "monthly_saving": monthly_saving,
            "note": (
                "Modelled from the sampled volume times the illustrative rate card. "
                "The retrieval charge is subtracted, so this is the net figure."
            ),
        },
        recommendation=(
            f"Add a lifecycle rule transitioning to {target_class} after "
            f"{thresholds.min_age_days_for_glacier} days, once you have confirmed the "
            f"objects are not read every month."
        ),
    )


def detect_bucket_without_rules(bucket: str, thresholds: Thresholds, card) -> Finding:
    """The "no lifecycle at all" finding, on its own.

    Useful when the caller only knows the bucket exists and has not
    sampled its objects.
    """
    return Finding(
        id=f"lifecycle:{bucket}:no-rules",
        detector=DETECTOR,
        title=f"{bucket} has no lifecycle rule",
        severity="medium",
        summary=(
            f"{bucket} has no lifecycle configuration. Objects in it keep their "
            f"current storage class for as long as they exist."
        ),
        target=bucket,
        cost_impact=0.0,
        cost_impact_basis=UPPER_BOUND,
        confidence=1.0,
        savings_basis=SAVINGS_BASIS_NOT_QUANTIFIED,
        evidence=[
            Evidence(
                metric="lifecycle_rule_count",
                value=0.0,
                unit="rules",
                source="s3_api",
                period="",
                detail={"bucket": bucket},
            )
        ],
        details={"problem": "no_lifecycle_configuration"},
        recommendation="Add a lifecycle rule for objects you no longer read.",
    )


def measured_bucket_size(bucket: str, gb: float, period: str) -> Evidence:
    """A measured bucket size from CloudWatch."""
    return Evidence(
        metric="bucket_size",
        value=gb,
        unit="GB",
        source="cloudwatch",
        period=period,
        detail={"bucket": bucket},
    )
