"""Hotel-booking service: hotels, rooms, date-range bookings, no double-booking.

Concurrency model
-----------------
- A service-level RLock guards collection-level operations (hotel create,
  room add). Reentrant because some helpers re-enter.
- A `threading.RLock` *per room* serializes the read-check-write sequence
  on the critical booking/cancel/availability path so two concurrent
  requests for overlapping dates cannot both win.
- Bookings are stored as `Booking` rows in a KeyValueStore; the index
  is `bookings_by_room:{room_id} -> [booking_id, ...]`.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, asdict, field
from datetime import date, datetime
from typing import Optional

from common.cache import LRUCache
from common.ids import Snowflake
from common.storage import KeyValueStore


STATUS_ACTIVE = "active"
STATUS_CANCELLED = "cancelled"


# --- exceptions -------------------------------------------------------------


class HotelBookingError(Exception):
    code: str = "internal_error"
    http_status: int = 500

    def __init__(self, message: str = ""):
        super().__init__(message or self.code)
        self.message = message or self.code


class HotelNotFound(HotelBookingError):
    code = "hotel_not_found"
    http_status = 404


class RoomNotFound(HotelBookingError):
    code = "room_not_found"
    http_status = 404


class BookingNotFound(HotelBookingError):
    code = "booking_not_found"
    http_status = 404


class RoomUnavailable(HotelBookingError):
    code = "room_unavailable"
    http_status = 409

    def __init__(self, message: str = "", conflicts: Optional[list[int]] = None):
        super().__init__(message)
        self.conflicts = conflicts or []


class InvalidDateRange(HotelBookingError):
    code = "invalid_date_range"
    http_status = 400


class NotAuthorized(HotelBookingError):
    code = "not_authorized"
    http_status = 403


# --- domain objects ---------------------------------------------------------


@dataclass
class Hotel:
    hotel_id: int
    name: str
    city: str
    created_at: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Room:
    room_id: int
    hotel_id: int
    room_number: str
    capacity: int
    price_cents: int
    created_at: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Booking:
    booking_id: int
    room_id: int
    user_id: int
    check_in: str  # ISO date
    check_out: str  # ISO date (exclusive)
    status: str = STATUS_ACTIVE
    created_at: float = 0.0
    cancelled_at: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


# --- helpers ---------------------------------------------------------------


def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def validate_range(check_in: str, check_out: str) -> tuple[date, date]:
    try:
        ci = parse_date(check_in)
        co = parse_date(check_out)
    except (TypeError, ValueError) as e:
        raise InvalidDateRange(f"could not parse date: {e}")
    if ci >= co:
        raise InvalidDateRange("check_in must be strictly before check_out")
    return ci, co


def overlaps(a_in: date, a_out: date, b_in: date, b_out: date) -> bool:
    """Half-open interval overlap: [a_in, a_out) ∩ [b_in, b_out) ≠ ∅."""
    return a_in < b_out and b_in < a_out


# --- service ---------------------------------------------------------------


class HotelBookingService:
    """Concurrency-safe hotel booking service.

    >>> svc = HotelBookingService()
    >>> h = svc.create_hotel("Inn", "Berkeley")
    >>> r = svc.create_room(h["hotel_id"], "101", 2, 15000)
    >>> b = svc.book(r["room_id"], user_id=1, check_in="2026-10-10", check_out="2026-10-12")
    >>> b["status"]
    'active'
    """

    def __init__(self, use_persistence: bool = False):
        self.snow = Snowflake(machine_id=19)

        persist = None
        self.hotels = KeyValueStore("hb_hotels", persist_path=persist)
        self.rooms = KeyValueStore("hb_rooms", persist_path=persist)
        self.bookings = KeyValueStore("hb_bookings", persist_path=persist)
        # Indexes
        self.room_index = KeyValueStore("hb_room_idx", persist_path=persist)  # room_id -> [booking_id]
        self.hotel_rooms = KeyValueStore("hb_hotel_rooms", persist_path=persist)  # hotel_id -> [room_id]

        # Aggregate
        self._agg_lock = threading.RLock()
        # Per-room lock
        self._room_locks: dict[int, threading.RLock] = {}
        self._room_locks_guard = threading.Lock()

        # LRU for availability results (read-heavy)
        self._avail_cache = LRUCache(max_entries=2_000)

        # Counters
        self.book_attempts = 0
        self.book_wins = 0
        self.book_conflicts = 0
        self.cancellations = 0

    # ---- per-room lock factory ----------------------------------------

    def _lock_for_room(self, room_id: int) -> threading.RLock:
        with self._room_locks_guard:
            lock = self._room_locks.get(room_id)
            if lock is None:
                lock = threading.RLock()
                self._room_locks[room_id] = lock
            return lock

    # ---- key helpers ---------------------------------------------------

    @staticmethod
    def _hotel_key(hotel_id: int) -> str:
        return f"hotel:{hotel_id}"

    @staticmethod
    def _room_key(room_id: int) -> str:
        return f"room:{room_id}"

    @staticmethod
    def _booking_key(booking_id: int) -> str:
        return f"booking:{booking_id}"

    @staticmethod
    def _room_bookings_index_key(room_id: int) -> str:
        return f"room_bookings:{room_id}"

    @staticmethod
    def _hotel_rooms_index_key(hotel_id: int) -> str:
        return f"hotel_rooms:{hotel_id}"

    # ---- hotels --------------------------------------------------------

    def create_hotel(self, name: str, city: str) -> dict:
        if not name or not city:
            raise ValueError("name and city are required")
        with self._agg_lock:
            hid = self.snow.next_id()
            h = Hotel(
                hotel_id=hid,
                name=name,
                city=city,
                created_at=time.time(),
            )
            self.hotels.set(self._hotel_key(hid), asdict(h))
            self.hotel_rooms.set(self._hotel_rooms_index_key(hid), [])
            return asdict(h)

    def list_hotels(self) -> list[dict]:
        out = []
        for _k, v in self.hotels.scan("hotel:"):
            out.append(v)
        out.sort(key=lambda x: x["hotel_id"])
        return out

    def get_hotel(self, hotel_id: int) -> dict:
        h = self.hotels.get(self._hotel_key(hotel_id))
        if not h:
            raise HotelNotFound()
        return h

    # ---- rooms ---------------------------------------------------------

    def create_room(
        self,
        hotel_id: int,
        room_number: str,
        capacity: int = 2,
        price_cents: int = 10_000,
    ) -> dict:
        if capacity <= 0 or price_cents < 0 or not room_number:
            raise ValueError("invalid room params")
        with self._agg_lock:
            if not self.hotels.get(self._hotel_key(hotel_id)):
                raise HotelNotFound()
            rid = self.snow.next_id()
            r = Room(
                room_id=rid,
                hotel_id=hotel_id,
                room_number=room_number,
                capacity=capacity,
                price_cents=price_cents,
                created_at=time.time(),
            )
            self.rooms.set(self._room_key(rid), asdict(r))
            # Append to hotel's room index
            rooms = self.hotel_rooms.get(self._hotel_rooms_index_key(hotel_id)) or []
            rooms.append(rid)
            self.hotel_rooms.set(self._hotel_rooms_index_key(hotel_id), rooms)
            # Init room booking index
            self.room_index.set(self._room_bookings_index_key(rid), [])
            return asdict(r)

    def list_rooms(self, hotel_id: int) -> list[dict]:
        with self._agg_lock:
            if not self.hotels.get(self._hotel_key(hotel_id)):
                raise HotelNotFound()
            rids = self.hotel_rooms.get(self._hotel_rooms_index_key(hotel_id)) or []
        out = []
        for rid in rids:
            rd = self.rooms.get(self._room_key(rid))
            if rd:
                out.append(rd)
        out.sort(key=lambda x: x["room_id"])
        return out

    def get_room(self, room_id: int) -> dict:
        r = self.rooms.get(self._room_key(room_id))
        if not r:
            raise RoomNotFound()
        return r

    # ---- bookings ------------------------------------------------------

    def _active_bookings_for_room(self, room_id: int) -> list[dict]:
        b_ids = self.room_index.get(self._room_bookings_index_key(room_id)) or []
        out = []
        for bid in b_ids:
            b = self.bookings.get(self._booking_key(bid))
            if b and b.get("status") == STATUS_ACTIVE:
                out.append(b)
        out.sort(key=lambda b: b["check_in"])
        return out

    def book(
        self,
        room_id: int,
        user_id: int,
        check_in: str,
        check_out: str,
    ) -> dict:
        self.book_attempts += 1
        ci, co = validate_range(check_in, check_out)
        if not self.rooms.get(self._room_key(room_id)):
            raise RoomNotFound()
        lock = self._lock_for_room(room_id)
        with lock:
            existing = self._active_bookings_for_room(room_id)
            conflicts = []
            for b in existing:
                b_in = parse_date(b["check_in"])
                b_out = parse_date(b["check_out"])
                if overlaps(ci, co, b_in, b_out):
                    conflicts.append(b["booking_id"])
            if conflicts:
                self.book_conflicts += 1
                raise RoomUnavailable(
                    f"room {room_id} is not available for {check_in}..{check_out}",
                    conflicts=conflicts,
                )
            bid = self.snow.next_id()
            booking = Booking(
                booking_id=bid,
                room_id=room_id,
                user_id=user_id,
                check_in=ci.isoformat(),
                check_out=co.isoformat(),
                status=STATUS_ACTIVE,
                created_at=time.time(),
            )
            self.bookings.set(self._booking_key(bid), asdict(booking))
            idx = self.room_index.get(self._room_bookings_index_key(room_id)) or []
            idx.append(bid)
            self.room_index.set(self._room_bookings_index_key(room_id), idx)
            # Bust availability cache for this room
            self._bust_avail_cache(room_id)
            self.book_wins += 1
            return asdict(booking)

    def availability(
        self, room_id: int, date_from: str, date_to: str
    ) -> dict:
        if not self.rooms.get(self._room_key(room_id)):
            raise RoomNotFound()
        ci, co = validate_range(date_from, date_to)
        cache_key = f"avail:{room_id}:{ci.isoformat()}:{co.isoformat()}"
        cached = self._avail_cache.get(cache_key)
        if cached is not None:
            return cached
        lock = self._lock_for_room(room_id)
        with lock:
            existing = self._active_bookings_for_room(room_id)
            conflicts = []
            for b in existing:
                b_in = parse_date(b["check_in"])
                b_out = parse_date(b["check_out"])
                if overlaps(ci, co, b_in, b_out):
                    conflicts.append(b["booking_id"])
            result = {
                "room_id": room_id,
                "from": ci.isoformat(),
                "to": co.isoformat(),
                "available": len(conflicts) == 0,
                "conflicts": conflicts,
                "bookings": [b["booking_id"] for b in existing],
            }
            self._avail_cache.set(cache_key, result)
            return result

    def cancel(self, booking_id: int, user_id: int) -> dict:
        b = self.bookings.get(self._booking_key(booking_id))
        if not b:
            raise BookingNotFound()
        if b.get("user_id") != user_id:
            raise NotAuthorized()
        lock = self._lock_for_room(b["room_id"])
        with lock:
            # Re-read inside the lock to avoid TOCTOU.
            b = self.bookings.get(self._booking_key(booking_id))
            if not b:
                raise BookingNotFound()
            if b.get("user_id") != user_id:
                raise NotAuthorized()
            if b.get("status") == STATUS_CANCELLED:
                return {"booking_id": booking_id, "cancelled": True, "already": True}
            b["status"] = STATUS_CANCELLED
            b["cancelled_at"] = time.time()
            self.bookings.set(self._booking_key(booking_id), b)
            self._bust_avail_cache(b["room_id"])
            self.cancellations += 1
            return {"booking_id": booking_id, "cancelled": True}

    def get_booking(self, booking_id: int) -> dict:
        b = self.bookings.get(self._booking_key(booking_id))
        if not b:
            raise BookingNotFound()
        return b

    def _bust_avail_cache(self, room_id: int) -> None:
        # LRUCache doesn't support prefix-delete; clear it as a small
        # concession. A real cache (Redis) would do SCAN+DEL.
        self._avail_cache.clear()

    # ---- stats ---------------------------------------------------------

    def stats(self) -> dict:
        with self._agg_lock:
            return {
                "hotels": self.hotels.size(),
                "rooms": self.rooms.size(),
                "bookings": self.bookings.size(),
                "active_bookings": sum(
                    1 for _k, v in self.bookings.scan("booking:")
                    if v.get("status") == STATUS_ACTIVE
                ),
                "book_attempts": self.book_attempts,
                "book_wins": self.book_wins,
                "book_conflicts": self.book_conflicts,
                "cancellations": self.cancellations,
                "avail_cache": self._avail_cache.stats(),
            }
