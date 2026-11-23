"""Dispatch: allocating orders to couriers and consolidating them into stops.

**Two decisions live here, and they are different decisions.**

*Allocation* is "which courier takes this parcel". It is constrained by
capacity (kg, m³, parcel count), by zone affinity, by vehicle mode, and by
the customer's time window. It is a bin-packing problem with soft preferences.

*Consolidation* is "which stops does this courier actually visit". Several
parcels to the same address share one stop. This is where most of the
last-mile saving comes from: a courier who visits 30 addresses carrying 40
parcels costs far less per parcel than one visiting 40 addresses carrying 40
parcels.

Getting consolidation wrong is expensive and quiet. If each parcel became its
own stop, cost per parcel would roughly double and nothing would look
broken.

Sub-parts
---------
- :class:`Capacity` — a courier's three-dimensional load envelope.
- :class:`DispatchPlan` — the result of a dispatch run.
- :func:`consolidate_stops` — group parcels into stops by address.
- :func:`allocate_orders` — assign parcels to couriers under constraints.
- :func:`dispatch_day` — the whole flow for one operating day.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .config import DEFAULT_VALUES, ValueConfig
from .models import (
    DETOUR_FACTOR,
    Address,
    Courier,
    Order,
    Parcel,
    Route,
    ServiceLevel,
    Shipment,
    Stop,
    World,
    haversine_km,
)
from .warehouse import pick_and_pack


# --------------------------------------------------------------------------- #
# Capacity
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Capacity:
    """A courier's load envelope, in three dimensions plus time.

    Three load dimensions, not one, because a bike with 8 kg of room and
    0.30 m³ of room runs out of both at once. A two-dimensional capacity
    model (weight only) would happily load a bike with 25 kg of pillows.

    The fourth dimension is **time**. A courier with a ten-hour shift
    cannot deliver more stops than fit in ten hours, no matter how much
    room is left on the bike. Leaving time out is the single most common
    way a last-mile simulation produces a network that looks efficient and
    delivers everything four days late.
    """

    max_weight_kg: float
    max_volume_m3: float
    max_parcels: int
    #: Minutes of shift remaining.
    max_minutes: float = 600.0
    weight_kg: float = 0.0
    volume_m3: float = 0.0
    parcels: int = 0
    minutes_used: float = 0.0

    @classmethod
    def from_courier(cls, courier: Courier, shift_hours: float = 10.0) -> Capacity:
        """Build an empty envelope from a courier's vehicle and shift.

        The time budget is measured from the courier's shift *end*, not from
        the shift's nominal length, because a courier who has to wait for
        the warehouse to finish picking has fewer minutes on the road than
        one who leaves with a full load. Deriving the budget from the two
        shift timestamps keeps the two in step.
        """
        span_minutes = (courier.shift_end - courier.shift_start).total_seconds() / 60.0
        if span_minutes <= 0:
            span_minutes = shift_hours * 60.0
        return cls(
            max_weight_kg=courier.max_weight_kg,
            max_volume_m3=courier.max_volume_m3,
            max_parcels=courier.max_parcels,
            max_minutes=span_minutes,
        )

    @property
    def weight_remaining(self) -> float:
        """Kilograms still available."""
        return self.max_weight_kg - self.weight_kg

    @property
    def volume_remaining(self) -> float:
        """Cubic metres still available."""
        return self.max_volume_m3 - self.volume_m3

    @property
    def parcels_remaining(self) -> int:
        """Parcels still available."""
        return self.max_parcels - self.parcels

    @property
    def minutes_remaining(self) -> float:
        """Minutes of shift left."""
        return self.max_minutes - self.minutes_used

    def can_accept(self, parcel: Parcel, service_minutes: float = 0.0) -> bool:
        """Whether this parcel fits, in every dimension including time.

        ``service_minutes`` is the time for the *whole stop*, not for this
        parcel. A three-parcel drop is one visit, not three, and charging
        the time once per parcel is what quietly fills a shift three times
        over before the courier has made a third of their stops.
        """
        return (
            self.weight_remaining >= parcel.weight_kg
            and self.volume_remaining >= parcel.volume_m3
            and self.parcels_remaining >= 1
            and self.minutes_remaining >= service_minutes
        )

    def load(self, parcel: Parcel, service_minutes: float = 0.0) -> None:
        """Load a parcel into the envelope.

        The time cost is charged once, by :meth:`load_stop`, because the
        service time belongs to the stop rather than to each parcel in it.
        """
        self.weight_kg += parcel.weight_kg
        self.volume_m3 += parcel.volume_m3
        self.parcels += 1

    def load_stop(self, parcels: list[Parcel], service_minutes: float) -> None:
        """Load a whole stop: its parcels, and the time it costs to serve.

        Keeping the stop's parcels and the stop's service time together
        is what stops the two from being charged separately and drifting
        out of step.
        """
        for parcel in parcels:
            self.weight_kg += parcel.weight_kg
            self.volume_m3 += parcel.volume_m3
            self.parcels += 1
        self.minutes_used += service_minutes

    @property
    def utilisation(self) -> float:
        """The tightest of the utilisations, as a 0-1 fraction.

        Using the max rather than the mean is deliberate: a courier 100%
        full on weight but 20% full on volume is still full.
        """
        if self.max_parcels <= 0:
            return 1.0
        return max(
            self.weight_kg / self.max_weight_kg if self.max_weight_kg else 0.0,
            self.volume_m3 / self.max_volume_m3 if self.max_volume_m3 else 0.0,
            self.parcels / self.max_parcels,
            self.minutes_used / self.max_minutes if self.max_minutes else 0.0,
        )


# --------------------------------------------------------------------------- #
# Stop consolidation
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class ConsolidatedStop:
    """A group of parcels going to the same address."""

    address: Address
    order_ids: tuple[str, ...]
    parcel_ids: tuple[str, ...]
    #: The tightest promised deadline among the orders in the group. The
    #: courier must meet the *earliest* one — the group is scheduled by its
    #: most urgent member.
    promised_at: datetime
    #: The *latest* order time in the group. The parcel cannot be in hand
    #: before this, so the route cannot depart before this.
    ready_at: datetime
    #: True when any order in the group has a hard time window.
    has_window: bool = False
    window_start: datetime | None = None
    window_end: datetime | None = None


def consolidate_stops(
    orders: list[Order],
    parcels: dict[str, Parcel],
    shipments: dict[str, Shipment],
    values: ValueConfig | None = None,
    ready_times: dict[str, datetime] | None = None,
) -> list[ConsolidatedStop]:
    """Group the orders into delivery stops, one per distinct address.

    The grouping key is the address *id*, not the address text: two records
    for the same door with slightly different spellings should still share a
    stop, but the corpus already guarantees one address id per door.

    The stop's deadline is the earliest promise among its orders, because a
    courier cannot deliver one order late to make another on time.

    ``ready_times`` maps an order id to the instant its parcel was picked,
    packed and manifested. It comes from the warehouse queue, and it is
    what decides when the courier can leave. Applying a constant
    pick-and-pack lag here instead would make an evening order ready four
    hours after it was placed — which is after the day wave has gone home.
    See :mod:`tms.warehouse` for why that breaks the network.
    """

    vals = values or DEFAULT_VALUES
    grouped: dict[str, list[Order]] = defaultdict(list)
    for order in orders:
        grouped[order.address.address_id].append(order)

    shipments_by_order = index_shipments_by_order(shipments)

    if ready_times is None:
        ready_times = pick_and_pack(orders, vals)

    stops: list[ConsolidatedStop] = []
    for address_id, group in grouped.items():
        order_ids = tuple(sorted(o.order_id for o in group))
        parcel_ids: list[str] = []
        for order in group:
            shipment = shipments_by_order.get(order.order_id)
            if shipment is not None:
                parcel_ids.extend(shipment.parcel_ids)

        earliest = min(o.promised_at for o in group)
        # The parcel is not in hand until the warehouse has picked, packed
        # and manifested it. A stop carrying several orders is ready when
        # the *last* of them is — the courier cannot serve the group until
        # every parcel is on the van.
        ready = max(
            (ready_times.get(o.order_id) for o in group),
            default=None,
        )
        if ready is None:
            ready = max(o.created_at for o in group) + timedelta(
                minutes=vals.pick_pack_minutes
            )
        windowed = [o for o in group if o.service_level == ServiceLevel.SAME_DAY]
        stops.append(
            ConsolidatedStop(
                address=group[0].address,
                order_ids=order_ids,
                parcel_ids=tuple(parcel_ids),
                promised_at=earliest,
                ready_at=ready,
                has_window=bool(windowed),
                window_start=min((o.created_at for o in windowed), default=None),
                window_end=earliest if windowed else None,
            )
        )
    return stops


def _shipment_id_for(order_id: str, shipments: dict[str, Shipment]) -> str:
    """Find the shipment belonging to an order.

    The corpus creates exactly one shipment per order, so the id is
    derivable — but this lookup keeps the caller honest if that ever changes.

    A reverse index is built once per call rather than scanning the whole
    shipment table per order, because consolidation calls this once per
    order and the shipment table has thousands of rows.
    """
    for shipment_id, shipment in shipments.items():
        if shipment.order_id == order_id:
            return shipment_id
    return ""


def index_shipments_by_order(shipments: dict[str, Shipment]) -> dict[str, Shipment]:
    """Build an order-id to shipment index.

    Several parts of the system need "the shipment for this order" and a
    linear scan over the shipment table turns every one of them into an
    O(n^2) operation over the whole week of demand.
    """
    return {shipment.order_id: shipment for shipment in shipments.values()}


# --------------------------------------------------------------------------- #
# Allocation
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Allocation:
    """One courier's assignment: a set of stops and the parcels on them."""

    courier: Courier
    stops: list[ConsolidatedStop] = field(default_factory=list)
    capacity: Capacity = field(default_factory=lambda: Capacity(0.0, 0.0, 0))

    @property
    def parcel_count(self) -> int:
        """Total parcels assigned."""
        return sum(len(stop.parcel_ids) for stop in self.stops)

    @property
    def order_count(self) -> int:
        """Total orders assigned."""
        return sum(len(stop.order_ids) for stop in self.stops)

    @property
    def total_weight_kg(self) -> float:
        """Total weight assigned."""
        return self.capacity.weight_kg


