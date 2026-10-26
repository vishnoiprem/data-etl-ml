"""Tests for the risk-budget gates. Pure functions, no broker, no LLM."""

from __future__ import annotations

import pytest

from shared.budget import (
    MAX_DRAWDOWN_PCT,
    MAX_GROSS_EXPOSURE,
    MAX_POSITION_PCT,
    MAX_TRADES_PER_DAY,
    SLIPPAGE_WARN_PCT,
    check_drawdown,
    check_gross_exposure,
    check_position_size,
    check_slippage,
    check_trade_count,
)


# ----- position size -----------------------------------------------------


def test_position_size_allows_under_limit() -> None:
    assert check_position_size(4_900.0, nav=100_000.0).allowed


def test_position_size_allows_exactly_at_limit() -> None:
    assert check_position_size(100_000.0 * MAX_POSITION_PCT, nav=100_000.0).allowed


def test_position_size_denies_over_limit() -> None:
    res = check_position_size(6_000.0, nav=100_000.0)
    assert not res.allowed
    assert "exceeds" in res.reason


def test_position_size_allows_zero() -> None:
    assert check_position_size(0.0, nav=100_000.0).allowed


def test_position_size_denies_nonpositive_nav() -> None:
    assert not check_position_size(100.0, nav=0.0).allowed


# ----- gross exposure ----------------------------------------------------


def test_gross_exposure_allows_under_limit() -> None:
    assert check_gross_exposure(140_000.0, nav=100_000.0).allowed


def test_gross_exposure_allows_exactly_at_limit() -> None:
    assert check_gross_exposure(100_000.0 * MAX_GROSS_EXPOSURE, 100_000.0).allowed


def test_gross_exposure_denies_over_limit() -> None:
    assert not check_gross_exposure(200_000.0, nav=100_000.0).allowed


# ----- drawdown ----------------------------------------------------------


def test_drawdown_allows_under_limit() -> None:
    assert check_drawdown(MAX_DRAWDOWN_PCT - 0.01).allowed


def test_drawdown_allows_exactly_at_limit() -> None:
    assert check_drawdown(MAX_DRAWDOWN_PCT).allowed


def test_drawdown_denies_over_limit() -> None:
    res = check_drawdown(0.09)
    assert not res.allowed
    assert "no new longs" in res.reason


# ----- trade count -------------------------------------------------------


def test_trade_count_allows_below_cap() -> None:
    assert check_trade_count(MAX_TRADES_PER_DAY - 1).allowed


def test_trade_count_denies_at_cap() -> None:
    res = check_trade_count(MAX_TRADES_PER_DAY)
    assert not res.allowed
    assert "cap" in res.reason


@pytest.mark.parametrize("n", [0, 1, 5, MAX_TRADES_PER_DAY - 1])
def test_trade_count_allowed_parametrised(n: int) -> None:
    assert check_trade_count(n).allowed


# ----- slippage ----------------------------------------------------------


def test_slippage_allows_small_drift() -> None:
    assert check_slippage(100.05, quote_price=100.00).allowed


def test_slippage_allows_zero_drift() -> None:
    assert check_slippage(100.0, quote_price=100.0).allowed


def test_slippage_denies_large_drift_up() -> None:
    res = check_slippage(102.0, quote_price=100.0)
    assert not res.allowed
    assert "slippage" in res.reason


def test_slippage_denies_large_drift_down() -> None:
    assert not check_slippage(98.0, quote_price=100.0).allowed


def test_slippage_denies_nonpositive_quote() -> None:
    assert not check_slippage(1.0, quote_price=0.0).allowed