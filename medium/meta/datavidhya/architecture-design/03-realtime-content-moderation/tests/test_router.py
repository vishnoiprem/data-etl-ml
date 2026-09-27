"""Tests for confidence router."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from scoring_aggregator import AggregatedDecision, ClassScore
from confidence_router import route


def test_severe_high_confidence_auto_removes():
    dec = AggregatedDecision("c1", [ClassScore("csam", "SEVERE",
                                                score_text=0.96, score_image=0.95)])
    out = route(dec)
    assert out[0].route == "AUTO_REMOVE"
    assert out[0].severity == "SEVERE"


def test_harmful_borderline_goes_to_human():
    dec = AggregatedDecision("c1", [ClassScore("hate_speech", "HARMFUL", score_text=0.5)])
    out = route(dec)
    assert out[0].route == "HUMAN_REVIEW"
    assert out[0].priority == 1


def test_safe_low_score_auto_approves():
    dec = AggregatedDecision("c1", [ClassScore("safe", "SAFE", score_text=0.05)])
    out = route(dec)
    assert out[0].route == "AUTO_APPROVE"


def test_borderline_never_auto_removed():
    dec = AggregatedDecision("c1", [ClassScore("mild_nudity", "BORDERLINE", score_text=0.95)])
    out = route(dec)
    assert out[0].route == "HUMAN_REVIEW"
    assert out[0].severity == "BORDERLINE"


def test_no_scores_safe_default():
    dec = AggregatedDecision("c1", [])
    out = route(dec)
    assert out[0].route == "AUTO_APPROVE"