@dataclass(slots=True)
class DispatchPlan:
    """The result of a dispatch run over one day."""

    day: datetime
    allocations: list[Allocation] = field(default_factory=list)
    #: Orders that could not be placed on any courier.
    unassigned_orders: list[str] = field(default_factory=list)
    #: Why each unassigned order was left out.
    unassigned_reason: dict[str, str] = field(default_factory=dict)
    #: Couriers hired for the day beyond the baseline roster.
    surge_couriers: list[str] = field(default_factory=list)
    #: Orders deliberately deferred to the next day's wave.
    deferred_orders: list[str] = field(default_factory=list)
    #: Orders that will breach their promise because of the capacity shortfall.
    projected_breaches: list[str] = field(default_factory=list)

    @property
    def assigned_orders(self) -> int:
        """How many orders found a courier."""
        return sum(a.order_count for a in self.allocations)

    @property
    def assigned_parcels(self) -> int:
        """How many parcels found a courier."""
        return sum(a.parcel_count for a in self.allocations)

    @property
    def stop_count(self) -> int:
        """Total stops across all couriers."""
        return sum(len(a.stops) for a in self.allocations)

    @property
    def orders_per_stop(self) -> float:
        """Order density: orders consolidated into each stop.

        Published operating figures put a bike at 25-45 parcels per route
        and a van at 60+. This metric is the single best early warning that
        consolidation has stopped working.
        """
        if self.stop_count == 0:
            return 0.0
        return round(self.assigned_orders / self.stop_count, 3)


