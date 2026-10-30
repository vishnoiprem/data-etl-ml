"""Tests for feedback loop."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from feedback_loop import build_training_set, compute_agreement_rate


def test_build_training_set():
    labels = [
        {"content_id": "c1", "class_label": "hate_speech",
         "decision": "REMOVE", "reviewer_id": "r0", "decided_ts": 1.0},
        {"content_id": "c2", "class_label": "spam",
         "decision": "APPROVE", "reviewer_id": "r1", "decided_ts": 2.0},
    ]
    scores = {
        "c1": {"score_text": 0.7, "score_image": 0.0, "score_video": 0.0},
        "c2": {"score_text": 0.3, "score_image": 0.5, "score_video": 0.0},
    }
    examples = build_training_set(labels, scores)
    assert len(examples) == 2
    assert examples[0].label == 1
    assert examples[1].label == 0


def test_agreement_rate_full_agreement():
    per_content = {
        "c1": ["REMOVE", "REMOVE"],
        "c2": ["APPROVE", "APPROVE"],
        "c3": ["REMOVE"],
    }
    rate = compute_agreement_rate(per_content)
    assert rate == 1.0


def test_agreement_rate_disagreement():
    per_content = {
        "c1": ["REMOVE", "APPROVE"],
        "c2": ["APPROVE", "APPROVE"],
    }
    rate = compute_agreement_rate(per_content)
    assert rate == 0.5
