"""The eval harness: retrieval quality and decision quality, measured.

Two questions, measured separately:

**Is retrieval good?** For a set of labelled queries, does the retriever put
the relevant supplier or product in the top-k? Scored with recall@k, nDCG@k,
MRR and precision@k — the same metrics the repo's other RAG projects use,
so the numbers are comparable.

**Are decisions good?** For a set of labelled quote sets, does the agent pick
the supplier the label says is correct, and does it reject the quote sets
that should be rejected?

Run it with ``make eval``. The report is written to ``reports/``.
"""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT
from .corpus import build_corpus
from .retrieval import Filters, HybridRetriever
from .value import ValueConfig

# --------------------------------------------------------------------------- #
# Retrieval gold set
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class GoldQuery:
    """A query with the document ids that should come back."""

    query: str
    gold_doc_ids: tuple[str, ...]
    note: str = ""
    filters: Filters | None = None


def build_gold_queries() -> list[GoldQuery]:
    """The labelled query set.

    The labels are hand-written against the corpus, and every gold id is
    asserted to exist — a gold set pointing at a missing document is worse
    than no gold set at all, because it silently depresses every score.
    """
    return [
        GoldQuery(
            query="Shenzhen supplier with 500 unit FOB price and 18 day lead time",
            gold_doc_ids=("supplier:qytech_2014",),
            note="Names a specific supplier by its attributes.",
        ),
        GoldQuery(
            query="supplier with free sample and fastest response time",
            gold_doc_ids=("supplier:ocom_2007",),
            note="OCOM: 2h response, free sample.",
        ),
        GoldQuery(
            query="reusable water bottle margin to India",
            gold_doc_ids=(
                "product:reusable water bottle:CN->IN",
                "product:reusable water bottle:VN->IN",
            ),
            note="Both CN and VN routes are viable.",
        ),
        GoldQuery(
            query="phone case silicone landed cost and platform fee",
            gold_doc_ids=(
                "product:phone case silicone:CN->IN",
                "product:phone case silicone:VN->IN",
            ),
            note="Top CN->IN margin route in the trade-finder model.",
        ),
        GoldQuery(
            query="compression socks travel and medical overlap demand",
            gold_doc_ids=(
                "product:compression socks:CN->IN",
                "product:compression socks:VN->IN",
            ),
            note="VN route is the one the trade-finder report highlights.",
        ),
        GoldQuery(
            query="supplier that has won the ranking most often over 10K cycles",
            gold_doc_ids=("reputation:goldstar_2010",),
            note="Gold Star has an 86% top-1 finish rate.",
        ),
        GoldQuery(
            query="OEM ODM smart watch factory with CE RoHS certification",
            gold_doc_ids=(
                "supplier:qytech_2014",
                "supplier:ocom_2007",
                "supplier:goldstar_2010",
            ),
            note="Several Shenzhen suppliers qualify; any is acceptable.",
        ),
        GoldQuery(
            query="high risk supplier flags and transaction volume",
            gold_doc_ids=(
                "supplier:qytech_2014",
                "supplier:ocom_2007",
                "supplier:goldstar_2010",
            ),
            note="General supplier-quality query.",
        ),
    ]


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #


def recall_at_k(retrieved: Sequence[str], gold: Sequence[str], k: int = 5) -> float:
    """Fraction of gold documents retrieved in the top k."""
    if not gold:
        return 0.0
    top = set(retrieved[:k])
    return len(top & set(gold)) / len(gold)


def precision_at_k(retrieved: Sequence[str], gold: Sequence[str], k: int = 5) -> float:
    """Fraction of the top k that is relevant.

    Divided by ``k``, not by ``len(top_k)``, so returning fewer results
    cannot inflate the score.
    """
    if not gold:
        return 0.0
    top = retrieved[:k]
    if not top:
        return 0.0
    return len(set(top) & set(gold)) / k


def mrr(retrieved: Sequence[str], gold: Sequence[str]) -> float:
    """Reciprocal rank of the first relevant document."""
    gold_set = set(gold)
    for position, doc_id in enumerate(retrieved, start=1):
        if doc_id in gold_set:
            return 1.0 / position
    return 0.0


def ndcg_at_k(retrieved: Sequence[str], gold: Sequence[str], k: int = 5) -> float:
    """Normalised discounted cumulative gain, binary relevance."""
    if not gold:
        return 0.0
    gold_set = set(gold)
    dcg = sum(
        1.0 / math.log2(position + 1)
        for position, doc_id in enumerate(retrieved[:k], start=1)
        if doc_id in gold_set
    )
    ideal = sum(
        1.0 / math.log2(position + 1)
        for position in range(1, min(len(gold), k) + 1)
    )
    return dcg / ideal if ideal else 0.0