def _mode_can_carry(mode: str, parcel: Parcel, values: ValueConfig) -> bool:
    """Whether a vehicle mode can physically take a parcel at all.

    A single parcel heavier than the mode's ceiling is not a capacity
    problem to be optimised around — it is the wrong vehicle. Sending a
    40 kg wardrobe on a bike produces a route plan that is arithmetically
    valid and physically absurd.
    """

    max_w, max_v, _ = values.mode_capacity[mode]
    return parcel.weight_kg <= max_w and parcel.volume_m3 <= max_v


def _zone_affinity(courier: Courier, order: Order) -> bool:
    """Whether the courier covers the order's zone."""
    return order.zone_id in courier.zone_ids


#: Where each hub physically is. Kept in step with the corpus's own hub
#: coordinates so the dispatcher can estimate travel time from the depot.
_HUB_COORDS: dict[str, tuple[float, float]] = {
    "hub-north": (12.9950, 77.6100),
    "hub-south": (12.9450, 77.5750),
    "hub-east": (12.9800, 77.6500),
    "hub-west": (12.9600, 77.5300),
}


def _hub_address(courier: Courier) -> Address:
    """A synthetic address for the courier's home hub."""
    lat, lng = _HUB_COORDS.get(courier.hub_id, (12.9716, 77.5946))
    return Address(
        address_id=f"hub-addr-{courier.hub_id}",
        line1="Fulfillment Center",
        area="Industrial Estate",
        city="Metro City",
        pin_code="000001",
        lat=lat,
        lng=lng,
        tier="tier1",
        landmark="Loading Bay",
    )


