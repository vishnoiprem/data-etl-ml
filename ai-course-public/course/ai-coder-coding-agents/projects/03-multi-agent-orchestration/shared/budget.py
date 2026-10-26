"""
Budget and risk limits for the multi-pole trading pipeline.

Single source of truth for every number the orchestrator and poles gate on.
Kept in one module so a risk-limit change is a single-file diff reviewable by
a human — the same discipline as a single `settings.py` in a normal app.

All limits are plain module constants. The course deliberately avoids a config
file here: a config file makes it possible to change a risk limit without
touching code, and the point of these limits is that changing one is an event,
not a config toggle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# --------------------------------------------------------------------------
# Risk limits (see risk-pole/CLAUDE.md — these are the same numbers)
# --------------------------------------------------------------------------

#: Max position size as a fraction of NAV for a single name.
MAX_POSITION_PCT: float = 0.05

#: Max gross exposure as a multiple of NAV.
MAX_GROSS_EXPOSURE: float = 1.5

#: Trailing peak-to-trough drawdown that halts new longs.
MAX_DRAWDOWN_PCT: float = 0.08

#: Max new orders in a single cycle, across all symbols.
MAX_TRADES_PER_DAY: int = 12

#: Fill price drift vs the consensus quote that triggers a slippage warning.
SLIPPAGE_WARN_PCT: float = 0.01

# --------------------------------------------------------------------------
# Cost budget
# --------------------------------------------------------------------------

#: Max USD of LLM spend per cycle before the orchestrator downgrades to
#: no-trade rather than blowing through the daily budget.
MAX_CYCLE_COST_USD: float = 5.00

#: Model routing per pole. Cheaper poles do cheaper work.
POLE_MODELS: dict[str, str] = {
    "data-pole": "haiku",
    "research-pole": "sonnet",
    "strategy-pole": "opus",
    "risk-pole": "haiku",
    "execution-pole": "haiku",
}

#: A pole that hasn't posted a final ledger entry within this many seconds is
#: timed out; the cycle downgrades to no-trade.
POLE_TIMEOUT_S: float = 90.0


# --------------------------------------------------------------------------
# Gates
# --------------------------------------------------------------------------

Verdict = Literal["allow", "deny"]


@dataclass(frozen=True, slots=True)
class GateResult:
    """Outcome of a single gate check. Always inspect `.verdict`; `.reason`
    is populated only on `deny`."""

    verdict: Verdict
    reason: str = ""

    @property
    def allowed(self) -> bool:
        return self.verdict == "allow"


def check_position_size(position_value: float, nav: float) -> GateResult:
    """Reject a single-name position larger than MAX_POSITION_PCT of NAV."""
    if nav <= 0:
        return GateResult("deny", "nav must be positive")
    if position_value <= 0:
        return GateResult("allow")
    if position_value > nav * MAX_POSITION_PCT:
        return GateResult(
            "deny",
            f"position ${position_value:.2f} exceeds "
            f"{MAX_POSITION_PCT:.0%} of NAV ${nav:.2f}",
        )
    return GateResult("allow")


def check_gross_exposure(gross: float, nav: float) -> GateResult:
    """Reject total exposure above MAX_GROSS_EXPOSURE × NAV."""
    if nav <= 0:
        return GateResult("deny", "nav must be positive")
    if gross > nav * MAX_GROSS_EXPOSURE:
        return GateResult(
            "deny",
            f"gross exposure ${gross:.2f} exceeds "
            f"{MAX_GROSS_EXPOSURE:.1f}x NAV ${nav:.2f}",
        )
    return GateResult("allow")


def check_drawdown(drawdown: float) -> GateResult:
    """Halt new longs once the trailing drawdown breaches MAX_DRAWDOWN_PCT.

    `drawdown` is a positive fraction (0.08 == 8% peak-to-trough).
    """
    if drawdown > MAX_DRAWDOWN_PCT:
        return GateResult(
            "deny",
            f"drawdown {drawdown:.2%} exceeds {MAX_DRAWDOWN_PCT:.0%} — no new longs",
        )
    return GateResult("allow")


def check_trade_count(trades_today: int) -> GateResult:
    """Reject the (N+1)-th trade of the day."""
    if trades_today >= MAX_TRADES_PER_DAY:
        return GateResult(
            "deny",
            f"{trades_today} trades today already meets the "
            f"{MAX_TRADES_PER_DAY}/day cap",
        )
    return GateResult("allow")


def check_slippage(fill_price: float, quote_price: float) -> GateResult:
    """Warn (never block) when the fill drifts from the consensus quote."""
    if quote_price <= 0:
        return GateResult("deny", "quote price must be positive")
    drift = abs(fill_price - quote_price) / quote_price
    if drift > SLIPPAGE_WARN_PCT:
        return GateResult(
            "deny",
            f"slippage {drift:.2%} exceeds {SLIPPAGE_WARN_PCT:.0%} "
            "(fill ${:.4f} vs quote ${:.4f})".format(fill_price, quote_price),
        )
    return GateResult("allow")