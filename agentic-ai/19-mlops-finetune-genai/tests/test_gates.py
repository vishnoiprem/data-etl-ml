"""Tests for `agent.gates` — pure functions, so this suite runs everywhere.

The contract under test: every gate returns `(allowed: bool, reason: str)`,
the reason is human-readable and names the specific limit that tripped.
"""

from __future__ import annotations

import time

import pytest

from agent.gates import (
    TrainSpend,
    cost_estimate_usd,
    per_request_cost_usd,
    retry_policy,
    train_budget,
)


class TestTrainBudget:
    def test_fresh_spend_allowed(self):
        allowed, reason = train_budget(TrainSpend(spent_usd=0.0), 200.0, 7200)
        assert allowed is True
        assert reason == "ok"

    def test_under_budget_allowed(self):
        allowed, _ = train_budget(TrainSpend(spent_usd=150.0), 200.0, 7200)
        assert allowed is True

    def test_over_usd_denied_with_reason(self):
        allowed, reason = train_budget(TrainSpend(spent_usd=250.0), 200.0, 7200)
        assert allowed is False
        assert "exceeded_budget_usd" in reason
        assert "250.00" in reason and "200.00" in reason

    def test_exactly_at_usd_cap_denied(self):
        """Boundary: == cap must deny, not allow. Off-by-one here leaks money."""
        allowed, reason = train_budget(TrainSpend(spent_usd=200.0), 200.0, 7200)
        assert allowed is False
        assert "exceeded_budget_usd" in reason

    def test_over_wall_clock_denied(self):
        stale = TrainSpend(spent_usd=1.0, started_at=time.monotonic() - 99999)
        allowed, reason = train_budget(stale, 200.0, 7200)
        assert allowed is False
        assert "exceeded_wall_clock" in reason

    def test_usd_checked_before_wallclock(self):
        """Both blown: the USD reason wins (cheaper to diagnose first)."""
        stale = TrainSpend(spent_usd=500.0, started_at=time.monotonic() - 99999)
        _, reason = train_budget(stale, 200.0, 7200)
        assert "exceeded_budget_usd" in reason


class TestRetryPolicy:
    @pytest.mark.parametrize("attempt", [0, 1, 2])
    def test_allows_below_max(self, attempt):
        allowed, reason = retry_policy(attempt, 3)
        assert allowed is True
        assert reason == "ok"

    @pytest.mark.parametrize("attempt", [3, 4, 10])
    def test_denies_at_or_above_max(self, attempt):
        allowed, reason = retry_policy(attempt, 3, "429 Too Many Requests")
        assert allowed is False
        assert "retry_exhausted" in reason
        assert "429 Too Many Requests" in reason

    def test_zero_max_denies_immediately(self):
        allowed, reason = retry_policy(0, 0)
        assert allowed is False
        assert "retry_exhausted" in reason


class TestCostMath:
    def test_known_cost(self):
        # 1000 in + 500 out at $0.18 / 1M each => 0.0018 * 0.5 = 0.00027
        assert cost_estimate_usd(1000, 500, 0.18, 0.18) == pytest.approx(0.00027)

    def test_zero_tokens_is_free(self):
        assert cost_estimate_usd(0, 0, 0.18, 0.18) == 0.0

    def test_input_and_output_prices_differ(self):
        got = cost_estimate_usd(1_000_000, 0, 0.18, 1.00)
        assert got == pytest.approx(0.18)

    def test_output_only(self):
        assert cost_estimate_usd(0, 1_000_000, 0.18, 1.00) == pytest.approx(1.00)

    def test_per_request_is_alias_of_estimate(self):
        args = (10, 20, 0.18, 0.18)
        assert per_request_cost_usd(*args) == cost_estimate_usd(*args)

    def test_negative_tokens_rejected_by_callers_not_here(self):
        # Pure function: no validation. Documented as caller responsibility.
        # This test pins the current behaviour so a future refactor is deliberate.
        assert cost_estimate_usd(-1, 0, 0.18, 0.18) < 0