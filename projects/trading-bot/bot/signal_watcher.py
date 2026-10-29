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
import logging
import time
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional, Callable

from broker.state import State, Signal, Decision, Trade
from broker.sizer import size_position
from broker.interface import Broker, Fill, CircuitBreakerOpenError

log = logging.getLogger("signal_watcher")


class SignalWatcher:
    """Processes trading signals and executes orders via a broker."""

    def __init__(
        self,
        state: State,
        broker: Broker,
        notional_per_trade: float = 200.0,
        max_position_pct: float = 0.20,
        max_retries: int = 3,
        base_retry_delay: float = 1.0,
    ):
        self.state = state
        self.broker = broker
        self.notional_per_trade = notional_per_trade
        self.max_position_pct = max_position_pct
        self.max_retries = max_retries
        self.base_retry_delay = base_retry_delay
        self._correlation_id: Optional[str] = None

    def _new_correlation_id(self) -> str:
        """Generate a new correlation ID for request tracing."""
        return uuid.uuid4().hex[:8]

    def _execute_with_retry(
        self,
        func: Callable,
        *args,
        retry_exceptions: tuple[type[Exception], ...] = (Exception,),
        **kwargs,
    ):
        """Execute func with exponential backoff retry."""
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except retry_exceptions as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = min(self.base_retry_delay * (2 ** attempt), 30.0)
                    log.warning(
                        "[%s] Attempt %d/%d failed: %s. Retrying in %.1fs...",
                        self._correlation_id or "N/A",
                        attempt + 1, self.max_retries + 1, e, delay
                    )
                    time.sleep(delay)
                else:
                    log.exception(
                        "[%s] All %d retry attempts exhausted",
                        self._correlation_id or "N/A", self.max_retries + 1
                    )
        raise last_exception

    def process_signal(self, sig: Signal) -> Optional[Decision]:
        """Process a single signal end-to-end. Returns the decision row.

        Idempotent: calling twice with the same (ticker, ts) is safe;
        the second call is a no-op that returns the existing decision.
        """
        self._correlation_id = self._new_correlation_id()
        log.info(
            "[%s] Processing signal: %s %s @ $%.2f (conf=%.2f)",
            self._correlation_id, sig.ticker, sig.action, sig.price, sig.confidence or 0
        )

        # 1. record (or recognize duplicate)
        is_new = self.state.record_signal(sig)
        if not is_new and self.state.has_decision(sig.ticker, sig.ts):
            existing = self.state.decision_for(sig.ticker, sig.ts)
            log.info("[%s] Signal already processed, returning existing decision: %s",
                     self._correlation_id, existing.verdict if existing else "None")
            return existing

        if sig.action != "BUY":
            # WATCH signals are recorded but never traded
            log.info("[%s] Non-BUY action (%s), skipping trade", self._correlation_id, sig.action)
            return self.state.record_decision(Decision(
                id=0, ticker=sig.ticker, signal_ts=sig.ts,
                verdict="SKIP", notional=None, shares=None,
                reason=f"non-BUY action: {sig.action}",
                decided_at=datetime.now(timezone.utc).isoformat(),
            ))

        # 2. size
        sizing = size_position(
            signal_price=sig.price,
            available_cash=self.broker.cash(),
            notional_per_trade=self.notional_per_trade,
            max_position_pct=self.max_position_pct,
        )

        if sizing.shares == 0:
            log.info("[%s] Skip %s: %s", self._correlation_id, sig.ticker, sizing.reason)
            return self.state.record_decision(Decision(
                id=0, ticker=sig.ticker, signal_ts=sig.ts,
                verdict="SKIP", notional=None, shares=None,
                reason=sizing.reason,
                decided_at=datetime.now(timezone.utc).isoformat(),
            ))

        # 3. submit buy with retry
        try:
            fill = self._execute_with_retry(
                self.broker.buy, sig.ticker, sizing.shares,
                retry_exceptions=(Exception, CircuitBreakerOpenError),
            )
        except CircuitBreakerOpenError:
            log.error("[%s] Circuit breaker open, skipping buy for %s", self._correlation_id, sig.ticker)
            return self.state.record_decision(Decision(
                id=0, ticker=sig.ticker, signal_ts=sig.ts,
                verdict="SKIP", notional=None, shares=None,
                reason="circuit breaker open",
                decided_at=datetime.now(timezone.utc).isoformat(),
            ))
        except Exception as e:
            log.exception("[%s] Buy failed for %s after retries", self._correlation_id, sig.ticker)
            return self.state.record_decision(Decision(
                id=0, ticker=sig.ticker, signal_ts=sig.ts,
                verdict="SKIP", notional=None, shares=None,
                reason=f"buy failed after retries: {e}",
                decided_at=datetime.now(timezone.utc).isoformat(),
            ))

        # 4. record decision + trade
        dec = self.state.record_decision(Decision(
            id=0, ticker=sig.ticker, signal_ts=sig.ts,
            verdict="BUY", notional=sizing.notional, shares=sizing.shares,
            reason=f"signal conf={sig.confidence:.2f} reason={sig.reason}",
            decided_at=datetime.now(timezone.utc).isoformat(),
        ))
        self.state.record_trade(Trade(
            id=0, decision_id=dec.id, ticker=fill.ticker, side=fill.side,
            shares=fill.shares, fill_price=fill.fill_price,
            notional=fill.notional, filled_at=fill.filled_at,
            broker_id=fill.broker_id,
        ))
        log.info(
            "[%s] BUY %s: %d shares @ $%.2f (id=%s, notional=$%.2f)",
            self._correlation_id, sig.ticker, fill.shares, fill.fill_price,
            fill.broker_id, fill.notional
        )
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
        self._correlation_id = self._new_correlation_id()
        log.info("[%s] Manual sell requested: %s %d shares", self._correlation_id, ticker, shares)

        held = self.broker.positions().get(ticker, 0)
        if shares > held:
            raise ValueError(
                f"can't sell {shares} {ticker}, only hold {held}"
            )

        fill = self._execute_with_retry(
            self.broker.sell, ticker, shares,
            retry_exceptions=(Exception, CircuitBreakerOpenError),
        )

        # Use UUID + timestamp for synthetic signal_ts to avoid collision
        # The "manual:" prefix ensures no clash with real signals
        now = datetime.now(timezone.utc)
        synthetic_ts = f"manual:{now.isoformat()}:{uuid.uuid4().hex[:8]}"

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
        log.info(
            "[%s] MANUAL_SELL %s: %d shares @ $%.2f (id=%s)",
            self._correlation_id, fill.ticker, fill.shares, fill.fill_price, fill.broker_id
        )
        return Trade(
            id=trade_id, decision_id=dec.id, ticker=fill.ticker,
            side=fill.side, shares=fill.shares,
            fill_price=fill.fill_price, notional=fill.notional,
            filled_at=fill.filled_at, broker_id=fill.broker_id,
        )
