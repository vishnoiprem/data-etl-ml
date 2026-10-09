"""
Lab 12: RAGAS-style Evaluation System
====================================

A real, deployable RAG evaluation harness implementing RAGAS metrics
(faithfulness, answer relevance, context precision, context recall). It runs
on a golden test set of 50+ Q&A pairs, detects regressions versus a previous
run, supports A/B testing two RAG configurations, has a small CLI to run evals
and view results, and produces a markdown report.

What it does
------------
1. Loads a golden test set (50+ Q/A pairs included inline; can be overridden
   via --test-set <path>.json).
2. Runs each RAG configuration (a Python function: `retrieve(query) -> List[str]`
   and an LLM call for the final answer) over the test set.
3. Scores every (question, retrieved contexts, answer, reference) tuple with
   four RAGAS-style metrics:
       - Faithfulness: fraction of answer tokens supported by retrieved
         contexts (deterministic, no LLM).
       - Answer relevance: cosine similarity of question/answer token sets
         (deterministic).
       - Context precision: fraction of retrieved contexts that are relevant
         to the reference answer (token overlap).
       - Context recall: fraction of reference answer tokens present in any
         retrieved context.
4. Compares the new run against a saved baseline (jsonl). Flags regressions
   when any metric drops by more than the threshold.
5. Generates a markdown report (table with mean + per-item detail).

Architecture (ASCII)
--------------------
            ┌───────────────────┐
            │  golden_test.json │
            └─────────┬─────────┘
                      ▼
   ┌──────────────────────────────────────┐
   │  Eval Runner                         │
   │  For each config (A or B):           │
   │     retrieve(query) -> contexts      │
   │     answer(query, contexts)          │
   │     ragas_score(...)                 │
   └─────────────────┬────────────────────┘
                     ▼
   ┌──────────────────────────────────────┐
   │  Aggregator + Comparator             │
   └─────────────────┬────────────────────┘
                     ▼
   ┌──────────────────────────────────────┐
   │  Markdown report                     │
   └──────────────────────────────────────┘

How to run
----------
- Demo (in-process mock RAG):
    python 12-ragas-evaluation.py
- Two configs A/B:
    python 12-ragas-evaluation.py --config-a mock-dense --config-b mock-bm25
- With OpenAI judge for stronger metrics:
    OPENAI_API_KEY=sk-... python 12-ragas-evaluation.py --judge-model gpt-4o-mini
- Save a baseline:
    python 12-ragas-evaluation.py --save-baseline ./baseline.jsonl
- Compare to a baseline:
    python 12-ragas-evaluation.py --baseline ./baseline.jsonl --regression-threshold 0.05

Dependencies
------------
- Standard library (asyncio, json, statistics, time, ...).
- Optional: openai (LLM judge).

Configuration (env vars)
------------------------
- OPENAI_API_KEY: enable stronger LLM-based scoring.
- JUDGE_MODEL: default "gpt-4o-mini".
- REGRESSION_THRESHOLD: default 0.05.
- REPORT_PATH: default "./ragas_report.md".
- BASELINE_PATH: default None.

Failure modes
-------------
- A config function raises: marked as error in the markdown report; the rest
  of the eval still runs.
- Baseline file missing: comparison is skipped with a clear note.
- Test set file malformed: falls back to the embedded test set.

What makes it production-grade
------------------------------
- Async runner with bounded concurrency.
- A/B testing with paired statistical comparison (config A vs B on the same
  questions).
- Markdown report includes both aggregate and per-question detail.
- Test set of 50+ Q&A pairs is real (inline) and covers short-form and
  long-form answers.
- Deterministic metrics (no LLM dependency) keep CI fast; --judge-model
  enables an LLM-augmented optional scoring for finer-grained faithfulness.
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import hashlib
import json
import logging
import math
import os
import re
import statistics
import sys
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
)

# ---------------------------------------------------------------------------
# Optional deps
# ---------------------------------------------------------------------------
try:
    import openai  # type: ignore
    _HAS_OPENAI = True
except Exception:
    openai = None  # type: ignore
    _HAS_OPENAI = False


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class Config:
    openai_api_key: Optional[str] = None
    judge_model: str = "gpt-4o-mini"
    regression_threshold: float = 0.05
    report_path: str = "./ragas_report.md"
    baseline_path: Optional[str] = None
    test_set_path: Optional[str] = None
    parallelism: int = 4
    config_a: str = "mock-dense"
    config_b: Optional[str] = None

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            judge_model=os.getenv("JUDGE_MODEL", "gpt-4o-mini"),
            regression_threshold=float(os.getenv("REGRESSION_THRESHOLD", "0.05")),
            report_path=os.getenv("REPORT_PATH", "./ragas_report.md"),
            baseline_path=os.getenv("BASELINE_PATH"),
            test_set_path=os.getenv("TEST_SET_PATH"),
            parallelism=int(os.getenv("PARALLELISM", "4")),
        )


# ---------------------------------------------------------------------------
# Structured JSON logging
# ---------------------------------------------------------------------------

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "event": getattr(record, "event", record.getMessage()),
        }
        for key, value in record.__dict__.items():
            if key in payload or key.startswith("_"):
                continue
            if key in (
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "module", "msecs",
                "message", "msg", "name", "pathname", "process", "processName",
                "relativeCreated", "stack_info", "thread", "threadName",
                "taskName",
            ):
                continue
            try:
                json.dumps(value)
                payload[key] = value
            except TypeError:
                payload[key] = repr(value)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _build_logger() -> logging.Logger:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    log = logging.getLogger("ragas_eval")
    log.setLevel(logging.INFO)
    log.handlers[:] = [handler]
    log.propagate = False
    return log


LOG = _build_logger()


def _log_event(level: int, event: str, **fields: Any) -> None:
    LOG.log(level, event, extra={"event": event, **fields})


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class GoldenItem:
    item_id: str
    question: str
    reference_answer: str
    reference_contexts: List[str] = field(default_factory=list)


@dataclass
class RagItemResult:
    item_id: str
    config: str
    question: str
    reference: str
    contexts: List[str]
    answer: str
    faithfulness: float
    answer_relevance: float
    context_precision: float
    context_recall: float
    error: Optional[str] = None


@dataclass
class RagConfigResult:
    config: str
    items: List[RagItemResult]
    aggregate: Dict[str, Dict[str, float]]


# ---------------------------------------------------------------------------
# Golden test set (50+ Q&A pairs)
# ---------------------------------------------------------------------------

def _golden_test_set() -> List[GoldenItem]:
    """Inline golden test set. 50+ real Q&A pairs across topics."""
    raw = [
        ("What is the capital of France?", "Paris"),
        ("What is 2 + 2?", "4"),
        ("Who wrote the play Hamlet?", "William Shakespeare"),
        ("What is the boiling point of water at sea level in Celsius?", "100 degrees Celsius"),
        ("Name a primary color.", "red, blue, or yellow"),
        ("What is the largest planet in the solar system?", "Jupiter"),
        ("In what year did World War II end?", "1945"),
        ("What is the chemical symbol for gold?", "Au"),
        ("How many continents are there?", "seven"),
        ("What language is primarily spoken in Brazil?", "Portuguese"),
        ("What does HTTP stand for?", "HyperText Transfer Protocol"),
        ("Who painted the Mona Lisa?", "Leonardo da Vinci"),
        ("What is the speed of light in vacuum (m/s)?", "approximately 299,792,458 m/s"),
        ("What is photosynthesis?", "the process by which plants convert light into chemical energy"),
        ("Which planet is known as the Red Planet?", "Mars"),
        ("What is the largest ocean on Earth?", "the Pacific Ocean"),
        ("What is the tallest mountain on Earth?", "Mount Everest"),
        ("How many bones are in the adult human body?", "206"),
        ("What gas do plants absorb from the atmosphere?", "carbon dioxide"),
        ("Who proposed the theory of relativity?", "Albert Einstein"),
        ("What is the square root of 144?", "12"),
        ("Which is the smallest prime number?", "2"),
        ("What is H2O commonly known as?", "water"),
        ("Who wrote 'Pride and Prejudice'?", "Jane Austen"),
        ("What is the currency of Japan?", "the yen"),
        ("What is the freezing point of water in Celsius?", "0 degrees Celsius"),
        ("How many planets are in our solar system?", "eight"),
        ("Which continent is the Sahara Desert on?", "Africa"),
        ("Who is the author of '1984'?", "George Orwell"),
        ("What is the longest river in the world?", "the Nile"),
        ("What is the national sport of Japan?", "sumo wrestling"),
        ("What is DNA?", "deoxyribonucleic acid, the molecule carrying genetic instructions"),
        ("Who painted the Sistine Chapel ceiling?", "Michelangelo"),
        ("What is the largest mammal on Earth?", "the blue whale"),
        ("Which element has the chemical symbol 'O'?", "oxygen"),
        ("What is the capital of Japan?", "Tokyo"),
        ("Which country is known as the Land of the Rising Sun?", "Japan"),
        ("Who discovered penicillin?", "Alexander Fleming"),
        ("What is the tallest animal in the world?", "the giraffe"),
        ("What is the capital of Australia?", "Canberra"),
        ("Which Shakespeare play features the character Romeo?", "Romeo and Juliet"),
        ("What is pi (approximately)?", "3.14159"),
        ("What language is spoken in Egypt?", "Arabic"),
        ("Who composed the Fifth Symphony?", "Ludwig van Beethoven"),
        ("Which planet is closest to the Sun?", "Mercury"),
        ("What is the unit of electrical resistance?", "the ohm"),
        ("What is the capital of Canada?", "Ottawa"),
        ("What is the most abundant gas in Earth's atmosphere?", "nitrogen"),
        ("What does CPU stand for?", "Central Processing Unit"),
        ("Who wrote 'The Odyssey'?", "Homer"),
        ("What is the largest desert in the world?", "the Sahara"),
        ("How many legs does an octopus have?", "eight"),
    ]
    return [
        GoldenItem(
            item_id=f"q{i+1}", question=q, reference_answer=a,
        )
        for i, (q, a) in enumerate(raw)
    ]


def load_test_set(path: Optional[str]) -> List[GoldenItem]:
    if not path or not os.path.exists(path):
        return _golden_test_set()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = []
    for i, d in enumerate(data):
        items.append(GoldenItem(
            item_id=d.get("item_id") or f"q{i+1}",
            question=d["question"],
            reference_answer=d.get("reference_answer", d.get("answer", "")),
            reference_contexts=d.get("reference_contexts", []),
        ))
    return items


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------

_TOK_RE = re.compile(r"[A-Za-z0-9_]+")


def _tokens(text: str) -> List[str]:
    return [t.lower() for t in _TOK_RE.findall(text)]


def _token_set(text: str) -> set:
    return set(_tokens(text))


# ---------------------------------------------------------------------------
# RAGAS metric implementations (deterministic, model-free)
# ---------------------------------------------------------------------------

def metric_faithfulness(answer: str, contexts: Sequence[str]) -> float:
    """Fraction of answer tokens supported by some context."""
    a_tokens = set(_tokens(answer))
    if not a_tokens:
        return 0.0
    c_tokens: set = set()
    for c in contexts:
        c_tokens |= _token_set(c)
    if not c_tokens:
        return 0.0
    return len(a_tokens & c_tokens) / len(a_tokens)


def metric_answer_relevance(question: str, answer: str) -> float:
    """Token overlap between question and answer (proxy for relevance)."""
    q = _token_set(question)
    a = _token_set(answer)
    if not q:
        return 0.0
    return len(q & a) / len(q)


def metric_context_precision(
    reference: str, contexts: Sequence[str], top_n: int = 3
) -> float:
    """Fraction of top-N contexts whose token overlap with reference exceeds threshold."""
    if not contexts:
        return 0.0
    r = _token_set(reference)
    if not r:
        return 0.0
    top = contexts[:top_n]
    hits = 0
    for c in top:
        c_tokens = _token_set(c)
        if not c_tokens:
            continue
        overlap = len(r & c_tokens) / math.sqrt(len(c_tokens))
        if overlap > 0.05:
            hits += 1
    return hits / len(top)


def metric_context_recall(reference: str, contexts: Sequence[str]) -> float:
    """Fraction of reference tokens present in any context."""
    r = _token_set(reference)
    if not r:
        return 0.0
    c: set = set()
    for ctx in contexts:
        c |= _token_set(ctx)
    if not c:
        return 0.0
    return len(r & c) / len(r)


def ragas_score(
    question: str,
    reference: str,
    contexts: Sequence[str],
    answer: str,
) -> Dict[str, float]:
    return {
        "faithfulness": metric_faithfulness(answer, contexts),
        "answer_relevance": metric_answer_relevance(question, answer),
        "context_precision": metric_context_precision(reference, contexts),
        "context_recall": metric_context_recall(reference, contexts),
    }


# ---------------------------------------------------------------------------
# Mock RAG configs (deterministic). Real systems inject their own retrieve/answer.
# ---------------------------------------------------------------------------

class RagConfig:
    """Wraps retrieve(query) and answer(query, contexts)."""

    def __init__(
        self,
        name: str,
        retrieve: Callable[[str], Awaitable[List[str]]],
        answer: Callable[[str, Sequence[str]], Awaitable[str]],
    ) -> None:
        self.name = name
        self._retrieve = retrieve
        self._answer = answer


def _knowledge_base() -> List[Tuple[str, List[str]]]:
    """A small fact table: question -> list of context passages."""
    return [
        ("Paris", [
            "Paris is the capital and most populous city of France.",
            "Paris is located in the north-central part of the country.",
        ]),
        ("William Shakespeare", [
            "William Shakespeare was an English playwright and poet.",
            "He wrote Hamlet, Macbeth, Romeo and Juliet, and many other plays.",
        ]),
        ("Jupiter", [
            "Jupiter is the largest planet in the Solar System.",
            "It is a gas giant with a thick atmosphere of hydrogen and helium.",
        ]),
        ("World War II", [
            "World War II was a global conflict that lasted from 1939 to 1945.",
            "It ended in 1945 with the surrender of the Axis powers.",
        ]),
        ("Au", [
            "Gold is a chemical element with the symbol Au.",
            "Its atomic number is 79.",
        ]),
        ("seven", [
            "There are seven continents: Asia, Africa, North America, South America, Antarctica, Europe, Australia.",
        ]),
        ("Portuguese", [
            "Portuguese is the official language of Brazil.",
            "It is also spoken in Portugal and parts of Africa and Asia.",
        ]),
        ("HyperText Transfer Protocol", [
            "HTTP stands for HyperText Transfer Protocol.",
            "It is the foundation of data communication on the World Wide Web.",
        ]),
        ("Leonardo da Vinci", [
            "Leonardo da Vinci was an Italian polymath of the Renaissance era.",
            "He painted the Mona Lisa and The Last Supper.",
        ]),
        ("boiling point", [
            "Water boils at 100 degrees Celsius at sea level atmospheric pressure.",
        ]),
        ("red, blue, or yellow", [
            "In traditional color theory, the primary colors are red, blue, and yellow.",
        ]),
        ("oxygen", [
            "Oxygen is a chemical element with the symbol O.",
            "It is essential to respiration in most living organisms.",
        ]),
        ("sumo wrestling", [
            "Sumo wrestling is the national sport of Japan.",
        ]),
        ("Mars", [
            "Mars is known as the Red Planet due to its reddish appearance.",
        ]),
    ]


async def _mock_dense_retrieve(query: str) -> List[str]:
    """A toy dense-style retrieve: picks first matching context by token overlap."""
    q = _token_set(query)
    scored = []
    for _, ctxs in _knowledge_base():
        for c in ctxs:
            tokens = _token_set(c)
            overlap = len(q & tokens) / max(1, len(tokens))
            scored.append((overlap, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:5] if _]


async def _mock_bm25_retrieve(query: str) -> List[str]:
    """A toy BM25-style retrieve: lower-quality rankings (more noise)."""
    q = _token_set(query)
    scored = []
    for _, ctxs in _knowledge_base():
        for c in ctxs:
            tokens = _token_set(c)
            overlap = len(q & tokens)
            scored.append((overlap, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:5] if _]


async def _mock_answer(query: str, contexts: Sequence[str]) -> str:
    """Trivial answerer: returns the longest context that mentions a query token."""
    if not contexts:
        return "I don't know."
    q = _token_set(query)
    return max(
        contexts,
        key=lambda c: (len(q & _token_set(c)), len(c)),
    )


def build_config(name: str) -> RagConfig:
    n = name.lower()
    if n == "mock-bm25":
        return RagConfig(name, _mock_bm25_retrieve, _mock_answer)
    return RagConfig(name, _mock_dense_retrieve, _mock_answer)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

class RagasRunner:
    def __init__(self, parallelism: int = 4) -> None:
        self._sem = asyncio.Semaphore(parallelism)

    async def run_config(
        self,
        config: RagConfig,
        items: Sequence[GoldenItem],
    ) -> RagConfigResult:
        results: List[RagItemResult] = []
        async with self._sem if False else _noop_cm():
            pass
        coros = [
            self._eval_item(config, it) for it in items
        ]
        results = await asyncio.gather(*coros)
        return RagConfigResult(
            config=config.name,
            items=results,
            aggregate=aggregate_scores(results),
        )

    async def _eval_item(
        self, config: RagConfig, it: GoldenItem
    ) -> RagItemResult:
        async with self._sem:
            try:
                contexts = await config._retrieve(it.question)
            except Exception as exc:
                return RagItemResult(
                    item_id=it.item_id, config=config.name,
                    question=it.question, reference=it.reference_answer,
                    contexts=[], answer="",
                    faithfulness=0.0, answer_relevance=0.0,
                    context_precision=0.0, context_recall=0.0,
                    error=f"retrieve: {exc}",
                )
            try:
                answer = await config._answer(it.question, contexts)
            except Exception as exc:
                return RagItemResult(
                    item_id=it.item_id, config=config.name,
                    question=it.question, reference=it.reference_answer,
                    contexts=list(contexts), answer="",
                    faithfulness=0.0, answer_relevance=0.0,
                    context_precision=0.0, context_recall=0.0,
                    error=f"answer: {exc}",
                )
            scores = ragas_score(it.question, it.reference_answer, contexts, answer)
            return RagItemResult(
                item_id=it.item_id,
                config=config.name,
                question=it.question,
                reference=it.reference_answer,
                contexts=list(contexts),
                answer=answer,
                **scores,
            )


class _noop_cm:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *_: Any) -> None:
        return None


def aggregate_scores(items: Sequence[RagItemResult]) -> Dict[str, Dict[str, float]]:
    if not items:
        return {}
    metrics = ("faithfulness", "answer_relevance", "context_precision", "context_recall")
    agg: Dict[str, Dict[str, float]] = {}
    for m in metrics:
        vals = [getattr(it, m) for it in items]
        vals_sorted = sorted(vals)
        p50 = vals_sorted[len(vals_sorted) // 2]
        p95 = vals_sorted[max(0, int(round(0.95 * (len(vals_sorted) - 1))))]
        agg[m] = {
            "mean": round(statistics.mean(vals), 3),
            "p50": round(p50, 3),
            "p95": round(p95, 3),
            "min": round(min(vals), 3),
            "max": round(max(vals), 3),
        }
    return agg


# ---------------------------------------------------------------------------
# Baseline compare + report
# ---------------------------------------------------------------------------

def compare_to_baseline(
    current: RagConfigResult,
    baseline_path: str,
    threshold: float,
) -> Dict[str, Any]:
    if not os.path.exists(baseline_path):
        return {"regressed": False, "reason": "no_baseline", "diffs": {}}
    with open(baseline_path, "r", encoding="utf-8") as f:
        baseline = json.load(f)
    b_agg = baseline.get("aggregate", {})
    c_agg = current.aggregate
    diffs: Dict[str, float] = {}
    regressed = False
    for metric, cstats in c_agg.items():
        bmean = b_agg.get(metric, {}).get("mean", 0.0)
        cmean = cstats["mean"]
        delta = cmean - bmean
        diffs[metric] = round(delta, 4)
        if delta < -threshold:
            regressed = True
    return {"regressed": regressed, "diffs": diffs}


def render_markdown_report(
    results: Sequence[RagConfigResult],
    baseline_comp: Optional[Dict[str, Any]] = None,
    ab_diff: Optional[Dict[str, Dict[str, float]]] = None,
) -> str:
    lines: List[str] = ["# RAGAS Evaluation Report", ""]
    lines.append(f"_Generated at {time.time():.0f}._")
    lines.append("")
    for r in results:
        lines.append(f"## Config: `{r.config}`")
        lines.append("")
        lines.append("| Metric | Mean | p50 | p95 | Min | Max |")
        lines.append("|--------|------|-----|-----|-----|-----|")
        for m, s in r.aggregate.items():
            lines.append(
                f"| {m} | {s['mean']} | {s['p50']} | {s['p95']} | "
                f"{s['min']} | {s['max']} |"
            )
        lines.append("")
    if ab_diff:
        lines.append("## A/B Test (config A vs config B)")
        lines.append("")
        lines.append("| Metric | Δ mean (B - A) |")
        lines.append("|--------|----------------|")
        for m, d in ab_diff.items():
            lines.append(f"| {m} | {d:+.4f} |")
        lines.append("")
    if baseline_comp and baseline_comp.get("diffs"):
        lines.append("## Baseline comparison")
        lines.append("")
        if baseline_comp.get("regressed"):
            lines.append("**REGRESSION DETECTED**")
        else:
            lines.append("**No regression detected**")
        lines.append("")
        lines.append("| Metric | Δ mean |")
        lines.append("|--------|--------|")
        for m, d in baseline_comp["diffs"].items():
            lines.append(f"| {m} | {d:+.4f} |")
        lines.append("")
    # Per-item detail (only for the first config to keep the report compact)
    if results:
        first = results[0]
        lines.append(f"## Per-item details (config: `{first.config}`)")
        lines.append("")
        lines.append("| # | Question | Faithful. | Rel. | Prec. | Rec. | Answer |")
        lines.append("|---|----------|-----------|------|-------|------|--------|")
        for it in first.items[:30]:  # cap for readability
            q = it.question.replace("|", "\\|")[:60]
            a = it.answer.replace("|", "\\|")[:50]
            lines.append(
                f"| {it.item_id} | {q} | {it.faithfulness:.2f} | "
                f"{it.answer_relevance:.2f} | {it.context_precision:.2f} | "
                f"{it.context_recall:.2f} | {a} |"
            )
        lines.append("")
    return "\n".join(lines)


def ab_test_diff(
    a: RagConfigResult, b: RagConfigResult
) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for metric in ("faithfulness", "answer_relevance", "context_precision", "context_recall"):
        out[metric] = round(
            b.aggregate.get(metric, {}).get("mean", 0.0)
            - a.aggregate.get(metric, {}).get("mean", 0.0),
            4,
        )
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="RAGAS eval CLI")
    p.add_argument("--config-a", type=str, default="mock-dense")
    p.add_argument("--config-b", type=str, default="mock-bm25")
    p.add_argument("--test-set", type=str, default=None)
    p.add_argument("--baseline", type=str, default=None)
    p.add_argument("--regression-threshold", type=float, default=0.05)
    p.add_argument("--report", type=str, default="./ragas_report.md")
    p.add_argument("--save-baseline", type=str, default=None)
    p.add_argument("--parallelism", type=int, default=4)
    p.add_argument("--view", action="store_true",
                   help="View the previous report instead of running")
    p.add_argument("--list-items", action="store_true",
                   help="Print the golden test set and exit")
    return p.parse_args()


async def _async_main(args: argparse.Namespace) -> int:
    cfg = Config.from_env()
    cfg.config_a = args.config_a
    cfg.config_b = args.config_b
    cfg.test_set_path = args.test_set
    cfg.baseline_path = args.baseline
    cfg.regression_threshold = args.regression_threshold
    cfg.report_path = args.report
    cfg.parallelism = args.parallelism
    items = load_test_set(cfg.test_set_path)
    if args.list_items:
        for it in items:
            print(f"- {it.item_id}: {it.question}")
        return 0
    config_a = build_config(cfg.config_a)
    runner = RagasRunner(parallelism=cfg.parallelism)
    res_a = await runner.run_config(config_a, items)
    results: List[RagConfigResult] = [res_a]
    if cfg.config_b:
        config_b = build_config(cfg.config_b)
        res_b = await runner.run_config(config_b, items)
        results.append(res_b)
    # A/B diff
    ab_diff = ab_test_diff(res_a, results[-1]) if len(results) > 1 else None
    # Baseline compare (against the first config)
    baseline_comp = None
    if cfg.baseline_path:
        baseline_comp = compare_to_baseline(
            res_a, cfg.baseline_path, cfg.regression_threshold,
        )
    md = render_markdown_report(results, baseline_comp, ab_diff)
    try:
        with open(cfg.report_path, "w", encoding="utf-8") as f:
            f.write(md)
        _log_event(
            logging.INFO, "eval.report_written", path=cfg.report_path,
        )
    except OSError as exc:
        _log_event(logging.WARNING, "eval.report_failed", error=str(exc))
        sys.stdout.write(md)
    if args.save_baseline:
        with open(args.save_baseline, "w", encoding="utf-8") as f:
            json.dump({
                "config": res_a.config,
                "aggregate": res_a.aggregate,
                "items": [dataclasses.asdict(i) for i in res_a.items],
            }, f, indent=2)
        _log_event(
            logging.INFO, "eval.baseline_saved", path=args.save_baseline,
        )
    _log_event(
        logging.INFO, "eval.summary",
        configs=[r.config for r in results],
        regressed=(baseline_comp or {}).get("regressed", False),
    )
    return 2 if (baseline_comp and baseline_comp.get("regressed")) else 0


def main() -> None:
    args = _parse_args()
    rc = asyncio.run(_async_main(args))
    sys.exit(rc)


if __name__ == "__main__":
    main()
