"""
Feedback Loop — converts human review labels into model retraining data.

Pipeline:
  1. Collect human decisions from review_queue
  2. Join with original model scores + features
  3. Build labeled training set (binary per class)
  4. Trigger nightly retraining job (in prod: Airflow + Vertex AI / Sagemaker)
  5. Shadow-deploy new model; canary at 5%
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class TrainingExample:
    content_id: str
    class_label: str
    features_text:  Optional[str]
    features_image: Optional[str]
    score_text:  float
    score_image: float
    score_video: float
    label: int              # 1 = harmful, 0 = safe
    reviewer_id: str
    decided_ts: float


def build_training_set(human_labels: List[dict],
                       content_scores: Dict[str, dict]) -> List[TrainingExample]:
    examples = []
    for label in human_labels:
        cid = label["content_id"]
        if cid not in content_scores:
            continue
        sc = content_scores[cid]
        examples.append(TrainingExample(
            content_id=cid,
            class_label=label["class_label"],
            features_text=sc.get("features_text"),
            features_image=sc.get("features_image"),
            score_text=sc.get("score_text", 0.0),
            score_image=sc.get("score_image", 0.0),
            score_video=sc.get("score_video", 0.0),
            label=1 if label["decision"] == "REMOVE" else 0,
            reviewer_id=label["reviewer_id"],
            decided_ts=label.get("decided_ts", time.time()),
        ))
    return examples


# --------------------------------------------------------------------- #
# Inter-reviewer agreement check (triggers senior review + model flag)
# --------------------------------------------------------------------- #

def compute_agreement_rate(per_content: Dict[str, List[str]]) -> float:
    agree = 0
    total = 0
    for decisions in per_content.values():
        if len(decisions) < 2:
            continue
        total += 1
        if len(set(decisions)) == 1:
            agree += 1
    return agree / max(total, 1)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--labels", default="sample_data/human_labels.jsonl")
    args = p.parse_args()

    labels = [json.loads(l) for l in Path(args.labels).read_text().splitlines() if l.strip()]
    print(f"Loaded {len(labels)} human labels")

    # Synthetic scores (real prod: join against content_scores table)
    scores = {l["content_id"]: {
        "score_text":  0.5,
        "score_image": 0.3,
        "score_video": 0.0,
    } for l in labels}

    examples = build_training_set(labels, scores)
    pos = sum(1 for e in examples if e.label == 1)
    neg = sum(1 for e in examples if e.label == 0)
    print(f"Training set: {len(examples)} examples ({pos} positive, {neg} negative)")
