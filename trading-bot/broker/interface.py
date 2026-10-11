"""Broker abstraction.

A single `Broker` protocol with two implementations:
  - AlpacaPaperBroker: hits the Alpaca paper-trading API (real fills)
  - FakeBroker: in-process simulator for the smoke test

Both return the same `Fill` dataclass. The signal_watcher uses the
interface; tests use the fake; the live bot uses the real one.
"""
from __future__ import annotations
import time
import uuid
from dataclasses import dataclass
from typing import Protocol


@dataclass
class Fill:
    ticker: str
    side: str            # 'BUY' or 'SELL'
    shares: int
    fill_price: float
    notional: float
    broker_id: str
    filled_at: str       # ISO 8601 UTC


class Broker(Protocol):
    def buy(self, ticker: str, shares: int) -> Fill: ...
    def sell(self, ticker: str, shares: int) -> Fill: ...
    def cash(self) -> float: ...
    def positions(self) -> dict[str, int]: ...


class FakeBroker:
    """In-process broker. Buys fill at signal_price, sells fill at
    current_price (whatever the caller passes). Tracks cash internally."""

    def __init__(self, starting_cash: float = 100_000.0,
                 commission_per_share: float = 0.0):
        self._cash = starting_cash
        self._positions: dict[str, int] = {}
        self._commission = commission_per_share
        self.fills: list[Fill] = []  # for assertions

    def buy(self, ticker: str, shares: int) -> Fill:
        # Use last-known price from price cache; fall back to $100 for tests
        price = self._prices.get(ticker, 100.0)
        cost = shares * price + shares * self._commission
        if cost > self._cash:
            raise ValueError(f"insufficient cash: ${cost:.2f} > ${self._cash:.2f}")
        self._cash -= cost
        self._positions[ticker] = self._positions.get(ticker, 0) + shares
        fill = Fill(
            ticker=ticker, side="BUY", shares=shares,
            fill_price=price, notional=shares * price,
            broker_id=f"FAKE-{uuid.uuid4().hex[:8]}",
            filled_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        self.fills.append(fill)
        return fill

    def sell(self, ticker: str, shares: int) -> Fill:
        if self._positions.get(ticker, 0) < shares:
            raise ValueError(f"can't sell {shares} {ticker}, only hold "
                             f"{self._positions.get(ticker, 0)}")
        price = self._prices.get(ticker, 100.0)
        proceeds = shares * price - shares * self._commission
        self._cash += proceeds
        self._positions[ticker] -= shares
        if self._positions[ticker] == 0:
            del self._positions[ticker]
        fill = Fill(
            ticker=ticker, side="SELL", shares=shares,
            fill_price=price, notional=shares * price,
            broker_id=f"FAKE-{uuid.uuid4().hex[:8]}",
            filled_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        self.fills.append(fill)
        return fill

    def cash(self) -> float:
        return self._cash

    def positions(self) -> dict[str, int]:
        return dict(self._positions)

    # ---- test-only helpers -----------------------------------------------
    _prices: dict[str, float] = {}

    def set_price(self, ticker: str, price: float) -> None:
        self._prices[ticker] = price


class AlpacaPaperBroker:
    """Real Alpaca paper-trading adapter.

    Requires env vars:
      ALPACA_API_KEY, ALPACA_SECRET_KEY

    Uses alpaca-py if installed; falls back to a no-op stub that
    raises if you try to trade without the library, so the smoke
    test runs even without Alpaca credentials.
    """

    def __init__(self):
        try:
            from alpaca_trade_api import REST  # type: ignore
            import os
            self._api = REST(
                key_id=os.environ["ALPACA_API_KEY"],
                secret_key=os.environ["ALPACA_SECRET_KEY"],
                base_url="https://paper-api.alpaca.markets",
            )
            self._live = True
        except Exception as e:
            self._api = None
            self._live = False
            self._init_err = str(e)

    def buy(self, ticker: str, shares: int) -> Fill:
        if not self._live:
            raise RuntimeError(
                f"Alpaca not configured ({self._init_err}); "
                "set ALPACA_API_KEY and ALPACA_SECRET_KEY, or use FakeBroker"
            )
        return self._submit(ticker, shares, "buy")

    def sell(self, ticker: str, shares: int) -> Fill:
        if not self._live:
            raise RuntimeError("Alpaca not configured")
        return self._submit(ticker, shares, "sell")

    def _submit(self, ticker: str, shares: int, side: str) -> Fill:
        order = self._api.submit_order(
            symbol=ticker, qty=shares, side=side,
            type="market", time_in_force="day",
        )
        # Block briefly for fill
        for _ in range(20):
            order = self._api.get_order(order.id)
            if order.filled_avg_price:
                break
            time.sleep(0.25)
        price = float(order.filled_avg_price or 0)
        return Fill(
            ticker=ticker, side=side.upper(), shares=shares,
            fill_price=price, notional=shares * price,
            broker_id=order.id,
            filled_at=order.filled_at.isoformat() if order.filled_at else "",
        )

    def cash(self) -> float:
        account = self._api.get_account()
        return float(account.cash)

    def positions(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for p in self._api.list_positions():
            out[p.symbol] = int(p.qty)
        return out
