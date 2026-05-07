"""Drift detection — three signals.

1. Topic drift  — KL divergence between current and baseline intent distributions
2. Length drift — KS-style statistic between input/output token distributions
3. Quality drift — CUSUM (cumulative sum) on rolling LLM-judge scores

All three return a normalized statistic + a boolean `alarm` flag.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class DriftReport:
    metric: str
    value: float
    threshold: float
    alarm: bool


def kl_divergence(p: dict[str, float], q: dict[str, float], eps: float = 1e-9) -> float:
    """KL(P || Q) over a discrete categorical distribution."""
    keys = set(p) | set(q)
    pv = np.array([p.get(k, eps) for k in keys])
    qv = np.array([q.get(k, eps) for k in keys])
    pv = pv / pv.sum()
    qv = qv / qv.sum()
    return float(np.sum(pv * np.log(pv / qv)))


def topic_drift(baseline_dist: dict[str, float], current_dist: dict[str, float],
                threshold: float = 0.20) -> DriftReport:
    kl = kl_divergence(current_dist, baseline_dist)
    return DriftReport(metric="topic_drift_kl", value=kl, threshold=threshold,
                       alarm=kl > threshold)


def length_drift(baseline_tokens: list[int], current_tokens: list[int],
                 threshold: float = 0.20) -> DriftReport:
    """KS-like: max abs difference of empirical CDFs."""
    if not baseline_tokens or not current_tokens:
        return DriftReport(metric="length_drift_ks", value=0.0, threshold=threshold, alarm=False)
    grid = sorted(set(baseline_tokens) | set(current_tokens))
    b = np.array(baseline_tokens, dtype=float)
    c = np.array(current_tokens, dtype=float)
    cdf_b = np.array([(b <= x).mean() for x in grid])
    cdf_c = np.array([(c <= x).mean() for x in grid])
    ks = float(np.max(np.abs(cdf_b - cdf_c)))
    return DriftReport(metric="length_drift_ks", value=ks, threshold=threshold, alarm=ks > threshold)


def quality_drift_cusum(scores: list[float], target: float = 0.85,
                        k: float = 0.02, h: float = 0.5) -> DriftReport:
    """CUSUM downward drift detector.

    Tracks the cumulative deviation below (target - k). Alarms when it exceeds h.
    """
    s = 0.0
    peak = 0.0
    for x in scores:
        s = max(0.0, s + (target - k) - x)
        peak = max(peak, s)
    return DriftReport(metric="quality_drift_cusum", value=peak, threshold=h, alarm=peak > h)
