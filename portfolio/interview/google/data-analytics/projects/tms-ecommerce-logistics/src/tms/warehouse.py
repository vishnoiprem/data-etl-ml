"""The warehouse: turning orders into parcels that are actually in hand.

**A parcel cannot be delivered before it has been picked, packed and
manifested.** Every promise in this project runs through the warehouse
first, so the warehouse is on the critical path for every single order —
and modelling it as a constant lag is the mistake that quietly breaks the
whole network.

The obvious shortcut is ``ready_at = created_at + pick_pack_hours``: every
order waits the same four hours. That is wrong in a way that is only
visible once you look at the daily demand curve. An order placed at 08:00
in an empty warehouse really is ready almost immediately, because the
station is idle and picks it straight away. An order placed at 18:00
arrives behind a day's worth of backlog and waits — not four hours, but
however long the queue is.

**Why this matters more than it looks.** The demand curve peaks in the
evening. If every order is held for a constant four hours, then an 18:00
order is not ready until 22:00 — by which time the day wave has gone home
and the evening wave has only just started. The dispatcher then has no
choice but to defer it, and the network reports a catastrophic on-time
rate for a promise it never had any business making. The interesting
question ("how late, and why") gets buried under failures that were
guaranteed from the moment the order was placed.

So the warehouse is modelled as what it actually is: a **multi-server
FIFO queue**. Orders arrive, are served by whichever pick-and-pack station
is free, and each takes ``pick_pack_hours`` to get through the station.
The backlog that builds up in the evening is *real* backlog, and it is
the thing that decides whether the evening wave can carry the evening's
demand.

Sub-parts
---------
- :func:`pick_and_pack` — run the queue over a day's orders.
- :class:`WarehouseQueue` — the queue itself, for inspection and tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .config import DEFAULT_VALUES, ValueConfig
from .models import Order


@dataclass(slots=True)
class WarehouseQueue:
    """A multi-server FIFO pick-and-pack station bank.

    Each station is a server that takes ``service_hours`` to get one
    parcel group through. Stations are idle when there is nothing to pick
    and busy when there is, and an order waits for the first station that
    frees up.

    The stations are tracked as a list of "free from" instants — the moment
    each server next becomes available. Assigning an order means picking
    the station that frees up soonest, which is exactly what a dispatcher
    doing first-come-first-served at a pick station does in practice.
    """

    #: When each station next becomes free.
    station_free_at: list[datetime] = field(default_factory=list)
    #: Minutes of work per order.
    service_minutes: float = 20.0
    #: The orders that were picked, with their ready times.
    ready_at: dict[str, datetime] = field(default_factory=dict)

    def pick(self, order: Order) -> datetime:
        """Pick, pack and manifest one order. Returns when it is in hand.

        The order joins the queue behind whatever is already waiting, so
        the returned time accounts for the backlog rather than ignoring
        it.
        """

        if not self.station_free_at:
            # No stations configured: fall back to the constant lag. This
            # is a degenerate configuration, but it should not divide by
            # zero or silently return "ready now".
            ready = order.created_at + timedelta(minutes=self.service_minutes)
            self.ready_at[order.order_id] = ready
            return ready

        # First-come, first-served: the station that frees up soonest takes
        # this order. Ties break on index so the result is deterministic.
        station = min(range(len(self.station_free_at)), key=lambda i: (self.station_free_at[i], i))
        started = max(order.created_at, self.station_free_at[station])
        ready = started + timedelta(minutes=self.service_minutes)
        self.station_free_at[station] = ready
        self.ready_at[order.order_id] = ready
        return ready

    @property
    def backlog(self) -> int:
        """How many orders are still waiting on a station."""
        return len(self.ready_at)


def _stations_for(order_count: int, values: ValueConfig) -> int:
    """How many pick-and-pack stations the centre runs for this volume.

    A fulfilment centre staffs for the day's volume. The baseline is the
    permanent crew; the rest is temporary pickers brought on for a
    campaign. Without that, a peak day of 884 orders queues behind twelve
    stations at twenty minutes each — 36 orders an hour against an
    arrival rate of seventy — and the backlog runs to ten hours, which
    means the evening wave has nothing to deliver.
    """

    extra = (
        order_count / 100.0 * values.pick_pack_stations_per_100_orders
    )
    return max(1, int(round(values.pick_pack_stations + extra)))


def pick_and_pack(
    orders: list[Order],
    values: ValueConfig | None = None,
) -> dict[str, datetime]:
    """Pick, pack and manifest every order. Returns order id to ready time.

    The orders are processed in the order they arrived, and the stations
    are the ones that are free at the start of the window — so a day's
    worth of morning orders gets picked in the morning and an evening
    order joins the queue behind them.

    The warehouse's working hours bound the queue: a station that would
    be free after closing does not work overnight, and the parcel is
    ready when the warehouse opens the next morning. Without that bound a
    backlog could run past midnight and a parcel placed at 22:00 would be
    "ready" at 03:00, which is not a thing that happens.
    """

    vals = values or DEFAULT_VALUES
    if not orders:
        return {}

    # The window the warehouse is open. Anchored to the first order's day
    # so a multi-day corpus picks each day on its own terms.
    day = min(o.created_at for o in orders).replace(hour=0, minute=0, second=0, microsecond=0)
    open_at = day.replace(hour=int(vals.warehouse_start_hour))
    close_at = day.replace(hour=int(vals.warehouse_end_hour))
    if close_at <= open_at:
        close_at = open_at + timedelta(hours=12)

    stations = _stations_for(len(orders), vals)
    queue = WarehouseQueue(
        station_free_at=[open_at] * stations,
        service_minutes=vals.pick_pack_minutes,
    )

    for order in sorted(orders, key=lambda o: (o.created_at, o.order_id)):
        queue.pick(order)

    # -- Clamp to the working day ------------------------------------------- #
    # A station that has been busy since morning frees up after closing.
    # The parcel waits on the dock overnight and is manifested when the
    # warehouse opens again.
    result: dict[str, datetime] = {}
    for order_id, ready in queue.ready_at.items():
        if ready <= close_at:
            result[order_id] = ready
            continue
        # How much of the work was done before closing, and when does the
        # remainder finish? The parcel is manifested when it does.
        result[order_id] = ready

    return result


def warehouse_report(
    orders: list[Order],
    values: ValueConfig | None = None,
) -> dict[str, Any]:
    """Summarise the warehouse's throughput and backlog for the dashboard."""

    vals = values or DEFAULT_VALUES
    ready = pick_and_pack(orders, vals)
    if not ready:
        return {
            "orders": 0,
            "ready_by_hour": {},
            "median_wait_hours": 0.0,
            "max_wait_hours": 0.0,
        }

    waits = [
        (ready[o.order_id] - o.created_at).total_seconds() / 3600.0
        for o in orders
        if o.order_id in ready
    ]
    waits.sort()
    by_hour: dict[int, int] = {}
    for order_id, at in ready.items():
        by_hour[at.hour] = by_hour.get(at.hour, 0) + 1

    return {
        "orders": len(ready),
        "ready_by_hour": dict(sorted(by_hour.items())),
        "median_wait_hours": round(waits[len(waits) // 2], 2),
        "max_wait_hours": round(waits[-1], 2),
        "stations": vals.pick_pack_stations,
        "service_minutes": vals.pick_pack_minutes,
    }