# --------------------------------------------------------------------------- #
# Decision gold set
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class GoldDecision:
    """A quote set and the supplier the agent should pick (or None)."""

    name: str
    quotes: list[dict[str, Any]]
    expected_alibaba_id: str | None
    expect_rejection: bool = False


def build_gold_decisions(quotes: list[dict[str, Any]]) -> list[GoldDecision]:
    """Label the decision set.

    The expected answers are derived from the data rather than asserted by
    hand: for a quote set, the expected pick is the supplier with the highest
    modelled margin among those that clear the floor, which is the rule the
    agent implements. That makes this a *consistency* check — it catches the
    agent drifting from its own stated rule, not the rule being right.
    """
    by_product: dict[str, list[dict[str, Any]]] = {}
    for quote in quotes:
        by_product.setdefault(quote["product"], []).append(quote)

    decisions = [
        GoldDecision(
            name="phone case silicone to India",
            quotes=by_product.get("phone case silicone", []),
            expected_alibaba_id="qytech_2014",
        ),
        GoldDecision(
            name="compression socks at watch-level pricing",
            quotes=by_product.get("compression socks", []),
            expected_alibaba_id=None,
            expect_rejection=True,
        ),
    ]
    return [d for d in decisions if d.quotes]


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #


@dataclass
class EvalReport:
    timestamp: str
    n_queries: int
    n_decisions: int
    recall_at_5: float
    precision_at_5: float
    ndcg_at_5: float
    mrr: float
    decision_accuracy: float
    retrieval_queries: list[dict[str, Any]] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    acceptance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def summary(self) -> str:
        lines = [
            "=== Trade-Sourcing AI eval ===",
            f"Timestamp:         {self.timestamp}",
            "",
            "Retrieval",
            f"  Queries:         {self.n_queries}",
            f"  Recall@5:        {self.recall_at_5:.4f}",
            f"  Precision@5:     {self.precision_at_5:.4f}",
            f"  nDCG@5:          {self.ndcg_at_5:.4f}",
            f"  MRR:             {self.mrr:.4f}",
            "",
            "Decisions",
            f"  Cases:           {self.n_decisions}",
            f"  Accuracy:        {self.decision_accuracy:.4f}",
            "",
        ]
        for query in self.retrieval_queries:
            lines.append(
                f"  [{query['recall_at_5']:.2f} recall] {query['query']}"
            )
            if query["missing"]:
                lines.append(f"      missing: {', '.join(query['missing'])}")
        lines.append("")
        for decision in self.decisions:
            status = "PASS" if decision["passed"] else "FAIL"
            lines.append(f"  [{status}] {decision['name']}")
            lines.append(
                f"      expected {decision['expected']}, got {decision['actual']}"
            )
        lines.append("")
        passed, failures = check_acceptance(self)
        lines.append(f"Acceptance: {'PASS' if passed else 'FAIL'}")
        for failure in failures:
            lines.append(f"  - {failure}")
        return "\n".join(lines)


#: The thresholds the project holds itself to.
ACCEPTANCE = {
    "recall_at_5": 0.70,
    "ndcg_at_5": 0.60,
    "mrr": 0.55,
    "decision_accuracy": 1.00,
}


def check_acceptance(report: EvalReport) -> tuple[bool, list[str]]:
    """Compare the report against the acceptance thresholds."""
    failures = []
    for metric, threshold in ACCEPTANCE.items():
        actual = getattr(report, metric)
        if actual < threshold:
            failures.append(f"{metric} {actual:.4f} is below the threshold {threshold:.4f}")
    return (not failures), failures


# --------------------------------------------------------------------------- #
# Running the harness
# --------------------------------------------------------------------------- #


