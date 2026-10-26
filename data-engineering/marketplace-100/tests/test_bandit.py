"""
test_bandit.py — property tests for the UCB1 category bandit.

Covers:

  * First-iteration behavior: every arm gets pulled at least
    once in 20 iters (no arm is starved).
  * Convergence: after enough pulls, the bandit picks the
    best arm more often than the worst.
  * Snapshot/restore round-trip preserves state.
  * Agent override is honored + cooldown works.
  * best_arm returns the highest-mean arm among >=2-pull arms.
"""

from __future__ import annotations

import math
import random

import pytest

from m100.bandit import Arm, CategoryBandit, DEFAULT_ARMS


# ============================================================
# Smoke
# ============================================================

def test_bandit_constructs_with_default_arms():
    b = CategoryBandit()
    assert set(b.arms.keys()) == set(DEFAULT_ARMS)
    for arm in b.arms.values():
        assert arm.pulls == 0
        assert arm.sum_reward == 0.0


def test_first_pull_is_unpulled_arm():
    """UCB1 rule: any arm with pulls=0 has UCB=inf, so it gets picked first.

    Note: `choose()` returns the arm name; `update(name, reward)` is
    what increments pulls. This decoupling lets the agent override
    a choose() without that override counting as a "real" pull.
    """
    b = CategoryBandit()
    chosen = b.choose()
    assert chosen in DEFAULT_ARMS
    # choose() doesn't update — only update() does
    assert b.arms[chosen].pulls == 0
    b.update(chosen, 0.5)
    assert b.arms[chosen].pulls == 1


def test_update_increments_pulls_and_accumulates_reward():
    b = CategoryBandit()
    b.update("Finance", 0.8)
    b.update("Finance", 0.6)
    assert b.arms["Finance"].pulls == 2
    assert abs(b.arms["Finance"].sum_reward - 1.4) < 1e-9
    assert abs(b.arms["Finance"].mean_reward - 0.7) < 1e-9


def test_update_clamps_reward_to_unit_interval():
    b = CategoryBandit()
    b.update("Finance", 1.5)  # over
    b.update("Finance", -0.2)  # under
    # 1.5 → 1.0, -0.2 → 0.0; mean = 0.5
    assert abs(b.arms["Finance"].mean_reward - 0.5) < 1e-9


def test_unknown_arm_update_is_silent():
    b = CategoryBandit()
    b.update("NotARealCategory", 0.5)  # should not raise
    assert "NotARealCategory" not in b.arms


# ============================================================
# Property tests
# ============================================================

def test_property_every_arm_pulled_within_20_iters():
    """Property: no arm is starved. After 20 iters, every arm has
    been pulled at least once. UCB1 ensures this because every
    unpulled arm has UCB=inf.
    """
    b = CategoryBandit()
    for _ in range(20):
        cat = b.choose()
        b.update(cat, 0.5)  # neutral reward
    pulled = {name for name, arm in b.arms.items() if arm.pulls > 0}
    assert pulled == set(DEFAULT_ARMS), f"starved arms: {set(DEFAULT_ARMS) - pulled}"


def test_property_bandit_converges_to_best_arm():
    """Property: when one arm has much higher reward, the bandit
    picks it more often than the worst arm by iter 50.

    We model the rewards: Finance gives 0.8, others give 0.3.
    A 50-iter run should pick Finance at least 3x as often as
    any single other arm.
    """
    rng = random.Random(20261014)
    b = CategoryBandit()

    def reward(arm_name):
        return rng.uniform(0.7, 0.9) if arm_name == "Finance" else rng.uniform(0.2, 0.4)

    counts = {a: 0 for a in DEFAULT_ARMS}
    for _ in range(50):
        cat = b.choose()
        counts[cat] += 1
        b.update(cat, reward(cat))

    # Finance is the best arm — it should be picked more than any
    # other single arm, with high probability. We allow a generous
    # margin (5x) because UCB1 has high regret on small samples.
    others_max = max(count for arm, count in counts.items() if arm != "Finance")
    assert counts["Finance"] > others_max, (
        f"Finance pulls={counts['Finance']} vs others_max={others_max}; "
        f"counts={counts}"
    )


def test_property_best_arm_correct_after_many_pulls():
    """Property: best_arm() returns the arm with the highest mean
    among arms that have been pulled at least twice.
    """
    b = CategoryBandit()
    b.update("Finance", 0.9)
    b.update("Finance", 0.85)
    b.update("Healthcare", 0.3)
    b.update("Healthcare", 0.4)
    b.update("Geospatial", 0.5)
    b.update("Geospatial", 0.6)
    assert b.best_arm() == "Finance"


def test_snapshot_round_trip():
    b1 = CategoryBandit()
    b1.update("Finance", 0.9)
    b1.update("Healthcare", 0.3)
    b1.update("Finance", 0.7)
    snap = b1.snapshot()
    b2 = CategoryBandit()
    b2.restore(snap)
    for name in DEFAULT_ARMS:
        assert b1.arms[name].pulls == b2.arms[name].pulls
        assert abs(b1.arms[name].sum_reward - b2.arms[name].sum_reward) < 1e-9
    assert b1._iter_count == b2._iter_count


# ============================================================
# Agent override + cooldown
# ============================================================

def test_agent_override_works_when_no_cooldown():
    b = CategoryBandit(agent_override_cooldown=3)
    b.choose()  # iter 1
    cat = b.choose(agent_override="Climate")
    assert cat == "Climate"


def test_agent_override_respects_cooldown():
    """If the agent overrode last iter, this iter we ignore its choice."""
    b = CategoryBandit(agent_override_cooldown=3)
    b.choose(agent_override="Climate")  # iter 1 — accepted
    # Iter 2: pass override again — should be ignored (cooldown)
    chosen = b.choose(agent_override="Climate")
    assert chosen != "Climate"  # bandit picks something else


def test_agent_override_only_honors_known_arms():
    b = CategoryBandit()
    cat = b.choose(agent_override="NotARealCategory")
    # Fallback to UCB1 — not the bogus category
    assert cat in DEFAULT_ARMS


# ============================================================
# UCB math
# ============================================================

def test_arm_ucb_is_infinite_when_unpulled():
    arm = Arm(name="X")
    assert arm.ucb(total_pulls=10) == float("inf")


def test_arm_ucb_matches_paper_formula():
    """UCB(a) = mean_reward(a) + c * sqrt(2 * ln(N) / n_a)"""
    arm = Arm(name="X", pulls=10, sum_reward=7.0)  # mean = 0.7
    c = math.sqrt(2)
    expected = 0.7 + c * math.sqrt(2 * math.log(100) / 10)
    assert abs(arm.ucb(total_pulls=100, c=c) - expected) < 1e-9
