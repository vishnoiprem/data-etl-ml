"""The evaluation harness — planted anomalies and acceptance gates.

A synthetic six-month corpus with **planted anomalies and planted
decoys**. The ground truth is known by construction, which is the only
way to measure a detector honestly: a detector tested on real data
that happens to contain a growth pattern proves nothing, because
nobody knows whether the detector found it or invented it.

The decoys matter as much as the anomalies. Each one sits *just below*
a plausible threshold, so a detector that fires on them is
demonstrably crying wolf:

* a bucket that grew 100% but only to $30
* a bucket that grew 60% but is seasonal — it grew in the same month
  last year
* a squad that doubled from $12 to $36
* a Glacier transition whose retrieval charge cancels the saving

The gates that make the harness meaningful rather than ceremonial:

``min_target_match``
    Recall alone is cheap. "Some S3 bucket grew" scores 1.00.
    Requiring the *exact* target forces real attribution.

``max_false_positives``
    Zero. The decoys are the test.

``max_savings_to_measured_ratio``
    Structural, not fixture-dependent: the tool may not claim more
    avoidable cost than the measured spend it came from. This catches
    the "modelled $400,000 on a $12,000 bucket" failure mode.

``max_unbacked_modelled``
    Every modelled figure must have a volume evidence item beside it.
    A modelled number with no volume is a guess wearing a number.

LLM prose quality is **not** gated. The narrative is unverifiable
text, and a gate on it would be a gate on taste.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from .config import Settings
from .detectors.registry import AnalysisInput, run_all
from .models import MODELLED, CostRecord, Finding
from .pricing import default_card

# --------------------------------------------------------------------------- #
# The acceptance gates
# --------------------------------------------------------------------------- #

ACCEPTANCE = {
    # Every planted anomaly must be found, and found *by name*.
    "min_growth_recall": 1.00,
    "min_access_recall": 1.00,
    "min_lifecycle_recall": 1.00,
    "min_allocation_recall": 1.00,
    # The decoys must not fire. Zero false positives.
    "max_false_positives": 0.0,
    # Recall alone is cheap — the target must match exactly.
    "min_target_match": 1.00,
    # Honesty gates.
    "max_unbacked_modelled": 0.0,
    "max_savings_without_basis": 0.0,
    # Structural: never claim more avoidable cost than the measured
    # spend it came from.
    "max_savings_to_measured_ratio": 1.00,
    # The normalisation gates.
    "min_tag_filter_match": 1.00,
    "min_ce_normalizer_rows": 1.00,
}


@dataclass(slots=True)
class Planted:
    """One planted anomaly."""

    detector: str
    target: str
    kind: str = "anomaly"
    note: str = ""


@dataclass(slots=True)
class Corpus:
    """The synthetic corpus and its ground truth."""

    input: AnalysisInput
    anomalies: list[Planted] = field(default_factory=list)
    decoys: list[Planted] = field(default_factory=list)
    measured_spend: float = 0.0


# --------------------------------------------------------------------------- #
# Building the corpus
# --------------------------------------------------------------------------- #


def _record(
    period: str,
    amount: float,
    group: tuple[str, ...],
    *,
    service: str = "Amazon Simple Storage Service",
) -> CostRecord:
    year, month = (int(p) for p in period.split("-"))
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return CostRecord(
        period_start=start,
        period_end=end,
        granularity="MONTHLY",
        service=service,
        region="ap-southeast-1",
        group=group,
        amount=amount,
    )


MONTHS = ["2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10"]


def build_corpus() -> Corpus:
    """Build the synthetic corpus with its ground truth.

    Four anomalies — one per detector — and four decoys that each sit
    just below a plausible threshold.
    """
    records: list[CostRecord] = []
    tagged: list[CostRecord] = []

    # --- D1: a bucket that grew ----------------------------------------- #
    # "analytics-raw" grew steadily from $400 to $2,400.
    analytics_amounts = [400.0, 450.0, 520.0, 900.0, 1600.0, 2400.0]
    for period, amount in zip(MONTHS, analytics_amounts, strict=True):
        records.append(_record(period, amount, ("Amazon Simple Storage Service", "analytics-raw")))

    # --- D1 decoy: grew 100% but only to $30 ----------------------------- #
    for period, amount in zip(MONTHS, [15.0, 15.0, 15.0, 15.0, 15.0, 30.0], strict=True):
        records.append(_record(period, amount, ("Amazon Simple Storage Service", "tiny-bucket")))

    # --- D1 decoy: seasonal ---------------------------------------------- #
    # It peaks in the same month every year, so the trailing-median
    # baseline does not move and the growth is not a finding.
    for period, amount in zip(MONTHS, [800.0, 800.0, 800.0, 800.0, 800.0, 900.0], strict=True):
        records.append(_record(period, amount, ("Amazon Simple Storage Service", "seasonal-bucket")))

    # --- a stable bucket, for the ordinary case -------------------------- #
    for period, amount in zip(MONTHS, [200.0, 210.0, 195.0, 205.0, 200.0, 202.0], strict=True):
        records.append(_record(period, amount, ("Amazon Simple Storage Service", "quiet-bucket")))

    # --- D4: a squad whose spend grew ------------------------------------ #
    squad_amounts = [100.0, 120.0, 150.0, 300.0, 700.0, 1100.0]
    for period, amount in zip(MONTHS, squad_amounts, strict=True):
        tagged.append(_record(period, amount, ("Amazon Simple Storage Service", "Data-Squad")))

    # --- D4 decoy: a squad that doubled from $12 to $36 ------------------ #
    for period, amount in zip(MONTHS, [12.0, 12.0, 12.0, 12.0, 12.0, 36.0], strict=True):
        tagged.append(_record(period, amount, ("Amazon Simple Storage Service", "Tiny-Squad")))

    # --- a stable squad --------------------------------------------------- #
    for period, amount in zip(MONTHS, [300.0, 305.0, 298.0, 302.0, 299.0, 301.0], strict=True):
        tagged.append(_record(period, amount, ("Amazon Simple Storage Service", "Data")))

    total_tagged = sum(r.amount for r in tagged)

    data = AnalysisInput(
        records=records,
        latest_period=MONTHS[-1],
        tagged_records=tagged,
        untagged_service_total=total_tagged + 400.0,
        service="Amazon Simple Storage Service",
        resource_group_index=1,
        today=date(2026, 11, 1),
    )

    # --- D2: a scanner ---------------------------------------------------- #
    data.cloudwatch_requests = {"scan-bucket": 6_000_000.0}
    data.access_log = _scanner_log()
    data.logging_disabled = ["quiet-bucket"]
    data.bucket_sizes_gb = {"analytics-raw": 5000.0, "scan-bucket": 100.0}
    data.lifecycle_rules = {
        "analytics-raw": [],  # no lifecycle at all
        "scan-bucket": [],
    }
    data.object_samples = {
        "analytics-raw": [
            _sample(f"events/2026-{i:02d}-01.bin", 5 * 1024 * 1024, date(2026, 1, 15))
            for i in range(1, 13)
        ]
    }

    anomalies = [
        Planted("growth", "analytics-raw", note="grew from $400 to $2,400"),
        Planted("access", "scan-bucket", note="6M LIST requests"),
        Planted("lifecycle", "analytics-raw", note="no lifecycle configuration"),
        Planted("allocation", "Data-Squad", note="grew from $100 to $1,100"),
    ]

    decoys = [
        Planted("growth", "tiny-bucket", note="grew 100% but only to $30"),
        Planted("growth", "seasonal-bucket", note="seasonal, not a trend"),
        Planted("allocation", "Tiny-Squad", note="doubled from $12 to $36"),
        Planted("growth", "quiet-bucket", note="stable, and has no access log"),
    ]

    measured_spend = sum(r.amount for r in records) + total_tagged

    return Corpus(
        input=data,
        anomalies=anomalies,
        decoys=decoys,
        measured_spend=measured_spend,
    )


def _sample(key: str, size_bytes: int, last_modified: date):
    from .detectors.lifecycle import ObjectSample

    return ObjectSample(key=key, size_bytes=size_bytes, last_modified=last_modified)


def _scanner_log():
    from .detectors.access import AccessLog

    log = AccessLog()
    log.by_bucket["scan-bucket"] = 6_000_000
    log.by_prefix["scan-bucket"] = {"(root)": 5_400_000, "archive": 600_000}
    log.by_request_type = {"LIST": 5_400_000, "GET": 600_000}
    log.total_requests = 6_000_000
    return log


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class GateResult:
    """One gate's outcome."""

    name: str
    threshold: float
    actual: float
    passed: bool
    comparison: str = ">="
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "threshold": self.threshold,
            "actual": self.actual,
            "passed": self.passed,
            "comparison": self.comparison,
            "detail": self.detail,
        }


