"""Broker abstraction.

A single `Broker` protocol with two implementations:
  - AlpacaPaperBroker: hits the Alpaca paper-trading API (real fills)
  - FakeBroker: in-process simulator for the smoke test

Both return the same `Fill` dataclass. The signal_watcher uses the
interface; tests use the fake; the live bot uses the real one.
"""
from __future__ import annotations
import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol, Optional
from contextlib import contextmanager

log = logging.getLogger(__name__)


@dataclass(frozen=True)
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


class CircuitBreaker:
    """Simple circuit breaker for broker failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exception: type[Exception] = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self._failures = 0
        self._last_failure_time: Optional[float] = None
        self._state = "closed"  # closed, open, half-open
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        with self._lock:
            if self._state == "open":
                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._state = "half-open"
            return self._state

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._state = "closed"

    def record_failure(self, exc: Exception) -> None:
        if not isinstance(exc, self.expected_exception):
            return
        with self._lock:
            self._failures += 1
            self._last_failure_time = time.time()
            if self._failures >= self.failure_threshold:
                self._state = "open"
                log.warning("Circuit breaker opened after %d failures", self._failures)

    def call(self, func, *args, **kwargs):
        """Execute func with circuit breaker protection."""
        if self.state == "open":
            raise CircuitBreakerOpenError("Circuit breaker is open")
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except self.expected_exception as e:
            self.record_failure(e)
            raise


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


def retry_with_backoff(
    func,
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
    **kwargs,
):
    """Execute func with exponential backoff retry."""
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except retry_exceptions as e:
            last_exception = e
            if attempt < max_retries:
                delay = min(base_delay * (exponential_base ** attempt), max_delay)
                log.warning(
                    "Attempt %d/%d failed: %s. Retrying in %.1fs...",
                    attempt + 1, max_retries + 1, e, delay
                )
                time.sleep(delay)
            else:
                log.exception("All %d retry attempts exhausted", max_retries + 1)
    raise last_exception


class FakeBroker:
    """In-process broker for testing. Thread-safe."""

    def __init__(
        self,
        starting_cash: float = 100_000.0,
        commission: float = 0.0,
    ):
        self._lock = threading.RLock()
        self._prices: dict[str, float] = {}
        self._cash = starting_cash
        self._positions: dict[str, int] = {}
        self._commission = commission
        self.fills: list[Fill] = []

    def buy(self, ticker: str, shares: int) -> Fill:
        with self._lock:
            price = self._prices.get(ticker, 100.0)
            cost = shares * price + shares * self._commission
            if cost > self._cash:
                raise ValueError(f"insufficient cash: ${cost:.2f} > ${self._cash:.2f}")
            self._cash -= cost
            self._positions[ticker] = self._positions.get(ticker, 0) + shares
            fill = Fill(
                ticker=ticker,
                side="BUY",
                shares=shares,
                fill_price=price,
                notional=shares * price,
                broker_id=f"FAKE-{uuid.uuid4().hex[:8]}",
                filled_at=datetime.now(timezone.utc).isoformat(),
            )
            self.fills.append(fill)
            log.debug("FakeBroker BUY: %s %d shares @ $%.2f", ticker, shares, price)
            return fill

    def sell(self, ticker: str, shares: int) -> Fill:
        with self._lock:
            if self._positions.get(ticker, 0) < shares:
                raise ValueError(
                    f"can't sell {shares} {ticker}, only hold "
                    f"{self._positions.get(ticker, 0)}"
                )
            price = self._prices.get(ticker, 100.0)
            proceeds = shares * price - shares * self._commission
            self._cash += proceeds
            self._positions[ticker] -= shares
            if self._positions[ticker] == 0:
                del self._positions[ticker]
            fill = Fill(
                ticker=ticker,
                side="SELL",
                shares=shares,
                fill_price=price,
                notional=shares * price,
                broker_id=f"FAKE-{uuid.uuid4().hex[:8]}",
                filled_at=datetime.now(timezone.utc).isoformat(),
            )
            self.fills.append(fill)
            log.debug("FakeBroker SELL: %s %d shares @ $%.2f", ticker, shares, price)
            return fill

    def cash(self) -> float:
        with self._lock:
            return self._cash

    def positions(self) -> dict[str, int]:
        with self._lock:
            return dict(self._positions)

    def set_price(self, ticker: str, price: float) -> None:
        with self._lock:
            self._prices[ticker] = price


class AlpacaPaperBroker:
    """Real Alpaca paper-trading adapter with retry logic and circuit breaker.

    Requires env vars:
      ALPACA_API_KEY, ALPACA_SECRET_KEY
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        base_url: str = "https://paper-api.alpaca.markets",
        max_retries: int = 3,
        base_retry_delay: float = 1.0,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: float = 30.0,
    ):
        self._lock = threading.RLock()
        self._api = None
        self._live = False
        self._init_err: Optional[str] = None
        self._max_retries = max_retries
        self._base_retry_delay = base_retry_delay
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_breaker_threshold,
            recovery_timeout=circuit_breaker_timeout,
            expected_exception=Exception,
        )

        # Try to initialize Alpaca API
        self._initialize(api_key, secret_key, base_url)

    def _initialize(
        self,
        api_key: Optional[str],
        secret_key: Optional[str],
        base_url: str,
    ) -> None:
        try:
            from alpaca_trade_api import REST  # type: ignore
            key = api_key or os.environ.get("ALPACA_API_KEY")
            secret = secret_key or os.environ.get("ALPACA_SECRET_KEY")
            if not key or not secret:
                raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set")
            self._api = REST(key_id=key, secret_key=secret, base_url=base_url)
            # Test connection
            self._api.get_account()
            self._live = True
            log.info("AlpacaPaperBroker initialized successfully")
        except Exception as e:
            self._api = None
            self._live = False
            self._init_err = str(e)
            log.warning("AlpacaPaperBroker initialization failed: %s", e)

    def _require_live(self) -> None:
        if not self._live:
            raise RuntimeError(
                f"Alpaca not configured ({self._init_err}); "
                "set ALPACA_API_KEY and ALPACA_SECRET_KEY, or use FakeBroker"
            )

    def _execute_with_retry(self, func, *args, **kwargs):
        """Execute with circuit breaker and retry."""
        return self._circuit_breaker.call(
            lambda: retry_with_backoff(
                func,
                *args,
                max_retries=self._max_retries,
                base_delay=self._base_retry_delay,
                **kwargs,
            )
        )

    def buy(self, ticker: str, shares: int) -> Fill:
        self._require_live()
        return self._execute_with_retry(self._submit, ticker, shares, "buy")

    def sell(self, ticker: str, shares: int) -> Fill:
        self._require_live()
        return self._execute_with_retry(self._submit, ticker, shares, "sell")

    def _submit(self, ticker: str, shares: int, side: str) -> Fill:
        def _do_submit():
            order = self._api.submit_order(
                symbol=ticker, qty=shares, side=side,
                type="market", time_in_force="day",
            )
            # Poll for fill with timeout
            for _ in range(40):  # 10 seconds max
                order = self._api.get_order(order.id)
                if order.filled_avg_price:
                    break
                time.sleep(0.25)
            else:
                raise TimeoutError(f"Order {order.id} not filled within timeout")

            price = float(order.filled_avg_price or 0)
            if price <= 0:
                raise ValueError(f"Invalid fill price: {price}")

            return Fill(
                ticker=ticker,
                side=side.upper(),
                shares=shares,
                fill_price=price,
                notional=shares * price,
                broker_id=order.id,
                filled_at=order.filled_at.isoformat() if order.filled_at else datetime.now(timezone.utc).isoformat(),
            )

        return _do_submit()

    def cash(self) -> float:
        self._require_live()
        return self._execute_with_retry(self._get_cash)

    def _get_cash(self) -> float:
        account = self._api.get_account()
        return float(account.cash)

    def positions(self) -> dict[str, int]:
        self._require_live()
        return self._execute_with_retry(self._get_positions)

    def _get_positions(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for p in self._api.list_positions():
            out[p.symbol] = int(p.qty)
        return out

    @property
    def is_live(self) -> bool:
        return self._live

    @property
    def circuit_breaker_state(self) -> str:
        return self._circuit_breaker.state
