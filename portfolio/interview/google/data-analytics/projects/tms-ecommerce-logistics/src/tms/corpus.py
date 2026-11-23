"""The synthetic corpus: a week of e-commerce delivery demand, generated.

**The corpus is the ground truth.** Every metric this project reports is a
function of the world this module builds, so the world has to be
(a) realistic enough that the numbers are worth reading and (b) deterministic
enough that a reviewer can reproduce them exactly.

Determinism comes from a single seeded PRNG — the same seed always produces
the same week of orders, the same couriers, the same planted fraud cases.

**Ground truth is planted, not inferred.** The generator deliberately creates
a set of orders that *are* return-fraud attempts, a set of addresses with a
known bad delivery history, and a set of parcels that trip the volumetric
weight rule. These are recorded in :attr:`World.ground_truth` so the eval
harness can check that the risk model and the billing model actually find
them, rather than measuring agreement with themselves.

Sub-parts
---------
- Geography: a small city lattice with hubs and delivery zones.
- Demand generation: orders per day, with a campaign-day peak.
- Parcel generation: log-normal weights and dimensions.
- Fleet generation: couriers per hub and zone, sized to the demand.
- :func:`build_world` — assembles everything.
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta, timezone
from typing import Any

from .config import DEFAULT_VALUES, Settings, ValueConfig
from .models import (
    Address,
    Courier,
    Order,
    OrderStatus,
    Parcel,
    ServiceLevel,
    Shipment,
    VehicleMode,
    World,
)
from .promises import is_offerable, service_window

# --------------------------------------------------------------------------- #
# Geography
# --------------------------------------------------------------------------- #

#: The simulated market. Four hubs, each with delivery zones around it.
#: Coordinates are plausible for a South-Asian metro but are invented.
CITY_CENTER = (12.9716, 77.5946)

_HUBS: list[tuple[str, str, float, float]] = [
    ("hub-north", "North Fulfillment Center", 12.9950, 77.6100),
    ("hub-south", "South Fulfillment Center", 12.9450, 77.5750),
    ("hub-east", "East Fulfillment Center", 12.9800, 77.6500),
    ("hub-west", "West Fulfillment Center", 12.9600, 77.5300),
]

_ZONE_TIERS: list[tuple[str, str]] = [
    ("z-n1", "tier1"),
    ("z-n2", "tier2"),
    ("z-n3", "tier3"),
    ("z-s1", "tier1"),
    ("z-s2", "tier2"),
    ("z-s3", "tier3"),
    ("z-e1", "tier1"),
    ("z-e2", "tier2"),
    ("z-e3", "tier3"),
    ("z-w1", "tier1"),
    ("z-w2", "tier2"),
    ("z-w3", "tier3"),
]

_CARRIERS: list[tuple[str, int]] = [
    ("ninja_van", 30),
    ("delhivery", 25),
    ("xpressbees", 20),
    ("jnt_express", 15),
    ("lalamove", 10),
]

_MERCHANTS: list[str] = [
    "merch-fashion-hub",
    "merch-electronics-direct",
    "merch-home-living",
    "merch-beauty-co",
    "merch-grocery-fresh",
]

_FIRST_NAMES = [
    "Aarav", "Mei", "Siti", "Rohan", "Priya", "Wei", "Anjali", "Kiran",
    "Fatima", "Dinesh", "Nurul", "Vikram", "Chloe", "Arjun", "Lakshmi",
    "Marco", "Yuki", "Omar", "Deepa", "Ravi",
]
_LAST_NAMES = [
    "Sharma", "Tan", "Lim", "Patel", "Wong", "Ibrahim", "Nair", "Khan",
    "Rao", "Singh", "Chong", "Fernandez", "Mehta", "Abdullah", "Raj",
]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _lognormal(rng: random.Random, mu: float, sigma: float, low: float, high: float) -> float:
    """A log-normal draw clamped to a sane range."""
    return max(low, min(high, rng.lognormvariate(mu, sigma)))


def _make_address(
    rng: random.Random,
    address_id: str,
    zone_id: str,
    zone_tier: str,
    hub_id: str,
) -> Address:
    """Build one address, sometimes a bad one.

    Address problems are a top-five cause of failed delivery in published
    breakdowns, so roughly one in nine addresses gets a flag: a bad PIN code,
    a missing landmark, a low geocode confidence, or a PIN code with a known
    fraud history.
    """

    hub = next(h for h in _HUBS if h[0] == hub_id)
    # Zone radius, in degrees of latitude. A real delivery zone in a dense
    # metro is 3-6 km across, not 25 km — and the size of this number sets
    # the achievable stop count for the whole network. With a 0.14-degree
    # spread a courier spends 40 minutes riding between two adjacent stops
    # and can only make five deliveries in a ten-hour shift, which shows up
    # downstream as a network that breaches every promise.
    #
    # The spread below is a *standard deviation*, not a diameter, so a zone
    # is roughly three times it across: a tier-1 zone about 3 km and a
    # tier-3 zone about 9 km. That is the range a bike courier actually
    # works, and it is what makes twenty stops in a shift arithmetically
    # possible.
    spread = {"tier1": 0.007, "tier2": 0.011, "tier3": 0.017}[zone_tier]
    # Each zone is centred a little way off its hub, so the three zones a
    # hub serves do not sit on top of each other. A courier whose route
    # crosses two zones has to cross a boundary, and that boundary is
    # where the interesting scheduling problems are.
    zone_index = int(zone_id.split("-")[1][1:])
    angle = (zone_index - 1) * (2.0 * math.pi / 3.0)
    offset = {"tier1": 0.009, "tier2": 0.014, "tier3": 0.020}[zone_tier]
    centre_lat = hub[2] + offset * math.sin(angle)
    centre_lng = hub[3] + offset * math.cos(angle)

    lat = centre_lat + rng.gauss(0, spread)
    lng = centre_lng + rng.gauss(0, spread)

    flagged = rng.random() < DEFAULT_VALUES.flagged_address_share
    known_bad_pin = False
    landmark: str | None = None
    geocode_confidence = 1.0
    pin = f"{rng.randint(110000, 799999)}"

    if flagged:
        defect = rng.choice(
            ["bad_pin", "no_landmark", "low_geocode", "known_bad", "short_pin"]
        )
        if defect == "bad_pin":
            pin = f"{rng.randint(100000, 999999)}"
        elif defect == "no_landmark":
            landmark = None
        elif defect == "low_geocode":
            geocode_confidence = rng.uniform(0.35, 0.65)
        elif defect == "known_bad":
            known_bad_pin = True
            pin = f"{rng.randint(560000, 560099)}"
        elif defect == "short_pin":
            pin = f"{rng.randint(1000, 9999)}"

    if rng.random() < 0.72:
        landmark = rng.choice(
            ["Near City Hospital", "Opposite Police Station", "Behind Central Mall",
             "Next to Sacred Heart School", "Above HDFC ATM", "Near Water Tank",
             "Adjacent to Tea Stall", "Behind Community Park"]
        )

    street_no = rng.randint(1, 240)
    street = rng.choice(
        ["MG Road", "Park Street", "Anna Salai", "Church Street", "Station Road",
         "Market Lane", "Nehru Avenue", "Gandhi Nagar", "Lake View Road", "Temple Street"]
    )
    area = rng.choice(
        ["Indiranagar", "Koramangala", "Jayanagar", "Banjara Hills", "Vembuli",
         "Ayanappa Nagar", "Gurugram Sector 14", "Powai", "Whitefield", "Kalyan Nagar"]
    )
    city = "Metro City"

    return Address(
        address_id=address_id,
        line1=f"{street_no}, {street}",
        area=area,
        city=city,
        pin_code=pin,
        lat=round(lat, 6),
        lng=round(lng, 6),
        tier=zone_tier,
        landmark=landmark,
        geocode_confidence=round(geocode_confidence, 3),
        known_bad_pin=known_bad_pin,
    )


def _make_parcels(
    rng: random.Random,
    order_id: str,
    values: ValueConfig,
    multi_package: bool,
) -> list[Parcel]:
    """Generate the parcels for one order.

    Weights and dimensions are log-normal, which is what parcel data actually
    looks like: a long thin tail of heavy boxes with most of the volume in
    small light parcels.
    """

    count = rng.randint(2, 3) if multi_package else 1
    parcels: list[Parcel] = []
    for idx in range(count):
        weight = _lognormal(rng, values.weight_mu, values.weight_sigma, 0.15, 42.0)
        length = _lognormal(rng, values.dim_mu, values.dim_sigma, 8.0, 95.0)
        width = _lognormal(rng, values.dim_mu - 0.35, values.dim_sigma, 6.0, 70.0)
        height = _lognormal(rng, values.dim_mu - 0.75, values.dim_sigma, 4.0, 55.0)
        parcels.append(
            Parcel(
                parcel_id=f"pcl-{order_id}-{idx + 1}",
                order_id=order_id,
                weight_kg=round(weight, 3),
                length_cm=round(length, 2),
                width_cm=round(width, 2),
                height_cm=round(height, 2),
            )
        )
    return parcels


def _make_courier(
    rng: random.Random,
    courier_id: str,
    mode: VehicleMode,
    hub_id: str,
    zone_ids: tuple[str, ...],
    day: datetime,
    values: ValueConfig,
    is_surge: bool = False,
    shift_wave: str = "day",
) -> Courier:
    """Build one courier with their capacity envelope and cost structure.

    ``shift_wave`` picks which part of the day the courier works. A
    single long shift cannot cover an evening-weighted demand curve: a
    courier who starts at 7am is off the road before the evening orders
    have been picked, and a dispatcher that respects the shift boundary
    then has to defer half of them to the next day. Two overlapping
    waves — a day wave and an evening wave — is how real networks cover
    the curve without asking anyone to work sixteen hours.
    """
    max_w, max_v, max_p = values.mode_capacity[mode.value]
    fixed = values.courier_fixed_cost[mode.value]
    if is_surge:
        fixed *= values.surge_premium_multiplier

    if shift_wave == "evening":
        start_hour = values.evening_shift_start_hour + rng.uniform(-0.5, 0.5)
        shift_hours = values.evening_shift_hours + rng.uniform(-0.5, 1.0)
    else:
        start_hour = values.dispatch_start_hour + rng.uniform(-0.75, 0.75)
        shift_hours = values.shift_hours + rng.uniform(-1.0, 1.5)

    start_hour = max(0.0, min(23.0, start_hour))
    shift_start = day.replace(hour=int(start_hour), minute=int((start_hour % 1) * 60))

    first = rng.choice(_FIRST_NAMES)
    last = rng.choice(_LAST_NAMES)
    return Courier(
        courier_id=courier_id,
        name=f"{first} {last}",
        mode=mode,
        hub_id=hub_id,
        zone_ids=zone_ids,
        shift_start=shift_start,
        shift_end=shift_start + timedelta(hours=shift_hours),
        is_surge=is_surge,
        fixed_cost=round(fixed, 2),
        cost_per_stop=values.courier_cost_per_stop[mode.value],
        cost_per_km=values.courier_cost_per_km[mode.value],
        max_weight_kg=max_w,
        max_volume_m3=max_v,
        max_parcels=max_p,
    )


# --------------------------------------------------------------------------- #
# World construction
# --------------------------------------------------------------------------- #


def build_world(settings: Settings | None = None, values: ValueConfig | None = None) -> World:
    """Build the whole simulated world.

    One call, one deterministic world. The function is pure with respect to
    its settings: same settings in, same world out.

    The shape of the week:

    - Day 0 is a normal Monday.
    - Day 3 is the campaign peak, with demand multiplied.
    - Day 5 is a normal Friday.
    - Days 1, 2, 4 and 6 are normal days.

    Couriers are sized to the demand of the day they work, so the surge day
    has a visibly larger roster — including surge couriers hired at a premium.
    """

    cfg = settings or Settings.from_env()
    vals = values or DEFAULT_VALUES
    rng = random.Random(cfg.seed)

    start_day = datetime(2026, 11, 16, 0, 0, 0, tzinfo=timezone.utc)
    peak_day_index = 3

    world = World(
        hubs={h[0]: h[1] for h in _HUBS},
        zones={zone_id: tier for zone_id, tier in _ZONE_TIERS},
        now=start_day + timedelta(days=cfg.now_day_index, hours=14),
    )

    # -- Zone to hub mapping ----------------------------------------------- #
    # Each hub serves the three zones around it. The zone ids already
    # encode their geography (n = north, s = south, e = east, w = west),
    # so the mapping is by geography rather than by position in a list.
    # Getting this wrong puts a north hub's courier on a route to the
    # south side of the city, which is both slow and completely
    # avoidable.
    _ZONE_HUB_BY_PREFIX = {
        "n": "hub-north",
        "s": "hub-south",
        "e": "hub-east",
        "w": "hub-west",
    }
    zone_hub: dict[str, str] = {
        zone_id: _ZONE_HUB_BY_PREFIX[zone_id.split("-")[1][0]]
        for zone_id, _ in _ZONE_TIERS
    }

    # -- Addresses ---------------------------------------------------------- #
    # A pool of addresses that orders draw from, so the same address appears
    # across multiple orders. That is what makes stop consolidation possible
    # and what gives a PIN code a track record.
    #
    # The pool is **per zone**, and an order draws from its own zone's pool.
    # This is how a real delivery network is built: a zone is a contiguous
    # patch of the city with its own address set, and the couriers who work
    # that zone know its streets. Drawing an order's address from the whole
    # city instead puts a north-zone courier on a 25 km round trip to the
    # south side, and the resulting route plan is arithmetically valid and
    # operationally absurd.
    #
    # A small minority of orders deliberately draw from a *neighbouring*
    # zone — that is the boundary case a dispatcher actually has to deal
    # with, and it gives zone affinity something to bite on.
    address_pool_by_zone: dict[str, list[Address]] = {}
    per_zone = 55
    for zone_id, zone_tier in _ZONE_TIERS:
        pool: list[Address] = []
        for n in range(per_zone):
            addr = _make_address(
                rng,
                f"adr-{zone_id}-{n:03d}",
                zone_id,
                zone_tier,
                zone_hub[zone_id],
            )
            pool.append(addr)
            world.addresses[addr.address_id] = addr
        address_pool_by_zone[zone_id] = pool
    address_pool = [a for pool in address_pool_by_zone.values() for a in pool]

    # Neighbouring zones, by the compass prefix. A zone's neighbours are the
    # zones on the other sides of its hub, so a boundary order is a short
    # drive away rather than a cross-city one.
    def _neighbours(zone_id: str) -> list[str]:
        prefix = zone_id.split("-")[1][0]
        others = [z for z, _ in _ZONE_TIERS if z.split("-")[1][0] != prefix]
        # Only the two adjacent sides, not the opposite one.
        return others[:2]

    # -- Orders, shipments, parcels ----------------------------------------- #
    order_seq = 0
    fraud_planted: list[str] = []
    breach_planted: list[str] = []
    cod_planted: list[str] = []

    for day_index in range(cfg.days):
        day = start_day + timedelta(days=day_index)
        is_peak = day_index == peak_day_index
        demand = int(cfg.orders_per_day * (cfg.peak_multiplier if is_peak else 1.0))

        # Demand is not uniform through the day: it follows a shopping curve
        # that peaks in the evening, which is why dispatch cut-off matters.
        for _ in range(demand):
            order_seq += 1
            order_id = f"ord-{order_seq:05d}"

            zone_id, zone_tier = rng.choice(_ZONE_TIERS)
            # Most orders are inside their own zone; a minority spill over
            # the boundary into a neighbouring one.
            if rng.random() < 0.12:
                neighbours = _neighbours(zone_id)
                if neighbours:
                    zone_id = rng.choice(neighbours)
            address = rng.choice(address_pool_by_zone[zone_id])

            # Time of day, weighted towards the evening peak.
            hour_weights = [1, 1, 1, 1, 1, 2, 3, 4, 5, 5, 5, 6, 6, 6, 6, 7, 8, 9, 10, 9, 8, 7, 5, 3]
            hour = rng.choices(range(24), weights=hour_weights, k=1)[0]
            created_at = day.replace(
                hour=hour, minute=rng.randint(0, 59), second=rng.randint(0, 59)
            )

            service_level = rng.choices(
                list(vals.service_level_mix),
                weights=list(vals.service_level_mix.values()),
                k=1,
            )[0]

            # -- The service-level cut-off ---------------------------------- #
            # A service level is only offered while the network can actually
            # meet it. A same-day order placed at 2am cannot be delivered by
            # 4pm in a network whose warehouse needs four hours to pick and
            # pack and whose couriers start at 7am — so a real operator
            # stops selling same-day once the cut-off passes, and sells
            # next-day instead.
            #
            # Modelling this is the difference between a network that
            # reports an honest on-time rate and one that reports a
            # catastrophic one because it promised what it could not
            # deliver. The failure rate becomes a *property of the
            # promise*, not an accident of the schedule.
            #
            # The cut-off is derived from the operating envelope rather
            # than being a hard-coded hour, so it moves when the shift
            # pattern moves. See :mod:`tms.promises`.
            if not is_offerable(ServiceLevel(service_level), created_at, zone_tier, vals):
                service_level = ServiceLevel.NEXT_DAY.value

            # -- Planted ground truth --------------------------------------- #
            # A small number of orders are genuine return-fraud attempts. The
            # generator plants them with telltale features so the risk model
            # has something real to find.
            planted_fraud = rng.random() < 0.022
            if planted_fraud:
                base = _make_address(
                    rng, f"adr-fraud-{order_id}", zone_id, zone_tier, zone_hub[zone_id]
                )
                address = Address(
                    address_id=base.address_id,
                    line1=base.line1,
                    area=base.area,
                    city=base.city,
                    pin_code=base.pin_code,
                    lat=base.lat,
                    lng=base.lng,
                    tier=base.tier,
                    landmark=None,
                    geocode_confidence=round(rng.uniform(0.25, 0.5), 3),
                    known_bad_pin=True,
                )
                world.addresses[address.address_id] = address
                fraud_planted.append(order_id)

            tier = address.tier

            # A few orders are placed against a promise the network cannot
            # possibly meet — a same-day promise in a tier-3 zone, for
            # instance. These become the planted SLA breaches.
            #
            # The breach is planted by *tightening the promise*, not by
            # changing the service level, so the order is still a
            # same-day order with a same-day promise — it is just a
            # promise the network had no way to keep.
            forced_breach = rng.random() < 0.035
            promised_at = service_window(
                ServiceLevel(service_level), created_at, tier, vals
            )
            if forced_breach:
                service_level = ServiceLevel.SAME_DAY
                promised_at = created_at + timedelta(
                    hours=vals.service_level_hours[ServiceLevel.SAME_DAY.value] // 3
                )
                breach_planted.append(order_id)

            cod_share = vals.cod_share_by_tier.get(tier, 0.5)
            is_cod = rng.random() < cod_share
            if is_cod:
                cod_planted.append(order_id)

            order_value = round(
                _lognormal(rng, vals.order_value_mu, vals.order_value_sigma, 99.0, 45000.0), 2
            )
            merchant = rng.choice(_MERCHANTS)
            customer_id = f"cus-{rng.randint(1, 900):04d}"

            multi_package = rng.random() < vals.multi_package_share

            order = Order(
                order_id=order_id,
                customer_id=customer_id,
                address=address,
                service_level=ServiceLevel(service_level),
                order_value=order_value,
                is_cod=is_cod,
                promised_at=promised_at,
                created_at=created_at,
                zone_id=zone_id,
                merchant_id=merchant,
                is_multi_package=multi_package,
                planted_fraud=planted_fraud,
            )
            world.orders[order_id] = order

            parcels = _make_parcels(rng, order_id, vals, multi_package)
            for parcel in parcels:
                world.parcels[parcel.parcel_id] = parcel

            carrier, _ = rng.choices(_CARRIERS, weights=[c[1] for c in _CARRIERS], k=1)[0]
            shipment_id = f"shp-{order_seq:05d}"
            tracking = f"{carrier[:3].upper()}{rng.randint(10_000_000, 99_999_999)}"
            world.shipments[shipment_id] = Shipment(
                shipment_id=shipment_id,
                order_id=order_id,
                tracking_number=tracking,
                service_level=ServiceLevel(service_level),
                carrier=carrier,
                origin_hub=zone_hub[zone_id],
                destination_hub=zone_hub[zone_id],
                status=OrderStatus.CREATED,
                promised_at=order.promised_at,
                parcel_ids=tuple(p.parcel_id for p in parcels),
            )

    # -- Fleet --------------------------------------------------------------- #
    # The roster is sized per day against that day's demand, then split across
    # hubs and zones. Each courier is given a home hub and the zones they
    # cover — zone affinity is a real cost driver, because a courier who
    # knows the area makes fewer mistakes.
    day_orders: dict[int, list[Order]] = {}
    for order in world.orders.values():
        idx = (order.created_at - start_day).days
        day_orders.setdefault(idx, []).append(order)

    courier_seq = 0
    for day_index in range(cfg.days):
        day = start_day + timedelta(days=day_index)
        orders_today = day_orders.get(day_index, [])
        if not orders_today:
            continue

        # -- Size each shift wave against the demand it can actually serve -- #
        # A wave can only take orders that are picked, packed and ready
        # before the wave's couriers go off shift. So the day wave is sized
        # against the demand up to the evening cut-off, and the evening wave
        # against everything after it. Sizing the whole roster against the
        # whole day instead leaves the evening wave short exactly when
        # demand peaks, and the shortfall shows up as deferred orders.
        day_cutoff = vals.evening_shift_start_hour
        day_wave_orders = [o for o in orders_today if o.created_at.hour < day_cutoff]
        evening_wave_orders = [o for o in orders_today if o.created_at.hour >= day_cutoff]

        # A courier completes roughly this many **orders** in a shift, at
        # realistic urban distances and service times. Sizing against
        # carrying capacity instead would over-staff the roster by a
        # factor of three.
        #
        # The figure is measured, not guessed: across a normal week the
        # planned routes put five or six stops on a courier, and the
        # binding constraint is geography and manifest time rather than
        # the size of the van. Staffing to an optimistic figure produces a
        # roster that looks adequate and a network that defers a fifth of
        # its demand.
        stops_per_courier = 5

        # -- Size the roster **per zone** ----------------------------------- #
        # This is the difference between a roster that works and a roster
        # that looks like it works.
        #
        # Demand is not spread evenly across the city. On a normal day one
        # zone carries a third more orders than another, and on a
        # campaign day the skew is wider still. A roster that spreads its
        # couriers evenly across the zones therefore *starves* the busy
        # zones and *idles* the quiet ones: the busy zone's couriers are
        # sent out with four stops each while the quiet zone's couriers
        # sit at the depot with one.
        #
        # The tell is the deferral count. On the campaign day an evenly
        # spread roster of 149 couriers deferred a sixth of the day's
        # orders — not because there were not enough couriers on the road,
        # but because the wrong ones were in the wrong place.
        #
        # So each zone gets couriers in proportion to *its* demand, and
        # the waves are sized independently inside each zone.
        demand_by_zone: dict[str, dict[str, int]] = {}
        for order in day_wave_orders:
            demand_by_zone.setdefault(order.zone_id, {"day": 0, "evening": 0})["day"] += 1
        for order in evening_wave_orders:
            demand_by_zone.setdefault(order.zone_id, {"day": 0, "evening": 0})["evening"] += 1

        # Every zone gets a minimum of one courier per wave, so a zone with
        # no orders today still has somebody on the road for the orders
        # that arrive tomorrow.
        zone_roster: list[tuple[str, str, bool]] = []
        for zone_id in sorted(demand_by_zone):
            counts = demand_by_zone[zone_id]
            day_n = max(1, math.ceil(counts["day"] / stops_per_courier))
            evening_n = max(1, math.ceil(counts["evening"] / stops_per_courier))
            for _ in range(day_n):
                zone_roster.append((zone_id, "day", False))
            for _ in range(evening_n):
                zone_roster.append((zone_id, "evening", False))

        is_peak = day_index == peak_day_index
        if is_peak and zone_roster:
            # The campaign day adds surge capacity on top of both waves,
            # and it is priced at a premium.
            #
            # The surge is **additional couriers**, not a relabelling of
            # the ones already on the roster. A campaign day that triples
            # the demand needs a roster that triples with it; marking the
            # existing couriers as "surge" changes their cost but not
            # their capacity, and the campaign's orders still go out on
            # tomorrow's wave.
            #
            # The surge is spread across the zones in proportion to
            # *their* demand — a surge that all lands on one zone is a
            # surge that does not help the zone that is short — and split
            # between the waves in proportion to theirs.
            surge_needed = int(len(zone_roster) * (1 - vals.surge_hiring_share))
            day_slots = [r for r in zone_roster if r[1] == "day"]
            evening_slots = [r for r in zone_roster if r[1] == "evening"]
            day_surge = math.ceil(surge_needed * len(day_slots) / len(zone_roster))
            evening_surge = surge_needed - day_surge

            def _add_surge(
                slots: list[tuple[str, str, bool]], count: int, wave: str
            ) -> None:
                """Add surge couriers to the zones with the most demand.

                The zones are taken in descending order of demand, so the
                surge lands where the orders are rather than where the
                roster happens to be even.
                """

                by_zone: dict[str, int] = {}
                for zone_id, _, _ in slots:
                    by_zone[zone_id] = by_zone.get(zone_id, 0) + 1

                added = 0
                for zone_id, _ in sorted(by_zone.items(), key=lambda kv: (-kv[1], kv[0])):
                    if added >= count:
                        break
                    # One surge courier per baseline courier in the zone,
                    # up to the budget. The campaign roughly triples
                    # demand, so a 100% uplift in the busy zones is the
                    # smallest honest number.
                    take = min(count - added, by_zone[zone_id])
                    for _ in range(take):
                        slots.append((zone_id, wave, True))
                    added += take

            _add_surge(day_slots, day_surge, "day")
            _add_surge(evening_slots, evening_surge, "evening")
            zone_roster = day_slots + evening_slots

        # -- Build the roster ------------------------------------------------ #
        # The day wave takes the morning and early-afternoon orders; the
        # evening wave takes the rest. Splitting the roster rather than
        # making one shift longer is what keeps the promise on orders
        # placed late in the day.
        for zone_id, shift_wave, is_surge in zone_roster:
            courier_seq += 1
            hub_id = zone_hub.get(zone_id, _HUBS[0][0])
            hub_zones = tuple(z for z, h in zone_hub.items() if h == hub_id)
            # Mode mix: mostly bikes, some 3-wheelers, a few vans, a handful
            # of walking couriers for the dense core.
            roll = rng.random()
            if roll < 0.08:
                mode = VehicleMode.WALK
            elif roll < 0.66:
                mode = VehicleMode.BIKE
            elif roll < 0.90:
                mode = VehicleMode.THREE_WHEELER
            else:
                mode = VehicleMode.VAN

            courier = _make_courier(
                rng,
                f"cou-{courier_seq:04d}",
                mode,
                hub_id,
                hub_zones,
                day,
                vals,
                is_surge=is_surge,
                shift_wave=shift_wave,
            )
            world.couriers[courier.courier_id] = courier

    # -- Ground truth -------------------------------------------------------- #
    world.ground_truth = {
        "fraud_order_ids": sorted(fraud_planted),
        "sla_breach_order_ids": sorted(breach_planted),
        "cod_order_ids": sorted(cod_planted),
        "dim_weighted_parcel_ids": sorted(
            p.parcel_id for p in world.parcels.values() if p.is_dim_weighted
        ),
        "peak_day_index": peak_day_index,
        "start_day": start_day.isoformat(),
        "seed": cfg.seed,
    }
    return world


def corpus_summary(world: World) -> dict[str, Any]:
    """A summary of what the corpus contains, for the health endpoint."""
    orders = list(world.orders.values())
    shipments = list(world.shipments.values())
    cod = [o for o in orders if o.is_cod]
    tiers: dict[str, int] = {}
    for order in orders:
        tiers[order.address.tier] = tiers.get(order.address.tier, 0) + 1
    flagged = [o for o in orders if o.address.has_quality_flag]
    return {
        "orders": len(orders),
        "shipments": len(shipments),
        "parcels": len(world.parcels),
        "couriers": len(world.couriers),
        "addresses": len(world.addresses),
        "zones": len(world.zones),
        "hubs": len(world.hubs),
        "cod_orders": len(cod),
        "cod_share": round(len(cod) / len(orders), 4) if orders else 0.0,
        "flagged_address_orders": len(flagged),
        "orders_by_tier": tiers,
        "planted_fraud_orders": len(world.ground_truth.get("fraud_order_ids", [])),
        "planted_sla_breach_orders": len(world.ground_truth.get("sla_breach_order_ids", [])),
        "dim_weighted_parcels": len(world.ground_truth.get("dim_weighted_parcel_ids", [])),
        "now": world.now.isoformat(),
        "seed": world.ground_truth.get("seed"),
    }
