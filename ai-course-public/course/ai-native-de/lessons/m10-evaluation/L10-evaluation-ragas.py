"""
================================================================
M10 L10  --  Evaluation and RAGAS-style metrics
================================================================

Run:    python3 lessons/m10-evaluation/L10-evaluation-ragas.py
Keys:   none

Builds a tiny RAGAS-style evaluation harness:
  * Golden set: query + ground-truth answer + relevant doc ids
  * Three core RAGAS metrics: faithfulness, answer relevancy, context recall
  * LLM-judge (mock): scores the answer on each metric
  * Aggregate report: per-metric mean + std + per-query breakdown
  * Regression detector: compares current run to baseline

The lesson's point: "the model is good" is not a metric.
You need a golden set, a scoring rubric, and a baseline.
RAGAS gives you the rubric; the golden set is your job.
"""

from __future__ import annotations

import random
import re
import statistics
import time
from dataclasses import dataclass, field
from typing import Callable


# =================================================================
# CONFIG
# =================================================================

LESSON_NUMBER = "M10.L10"
SEED = 17
FAITHFULNESS_THRESHOLD = 0.7
ANSWER_RELEVANCY_THRESHOLD = 0.6
CONTEXT_RECALL_THRESHOLD = 0.7


# =================================================================
# SECTION 1  --  Golden set
# =================================================================

@dataclass(frozen=True)
class GoldenExample:
    """One query + ground-truth answer + relevant doc ids."""
    query: str
    ground_truth: str           # what the answer should contain
    relevant_doc_ids: list[str] # what the retrieval should return
    category: str = "general"     # for stratified reporting


@dataclass
class GoldenSet:
    examples: list[GoldenExample] = field(default_factory=list)

    def add(self, ex: GoldenExample) -> None:
        self.examples.append(ex)

    def by_category(self) -> dict[str, list[GoldenExample]]:
        out: dict[str, list[GoldenExample]] = {}
        for ex in self.examples:
            out.setdefault(ex.category, []).append(ex)
        return out

    def __len__(self) -> int:
        return len(self.examples)


# =================================================================
# SECTION 2  --  The three RAGAS metrics
# =================================================================

@dataclass
class RAGASScores:
    """The three RAGAS core metrics for one query."""
    faithfulness: float        # is the answer supported by the context?  [0, 1]
    answer_relevancy: float    # is the answer relevant to the query?     [0, 1]
    context_recall: float      # did retrieval find all relevant docs?    [0, 1]

    def mean(self) -> float:
        return (self.faithfulness + self.answer_relevancy + self.context_recall) / 3


# =================================================================
# SECTION 3  --  Mock LLM judge
# =================================================================

@dataclass
class MockJudge:
    """A mock LLM-as-judge that scores answers on the three RAGAS metrics."""
    judge_id: str = "mock-judge-1"

    def judge_faithfulness(self, answer: str, context: str) -> float:
        """Faithfulness = fraction of answer claims that are supported by the context.

        Heuristic: split answer into sentences, check if 50% of the words appear
        in the context.  A real judge would use an LLM.
        """
        if not answer or not context:
            return 0.0
        answer_words = set(re.findall(r"\w+", answer.lower()))
        context_words = set(re.findall(r"\w+", context.lower()))
        if not answer_words:
            return 0.0
        overlap = len(answer_words & context_words) / len(answer_words)
        return min(1.0, overlap * 1.5)  # boost; in reality LLM judges are stricter

    def judge_answer_relevancy(self, answer: str, query: str) -> float:
        """Answer relevancy = how well the answer addresses the query.

        Heuristic: fraction of query words that appear in the answer.
        """
        if not answer or not query:
            return 0.0
        q_words = set(re.findall(r"\w+", query.lower()))
        a_words = set(re.findall(r"\w+", answer.lower()))
        if not q_words:
            return 0.0
        return len(q_words & a_words) / len(q_words)

    def judge_context_recall(self, retrieved_ids: list[str], relevant_ids: list[str]) -> float:
        """Context recall = fraction of relevant docs in the retrieved set."""
        if not relevant_ids:
            return 1.0
        return len(set(retrieved_ids) & set(relevant_ids)) / len(relevant_ids)


# =================================================================
# SECTION 4  --  Evaluation run
# =================================================================

@dataclass
class EvalResult:
    """The result of evaluating one example."""
    query: str
    ground_truth: str
    answer: str
    retrieved_ids: list[str]
    relevant_ids: list[str]
    scores: RAGASScores
    category: str

    @property
    def passed(self) -> bool:
        return (
            self.scores.faithfulness >= FAITHFULNESS_THRESHOLD
            and self.scores.answer_relevancy >= ANSWER_RELEVANCY_THRESHOLD
            and self.scores.context_recall >= CONTEXT_RECALL_THRESHOLD
        )


