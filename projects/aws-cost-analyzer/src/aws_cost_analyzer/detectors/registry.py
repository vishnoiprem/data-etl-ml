"""The detector registry — runs all four and keeps the findings stable.

Finding IDs must be **stable**: the same input has to produce the same
IDs across runs, or the eval harness cannot compare two runs and a
reader cannot tell whether a finding is new or a repeat. Every ID is
built from the detector, the target and the period — never from a
timestamp or a list index.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..config import Settings
from ..models import CostRecord, Finding
from . import access, allocation, growth, lifecycle


@dataclass(slots=True)
class AnalysisInput:
    """Everything the detectors may read.

    Every field is optional except the cost records, because a run may
    have only some of the data — a snapshot of Cost Explorer output
    with no CloudWatch, no S3 metadata and no access logs. The
    detectors use what is there and say what is missing.
    """

    records: list[CostRecord] = field(default_factory=list)
    latest_period: str = ""

    #: Per-bucket CloudWatch request counts, for the D2 cross-check.
    cloudwatch_requests: dict[str, float] = field(default_factory=dict)

    #: Per-bucket CloudWatch bucket sizes, in GB.
    bucket_sizes_gb: dict[str, float] = field(default_factory=dict)

    #: Per-bucket lifecycle rules, already parsed.
    lifecycle_rules: dict[str, list[lifecycle.LifecycleRule]] = field(default_factory=dict)

    #: Per-bucket sampled objects.
    object_samples: dict[str, list[lifecycle.ObjectSample]] = field(default_factory=dict)

    #: Buckets known to have access logging disabled.
    logging_disabled: list[str] = field(default_factory=list)

    #: The parsed access log, if one was available.
    access_log: access.AccessLog | None = None

    #: Per-tag-value cost records (group is [SERVICE, TAG]).
    tagged_records: list[CostRecord] = field(default_factory=list)

    #: The unfiltered total for the service being allocated.
    untagged_service_total: float = 0.0

    #: The service under analysis.
    service: str = "Amazon Simple Storage Service"

    #: The index of the group element that identifies a resource.
    resource_group_index: int = 1

    #: Today's date, for age calculations.
    today: Any = None

    notes: list[str] = field(default_factory=list)


def run_all(
    data: AnalysisInput,
    settings: Settings,
    card,
) -> list[Finding]:
    """Run all four detectors and return the findings, most severe first.

    A detector that raises does not take the run down with it: the
    other three still report, and the failure is recorded as a note.
    One broken detector must not hide the findings of the ones that
    work.
    """
    findings: list[Finding] = []
    notes: list[str] = list(data.notes)

    runners = [
        ("growth", lambda: _run_growth(data, settings)),
        ("access", lambda: _run_access(data, settings, card)),
        ("lifecycle", lambda: _run_lifecycle(data, settings, card)),
        ("allocation", lambda: _run_allocation(data, settings)),
    ]

    for name, runner in runners:
        try:
            findings.extend(runner())
        except Exception as exc:  # noqa: BLE001 — one detector must not sink the run
            notes.append(f"{name} detector failed: {exc}")

    findings.sort(key=_sort_key)
    data.notes = notes
    return findings


def _sort_key(finding: Finding) -> tuple:
    """Order: severity, then impact, then ID (for stability)."""
    severity_order = {"high": 0, "medium": 1, "low": 2}
    return (
        severity_order.get(finding.severity, 3),
        -finding.cost_impact,
        finding.id,
    )


def _run_growth(data: AnalysisInput, settings: Settings) -> list[Finding]:
    if not data.records:
        return []
    return growth.detect_growth(
        data.records,
        settings.thresholds,
        group_index=data.resource_group_index,
        service_filter=None,
        latest_period=data.latest_period,
    )


def _run_access(data: AnalysisInput, settings: Settings, card) -> list[Finding]:
    findings: list[Finding] = []

    monthly_spend = sum(r.amount for r in data.records)

    if data.access_log is not None and data.access_log.by_bucket:
        findings.extend(
            access.detect_access_patterns(
                data.access_log,
                data.cloudwatch_requests,
                settings.thresholds,
                card,
                region=settings.region,
                monthly_spend=monthly_spend,
            )
        )
    elif data.logging_disabled:
        findings.extend(
            access.detect_logging_disabled(
                data.logging_disabled,
                settings.thresholds,
                card,
                region=settings.region,
                monthly_spend=monthly_spend,
            )
        )

    return findings


def _run_lifecycle(data: AnalysisInput, settings: Settings, card) -> list[Finding]:
    findings: list[Finding] = []
    today = data.today

    for bucket, rules in data.lifecycle_rules.items():
        size_gb = data.bucket_sizes_gb.get(bucket, 0.0)
        samples = data.object_samples.get(bucket, [])
        findings.extend(
            lifecycle.detect_lifecycle(
                bucket,
                rules,
                samples,
                size_gb,
                settings.thresholds,
                card,
                today=today,
                region=settings.region,
            )
        )

    return findings


def _run_allocation(data: AnalysisInput, settings: Settings) -> list[Finding]:
    if not data.tagged_records:
        return []

    # The untagged gap is emitted by the detector itself — it is part of
    # the allocation answer, not a separate concern.
    return allocation.detect_allocation(
        data.tagged_records,
        data.untagged_service_total,
        settings.thresholds,
        region=settings.region,
        service=data.service,
    )


def dedupe(findings: list[Finding]) -> list[Finding]:
    """Remove duplicate IDs, keeping the first.

    Two detectors can reach the same conclusion from different
    evidence — a bucket can both have grown and have no lifecycle rule.
    When they produce the same ID, the first one wins.
    """
    seen: set[str] = set()
    unique: list[Finding] = []
    for finding in findings:
        if finding.id in seen:
            continue
        seen.add(finding.id)
        unique.append(finding)
    return unique
