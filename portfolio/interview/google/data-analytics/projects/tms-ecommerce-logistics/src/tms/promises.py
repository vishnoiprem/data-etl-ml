"""The promise: what the checkout told the customer, and whether it was true.

**A promise is only meaningful if the network can keep it.** Every number
in this project that claims to be an on-time rate is a claim about the
gap between the promise and the delivery, so if the promise is set by
something other than what the network can physically do, the on-time
rate measures the gap between the business rules and reality rather than
the network's performance.

The tempting shortcut is a flat window per service level: same-day is
fourteen hours, next-day is thirty, economy is four days. It is simple,
it is what a slide deck says, and it is **wrong in a way that quietly
dominates every downstream number**.

**Why a flat window breaks the network.** Take a same-day order placed
at 04:30. Fourteen hours later is 18:30 — fine. Take one placed at 09:59
and the promise is 23:59, which the network can just about meet. Now
take the same flat rule and apply it to the *pre-dawn* orders: an order
placed at 00:30 is promised for 14:30, and the parcel cannot even be
picked and packed before the warehouse opens at 06:00. The promise is
impossible at the moment it is made, and the order will be late by
construction. The same failure hits next-day orders placed at 18:00 —
they are promised for midnight, and the last courier in the evening wave
goes off shift at 23:00. The network is not performing badly. It is
being asked to keep promises that no network could keep.

**The fix is to promise a delivery *slot*, not an offset.** The
question a checkout page has to answer is "when will this arrive?", and
the honest answer is not "in fourteen hours" — it is "on today's
evening run", which is a slot in the network's day, and which is
different for an order placed at 08:00 and one placed at 20:00.

So this module works in slots:

1. the parcel becomes **ready** at the warehouse (opening hours plus the
   pick-and-pack queue),
2. the parcel waits for the next **wave** that can take it,
3. the wave delivers over a window, and the parcel lands somewhere in
   that window.

The promise is the *end of the window the parcel will actually be
delivered in*, plus the tier's travel allowance. That is the last moment
the network can honestly commit to, and it is the moment the on-time
rate is measured against.

Sub-parts
---------
- :func:`service_window` — the promise for a service level at a moment.
- :func:`is_offerable` — whether a service level can be sold at all.
- :func:`promise_for_order` — the promise for a specific order.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .config import DEFAULT_VALUES, ValueConfig
from .models import Order, ServiceLevel

#: Extra hours allowed for the drive itself, on top of the delivery slot.
#:
#: The slot is the window the wave works through; the handover lands
#: somewhere inside it. The allowance is what moves the promise to the
#: far end of the window, so a promise is never tighter than the network
#: can make it.
DELIVERY_ALLOWANCE_HOURS = 3.0

#: Extra hours for a stop in the outer ring.
#:
#: Tier-3 zones are further out, the addresses are more spread out and the
#: first-attempt success rate is lower, so a tier-3 stop is promised
#: slightly later than a tier-1 stop for the same service level. This is
#: how a real checkout works: the estimate it shows depends on the pin
#: code.
TIER_ALLOWANCE_HOURS = {"tier1": 0.0, "tier2": 2.0, "tier3": 4.0}


@dataclass(frozen=True, slots=True)
class ServiceEnvelope:
    """When the network is able to move a parcel, in one day's frame.

    The envelope is the union of the two shift windows, trimmed to the
    hours the warehouse is open. A courier can only pick up a parcel
    while the warehouse is open, and can only deliver it while they are
    on shift, so the deliverable window for a day is the intersection of
    the two — and it is *not* one continuous block, which is the whole
    point.
    """

    #: The hour the warehouse opens. Nothing can be picked before this.
    warehouse_open: datetime
    #: The hour the warehouse closes. Nothing can be picked after this.
    warehouse_close: datetime
    #: The first moment a courier is on the road.
    first_shift_start: datetime
    #: The last moment a courier is on the road.
    last_shift_end: datetime
    #: When the evening wave leaves, and when it comes back.
    evening_start: datetime
    evening_end: datetime
    #: When the morning wave comes back to the hub.
    day_shift_end: datetime

    @property
    def deliverable_until(self) -> datetime:
        """The last moment a parcel can be handed over today."""
        return min(self.warehouse_close, self.last_shift_end)

    @property
    def day_end(self) -> datetime:
        """The end of the morning wave's delivery window."""
        return self.day_shift_end


