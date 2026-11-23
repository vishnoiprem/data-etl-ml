"""The FastAPI app.

**One app, built once, at import time.** The simulation is deterministic, so
there is no reason to rebuild the world per request — and building it once
means the endpoint latencies reflect the cost of the *query*, not the cost of
regenerating a week of e-commerce demand.

The endpoints are thin: parse a request model, call the service, return the
result. No business logic lives in this file, which is why the demo script
and the tests can exercise exactly the same behaviour without going through
HTTP.

Sub-parts
---------
- ``GET /health`` — what is loaded, what is live.
- ``GET /metrics`` — the full KPI, cost and commercial scorecard.
- ``GET /dispatch`` — dispatch plans, per day or all days.
- ``GET /routes`` — planned routes with their cost breakdown.
- ``GET /tracking/{shipment_id}`` — the customer-facing tracking timeline.
- ``GET /sla`` — confirmed breaches and at-risk shipments.
- ``GET /fraud`` — risk decisions, planted-fraud recall, courier findings.
- ``GET /cod`` — cash collected, outstanding and the remittance cycle.
- ``GET /assumptions`` — every business number, with its provenance.
- ``GET /decisions`` — the audit ledger.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

HERE = Path(__file__).resolve().parent
SRC = HERE / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tms.audit import write_ledger  # noqa: E402
from tms.config import REPORTS_DIR, Settings  # noqa: E402
from tms.service import TmsService  # noqa: E402

app = FastAPI(
    title="TMS — E-commerce Logistics",
    version="0.1.0",
    description=(
        "A transport management system for e-commerce last-mile delivery: order "
        "lifecycle, dispatch under capacity, VRPTW routing, dynamic ETA with "
        "P50/P90, NDR retry, COD remittance, SLA early-warning and COD fraud "
        "scoring. Runs fully offline on a synthetic corpus."
    ),
)

#: The one built system every endpoint reads from.
service = TmsService.create(Settings.from_env())


# --------------------------------------------------------------------------- #
# Request models
# --------------------------------------------------------------------------- #


class ShipmentLookup(BaseModel):
    """A request to look up one shipment's tracking timeline."""

    shipment_id: str = Field(..., min_length=3, max_length=64)


class DispatchQuery(BaseModel):
    """A request for one day's dispatch plan."""

    day: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #


@app.get("/health")
def health() -> dict[str, Any]:
    """Corpus size, what is live, and the current simulated clock."""
    return service.health()


@app.get("/metrics")
def metrics() -> dict[str, Any]:
    """The full scorecard: delivery KPIs, cost model and commercial view."""
    return service.metrics()


@app.get("/dispatch")
def dispatch(day: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")) -> dict[str, Any]:
    """Dispatch plans — one day, or every day."""
    result = service.dispatch_view(day)
    if not result.get("ok", True):
        raise HTTPException(status_code=404, detail=result.get("error", "not found"))
    return result


@app.get("/routes")
def routes() -> dict[str, Any]:
    """Every planned route with its cost breakdown and utilisation."""
    return service.routes_view()


@app.get("/tracking/{shipment_id}")
def tracking(shipment_id: str) -> dict[str, Any]:
    """The tracking timeline for one shipment."""
    result = service.tracking_view(shipment_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error", "not found"))
    return result


@app.get("/sla")
def sla() -> dict[str, Any]:
    """Confirmed SLA breaches, and the shipments heading for one."""
    return service.sla_view()


@app.get("/fraud")
def fraud() -> dict[str, Any]:
    """Risk decisions, planted-fraud recall, and courier-side findings."""
    return service.fraud_view()


@app.get("/cod")
def cod() -> dict[str, Any]:
    """Cash-on-delivery collections and the remittance cycle."""
    return service.cod_view()


@app.get("/assumptions")
def assumptions() -> dict[str, Any]:
    """Every business assumption, labelled published / estimated / design."""
    return service.assumptions()


@app.get("/decisions")
def decisions(kind: str | None = Query(default=None, min_length=2, max_length=64)) -> dict[str, Any]:
    """The audit ledger of decisions."""
    if kind is None:
        rows = [d.as_dict() for d in service.ledger.decisions]
    else:
        rows = [d.as_dict() for d in service.ledger.by_kind(kind)]

    return {
        "count": len(rows),
        "summary": service.ledger.summary(),
        "decisions": rows[:500],
    }


@app.post("/ledger/export")
def export_ledger() -> dict[str, Any]:
    """Write the audit ledger to a JSONL file and report where it went."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = write_ledger(service.ledger, REPORTS_DIR / "decisions.jsonl")
    return {
        "ok": True,
        "path": str(path),
        "decisions": len(service.ledger.decisions),
    }
