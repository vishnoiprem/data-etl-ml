"""The agent service — the composition root.

Everything the API and the demo need is wired together here: the corpus, the
retriever, the quote agent, the router, the audit ledger and the value
report. The API module and the demo script both go through this object, so
they cannot drift apart.

The service is constructed once and reused. Building the dense index is the
expensive part, so it is done lazily on the first search rather than at
import time.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from .audit import AuditLog
from .config import Settings
from .corpus import Document, build_corpus, corpus_summary
from .explain import explain_recommendation
from .llm import LLMRouter, get_default_router
from .quote_agent import recommend
from .quotes import QuoteError, parse_quotes
from .retrieval import Filters, HybridRetriever
from .supplier_discovery import coverage_gaps, sourcing_plan
from .value import ValueReport, build_value_report, summarise_reports


@dataclass
class SourcingService:
    """Everything, wired together."""

    settings: Settings
    documents: list[Document]
    retriever: HybridRetriever
    router: LLMRouter
    audit: AuditLog

    # -- construction ------------------------------------------------------ #

    @classmethod
    def create(
        cls,
        settings: Settings | None = None,
        *,
        router: LLMRouter | None = None,
        audit: AuditLog | None = None,
    ) -> SourcingService:
        settings = settings or Settings.from_env()
        documents = build_corpus()
        retriever = HybridRetriever(documents, use_dense=settings.use_dense)
        return cls(
            settings=settings,
            documents=documents,
            retriever=retriever,
            router=router or get_default_router(),
            audit=audit or AuditLog(),
        )

    # -- health ------------------------------------------------------------ #

    def health(self) -> dict[str, Any]:
        summary = corpus_summary(self.documents)
        return {
            "status": "ok",
            "documents": summary["total_documents"],
            "documents_by_type": summary["by_type"],
            "source_paths": summary["source_paths"],
            "dense_enabled": self.retriever.dense_enabled,
            "dense_reason": self.retriever.dense_reason,
            "router": getattr(self.router, "name", type(self.router).__name__),
            "llm_provider_env": self.settings.llm_provider,
            "audit_log": str(self.audit.path),
        }

    # -- retrieval --------------------------------------------------------- #

    def search(
        self,
        query: str,
        *,
        top_k: int | None = None,
        filters: Filters | None = None,
    ) -> dict[str, Any]:
        result = self.retriever.search(
            query,
            top_k=top_k or self.settings.top_k,
            filters=filters,
        )
        return {
            "query": result["query"],
            "dense_enabled": result["dense_enabled"],
            "dense_reason": result["dense_reason"],
            "filters_applied": result["filters_applied"],
            "stages": result["stages"],
            "total_latency_ms": result["total_latency_ms"],
            "hits": [hit.to_dict() for hit in result["hits"]],
        }

    def suppliers(
        self, *, dest_country: str | None = None, max_lead_time_days: int | None = None
    ) -> list[dict[str, Any]]:
        """The verified supplier pool, ranked by composite score."""
        docs = [d for d in self.documents if d.doc_type == "supplier"]
        docs.sort(key=lambda d: -d.metadata.get("composite_score", 0.0))
        results = []
        for doc in docs:
            meta = doc.metadata
            if max_lead_time_days is not None:
                if meta.get("lead_time_days", 0) > max_lead_time_days:
                    continue
            results.append(
                {
                    "alibaba_id": meta["alibaba_id"],
                    "name": meta["name"],
                    "city": meta["city"],
                    "composite_score": meta["composite_score"],
                    "authenticity_score": meta["authenticity_score"],
                    "price_score": meta["price_score"],
                    "reliability_score": meta["reliability_score"],
                    "risk_level": meta["risk_level"],
                    "flags": meta["flags"],
                    "fob_price_usd_500u": meta["fob_price_usd_500u"],
                    "fob_price_usd_1000u": meta["fob_price_usd_1000u"],
                    "lead_time_days": meta["lead_time_days"],
                    "min_order_qty": meta["min_order_qty"],
                    "response_rate": meta["response_rate"],
                    "has_ce_rohs": meta["has_ce_rohs"],
                    "source_path": doc.source_path,
                }
            )
        return results

    # -- sourcing ---------------------------------------------------------- #

    def find_suppliers(
        self,
        product: str,
        *,
        dest_country: str = "IN",
        order_units: int | None = None,
    ) -> dict[str, Any]:
        """The plan for sourcing one product: search strategy, RFQ, economics.

        The verified supplier pool covers only the smart-watch line, so for
        most viable products this returns an RFQ to send rather than a list
        of ready suppliers.
        """
        return sourcing_plan(
            product,
            dest_country=dest_country,
            order_units=order_units or self.settings.value.default_order_units,
        )

    def supplier_coverage(
        self,
        *,
        dest_country: str = "IN",
        min_margin_pct: float | None = None,
    ) -> dict[str, Any]:
        """Which viable products have a verified supplier, and which do not."""
        gaps = coverage_gaps(
            dest_country=dest_country,
            order_units=self.settings.value.default_order_units,
            min_margin_pct=(
                min_margin_pct
                if min_margin_pct is not None
                else self.settings.value.min_margin_pct
            ),
        )
        return {
            "dest_country": dest_country,
            "total_viable": len(gaps),
            "covered": [g.to_dict() for g in gaps if not g.needs_sourcing],
            "needs_sourcing": [g.to_dict() for g in gaps if g.needs_sourcing],
            "coverage_pct": (
                round(
                    100.0 * sum(1 for g in gaps if not g.needs_sourcing) / len(gaps), 1
                )
                if gaps
                else 0.0
            ),
        }

    # -- decisions --------------------------------------------------------- #

    def compare_quotes(
        self,
        quote_payloads: Sequence[dict[str, Any]],
        *,
        min_margin_pct: float | None = None,
        deadline_days: int | None = None,
        status_quo_alibaba_id: str | None = None,
        record: bool = True,
    ) -> dict[str, Any]:
        """Compare quotes, recommend a supplier, and record the decision."""
        started = time.perf_counter()
        margin_floor = (
            min_margin_pct
            if min_margin_pct is not None
            else self.settings.value.min_margin_pct
        )

        try:
            parsed = parse_quotes(list(quote_payloads))
        except QuoteError as exc:
            return {
                "ok": False,
                "error": "invalid_quote",
                "detail": str(exc),
                "evaluations": [],
                "recommended": None,
            }

        recommendation = recommend(
            parsed, min_margin_pct=margin_floor, deadline_days=deadline_days
        )
        explanation = explain_recommendation(recommendation, router=self.router)

        elapsed = time.perf_counter() - started
        report = build_value_report(
            recommendation,
            config=self.settings.value,
            tokens_used=0,
            agent_seconds=elapsed,
            status_quo_alibaba_id=status_quo_alibaba_id,
        )

        decision_id = None
        if record:
            decision_id = self.audit.emit(
                "quote_decision",
                {
                    "product": recommendation.product,
                    "dest_country": recommendation.dest_country,
                    "order_units": recommendation.order_units,
                    "recommended": recommendation.recommended.to_dict()
                    if recommendation.recommended
                    else None,
                    "evaluations": [e.to_dict() for e in recommendation.evaluations],
                    "rationale": recommendation.rationale,
                    "conflicts": recommendation.conflicts,
                    "confidence": recommendation.confidence,
                    "explanation": explanation["explanation"],
                    "router": explanation["router"],
                    "value": report.to_dict(),
                },
            )

        return {
            "ok": True,
            "decision_id": decision_id,
            "product": recommendation.product,
            "dest_country": recommendation.dest_country,
            "order_units": recommendation.order_units,
            "recommended": (
                recommendation.recommended.to_dict() if recommendation.recommended else None
            ),
            "evaluations": [e.to_dict() for e in recommendation.evaluations],
            "rationale": recommendation.rationale,
            "conflicts": recommendation.conflicts,
            "confidence": recommendation.confidence,
            "explanation": explanation["explanation"],
            "router": explanation["router"],
            "stages": recommendation.stages,
            "total_latency_ms": round(elapsed * 1000, 3),
            "value": report.to_dict(),
        }

    # -- value ------------------------------------------------------------- #

    def value_report(
        self,
        quote_payloads: Sequence[dict[str, Any]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Run a decision and return only the value view of it."""
        result = self.compare_quotes(quote_payloads, **kwargs)
        return {
            "decision_id": result.get("decision_id"),
            "ok": result.get("ok"),
            "value": result.get("value"),
        }

    def decision_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Recent decisions from the audit ledger."""
        return [event.to_dict() for event in self.audit.recent(limit=limit)]

    def summarise_history(self) -> dict[str, Any]:
        """Aggregate the recorded decisions into one number set."""
        events = self.audit.recent(limit=10_000, event_type="quote_decision")
        reports: list[ValueReport] = []
        for event in events:
            payload = event.payload.get("value")
            if not payload:
                continue
            reports.append(_report_from_dict(payload))
        return summarise_reports(reports)


def _report_from_dict(payload: dict[str, Any]) -> ValueReport:
    """Rebuild a ValueReport from its serialised form."""
    from .value import DecisionCost

    cost = payload.get("cost", {})
    return ValueReport(
        product=payload.get("product", ""),
        dest_country=payload.get("dest_country", ""),
        order_units=payload.get("order_units", 0),
        cost=DecisionCost(
            compute_seconds=cost.get("compute_seconds", 0.0),
            compute_cost_usd=cost.get("compute_cost_usd", 0.0),
            model_cost_usd=cost.get("model_cost_usd", 0.0),
            total_cost_usd=cost.get("total_cost_usd", 0.0),
        ),
        agent_seconds=payload.get("agent_seconds", 0.0),
        manual_minutes=payload.get("manual_minutes", 0.0),
        manual_cost_usd=payload.get("manual_cost_usd", 0.0),
        time_saved_minutes=payload.get("time_saved_minutes", 0.0),
        time_saved_cost_usd=payload.get("time_saved_cost_usd", 0.0),
        recommended_supplier=payload.get("recommended_supplier"),
        recommended_margin_usd=payload.get("recommended_margin_usd", 0.0),
        naive_margin_usd=payload.get("naive_margin_usd", 0.0),
        status_quo_margin_usd=payload.get("status_quo_margin_usd", 0.0),
        margin_captured_vs_naive_usd=payload.get("margin_captured_vs_naive_usd", 0.0),
        margin_captured_vs_status_quo_usd=payload.get(
            "margin_captured_vs_status_quo_usd", 0.0
        ),
        payback_decisions=payload.get("payback_decisions"),
        scenarios=payload.get("scenarios", []),
        assumptions=payload.get("assumptions", {}),
    )
