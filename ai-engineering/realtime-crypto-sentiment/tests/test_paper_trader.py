"""Tests for the paper broker.

Author: Prem Vishnoi <pvishnoi@avilx.com>
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
        sentiment_zscore=1.0, momentum_zscore=1.0, reason=reason,
    )


# ── Lifecycle ────────────────────────────────────────────────────────────

def test_init_uses_settings_defaults():
    b = PaperBroker()
    assert b.cash_usd == 10_000.0
    assert b.max_position_pct == 5.0
    assert b.max_open_positions == 3
    assert b.fee_bps == 10
    assert b.fee_fraction == pytest.approx(0.001)
    assert b.positions == {}


def test_init_overrides_take_precedence():
    b = PaperBroker(starting_cash_usd=500.0, fee_bps=20, max_position_pct=2.0, max_open_positions=2)
    assert b.cash_usd == 500.0
    assert b.fee_bps == 20
    assert b.fee_fraction == pytest.approx(0.002)
    assert b.max_position_pct == 2.0
    assert b.max_open_positions == 2


# ── on_signal ───────────────────────────────────────────────────────────

def test_hold_returns_none():
    b = PaperBroker(starting_cash_usd=1000.0)
    fill = b.on_signal(_sig("BTC", "HOLD"), price=50000.0)
    assert fill is None
    assert b.cash_usd == 1000.0
    assert b.positions == {}


def test_buy_reduces_cash_and_creates_position():
    b = PaperBroker(starting_cash_usd=10_000.0, fee_bps=10, max_position_pct=5.0)
    fill = b.on_signal(_sig("BTC", "BUY", reason="z=1.5"), price=50_000.0)
    assert fill is not None
    assert fill.side == "BUY"
    assert fill.symbol == "BTC"
    assert fill.price_usd == 50_000.0
    # 5% of 10k = $500 notional, less fees
    expected_qty = (10_000.0 * 0.05) / 50_000.0
    assert fill.qty == pytest.approx(expected_qty, rel=1e-6)
    # Cash after = 10000 - qty*price*(1+fee)
    assert b.cash_usd < 10_000.0
    assert b.positions["BTC"].qty == pytest.approx(expected_qty, rel=1e-6)
    assert b.positions["BTC"].avg_price == 50_000.0
    assert fill.reason == "z=1.5"


def test_sell_increases_cash_and_closes_position():
    b = PaperBroker(starting_cash_usd=10_000.0, fee_bps=10, max_position_pct=10.0)
    b.on_signal(_sig("BTC", "BUY"), price=50_000.0)
    cash_after_buy = b.cash_usd
    pos_qty = b.positions["BTC"].qty

    fill = b.on_signal(_sig("BTC", "SELL"), price=51_000.0)
    assert fill is not None
    assert fill.side == "SELL"
    assert fill.qty == pytest.approx(pos_qty, rel=1e-6)
    # Realized PnL = (proceeds - sell_fee) - cost_basis * qty
    #              = pos_qty*(price-avg_price) - sell_fee
    sell_fee = pos_qty * 51_000.0 * b.fee_fraction
    expected_realized = (51_000.0 - 50_000.0) * pos_qty - sell_fee
    assert b.positions["BTC"].realized_pnl == pytest.approx(expected_realized, rel=1e-6)
    assert b.positions["BTC"].qty == 0.0
    assert b.positions["BTC"].avg_price == 0.0
    assert b.cash_usd > cash_after_buy


def test_sell_with_no_position_returns_none():
    b = PaperBroker(starting_cash_usd=10_000.0)
    fill = b.on_signal(_sig("BTC", "SELL"), price=50_000.0)
    assert fill is None
    assert b.trades == []


# ── Risk limits ─────────────────────────────────────────────────────────

def test_max_position_size_enforced():
    b = PaperBroker(starting_cash_usd=100_000.0, fee_bps=0, max_position_pct=2.0)
    b.on_signal(_sig("BTC", "BUY"), price=50_000.0)
    # 2% of $100k = $2000 notional → 0.04 BTC
    assert b.positions["BTC"].qty == pytest.approx(0.04, rel=1e-6)
    assert b.cash_usd == pytest.approx(100_000.0 - 0.04 * 50_000.0, rel=1e-6)


def test_max_open_positions_blocks_new_buys():
    b = PaperBroker(starting_cash_usd=100_000.0, fee_bps=0, max_position_pct=10.0, max_open_positions=2)
    b.on_signal(_sig("BTC", "BUY"), price=50_000.0)
    b.on_signal(_sig("ETH", "BUY"), price=3_000.0)
    assert b.open_position_count() == 2
    # Third symbol should be rejected
    fill = b.on_signal(_sig("SOL", "BUY"), price=100.0)
    assert fill is None
    assert "SOL" not in b.positions
    assert b.open_position_count() == 2


def test_re_buy_same_symbol_does_not_count_as_new_position():
    b = PaperBroker(starting_cash_usd=100_000.0, fee_bps=0, max_position_pct=10.0, max_open_positions=1)
    b.on_signal(_sig("BTC", "BUY"), price=50_000.0)
    assert b.open_position_count() == 1
    # 10% of 100k = 10k / 50k = 0.2 BTC per BUY
    assert b.positions["BTC"].qty == pytest.approx(0.2, rel=1e-6)
    # Re-buy same symbol should be allowed (it has a position already)
    fill = b.on_signal(_sig("BTC", "BUY"), price=50_000.0)
    assert fill is not None
    assert b.positions["BTC"].qty == pytest.approx(0.4, rel=1e-6)  # doubled


# ── Equity & metrics ────────────────────────────────────────────────────

def test_equity_uses_latest_prices():
    b = PaperBroker(starting_cash_usd=10_000.0, fee_bps=0, max_position_pct=50.0)
    b.on_signal(_sig("BTC", "BUY"), price=50_000.0)
    b.on_price_tick({"symbol": "BTC", "ts": _now(), "price_usd": 60_000.0})
    # cash_after_buy = 10000 - 0.1 * 50000 = 5000 (no fee, 50% pos = 5000/50000 = 0.1)
    # equity = cash + qty * mkt = 5000 + 0.1 * 60000 = 11000
    assert b.equity() == pytest.approx(11_000.0, rel=1e-6)


def test_equity_curve_samples_increases():
    b = PaperBroker(starting_cash_usd=10_000.0)
    b.on_price_tick({"symbol": "BTC", "ts": _now(), "price_usd": 50_000.0})
    assert len(b.equity_curve) >= 1


def test_metrics_empty_broker_returns_zeros():
    b = PaperBroker(starting_cash_usd=10_000.0)
    m = b.metrics()
    assert m["pnl_usd"] == 0.0
    assert m["win_rate"] == 0.0
    assert m["max_drawdown_usd"] == 0.0
    assert m["sharpe"] == 0.0
    assert m["trade_count"] == 0


def test_metrics_after_round_trip():
    """Single round-trip at a $1k profit → trade_count=2, pnl>0, win_rate=1.0
    (the one and only SELL was a win)."""
    b = PaperBroker(starting_cash_usd=10_000.0, fee_bps=10, max_position_pct=20.0)
    b.on_signal(_sig("BTC", "BUY"), price=50_000.0)
    b.on_signal(_sig("BTC", "SELL"), price=51_000.0)
    m = b.metrics()
    assert m["trade_count"] == 2
    # Net realized PnL: $1k move × qty - fees
    assert m["pnl_usd"] > 0
    # One SELL, that SELL was profitable → 1/1
    assert m["win_rate"] == pytest.approx(1.0, abs=1e-6)
    assert m["max_drawdown_usd"] >= 0.0


def test_metrics_loss_round_trip_records_losing_sell():
    """BUY at 50k, SELL at 49k → realized < 0, win_rate = 0.0."""
    b = PaperBroker(starting_cash_usd=10_000.0, fee_bps=0, max_position_pct=20.0)
    b.on_signal(_sig("BTC", "BUY"), price=50_000.0)
    sell = b.on_signal(_sig("BTC", "SELL"), price=49_000.0)
    m = b.metrics()
    assert sell is not None
    assert sell.realized_pnl < 0
    assert m["win_rate"] == 0.0
    assert m["pnl_usd"] < 0


def test_metrics_pnl_excludes_open_position_unrealized():
    """Open positions are NOT counted in pnl_usd (only closed SELLs).
    BUY only → pnl_usd = 0 even though the position has mark-to-market value."""
    b = PaperBroker(starting_cash_usd=10_000.0, fee_bps=0, max_position_pct=20.0)
    b.on_signal(_sig("BTC", "BUY"), price=50_000.0)
    b.on_price_tick({"symbol": "BTC", "ts": _now(), "price_usd": 60_000.0})
    m = b.metrics()
    assert m["pnl_usd"] == 0.0  # open position, no realized PnL
    # 20% of 10k = $2k notional → 0.04 BTC. After buy: cash=8000, position=0.04 BTC.
    # At $60k: position value = $2,400. Equity = 8000 + 2400 = 10,400.
    assert b.equity() == pytest.approx(10_400.0, rel=1e-6)


def test_equity_curve_appends_only_one_sample_per_second(monkeypatch):
    """The broker throttles equity-curve samples to 1Hz to bound memory."""
    b = PaperBroker(starting_cash_usd=10_000.0)
    base = _now()
    # 5 ticks in the same second → only 1 sample
    for i in range(5):
        b.on_price_tick({"symbol": "BTC", "ts": base, "price_usd": 50_000.0 + i})
    assert len(b.equity_curve) == 1
    # A tick 2s later → new sample
    b.on_price_tick({"symbol": "BTC", "ts": base + timedelta(seconds=2), "price_usd": 51_000.0})
    assert len(b.equity_curve) == 2


def test_sell_realized_pnl_includes_fee():
    """Fee is deducted from realized PnL — buyer pays $X + fee, seller
    receives $Y - fee. PnL = (Y - fee) - X (for fee=0 case), or
    (Y - sell_fee) - (X + buy_fee) when buy_fee is also non-zero."""
    b = PaperBroker(starting_cash_usd=10_000.0, fee_bps=10, max_position_pct=20.0)
    b.on_signal(_sig("BTC", "BUY"), price=50_000.0)
    # Buy qty = 2000 / 50000 = 0.04
    # Buy fee = 0.04 * 50000 * 0.001 = 2.0
    # Sell at 50_000 (flat price): proceeds = 0.04 * 50000 = 2000
    # sell fee = 2000 * 0.001 = 2.0
    # realized = (2000 - 2) - (50_000 * 0.04) = 1998 - 2000 = -2 (just the fees)
    sell = b.on_signal(_sig("BTC", "SELL"), price=50_000.0)
    assert sell is not None
    assert sell.realized_pnl == pytest.approx(-2.0, abs=0.01)
    assert sell.fee_usd == pytest.approx(2.0, abs=0.01)


def test_avg_price_weighted_across_re_buys():
    """If the broker re-buys the same symbol at different prices, the
    avg_price must be a weighted average, not a simple overwrite."""
    b = PaperBroker(starting_cash_usd=10_000.0, fee_bps=0, max_position_pct=10.0)
    # 10% of 10k = $1k notional; at $50k → 0.02 BTC
    b.on_signal(_sig("BTC", "BUY"), price=50_000.0)
    assert b.positions["BTC"].qty == pytest.approx(0.02)
    assert b.positions["BTC"].avg_price == 50_000.0
    # Re-buy at $60k → 0.0167 BTC more (limited by same 10% of equity)
    # Actually since equity grew, the size is 1k / 60k ≈ 0.01667
    b.on_signal(_sig("BTC", "BUY"), price=60_000.0)
    pos = b.positions["BTC"]
    # New qty
    second_buy_qty = 1_000.0 / 60_000.0
    expected_avg = (50_000.0 * 0.02 + 60_000.0 * second_buy_qty) / (0.02 + second_buy_qty)
    assert pos.avg_price == pytest.approx(expected_avg, rel=1e-6)
    assert pos.qty == pytest.approx(0.02 + second_buy_qty, rel=1e-6)


def test_metrics_multiple_round_trips_correct_win_rate():
    """Two round-trips on the same symbol: 1 win + 1 loss → win_rate = 0.5.

    Pre-fix the broker counted Position.realized_pnl > 0 (cumulative) and
    divided by sell count, giving wrong ratios after >1 round-trip.
    """
    b = PaperBroker(starting_cash_usd=10_000.0, fee_bps=0, max_position_pct=20.0)
    # Round 1: BUY @ 50k, SELL @ 51k → +$win
    b.on_signal(_sig("BTC", "BUY"), price=50_000.0)
    sell1 = b.on_signal(_sig("BTC", "SELL"), price=51_000.0)
    # Round 2: BUY @ 51k, SELL @ 50k → -$loss
    b.on_signal(_sig("BTC", "BUY"), price=51_000.0)
    sell2 = b.on_signal(_sig("BTC", "SELL"), price=50_000.0)
    m = b.metrics()
    assert sell1 is not None and sell2 is not None
    assert sell1.realized_pnl > 0
    assert sell2.realized_pnl < 0
    # Per-fill: 1 win / 2 sells = 0.5
    assert m["win_rate"] == pytest.approx(0.5, abs=1e-6)
    # pnl_usd = sum of per-fill realized
    assert m["pnl_usd"] == pytest.approx(sell1.realized_pnl + sell2.realized_pnl, abs=1e-6)
    # trade_count includes BUYs too
    assert m["trade_count"] == 4


def test_metrics_empty_sells_reports_zero_win_rate():
    """If only BUYs so far (no SELLs), win_rate should be 0.0, not 1.0 from 0/0 fallback."""
    b = PaperBroker(starting_cash_usd=10_000.0, fee_bps=0, max_position_pct=10.0)
    b.on_signal(_sig("BTC", "BUY"), price=50_000.0)
    m = b.metrics()
    assert m["trade_count"] == 1
    assert m["win_rate"] == 0.0
    assert m["pnl_usd"] == 0.0


def test_fill_realized_pnl_only_on_sell():
    """BUY fills always have realized_pnl=0; only SELL fills carry PnL."""
    b = PaperBroker(starting_cash_usd=10_000.0, fee_bps=0, max_position_pct=10.0)
    buy = b.on_signal(_sig("BTC", "BUY"), price=50_000.0)
    assert buy is not None
    assert buy.realized_pnl == 0.0
    sell = b.on_signal(_sig("BTC", "SELL"), price=51_000.0)
    assert sell is not None
    assert sell.realized_pnl > 0