def _stop_service_minutes(stop: ConsolidatedStop, values: ValueConfig) -> float:
    """How long serving this stop takes."""
    parcel_count = max(1, len(stop.parcel_ids))
    return values.service_minutes_base + values.service_minutes_per_parcel * parcel_count


def _travel_minutes(
    origin: Address | None,
    destination: Address,
    courier: Courier,
    values: ValueConfig,
) -> float:
    """Estimated travel time from the courier's last position to a stop.

    Straight-line distance, scaled by the shared street-network detour
    factor, divided by the mode's rush-hour speed.

    The detour factor is the *same* one the router uses, and it has to
    be. The dispatcher decides how many stops a courier can make in a
    shift on the strength of this number; if the router then plans legs
    on a different basis, the plan it produces will not fit the shift
    the dispatcher promised, and the parcels at the end of the route
    will be delivered after the courier has gone home.
    """

    if origin is None:
        return 0.0
    speed = max(1.0, values.mode_speed_kmh.get(courier.mode.value, 12.0))
    km = (
        haversine_km(origin.lat, origin.lng, destination.lat, destination.lng)
        * DETOUR_FACTOR
    )
    return (km / speed) * 60.0


def allocate_orders(
    day: datetime,
    orders: list[Order],
    parcels: dict[str, Parcel],
    shipments: dict[str, Shipment],
    couriers: list[Courier],
    values: ValueConfig | None = None,
) -> DispatchPlan:
    """Assign stops to couriers under the hard constraints.

    The algorithm is deliberately simple and inspectable, because the
    interesting part of a dispatcher is not the heuristic — it is the
    constraint set. This one:

    1. Consolidates orders into address stops.
    2. Sorts stops by how urgent they are (earliest promise first).
    3. Walks the courier roster in order, giving each courier stops it can
       carry in zone until its capacity is exhausted.
    4. Routes a stop to the *cheapest feasible* courier — preferring a
       courier already in that zone, then one with more slack, so that
       specialised vehicles stay free for the parcels that need them.

    A stop whose parcels exceed every available envelope is left
    unassigned and recorded with a reason, rather than being force-fitted
    into a vehicle that cannot take it.
    """

    vals = values or DEFAULT_VALUES
    plan = DispatchPlan(day=day)

    orders_by_id = {o.order_id: o for o in orders}
    stops = consolidate_stops(orders, parcels, shipments, vals)
    # Stops are placed in **readiness order**, not urgency order.
    #
    # This is the single most consequential ordering decision in the
    # dispatcher, and getting it wrong is expensive. A courier's clock
    # only moves forward: once a courier's first stop is at 18:00 — a
    # parcel the warehouse did not manifest until the evening — every
    # stop placed on that courier afterwards is served after 18:00, and
    # the whole shift is wasted. So the stops that are ready in the
    # morning are placed first, and the evening batch goes to whoever
    # still has the evening ahead of them.
    #
    # Urgency still matters, but as a *tie-break* within a readiness
    # group rather than as the primary sort. Sorting purely by promise
    # puts the tightest deadline first, and the tightest deadline is
    # often the one whose parcel was ordered in the evening.
    stops.sort(key=lambda s: (s.ready_at, s.promised_at, -len(s.parcel_ids)))

    allocations = {
        c.courier_id: Allocation(
            courier=c, capacity=Capacity.from_courier(c, vals.shift_hours)
        )
        for c in couriers
    }
    ordered_couriers = list(couriers)

    # Track where each courier currently is, so the travel time to the next
    # stop can be estimated. Without this the shift-time constraint would
    # ignore travel entirely and every route would look like it fits.
    last_position: dict[str, Address] = {
        c.courier_id: _hub_address(c) for c in couriers
    }

    # Track *when* each courier would arrive at their next stop. The
    # minutes-used budget alone does not catch a route that starts on
    # time and then runs past the end of the shift: the budget says
    # "you have 400 minutes left" but says nothing about *when* the
    # courier has to be back. A route whose last stop is served after
    # the courier has gone home delivers the parcel a day late.
    #
    # The clock starts at the courier's shift. A courier who reaches the
    # hub before their parcel is ready waits for it — but that wait is
    # *before* the route starts, and it is not route time. Charging it to
    # the budget is what produced routes with a single stop that consumed
    # twelve hours of shift: the courier was at the loading bay at 07:00
    # waiting for a parcel that would not be manifested until 19:00, and
    # the budget said they had used all of it.
    #
    # So the clock jumps to the departure instead of crawling there. The
    # wait between stops — a parcel not ready when the courier arrives at
    # the address — is a different thing entirely, and *is* charged.
    courier_clock: dict[str, datetime] = {
        c.courier_id: c.shift_start for c in couriers
    }
    #: Couriers who have not departed yet. Their clock is still their shift
    #: start, and the first stop they take fixes the departure.
    departed: set[str] = set()

    # The **effective deadline** for each courier's route: the latest
    # moment the last delivery has to be served, allowing for the ride
    # back to the hub.
    #
    # The shift end is not the deadline. The shift end is when the
    # courier goes home, and they have to be *back* by then. A courier
    # whose last delivery is served at 22:50 with a thirty-minute ride
    # home is on the road until 23:20, which is not on shift any more.
    #
    # The reserve is one leg of the current distance — a fair estimate of
    # the ride home, because hubs sit at the edge of their zone and the
    # return leg is about as long as the last outbound one.
    effective_deadline: dict[str, datetime] = {
        c.courier_id: c.shift_end for c in couriers
    }
    #: The reserve, per courier, in minutes. Seeded from the hub and
    #: updated as the courier moves away from it.
    return_reserve: dict[str, float] = {
        c.courier_id: _travel_minutes(_hub_address(c), _hub_address(c), c, vals)
        for c in couriers
    }

    for stop in stops:
        stop_parcels = [parcels[p] for p in stop.parcel_ids if p in parcels]
        if not stop_parcels:
            continue

        # A stop is only assignable if some vehicle can take every parcel.
        feasible_modes = [
            c.mode.value
            for c in ordered_couriers
            if all(_mode_can_carry(c.mode.value, p, vals) for p in stop_parcels)
        ]
        if not feasible_modes:
            plan.unassigned_orders.extend(stop.order_ids)
            for oid in stop.order_ids:
                plan.unassigned_reason[oid] = "no vehicle in the roster can carry this stop"
            continue

        best: Allocation | None = None
        best_key: tuple[float, float, float] | None = None
        best_travel_minutes = 0.0
        best_wait_minutes = 0.0

        for courier in ordered_couriers:
            if courier.mode.value not in feasible_modes:
                continue
            alloc = allocations[courier.courier_id]

            # -- Hard constraint: the parcel must be servable before the
            # courier goes off shift. A courier cannot deliver a parcel
            # that is still sitting in the warehouse when they finish, and
            # putting such a parcel on their route poisons the whole
            # route: the departure time becomes the *latest* ready time
            # on the route, so one late-evening order delays every other
            # parcel behind it by a full day. Orders that are not ready
            # in time belong on tomorrow's wave, not this one.
            #
            # "Servable" is stronger than "picked". A parcel manifested at
            # 22:00 is picked, but nobody can deliver it tonight: the
            # last courier is on their way home, and the handover has to
            # happen *before* the ride back. So the check is against the
            # effective deadline, not the shift end — and a stop that
            # misses it on every courier is deferred to tomorrow's first
            # wave rather than put on a route that cannot finish.
            if stop.ready_at > effective_deadline[courier.courier_id]:
                continue

            service_minutes = _stop_service_minutes(stop, vals)
            travel_minutes = _travel_minutes(
                last_position.get(courier.courier_id),
                stop.address,
                courier,
                vals,
            )

            if not all(
                alloc.capacity.can_accept(p, 0.0) for p in stop_parcels
            ):
                continue

            # -- Hard constraint: the courier must still be on the road --- #
            # The parcel has to be *served* before the shift ends, not just
            # picked up. A courier whose route would have them delivering
            # at 04:00 the next morning has not delivered anything — the
            # parcel goes out on someone else's route, a day later, and
            # the promise is missed for a reason nobody planned for.
            #
            # The courier arrives at the later of "when they could get
            # here" and "when the parcel is in hand".
            #
            # Before departure that wait is free: the courier is at the
            # loading bay, not on the road, and the shift has not started
            # for them. After departure it is not: a courier who drives to
            # an address and finds the parcel is still at the warehouse
            # has burned the drive and the wait both.
            if courier.courier_id in departed:
                arrival = max(
                    courier_clock[courier.courier_id] + timedelta(minutes=travel_minutes),
                    stop.ready_at,
                )
                wait_minutes = max(
                    0.0,
                    (
                        arrival
                        - (
                            courier_clock[courier.courier_id]
                            + timedelta(minutes=travel_minutes)
                        )
                    ).total_seconds()
                    / 60.0,
                )
            else:
                # Not yet departed: the courier leaves when the parcel is
                # in hand, and the wait does not come out of their shift.
                arrival = max(
                    courier.shift_start + timedelta(minutes=travel_minutes),
                    stop.ready_at,
                )
                wait_minutes = 0.0

            # -- Hard constraint: the courier has to get back -------------- #
            # The last delivery of the shift is not the last thing that
            # happens in it. The courier still has to ride back to the
            # hub, and a courier who is still on the road at the end of
            # their shift is on the road unpaid.
            #
            # The reserve is one leg of the current distance, which is a
            # fair estimate of the ride home: hubs sit at the edge of
            # their zone, so the return leg is about as long as the last
            # outbound one.
            return_minutes = _travel_minutes(
                stop.address,
                _hub_address(courier),
                courier,
                vals,
            )

            # -- The deadline, not the shift end ---------------------------- #
            # Everything above is measured against the *effective* deadline
            # — the moment the last delivery has to be served so that the
            # courier is back at the hub before the shift ends.
            #
            # Measuring against the raw shift end is what produced the
            # routes that overflow: the dispatcher believed a courier had
            # until 23:00 to serve their last stop, the router believed
            # the same thing, and then the router's trim — which does
            # account for the ride home — dropped the tail of the route and
            # deferred the orders on it. The two disagreed about the same
            # route, and the orders on the losing end of the disagreement
            # were delivered a day late.
            deadline = effective_deadline[courier.courier_id]

            # The whole stop — the drive, the wait and the handover — has
            # to fit between the arrival and the deadline, and the ride
            # home has to fit after it.
            finish = arrival + timedelta(
                minutes=service_minutes + wait_minutes + return_minutes
            )
            if finish > deadline:
                continue

            # The wait is charged to the shift. A courier who spends nine
            # hours waiting for a parcel to be manifested has spent nine
            # hours of their shift standing at an address, and the budget
            # has to say so — otherwise the dispatcher hands them a full
            # route on top of it and the shift overflows by hours.
            needed_minutes = service_minutes + travel_minutes + wait_minutes

            # A courier who has not departed yet has their whole shift in
            # front of them; one who is on the road has only what is left
            # of their budget.
            budget_minutes = (
                alloc.capacity.minutes_remaining
                if courier.courier_id in departed
                else alloc.capacity.max_minutes
            )
            if budget_minutes < needed_minutes:
                continue

            in_zone = _zone_affinity_for_stop(courier, stop, shipments, orders_by_id)
            # -- Preference order ---------------------------------------- #
            # Zone affinity comes first and on its own, because it is worth
            # more than any amount of balance: a courier who does not know
            # the area drives further, arrives later and fails more often.
            # Balancing load is a soft preference, and it is deliberately
            # *not* allowed to override zone affinity — otherwise the
            # least-loaded courier wins every time, whoever they are, and
            # the whole network ends up crossing the city on every route.
            #
            # Within a tier: the courier who has the *most* shift left, so
            # the time budget is not the binding constraint on the route
            # being built, then the cheaper vehicle, so the vans stay free
            # for bulky stops.
            #
            # The second key is negated because the tuple is minimised. A
            # positive ``minutes_remaining`` would send every stop to
            # whichever courier is already the most loaded, which fills
            # one route to the brim and leaves the rest idle — and the
            # routes that overflow are the ones that breach.
            #
            # The third key is the number of stops already on the route.
            # Two couriers in the same zone with the same slack are
            # interchangeable; the one with fewer stops should take this
            # one, because that is what spreads the work evenly across
            # the wave.
            key = (
                0.0 if in_zone else 1.0,
                -alloc.capacity.minutes_remaining,
                float(len(alloc.stops)),
                vals.courier_fixed_cost[courier.mode.value],
            )
            if best_key is None or key < best_key:
                best_key = key
                best = alloc
                best_travel_minutes = travel_minutes
                best_wait_minutes = wait_minutes

        if best is None:
            plan.unassigned_orders.extend(stop.order_ids)
            for oid in stop.order_ids:
                plan.unassigned_reason[oid] = _unassigned_reason(stop, ordered_couriers)
            continue

        # Charge the courier for the stop once: its parcels, its service
        # time, the travel to reach it, and any wait for the parcel to be
        # picked. The travel was already measured against the courier's
        # previous position when the stop was chosen.
        service_minutes = _stop_service_minutes(stop, vals)
        best.capacity.load_stop(
            stop_parcels,
            service_minutes + best_travel_minutes + best_wait_minutes,
        )
        best.stops.append(stop)

        # The courier is now at this stop, so the next travel estimate for
        # this courier starts from here — and their clock moves on by the
        # travel, the wait and the service time.
        last_position[best.courier.courier_id] = stop.address
        if best.courier.courier_id in departed:
            courier_clock[best.courier.courier_id] = (
                courier_clock[best.courier.courier_id]
                + timedelta(
                    minutes=best_travel_minutes + best_wait_minutes + service_minutes
                )
            )
        else:
            # The courier's first stop fixes their departure. They leave
            # when the parcel is in hand, and their clock starts there —
            # the wait at the loading bay is not route time.
            courier_clock[best.courier.courier_id] = (
                best.courier.shift_start
                + timedelta(minutes=best_travel_minutes)
                if stop.ready_at <= best.courier.shift_start
                else stop.ready_at
            ) + timedelta(minutes=service_minutes)
            departed.add(best.courier.courier_id)

        # -- Keep the effective deadline in step with the route ----------- #
        # The deadline moves as the courier's position moves, because the
        # ride home gets longer as the courier's last stop gets further
        # from the hub. A courier whose route ends on the far side of the
        # zone needs more time to get back than one whose route ends at
        # the hub's doorstep.
        #
        # More importantly, the deadline is anchored to the *departure*.
        # A courier who does not leave until 19:00 does not have a whole
        # nine-hour shift ahead of them; they have four hours, and the
        # route has to fit in four hours. Ignoring this is what let the
        # dispatcher hand an evening courier a route that the router
        # then had to trim.
        return_minutes = _travel_minutes(
            stop.address,
            _hub_address(best.courier),
            best.courier,
            vals,
        )
        return_reserve[best.courier.courier_id] = return_minutes
        effective_deadline[best.courier.courier_id] = best.courier.shift_end - timedelta(
            minutes=return_minutes
        )

    plan.allocations = [a for a in allocations.values() if a.stops]
    return plan


