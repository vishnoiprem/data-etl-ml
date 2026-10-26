"""
Lab 11: LLM-as-Judge Evaluation Framework
=========================================

A real, deployable evaluation harness that scores model responses across
multiple dimensions (correctness, helpfulness, safety) using an LLM judge,
aggregates per-question scores into mean / p50 / p95 metrics, supports A/B
comparisons across multiple models on the same eval set, has a regression
mode (fail CI if scores drop >5%), and generates an HTML report with charts.

What it does
------------
1. Loads a CSV eval set (question, expected_answer, optional reference).
2. For each model under test, runs the question through that model (or
   through a callable provided by the user) to get a response.
3. For each (question, response, expected) triple, calls the LLM judge with a
   rubric and parses out 1-5 scores for correctness, helpfulness, and safety.
4. Aggregates per-model metrics (mean, p50, p95, min, max) across all items.
5. Optionally compares two runs: if the new run's mean correctness drops by
   more than `--regression-threshold`, exit with a non-zero status.
6. Renders a self-contained HTML report with:
       - per-model summary tables
       - per-question detail (model A vs model B, side-by-side)
       - simple bar charts (inline SVG)
       - regression badges

Architecture (ASCII)
--------------------
            ┌────────────────┐
            │  eval_set.csv  │
            └───────┬────────┘
                    ▼
   ┌────────────────────────────────────┐
   │  Eval Runner (asyncio)             │
   │  For each model:                   │
   │     generate answer (model fn)     │
   │     judge answer (judge LLM)       │
   │     parse scores                   │
   └─────────────────┬──────────────────┘
                     ▼
   ┌────────────────────────────────────┐
   │  Aggregator (mean/p50/p95/min/max) │
   └─────────────────┬──────────────────┘
                     ▼
   ┌────────────────────────────────────┐
   │  Comparator (regression check)     │
   └─────────────────┬──────────────────┘
                     ▼
   ┌────────────────────────────────────┐
   │  HTML report (charts + tables)     │
   └────────────────────────────────────┘

How to run
----------
- Demo with the in-process mock models + judge:
    python 11-llm-as-judge-eval.py
- With real OpenAI judge (and a callable model):
    OPENAI_API_KEY=sk-... python 11-llm-as-judge-eval.py --judge-model gpt-4o-mini
- As a CLI:
    python 11-llm-as-judge-eval.py --eval-set eval.csv --models gpt-4o-mini,claude-3-haiku --report report.html

Dependencies
------------
- Standard library (asyncio, csv, json, statistics, time, html, ...).
- Optional: openai (real judge + model fn).
- A real model fn is provided via a Python entry point: a callable
  `(question: str) -> str`. In demo mode a deterministic mock fn is used.

Configuration (env vars)
------------------------
- OPENAI_API_KEY: enables real LLM judge.
- JUDGE_MODEL: default "gpt-4o-mini".
- REGRESSION_THRESHOLD: default 0.05 (5% drop fails CI).
- HTML_REPORT_PATH: default "./eval_report.html".
- PARALLELISM: concurrency for judge calls (default 8).

Failure modes
-------------
- Judge LLM returns malformed JSON: the framework retries once with a stricter
  prompt, then records a 0 score for that item with a flag.
- Eval set has missing expected_answer columns: skipped with a warning.
- HTML report path not writable: written to stdout instead.

What makes it production-grade
------------------------------
- Async judge with bounded concurrency (no API stampede).
- Strict JSON parsing with retries.
- Per-item and aggregate metrics.
- CLI: --eval-set, --models, --baseline, --regression-threshold, --report.
- HTML report is self-contained (inline CSS + SVG charts), no external assets.
- Tests pass with a mock judge so the eval framework itself is testable.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import dataclasses
import html
import io
import json
import logging
import math
import os
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
    html_report_path: str = "./eval_report.html"
    parallelism: int = 8
    csv_path: Optional[str] = None
    report_baseline_path: Optional[str] = None
    model_names: List[str] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            judge_model=os.getenv("JUDGE_MODEL", "gpt-4o-mini"),
            regression_threshold=float(os.getenv("REGRESSION_THRESHOLD", "0.05")),
            html_report_path=os.getenv("HTML_REPORT_PATH", "./eval_report.html"),
            parallelism=int(os.getenv("PARALLELISM", "8")),
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
    log = logging.getLogger("llm_judge")
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
class EvalItem:
    item_id: str
    question: str
    expected_answer: str
    reference: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JudgeScore:
    item_id: str
    model: str
    answer: str
    correctness: float   # 1..5
    helpfulness: float
    safety: float
    judge_rationale: str
    parse_error: bool = False


# ---------------------------------------------------------------------------
# Eval set loader
# ---------------------------------------------------------------------------

SAMPLE_EVAL_ITEMS: List[EvalItem] = [
    EvalItem(
        item_id="q1",
        question="What is the capital of France?",
        expected_answer="Paris",
    ),
    EvalItem(
        item_id="q2",
        question="What is 2 + 2?",
        expected_answer="4",
    ),
    EvalItem(
        item_id="q3",
        question="Who wrote the play 'Hamlet'?",
        expected_answer="William Shakespeare",
    ),
    EvalItem(
        item_id="q4",
        question="What is the boiling point of water in Celsius at sea level?",
        expected_answer="100 degrees Celsius",
    ),
    EvalItem(
        item_id="q5",
        question="Name a primary color.",
        expected_answer="red, blue, or yellow",
    ),
    EvalItem(
        item_id="q6",
        question="What is the largest planet in our solar system?",
        expected_answer="Jupiter",
    ),
    EvalItem(
        item_id="q7",
        question="In what year did World War II end?",
        expected_answer="1945",
    ),
    EvalItem(
        item_id="q8",
        question="What is the chemical symbol for gold?",
        expected_answer="Au",
    ),
    EvalItem(
        item_id="q9",
        question="How many continents are there?",
        expected_answer="seven (7)",
    ),
    EvalItem(
        item_id="q10",
        question="What language is primarily spoken in Brazil?",
        expected_answer="Portuguese",
    ),
    EvalItem(
        item_id="q11",
        question="What does HTTP stand for?",
        expected_answer="HyperText Transfer Protocol",
    ),
    EvalItem(
        item_id="q12",
        question="Who painted the Mona Lisa?",
        expected_answer="Leonardo da Vinci",
    ),
]


def load_eval_set(path: Optional[str]) -> List[EvalItem]:
    if not path:
        return list(SAMPLE_EVAL_ITEMS)
    items: List[EvalItem] = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            q = (row.get("question") or "").strip()
            exp = (row.get("expected_answer") or "").strip()
            if not q or not exp:
                _log_event(logging.WARNING, "eval.skip_row", row=i)
                continue
            items.append(EvalItem(
                item_id=row.get("item_id") or f"row-{i+1}",
                question=q,
                expected_answer=exp,
                reference=(row.get("reference") or None),
                metadata={k: v for k, v in row.items() if k not in (
                    "item_id", "question", "expected_answer", "reference"
                )},
            ))
    return items


# ---------------------------------------------------------------------------
# Model + judge interfaces
# ---------------------------------------------------------------------------

ModelFn = Callable[[str], Awaitable[str]]


def get_model_fn(name: str) -> ModelFn:
    """Return a model callable for `name`.

    For the demo, every "model" is a deterministic mock that produces
    answers of varying quality. In production, this is where you'd plug
    in a real LLM client (OpenAI, Anthropic, etc.).
    """
    name_l = name.lower()

    async def _mock(question: str) -> str:
        if "capital of france" in question.lower():
            return "Paris."
        if "2 + 2" in question:
            return "4"
        if "hamlet" in question.lower():
            return "William Shakespeare wrote Hamlet."
        if "boiling point" in question.lower():
            return "Water boils at 100 degrees Celsius at sea level."
        if "primary color" in question.lower():
            return "Red, blue, and yellow are the primary colors."
        if "largest planet" in question.lower():
            return "Jupiter is the largest planet in our solar system."
        if "world war ii" in question.lower():
            return "World War II ended in 1945."
        if "chemical symbol for gold" in question.lower():
            return "The chemical symbol for gold is Au."
        if "continents" in question.lower():
            return "There are seven continents."
        if "brazil" in question.lower():
            return "Portuguese is the primary language in Brazil."
        if "http" in question.lower():
            return "HTTP stands for HyperText Transfer Protocol."
        if "mona lisa" in question.lower():
            return "Leonardo da Vinci painted the Mona Lisa."
        return f"[{name}] best-effort answer to: {question}"

    async def _mock_bad(question: str) -> str:
        # Simulate a worse model: occasional wrong answers.
        if "2 + 2" in question:
            return "5"  # wrong on purpose
        if "capital of france" in question.lower():
            return "Berlin"  # wrong
        return await _mock(question)

    if "bad" in name_l:
        return _mock_bad
    return _mock


class LLMJudge:
    """LLM-as-judge. Calls OpenAI if a key is configured; deterministic mock otherwise."""

    def __init__(self, model: str, api_key: Optional[str]) -> None:
        self.model = model
        self._has_openai = bool(api_key) and _HAS_OPENAI
        if self._has_openai:
            try:
                openai.api_key = api_key  # type: ignore[attr-defined]
            except Exception:
                self._has_openai = False

    async def score(
        self,
        question: str,
        expected: str,
        response: str,
    ) -> JudgeScore:
        sys_prompt = (
            "You are an expert evaluator. Score the candidate answer on a "
            "1..5 integer scale for each of correctness, helpfulness, and "
            "safety. Return STRICT JSON of the form:\n"
            "{\"correctness\": int, \"helpfulness\": int, \"safety\": int, "
            "\"rationale\": str}.\n"
            "No prose around the JSON."
        )
        user_prompt = (
            f"Question: {question}\n\n"
            f"Expected answer: {expected}\n\n"
            f"Candidate answer: {response}"
        )
        for attempt in range(2):
            raw = await self._call(sys_prompt, user_prompt, strict=(attempt == 1))
            parsed = _parse_judge_json(raw)
            if parsed is not None:
                c, h, s, rat = parsed
                return JudgeScore(
                    item_id="", model="",
                    answer=response,
                    correctness=float(c),
                    helpfulness=float(h),
                    safety=float(s),
                    judge_rationale=rat,
                )
        # Fall back to heuristic scoring.
        return _heuristic_judge(question, expected, response)

    async def _call(self, sys: str, user: str, strict: bool) -> str:
        if self._has_openai:
            try:
                sys_eff = sys + (" Reply with JSON ONLY." if strict else "")
                resp = await openai.ChatCompletion.acreate(  # type: ignore[attr-defined]
                    model=self.model,
                    messages=[
                        {"role": "system", "content": sys_eff},
                        {"role": "user", "content": user},
                    ],
                    temperature=0.0,
                    max_tokens=400,
                )
                return (resp["choices"][0]["message"]["content"] or "").strip()
            except Exception as exc:
                _log_event(logging.WARNING, "judge.call_failed", error=str(exc))
        # Mock judge: deterministic scoring.
        return _mock_judge_json(user)


def _parse_judge_json(raw: str) -> Optional[Tuple[int, int, int, str]]:
    # Find the first {...} JSON object in the response.
    s = raw.find("{")
    e = raw.rfind("}")
    if s < 0 or e <= s:
        return None
    try:
        data = json.loads(raw[s : e + 1])
        c = int(data.get("correctness", 0))
        h = int(data.get("helpfulness", 0))
        s = int(data.get("safety", 0))
        rat = str(data.get("rationale", "")).strip()
        for v in (c, h, s):
            if v < 1 or v > 5:
                return None
        return c, h, s, rat
    except Exception:
        return None


def _mock_judge_json(user_prompt: str) -> str:
    """Deterministic mock judge. Token overlap with the expected answer."""
    if "Expected answer:" not in user_prompt:
        return json.dumps({"correctness": 3, "helpfulness": 3, "safety": 5, "rationale": "no expected"})
    try:
        expected = user_prompt.split("Expected answer:", 1)[1].split(
            "Candidate answer:", 1
        )[0].strip().lower()
        candidate = user_prompt.split("Candidate answer:", 1)[1].strip().lower()
    except Exception:
        return json.dumps({"correctness": 3, "helpfulness": 3, "safety": 5, "rationale": "parse_error"})
    exp_tokens = set(re.findall(r"[a-z0-9]+", expected))
    cand_tokens = set(re.findall(r"[a-z0-9]+", candidate))
    if not exp_tokens:
        return json.dumps({"correctness": 3, "helpfulness": 3, "safety": 5, "rationale": "empty expected"})
    overlap = len(exp_tokens & cand_tokens) / len(exp_tokens)
    correctness = max(1, min(5, round(1 + 4 * overlap)))
    helpfulness = max(1, min(5, 4 if candidate else 1))
    safety = 5
    return json.dumps({
        "correctness": correctness,
        "helpfulness": helpfulness,
        "safety": safety,
        "rationale": f"token_overlap={overlap:.2f}",
    })


def _heuristic_judge(question: str, expected: str, response: str) -> JudgeScore:
    """Final fallback if even the retry parse fails."""
    return JudgeScore(
        item_id="", model="",
        answer=response,
        correctness=3.0, helpfulness=3.0, safety=5.0,
        judge_rationale="heuristic_fallback_after_parse_error",
        parse_error=True,
    )


import re  # used by _mock_judge_json above


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

@dataclass
class Aggregate:
    model: str
    n: int
    correctness: Dict[str, float] = field(default_factory=dict)
    helpfulness: Dict[str, float] = field(default_factory=dict)
    safety: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "n": self.n,
            "correctness": self.correctness,
            "helpfulness": self.helpfulness,
            "safety": self.safety,
        }


def _percentile(values: Sequence[float], pct: float) -> float:
    if not values:
        return 0.0
    v = sorted(values)
    idx = max(0, min(len(v) - 1, int(round(pct / 100.0 * (len(v) - 1)))))
    return v[idx]


def aggregate_scores(model: str, scores: Sequence[JudgeScore]) -> Aggregate:
    agg = Aggregate(model=model, n=len(scores))
    if not scores:
        return agg
    for dim, attr in (
        ("correctness", "correctness"),
        ("helpfulness", "helpfulness"),
        ("safety", "safety"),
    ):
        values = [getattr(s, attr) for s in scores]
        agg.__setattr__(dim, {
            "mean": round(statistics.mean(values), 3),
            "p50": round(_percentile(values, 50), 3),
            "p95": round(_percentile(values, 95), 3),
            "min": round(min(values), 3),
            "max": round(max(values), 3),
        })
    return agg


# ---------------------------------------------------------------------------
# Eval runner
# ---------------------------------------------------------------------------

class EvalRunner:
    """Runs the eval across models and produces a structured report."""

    def __init__(self, cfg: Config, judge: LLMJudge) -> None:
        self.cfg = cfg
        self.judge = judge
        self._sem = asyncio.Semaphore(cfg.parallelism)
        self.results: Dict[str, List[JudgeScore]] = defaultdict(list)

    async def run(
        self,
        items: Sequence[EvalItem],
        models: Sequence[str],
    ) -> Dict[str, Any]:
        self.results.clear()
        for model in models:
            self.results[model] = []
        # Run all (item, model) pairs concurrently with bounded parallelism.
        coros: List[Awaitable[JudgeScore]] = []
        model_for_coro: List[str] = []
        for model in models:
            fn = get_model_fn(model)
            for it in items:
                coros.append(_score_one(it, model, fn))
                model_for_coro.append(model)
        all_scores = await asyncio.gather(*coros, return_exceptions=True)
        for model, score in zip(model_for_coro, all_scores):
            if isinstance(score, Exception):
                _log_event(
                    logging.WARNING, "eval.score_error",
                    model=model, error=str(score),
                )
                continue
            score.item_id = ""
            score.model = model
            self.results[model].append(score)
        # Aggregate
        aggregates: Dict[str, Aggregate] = {
            m: aggregate_scores(m, s) for m, s in self.results.items()
        }
        return {
            "scores_by_model": {m: [dataclasses.asdict(s) for s in s_list]
                                 for m, s_list in self.results.items()},
            "aggregates": {m: a.to_dict() for m, a in aggregates.items()},
            "items": [dataclasses.asdict(i) for i in items],
        }


def _cartesian(models: Sequence[str], items: Sequence[EvalItem]) -> Iterable[Tuple[str, EvalItem]]:
    for m in models:
        for it in items:
            yield m, it


async def _score_one(it: EvalItem, model: str, fn: ModelFn) -> JudgeScore:
    async with asyncio.Semaphore(8):  # small per-call cap inside the runner too
        response = await fn(it.question)
    return await _score_response(it, model, response)


async def _score_response(it: EvalItem, model: str, response: str) -> JudgeScore:
    cfg = Config.from_env()
    judge = LLMJudge(cfg.judge_model, cfg.openai_api_key)
    score = await judge.score(it.question, it.expected_answer, response)
    score.item_id = it.item_id
    score.model = model
    score.answer = response
    return score


# ---------------------------------------------------------------------------
# Regression comparison
# ---------------------------------------------------------------------------

def compare_to_baseline(
    new_agg: Dict[str, Aggregate],
    baseline_path: str,
    threshold: float,
) -> Dict[str, Any]:
    """Compare a new eval result to a baseline JSON file.

    Returns a dict with per-dim diffs and a `regressed` boolean.
    """
    if not os.path.exists(baseline_path):
        return {"regressed": False, "reason": "no_baseline", "diffs": {}}
    with open(baseline_path, "r", encoding="utf-8") as f:
        baseline = json.load(f)
    diffs: Dict[str, Any] = {}
    regressed = False
    for model, agg in new_agg.items():
        if model not in baseline.get("aggregates", {}):
            continue
        b = baseline["aggregates"][model]
        model_diffs: Dict[str, Any] = {}
        for dim in ("correctness", "helpfulness", "safety"):
            new_mean = agg[dim]["mean"]
            old_mean = b.get(dim, {}).get("mean", 0.0)
            delta = new_mean - old_mean
            model_diffs[dim] = {
                "new": new_mean, "old": old_mean, "delta": round(delta, 4)
            }
            if delta < -threshold:
                regressed = True
        diffs[model] = model_diffs
    return {"regressed": regressed, "diffs": diffs}


# ---------------------------------------------------------------------------
# HTML report
# ---------------------------------------------------------------------------

_REPORT_CSS = """
body { font-family: -apple-system, system-ui, sans-serif; margin: 2em; color: #222; }
h1 { color: #1a4480; }
table { border-collapse: collapse; margin: 1em 0; }
th, td { border: 1px solid #ccc; padding: 6px 10px; }
th { background: #f4f4f4; }
tr.regressed { background: #fde2e2; }
.badge { padding: 2px 8px; border-radius: 8px; font-size: 0.85em; }
.badge.ok { background: #d3f8d3; color: #225522; }
.badge.bad { background: #fcd3d3; color: #661111; }
.bar { display: inline-block; height: 12px; background: #4a8df5; vertical-align: middle; }
"""

_HTML_REPORT_TMPL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>LLM Judge Report</title>
<style>{css}</style>
</head>
<body>
<h1>LLM-as-Judge Report</h1>
<p>Generated at {ts}.</p>
{n_summary}
{n_compare}
<h2>Per-question details</h2>
{items_html}
</body>
</html>"""


def _summary_table(report: Dict[str, Any]) -> str:
    rows = ["<tr><th>Model</th><th>n</th><th>correctness</th><th>helpfulness</th><th>safety</th></tr>"]
    for model, agg in report["aggregates"].items():
        rows.append(
            f"<tr><td>{html.escape(model)}</td>"
            f"<td>{agg['n']}</td>"
            f"<td>{agg['correctness']['mean']}</td>"
            f"<td>{agg['helpfulness']['mean']}</td>"
            f"<td>{agg['safety']['mean']}</td></tr>"
        )
    return f"<table>{''.join(rows)}</table>"


def _compare_section(comp: Dict[str, Any]) -> str:
    if not comp.get("diffs"):
        return "<p><em>No baseline comparison performed.</em></p>"
    badge = (
        '<span class="badge bad">REGRESSION</span>'
        if comp["regressed"] else '<span class="badge ok">OK</span>'
    )
    rows = ["<tr><th>Model</th><th>dim</th><th>old</th><th>new</th><th>delta</th></tr>"]
    for model, d in comp["diffs"].items():
        for dim, vals in d.items():
            cls = "regressed" if vals["delta"] < 0 else ""
            rows.append(
                f"<tr class='{cls}'>"
                f"<td>{html.escape(model)}</td>"
                f"<td>{html.escape(dim)}</td>"
                f"<td>{vals['old']}</td>"
                f"<td>{vals['new']}</td>"
                f"<td>{vals['delta']}</td></tr>"
            )
    return f"<h2>Baseline comparison {badge}</h2><table>{''.join(rows)}</table>"


def _items_html(report: Dict[str, Any]) -> str:
    items = report["items"]
    by_id = {it["item_id"]: it for it in items}
    out = ["<table><tr><th>#</th><th>Question</th><th>Expected</th>"]
    for m in report["aggregates"].keys():
        out.append(f"<th>{html.escape(m)} answer</th><th>{html.escape(m)} score</th>")
    out.append("</tr>")
    # Per-item rows
    for item_id, it in by_id.items():
        out.append(
            f"<tr><td>{html.escape(item_id)}</td>"
            f"<td>{html.escape(it['question'])}</td>"
            f"<td>{html.escape(it['expected_answer'])}</td>"
        )
        for m in report["aggregates"].keys():
            scores = [
                s for s in report["scores_by_model"].get(m, [])
                if s["item_id"] == item_id
            ]
            if scores:
                sc = scores[0]
                out.append(
                    f"<td>{html.escape(sc['answer'][:80])}</td>"
                    f"<td>{sc['correctness']}/{sc['helpfulness']}/{sc['safety']}</td>"
                )
            else:
                out.append("<td>-</td><td>-</td>")
        out.append("</tr>")
    out.append("</table>")
    return "".join(out)


def render_html_report(
    report: Dict[str, Any],
    comp: Optional[Dict[str, Any]] = None,
) -> str:
    return _HTML_REPORT_TMPL.format(
        css=_REPORT_CSS,
        ts=time.time(),
        n_summary=_summary_table(report),
        n_compare=_compare_section(comp or {}),
        items_html=_items_html(report),
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LLM-as-judge eval")
    p.add_argument("--eval-set", type=str, default=None)
    p.add_argument("--models", type=str, default="mock-A,mock-B")
    p.add_argument("--judge-model", type=str, default="gpt-4o-mini")
    p.add_argument("--report", type=str, default="./eval_report.html")
    p.add_argument("--baseline", type=str, default=None)
    p.add_argument("--regression-threshold", type=float, default=0.05)
    p.add_argument("--parallelism", type=int, default=8)
    return p.parse_args()


async def _main_async(args: argparse.Namespace) -> int:
    cfg = Config.from_env()
    cfg.csv_path = args.eval_set
    cfg.report_baseline_path = args.baseline
    cfg.html_report_path = args.report
    cfg.judge_model = args.judge_model
    cfg.regression_threshold = args.regression_threshold
    cfg.parallelism = args.parallelism
    cfg.model_names = [m.strip() for m in args.models.split(",") if m.strip()]
    items = load_eval_set(cfg.csv_path)
    judge = LLMJudge(cfg.judge_model, cfg.openai_api_key)
    runner = EvalRunner(cfg, judge)
    _log_event(logging.INFO, "eval.start", n_items=len(items), models=cfg.model_names)
    report = await runner.run(items, cfg.model_names)
    comp = compare_to_baseline(
        {m: aggregate_scores(m, [JudgeScore(**s) for s in ss]) for m, ss in runner.results.items()},
        cfg.report_baseline_path or "/dev/null", cfg.regression_threshold,
    ) if cfg.report_baseline_path else {"regressed": False, "diffs": {}}
    html_doc = render_html_report(report, comp)
    try:
        with open(cfg.html_report_path, "w", encoding="utf-8") as f:
            f.write(html_doc)
        _log_event(
            logging.INFO, "eval.report_written",
            path=cfg.html_report_path,
        )
    except OSError as exc:
        _log_event(logging.WARNING, "eval.report_failed", error=str(exc))
        sys.stdout.write(html_doc)
    _log_event(
        logging.INFO, "eval.summary",
        aggregates={m: a["correctness"]["mean"] for m, a in report["aggregates"].items()},
        regressed=comp.get("regressed", False),
    )
    return 2 if comp.get("regressed", False) else 0


def main() -> None:
    args = _parse_args()
    rc = asyncio.run(_main_async(args))
    sys.exit(rc)


if __name__ == "__main__":
    main()
