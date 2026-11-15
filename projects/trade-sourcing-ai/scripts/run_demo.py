#!/usr/bin/env python3
"""Run the trade-sourcing agent end to end, offline, with no API key.

The demo tells the whole story in one pass:

1. What is in the corpus, and where did it come from.
2. A retrieval query, showing BM25 + dense and the per-stage timings.
3. The sourcing gap — which viable routes have a verified supplier, and
   which ones have to be sourced from scratch.
4. The sourcing plan — the Alibaba search and the RFQ to send for one
   product, with the target price the margin model can support.
5. A real decision — three quotes in, one supplier out, with the rationale.
6. The business case — what the decision cost and what it captured.
7. The rejection case — quotes that must be turned down, and why.

Run it with ``make demo``. Add ``--report-only`` to just write the value
report to ``reports/``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(
    0, str(PROJECT_ROOT.parent / "realtime-stock-pipeline" / "trade-finder")
)

from trade_sourcing_ai.audit import AuditLog  # noqa: E402
from trade_sourcing_ai.service import SourcingService  # noqa: E402


def rule(title: str = "") -> None:
    if title:
        print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")
    else:
        print("=" * 78)


def demo(service: SourcingService) -> dict:
    quotes = json.loads(
        (PROJECT_ROOT / "data" / "quotes.json").read_text(encoding="utf-8")
    )["quotes"]

    # -- 1. the corpus ---------------------------------------------------- #
    rule("1. THE CORPUS — every document traces back to a file in this repo")
    health = service.health()
    print(f"Documents: {health['documents']}")
    for doc_type, count in health["documents_by_type"].items():
        print(f"  {doc_type:<12} {count}")
    print("\nSource files:")
    for path in health["source_paths"]:
        print(f"  {path}")
    print(f"\nDense retrieval: {health['dense_enabled']}"
          + (f"  ({health['dense_reason']})" if health["dense_reason"] else ""))
    print(f"LLM router:      {health['router']}")

    # -- 2. retrieval ----------------------------------------------------- #
    rule("2. RETRIEVAL — BM25 + dense, fused with reciprocal rank fusion")
    result = service.search("supplier with CE RoHS and a fast lead time", top_k=5)
    print(f"Query: {result['query']}\n")
    for hit in result["hits"]:
        print(f"  {hit['rank']}. [{hit['doc_type']}] {hit['title']}")
        print(f"     source: {hit['source_path']}:{hit['source_line']}")
        print(
            f"     lexical_rank={hit['lexical_rank']} dense_rank={hit['dense_rank']} "
            f"score={hit['score']:.5f}"
        )
    print("\nStage timings:")
    for stage in result["stages"]:
        print(f"  {stage['name']:<8} {stage['latency_ms']:>8.3f} ms  {stage['status']}")

    # -- 3. the sourcing gap ---------------------------------------------- #
    rule("3. THE SOURCING GAP — where the verified pool does not reach")
    coverage = service.supplier_coverage(dest_country="IN")
    print(f"Viable CN→IN routes: {coverage['total_viable']}")
    print(f"Covered by a verified supplier: {len(coverage['covered'])} "
          f"({coverage['coverage_pct']}%)\n")
    print(f"{'product':26} {'margin':>7} {'demand':>6} {'sells on':>10}  suppliers")
    print("-" * 88)
    for gap in coverage["covered"] + coverage["needs_sourcing"]:
        who = (
            ", ".join(gap["verified_suppliers"])
            if gap["verified_suppliers"]
            else "— none, must be sourced —"
        )
        print(
            f"{gap['product']:26} {gap['margin_pct'] * 100:6.1f}% "
            f"{str(gap['demand_score']):>6} {gap['platform']:>10}  {who}"
        )

    # -- 4. the sourcing plan --------------------------------------------- #
    rule("4. THE SOURCING PLAN — an RFQ you can actually send")
    plan = service.find_suppliers("phone case silicone", dest_country="IN")
    strategy = plan["strategy"]
    economics = plan["economics"]
    print(f"Product: {plan['product']}  →  {plan['dest_country']}\n")
    print(f"Alibaba category: {strategy['alibaba_category_path']}")
    print(f"Search queries:   {', '.join(strategy['search_queries'])}")
    print(f"City cluster:     {', '.join(strategy['cities'])}")
    print(f"Filters:          {', '.join(strategy['filters'])}")
    print(f"MOQ band:         {strategy['moq_band']} (max {strategy['max_moq']} units)")
    print(f"\nTarget FOB:  ${economics['target_fob_usd']:.2f}")
    print(f"Max FOB:     ${economics['max_fob_usd']:.2f} "
          f"(above this the route dies)")
    print(f"Sells on:    {economics['platform']} "
          f"at ${economics['destination_price_usd']:.2f} retail")
    for warning in plan["warnings"]:
        print(f"\n  ⚠️  {warning}")
    print(f"\nRFQ subject: {plan['rfq']['subject']}")
    print("\n--- RFQ body ---")
    print(plan["rfq"]["body"])

    # -- 5. the decision -------------------------------------------------- #
    rule("5. THE DECISION — three quotes in, one supplier out")
    primary = [q for q in quotes if q["product"] == "phone case silicone"]
    decision = service.compare_quotes(
        primary, status_quo_alibaba_id="goldstar_2010"
    )
    print(f"Product: {decision['product']}  →  {decision['dest_country']}  "
          f"({decision['order_units']} units)\n")
    for evaluation in decision["evaluations"]:
        marker = "✗" if evaluation["disqualified"] else "✓"
        print(
            f"  {marker} {evaluation['supplier_name']:<38} "
            f"${evaluation['fob_usd']:.2f} FOB  "
            f"margin {evaluation['margin_pct'] * 100:>5.1f}%  "
            f"lead {evaluation['lead_time_days']:>2}d  "
            f"score {evaluation['score']:.3f}  risk {evaluation['risk_level']}"
        )
        for reason in evaluation["disqualification_reasons"]:
            print(f"      rejected: {reason}")

    recommended = decision["recommended"]
    if recommended:
        print(f"\n  → RECOMMENDED: {recommended['supplier_name']}")
        print(f"    confidence:  {decision['confidence']:.2f}")
    print("\nRationale:")
    for line in decision["rationale"]:
        print(f"  • {line}")
    print(f"\nNarrated by the {decision['router']} router:")
    print(f"  {decision['explanation']}")

    # -- 6. the business case --------------------------------------------- #
    rule("6. THE BUSINESS CASE — what the decision cost, what it captured")
    value = decision["value"]
    print(f"  Agent cost:            ${value['cost']['total_cost_usd']:.4f} "
          f"({value['agent_seconds'] * 1000:.1f} ms, "
          f"${value['cost']['model_cost_usd']:.2f} model spend)")
    print(f"  Manual baseline:       {value['manual_minutes']:.0f} min "
          f"= ${value['manual_cost_usd']:.2f}")
    print(f"  Time saved:            {value['time_saved_minutes']:.1f} min "
          f"= ${value['time_saved_cost_usd']:.2f}")
    print(f"  Margin (recommended):  ${value['recommended_margin_usd']:.2f}/unit")
    print(f"  Margin (cheapest):     ${value['naive_margin_usd']:.2f}/unit "
          f"(the naive 'pick the lowest price' strategy)")
    print(f"  Margin (status quo):   ${value['status_quo_margin_usd']:.2f}/unit "
          f"(the current shortlist's first pick)")
    print(f"  Captured vs status quo: ${value['margin_captured_vs_status_quo_usd']:.2f}/unit "
          f"= ${value['margin_captured_vs_status_quo_usd'] * decision['order_units']:.0f} on this order")
    print("\nScenarios:")
    for scenario in value["scenarios"]:
        print(f"  {scenario['name']:<12} ${scenario['margin_captured_usd']:>8.2f} captured")
        print(f"      {scenario['assumption']}")

    # -- 7. the rejection case -------------------------------------------- #
    rule("7. THE REJECTION CASE — quotes that must be turned down")
    unviable = [q for q in quotes if q["product"] == "compression socks"]
    rejected = service.compare_quotes(unviable)
    if rejected["recommended"] is None:
        print("No supplier recommended — correctly.")
        print(f"Confidence: {rejected['confidence']:.2f}\n")
        for line in rejected["rationale"]:
            print(f"  • {line}")
    else:
        print(f"UNEXPECTED: recommended {rejected['recommended']['supplier_name']}")

    rule()
    print(f"Decision id: {decision['decision_id']}")
    print(f"Audit ledger: {service.audit.path}")
    return decision


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Only write the value report to reports/, without the walkthrough.",
    )
    parser.add_argument(
        "--no-dense",
        action="store_true",
        help="Skip dense retrieval (avoids downloading an embedding model).",
    )
    args = parser.parse_args(argv)

    from trade_sourcing_ai.config import Settings

    settings = Settings.from_env()
    if args.no_dense:
        settings = Settings(
            llm_provider=settings.llm_provider,
            ollama_model=settings.ollama_model,
            ollama_host=settings.ollama_host,
            use_dense=False,
            top_k=settings.top_k,
            value=settings.value,
        )

    # A demo-local audit log, so running the demo does not pollute the
    # decision history that the API reports on.
    service = SourcingService.create(
        settings=settings, audit=AuditLog(PROJECT_ROOT / "reports" / "audit" / "demo.jsonl")
    )

    decision = demo(service)

    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    output = reports_dir / "value_report.json"
    output.write_text(
        json.dumps(
            {
                "decision_id": decision["decision_id"],
                "recommended": decision["recommended"],
                "value": decision["value"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Value report written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
