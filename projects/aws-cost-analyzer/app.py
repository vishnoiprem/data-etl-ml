"""The FastAPI app — a read-only view over the analysis.

    uvicorn app:app --reload

Four endpoints:

``GET /health``
    The snapshot count, the rate card's region, and the router name.

``GET /findings``
    The findings, filterable by detector. Every figure carries its
    basis.

``GET /report``
    The same view as the text report.

``GET /detectors``
    The four detectors and what each one needs to answer.

The app is **read-only by construction**: there is no endpoint that
fetches from AWS, mutates anything, or writes a finding. Fetching is
the separate ``fetch_aws.py`` script's job, and a finding is only ever
produced by the deterministic path.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from fastapi import FastAPI, Query  # noqa: E402

from aws_cost_analyzer.config import load_settings  # noqa: E402
from aws_cost_analyzer.detectors.registry import AnalysisInput, run_all  # noqa: E402
from aws_cost_analyzer.evaluation import build_corpus  # noqa: E402
from aws_cost_analyzer.narrative import apply_narratives, get_default_router  # noqa: E402
from aws_cost_analyzer.pricing import default_card  # noqa: E402
from aws_cost_analyzer.report import ReportContext, render_text, to_json  # noqa: E402
from aws_cost_analyzer.snapshots import (  # noqa: E402
    DEFAULT_SNAPSHOT_DIR,
    KIND_COST_RECORDS,
    list_snapshots,
    read_snapshot,
)

app = FastAPI(
    title="AWS Cost Analyzer",
    description="Deterministic S3 cost root-cause analysis. Read-only.",
    version="0.1.0",
)

#: Where the snapshots live, relative to the project root.
SNAPSHOTS_DIR = ROOT / DEFAULT_SNAPSHOT_DIR


def _analysis() -> tuple[list, ReportContext]:
    """Run the analysis over the best available data.

    A snapshot is preferred; the synthetic corpus is the fallback so
    the app is useful out of the box, and so the endpoints can be
    tested without any AWS data on disk.
    """
    settings = load_settings()
    card = default_card()

    snapshots = [
        read_snapshot(path) for path in list_snapshots(SNAPSHOTS_DIR) if path.suffix == ".json"
    ]
    snapshots = [s for s in snapshots if s.kind == KIND_COST_RECORDS]

    if snapshots:
        snapshot = snapshots[0]
        records = list(snapshot.records)
        periods = sorted({r.period_label for r in records if not r.estimated})
        data = AnalysisInput(
            records=records,
            latest_period=periods[-1] if periods else "",
            resource_group_index=-1,
            service="Amazon Simple Storage Service",
            untagged_service_total=sum(r.amount for r in records),
        )
        context = ReportContext(
            region=snapshot.region or settings.region,
            start=snapshot.start,
            end=snapshot.end,
            rate_card_region=card.region,
            rate_card_checked_on=card.checked_on,
            total_spend=sum(r.amount for r in snapshot.complete_records),
            records_analyzed=len(snapshot.records),
            excluded_periods=snapshot.excluded_periods,
            notes=list(snapshot.errors),
        )
        source = "snapshot"
    else:
        corpus = build_corpus()
        data = corpus.input
        context = ReportContext(
            region=settings.region,
            start=settings.start,
            end=settings.end,
            rate_card_region=card.region,
            rate_card_checked_on=card.checked_on,
            total_spend=corpus.measured_spend,
            records_analyzed=len(corpus.input.records),
            notes=list(corpus.input.notes),
        )
        source = "demo corpus"

    findings = run_all(data, settings, card)
    router = get_default_router()
    apply_narratives(router, findings)
    context.router_name = router.name
    context.notes.append(f"Source: {source}")

    return findings, context


@app.get("/health")
def health() -> dict:
    """Is it running, and on what?"""
    card = default_card()
    snapshots = list_snapshots(SNAPSHOTS_DIR)
    router = get_default_router()
    return {
        "status": "ok",
        "snapshots": len(snapshots),
        "rate_card_region": card.region,
        "rate_card_checked_on": card.checked_on,
        "router": router.name,
        "read_only": True,
    }


@app.get("/findings")
def findings(
    detector: str | None = Query(default=None, description="Filter by detector."),
    severity: str | None = Query(default=None, description="Filter by severity."),
) -> dict:
    """The findings, with every figure carrying its basis."""
    all_findings, context = _analysis()

    selected = all_findings
    if detector:
        selected = [f for f in selected if f.detector == detector]
    if severity:
        selected = [f for f in selected if f.severity == severity]

    payload = to_json(selected, context)
    payload["findings"] = [f.to_dict() for f in selected]
    payload["finding_count"] = len(selected)
    return payload


@app.get("/report")
def report() -> dict:
    """The full report — the same view as the Cost Explorer URL."""
    all_findings, context = _analysis()
    payload = to_json(all_findings, context)
    payload["text"] = render_text(all_findings, context)
    return payload


@app.get("/detectors")
def detectors() -> dict:
    """Which detectors exist and what they answer."""
    return {
        "detectors": [
            {
                "name": "growth",
                "question": "which bucket or prefix grew, and by how much?",
                "needs": "Cost Explorer with the resource dimension",
            },
            {
                "name": "access",
                "question": "which access pattern cost money?",
                "needs": "S3 server access logs (CloudWatch is per-bucket only)",
            },
            {
                "name": "lifecycle",
                "question": "which storage class is wrong?",
                "needs": "the bucket's lifecycle configuration and a sample of objects",
            },
            {
                "name": "allocation",
                "question": "which tag or squad is spending?",
                "needs": "Cost Explorer grouped by tag",
            },
        ]
    }


@app.get("/healthz")
def healthz() -> dict:
    """A liveness probe that does not do any work."""
    return {"status": "ok"}