@dataclass
class EvaluationReport:
    """Aggregated results across the golden set."""
    results: list[EvalResult] = field(default_factory=list)
    judge: MockJudge = field(default_factory=MockJudge)

    def add(self, r: EvalResult) -> None:
        self.results.append(r)

    def mean_scores(self) -> RAGASScores:
        if not self.results:
            return RAGASScores(0, 0, 0)
        return RAGASScores(
            faithfulness=statistics.mean(r.scores.faithfulness for r in self.results),
            answer_relevancy=statistics.mean(r.scores.answer_relevancy for r in self.results),
            context_recall=statistics.mean(r.scores.context_recall for r in self.results),
        )

    def std_scores(self) -> RAGASScores:
        if len(self.results) < 2:
            return RAGASScores(0, 0, 0)
        return RAGASScores(
            faithfulness=statistics.stdev(r.scores.faithfulness for r in self.results),
            answer_relevancy=statistics.stdev(r.scores.answer_relevancy for r in self.results),
            context_recall=statistics.stdev(r.scores.context_recall for r in self.results),
        )

    def pass_rate(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if r.passed) / len(self.results)

    def by_category(self) -> dict[str, RAGASScores]:
        out: dict[str, list[RAGASScores]] = {}
        for r in self.results:
            out.setdefault(r.category, []).append(r.scores)
        return {
            cat: RAGASScores(
                faithfulness=statistics.mean(s.faithfulness for s in scores),
                answer_relevancy=statistics.mean(s.answer_relevancy for s in scores),
                context_recall=statistics.mean(s.context_recall for s in scores),
            )
            for cat, scores in out.items()
        }


# =================================================================
# SECTION 5  --  Regression detector
# =================================================================

@dataclass
class RegressionAlert:
    metric: str
    baseline: float
    current: float
    delta: float
    threshold: float

    @property
    def is_regression(self) -> bool:
        return self.delta < -self.threshold

    def __str__(self) -> str:
        sign = "REGRESSION" if self.is_regression else "OK"
        return f"[{sign}] {self.metric}: baseline={self.baseline:.3f}  current={self.current:.3f}  delta={self.delta:+.3f}"


def detect_regressions(
    baseline: RAGASScores,
    current: RAGASScores,
    threshold: float = 0.05,
) -> list[RegressionAlert]:
    """Compare current to baseline; return alerts if any metric dropped > threshold."""
    alerts: list[RegressionAlert] = []
    for metric in ("faithfulness", "answer_relevancy", "context_recall"):
        b = getattr(baseline, metric)
        c = getattr(current, metric)
        alerts.append(RegressionAlert(
            metric=metric, baseline=b, current=c, delta=c - b, threshold=threshold,
        ))
    return alerts


# =================================================================
# SECTION 5b  --  Latency benchmark
# =================================================================

