"""
Tests for the Sales Coach
=========================
Run:  pytest tests/
"""

import os
import pytest


# =============================================================================
# UNIT TESTS (no API calls)
# =============================================================================

def test_callanalysis_schema_validates():
    from analyzer import CallAnalysis, Objection, KeyMoment, SentimentSegment
    sample = {
        "summary": "Discovery call with Acme.",
        "outcome": "follow_up_scheduled",
        "talk_ratio_rep_pct": 55.0,
        "pace_wpm": 145.0,
        "objections": [
            {"type": "price", "timestamp": 320.5, "prospect_quote": "It's expensive", "rep_response": "Let's compare", "resolved": True}
        ],
        "key_moments": [
            {"timestamp": 100.0, "label": "demo walkthrough", "importance": 4, "quote": "show me how it works"}
        ],
        "sentiment_segments": [
            {"start_s": 0, "end_s": 200, "sentiment": "neutral", "score": 0.1}
        ],
        "discovery_questions_asked": 7,
        "next_steps_defined": True,
    }
    parsed = CallAnalysis.model_validate(sample)
    assert parsed.outcome == "follow_up_scheduled"
    assert len(parsed.objections) == 1


def test_coachingfeedback_schema_validates():
    from feedback_engine import CoachingFeedback, RubricScore
    sample = {
        "scores": {"rapport": 8, "discovery": 7, "objection_handling": 6, "value_communication": 7, "close": 5},
        "overall": 7,
        "top_wins": ["Asked open questions", "Mirrored prospect language", "Summarized at midpoint"],
        "top_improvements": [
            {"issue": "Weak close", "timestamp": 540.0, "suggestion": "Ask for the next step explicitly"}
        ],
        "drill": "Practice the 'assumptive close' for 5 minutes.",
    }
    parsed = CoachingFeedback.model_validate(sample)
    assert parsed.scores.rapport == 8
    assert parsed.drill.startswith("Practice")


# =============================================================================
# INTEGRATION TESTS (require API key)
# =============================================================================

SAMPLE_TRANSCRIPT = {
    "text": "Hi, this is Sarah from Acme. Thanks for taking the call. I'm curious about your product. How does pricing work? It's a bit more than we budgeted. Can you send me a deck? Sure, I'll follow up next week.",
    "language": "en",
    "duration_s": 90.0,
    "segments": [
        {"start": 0.0, "end": 5.0, "text": "Hi, this is Sarah from Acme."},
        {"start": 5.0, "end": 15.0, "text": "Thanks for taking the call."},
        {"start": 15.0, "end": 30.0, "text": "I'm curious about your product."},
        {"start": 30.0, "end": 50.0, "text": "How does pricing work?"},
        {"start": 50.0, "end": 70.0, "text": "It's a bit more than we budgeted."},
        {"start": 70.0, "end": 85.0, "text": "Can you send me a deck?"},
        {"start": 85.0, "end": 90.0, "text": "Sure, I'll follow up next week."},
    ],
}


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
def test_analyze_call():
    from analyzer import analyze_call
    analysis, cost = analyze_call(SAMPLE_TRANSCRIPT, os.environ["OPENAI_API_KEY"])
    assert "summary" in analysis
    assert "objections" in analysis
    assert cost > 0
    assert cost < 0.5  # sanity


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
def test_generate_feedback():
    from feedback_engine import generate_feedback
    sample_analysis = {
        "summary": "Discovery call with pricing concern.",
        "outcome": "follow_up_scheduled",
        "talk_ratio_rep_pct": 50.0,
        "pace_wpm": 120.0,
        "objections": [{"type": "price", "timestamp": 50.0, "prospect_quote": "It's expensive", "resolved": False}],
        "key_moments": [],
        "sentiment_segments": [{"start_s": 0, "end_s": 90, "sentiment": "neutral", "score": 0.0}],
        "discovery_questions_asked": 2,
        "next_steps_defined": True,
    }
    feedback, cost = generate_feedback(sample_analysis, SAMPLE_TRANSCRIPT, os.environ["OPENAI_API_KEY"])
    assert "scores" in feedback
    assert "top_wins" in feedback
    assert cost > 0
    assert cost < 0.05