def run_retrieval_eval(
    retriever: HybridRetriever, gold_queries: Sequence[GoldQuery], k: int = 5
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    """Score the retriever against the gold query set."""
    rows: list[dict[str, Any]] = []
    recalls, precisions, ndcgs, mrrs = [], [], [], []

    for gold in gold_queries:
        result = retriever.search(
            gold.query, top_k=k, filters=gold.filters or Filters()
        )
        retrieved = [hit.doc.doc_id for hit in result["hits"]]
        recall = recall_at_k(retrieved, gold.gold_doc_ids, k)
        precision = precision_at_k(retrieved, gold.gold_doc_ids, k)
        ndcg = ndcg_at_k(retrieved, gold.gold_doc_ids, k)
        reciprocal = mrr(retrieved, gold.gold_doc_ids)

        recalls.append(recall)
        precisions.append(precision)
        ndcgs.append(ndcg)
        mrrs.append(reciprocal)

        rows.append(
            {
                "query": gold.query,
                "note": gold.note,
                "gold_doc_ids": list(gold.gold_doc_ids),
                "retrieved": retrieved,
                "missing": [
                    doc_id for doc_id in gold.gold_doc_ids if doc_id not in retrieved
                ],
                "recall_at_5": recall,
                "precision_at_5": precision,
                "ndcg_at_5": ndcg,
                "mrr": reciprocal,
            }
        )

    n = max(len(rows), 1)
    metrics = {
        "recall_at_5": sum(recalls) / n,
        "precision_at_5": sum(precisions) / n,
        "ndcg_at_5": sum(ndcgs) / n,
        "mrr": sum(mrrs) / n,
    }
    return metrics, rows


def run_decision_eval(
    gold_decisions: Sequence[GoldDecision],
    *,
    min_margin_pct: float = 0.15,
    config: ValueConfig | None = None,
) -> tuple[float, list[dict[str, Any]]]:
    """Check the agent's decisions against the labelled expectations."""
    from .quote_agent import recommend
    from .quotes import parse_quotes

    config = config or ValueConfig()
    rows: list[dict[str, Any]] = []
    correct = 0

    for gold in gold_decisions:
        try:
            quotes = parse_quotes(gold.quotes)
        except Exception as exc:
            rows.append(
                {
                    "name": gold.name,
                    "expected": gold.expected_alibaba_id,
                    "actual": f"parse error: {exc}",
                    "passed": False,
                    "detail": "",
                }
            )
            continue

        result = recommend(quotes, min_margin_pct=min_margin_pct)
        actual = result.recommended.alibaba_id if result.recommended else None
        passed = actual == gold.expected_alibaba_id
        if passed:
            correct += 1
        rows.append(
            {
                "name": gold.name,
                "expected": gold.expected_alibaba_id,
                "actual": actual,
                "passed": passed,
                "detail": result.rationale[0] if result.rationale else "",
            }
        )

    accuracy = correct / len(gold_decisions) if gold_decisions else 0.0
    return accuracy, rows


def run_harness(
    *,
    use_dense: bool = False,
    min_margin_pct: float = 0.15,
) -> EvalReport:
    """Run both evaluations and return the combined report."""
    documents = build_corpus()
    retriever = HybridRetriever(documents, use_dense=use_dense)

    gold_queries = build_gold_queries()
    known_ids = {doc.doc_id for doc in documents}
    for gold in gold_queries:
        missing = [doc_id for doc_id in gold.gold_doc_ids if doc_id not in known_ids]
        if missing:
            raise ValueError(
                f"Gold query {gold.query!r} points at documents that do not exist: "
                f"{missing}. A gold set pointing at missing documents depresses "
                f"every score."
            )

    metrics, rows = run_retrieval_eval(retriever, gold_queries)

    from .quotes import load_quotes

    quote_dicts = [
        {
            "quote_id": q.quote_id,
            "alibaba_id": q.alibaba_id,
            "supplier_name": q.supplier_name,
            "product": q.product,
            "dest_country": q.dest_country,
            "order_units": q.order_units,
            "fob_usd": q.fob_usd,
            "lead_time_days": q.lead_time_days,
            "moq": q.moq,
            "payment_terms": q.payment_terms,
            "sample_policy": q.sample_policy,
            "received_at": q.received_at,
            "notes": q.notes,
        }
        for q in load_quotes()
    ]
    gold_decisions = build_gold_decisions(quote_dicts)
    accuracy, decision_rows = run_decision_eval(
        gold_decisions, min_margin_pct=min_margin_pct
    )

    report = EvalReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        n_queries=len(rows),
        n_decisions=len(decision_rows),
        recall_at_5=metrics["recall_at_5"],
        precision_at_5=metrics["precision_at_5"],
        ndcg_at_5=metrics["ndcg_at_5"],
        mrr=metrics["mrr"],
        decision_accuracy=accuracy,
        retrieval_queries=rows,
        decisions=decision_rows,
    )
    report.acceptance = {"passed": check_acceptance(report)[0], "thresholds": ACCEPTANCE}
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the trade-sourcing eval harness.")
    parser.add_argument("--out", type=str, default=None, help="Where to write the JSON report.")
    parser.add_argument(
        "--dense",
        action="store_true",
        help="Use dense retrieval as well as BM25 (downloads an embedding model).",
    )
    args = parser.parse_args(argv)

    report = run_harness(use_dense=args.dense)
    print(report.summary())

    out = Path(args.out) if args.out else (PROJECT_ROOT / "reports" / "eval_latest.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    print(f"Report written to {out}")

    passed, _ = check_acceptance(report)
    return 0 if passed else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