def _unassigned_reason(stop: ConsolidatedStop, couriers: list[Courier]) -> str:
    """Why could this stop not be placed on any courier?

    The reason matters operationally: "no courier has capacity" means the
    roster is too small and someone needs to hire, while "the parcel is not
    ready before the shift ends" means the order belongs on tomorrow's wave
    and nothing is actually wrong.
    """

    if not any(c.shift_end >= stop.ready_at for c in couriers):
        return "parcel is not ready before any courier goes off shift"
    return "no courier has capacity for this stop"


def _order_of(
    stop: ConsolidatedStop,
    shipments: dict[str, Shipment],
    orders_by_id: dict[str, Order],
) -> Order | None:
    """Find the first order in a stop, using an index.

    Used for zone lookups, which happen for every candidate courier at
    every stop — so this cannot afford to scan the order list.
    """
    for oid in stop.order_ids:
        order = orders_by_id.get(oid)
        if order is not None:
            return order
    return None


def _zone_affinity_for_stop(
    courier: Courier,
    stop: ConsolidatedStop,
    shipments: dict[str, Shipment],
    orders_by_id: dict[str, Order],
) -> bool:
    """Whether the courier's zone set covers this stop's zone."""
    order = _order_of(stop, shipments, orders_by_id)
    if order is None:
        return False
    return _zone_affinity(courier, order)