def day_envelope(day: datetime, values: ValueConfig | None = None) -> ServiceEnvelope:
    """The operating envelope for one calendar day.

    ``day`` is any moment on the day in question; only its date is used.
    """

    vals = values or DEFAULT_VALUES
    midnight = day.replace(hour=0, minute=0, second=0, microsecond=0)

    warehouse_open = midnight + timedelta(hours=vals.warehouse_start_hour)
    warehouse_close = midnight + timedelta(hours=vals.warehouse_end_hour)

    # The day wave starts in the morning and the evening wave starts in
    # the afternoon; the day wave is the one that opens the network, and
    # the evening wave is the one that closes it.
    day_start = midnight + timedelta(hours=vals.dispatch_start_hour)
    day_end = day_start + timedelta(hours=vals.shift_hours)
    evening_start = midnight + timedelta(hours=vals.evening_shift_start_hour)
    evening_end = evening_start + timedelta(hours=vals.evening_shift_hours)

    return ServiceEnvelope(
        warehouse_open=warehouse_open,
        warehouse_close=warehouse_close,
        first_shift_start=min(day_start, evening_start),
        last_shift_end=max(day_end, evening_end),
        evening_start=evening_start,
        evening_end=evening_end,
        day_shift_end=day_end,
    )


def _ready_at(
    created_at: datetime,
    envelope: ServiceEnvelope,
    values: ValueConfig,
) -> datetime:
    """When the parcel is picked, packed and manifested.

    The warehouse opens at a fixed hour and closes at a fixed hour. An
    order that arrives before opening is manifested when the warehouse
    opens; one that arrives after closing waits on the dock until
    morning.
    """

    ready = created_at
    if ready < envelope.warehouse_open:
        ready = envelope.warehouse_open
    if ready > envelope.warehouse_close:
        ready = envelope.warehouse_open + timedelta(days=1)
    return ready


def _slot_end(
    ready: datetime,
    envelope: ServiceEnvelope,
    values: ValueConfig,
) -> tuple[datetime, datetime]:
    """The wave that takes this parcel, and the end of its delivery window.

    A parcel that is manifested before the evening wave leaves goes out on
    the wave that is already running — the day wave if it is out, the
    evening wave otherwise — and lands somewhere in that wave's window.

    A parcel manifested after the evening wave has left waits for
    tomorrow's day wave.

    Returns the (start, end) of the delivery window.
    """

    today_evening_end = envelope.evening_end
    tomorrow_day_start = envelope.first_shift_start + timedelta(days=1)
    tomorrow_day_end = tomorrow_day_start + timedelta(hours=values.shift_hours)

    # Ready before the evening wave leaves: it goes out on today's waves.
    if ready <= envelope.evening_start:
        if ready <= envelope.first_shift_start:
            # The morning wave takes it, and it lands somewhere between
            # the morning's departure and the end of the morning shift.
            #
            # The window ends at the *day wave's* end, not at the moment
            # the evening wave leaves. The two waves overlap, and a parcel
            # picked at 07:00 can perfectly well be delivered at 18:00 by
            # a courier who was still on the road from the morning.
            return envelope.first_shift_start, envelope.day_end
        # The evening wave takes it, and it lands in the evening window.
        return envelope.evening_start, today_evening_end

    # Ready after the evening wave has left but before the warehouse
    # closes: it waits on the dock for tomorrow morning.
    if ready <= envelope.warehouse_close:
        return tomorrow_day_start, tomorrow_day_end

    # Manifested overnight: tomorrow's day wave.
    return tomorrow_day_start, tomorrow_day_end