def evaluate_latency_ms(judge: MockJudge, golden: GoldenSet, n_runs: int = 20, seed: int = SEED) -> dict[str, float]:
    """Time `evaluate_rag` over n_runs.  Reports avg / p50 / p95 in ms.

    The lesson's point: evaluation is offline but not free.  A 100-example
    golden set at 5 ms/example = 0.5 seconds; 10K examples = 50 seconds.
    Real LLM-as-judge evals are 100x-1000x slower (network + tokens).
    """
    rng = random.Random(seed)
    for _ in range(3):
        _ = evaluate_rag(judge, golden)
        rng.random()
    samples_ms: list[float] = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        _ = evaluate_rag(judge, golden)
        samples_ms.append((time.perf_counter() - t0) * 1000.0)
    samples_ms.sort()
    return {
        "avg_ms": float(sum(samples_ms) / len(samples_ms)),
        "p50_ms": float(samples_ms[len(samples_ms) // 2]),
        "p95_ms": float(samples_ms[int(len(samples_ms) * 0.95)]),
        "n_runs": float(n_runs),
        "n_examples": float(len(golden.examples)),
        "seed": float(seed),
    }


# =================================================================
# SECTION 6  --  Sample golden set + mock RAG
# =================================================================

GOLDEN_SET = GoldenSet()
GOLDEN_SET.add(GoldenExample(
    query="how much vacation do I get per year",
    ground_truth="20 days per year, accrued monthly",
    relevant_doc_ids=["hr-1"],
    category="factual",
))
GOLDEN_SET.add(GoldenExample(
    query="what is the 401k match",
    ground_truth="100% of the first 3% of salary, 50% of the next 2%",
    relevant_doc_ids=["hr-2"],
    category="factual",
))
GOLDEN_SET.add(GoldenExample(
    query="sick leave doctor's note rule",
    ground_truth="A doctor's note is required after 3 consecutive days",
    relevant_doc_ids=["hr-3"],
    category="factual",
))
GOLDEN_SET.add(GoldenExample(
    query="how long do I have to submit expenses",
    ground_truth="Within 30 days",
    relevant_doc_ids=["fin-1"],
    category="factual",
))
GOLDEN_SET.add(GoldenExample(
    query="code review SLA",
    ground_truth="Within 1 business day, PRs under 400 lines",
    relevant_doc_ids=["ops-1"],
    category="procedural",
))
GOLDEN_SET.add(GoldenExample(
    query="P1 incident response time",
    ground_truth="Acknowledged within 15 minutes, resolved within 4 hours",
    relevant_doc_ids=["ops-2"],
    category="procedural",
))
GOLDEN_SET.add(GoldenExample(
    query="data retention policy",
    ground_truth="Customer PII 7 years, logs 90 days, backups 1 year",
    relevant_doc_ids=["ops-3"],
    category="factual",
))


# Mock RAG: a simple lookup that returns the "correct" answer for golden queries
# and a plausible answer for others.  In production this is the real RAG.
MOCK_CORPUS: dict[str, str] = {
    "hr-1": "Employees accrue 20 days of vacation per year, accrued monthly at 1.67 days per month. Unused days carry over up to 5.",
    "hr-2": "The 401k match is 100% of the first 3% of salary and 50% of the next 2%. Vesting is immediate.",
    "hr-3": "Sick leave is 10 days per year. A doctor's note is required after 3 consecutive days.",
    "fin-1": "Expense reports must be submitted within 30 days. Receipts are required for expenses over $25.",
    "fin-2": "Reimbursement is processed within 14 days of approval. Manager approval is required over $500.",
    "ops-1": "Code reviews must be completed within 1 business day. PRs should be under 400 lines.",
    "ops-2": "P1 incidents must be acknowledged within 15 minutes and resolved within 4 hours.",
    "ops-3": "Customer PII is retained for 7 years. Logs are retained for 90 days. Backups for 1 year.",
}


def mock_rag(query: str) -> tuple[str, list[str], str]:
    """A mock RAG that returns the doc whose text most overlaps with the query."""
    q_words = set(re.findall(r"\w+", query.lower()))
    best_id = None
    best_overlap = -1
    for doc_id, text in MOCK_CORPUS.items():
        d_words = set(re.findall(r"\w+", text.lower()))
        overlap = len(q_words & d_words)
        if overlap > best_overlap:
            best_overlap = overlap
            best_id = doc_id
    if best_id is None:
        return ("I don't know.", [], "")
    retrieved = [best_id, list(MOCK_CORPUS.keys())[0]]  # the second is always wrong
    answer = f"Based on policy: {MOCK_CORPUS[best_id]}"
    context = MOCK_CORPUS[best_id]
    return (answer, retrieved, context)


# =================================================================
# SECTION 7  --  End-to-end evaluation
# =================================================================

def evaluate_rag(judge: MockJudge, golden: GoldenSet) -> EvaluationReport:
    """Run the golden set through the mock RAG and judge each result."""
    report = EvaluationReport(judge=judge)
    for ex in golden.examples:
        answer, retrieved_ids, context = mock_rag(ex.query)
        scores = RAGASScores(
            faithfulness=judge.judge_faithfulness(answer, context),
            answer_relevancy=judge.judge_answer_relevancy(answer, ex.query),
            context_recall=judge.judge_context_recall(retrieved_ids, ex.relevant_doc_ids),
        )
        report.add(EvalResult(
            query=ex.query,
            ground_truth=ex.ground_truth,
            answer=answer,
            retrieved_ids=retrieved_ids,
            relevant_ids=ex.relevant_doc_ids,
            scores=scores,
            category=ex.category,
        ))
    return report


# =================================================================
# SECTION 8  --  Demo
# =================================================================

def demo() -> None:
    print("=" * 70)
    print(f"  {LESSON_NUMBER}  --  Evaluation and RAGAS-style metrics")
    print("=" * 70)

    # 1. Golden set
    print("\n  Section 1: Golden set")
    print("  " + "-" * 66)
    print(f"    size: {len(GOLDEN_SET)}")
    cats = GOLDEN_SET.by_category()
    for cat, exs in cats.items():
        print(f"    {cat:<14} {len(exs)} examples")

    # 2. Run eval
    print("\n  Section 2: Run evaluation")
    print("  " + "-" * 66)
    judge = MockJudge()
    report = evaluate_rag(judge, GOLDEN_SET)
    print(f"    evaluated: {len(report.results)}")

    # 3. Per-example scores
    print("\n  Section 3: Per-example scores")
    print("  " + "-" * 66)
    print(f"    {'query':<42}  {'faith':>6}  {'rel':>6}  {'recall':>6}  pass?")
    for r in report.results:
        q = r.query[:40]
        ok = "OK" if r.passed else "MISS"
        print(f"    {q:<42}  {r.scores.faithfulness:>6.2f}  {r.scores.answer_relevancy:>6.2f}  {r.scores.context_recall:>6.2f}  {ok}")

    # 4. Aggregate
    print("\n  Section 4: Aggregate scores")
    print("  " + "-" * 66)
    m = report.mean_scores()
    s = report.std_scores()
    print(f"    {'metric':<20}  {'mean':>6}  {'std':>6}")
    print(f"    {'faithfulness':<20}  {m.faithfulness:>6.2f}  {s.faithfulness:>6.2f}")
    print(f"    {'answer_relevancy':<20}  {m.answer_relevancy:>6.2f}  {s.answer_relevancy:>6.2f}")
    print(f"    {'context_recall':<20}  {m.context_recall:>6.2f}  {s.context_recall:>6.2f}")
    print(f"    pass rate:  {report.pass_rate():.0%}")

    # 5. By category
    print("\n  Section 5: By category")
    print("  " + "-" * 66)
    for cat, scores in report.by_category().items():
        print(f"    {cat:<14}  faith={scores.faithfulness:.2f}  rel={scores.answer_relevancy:.2f}  recall={scores.context_recall:.2f}")

    # 6. Regression detector
    print("\n  Section 6: Regression detector (simulated baseline)")
    print("  " + "-" * 66)
    fake_baseline = RAGASScores(faithfulness=0.90, answer_relevancy=0.85, context_recall=0.95)
    alerts = detect_regressions(fake_baseline, m, threshold=0.05)
    for a in alerts:
        print(f"    {a}")

    # 7. Latency benchmark
    print("\n  Section 7: Evaluation latency (avg / p50 / p95 in ms)")
    print("  " + "-" * 66)
    judge = MockJudge()
    lat = evaluate_latency_ms(judge, GOLDEN_SET, n_runs=20, seed=17)
    print(f"    n_examples={int(lat['n_examples'])}  n_runs={int(lat['n_runs'])}")
    print(f"    avg={lat['avg_ms']:>6.2f} ms   p50={lat['p50_ms']:>6.2f}   p95={lat['p95_ms']:>6.2f}")
    print(f"    seed={int(lat['seed'])}  --  evaluations/hour on one core ~ {3600_000 / max(lat['avg_ms'], 0.01):,.0f}")

    print("=" * 70)
    print("  See L10-evaluation-ragas.ipynb for the runnable version.")
    print("=" * 70)


# =================================================================
# SECTION 9  --  Tests
# =================================================================

def test_golden_set_by_category() -> None:
    gs = GoldenSet()
    gs.add(GoldenExample("q1", "a", ["d1"], "factual"))
    gs.add(GoldenExample("q2", "b", ["d2"], "procedural"))
    cats = gs.by_category()
    assert "factual" in cats
    assert "procedural" in cats
    assert len(cats["factual"]) == 1


def test_golden_set_len() -> None:
    assert len(GOLDEN_SET) == 7


def test_judge_faithfulness_supported() -> None:
    j = MockJudge()
    s = j.judge_faithfulness("the cat is on the mat", "the cat is on the mat")
    assert s > 0.9


def test_judge_faithfulness_unsupported() -> None:
    j = MockJudge()
    s = j.judge_faithfulness("the quantum entanglement is purple", "the cat is on the mat")
    # The "the" overlap gives a non-zero score; assert it's lower than supported
    supported = j.judge_faithfulness("the cat is on the mat", "the cat is on the mat")
    assert s < supported


def test_judge_answer_relevancy_match() -> None:
    j = MockJudge()
    s = j.judge_answer_relevancy("you get 20 days vacation", "how much vacation do I get")
    assert s > 0.3


def test_judge_answer_relevancy_mismatch() -> None:
    j = MockJudge()
    s = j.judge_answer_relevancy("the cat sat on the mat", "what is the 401k match")
    assert s < 0.3


def test_judge_context_recall_perfect() -> None:
    j = MockJudge()
    s = j.judge_context_recall(["d1", "d2"], ["d1", "d2"])
    assert s == 1.0


def test_judge_context_recall_zero() -> None:
    j = MockJudge()
    s = j.judge_context_recall([], ["d1", "d2"])
    assert s == 0.0


def test_judge_context_recall_empty_relevant() -> None:
    j = MockJudge()
    s = j.judge_context_recall(["d1"], [])
    assert s == 1.0  # vacuous


def test_eval_result_pass() -> None:
    r = EvalResult(
        "q", "truth", "answer", ["d"], ["d"],
        RAGASScores(0.9, 0.8, 0.9), "factual",
    )
    assert r.passed


def test_eval_result_fail() -> None:
    r = EvalResult(
        "q", "truth", "answer", ["d"], ["d"],
        RAGASScores(0.5, 0.5, 0.5), "factual",
    )
    assert not r.passed


def test_report_mean_scores() -> None:
    j = MockJudge()
    report = evaluate_rag(j, GOLDEN_SET)
    m = report.mean_scores()
    assert 0 <= m.faithfulness <= 1
    assert 0 <= m.answer_relevancy <= 1
    assert 0 <= m.context_recall <= 1


def test_report_by_category() -> None:
    j = MockJudge()
    report = evaluate_rag(j, GOLDEN_SET)
    by_cat = report.by_category()
    assert "factual" in by_cat
    assert "procedural" in by_cat


def test_detect_regressions_no_regression() -> None:
    base = RAGASScores(0.8, 0.8, 0.8)
    cur = RAGASScores(0.82, 0.81, 0.79)
    alerts = detect_regressions(base, cur, threshold=0.05)
    # 0.79 vs 0.8 is -0.01, no regression
    for a in alerts:
        if a.metric == "context_recall":
            assert not a.is_regression


def test_detect_regressions_alert() -> None:
    base = RAGASScores(0.9, 0.9, 0.9)
    cur = RAGASScores(0.7, 0.9, 0.9)  # faithfulness dropped 0.2
    alerts = detect_regressions(base, cur, threshold=0.05)
    faith_alert = next(a for a in alerts if a.metric == "faithfulness")
    assert faith_alert.is_regression


def test_ragas_scores_mean() -> None:
    """The 3-metric mean is the simple arithmetic mean of the three RAGAS scores."""
    s = RAGASScores(faithfulness=0.6, answer_relevancy=0.9, context_recall=0.3)
    assert abs(s.mean() - 0.6) < 1e-9


def test_pass_rate_all_pass() -> None:
    """pass_rate is 1.0 when every EvalResult.passed is True."""
    report = EvaluationReport()
    for i in range(3):
        report.add(EvalResult(
            query=f"q{i}", ground_truth="t", answer="a",
            retrieved_ids=["d"], relevant_ids=["d"],
            scores=RAGASScores(0.9, 0.9, 0.9), category="factual",
        ))
    assert report.pass_rate() == 1.0


def test_pass_rate_none_pass() -> None:
    """pass_rate is 0.0 when no EvalResult.passed is True."""
    report = EvaluationReport()
    for i in range(3):
        report.add(EvalResult(
            query=f"q{i}", ground_truth="t", answer="a",
            retrieved_ids=["d"], relevant_ids=["d"],
            scores=RAGASScores(0.1, 0.1, 0.1), category="factual",
        ))
    assert report.pass_rate() == 0.0


def test_std_scores_one_sample_is_zero() -> None:
    """With one sample, std is 0 (rubric: len < 2 → zero std)."""
    report = EvaluationReport()
    report.add(EvalResult(
        query="q", ground_truth="t", answer="a",
        retrieved_ids=["d"], relevant_ids=["d"],
        scores=RAGASScores(0.5, 0.6, 0.7), category="factual",
    ))
    s = report.std_scores()
    assert s.faithfulness == 0.0
    assert s.answer_relevancy == 0.0
    assert s.context_recall == 0.0


def test_golden_set_default_len_is_zero() -> None:
    """A fresh GoldenSet is empty."""
    gs = GoldenSet()
    assert len(gs) == 0
    assert gs.by_category() == {}


def test_regression_alert_str_format() -> None:
    """The RegressionAlert __str__ includes the metric name and the delta."""
    a = RegressionAlert(metric="faithfulness", baseline=0.9, current=0.7,
                         delta=-0.2, threshold=0.05)
    s = str(a)
    assert "faithfulness" in s
    assert "-0.200" in s or "-0.2" in s
    assert "REGRESSION" in s


# =================================================================
# ENTRY
# =================================================================

if __name__ == "__main__":
    demo()