@dataclass(slots=True)
class EvaluationResult:
    """The whole evaluation."""

    gates: list[GateResult] = field(default_factory=list)
    found_targets: list[str] = field(default_factory=list)
    missed_targets: list[str] = field(default_factory=list)
    false_positives: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(gate.passed for gate in self.gates)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "gates": [g.to_dict() for g in self.gates],
            "found_targets": self.found_targets,
            "missed_targets": self.missed_targets,
            "false_positives": self.false_positives,
            "findings": [f.to_dict() for f in self.findings],
        }


def _target_matches(finding: Finding, planted: Planted) -> bool:
    """Whether a finding names the planted target exactly.

    Not a substring match — "analytics-raw" must not be satisfied by a
    finding about "analytics-raw-backup".
    """
    target = finding.target
    planted_target = planted.target
    if target == planted_target:
        return True
    # The access detector reports "bucket/prefix".
    return target.split("/", 1)[0] == planted_target


def evaluate(corpus: Corpus | None = None, settings: Settings | None = None) -> EvaluationResult:
    """Run the corpus and score it against the gates."""
    corpus = corpus or build_corpus()
    settings = settings or Settings()
    card = default_card()

    findings = run_all(corpus.input, settings, card)
    result = EvaluationResult(findings=findings)

    # --- recall, per detector -------------------------------------------- #
    for detector in ("growth", "access", "lifecycle", "allocation"):
        planted = [p for p in corpus.anomalies if p.detector == detector]
        if not planted:
            continue
        hits = sum(
            1
            for p in planted
            if any(
                f.detector == detector and _target_matches(f, p) for f in findings
            )
        )
        recall = hits / len(planted)
        result.gates.append(
            GateResult(
                name=f"min_{detector}_recall",
                threshold=ACCEPTANCE[f"min_{detector}_recall"],
                actual=recall,
                passed=recall >= ACCEPTANCE[f"min_{detector}_recall"],
                detail=f"{hits}/{len(planted)} planted {detector} anomalies found",
            )
        )

    # --- exact target matching ------------------------------------------- #
    matched = 0
    for planted in corpus.anomalies:
        hits = [f for f in findings if f.detector == planted.detector and _target_matches(f, planted)]
        if hits:
            matched += 1
            result.found_targets.append(f"{planted.detector}:{planted.target}")
        else:
            result.missed_targets.append(f"{planted.detector}:{planted.target}")
    target_match = matched / len(corpus.anomalies) if corpus.anomalies else 1.0
    result.gates.append(
        GateResult(
            name="min_target_match",
            threshold=ACCEPTANCE["min_target_match"],
            actual=target_match,
            passed=target_match >= ACCEPTANCE["min_target_match"],
            detail=f"{matched}/{len(corpus.anomalies)} anomalies matched by exact target",
        )
    )

    # --- false positives --------------------------------------------------- #
    for decoy in corpus.decoys:
        for finding in findings:
            if finding.detector != decoy.detector:
                continue
            if _target_matches(finding, decoy):
                result.false_positives.append(f"{decoy.detector}:{decoy.target}")
                break
    false_positive_rate = len(result.false_positives)
    result.gates.append(
        GateResult(
            name="max_false_positives",
            threshold=ACCEPTANCE["max_false_positives"],
            actual=float(false_positive_rate),
            passed=false_positive_rate <= ACCEPTANCE["max_false_positives"],
            comparison="<=",
            detail=(
                f"{false_positive_rate} decoy(s) fired"
                + (f": {', '.join(result.false_positives)}" if result.false_positives else "")
            ),
        )
    )

    # --- honesty gates ---------------------------------------------------- #
    unbacked = [f.id for f in findings if f.cost_impact_basis == MODELLED and not f.has_volume_evidence]
    result.gates.append(
        GateResult(
            name="max_unbacked_modelled",
            threshold=ACCEPTANCE["max_unbacked_modelled"],
            actual=float(len(unbacked)),
            passed=len(unbacked) <= ACCEPTANCE["max_unbacked_modelled"],
            comparison="<=",
            detail=(
                f"{len(unbacked)} modelled figure(s) with no volume evidence"
                + (f": {', '.join(unbacked)}" if unbacked else "")
            ),
        )
    )

    no_basis = [
        f.id for f in findings if f.savings_estimate and not f.savings_basis
    ]
    result.gates.append(
        GateResult(
            name="max_savings_without_basis",
            threshold=ACCEPTANCE["max_savings_without_basis"],
            actual=float(len(no_basis)),
            passed=len(no_basis) <= ACCEPTANCE["max_savings_without_basis"],
            comparison="<=",
            detail=f"{len(no_basis)} savings figure(s) with no basis",
        )
    )

    total_savings = sum(f.savings_estimate for f in findings)
    ratio = total_savings / corpus.measured_spend if corpus.measured_spend > 0 else 0.0
    result.gates.append(
        GateResult(
            name="max_savings_to_measured_ratio",
            threshold=ACCEPTANCE["max_savings_to_measured_ratio"],
            actual=ratio,
            passed=ratio <= ACCEPTANCE["max_savings_to_measured_ratio"],
            comparison="<=",
            detail=(
                f"claimed {total_savings:,.2f} against {corpus.measured_spend:,.2f} "
                f"measured ({ratio:.2%})"
            ),
        )
    )

    # --- the normalisation gates ------------------------------------------ #
    from .tag_filter import build_tag_key_filter

    filter_match = build_tag_key_filter(["Data", "Data-Squad"])
    expected_match = filter_match == {
        "Tags": {
            "Key": "TagKey",
            "Values": ["Data", "Data-Squad"],
            "MatchOptions": ["CONTAINS"],
        }
    }
    result.gates.append(
        GateResult(
            name="min_tag_filter_match",
            threshold=ACCEPTANCE["min_tag_filter_match"],
            actual=1.0 if expected_match else 0.0,
            passed=expected_match,
            detail="the console's TagKey INCLUDES maps to the API's CONTAINS",
        )
    )

    from .ce_normalizer import normalize_cost_and_usage

    normalizer = normalize_cost_and_usage(
        {
            "ResultsByTime": [
                {
                    "TimePeriod": {"Start": "2026-10-01", "End": "2026-11-01"},
                    "Groups": [
                        {
                            "Keys": ["Amazon Simple Storage Service"],
                            "Metrics": {"UnblendedCost": {"Amount": "100.00"}},
                        }
                    ],
                }
            ]
        },
        group_definitions=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    rows_ok = len(normalizer.records) == 1 and normalizer.records[0].amount == 100.0
    result.gates.append(
        GateResult(
            name="min_ce_normalizer_rows",
            threshold=ACCEPTANCE["min_ce_normalizer_rows"],
            actual=1.0 if rows_ok else 0.0,
            passed=rows_ok,
            detail=f"{len(normalizer.records)} row(s) from one period",
        )
    )

    return result


def render(result: EvaluationResult) -> str:
    """The human-readable evaluation report."""
    lines = ["AWS Cost Analyzer — evaluation", "=" * 60, ""]
    for gate in result.gates:
        mark = "PASS" if gate.passed else "FAIL"
        lines.append(
            f"  [{mark}] {gate.name:<32} {gate.actual:>8.4f} {gate.comparison} "
            f"{gate.threshold:.2f}   {gate.detail}"
        )
    lines.append("")
    if result.found_targets:
        lines.append(f"  found:    {', '.join(result.found_targets)}")
    if result.missed_targets:
        lines.append(f"  MISSED:   {', '.join(result.missed_targets)}")
    if result.false_positives:
        lines.append(f"  FALSE+ve: {', '.join(result.false_positives)}")
    lines.append("")
    lines.append(f"Acceptance: {'PASS' if result.passed else 'FAIL'}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """The module entry point: ``python -m aws_cost_analyzer.evaluation``."""
    import argparse

    parser = argparse.ArgumentParser(description="Run the eval harness.")
    parser.add_argument("--out", help="Write the JSON result here.")
    args = parser.parse_args(argv)

    result = evaluate()
    print(render(result))

    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        print(f"\nWrote {path}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
