"""FastAPI app for the trade-sourcing agent.

Six endpoints, built around the three questions a sourcing operator actually
asks: *what can source this?*, *which supplier should I buy from?*, and *was
that worth it?*

The service is built once at import time. The corpus is cheap to build; the
dense index is not, so it is built lazily on the first search.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from src.trade_sourcing_ai.retrieval import Filters
from src.trade_sourcing_ai.service import SourcingService

app = FastAPI(
    title="Trade-Sourcing AI",
    version="0.1.0",
    description=(
        "A sourcing agent over the trade-finder dataset. Retrieves over the "
        "real product and supplier corpus, compares incoming quotes against "
        "the real margin model, and recommends one supplier with an auditable "
        "rationale and a cost-per-decision number."
    ),
)

service = SourcingService.create()


# --------------------------------------------------------------------------- #
# Request models
# --------------------------------------------------------------------------- #


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=50)
    dest_country: str | None = Field(default=None, description="e.g. IN, UK, US")
    category: str | None = None
    min_margin: float | None = Field(default=None, ge=0.0, le=1.0)
    max_lead_time_days: int | None = Field(default=None, ge=1, le=365)


class QuoteRequest(BaseModel):
    quotes: list[dict[str, Any]] = Field(..., min_length=1)
    min_margin_pct: float | None = Field(default=None, ge=0.0, le=1.0)
    deadline_days: int | None = Field(
        default=None, ge=1, le=365, description="Days until the goods must arrive."
    )
    status_quo_alibaba_id: str | None = Field(
        default=None,
        description="The supplier the current shortlist ranks first, for comparison.",
    )


class FindSuppliersRequest(BaseModel):
    product: str = Field(..., min_length=2, max_length=200)
    dest_country: str = Field(default="IN", min_length=2, max_length=2)
    order_units: int = Field(default=500, ge=1, le=100000)


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #


@app.get("/health")
def health() -> dict[str, Any]:
    """Service status, corpus size, and which retrieval paths are live."""
    return service.health()


@app.get("/suppliers")
def suppliers(
    max_lead_time_days: int | None = Query(default=None, ge=1, le=365),
) -> dict[str, Any]:
    """The verified supplier pool, ranked by composite score."""
    return {
        "suppliers": service.suppliers(max_lead_time_days=max_lead_time_days),
        "count": len(service.suppliers(max_lead_time_days=max_lead_time_days)),
    }


@app.post("/search")
def search(request: SearchRequest) -> dict[str, Any]:
    """Hybrid BM25 + dense retrieval over products, suppliers and reputation."""
    filters = Filters(
        dest_country=request.dest_country,
        category=request.category,
        min_margin=request.min_margin,
        max_lead_time_days=request.max_lead_time_days,
    )
    return service.search(request.query, top_k=request.top_k, filters=filters)


@app.post("/suppliers/find")
def find_suppliers(request: FindSuppliersRequest) -> dict[str, Any]:
    """The sourcing plan for one product: search strategy, RFQ, economics.

    Returns the RFQ email to send, the Alibaba search that finds
    candidates, and the target price the margin model can support.
    """
    result = service.find_suppliers(
        request.product,
        dest_country=request.dest_country,
        order_units=request.order_units,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@app.get("/suppliers/coverage")
def supplier_coverage(
    dest_country: str = Query(default="IN", min_length=2, max_length=2),
) -> dict[str, Any]:
    """Which viable routes have a verified supplier, and which need sourcing."""
    return service.supplier_coverage(dest_country=dest_country)


@app.post("/quotes/compare")
def compare_quotes(request: QuoteRequest) -> dict[str, Any]:
    """Compare supplier quotes and recommend one.

    The recommendation is computed in Python against the trade-finder margin
    model. The LLM only narrates it.
    """
    result = service.compare_quotes(
        request.quotes,
        min_margin_pct=request.min_margin_pct,
        deadline_days=request.deadline_days,
        status_quo_alibaba_id=request.status_quo_alibaba_id,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("detail", "invalid quote"))
    return result


@app.post("/value/report")
def value_report(request: QuoteRequest) -> dict[str, Any]:
    """Run a decision and return only the business view of it."""
    result = service.compare_quotes(
        request.quotes,
        min_margin_pct=request.min_margin_pct,
        deadline_days=request.deadline_days,
        status_quo_alibaba_id=request.status_quo_alibaba_id,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("detail", "invalid quote"))
    return {
        "decision_id": result.get("decision_id"),
        "value": result.get("value"),
        "recommended": result.get("recommended"),
    }


@app.get("/decisions")
def decisions(limit: int = Query(default=50, ge=1, le=500)) -> dict[str, Any]:
    """The decision ledger, newest last."""
    return {
        "decisions": service.decision_history(limit=limit),
        "summary": service.summarise_history(),
    }
