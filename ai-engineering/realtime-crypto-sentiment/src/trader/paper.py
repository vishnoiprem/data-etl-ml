"""Paper-trade broker.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Simulated fills at the most recent synthetic unit price. State: cash
(units) + positions + trade log. Enforces:
- MAX_POSITION_PCT (fraction of equity per symbol)
- MAX_OPEN_POSITIONS
- FEE_BPS fee on each fill

Note: there is no real money. "Price" is a synthetic unit price (in
this pipeline, derived from tweet engagement — see pipeline.py). All
monetary fields are unitless.
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from datetime import datetime

from loguru import logger

from src.config import settings
from src.ml.signal import Signal


@dataclass
class Fill:
    ts: datetime
    symbol: str
    side: str  # BUY | SELL
    qty: float
    price: float
    fee: float
    cash_after: float
    reason: str | None = None
    realized_pnl: float = 0.0  # populated on SELL (0 on BUY)


@dataclass
class Position:
    qty: float = 0.0
    avg_price: float = 0.0
    realized_pnl: float = 0.0


class PaperBroker:
    def __init__(
        self,
        starting_units: float | None = None,
        max_position_pct: float | None = None,
        max_open_positions: int | None = None,
        fee_bps: int | None = None,
    ):
        self.cash: float = (
            starting_units if starting_units is not None else settings.starting_units
        )
        self.max_position_pct: float = (
            max_position_pct if max_position_pct is not None else settings.max_position_pct
        )
        self.max_open_positions: int = (
            max_open_positions if max_open_positions is not None else settings.max_open_positions
        )
        self.fee_bps: int = fee_bps if fee_bps is not None else settings.fee_bps
        self.fee_fraction: float = self.fee_bps / 10_000.0

        self.positions: dict[str, Position] = {}
        self.trades: list[Fill] = []
        # Equity curve samples (ts, equity)
        self.equity_curve: deque = deque(maxlen=10_000)
        self._latest_prices: dict[str, float] = {}

    # ── Public API ───────────────────────────────────────────────────

    def on_price_tick(self, tick: dict) -> None:
        """Update mark-to-market and append an equity-curve sample.

        `tick` is `{ts, symbol, price}` (price is a synthetic unit price).
        """
        self._latest_prices[tick["symbol"]] = float(tick["price"])
        # Sample equity at most once per second (cheap hash check)
        if not self.equity_curve or (tick["ts"] - self.equity_curve[-1][0]).total_seconds() >= 1:
            self.equity_curve.append((tick["ts"], self.equity()))

    def on_signal(self, sig: Signal, price: float) -> Fill | None:
        """Act on a signal at the given `price`. Returns the Fill or None."""
        if sig.action == "HOLD":
            return None
        if sig.action == "BUY":
            return self._buy(sig.symbol, price, sig.ts, sig.reason)
        if sig.action == "SELL":
            return self._sell(sig.symbol, price, sig.ts, sig.reason)
        return None

    def equity(self) -> float:
        return self.cash + sum(
            (self.positions[s].qty * self._latest_prices.get(s, self.positions[s].avg_price))
            for s in self.positions
            if self.positions[s].qty > 0
        )

    def open_position_count(self) -> int:
        return sum(1 for p in self.positions.values() if p.qty > 0)

    def metrics(self) -> dict:
        """Compute PnL, win rate, max drawdown, Sharpe.

        PnL and win-rate are computed from per-Fill `realized_pnl` (populated
        on every SELL), so the numbers stay correct across multiple
        round-trips on the same symbol.
        """
        sells = [t for t in self.trades if t.side == "SELL"]
        if not self.trades:
            return {
                "pnl": 0.0,
                "win_rate": 0.0,
                "max_drawdown": 0.0,
                "sharpe": 0.0,
                "trade_count": 0,
            }
        # Realized PnL = sum of per-fill realized PnL on SELLs
        realized = sum(t.realized_pnl for t in sells)
        # Win rate: fraction of SELLs that closed in profit.
        # If there are no SELLs yet, report 0.0 (not 1.0 from a 0/0 fallback).
        win_rate = sum(1 for t in sells if t.realized_pnl > 0) / len(sells) if sells else 0.0

        # Max drawdown over equity curve
        max_dd = 0.0
        peak = -math.inf
        for _, eq in self.equity_curve:
            peak = max(peak, eq)
            dd = peak - eq
            max_dd = max(max_dd, dd)

        # Sharpe (annualized) over equity-curve returns
        if len(self.equity_curve) >= 2:
            rets = []
            prev = None
            for _, eq in self.equity_curve:
                if prev is not None and prev > 0:
                    rets.append((eq - prev) / prev)
                prev = eq
            if len(rets) >= 2:
                mean = sum(rets) / len(rets)
                var = sum((r - mean) ** 2 for r in rets) / len(rets)
                std = math.sqrt(var)
                sharpe = (mean / std) * math.sqrt(252 * 24 * 60) if std > 0 else 0.0  # minute-level
            else:
                sharpe = 0.0
        else:
            sharpe = 0.0

        return {
            "pnl": realized,
            "win_rate": win_rate,
            "max_drawdown": max_dd,
            "sharpe": sharpe,
            "trade_count": len(self.trades),
        }

    # ── Internals ────────────────────────────────────────────────────

    # Smallest notional we'll attempt to fill at. Below this the position
    # is effectively a no-op (rounding + fee would leave a sub-1e-10
    # qty) and just pollutes the trade log with phantom fills.
    _MIN_NOTIONAL = 0.01  # 0.01 units (e.g. cents worth of equity)

    def _buy(self, symbol: str, price: float, ts: datetime, reason: str) -> Fill | None:
        # Position-size cap
        if self.open_position_count() >= self.max_open_positions and self.positions.get(symbol, Position()).qty == 0:
            logger.debug(f"buy({symbol}): max open positions reached")
            return None
        equity = self.equity()
        max_notional = equity * (self.max_position_pct / 100.0)
        # Cap by available cash too. The `1 + fee_fraction` divisor
        # pre-pays the fee so the resulting cash balance can never
        # go negative due to fees. See test_max_position_size_enforced.
        max_qty_by_cash = self.cash / (price * (1 + self.fee_fraction))
        qty = min(max_notional / price, max_qty_by_cash)
        if qty * price < self._MIN_NOTIONAL:
            # Not enough equity or cash to make a meaningful fill
            # (e.g. price is 1e6 and equity is 1.0).
            logger.debug(
                f"buy({symbol}): notional {qty * price:.6f} < {self._MIN_NOTIONAL}; skipping"
            )
            return None
        cost = qty * price
        fee = cost * self.fee_fraction
        self.cash -= (cost + fee)

        pos = self.positions.setdefault(symbol, Position())
        # Update avg price (weighted)
        if pos.qty == 0:
            pos.avg_price = price
        else:
            total_qty = pos.qty + qty
            pos.avg_price = ((pos.avg_price * pos.qty) + (price * qty)) / total_qty
        pos.qty += qty
        fill = Fill(
            ts=ts, symbol=symbol, side="BUY", qty=qty, price=price,
            fee=fee, cash_after=self.cash, reason=reason,
        )
        self.trades.append(fill)
        logger.info(
            f"BUY {qty:.6f} {symbol} @ {price:.2f} (fee {fee:.2f}); cash={self.cash:.2f}"
        )
        return fill

    def _sell(self, symbol: str, price: float, ts: datetime, reason: str) -> Fill | None:
        pos = self.positions.get(symbol)
        if pos is None or pos.qty <= 0:
            return None
        qty = pos.qty  # sell all
        proceeds = qty * price
        fee = proceeds * self.fee_fraction
        realized = proceeds - fee - (pos.avg_price * qty)
        self.cash += (proceeds - fee)
        pos.realized_pnl += realized
        pos.qty = 0.0
        pos.avg_price = 0.0
        fill = Fill(
            ts=ts, symbol=symbol, side="SELL", qty=qty, price=price,
            fee=fee, cash_after=self.cash, reason=reason,
            realized_pnl=realized,
        )
        self.trades.append(fill)
        logger.info(
            f"SELL {qty:.6f} {symbol} @ {price:.2f} (fee {fee:.2f}); realized={realized:+.2f}; cash={self.cash:.2f}"
        )
        return fill