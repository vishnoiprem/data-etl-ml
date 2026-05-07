from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from src.eval_runner import bootstrap_ci, detect_regression, evaluate_model, load_jsonl
from src.metrics import exact_match, f1_token, must_refuse
from src.models import BaselineModel, RegressionModel


ROOT = Path(__file__).resolve().parent.parent


def test_exact_match():
    assert exact_match("AUT-2024-001", "AUT-2024-001") == 1.0
    assert exact_match("aut-2024-001", "AUT-2024-001") == 1.0   # case-insensitive
    assert exact_match("X", "Y") == 0.0


def test_f1_token():
    assert f1_token("the cat sat", "the cat sat") == 1.0
    assert 0.0 < f1_token("the cat", "a black cat") < 1.0


def test_must_refuse():
    assert must_refuse("I can't share that.", False) == 1.0
    assert must_refuse("Sure, here it is.", False) == 0.0
    assert must_refuse("anything", True) == 1.0


def test_bootstrap_ci():
    rng = np.random.default_rng(0)
    vals = rng.normal(0.5, 0.1, 200)
    mean, lo, hi = bootstrap_ci(vals)
    assert lo < mean < hi


def test_eval_pipeline_detects_regression():
    golden = load_jsonl(ROOT / "sample_data" / "golden.jsonl")
    adv = load_jsonl(ROOT / "sample_data" / "adversarial.jsonl")
    baseline = evaluate_model(BaselineModel(), golden, adv)
    candidate = evaluate_model(RegressionModel(), golden, adv)
    verdicts = detect_regression(baseline, candidate, threshold=0.05)
    assert any(v.regression for v in verdicts), "should flag at least one regression"
