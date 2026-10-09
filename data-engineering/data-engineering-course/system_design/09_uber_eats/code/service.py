"""Uber Eats-style 3-sided marketplace.

A working implementation of the design in ``design/README.md``:

* Restaurants register, hold a menu of priced items.
* Drivers register, have a location and an ``available`` flag.
* Eaters place orders against a restaurant; the service prices the
  order, suggests the nearest available driver, and persists the
  state.
* State machine: ``PLACED → ACCEPTED → PICKED_UP → DELIVERED`` (with
  ``CANCELLED`` as a terminal leak). All other transitions raise
  ``InvalidTransitionError``.

The HTTP layer in ``app.py`` is a thin wrapper.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, asdict, field
from threading import RLock
from typing import Optional

from common.ids import Snowflake
from common.storage import KeyValueStore


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class InvalidTransitionError(ValueError):
    """Raised when a caller tries to make an illegal state move."""


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------


PLACED = "PLACED"
ACCEPTED = "ACCEPTED"
PICKED_UP = "PICKED_UP"
DELIVERED = "DELIVERED"
CANCELLED = "CANCELLED"

ALL_STATES = (PLACED, ACCEPTED, PICKED_UP, DELIVERED, CANCELLED)
TERMINAL_STATES = (DELIVERED, CANCELLED)

# from -> set of allowed to-states.
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    PLACED: frozenset({ACCEPTED, CANCELLED}),
    ACCEPTED: frozenset({PICKED_UP, CANCELLED}),
    PICKED_UP: frozenset({DELIVERED}),
    DELIVERED: frozenset(),
    CANCELLED: frozenset(),
}


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass
class Restaurant:
    restaurant_id: int
    name: str
    address: str
    lat: float
    lng: float
    created_at: float
    # menu is a dict so JSON-friendly; item_id -> {name, price_cents}.
    menu: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MenuItem:
    item_id: int
    name: str
    price_cents: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Driver:
    driver_id: int
    name: str
    lat: float
    lng: float
    available: bool = True
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Order:
    order_id: int
    eater_id: int
    restaurant_id: int
    items: list
    subtotal_cents: int
    address: str
    lat: float
    lng: float
    status: str
    suggested_driver_id: Optional[int]
    driver_id: Optional[int]
    history: list
    created_at: float
    updated_at: float

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class UberEatsService:
    """A working 3-sided marketplace.

    >>> svc = UberEatsService()
    >>> r = svc.create_restaurant("R1", "addr", 37.0, -122.0)
    >>> item = svc.add_menu_item(r.restaurant_id, "Pizza", 1200)
    >>> d = svc.create_driver("D1", 37.001, -122.001)
    >>> o = svc.place_order(
    ...     eater_id=1,
    ...     restaurant_id=r.restaurant_id,
    ...     items=[{"menu_item_id": item.item_id, "qty": 2}],
    ...     address="home",
    ...     lat=37.0, lng=-122.0,
    ... )
    >>> o.status
    'PLACED'
    >>> o = svc.accept_order(o.order_id, d.driver_id)
    >>> o.status
    'ACCEPTED'
    >>> o = svc.transition(o.order_id, PICKED_UP, by=str(d.driver_id))
    >>> o.status
    'PICKED_UP'
    >>> o = svc.transition(o.order_id, DELIVERED, by=str(d.driver_id))
    >>> o.status
    'DELIVERED'
    """

    def __init__(
        self,
        store: Optional[KeyValueStore] = None,
        id_gen: Optional[Snowflake] = None,
    ):
        self.store = store or KeyValueStore("uber_eats")
        self.id_gen = id_gen or Snowflake(machine_id=9)
        self._lock = RLock()

    # ------------------------------------------------------------------
    # restaurants — design §4
    # ------------------------------------------------------------------

    def create_restaurant(
        self, name: str, address: str, lat: float, lng: float
    ) -> Restaurant:
        self._validate_str("name", name)
        self._validate_str("address", address)
        self._validate_latlng(lat, lng)
        r = Restaurant(
            restaurant_id=self.id_gen.next_id(),
            name=name.strip(),
            address=address.strip(),
            lat=float(lat),
            lng=float(lng),
            created_at=time.time(),
        )
        self.store.set(self._k_rest(r.restaurant_id), r.to_dict())
        return r

    def get_restaurant(self, rid: int) -> Optional[Restaurant]:
        d = self.store.get(self._k_rest(rid))
        return Restaurant(**d) if d else None

    def list_restaurants(self) -> list[Restaurant]:
        out: list[Restaurant] = []
        for k, v in self.store.scan("restaurant:"):
            if isinstance(v, dict):
                out.append(Restaurant(**v))
        out.sort(key=lambda r: r.created_at)
        return out

    def add_menu_item(
        self, restaurant_id: int, name: str, price_cents: int
    ) -> MenuItem:
        r = self.get_restaurant(restaurant_id)
        if r is None:
            raise ValueError(f"unknown restaurant {restaurant_id!r}")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if not isinstance(price_cents, int) or price_cents <= 0:
            raise ValueError("price_cents must be a positive int")
        item = MenuItem(
            item_id=self.id_gen.next_id(),
            name=name.strip(),
            price_cents=int(price_cents),
        )
        r.menu[str(item.item_id)] = item.to_dict()
        self.store.set(self._k_rest(restaurant_id), r.to_dict())
        return item

    def get_menu_item(self, restaurant_id: int, item_id: int) -> Optional[dict]:
        r = self.get_restaurant(restaurant_id)
        if r is None:
            return None
        return r.menu.get(str(item_id))

    # ------------------------------------------------------------------
    # drivers — design §4
    # ------------------------------------------------------------------

    def create_driver(
        self, name: str, lat: float, lng: float, available: bool = True
    ) -> Driver:
        self._validate_str("name", name)
        self._validate_latlng(lat, lng)
        d = Driver(
            driver_id=self.id_gen.next_id(),
            name=name.strip(),
            lat=float(lat),
            lng=float(lng),
            available=bool(available),
            created_at=time.time(),
        )
        self.store.set(self._k_drv(d.driver_id), d.to_dict())
        return d

    def get_driver(self, did: int) -> Optional[Driver]:
        d = self.store.get(self._k_drv(did))
        return Driver(**d) if d else None

    def list_drivers(self) -> list[Driver]:
        out: list[Driver] = []
        for k, v in self.store.scan("driver:"):
            if isinstance(v, dict):
                out.append(Driver(**v))
        out.sort(key=lambda d: d.created_at)
        return out

    def set_driver_available(self, did: int, available: bool) -> Driver:
        d = self.get_driver(did)
        if d is None:
            raise ValueError(f"unknown driver {did!r}")
        d.available = bool(available)
        self.store.set(self._k_drv(did), d.to_dict())
        return d

    # ------------------------------------------------------------------
    # orders — design §5/§6/§8
    # ------------------------------------------------------------------

    def place_order(
        self,
        eater_id: int,
        restaurant_id: int,
        items: list,
        address: str,
        lat: float,
        lng: float,
    ) -> Order:
        """Place an order. Prices the items, picks the nearest
        available driver, and persists the order with status=PLACED.
        """
        self._validate_str("address", address)
        self._validate_latlng(lat, lng)
        r = self.get_restaurant(restaurant_id)
        if r is None:
            raise ValueError(f"unknown restaurant {restaurant_id!r}")
        if not items or not isinstance(items, list):
            raise ValueError("items must be a non-empty list")

        priced_items: list[dict] = []
        subtotal = 0
        for entry in items:
            if not isinstance(entry, dict):
                raise ValueError("each item must be a dict")
            mid = int(entry["menu_item_id"])
            qty = int(entry.get("qty", 1))
            if qty <= 0:
                raise ValueError("qty must be a positive int")
            mi = r.menu.get(str(mid))
            if mi is None:
                raise ValueError(
                    f"menu item {mid} not in restaurant {restaurant_id}"
                )
            line_total = int(mi["price_cents"]) * qty
            subtotal += line_total
            priced_items.append(
                {
                    "menu_item_id": mid,
                    "name": mi["name"],
                    "price_cents": int(mi["price_cents"]),
                    "qty": qty,
                    "line_total_cents": line_total,
                }
            )

        # Dispatch — design §7.
        suggested = self.nearest_driver((r.lat, r.lng))

        now = time.time()
        order = Order(
            order_id=self.id_gen.next_id(),
            eater_id=int(eater_id),
            restaurant_id=int(restaurant_id),
            items=priced_items,
            subtotal_cents=subtotal,
            address=address.strip(),
            lat=float(lat),
            lng=float(lng),
            status=PLACED,
            suggested_driver_id=suggested.driver_id if suggested else None,
            driver_id=None,
            history=[{"status": PLACED, "ts": now, "by": str(eater_id), "note": ""}],
            created_at=now,
            updated_at=now,
        )
        self.store.set(self._k_ord(order.order_id), order.to_dict())
        return order

    def get_order(self, oid: int) -> Optional[Order]:
        d = self.store.get(self._k_ord(oid))
        return Order(**d) if d else None

    def list_orders(self, status: Optional[str] = None) -> list[Order]:
        out: list[Order] = []
        for k, v in self.store.scan("order:"):
            if not isinstance(v, dict):
                continue
            if status is not None and v.get("status") != status:
                continue
            out.append(Order(**v))
        out.sort(key=lambda o: o.created_at, reverse=True)
        return out

    # ---- state transitions --------------------------------------------

    def accept_order(self, order_id: int, driver_id: int) -> Order:
        """Driver accepts a PLACED order. The driver must be the
        suggested one (relax this in production) and must be
        available.
        """
        order = self.get_order(order_id)
        if order is None:
            raise ValueError(f"unknown order {order_id!r}")
        if order.status != PLACED:
            raise InvalidTransitionError(
                f"order is in {order.status!r}, cannot accept"
            )
        driver = self.get_driver(driver_id)
        if driver is None:
            raise ValueError(f"unknown driver {driver_id!r}")
        if not driver.available:
            raise ValueError("driver is not available")
        if (
            order.suggested_driver_id is not None
            and order.suggested_driver_id != driver_id
        ):
            # Soft check — in production any available driver can grab.
            # Here we enforce the suggestion so tests can rely on it.
            raise ValueError(
                "driver is not the suggested driver for this order"
            )
        return self._transition_internal(
            order, ACCEPTED, by=str(driver_id), note=""
        )

    def transition(
        self, order_id: int, new_status: str, by: str = "", note: str = ""
    ) -> Order:
        """Generic state transition. Used for PICKED_UP, DELIVERED,
        CANCELLED. ``accept_order`` has its own method.
        """
        if new_status == ACCEPTED:
            # Force callers to use accept_order so the driver is bound.
            raise InvalidTransitionError(
                "use accept_order() to move to ACCEPTED"
            )
        order = self.get_order(order_id)
        if order is None:
            raise ValueError(f"unknown order {order_id!r}")
        return self._transition_internal(order, new_status, by=by, note=note)

    def _transition_internal(
        self, order: Order, new_status: str, by: str, note: str
    ) -> Order:
        allowed = ALLOWED_TRANSITIONS.get(order.status, frozenset())
        if new_status not in allowed:
            raise InvalidTransitionError(
                f"cannot transition from {order.status!r} to {new_status!r}"
            )
        now = time.time()
        order.status = new_status
        order.updated_at = now
        order.history.append(
            {"status": new_status, "ts": now, "by": by, "note": note}
        )
        if new_status == ACCEPTED and order.driver_id is None:
            # Defensive — accept_order should already have set it.
            order.driver_id = int(by) if str(by).isdigit() else None
        self.store.set(self._k_ord(order.order_id), order.to_dict())
        return order

    # ---- dispatch — design §7 -----------------------------------------

    def nearest_driver(
        self, restaurant_loc: tuple[float, float]
    ) -> Optional[Driver]:
        """Return the closest available driver to ``restaurant_loc``.

        Uses Euclidean distance on ``(lat, lng)`` — fine for the
        lesson, replace with Haversine + a routing ETA in
        production.
        """
        best: Optional[Driver] = None
        best_d = math.inf
        for d in self.list_drivers():
            if not d.available:
                continue
            dist = self._euclidean(restaurant_loc, (d.lat, d.lng))
            if dist < best_d:
                best = d
                best_d = dist
        return best

    @staticmethod
    def _euclidean(
        a: tuple[float, float], b: tuple[float, float]
    ) -> float:
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    # ------------------------------------------------------------------
    # stats
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        restaurants = self.list_restaurants()
        drivers = self.list_drivers()
        orders = self.list_orders()
        by_state: dict[str, int] = {s: 0 for s in ALL_STATES}
        for o in orders:
            by_state[o.status] = by_state.get(o.status, 0) + 1
        return {
            "restaurants": len(restaurants),
            "drivers": len(drivers),
            "orders": len(orders),
            "orders_by_state": by_state,
        }

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_str(field: str, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-empty string")

    @staticmethod
    def _validate_latlng(lat: float, lng: float) -> None:
        try:
            lat_f, lng_f = float(lat), float(lng)
        except (TypeError, ValueError):
            raise ValueError("lat/lng must be numeric")
        if not -90 <= lat_f <= 90:
            raise ValueError("lat must be in [-90, 90]")
        if not -180 <= lng_f <= 180:
            raise ValueError("lng must be in [-180, 180]")

    @staticmethod
    def _k_rest(rid: int) -> str:
        return f"restaurant:{rid}"

    @staticmethod
    def _k_drv(did: int) -> str:
        return f"driver:{did}"

    @staticmethod
    def _k_ord(oid: int) -> str:
        return f"order:{oid}"
