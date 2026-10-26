"""Tests for the paper broker.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Currency-agnostic: the broker uses generic "units" for cash, price,
and fee (no USD suffix). Prices are synthetic unit prices.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from src.ml.signal import Signal
from src.trader.paper import PaperBroker


def _now():
    return datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


def _sig(symbol: str, action: str, reason: str = "test") -> Signal:
    return Signal(
        symbol=symbol, ts=_now(), action=action, score=1.0,
        sentiment_zscore=1.0, momentum_zscore=0.0, reason=reason,
    )


# ── Lifecycle ────────────────────────────────────────────────────────────

def test_init_uses_settings_defaults():
    b = PaperBroker()
    assert b.cash == 10_000.0
    assert b.max_position_pct == 5.0
    assert b.max_open_positions == 3
    assert b.fee_bps == 10
    assert b.fee_fraction == pytest.approx(0.001)
    assert b.positions == {}


def test_init_overrides_take_precedence():
    b = PaperBroker(starting_units=500.0, fee_bps=20, max_position_pct=2.0, max_open_positions=2)
    assert b.cash == 500.0
    assert b.fee_bps == 20
    assert b.fee_fraction == pytest.approx(0.002)
    assert b.max_position_pct == 2.0
    assert b.max_open_positions == 2


# ── on_signal ───────────────────────────────────────────────────────────

def test_hold_returns_none():
    b = PaperBroker(starting_units=1000.0)
    fill = b.on_signal(_sig("AI", "HOLD"), price=50.0)
    assert fill is None
    assert b.cash == 1000.0
    assert b.positions == {}


def test_buy_reduces_cash_and_creates_position():
    b = PaperBroker(starting_units=10_000.0, fee_bps=10, max_position_pct=5.0)
    fill = b.on_signal(_sig("AI", "BUY", reason="z=1.5"), price=50.0)
    assert fill is not None
    assert fill.side == "BUY"
    assert fill.symbol == "AI"
    assert fill.price == 50.0
    # 5% of 10k = $500 notional, less fees
    expected_qty = (10_000.0 * 0.05) / 50.0
    assert fill.qty == pytest.approx(expected_qty, rel=1e-6)
    # Cash after = 10000 - qty*price*(1+fee)
    assert b.cash < 10_000.0
    assert b.positions["AI"].qty == pytest.approx(expected_qty, rel=1e-6)
    assert b.positions["AI"].avg_price == 50.0
    assert fill.reason == "z=1.5"


def test_sell_increases_cash_and_closes_position():
    b = PaperBroker(starting_units=10_000.0, fee_bps=10, max_position_pct=10.0)
    b.on_signal(_sig("AI", "BUY"), price=50.0)
    cash_after_buy = b.cash
    pos_qty = b.positions["AI"].qty

    fill = b.on_signal(_sig("AI", "SELL"), price=51.0)
    assert fill is not None
    assert fill.side == "SELL"
    assert fill.qty == pytest.approx(pos_qty, rel=1e-6)
    # Realized PnL = (proceeds - sell_fee) - cost_basis * qty
    sell_fee = pos_qty * 51.0 * b.fee_fraction
    expected_realized = (51.0 - 50.0) * pos_qty - sell_fee
    assert b.positions["AI"].realized_pnl == pytest.approx(expected_realized, rel=1e-6)
    assert b.positions["AI"].qty == 0.0
    assert b.positions["AI"].avg_price == 0.0
    assert b.cash > cash_after_buy


def test_sell_with_no_position_returns_none():
    b = PaperBroker(starting_units=10_000.0)
    fill = b.on_signal(_sig("AI", "SELL"), price=50.0)
    assert fill is None
    assert b.trades == []


# ── Risk limits ─────────────────────────────────────────────────────────

def test_max_position_size_enforced():
    b = PaperBroker(starting_units=100_000.0, fee_bps=0, max_position_pct=2.0)
    b.on_signal(_sig("AI", "BUY"), price=50.0)
    # 2% of 100k = 2000 notional → 40 units
    assert b.positions["AI"].qty == pytest.approx(40.0, rel=1e-6)
    assert b.cash == pytest.approx(100_000.0 - 40.0 * 50.0, rel=1e-6)


def test_max_open_positions_blocks_new_buys():
    b = PaperBroker(starting_units=100_000.0, fee_bps=0, max_position_pct=10.0, max_open_positions=2)
    b.on_signal(_sig("AI", "BUY"), price=50.0)
    b.on_signal(_sig("LLM", "BUY"), price=3.0)
    assert b.open_position_count() == 2
    # Third symbol should be rejected
    fill = b.on_signal(_sig("TSLA", "BUY"), price=100.0)
    assert fill is None
    assert "TSLA" not in b.positions
    assert b.open_position_count() == 2


def test_re_buy_same_symbol_does_not_count_as_new_position():
    b = PaperBroker(starting_units=100_000.0, fee_bps=0, max_position_pct=10.0, max_open_positions=1)
    b.on_signal(_sig("AI", "BUY"), price=50.0)
    assert b.open_position_count() == 1
    # 10% of 100k = 10k / 50k = 200 units per BUY
    assert b.positions["AI"].qty == pytest.approx(200.0, rel=1e-6)
    # Re-buy same symbol should be allowed (it has a position already)
    fill = b.on_signal(_sig("AI", "BUY"), price=50.0)
    assert fill is not None
    assert b.positions["AI"].qty == pytest.approx(400.0, rel=1e-6)  # doubled


# ── Equity & metrics ────────────────────────────────────────────────────

def test_equity_uses_latest_prices():
    b = PaperBroker(starting_units=10_000.0, fee_bps=0, max_position_pct=50.0)
    b.on_signal(_sig("AI", "BUY"), price=50.0)
    b.on_price_tick({"symbol": "AI", "ts": _now(), "price": 60.0})
    # 50% of 10k = 5000/50 = 100 units; cash after buy = 5000; equity = 5000 + 100*60 = 11000
    assert b.equity() == pytest.approx(11_000.0, rel=1e-6)


def test_equity_curve_samples_increases():
    b = PaperBroker(starting_units=10_000.0)
    b.on_price_tick({"symbol": "AI", "ts": _now(), "price": 50.0})
    assert len(b.equity_curve) >= 1


def test_metrics_empty_broker_returns_zeros():
    b = PaperBroker(starting_units=10_000.0)
    m = b.metrics()
    assert m["pnl"] == 0.0
    assert m["win_rate"] == 0.0
    assert m["max_drawdown"] == 0.0
    assert m["sharpe"] == 0.0
    assert m["trade_count"] == 0


def test_metrics_after_round_trip():
    """Single round-trip at a profit → trade_count=2, pnl>0, win_rate=1.0
    (the one and only SELL was a win)."""
    b = PaperBroker(starting_units=10_000.0, fee_bps=10, max_position_pct=20.0)
    b.on_signal(_sig("AI", "BUY"), price=50.0)
    b.on_signal(_sig("AI", "SELL"), price=51.0)
    m = b.metrics()
    assert m["trade_count"] == 2
    assert m["pnl"] > 0
    assert m["win_rate"] == pytest.approx(1.0, abs=1e-6)
    assert m["max_drawdown"] >= 0.0


def test_metrics_loss_round_trip_records_losing_sell():
    """BUY at 50, SELL at 49 → realized < 0, win_rate = 0.0."""
    b = PaperBroker(starting_units=10_000.0, fee_bps=0, max_position_pct=20.0)
    b.on_signal(_sig("AI", "BUY"), price=50.0)
    sell = b.on_signal(_sig("AI", "SELL"), price=49.0)
    m = b.metrics()
    assert sell is not None
    assert sell.realized_pnl < 0
    assert m["win_rate"] == 0.0
    assert m["pnl"] < 0


def test_metrics_pnl_excludes_open_position_unrealized():
    """Open positions are NOT counted in pnl (only closed SELLs).
    BUY only → pnl = 0 even though the position has mark-to-market value."""
    b = PaperBroker(starting_units=10_000.0, fee_bps=0, max_position_pct=20.0)
    b.on_signal(_sig("AI", "BUY"), price=50.0)
    b.on_price_tick({"symbol": "AI", "ts": _now(), "price": 60.0})
    m = b.metrics()
    assert m["pnl"] == 0.0
    # 20% of 10k = 2000 notional → 40 units. After buy: cash=8000, position=40.
    # At 60: position value = 40*60 = 2400. Equity = 8000 + 2400 = 10,400.
    assert b.equity() == pytest.approx(10_400.0, rel=1e-6)


def test_equity_curve_appends_only_one_sample_per_second():
    """The broker throttles equity-curve samples to 1Hz to bound memory."""
    b = PaperBroker(starting_units=10_000.0)
    base = _now()
    # 5 ticks in the same second → only 1 sample
    for i in range(5):
        b.on_price_tick({"symbol": "AI", "ts": base, "price": 50.0 + i})
    assert len(b.equity_curve) == 1
    # A tick 2s later → new sample
    b.on_price_tick({"symbol": "AI", "ts": base + timedelta(seconds=2), "price": 51.0})
    assert len(b.equity_curve) == 2


def test_sell_realized_pnl_includes_fee():
    """Fee is deducted from realized PnL — buyer pays X + fee, seller
    receives Y - fee. PnL = (Y - fee) - X (for fee=0 case), or
    (Y - sell_fee) - (X + buy_fee) when buy_fee is also non-zero."""
    b = PaperBroker(starting_units=10_000.0, fee_bps=10, max_position_pct=20.0)
    b.on_signal(_sig("AI", "BUY"), price=50.0)
    # Buy qty = 2000 / 50 = 40
    # Buy fee = 40 * 50 * 0.001 = 2.0
    # Sell at 50 (flat price): proceeds = 40 * 50 = 2000
    # sell fee = 2000 * 0.001 = 2.0
    # realized = (2000 - 2) - (50 * 40) = 1998 - 2000 = -2 (just the fees)
    sell = b.on_signal(_sig("AI", "SELL"), price=50.0)
    assert sell is not None
    assert sell.realized_pnl == pytest.approx(-2.0, abs=0.01)
    assert sell.fee == pytest.approx(2.0, abs=0.01)


def test_avg_price_weighted_across_re_buys():
    """If the broker re-buys the same symbol at different prices, the
    avg_price must be a weighted average, not a simple overwrite."""
    b = PaperBroker(starting_units=10_000.0, fee_bps=0, max_position_pct=10.0)
    # 10% of 10k = 1000 notional; at 50 → 20 units
    b.on_signal(_sig("AI", "BUY"), price=50.0)
    assert b.positions["AI"].qty == pytest.approx(20.0)
    assert b.positions["AI"].avg_price == 50.0
    # Re-buy at 60 → more units (limited by same 10% of equity)
    b.on_signal(_sig("AI", "BUY"), price=60.0)
    pos = b.positions["AI"]
    second_buy_qty = 1_000.0 / 60.0
    expected_avg = (50.0 * 20.0 + 60.0 * second_buy_qty) / (20.0 + second_buy_qty)
    assert pos.avg_price == pytest.approx(expected_avg, rel=1e-6)
    assert pos.qty == pytest.approx(20.0 + second_buy_qty, rel=1e-6)


def test_metrics_multiple_round_trips_correct_win_rate():
    """Two round-trips on the same symbol: 1 win + 1 loss → win_rate = 0.5.

    Pre-fix the broker counted Position.realized_pnl > 0 (cumulative) and
    divided by sell count, giving wrong ratios after >1 round-trip.
    """
    b = PaperBroker(starting_units=10_000.0, fee_bps=0, max_position_pct=20.0)
    # Round 1: BUY @ 50, SELL @ 51 → +win
    b.on_signal(_sig("AI", "BUY"), price=50.0)
    sell1 = b.on_signal(_sig("AI", "SELL"), price=51.0)
    # Round 2: BUY @ 51, SELL @ 50 → -loss
    b.on_signal(_sig("AI", "BUY"), price=51.0)
    sell2 = b.on_signal(_sig("AI", "SELL"), price=50.0)
    m = b.metrics()
    assert sell1 is not None and sell2 is not None
    assert sell1.realized_pnl > 0
    assert sell2.realized_pnl < 0
    # Per-fill: 1 win / 2 sells = 0.5
    assert m["win_rate"] == pytest.approx(0.5, abs=1e-6)
    # pnl = sum of per-fill realized
    assert m["pnl"] == pytest.approx(sell1.realized_pnl + sell2.realized_pnl, abs=1e-6)
    # trade_count includes BUYs too
    assert m["trade_count"] == 4


def test_metrics_empty_sells_reports_zero_win_rate():
    """If only BUYs so far (no SELLs), win_rate should be 0.0, not 1.0 from 0/0 fallback."""
    b = PaperBroker(starting_units=10_000.0, fee_bps=0, max_position_pct=10.0)
    b.on_signal(_sig("AI", "BUY"), price=50.0)
    m = b.metrics()
    assert m["trade_count"] == 1
    assert m["win_rate"] == 0.0
    assert m["pnl"] == 0.0


def test_fill_realized_pnl_only_on_sell():
    """BUY fills always have realized_pnl=0; only SELL fills carry PnL."""
    b = PaperBroker(starting_units=10_000.0, fee_bps=0, max_position_pct=10.0)
    buy = b.on_signal(_sig("AI", "BUY"), price=50.0)
    assert buy is not None
    assert buy.realized_pnl == 0.0
    sell = b.on_signal(_sig("AI", "SELL"), price=51.0)
    assert sell is not None
    assert sell.realized_pnl > 0


def test_buy_skipped_when_notional_below_minimum():
    """If the resulting notional would be <0.01 units, the BUY is
    skipped (no phantom fills in the trade log). This can happen when
    price is much higher than equity."""
    # 100 units of cash, price = 1_000_000 → max_qty_by_cash ≈ 1e-4
    # → notional ≈ 100, well above 0.01, so this DOES fill.
    # The floor is meant for *extreme* edge cases.
    b = PaperBroker(starting_units=0.001, fee_bps=0, max_position_pct=100.0)
    fill = b.on_signal(_sig("EXPENSIVE", "BUY"), price=1_000_000.0)
    assert fill is None  # notional = 0.001 < 0.01 floor
    assert b.positions == {}
    assert b.trades == []


def test_buy_with_huge_price_but_big_equity_still_fills():
    """Sanity check: the floor doesn't accidentally reject legitimate
    high-price, high-equity trades."""
    b = PaperBroker(starting_units=1_000_000.0, fee_bps=0, max_position_pct=10.0)
    fill = b.on_signal(_sig("BRK", "BUY"), price=1_000_000.0)
    assert fill is not None
    # 10% of 1M = 100k notional / 1M price = 0.1 qty
    assert fill.qty == pytest.approx(0.1, rel=1e-6)