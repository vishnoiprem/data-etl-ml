"""Position-sizing rules.

Decides how many shares to buy for a given signal. Pure function,
no I/O. The rule we ship is "fixed notional, capped by available
cash, rounded down to whole shares":
  shares = floor(min(NOTIONAL, available_cash) / price)

This is the simplest reasonable rule. The user can swap in a
Kelly-fraction or volatility-targeted version later without
touching the broker code.
"""
from __future__ import annotations
import math
from dataclasses import dataclass


@dataclass
class SizingDecision:
    shares: int
    notional: float
    capped: bool        # True if hit cash or price limit
    reason: str


def size_position(
    signal_price: float,
    available_cash: float,
    notional_per_trade: float = 200.0,
    max_position_pct: float = 0.20,   # never put >20% of cash in one name
) -> SizingDecision:
    """Compute shares to buy.

    Args:
      signal_price: limit price (we use the current price from the signal)
      available_cash: cash in the brokerage account (USD)
      notional_per_trade: default dollar size per trade
      max_position_pct: hard cap — 0.20 means 20% of cash max

    Returns SizingDecision with shares=0 if the signal can't be acted on
    (insufficient cash, non-positive price, etc).
    """
    if signal_price <= 0 or not math.isfinite(signal_price):
        return SizingDecision(0, 0.0, True, "non-positive price")

    hard_cap = available_cash * max_position_pct
    intended = min(notional_per_trade, hard_cap, available_cash)

    if intended < signal_price:
        return SizingDecision(0, intended, True,
                              f"insufficient cash: ${intended:.2f} < price ${signal_price:.2f}")

    shares = int(intended // signal_price)
    actual_notional = shares * signal_price
    capped = intended < notional_per_trade

    if shares == 0:
        return SizingDecision(0, intended, True, "rounds to 0 shares")

    return SizingDecision(shares, actual_notional, capped,
                          f"${actual_notional:.2f} of ${notional_per_trade:.2f} target")
