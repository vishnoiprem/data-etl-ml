"""Paper-trade broker.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Simulated fills at last-tick. State: cash + positions + trade log.
Enforces:
- MAX_POSITION_PCT (fraction of equity per symbol)
- MAX_OPEN_POSITIONS
- FEE_BPS fee on each fill
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Deque, Dict, List, Optional

from loguru import logger

from src.config import settings
from src.ml.signal import Signal


@dataclass
class Fill:
    ts: datetime
    symbol: str
    side: str  # BUY | SELL
    qty: float
    price_usd: float
    fee_usd: float
    cash_after: float
    reason: Optional[str] = None


@dataclass
class Position:
    qty: float = 0.0
    avg_price: float = 0.0
    realized_pnl: float = 0.0


class PaperBroker:
    def __init__(
        self,
        starting_cash_usd: float = None,
        max_position_pct: float = None,
        max_open_positions: int = None,
        fee_bps: int = None,
    ):
        self.cash_usd: float = (
            starting_cash_usd if starting_cash_usd is not None else settings.starting_cash_usd
        )
        self.max_position_pct: float = (
            max_position_pct if max_position_pct is not None else settings.max_position_pct
        )
        self.max_open_positions: int = (
            max_open_positions if max_open_positions is not None else settings.max_open_positions
        )
        self.fee_bps: int = fee_bps if fee_bps is not None else settings.fee_bps
        self.fee_fraction: float = self.fee_bps / 10_000.0

        self.positions: Dict[str, Position] = {}
        self.trades: List[Fill] = []
        # Equity curve samples (ts, equity)
        self.equity_curve: Deque = deque(maxlen=10_000)
        self._latest_prices: Dict[str, float] = {}

    # ── Public API ───────────────────────────────────────────────────

    def on_price_tick(self, tick: dict) -> None:
        """Update mark-to-market and append an equity-curve sample."""
        self._latest_prices[tick["symbol"]] = float(tick["price_usd"])
        # Sample equity at most once per second (cheap hash check)
        if not self.equity_curve or (tick["ts"] - self.equity_curve[-1][0]).total_seconds() >= 1:
            self.equity_curve.append((tick["ts"], self.equity()))

    def on_signal(self, sig: Signal, price: float) -> Optional[Fill]:
        """Act on a signal at the given `price`. Returns the Fill or None."""
        if sig.action == "HOLD":
            return None
        if sig.action == "BUY":
            return self._buy(sig.symbol, price, sig.ts, sig.reason)
        if sig.action == "SELL":
            return self._sell(sig.symbol, price, sig.ts, sig.reason)
        return None

    def equity(self) -> float:
        return self.cash_usd + sum(
            (self.positions[s].qty * self._latest_prices.get(s, self.positions[s].avg_price))
            for s in self.positions
            if self.positions[s].qty > 0
        )

    def open_position_count(self) -> int:
        return sum(1 for p in self.positions.values() if p.qty > 0)

    def metrics(self) -> dict:
        """Compute PnL, win rate, max drawdown, Sharpe."""
        if not self.trades:
            return {
                "pnl_usd": 0.0,
                "win_rate": 0.0,
                "max_drawdown_usd": 0.0,
                "sharpe": 0.0,
                "trade_count": 0,
            }
        # Realized PnL = sum of (sell - buy_cost) minus fees. We track per-trade realized_pnl
        # in the Position; total it.
        realized = sum(p.realized_pnl for p in self.positions.values())
        # Win rate: percentage of SELL fills where realized PnL > 0
        # We approximate by counting Position.realized_pnl transitions; if not tracked per
        # sell, fall back to 0.5 placeholder.
        wins = sum(1 for p in self.positions.values() if p.realized_pnl > 0)
        sells = max(1, sum(1 for t in self.trades if t.side == "SELL"))
        win_rate = wins / sells

        # Max drawdown over equity curve
        max_dd = 0.0
        peak = -math.inf
        for _, eq in self.equity_curve:
            if eq > peak:
                peak = eq
            dd = peak - eq
            if dd > max_dd:
                max_dd = dd

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
            "pnl_usd": realized,
            "win_rate": win_rate,
            "max_drawdown_usd": max_dd,
            "sharpe": sharpe,
            "trade_count": len(self.trades),
        }

    # ── Internals ────────────────────────────────────────────────────

    def _buy(self, symbol: str, price: float, ts: datetime, reason: str) -> Optional[Fill]:
        # Position-size cap
        if self.open_position_count() >= self.max_open_positions and self.positions.get(symbol, Position()).qty == 0:
            logger.debug(f"buy({symbol}): max open positions reached")
            return None
        equity = self.equity()
        max_notional = equity * (self.max_position_pct / 100.0)
        # Cap by available cash too
        max_qty_by_cash = self.cash_usd / (price * (1 + self.fee_fraction))
        qty = min(max_notional / price, max_qty_by_cash)
        if qty <= 0:
            return None
        cost = qty * price
        fee = cost * self.fee_fraction
        self.cash_usd -= (cost + fee)

        pos = self.positions.setdefault(symbol, Position())
        # Update avg price (weighted)
        if pos.qty == 0:
            pos.avg_price = price
        else:
            total_qty = pos.qty + qty
            pos.avg_price = ((pos.avg_price * pos.qty) + (price * qty)) / total_qty
        pos.qty += qty
        fill = Fill(
            ts=ts, symbol=symbol, side="BUY", qty=qty, price_usd=price,
            fee_usd=fee, cash_after=self.cash_usd, reason=reason,
        )
        self.trades.append(fill)
        logger.info(
            f"BUY {qty:.6f} {symbol} @ ${price:.2f} (fee ${fee:.2f}); cash=${self.cash_usd:.2f}"
        )
        return fill

    def _sell(self, symbol: str, price: float, ts: datetime, reason: str) -> Optional[Fill]:
        pos = self.positions.get(symbol)
        if pos is None or pos.qty <= 0:
            return None
        qty = pos.qty  # sell all
        proceeds = qty * price
        fee = proceeds * self.fee_fraction
        realized = proceeds - fee - (pos.avg_price * qty)
        self.cash_usd += (proceeds - fee)
        pos.realized_pnl += realized
        pos.qty = 0.0
        pos.avg_price = 0.0
        fill = Fill(
            ts=ts, symbol=symbol, side="SELL", qty=qty, price_usd=price,
            fee_usd=fee, cash_after=self.cash_usd, reason=reason,
        )
        self.trades.append(fill)
        logger.info(
            f"SELL {qty:.6f} {symbol} @ ${price:.2f} (fee ${fee:.2f}); realized=${realized:+.2f}; cash=${self.cash_usd:.2f}"
        )
        return fill
