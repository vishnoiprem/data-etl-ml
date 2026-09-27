"""
Score Aggregator — combines multi-modal model outputs into a single decision.

Strategy:
  - SEVERE classes: take the WORST (max) score across modalities → minimize FN
  - SAFE classes:   take the BEST (min) score across modalities → minimize FP
  - Default:        weighted average

For demo: produces a synthetic per-modality score; in prod these come from
real model inference endpoints (TF Serving / Triton).
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


SEVERITY_CLASSES = ["SEVERE", "HARMFUL", "BORDERLINE", "SAFE"]


@dataclass
class ClassScore:
    class_label: str
    severity: str               # one of SEVERITY_CLASSES
    score_text:  float = 0.0    # 0..1
    score_image: float = 0.0
    score_video: float = 0.0
    is_appeal:   bool = False

    @property
    def aggregated(self) -> float:
        scores = [s for s in (self.score_text, self.score_image, self.score_video) if s > 0]
        if not scores:
            return 0.0
        if self.severity == "SEVERE":
            return max(scores)       # worst case → minimize FN
        if self.severity == "SAFE":
            return min(scores)       # best case → minimize FP
        return sum(scores) / len(scores)


@dataclass
class AggregatedDecision:
    content_id: str
    class_scores: List[ClassScore] = field(default_factory=list)

    @property
    def top_class(self) -> Optional[ClassScore]:
        if not self.class_scores:
            return None
        return max(self.class_scores, key=lambda c: c.aggregated)


def aggregate(content_id: str, class_scores: List[ClassScore]) -> AggregatedDecision:
    return AggregatedDecision(content_id=content_id, class_scores=class_scores)


# --------------------------------------------------------------------- #
# Demo: generate synthetic content + scores
# --------------------------------------------------------------------- #

def demo(n: int = 50, out: str = "sample_data/content.jsonl"):
    rng = random.Random(42)
    class_catalog = [
        ("hate_speech",       "HARMFUL"),
        ("harassment",        "HARMFUL"),
        ("nudity_adult",      "HARMFUL"),
        ("violence_gore",     "HARMFUL"),
        ("csam",              "SEVERE"),
        ("terrorism",         "SEVERE"),
        ("self_harm",         "SEVERE"),
        ("mild_nudity",       "BORDERLINE"),
        ("political_misinfo", "BORDERLINE"),
        ("spam",              "BORDERLINE"),
        ("safe",              "SAFE"),
    ]
    with open(out, "w") as f:
        for i in range(n):
            label, sev = rng.choice(class_catalog)
            score = rng.uniform(0.05, 0.99)
            ev = {
                "content_id": f"c_{i:06d}",
                "user_id":    f"user_{rng.randint(1, 1000):06d}",
                "type":       rng.choice(["text", "image", "video"]),
                "class_scores": [{
                    "class_label":  label,
                    "severity":     sev,
                    "score_text":   rng.uniform(0, 0.99),
                    "score_image":  rng.uniform(0, 0.99) if rng.random() > 0.4 else 0.0,
                    "score_video":  rng.uniform(0, 0.99) if rng.random() > 0.7 else 0.0,
                }],
            }
            f.write(json.dumps(ev) + "\n")
    print(f"Wrote {n} content items to {out}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--demo", action="store_true")
    p.add_argument("--n", type=int, default=50)
    p.add_argument("--out", default="sample_data/content.jsonl")
    args = p.parse_args()
    if args.demo:
        demo(args.n, args.out)
