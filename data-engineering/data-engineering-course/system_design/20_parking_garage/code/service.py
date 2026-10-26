"""Parking-garage service: multi-floor, real-time spot allocation.

Concurrency model
-----------------
- A service-level RLock guards collection-level state and config.
- A per-floor RLock serializes allocation within a floor: the
  algorithm walks spots in ascending order, so two threads cannot
  both see "first free spot is F1-S007" and both take it.
- A per-spot threading.Lock is held during the final claim for an
  extra layer of safety (TOCTOU defence).
- On every check-in/check-out, the per-floor free counter is
  decremented/incremented so `GET /api/availability` is O(floors),
  not O(spots).
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, asdict
from typing import Optional

from common.cache import TTLCache
from common.ids import Snowflake
from common.storage import KeyValueStore


# Spot types
TYPE_STANDARD = "standard"
TYPE_COMPACT = "compact"
TYPE_EV = "ev"

# Spot status
STATUS_FREE = "free"
STATUS_OCCUPIED = "occupied"

# Defaults
DEFAULT_RATE_CENTS_PER_HOUR = 500  # $5.00 / hour
AVAIL_CACHE_TTL = 1.0


# --- exceptions -----------------------------------------------------------


class ParkingError(Exception):
    code: str = "internal_error"
    http_status: int = 500

    def __init__(self, message: str = ""):
        super().__init__(message or self.code)
        self.message = message or self.code


class GarageFull(ParkingError):
    code = "garage_full"
    http_status = 503


class NoSpotForType(ParkingError):
    code = "no_spot_for_type"
    http_status = 409


class TicketNotFound(ParkingError):
    code = "ticket_not_found"
    http_status = 404


class TicketAlreadyClosed(ParkingError):
    code = "ticket_already_closed"
    http_status = 409


# --- domain objects ------------------------------------------------------


@dataclass
class Spot:
    spot_id: str
    floor: int
    number: int
    type: str
    status: str = STATUS_FREE

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Session:
    ticket_id: int
    vehicle_id: int
    spot_id: str
    floor: int
    type: str
    checkin_at: float
    checkout_at: Optional[float] = None
    fee_cents: Optional[int] = None
    duration_seconds: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


# --- service -------------------------------------------------------------


class ParkingGarageService:
    """Multi-floor parking garage with closest-to-entry allocation.

    >>> svc = ParkingGarageService(floors=2, spots_per_floor=4)
    >>> t = svc.checkin(vehicle_id=1)
    >>> t["spot_id"].startswith("F")
    True
    >>> out = svc.checkout(t["ticket_id"])
    >>> out["fee_cents"] >= 0
    True
    """

    def __init__(
        self,
        floors: int = 3,
        spots_per_floor: int = 20,
        rate_cents_per_hour: int = DEFAULT_RATE_CENTS_PER_HOUR,
        use_persistence: bool = False,
    ):
        if floors <= 0 or spots_per_floor <= 0:
            raise ValueError("floors and spots_per_floor must be positive")
        self.floors = floors
        self.spots_per_floor = spots_per_floor
        self.rate_cents_per_hour = rate_cents_per_hour

        self.snow = Snowflake(machine_id=20)

        persist = None
        self.spots = KeyValueStore("pg_spots", persist_path=persist)
        self.sessions = KeyValueStore("pg_sessions", persist_path=persist)
        # active_sessions:{ticket_id} -> True
        self.active_index = KeyValueStore("pg_active_idx", persist_path=persist)

        self._agg_lock = threading.RLock()
        # per-floor lock
        self._floor_locks: dict[int, threading.RLock] = {}
        self._floor_locks_guard = threading.Lock()
        # per-spot lock
        self._spot_locks: dict[str, threading.Lock] = {}
        self._spot_locks_guard = threading.Lock()
        # per-floor free counts — atomic int-like with a lock
        self._free_counts: dict[int, int] = {}
        self._free_counts_lock = threading.RLock()

        # Read cache for availability
        self._avail_cache = TTLCache(ttl_seconds=AVAIL_CACHE_TTL)

        # Build initial spot map.
        self._build_spots()

        # Counters
        self.checkin_total = 0
        self.checkout_total = 0
        self.garage_full_count = 0
        self.no_spot_for_type_count = 0

    # ---- initial layout ------------------------------------------------

    def _spot_type_for(self, floor: int, number: int) -> str:
        # Rotate by index within floor.
        idx = (number - 1) % self.spots_per_floor
        ratio = idx / max(1, self.spots_per_floor)
        if ratio < 0.40:
            return TYPE_STANDARD
        if ratio < 0.75:
            return TYPE_COMPACT
        return TYPE_EV

    def _build_spots(self) -> None:
        with self._agg_lock:
            for f in range(1, self.floors + 1):
                floor_free = 0
                for n in range(1, self.spots_per_floor + 1):
                    spot_id = f"F{f}-S{n:03d}"
                    spot = Spot(
                        spot_id=spot_id,
                        floor=f,
                        number=n,
                        type=self._spot_type_for(f, n),
                        status=STATUS_FREE,
                    )
                    self.spots.set(self._spot_key(spot_id), asdict(spot))
                    floor_free += 1
                with self._free_counts_lock:
                    self._free_counts[f] = floor_free

    # ---- per-floor / per-spot lock factory ---------------------------

    def _lock_for_floor(self, floor: int) -> threading.RLock:
        with self._floor_locks_guard:
            lock = self._floor_locks.get(floor)
            if lock is None:
                lock = threading.RLock()
                self._floor_locks[floor] = lock
            return lock

    def _lock_for_spot(self, spot_id: str) -> threading.Lock:
        with self._spot_locks_guard:
            lock = self._spot_locks.get(spot_id)
            if lock is None:
                lock = threading.Lock()
                self._spot_locks[spot_id] = lock
            return lock

    def _dec_free(self, floor: int) -> None:
        with self._free_counts_lock:
            self._free_counts[floor] = max(0, self._free_counts.get(floor, 0) - 1)

    def _inc_free(self, floor: int) -> None:
        with self._free_counts_lock:
            cap = self.spots_per_floor
            self._free_counts[floor] = min(cap, self._free_counts.get(floor, 0) + 1)

    # ---- key helpers --------------------------------------------------

    @staticmethod
    def _spot_key(spot_id: str) -> str:
        return f"spot:{spot_id}"

    @staticmethod
    def _session_key(ticket_id: int) -> str:
        return f"session:{ticket_id}"

    @staticmethod
    def _active_key(ticket_id: int) -> str:
        return f"active:{ticket_id}"

    # ---- check-in / check-out -----------------------------------------

    def checkin(self, vehicle_id: int, preferred_type: Optional[str] = None) -> dict:
        if vehicle_id is None:
            raise ValueError("vehicle_id is required")
        # Iterate floors in order (lowest = closest to entry).
        for f in range(1, self.floors + 1):
            lock = self._lock_for_floor(f)
            with lock:
                chosen = self._find_free_spot_on_floor(f, preferred_type)
                if not chosen:
                    continue
                # Final atomic claim.
                spot_lock = self._lock_for_spot(chosen)
                with spot_lock:
                    spot = self.spots.get(self._spot_key(chosen))
                    if not spot or spot["status"] != STATUS_FREE:
                        # Someone else got it; loop continues but on this
                        # same lock we won't see the same spot again.
                        continue
                    spot["status"] = STATUS_OCCUPIED
                    self.spots.set(self._spot_key(chosen), spot)
                    self._dec_free(f)
                    self._avail_cache.clear()
                    ticket_id = self.snow.next_id()
                    session = Session(
                        ticket_id=ticket_id,
                        vehicle_id=vehicle_id,
                        spot_id=chosen,
                        floor=f,
                        type=spot["type"],
                        checkin_at=time.time(),
                    )
                    self.sessions.set(self._session_key(ticket_id), asdict(session))
                    self.active_index.set(self._active_key(ticket_id), True)
                    self.checkin_total += 1
                    return asdict(session)
        # Fell out of the floor loop.
        if preferred_type is not None:
            # Try again with no preference.
            retry = self.checkin(vehicle_id, preferred_type=None)
            self.no_spot_for_type_count += 1
            return retry
        self.garage_full_count += 1
        raise GarageFull("no free spots in any floor")

    def _find_free_spot_on_floor(
        self, floor: int, preferred_type: Optional[str]
    ) -> Optional[str]:
        # Walk all spots on this floor; return the first free match.
        # preferred_type honored first; if none found, fall back to any.
        primary = None
        fallback = None
        for n in range(1, self.spots_per_floor + 1):
            spot_id = f"F{floor}-S{n:03d}"
            spot = self.spots.get(self._spot_key(spot_id))
            if not spot or spot["status"] != STATUS_FREE:
                continue
            if preferred_type and spot["type"] == preferred_type:
                if primary is None:
                    primary = spot_id
                    break  # earliest match on this floor
            else:
                if fallback is None and preferred_type is None:
                    fallback = spot_id
        if preferred_type:
            return primary
        return fallback

    def checkout(self, ticket_id: int) -> dict:
        s = self.sessions.get(self._session_key(ticket_id))
        if not s:
            raise TicketNotFound()
        if s.get("checkout_at") is not None:
            raise TicketAlreadyClosed()
        spot_id = s["spot_id"]
        floor = s["floor"]
        spot_lock = self._lock_for_spot(spot_id)
        with spot_lock:
            # Re-read inside the lock.
            s = self.sessions.get(self._session_key(ticket_id))
            if not s:
                raise TicketNotFound()
            if s.get("checkout_at") is not None:
                raise TicketAlreadyClosed()
            spot = self.spots.get(self._spot_key(spot_id))
            if spot and spot["status"] == STATUS_OCCUPIED:
                spot["status"] = STATUS_FREE
                self.spots.set(self._spot_key(spot_id), spot)
            self._inc_free(floor)
            self._avail_cache.clear()
            checkout_at = time.time()
            duration = checkout_at - s["checkin_at"]
            fee = self._compute_fee(duration)
            s["checkout_at"] = checkout_at
            s["duration_seconds"] = duration
            s["fee_cents"] = fee
            self.sessions.set(self._session_key(ticket_id), s)
            self.active_index.delete(self._active_key(ticket_id))
            self.checkout_total += 1
            return s

    def _compute_fee(self, duration_seconds: float) -> int:
        # Round up to the next hour. Minimum 1 hour.
        hours = max(1, int((duration_seconds + 3599) // 3600))
        return hours * self.rate_cents_per_hour

    # ---- queries ------------------------------------------------------

    def availability(self) -> dict:
        cached = self._avail_cache.get("availability")
        if cached is not None:
            return cached
        with self._free_counts_lock:
            per_floor = {f: self._free_counts.get(f, 0) for f in range(1, self.floors + 1)}
        total_free = sum(per_floor.values())
        out = {
            "total_free": total_free,
            "total_capacity": self.floors * self.spots_per_floor,
            "per_floor": per_floor,
        }
        self._avail_cache.set("availability", out)
        return out

    def list_spots(self) -> list[dict]:
        out = []
        for _k, v in self.spots.scan("spot:"):
            out.append(v)
        out.sort(key=lambda s: (s["floor"], s["number"]))
        return out

    def get_ticket(self, ticket_id: int) -> dict:
        s = self.sessions.get(self._session_key(ticket_id))
        if not s:
            raise TicketNotFound()
        return s

    def list_active_sessions(self) -> list[dict]:
        out = []
        for k, _v in self.active_index.scan("active:"):
            tid = int(k.split(":")[1])
            s = self.sessions.get(self._session_key(tid))
            if s and s.get("checkout_at") is None:
                out.append(s)
        out.sort(key=lambda s: s["checkin_at"])
        return out

    # ---- stats --------------------------------------------------------

    def stats(self) -> dict:
        return {
            "floors": self.floors,
            "spots_per_floor": self.spots_per_floor,
            "total_capacity": self.floors * self.spots_per_floor,
            "availability": self.availability(),
            "active_sessions": len(self.list_active_sessions()),
            "checkin_total": self.checkin_total,
            "checkout_total": self.checkout_total,
            "garage_full_count": self.garage_full_count,
            "no_spot_for_type_count": self.no_spot_for_type_count,
            "rate_cents_per_hour": self.rate_cents_per_hour,
            "cache": self._avail_cache.stats(),
        }
