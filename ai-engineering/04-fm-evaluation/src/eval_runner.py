"""Eval runner — runs a candidate model against eval sets and produces a
scored report with bootstrap confidence intervals.

Regression policy:
  - For each metric, compute mean and 95% bootstrap CI on (current - baseline).
  - REGRESSION if (mean delta < -threshold) AND (CI excludes zero on the bad side).
  - PASS otherwise.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import numpy as np
from loguru import logger

from src.metrics import (
    contains, exact_match, f1_token, must_not_contain, must_refuse,
)
from src.models import CandidateModel, ModelOutput


@dataclass
class EvalScore:
    item_id: str
    task: str
    metric: str
    score: float
    pred: str
    latency_ms: int


@dataclass
class ModelRunReport:
    model_name: str
    scores: list[EvalScore] = field(default_factory=list)

    def by_metric(self) -> dict[str, np.ndarray]:
        out: dict[str, list[float]] = {}
        for s in self.scores:
            out.setdefault(s.metric, []).append(s.score)
        return {k: np.array(v, dtype=np.float64) for k, v in out.items()}

    def latencies(self) -> np.ndarray:
        return np.array([s.latency_ms for s in self.scores], dtype=np.float64)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def score_golden(model: CandidateModel, items: Sequence[dict]) -> list[EvalScore]:
    out: list[EvalScore] = []
    for item in items:
        result: ModelOutput = model(item["prompt"])
        ref = item["reference"]
        # Pick metric per task
        if item["task"] in {"extraction", "qa", "classification"}:
            score_em = exact_match(result.text, ref)
            score_f1 = f1_token(result.text, ref)
            out.append(EvalScore(item["id"], item["task"], "exact_match", score_em, result.text, result.latency_ms))
            out.append(EvalScore(item["id"], item["task"], "f1", score_f1, result.text, result.latency_ms))
        elif item["task"] == "summarization":
            # Use containment as a soft proxy
            out.append(EvalScore(item["id"], item["task"], "contains", contains(result.text, "Tesla"), result.text, result.latency_ms))
            out.append(EvalScore(item["id"], item["task"], "f1", f1_token(result.text, ref), result.text, result.latency_ms))
        else:
            out.append(EvalScore(item["id"], item["task"], "exact_match", exact_match(result.text, ref), result.text, result.latency_ms))
    return out


def score_adversarial(model: CandidateModel, items: Sequence[dict]) -> list[EvalScore]:
    out: list[EvalScore] = []
    for item in items:
        result: ModelOutput = model(item["prompt"])
        kind = item["reference_kind"]
        if kind == "must_refuse":
            score = must_refuse(result.text, result.refused)
            out.append(EvalScore(item["id"], item["task"], "refusal", score, result.text, result.latency_ms))
            if "should_contain_none_of" in item:
                score = must_not_contain(result.text, item["should_contain_none_of"])
                out.append(EvalScore(item["id"], item["task"], "no_leak", score, result.text, result.latency_ms))
        elif kind == "exact_match":
            out.append(EvalScore(item["id"], item["task"], "exact_match", exact_match(result.text, item["reference"]), result.text, result.latency_ms))
    return out


def evaluate_model(model: CandidateModel, golden: Sequence[dict], adv: Sequence[dict]) -> ModelRunReport:
    rep = ModelRunReport(model_name=model.name)
    rep.scores.extend(score_golden(model, golden))
    rep.scores.extend(score_adversarial(model, adv))
    return rep


# ---- Statistical regression detection -------------------------------------

def bootstrap_ci(values: np.ndarray, n_resamples: int = 1000, alpha: float = 0.05, seed: int = 0):
    rng = np.random.default_rng(seed)
    if len(values) == 0:
        return 0.0, 0.0, 0.0
    idx = rng.integers(0, len(values), size=(n_resamples, len(values)))
    means = values[idx].mean(axis=1)
    lo = float(np.percentile(means, 100 * alpha / 2))
    hi = float(np.percentile(means, 100 * (1 - alpha / 2)))
    return float(values.mean()), lo, hi


@dataclass
class RegressionVerdict:
    metric: str
    baseline_mean: float
    candidate_mean: float
    delta: float
    delta_lo: float
    delta_hi: float
    regression: bool
    practical: bool


def detect_regression(
    baseline: ModelRunReport,
    candidate: ModelRunReport,
    threshold: float = 0.02,
) -> list[RegressionVerdict]:
    """Per-metric regression test. Items must align (same prompts, same order)."""
    bl = baseline.by_metric()
    cd = candidate.by_metric()
    verdicts: list[RegressionVerdict] = []
    for metric in sorted(set(bl) | set(cd)):
        b = bl.get(metric, np.array([]))
        c = cd.get(metric, np.array([]))
        n = min(len(b), len(c))
        if n == 0:
            continue
        diffs = c[:n] - b[:n]                       # candidate - baseline (negative = worse)
        mean, lo, hi = bootstrap_ci(diffs)
        # Regression if mean is clearly negative (CI fully below zero) AND practically meaningful
        regressed = hi < 0 and mean < -threshold
        verdicts.append(RegressionVerdict(
            metric=metric,
            baseline_mean=float(b.mean()),
            candidate_mean=float(c.mean()),
            delta=mean, delta_lo=lo, delta_hi=hi,
            regression=regressed,
            practical=abs(mean) >= threshold,
        ))
    return verdicts
