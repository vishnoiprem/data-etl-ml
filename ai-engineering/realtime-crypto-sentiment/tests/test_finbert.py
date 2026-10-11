"""Tests for the FinBERT scorer (mocked pipeline).

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""
from __future__ import annotations

import sys
from typing import List

import pytest


# ── Stubs ────────────────────────────────────────────────────────────────

class _StubResult:
    """One inner-list per text: [{'label':..., 'score':...}, ...]"""

    def __init__(self, per_text):
        self.per_text = per_text


def _stub_pipeline_factory(per_text_responses: List[List[dict]]):
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
    from src.ml.finbert import FinBERTScorer
    state = _install_fake_pipeline(monkeypatch, [
        [{"label": "positive", "score": 0.93},
         {"label": "negative", "score": 0.04},
         {"label": "neutral", "score": 0.03}],
    ])
    s = FinBERTScorer()
    scores = s.score(["Bitcoin is going to the moon!"])
    assert len(scores) == 1
    assert scores[0] == pytest.approx(0.89, abs=1e-6)
    assert state["calls"] == [["Bitcoin is going to the moon!"]]


def test_negative_text_scores_negative(monkeypatch):
    from src.ml.finbert import FinBERTScorer
    _install_fake_pipeline(monkeypatch, [
        [{"label": "positive", "score": 0.02},
         {"label": "negative", "score": 0.95},
         {"label": "neutral", "score": 0.03}],
    ])
    s = FinBERTScorer()
    scores = s.score(["ETH crashing, exit now"])
    assert scores[0] == pytest.approx(-0.93, abs=1e-6)


def test_neutral_text_scores_zero(monkeypatch):
    from src.ml.finbert import FinBERTScorer
    _install_fake_pipeline(monkeypatch, [
        [{"label": "positive", "score": 0.10},
         {"label": "negative", "score": 0.10},
         {"label": "neutral", "score": 0.80}],
    ])
    s = FinBERTScorer()
    scores = s.score(["$BTC trades sideways near 67k"])
    assert scores[0] == pytest.approx(0.0, abs=1e-6)


def test_empty_list_returns_empty(monkeypatch):
    from src.ml.finbert import FinBERTScorer
    # Pipeline should never be called
    state = _install_fake_pipeline(monkeypatch, [])
    s = FinBERTScorer()
    assert s.score([]) == []
    assert state["calls"] == []


def test_batch_handles_multiple_texts(monkeypatch):
    from src.ml.finbert import FinBERTScorer
    _install_fake_pipeline(monkeypatch, [
        [{"label": "positive", "score": 0.9},
         {"label": "negative", "score": 0.05},
         {"label": "neutral", "score": 0.05}],
        [{"label": "positive", "score": 0.1},
         {"label": "negative", "score": 0.85},
         {"label": "neutral", "score": 0.05}],
        [{"label": "positive", "score": 0.3},
         {"label": "negative", "score": 0.3},
         {"label": "neutral", "score": 0.4}],
    ])
    s = FinBERTScorer()
    scores = s.score(["good!", "bad!", "meh"])
    assert len(scores) == 3
    assert scores[0] > 0
    assert scores[1] < 0
    assert scores[2] == pytest.approx(0.0, abs=1e-6)


def test_combine_handles_missing_labels(monkeypatch):
    from src.ml.finbert import FinBERTScorer
    # Only positive + negative; no neutral label
    _install_fake_pipeline(monkeypatch, [
        [{"label": "positive", "score": 0.7},
         {"label": "negative", "score": 0.3}],
    ])
    s = FinBERTScorer()
    assert s.score(["x"])[0] == pytest.approx(0.4, abs=1e-6)
