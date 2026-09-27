"""
Unit tests: deterministic assignment.

Properties tested:
  - Determinism: same (user, experiment) → same variant across runs
  - Uniformity: ~50/50 split for 100k users at 50/50 allocation
  - Layer independence: same user gets independent variant across layers
  - Mutex: a user is in at most one experiment per mutex group
  - Global holdout: ~5% of users in holdout; none get any experiment
  - Edge cases: zero traffic, 100% traffic
"""

import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
from assignment import (
    Experiment, Variant, assign, assign_many, is_in_global_holdout, LAYER_SALTS
)


@pytest.fixture
def binary_exp():
    return Experiment(
        experiment_id="exp_test",
        layer="layer_1_feed",
        traffic_allocation=1.0,
        variants=[Variant("control", "C", 0.5), Variant("v1", "V1", 0.5)],
    )


def test_determinism(binary_exp):
    a1 = assign("user_42", binary_exp)
    a2 = assign("user_42", binary_exp)
    a3 = assign("user_42", binary_exp)
    assert a1.variant_id == a2.variant_id == a3.variant_id
    assert a1.layer == binary_exp.layer


def test_uniformity(binary_exp):
    counts = Counter()
    for i in range(50_000):
        a = assign(f"user_{i}", binary_exp)
        counts[a.variant_id] += 1
    # Expect ~50/50, allow 1% deviation
    assert abs(counts["control"] - counts["v1"]) / 50_000 < 0.01


def test_layer_independence():
    exp1 = Experiment("exp_1", "layer_1_feed",    1.0,
                      [Variant("c", "C", 0.5), Variant("v", "V", 0.5)])
    exp2 = Experiment("exp_2", "layer_3_product", 1.0,
                      [Variant("c", "C", 0.5), Variant("v", "V", 0.5)])
    # Across 10k users, layer-independence means assignments should be uncorrelated.
    same_variant = 0
    for i in range(10_000):
        a1 = assign(f"u_{i}", exp1)
        a2 = assign(f"u_{i}", exp2)
        if a1.variant_id == a2.variant_id:
            same_variant += 1
    # Expected ~50%, allow ±3% (correlation under 1% is well within statistical noise)
    assert abs(same_variant / 10_000 - 0.5) < 0.03


def test_traffic_allocation_zero():
    exp = Experiment("exp_zero", "layer_1_feed", 0.0,
                     [Variant("c", "C", 1.0)])
    a = assign("user_1", exp)
    assert a.variant_id is None


def test_global_holdout_excludes():
    exp = Experiment("exp_x", "layer_1_feed", 1.0,
                     [Variant("c", "C", 1.0)])
    in_holdout = 0
    for i in range(20_000):
        if is_in_global_holdout(f"u_{i}"):
            in_holdout += 1
            a = assign(f"u_{i}", exp)
            assert a.variant_id is None   # user in holdout should not get experiment
    # Expect ~5% ±1%
    assert 0.04 <= in_holdout / 20_000 <= 0.06


def test_mutex_groups():
    e1 = Experiment("exp_a", "layer_1_feed", 1.0,
                    [Variant("c", "C", 0.5), Variant("v", "V", 0.5)],
                    mutex_group="group_x")
    e2 = Experiment("exp_b", "layer_1_feed", 1.0,
                    [Variant("c", "C", 0.5), Variant("v", "V", 0.5)],
                    mutex_group="group_x")

    for i in range(1_000):
        assigned = assign_many(f"u_{i}", [e1, e2])
        # At most one of the two should be assigned
        exp_ids = {a.experiment_id for a in assigned}
        assert len(exp_ids & {"exp_a", "exp_b"}) <= 1


def test_allocation_validation():
    with pytest.raises(ValueError):
        Experiment("exp_bad", "layer_1_feed", 1.0,
                   [Variant("c", "C", 0.7), Variant("v", "V", 0.7)])
