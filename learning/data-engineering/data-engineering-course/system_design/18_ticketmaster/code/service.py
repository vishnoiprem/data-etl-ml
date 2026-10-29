"""Ticketmaster-style service: events, seats, hold/purchase/release.

Concurrency model
-----------------
- A service-level RLock guards collection-level operations (event create,
  seat lookup map). Reentrant because some helpers re-acquire it.
- A `threading.Lock` *per seat* serializes the read-check-write sequence
  on the critical path so two concurrent hold/purchase/release calls on
  the same seat cannot both observe `available` and both succeed.
- A background sweeper thread expires stale holds (10-minute default TTL).
  The sweeper goes through the same per-seat lock, so it cannot race
  with an in-flight hold.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, asdict
from typing import Optional

from common.cache import TTLCache
from common.ids import Snowflake
from common.storage import KeyValueStore


# Defaults
DEFAULT_HOLD_TTL_SECONDS = 600.0  # 10 minutes
SEATS_CACHE_TTL = 5.0

STATUS_AVAILABLE = "available"
STATUS_HELD = "held"
STATUS_SOLD = "sold"


# --- domain exceptions ------------------------------------------------------


class TicketmasterError(Exception):
    """Base error with an HTTP-friendly code."""

    code: str = "internal_error"
    http_status: int = 500

    def __init__(self, message: str = ""):
        super().__init__(message or self.code)
        self.message = message or self.code


class EventNotFound(TicketmasterError):
    code = "event_not_found"
    http_status = 404


class SeatNotFound(TicketmasterError):
    code = "seat_not_found"
    http_status = 404


class SeatUnavailable(TicketmasterError):
    code = "seat_unavailable"
    http_status = 409


class HoldExpired(TicketmasterError):
    code = "hold_expired"
    http_status = 410


class HoldTokenMismatch(TicketmasterError):
    code = "hold_token_mismatch"
    http_status = 409


# --- domain objects ---------------------------------------------------------


@dataclass
class Event:
    event_id: int
    name: str
    rows: int
    cols: int
    created_at: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Seat:
    event_id: int
    seat_id: str  # e.g. "A-12"
    label: str
    section: str
    row: str
    col: int
    status: str = STATUS_AVAILABLE
    held_by: Optional[int] = None
    hold_token: Optional[int] = None
    hold_expires_at: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Ticket:
    ticket_id: int
    event_id: int
    seat_id: str
    user_id: int
    purchased_at: float

    def to_dict(self) -> dict:
        return asdict(self)


# --- service ----------------------------------------------------------------


class TicketmasterService:
    """Concurrency-safe seat reservation service.

    >>> svc = TicketmasterService(hold_ttl_seconds=60)
    >>> eid = svc.create_event("Concert", rows=2, cols=2)["event_id"]
    >>> seats = svc.list_seats(eid)
    >>> len(seats)
    4
    >>> r = svc.hold(eid, "A-1", user_id=1)
    >>> r["hold_token"] > 0
    True
    """

    def __init__(
        self,
        hold_ttl_seconds: float = DEFAULT_HOLD_TTL_SECONDS,
        sweeper_interval: float = 1.0,
        use_persistence: bool = False,
    ):
        self.hold_ttl = hold_ttl_seconds
        self.sweeper_interval = sweeper_interval

        self.snow = Snowflake(machine_id=18)

        # Persistence optional (disabled in tests for clean state).
        persist = None if not use_persistence else None  # KV default
        self.events = KeyValueStore("tm_events", persist_path=persist)
        self.seats = KeyValueStore("tm_seats", persist_path=persist)
        self.tickets = KeyValueStore("tm_tickets", persist_path=persist)

        # Aggregate lock — collection-level, reentrant.
        self._agg_lock = threading.RLock()
        # Per-seat lock — the critical path.
        self._seat_locks: dict[str, threading.Lock] = {}
        self._seat_locks_guard = threading.Lock()

        # Read cache: event_id -> [seat dicts]
        self._seat_cache = TTLCache(ttl_seconds=SEATS_CACHE_TTL)

        # Sweeper
        self._sweeper_stop = threading.Event()
        self._sweeper_thread: Optional[threading.Thread] = None
        self._start_sweeper()

        # Counters (lightweight, in-process; the Flask layer wires a
        # MetricsRegistry in front of these for /metrics).
        self.hold_attempts = 0
        self.hold_wins = 0
        self.hold_conflicts = 0
        self.purchases = 0
        self.releases = 0
        self.expirations = 0

    # ---- lifecycle ------------------------------------------------------

    def stop(self) -> None:
        """Stop the sweeper thread. Tests should call this in tearDown."""
        self._sweeper_stop.set()
        if self._sweeper_thread:
            self._sweeper_thread.join(timeout=2.0)
            self._sweeper_thread = None

    def _start_sweeper(self) -> None:
        self._sweeper_thread = threading.Thread(
            target=self._sweep_loop, name="tm-sweeper", daemon=True
        )
        self._sweeper_thread.start()

    def _sweep_loop(self) -> None:
        while not self._sweeper_stop.is_set():
            try:
                self._sweep_once()
            except Exception:  # pragma: no cover - sweeper must not die
                pass
            self._sweeper_stop.wait(self.sweeper_interval)

    def _sweep_once(self) -> int:
        """Drop all holds whose `expires_at < now`. Returns the count."""
        now = time.time()
        expired = 0
        # Walk active holds via the seat store; per-seat filters quickly.
        for _k, seat_dict in self.seats.scan("seat:"):
            if seat_dict.get("status") != STATUS_HELD:
                continue
            exp = seat_dict.get("hold_expires_at")
            if exp is None or exp > now:
                continue
            seat_id = seat_dict["seat_id"]
            event_id = seat_dict["event_id"]
            try:
                self._expire_hold(event_id, seat_id)
                expired += 1
            except Exception:
                # If a user is concurrently purchasing, the seat may
                # already be SOLD — that's fine, just skip.
                continue
        return expired

    # ---- per-seat lock factory -----------------------------------------

    def _lock_for(self, key: str) -> threading.Lock:
        with self._seat_locks_guard:
            lock = self._seat_locks.get(key)
            if lock is None:
                lock = threading.Lock()
                self._seat_locks[key] = lock
            return lock

    # ---- key helpers ---------------------------------------------------

    @staticmethod
    def _seat_key(event_id: int, seat_id: str) -> str:
        return f"seat:{event_id}:{seat_id}"

    @staticmethod
    def _event_key(event_id: int) -> str:
        return f"event:{event_id}"

    @staticmethod
    def _ticket_key(ticket_id: int) -> str:
        return f"ticket:{ticket_id}"

    # ---- events --------------------------------------------------------

    def create_event(self, name: str, rows: int, cols: int) -> dict:
        if rows <= 0 or cols <= 0:
            raise ValueError("rows and cols must be positive")
        with self._agg_lock:
            event_id = self.snow.next_id()
            event = Event(
                event_id=event_id,
                name=name,
                rows=rows,
                cols=cols,
                created_at=time.time(),
            )
            self.events.set(self._event_key(event_id), asdict(event))
            # Generate all seats up-front so the seat map is known.
            row_letters = [chr(ord("A") + i) for i in range(rows)]
            for r_idx, row_label in enumerate(row_letters):
                for c in range(1, cols + 1):
                    seat_id = f"{row_label}-{c}"
                    seat = Seat(
                        event_id=event_id,
                        seat_id=seat_id,
                        label=seat_id,
                        section="MAIN",
                        row=row_label,
                        col=c,
                        status=STATUS_AVAILABLE,
                    )
                    self.seats.set(
                        self._seat_key(event_id, seat_id), asdict(seat)
                    )
            # Bust the seat cache (any prior cached event_id is stale
            # under our namespace but be safe).
            self._seat_cache.clear()
            return asdict(event)

    def get_event(self, event_id: int) -> dict:
        with self._agg_lock:
            ev = self.events.get(self._event_key(event_id))
            if not ev:
                raise EventNotFound()
            return ev

    # ---- seats ---------------------------------------------------------

    def list_seats(self, event_id: int) -> list[dict]:
        # Cache hit
        cache_key = f"event:{event_id}:seats"
        cached = self._seat_cache.get(cache_key)
        if cached is not None:
            return cached
        # Event must exist
        with self._agg_lock:
            ev = self.events.get(self._event_key(event_id))
            if not ev:
                raise EventNotFound()
        seats: list[dict] = []
        for k, v in self.seats.scan("seat:"):
            if v.get("event_id") != event_id:
                continue
            seats.append(v)
        seats.sort(key=lambda s: (s["row"], s["col"]))
        self._seat_cache.set(cache_key, seats)
        return seats

    def get_seat(self, event_id: int, seat_id: str) -> dict:
        seat = self.seats.get(self._seat_key(event_id, seat_id))
        if not seat:
            raise SeatNotFound()
        return seat

    # ---- hold / purchase / release -------------------------------------

    def hold(self, event_id: int, seat_id: str, user_id: int) -> dict:
        """Atomically transition a seat to `held` for `user_id`."""
        if user_id is None:
            raise ValueError("user_id is required")
        self.hold_attempts += 1
        lock = self._lock_for(self._seat_key(event_id, seat_id))
        with lock:
            seat = self.seats.get(self._seat_key(event_id, seat_id))
            if not seat:
                raise SeatNotFound()
            if seat["status"] == STATUS_SOLD:
                self.hold_conflicts += 1
                raise SeatUnavailable("seat already sold")
            if seat["status"] == STATUS_HELD:
                # If expired, treat as available and re-claim; otherwise
                # conflict.
                if seat.get("hold_expires_at") and seat["hold_expires_at"] > time.time():
                    self.hold_conflicts += 1
                    raise SeatUnavailable("seat is currently held")
                # else: fall through to re-claim
            # Now claim it.
            token = self.snow.next_id()
            expires = time.time() + self.hold_ttl
            seat["status"] = STATUS_HELD
            seat["held_by"] = user_id
            seat["hold_token"] = token
            seat["hold_expires_at"] = expires
            self.seats.set(self._seat_key(event_id, seat_id), seat)
            self.hold_wins += 1
            self._seat_cache.delete(f"event:{event_id}:seats")
            return {
                "event_id": event_id,
                "seat_id": seat_id,
                "hold_token": token,
                "expires_at": expires,
                "user_id": user_id,
            }

    def purchase(
        self, event_id: int, seat_id: str, user_id: int, hold_token: int
    ) -> dict:
        """Convert a valid hold into a sold ticket."""
        if hold_token is None:
            raise HoldTokenMismatch("hold_token is required")
        lock = self._lock_for(self._seat_key(event_id, seat_id))
        with lock:
            seat = self.seats.get(self._seat_key(event_id, seat_id))
            if not seat:
                raise SeatNotFound()
            if seat["status"] == STATUS_SOLD:
                raise SeatUnavailable("seat already sold")
            if seat["status"] != STATUS_HELD:
                raise SeatUnavailable("seat is not held")
            if seat.get("hold_token") != hold_token or seat.get("held_by") != user_id:
                raise HoldTokenMismatch()
            if seat.get("hold_expires_at") and seat["hold_expires_at"] < time.time():
                # Sweeper hasn't caught up yet — refuse.
                self._clear_hold(seat)
                self.seats.set(self._seat_key(event_id, seat_id), seat)
                raise HoldExpired()
            seat["status"] = STATUS_SOLD
            seat["hold_token"] = None
            seat["hold_expires_at"] = None
            self.seats.set(self._seat_key(event_id, seat_id), seat)
            ticket_id = self.snow.next_id()
            ticket = Ticket(
                ticket_id=ticket_id,
                event_id=event_id,
                seat_id=seat_id,
                user_id=user_id,
                purchased_at=time.time(),
            )
            self.tickets.set(self._ticket_key(ticket_id), asdict(ticket))
            self.purchases += 1
            self._seat_cache.delete(f"event:{event_id}:seats")
            return asdict(ticket)

    def release(
        self, event_id: int, seat_id: str, user_id: int, hold_token: int
    ) -> dict:
        """User-initiated hold release."""
        lock = self._lock_for(self._seat_key(event_id, seat_id))
        with lock:
            seat = self.seats.get(self._seat_key(event_id, seat_id))
            if not seat:
                raise SeatNotFound()
            if seat["status"] != STATUS_HELD:
                raise SeatUnavailable("seat is not held")
            if seat.get("hold_token") != hold_token or seat.get("held_by") != user_id:
                raise HoldTokenMismatch()
            self._clear_hold(seat)
            self.seats.set(self._seat_key(event_id, seat_id), seat)
            self.releases += 1
            self._seat_cache.delete(f"event:{event_id}:seats")
            return {"released": True, "event_id": event_id, "seat_id": seat_id}

    # ---- internal: hold lifecycle -------------------------------------

    def _expire_hold(self, event_id: int, seat_id: str) -> None:
        lock = self._lock_for(self._seat_key(event_id, seat_id))
        with lock:
            seat = self.seats.get(self._seat_key(event_id, seat_id))
            if not seat:
                return
            if seat["status"] != STATUS_HELD:
                return
            if seat.get("hold_expires_at") and seat["hold_expires_at"] > time.time():
                return  # extended or freshly re-held
            self._clear_hold(seat)
            self.seats.set(self._seat_key(event_id, seat_id), seat)
            self.expirations += 1
            self._seat_cache.delete(f"event:{event_id}:seats")

    @staticmethod
    def _clear_hold(seat: dict) -> None:
        seat["status"] = STATUS_AVAILABLE
        seat["held_by"] = None
        seat["hold_token"] = None
        seat["hold_expires_at"] = None

    # ---- stats ---------------------------------------------------------

    def stats(self) -> dict:
        with self._agg_lock:
            return {
                "events": self.events.size(),
                "seats": self.seats.size(),
                "tickets": self.tickets.size(),
                "hold_attempts": self.hold_attempts,
                "hold_wins": self.hold_wins,
                "hold_conflicts": self.hold_conflicts,
                "purchases": self.purchases,
                "releases": self.releases,
                "expirations": self.expirations,
                "hold_ttl_seconds": self.hold_ttl,
                "cache": self._seat_cache.stats(),
            }
