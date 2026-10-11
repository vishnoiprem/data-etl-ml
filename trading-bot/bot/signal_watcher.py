"""The signal → decision → fill loop.

Polls TimescaleDB for new BUY signals, sizes each, places the buy,
records everything in the state store. Sells are NEVER placed by the
watcher — that's the user's job via the Telegram bot. This is the
"auto-buy, manual-sell" pattern.

The watcher is a single async loop with a clear state machine per
signal:
  1. NEW:   poll finds signal, not yet in decisions table
  2. BUY:   size + submit buy order, record decision + trade
  3. SKIP:  if sizing returns 0 shares (insufficient cash, etc)
  4. DONE:  once a decision row exists, the watcher ignores the signal

Idempotency: every step is gated by the UNIQUE INDEX on
decisions(ticker, signal_ts). Even if the watcher crashes mid-flight
and restarts, polling the same signal twice produces no duplicate.
"""
from __future__ import annotations
import time
import logging
from dataclasses import asdict
from datetime import datetime
from typing import Optional

from broker.state import State, Signal, Decision, Trade
from broker.sizer import size_position
from broker.interface import Broker


log = logging.getLogger("signal_watcher")


class SignalWatcher:
    def __init__(self, state: State, broker: Broker,
                 notional_per_trade: float = 200.0,
                 max_position_pct: float = 0.20):
        self.state = state
        self.broker = broker
        self.notional_per_trade = notional_per_trade
        self.max_position_pct = max_position_pct

    def process_signal(self, sig: Signal) -> Optional[Decision]:
        """Process a single signal end-to-end. Returns the decision row.

        Idempotent: calling twice with the same (ticker, ts) is safe;
        the second call is a no-op that returns the existing decision.
        """
        # 1. record (or recognize duplicate)
        is_new = self.state.record_signal(sig)
        if not is_new and self.state.has_decision(sig.ticker, sig.ts):
            return self.state.decision_for(sig.ticker, sig.ts)

        if sig.action != "BUY":
            # WATCH signals are recorded but never traded
            return self.state.record_decision(Decision(
                id=0, ticker=sig.ticker, signal_ts=sig.ts,
                verdict="SKIP", notional=None, shares=None,
                reason=f"non-BUY action: {sig.action}",
                decided_at=datetime.utcnow().isoformat(),
            ))

        # 2. size
        sizing = size_position(
            signal_price=sig.price,
            available_cash=self.broker.cash(),
            notional_per_trade=self.notional_per_trade,
            max_position_pct=self.max_position_pct,
        )

        if sizing.shares == 0:
            log.info("skip %s: %s", sig.ticker, sizing.reason)
            return self.state.record_decision(Decision(
                id=0, ticker=sig.ticker, signal_ts=sig.ts,
                verdict="SKIP", notional=None, shares=None,
                reason=sizing.reason,
                decided_at=datetime.utcnow().isoformat(),
            ))

        # 3. submit buy
        try:
            fill = self.broker.buy(sig.ticker, sizing.shares)
        except Exception as e:
            log.exception("buy failed for %s", sig.ticker)
            return self.state.record_decision(Decision(
                id=0, ticker=sig.ticker, signal_ts=sig.ts,
                verdict="SKIP", notional=None, shares=None,
                reason=f"buy failed: {e}",
                decided_at=datetime.utcnow().isoformat(),
            ))

        # 4. record decision + trade
        dec = self.state.record_decision(Decision(
            id=0, ticker=sig.ticker, signal_ts=sig.ts,
            verdict="BUY", notional=sizing.notional, shares=sizing.shares,
            reason=f"signal conf={sig.confidence:.2f} reason={sig.reason}",
            decided_at=datetime.utcnow().isoformat(),
        ))
        self.state.record_trade(Trade(
            id=0, decision_id=dec.id, ticker=fill.ticker, side=fill.side,
            shares=fill.shares, fill_price=fill.fill_price,
            notional=fill.notional, filled_at=fill.filled_at,
            broker_id=fill.broker_id,
        ))
        log.info("BUY %s: %d shares @ $%.2f (id=%s)",
                 sig.ticker, fill.shares, fill.fill_price, fill.broker_id)
        return self.state.decision_for(sig.ticker, sig.ts)

    def process_pending(self) -> list[Decision]:
        """Process every signal that doesn't have a decision yet."""
        out: list[Decision] = []
        for sig in self.state.unseen_buy_signals():
            d = self.process_signal(sig)
            if d:
                out.append(d)
        return out

    # ---- sell side (manual, called from Telegram) -------------------------
    def manual_sell(self, ticker: str, shares: int) -> Trade:
        """Place a SELL. The user invoked this from Telegram.

        We do NOT consult the signal table. We just sell whatever
        shares the user said to sell, from the position we hold.
        The check is against the BROKER (authoritative) not the state
        store (cached), so a stale state can't cause over-selling.
        """
        held = self.broker.positions().get(ticker, 0)
        if shares > held:
            raise ValueError(
                f"can't sell {shares} {ticker}, only hold {held}"
            )
        fill = self.broker.sell(ticker, shares)
        # Use datetime.utcnow() with microsecond precision as the synthetic
        # signal_ts, prefixed with "manual:" so even if a real signal
        # arrives in the same microsecond they don't clash on the
        # UNIQUE INDEX (ticker, signal_ts).
        now = datetime.utcnow()
        synthetic_ts = f"manual:{now.isoformat()}"
        dec = self.state.record_decision(Decision(
            id=0, ticker=ticker,
            signal_ts=synthetic_ts,
            verdict="MANUAL_SELL",
            notional=None, shares=shares,
            reason="manual sell from Telegram",
            decided_at=now.isoformat(),
        ))
        trade_id = self.state.record_trade(Trade(
            id=0, decision_id=dec.id, ticker=fill.ticker, side=fill.side,
            shares=fill.shares, fill_price=fill.fill_price,
            notional=fill.notional, filled_at=fill.filled_at,
            broker_id=fill.broker_id,
        ))
        return Trade(
            id=trade_id, decision_id=dec.id, ticker=fill.ticker,
            side=fill.side, shares=fill.shares,
            fill_price=fill.fill_price, notional=fill.notional,
            filled_at=fill.filled_at, broker_id=fill.broker_id,
        )