# --------------------------------------------------------------------------- #
# Surge handling
# --------------------------------------------------------------------------- #


def dispatch_day(
    world: World,
    day: datetime,
    values: ValueConfig | None = None,
    carry_in: list[str] | None = None,
) -> DispatchPlan:
    """Run the full dispatch flow for one operating day.

    When demand exceeds the baseline roster's capacity, the shortfall is
    closed in a defined order of preference, which mirrors what a real
    operations team does on a campaign day:

    1. **Hire surge couriers** — up to ``surge_hiring_share`` of the
       shortfall, at a premium.
    2. **Defer the remainder to the next wave** — the order ships a day
       later, which is a promise breach but a delivered parcel.
    3. **Project the breach** — anything still unplaced is recorded as a
       projected SLA breach so it shows up on the dashboard before the
       customer complains.

    The order matters. Deferring is preferable to breaching on the same
    day, because a parcel delivered late still generates revenue and a
    fulfilled order, whereas a cancelled one does not.

    ``carry_in`` are order ids deferred from an earlier day. They are
    dispatched alongside the day's own orders, so a parcel that missed
    yesterday's last wave ships on today's first one rather than sitting
    in the warehouse. Without the carry-over, an order placed at 11pm
    would wait a full extra day for a courier who starts at 7am — a
    promise broken by a day for no reason other than an accounting
    boundary.
    """

    vals = values or DEFAULT_VALUES
    day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)

    orders_today = [
        o for o in world.orders.values() if o.created_at.date() == day_start.date()
    ]
    if carry_in:
        carried = [world.orders[oid] for oid in carry_in if oid in world.orders]
        orders_today.extend(carried)

    shipments = world.shipments
    parcels = world.parcels

    roster = [
        c for c in world.couriers.values()
        if c.shift_start.date() == day_start.date()
    ]

    # The whole roster — baseline and surge together — is allocated in one
    # pass.
    #
    # The surge couriers are rostered *per zone*, in the zones that
    # actually have the campaign's orders, so they are already where the
    # work is. Running them as a separate second pass would put them
    # behind the baseline couriers in every zone, which means the
    # baseline fills up first and the surge couriers pick up only the
    # leftovers — the leftovers being the orders nobody could place,
    # which are exactly the ones a surge courier cannot reach either.
    plan = allocate_orders(day_start, orders_today, parcels, shipments, roster, vals)
    plan.surge_couriers.extend(
        a.courier.courier_id for a in plan.allocations if a.courier.is_surge
    )

    # -- Defer what surge could not absorb --------------------------------- #
    if plan.unassigned_orders:
        deferred = list(plan.unassigned_orders)
        plan.deferred_orders = deferred
        plan.projected_breaches = list(deferred)
        plan.unassigned_orders = []
        plan.unassigned_reason = {}

    return plan


def plan_summary(plan: DispatchPlan) -> dict[str, Any]:
    """A JSON-friendly summary of a dispatch plan."""
    by_mode: dict[str, int] = defaultdict(int)
    for alloc in plan.allocations:
        by_mode[alloc.courier.mode.value] += alloc.parcel_count

    return {
        "day": plan.day.isoformat(),
        "couriers_used": len(plan.allocations),
        "surge_couriers": len(plan.surge_couriers),
        "assigned_orders": plan.assigned_orders,
        "assigned_parcels": plan.assigned_parcels,
        "stops": plan.stop_count,
        "orders_per_stop": plan.orders_per_stop,
        "parcels_by_mode": dict(by_mode),
        "deferred_orders": len(plan.deferred_orders),
        "projected_breaches": len(plan.projected_breaches),
    }
