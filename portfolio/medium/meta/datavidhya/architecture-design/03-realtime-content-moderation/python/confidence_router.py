"""
Confidence Router — picks AUTO_REMOVE / HUMAN_REVIEW / AUTO_APPROVE.

Severity-aware thresholds:
  - SEVERE:    very low bar for auto-remove (FN cost >> FP cost)
  - HARMFUL:   medium bar
  - BORDERLINE: only humans can decide
  - SAFE:      very low bar for auto-approve (FP cost >> FN cost)
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

from scoring_aggregator import AggregatedDecision, ClassScore, SEVERITY_CLASSES


# Per-severity-class decision thresholds
THRESHOLDS = {
    # (auto_remove_min, human_review_min)
    "SEVERE":    (0.20, 0.05),    # very aggressive auto-remove
    "HARMFUL":   (0.85, 0.40),
    "BORDERLINE": (1.10, 0.50),  # never auto-remove borderline
    "SAFE":      (1.10, 0.30),    # never auto-remove safe; auto-approve unless concerning
}


@dataclass
class RouteDecision:
    content_id: str
    route: str                     # AUTO_REMOVE | HUMAN_REVIEW | AUTO_APPROVE
    severity: str
    confidence: float
    class_label: str
    sla_minutes: int               # for HUMAN_REVIEW

    @property
    def priority(self) -> int:
        return {
            "AUTO_REMOVE":   -1,
            "AUTO_APPROVE":  99,
            "HUMAN_REVIEW":  {"SEVERE": 0, "HARMFUL": 1, "BORDERLINE": 2}[self.severity],
        }.get(self.route, 5)


def route(decision: AggregatedDecision) -> List[RouteDecision]:
    out = []
    top = decision.top_class
    if top is None:
        return [RouteDecision(decision.content_id, "AUTO_APPROVE", "SAFE", 0.0, "safe", 0)]

    auto_remove_min, human_review_min = THRESHOLDS[top.severity]
    score = top.aggregated

    if top.severity == "SEVERE" and score >= 0.95:
        # Very high confidence on severe → instant auto-remove + NCMEC report
        return [RouteDecision(decision.content_id, "AUTO_REMOVE", top.severity, score,
                              top.class_label, 0)]
    if score >= auto_remove_min:
        return [RouteDecision(decision.content_id, "AUTO_REMOVE", top.severity, score,
                              top.class_label, 0)]
    if score >= human_review_min:
        sla = {0: 5, 1: 30, 2: 240}[{"SEVERE": 0, "HARMFUL": 1, "BORDERLINE": 2}[top.severity]]
        return [RouteDecision(decision.content_id, "HUMAN_REVIEW", top.severity, score,
                              top.class_label, sla)]
    return [RouteDecision(decision.content_id, "AUTO_APPROVE", top.severity, score,
                          top.class_label, 0)]


# --------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------- #

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="sample_data/content.jsonl")
    args = p.parse_args()

    auto_r, human_q, auto_a = 0, 0, 0
    for line in Path(args.input).read_text().splitlines():
        if not line.strip():
            continue
        ev = json.loads(line)
        cs = [ClassScore(**c) for c in ev["class_scores"]]
        agg = AggregatedDecision(content_id=ev["content_id"], class_scores=cs)
        routed = route(agg)
        d = routed[0]
        if d.route == "AUTO_REMOVE":
            auto_r += 1
        elif d.route == "HUMAN_REVIEW":
            human_q += 1
        else:
            auto_a += 1

    total = auto_r + human_q + auto_a
    print(f"Total: {total}")
    print(f"  AUTO_REMOVE:   {auto_r}  ({100*auto_r/total:.1f}%)")
    print(f"  HUMAN_REVIEW:  {human_q} ({100*human_q/total:.1f}%)")
    print(f"  AUTO_APPROVE:  {auto_a}  ({100*auto_a/total:.1f}%)")
