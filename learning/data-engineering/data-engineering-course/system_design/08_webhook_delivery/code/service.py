"""Webhook delivery service.

A working implementation of the design in ``design/README.md``:

* Subscriptions registered with a URL, secret, and event-type filter.
* Each ``deliver`` enqueues a delivery; a background thread dispatches
  in the background.
* HMAC-SHA256 signature (Stripe-style) over ``<ts>.<body>``.
* Exponential backoff with jitter, capped at ``max_attempts``.
* DLQ (status=dead) listable + replayable.

The HTTP layer in ``app.py`` is a thin wrapper around this class.
The transport is pluggable: tests inject a ``SimulatedTransport`` to
control outcomes; production wires a real HTTP client.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import random
import threading
import time
from dataclasses import dataclass, asdict, field
from typing import Optional, Protocol

from common.ids import Snowflake
from common.storage import KeyValueStore

# Default delivery tunables. See design §7.
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_BASE_DELAY_S = 1.0
DEFAULT_MAX_DELAY_S = 300.0
LOOP_INTERVAL_S = 0.1

# Per-attempt HTTP timeout.
ATTEMPT_TIMEOUT_S = 10.0

# HTTP status classes we treat as retryable.
RETRYABLE_STATUSES = set(range(500, 600))


# ---------------------------------------------------------------------------
# Transport interface (design §3)
# ---------------------------------------------------------------------------


class Transport(Protocol):
    """Send a webhook. Implementations return ``(status_code, error)``.

    A real implementation would use ``requests`` or ``httpx``; for the
    lesson we ship a deterministic simulator the tests can drive.
    """

    def send(
        self,
        url: str,
        body: str,
        headers: dict,
        timeout_s: float,
    ) -> tuple[Optional[int], Optional[str], float]:
        """Returns (status_code, error, latency_ms)."""
        ...


class SimulatedTransport:
    """A transport that records every send and returns a configurable result.

    The test harness pushes outcomes via :meth:`queue_outcome`; if no
    outcome is queued, it returns ``(200, None, 1.0)`` (success).
    """

    def __init__(self):
        self._outcomes: list[tuple[Optional[int], Optional[str]]] = []
        self._lock = threading.Lock()
        self.calls: list[dict] = []

    def queue_outcome(
        self,
        status_code: Optional[int] = 200,
        error: Optional[str] = None,
    ) -> None:
        with self._lock:
            self._outcomes.append((status_code, error))

    def send(
        self,
        url: str,
        body: str,
        headers: dict,
        timeout_s: float,
    ) -> tuple[Optional[int], Optional[str], float]:
        with self._lock:
            self.calls.append({"url": url, "body": body, "headers": dict(headers)})
            if self._outcomes:
                status, err = self._outcomes.pop(0)
            else:
                status, err = 200, None
        # Tiny sleep so the latency histogram isn't all zeros.
        time.sleep(0.001)
        return status, err, 1.0

    def reset(self) -> None:
        with self._lock:
            self._outcomes.clear()
            self.calls.clear()


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass
class Subscription:
    subscription_id: str
    url: str
    secret: str
    event_types: list
    created_at: float
    delivered_total: int = 0
    retried_total: int = 0
    dlq_total: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Delivery:
    delivery_id: str
    subscription_id: str
    event: str
    payload: dict
    status: str  # "pending" | "delivered" | "dead"
    attempts: int
    max_attempts: int
    next_attempt_at: float
    created_at: float
    last_status_code: Optional[int] = None
    last_error: Optional[str] = None
    last_attempt_at: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Attempt:
    n: int
    ts: float
    status_code: Optional[int]
    latency_ms: float
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class WebhookService:
    """A working webhook delivery service.

    >>> svc = WebhookService(transport=SimulatedTransport())
    >>> sub = svc.create_subscription(url="https://example.com/hook",
    ...                                secret="s3cret",
    ...                                event_types=["order.placed"])
    >>> d = svc.deliver(sub.subscription_id, event="order.placed",
    ...                  payload={"order_id": 1})
    >>> d.status
    'pending'
    >>> svc.dispatch_pending_now()  # synchronously run one pass
    >>> d = svc.get_delivery(d.delivery_id)
    >>> d.status
    'delivered'
    """

    def __init__(
        self,
        store: Optional[KeyValueStore] = None,
        id_gen: Optional[Snowflake] = None,
        transport: Optional[Transport] = None,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        base_delay_s: float = DEFAULT_BASE_DELAY_S,
        max_delay_s: float = DEFAULT_MAX_DELAY_S,
        loop_interval_s: float = LOOP_INTERVAL_S,
    ):
        self.store = store or KeyValueStore("webhook_delivery")
        self.id_gen = id_gen or Snowflake(machine_id=8)
        self.transport = transport or SimulatedTransport()
        self.max_attempts = max_attempts
        self.base_delay_s = base_delay_s
        self.max_delay_s = max_delay_s
        self.loop_interval_s = loop_interval_s

        # Coordination
        self._lock = threading.RLock()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._in_flight: set[str] = set()
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # lifecycle (design §3 delivery loop)
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the background delivery loop. Idempotent."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, name="webhook-delivery", daemon=True
        )
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        """Signal the loop to stop and wait for it."""
        self._stop.set()
        self._wake.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
        self._thread = None

    def dispatch_pending_now(self) -> int:
        """Run one synchronous pass over pending deliveries. Returns
        the number of deliveries touched. Tests use this to drive
        delivery deterministically without the background thread.
        """
        touched = 0
        now = time.time()
        for d in self._pending_snap(now):
            if d.delivery_id in self._in_flight:
                continue
            with self._lock:
                self._in_flight.add(d.delivery_id)
            try:
                self._dispatch(d)
                touched += 1
            finally:
                with self._lock:
                    self._in_flight.discard(d.delivery_id)
        return touched

    # ------------------------------------------------------------------
    # subscriptions — design §4
    # ------------------------------------------------------------------

    def create_subscription(
        self,
        url: str,
        secret: str,
        event_types: Optional[list] = None,
    ) -> Subscription:
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            raise ValueError("url must be a valid http(s) URL")
        if not isinstance(secret, str) or len(secret) < 8:
            raise ValueError("secret must be a string of length >= 8")
        sub = Subscription(
            subscription_id=str(self.id_gen.next_id()),
            url=url,
            secret=secret,
            event_types=list(event_types or []),
            created_at=time.time(),
        )
        self.store.set(self._k_sub(sub.subscription_id), sub.to_dict())
        return sub

    def get_subscription(self, sub_id: str) -> Optional[Subscription]:
        d = self.store.get(self._k_sub(sub_id))
        return Subscription(**d) if d else None

    def list_subscriptions(self) -> list[Subscription]:
        out: list[Subscription] = []
        for k, v in self.store.scan("sub:"):
            if isinstance(v, dict):
                out.append(Subscription(**v))
        out.sort(key=lambda s: s.created_at)
        return out

    # ------------------------------------------------------------------
    # deliveries — design §6
    # ------------------------------------------------------------------

    def deliver(
        self,
        subscription_id: str,
        event: str,
        payload: dict,
        max_attempts: Optional[int] = None,
    ) -> Delivery:
        sub = self.get_subscription(subscription_id)
        if sub is None:
            raise ValueError(f"unknown subscription {subscription_id!r}")
        if sub.event_types and event not in sub.event_types:
            raise ValueError(
                f"event {event!r} not in subscription filter {sub.event_types}"
            )
        if not isinstance(event, str) or not event:
            raise ValueError("event must be a non-empty string")
        if not isinstance(payload, dict):
            raise ValueError("payload must be a dict")

        d = Delivery(
            delivery_id=str(self.id_gen.next_id()),
            subscription_id=subscription_id,
            event=event,
            payload=dict(payload),
            status="pending",
            attempts=0,
            max_attempts=int(max_attempts) if max_attempts else self.max_attempts,
            next_attempt_at=time.time(),
            created_at=time.time(),
        )
        self.store.set(self._k_del(d.delivery_id), d.to_dict())
        # Wake the loop.
        self._wake.set()
        return d

    def get_delivery(self, delivery_id: str) -> Optional[Delivery]:
        d = self.store.get(self._k_del(delivery_id))
        return Delivery(**d) if d else None

    def list_deliveries(self, subscription_id: str) -> list[Delivery]:
        out: list[Delivery] = []
        for k, v in self.store.scan("del:"):
            if isinstance(v, dict) and v.get("subscription_id") == subscription_id:
                out.append(Delivery(**v))
        out.sort(key=lambda d: d.created_at, reverse=True)
        return out

    def list_dlq(self) -> list[Delivery]:
        out: list[Delivery] = []
        for k, v in self.store.scan("del:"):
            if isinstance(v, dict) and v.get("status") == "dead":
                out.append(Delivery(**v))
        out.sort(key=lambda d: d.created_at, reverse=True)
        return out

    def attempts_for(self, delivery_id: str) -> list[Attempt]:
        out: list[Attempt] = []
        prefix = f"attempt:{delivery_id}:"
        for k, v in self.store.scan("attempt:"):
            if k.startswith(prefix) and isinstance(v, dict):
                out.append(Attempt(**v))
        out.sort(key=lambda a: a.n)
        return out

    def replay(self, subscription_id: str, delivery_id: str) -> Delivery:
        d = self.get_delivery(delivery_id)
        if d is None:
            raise ValueError(f"unknown delivery {delivery_id!r}")
        if d.subscription_id != subscription_id:
            raise ValueError("delivery does not belong to subscription")
        # Reset and re-enqueue.
        d.status = "pending"
        d.attempts = 0
        d.next_attempt_at = time.time()
        d.last_error = None
        d.last_status_code = None
        self.store.set(self._k_del(d.delivery_id), d.to_dict())
        self._wake.set()
        return d

    # ------------------------------------------------------------------
    # signing — design §7
    # ---------------------------------------------------------------------------

    @staticmethod
    def sign(secret: str, body: str, ts: Optional[int] = None) -> str:
        """Stripe-style signature header value.

        Returns ``"t=<unix_ts>,v1=<hex>"`` where ``hex`` is
        ``HMAC_SHA256(secret, f"{ts}.{body}")``.
        """
        ts = ts if ts is not None else int(time.time())
        mac = hmac.new(
            secret.encode("utf-8"),
            f"{ts}.{body}".encode("utf-8"),
            hashlib.sha256,
        )
        return f"t={ts},v1={mac.hexdigest()}"

    # ------------------------------------------------------------------
    # delivery loop internals
    # ------------------------------------------------------------------

    def _loop(self) -> None:
        while not self._stop.is_set():
            # Wait for either a wakeup or the loop tick.
            self._wake.wait(timeout=self.loop_interval_s)
            self._wake.clear()
            if self._stop.is_set():
                return
            try:
                self.dispatch_pending_now()
            except Exception:
                # Never let a bug in dispatch kill the loop.
                time.sleep(0.05)

    def _pending_snap(self, now: float) -> list[Delivery]:
        out: list[Delivery] = []
        for k, v in self.store.scan("del:"):
            if not isinstance(v, dict):
                continue
            if v.get("status") != "pending":
                continue
            if v.get("next_attempt_at", 0) > now:
                continue
            out.append(Delivery(**v))
        out.sort(key=lambda d: d.next_attempt_at)
        return out

    def _dispatch(self, d: Delivery) -> None:
        sub = self.get_subscription(d.subscription_id)
        if sub is None:
            # Subscription deleted between enqueue and dispatch.
            d.status = "dead"
            d.last_error = "subscription not found"
            self.store.set(self._k_del(d.delivery_id), d.to_dict())
            return

        d.attempts += 1
        d.last_attempt_at = time.time()

        body = json.dumps(
            {
                "id": d.delivery_id,
                "event": d.event,
                "payload": d.payload,
            },
            separators=(",", ":"),
        )
        ts = int(d.last_attempt_at)
        signature = self.sign(sub.secret, body, ts=ts)
        headers = {
            "Content-Type": "application/json",
            "X-Signature": signature,
            "X-Event": d.event,
            "X-Delivery-Id": d.delivery_id,
        }

        try:
            status, err, latency_ms = self.transport.send(
                url=sub.url,
                body=body,
                headers=headers,
                timeout_s=ATTEMPT_TIMEOUT_S,
            )
        except Exception as e:
            # Treat any transport exception as a transient failure.
            status, err, latency_ms = None, str(e), 0.0

        # Record the attempt.
        self.store.set(
            self._k_attempt(d.delivery_id, d.attempts),
            Attempt(
                n=d.attempts,
                ts=d.last_attempt_at,
                status_code=status,
                latency_ms=latency_ms,
                error=err,
            ).to_dict(),
        )

        d.last_status_code = status
        d.last_error = err

        if status is not None and 200 <= status < 300:
            d.status = "delivered"
            sub.delivered_total += 1
            self._bump_subscription(sub)
        elif status is not None and 400 <= status < 500:
            # Permanent — bad request, not retriable.
            d.status = "dead"
            sub.dlq_total += 1
            self._bump_subscription(sub)
        else:
            # Transient: 5xx, timeout, network error.
            if d.attempts >= d.max_attempts:
                d.status = "dead"
                sub.dlq_total += 1
                self._bump_subscription(sub)
            else:
                delay = self._backoff(d.attempts)
                d.next_attempt_at = time.time() + delay
                sub.retried_total += 1
                self._bump_subscription(sub)
        self.store.set(self._k_del(d.delivery_id), d.to_dict())

    def _backoff(self, attempt: int) -> float:
        """Exponential backoff with jitter, capped at max_delay_s."""
        delay = self.base_delay_s * (2 ** (attempt - 1))
        delay = min(delay, self.max_delay_s)
        # Jitter: +/- 25 %.
        jitter = delay * 0.25
        return max(0.0, delay + random.uniform(-jitter, jitter))

    def _bump_subscription(self, sub: Subscription) -> None:
        self.store.set(self._k_sub(sub.subscription_id), sub.to_dict())

    # ------------------------------------------------------------------
    # stats
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        subs = self.list_subscriptions()
        total_deliveries = 0
        delivered = 0
        dead = 0
        pending = 0
        for k, v in self.store.scan("del:"):
            if not isinstance(v, dict):
                continue
            total_deliveries += 1
            s = v.get("status")
            if s == "delivered":
                delivered += 1
            elif s == "dead":
                dead += 1
            elif s == "pending":
                pending += 1
        return {
            "subscriptions": len(subs),
            "deliveries": total_deliveries,
            "delivered": delivered,
            "dlq": dead,
            "pending": pending,
            "loop_alive": bool(self._thread and self._thread.is_alive()),
        }

    # ------------------------------------------------------------------
    # key naming
    # ------------------------------------------------------------------

    @staticmethod
    def _k_sub(sid: str) -> str:
        return f"sub:{sid}"

    @staticmethod
    def _k_del(did: str) -> str:
        return f"del:{did}"

    @staticmethod
    def _k_attempt(did: str, n: int) -> str:
        return f"attempt:{did}:{n}"
