"""Tests for the Twitter sentiment scorer (mocked pipeline).

Author: Prem Vishnoi <pvishnoi@avilx.com>

The cardiffnlp model uses LABEL_0 (negative) / LABEL_1 (neutral) /
LABEL_2 (positive). The scorer accepts both that format and the
FinBERT-style "positive"/"negative"/"neutral" labels for back-compat.
"""
from __future__ import annotations

import sys

import pytest

# ── Stubs ────────────────────────────────────────────────────────────────

class _StubResult:
    """One inner-list per text: [{'label':..., 'score':...}, ...]"""

    def __init__(self, per_text):
        self.per_text = per_text


def _stub_pipeline_factory(per_text_responses: list[list[dict]]):
    """Build a fake transformers.pipeline that returns canned outputs in order."""
    state = {"i": 0, "calls": []}

    def fake_pipeline(*args, **kwargs):
        def _fn(texts, batch_size=None, **_kw):
            state["calls"].append(list(texts))
            out = []
            for t in texts:
                if state["i"] >= len(per_text_responses):
                    raise RuntimeError("out of canned responses")
                out.append(per_text_responses[state["i"]])
                state["i"] += 1
            return out

        return _fn

    return fake_pipeline, state


def _install_fake_pipeline(monkeypatch, responses):
    fake_pipeline, state = _stub_pipeline_factory(responses)

    class _FakeTransformers:
        @staticmethod
        def pipeline(*args, **kwargs):
            return fake_pipeline(*args, **kwargs)

    sys.modules["transformers"] = _FakeTransformers
    return state


# ── Tests ────────────────────────────────────────────────────────────────

def test_positive_text_scores_positive(monkeypatch):
    from src.ml.sentiment import TwitterSentimentScorer
    # cardiffnlp format
    state = _install_fake_pipeline(monkeypatch, [
        [{"label": "LABEL_2", "score": 0.93},
         {"label": "LABEL_0", "score": 0.04},
         {"label": "LABEL_1", "score": 0.03}],
    ])
    s = TwitterSentimentScorer()
    scores = s.score(["The new LLM is going to change everything!"])
    assert len(scores) == 1
    assert scores[0] == pytest.approx(0.89, abs=1e-6)
    assert state["calls"] == [["The new LLM is going to change everything!"]]


def test_negative_text_scores_negative(monkeypatch):
    from src.ml.sentiment import TwitterSentimentScorer
    _install_fake_pipeline(monkeypatch, [
        [{"label": "LABEL_2", "score": 0.02},
         {"label": "LABEL_0", "score": 0.95},
         {"label": "LABEL_1", "score": 0.03}],
    ])
    s = TwitterSentimentScorer()
    scores = s.score(["This launch was a complete disaster"])
    assert scores[0] == pytest.approx(-0.93, abs=1e-6)


def test_neutral_text_scores_zero(monkeypatch):
    from src.ml.sentiment import TwitterSentimentScorer
    _install_fake_pipeline(monkeypatch, [
        [{"label": "LABEL_2", "score": 0.10},
         {"label": "LABEL_0", "score": 0.10},
         {"label": "LABEL_1", "score": 0.80}],
    ])
    s = TwitterSentimentScorer()
    scores = s.score(["Today's meeting is at 3pm"])
    assert scores[0] == pytest.approx(0.0, abs=1e-6)


def test_empty_list_returns_empty(monkeypatch):
    from src.ml.sentiment import TwitterSentimentScorer
    # Pipeline should never be called
    state = _install_fake_pipeline(monkeypatch, [])
    s = TwitterSentimentScorer()
    assert s.score([]) == []
    assert state["calls"] == []


def test_batch_handles_multiple_texts(monkeypatch):
    from src.ml.sentiment import TwitterSentimentScorer
    _install_fake_pipeline(monkeypatch, [
        [{"label": "LABEL_2", "score": 0.9},
         {"label": "LABEL_0", "score": 0.05},
         {"label": "LABEL_1", "score": 0.05}],
        [{"label": "LABEL_2", "score": 0.1},
         {"label": "LABEL_0", "score": 0.85},
         {"label": "LABEL_1", "score": 0.05}],
        [{"label": "LABEL_2", "score": 0.3},
         {"label": "LABEL_0", "score": 0.3},
         {"label": "LABEL_1", "score": 0.4}],
    ])
    s = TwitterSentimentScorer()
    scores = s.score(["good!", "bad!", "meh"])
    assert len(scores) == 3
    assert scores[0] > 0
    assert scores[1] < 0
    assert scores[2] == pytest.approx(0.0, abs=1e-6)


def test_combine_handles_missing_labels(monkeypatch):
    from src.ml.sentiment import TwitterSentimentScorer
    # Only positive + negative; no neutral label
    _install_fake_pipeline(monkeypatch, [
        [{"label": "LABEL_2", "score": 0.7},
         {"label": "LABEL_0", "score": 0.3}],
    ])
    s = TwitterSentimentScorer()
    assert s.score(["x"])[0] == pytest.approx(0.4, abs=1e-6)


def test_backward_compat_with_finbert_labels(monkeypatch):
    """If a test or alternate code path still emits FinBERT-style labels
    (positive/negative/neutral), the scorer still works."""
    from src.ml.sentiment import TwitterSentimentScorer
    _install_fake_pipeline(monkeypatch, [
        [{"label": "positive", "score": 0.8},
         {"label": "negative", "score": 0.1},
         {"label": "neutral",  "score": 0.1}],
    ])
    s = TwitterSentimentScorer()
    assert s.score(["hi"])[0] == pytest.approx(0.7, abs=1e-6)


def test_default_model_name_is_cardiffnlp():
    from src.ml.sentiment import TwitterSentimentScorer
    s = TwitterSentimentScorer()
    assert "twitter-roberta" in s.model_name
    assert s.model_name == "cardiffnlp/twitter-roberta-base-sentiment-latest"


def test_finbert_alias_still_works():
    """The old FinBERTScorer name should still importable as an alias
    so any older code keeps working."""
    from src.ml.sentiment import FinBERTScorer, TwitterSentimentScorer
    assert FinBERTScorer is TwitterSentimentScorer