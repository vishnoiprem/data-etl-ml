"""Turn a structured recommendation into prose — and only prose.

The decision is already made by the time this module runs. The router is
handed the *facts* and asked to narrate them. If the model invents a
supplier or a margin, the structured rationale right next to it in the
response is still the source of truth, and the audit ledger records both.
"""

from __future__ import annotations

import time
from typing import Any

from .llm import LLMRouter, StubRouter
from .quote_agent import Recommendation

SYSTEM_PROMPT = (
    "You are a sourcing analyst for a cross-border trading business. "
    "Explain the recommended supplier choice to the operator in two or three "
    "sentences. State only facts that appear in the prompt. Do not invent "
    "prices, suppliers, dates or risks. If there are conflicts, say so plainly."
)


def build_prompt(recommendation: Recommendation) -> str:
    """Render the recommendation as a labelled prompt.

    The labels matter: the stub router parses them back out, which is how
    the offline mode stays specific instead of generic.
    """
    recommended = recommendation.recommended
    if recommended is None:
        lines = [
            "Supplier: none",
            "Margin: n/a",
            "Score: n/a",
            "Conflicts: no quote cleared the margin, risk and lead-time bar",
        ]
        for evaluation in recommendation.evaluations:
            if evaluation.disqualification_reasons:
                lines.append(
                    f"Rejected: {evaluation.quote.supplier_name} — "
                    f"{evaluation.disqualification_reasons[0]}"
                )
        return "\n".join(lines)

    lines = [
        f"Supplier: {recommended.quote.supplier_name} ({recommended.quote.alibaba_id})",
        f"Margin: {recommended.margin_pct * 100:.1f}% "
        f"(${recommended.margin_usd:.2f} per unit, "
        f"${recommended.margin_at_order_usd:,.0f} on this order)",
        f"Score: {recommended.composite_score}/10, risk level {recommended.risk_level}, "
        f"lead time {recommended.quote.lead_time_days} days",
        f"Price: ${recommended.quote.fob_usd:.2f} FOB for "
        f"{recommended.quote.order_units} units",
        f"Landed cost: ${recommended.landed_cost_usd:.2f} against a "
        f"${recommended.dest_price_usd:.2f} destination price",
        f"Conflicts: {'; '.join(recommendation.conflicts) if recommendation.conflicts else 'none'}",
    ]

    runner_up = next(
        (e for e in recommendation.evaluations if e is not recommended and not e.disqualified),
        None,
    )
    if runner_up:
        lines.append(
            f"Runner up: {runner_up.quote.supplier_name} at "
            f"${runner_up.quote.fob_usd:.2f} FOB, margin "
            f"{runner_up.margin_pct * 100:.1f}%, score {runner_up.score}"
        )

    for evaluation in recommendation.evaluations:
        if evaluation is recommended:
            continue
        if evaluation.disqualified and evaluation.disqualification_reasons:
            lines.append(
                f"Rejected: {evaluation.quote.supplier_name} — "
                f"{evaluation.disqualification_reasons[0]}"
            )

    return "\n".join(lines)


def explain_recommendation(
    recommendation: Recommendation, router: LLMRouter | None = None
) -> dict[str, Any]:
    """Ask the router to narrate the decision.

    Returns the explanation plus the latency and which router produced it.
    A router failure never loses the decision — the structured rationale is
    still returned, and the error is reported alongside it.
    """
    active = router or StubRouter()
    prompt = build_prompt(recommendation)

    started = time.perf_counter()
    try:
        explanation = active.complete(prompt, system=SYSTEM_PROMPT, max_tokens=400)
        error = None
    except Exception as exc:
        explanation = " ".join(recommendation.rationale)
        error = f"{type(exc).__name__}: {exc}"
    latency_ms = (time.perf_counter() - started) * 1000

    return {
        "explanation": explanation,
        "router": getattr(active, "name", type(active).__name__),
        "latency_ms": round(latency_ms, 3),
        "error": error,
        "prompt": prompt,
    }