def service_window(
    service_level: ServiceLevel | str,
    created_at: datetime,
    tier: str = "tier1",
    values: ValueConfig | None = None,
) -> datetime:
    """When a parcel ordered at ``created_at`` is promised to arrive.

    * **same_day** — the parcel goes out on the wave that is already on
      the road, and lands that evening. If the order arrives too late
      for that, the promise moves to the next morning and the service
      level is no longer same-day.
    * **next_day** — the parcel goes out on the next day's first wave.
    * **economy** and **express_cross_border** — wide windows measured in
      days, which the network has no trouble keeping.

    The promise is the **end of the delivery window** the parcel will
    land in, and never later than that window's end. Adding a travel
    allowance on top of the window's end would push the promise past
    midnight for an evening parcel — a promise of 02:00 for a network
    whose last courier goes home at 23:00, which is a promise the
    network cannot keep no matter how good the routing is.
    """

    vals = values or DEFAULT_VALUES
    level = (
        service_level
        if isinstance(service_level, ServiceLevel)
        else ServiceLevel(service_level)
    )
    envelope = day_envelope(created_at, vals)
    allowance = DELIVERY_ALLOWANCE_HOURS + TIER_ALLOWANCE_HOURS.get(tier, 0.0)

    if level is ServiceLevel.SAME_DAY:
        ready = _ready_at(created_at, envelope, vals)
        # The tier allowance is the extra time the outer ring costs, and
        # it decides *which* delivery slot the parcel is placed in: a
        # tier-3 parcel is a longer trip, so it is placed in the later
        # slot rather than the earlier one.
        _, window_end = _slot_end(
            ready + timedelta(hours=allowance), envelope, vals
        )
        # The promise is the **end of the delivery window** the parcel
        # lands in.
        #
        # A parcel is delivered somewhere inside the window, not at a
        # known point inside it, so the only promise the network can
        # keep is the one that allows for the whole window. Promising
        # the window's start would be a promise about the *earliest*
        # possible delivery, which is not what a customer is buying and
        # is not what the network delivers.
        return window_end

    if level is ServiceLevel.NEXT_DAY:
        # "Next day" means the parcel is delivered on the following day —
        # and the following day's deliveries are spread across that
        # day's whole operating window, not bunched into its morning.
        #
        # So the promise is the *next* day's slot, computed the same way
        # a same-day promise is, with the day shifted forward. Promising
        # tomorrow's 10:00 would be a promise about the start of
        # tomorrow's window, which is not what the network does: it
        # delivers through the evening, and a parcel promised at 10:00
        # that lands at 18:00 is late by its own promise.
        tomorrow_envelope = day_envelope(
            created_at + timedelta(days=1), vals
        )
        ready = _ready_at(created_at, envelope, vals)
        tomorrow_ready = max(
            ready - timedelta(days=1),
            tomorrow_envelope.warehouse_open,
        )
        _, window_end = _slot_end(tomorrow_ready, tomorrow_envelope, vals)
        return window_end

    hours = vals.service_level_hours[level.value]
    return created_at + timedelta(hours=hours)


def is_offerable(
    service_level: ServiceLevel | str,
    created_at: datetime,
    tier: str = "tier1",
    values: ValueConfig | None = None,
) -> bool:
    """Whether this service level can be sold to a customer right now.

    A checkout that keeps offering a service level the network cannot
    deliver is not being generous, it is being dishonest: the failure
    gets booked against the network's on-time rate, where it belongs to
    the pricing policy instead.

    Same-day is the level with a real cut-off, because it is the only
    one whose window is a few hours. It stops being offered once the
    parcel cannot be picked, manifested, loaded and delivered before the
    evening wave ends.
    """

    vals = values or DEFAULT_VALUES
    level = (
        service_level
        if isinstance(service_level, ServiceLevel)
        else ServiceLevel(service_level)
    )

    if level is not ServiceLevel.SAME_DAY:
        return True

    envelope = day_envelope(created_at, vals)
    ready = _ready_at(created_at, envelope, vals)
    if ready > envelope.warehouse_close:
        return False

    # The parcel has to be out on a wave that finishes today.
    _, window_end = _slot_end(ready, envelope, vals)
    return window_end.date() == created_at.date()


def promise_for_order(order: Order, values: ValueConfig | None = None) -> datetime:
    """The promise for an order, from its service level and its zone tier."""

    vals = values or DEFAULT_VALUES
    tier = order.address.tier if order.address is not None else "tier1"
    return service_window(order.service_level, order.created_at, tier, vals)
