"""Tests for the paper broker.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.ml.signal import Signal
from src.trader.paper import Fill, PaperBroker, Position


def _now():
    return datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


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
    b = PaperBroker(starting_cash_usd=10_000.0, fee_bps=10, max_position_pct=20.0)
    b.on_signal(_sig("BTC", "BUY"), price=50_000.0)
    b.on_signal(_sig("BTC", "SELL"), price=51_000.0)
    m = b.metrics()
    assert m["trade_count"] == 2
    assert m["pnl_usd"] > 0  # net profitable on a $1k move
    # Win rate based on a single sell position with realized > 0
    assert m["win_rate"] >= 0.0
    assert m["max_drawdown_usd"] >= 0.0
