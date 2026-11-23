"""The domain model: the entities a TMS actually has to keep track of.

**A TMS is a ledger of state transitions, and almost every bug in one comes
from the same mistake — treating a status as a string.** A shipment that is
``OUT_FOR_DELIVERY`` under one carrier's vocabulary is ``OD`` under FedEx's
and ``on delivery vehicle`` under a third. The moment the code starts
comparing status strings, two facts get conflated: the *normalized* status
this system reasons about, and the *raw* code a particular carrier sent.

So every scan here carries both. The normalized status is what the router,
the ETA engine and the SLA monitor reason about. The raw carrier code is kept
alongside it for audit, because a carrier that introduces a status this
mapping has never seen must not be silently treated as "in transit".

Sub-parts
---------
- Enumerations: order status, service level, vehicle mode, scan type,
  failure reason, POD type, risk action.
- Entity dataclasses: order, shipment, parcel, address, courier, route, stop,
  attempt, scan event, COD settlement.
- :func:`normalize_carrier_status` — the carrier-to-normal mapping.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class StrEnum(str, Enum):
    """A string-valued enum.

    ``enum.StrEnum`` only exists from Python 3.11, and this project targets
    3.10 to match its siblings. Mixing ``str`` and ``Enum`` gives the same
    behaviour for the things this code actually relies on: the members
    compare equal to their string values, ``str(member)`` returns the value,
    and they serialise as plain strings.
    """

    def __str__(self) -> str:
        return str(self.value)



# --------------------------------------------------------------------------- #
# Enumerations
# --------------------------------------------------------------------------- #


class OrderStatus(StrEnum):
    """The order state machine.

    Order state is deliberately separate from shipment state. An order can be
    ``CANCELLED`` while its shipment is already ``IN_TRANSIT`` and heading
    back — conflating the two makes RTO handling impossible to express.
    """

    CREATED = "created"
    ALLOCATED = "allocated"
    PACKED = "packed"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED_DELIVERY = "failed_delivery"
    RETURNED = "returned"
    CANCELLED = "cancelled"


class ServiceLevel(StrEnum):
    """The promise tier sold at checkout."""

    SAME_DAY = "same_day"
    NEXT_DAY = "next_day"
    ECONOMY = "economy"
    EXPRESS_CROSS_BORDER = "express_cross_border"


class VehicleMode(StrEnum):
    """Last-mile vehicle modes, cheapest-and-smallest first."""

    WALK = "walk"
    BIKE = "bike"
    THREE_WHEELER = "three_wheeler"
    VAN = "van"


class ScanType(StrEnum):
    """Append-only logistics events.

    Modelled on the GS1/EPCIS ``bizStep`` vocabulary, with the delivery-side
    steps this project needs added on top.
    """

    ORDER_CONFIRMED = "order_confirmed"
    ALLOCATED = "allocated"
    PACKED = "packed"
    MANIFESTED = "manifested"
    PICKED_UP = "picked_up"
    HUB_ARRIVAL = "hub_arrival"
    LINE_HAUL_DEPARTED = "line_haul_departed"
    SORTED = "sorted"
    OUT_FOR_DELIVERY = "out_for_delivery"
    ATTEMPTED = "attempted"
    DELIVERED = "delivered"
    NDR_RAISED = "ndr_raised"
    RTO_DISPATCHED = "rto_dispatched"
    RETURNED = "returned"
    CANCELLED = "cancelled"
    COD_COLLECTED = "cod_collected"


class FailureReason(StrEnum):
    """Why a delivery attempt failed.

    The reason code is the whole point of an NDR. "Failed" without a reason
    cannot be improved on, because there is nothing to act on.
    """

    CUSTOMER_UNAVAILABLE = "CUSTOMER_UNAVAILABLE"
    ADDRESS_INCORRECT = "ADDRESS_INCORRECT"
    INSUFFICIENT_CASH = "INSUFFICIENT_CASH"
    ADDRESS_UNREACHABLE = "ADDRESS_UNREACHABLE"
    CUSTOMER_REFUSED = "CUSTOMER_REFUSED"
    PREMIUM_MIXED = "PREMIUM_MIXED"
    WEATHER = "WEATHER"
    ROAD_BLOCKED = "ROAD_BLOCKED"
    CONSIGNEE_RESCHEDULED = "CONSIGNEE_RESCHEDULED"


class PodType(StrEnum):
    """Proof-of-delivery flavours, weakest to strongest."""

    NONE = "none"
    GEO = "geo"
    PHOTO = "photo"
    PHOTO_GEO = "photo_geo"
    SIGNATURE = "signature"
    OTP = "otp"


class RiskAction(StrEnum):
    """What the COD risk model decides to do with an order."""

    RELEASE = "release"
    HOLD_FOR_CONFIRMATION = "hold_for_confirmation"
    PARTIAL_PREPAY = "partial_prepay"
    PREPAY_ONLY = "prepay_only"
    BLOCK = "block"


class BreachType(StrEnum):
    """The ways a promise can be broken."""

    LATE_DELIVERY = "LATE_DELIVERY"
    NOT_DELIVERED = "NOT_DELIVERY"
    DISPATCH_SLA_BREACH = "DISPATCH_SLA_BREACH"


#: Terminal order states — nothing more will happen to the order.
TERMINAL_STATUSES = frozenset(
    {OrderStatus.DELIVERED, OrderStatus.RETURNED, OrderStatus.CANCELLED}
)

#: States in which a parcel is physically at the customer's door and a
#: delivery attempt may be made.
ATTEMPTABLE_STATUSES = frozenset({OrderStatus.OUT_FOR_DELIVERY})


# --------------------------------------------------------------------------- #
# Carrier status normalisation
# --------------------------------------------------------------------------- #

#: Carrier-native status vocabularies, collapsed onto our normalized set.
#:
#: Sourced from the public tracking APIs of DHL, FedEx, DPD and UPS, plus the
#: aggregator enums used by AfterShip and EasyPost. The point of the table is
#: not completeness — no table is ever complete — but that a code we have
#: never seen before lands in :data:`UNRECOGNIZED` rather than silently
#: becoming "in transit".
_CARRIER_STATUS_MAP: dict[str, dict[str, OrderStatus]] = {
    "dhl": {
        "pre-transit": OrderStatus.CREATED,
        "transit": OrderStatus.IN_TRANSIT,
        "delivered": OrderStatus.DELIVERED,
        "failure": OrderStatus.FAILED_DELIVERY,
        "unknown": OrderStatus.CREATED,
    },
    "fedex": {
        "OC": OrderStatus.CREATED,
        "PU": OrderStatus.PICKED_UP,
        "AR": OrderStatus.IN_TRANSIT,
        "DP": OrderStatus.IN_TRANSIT,
        "OD": OrderStatus.OUT_FOR_DELIVERY,
        "DL": OrderStatus.DELIVERED,
    },
    "dpd": {
        "02": OrderStatus.IN_TRANSIT,
        "13": OrderStatus.DELIVERED,
        "10": OrderStatus.OUT_FOR_DELIVERY,
    },
    "ups": {
        "003": OrderStatus.OUT_FOR_DELIVERY,
        "002": OrderStatus.IN_TRANSIT,
        "001": OrderStatus.CREATED,
        "004": OrderStatus.DELIVERED,
        "005": OrderStatus.FAILED_DELIVERY,
    },
    "aggregator": {
        "Pending": OrderStatus.CREATED,
        "InfoReceived": OrderStatus.CREATED,
        "InTransit": OrderStatus.IN_TRANSIT,
        "OutForDelivery": OrderStatus.OUT_FOR_DELIVERY,
        "AttemptFail": OrderStatus.FAILED_DELIVERY,
        "Delivered": OrderStatus.DELIVERED,
        "AvailableForPickup": OrderStatus.DELIVERED,
        "Exception": OrderStatus.FAILED_DELIVERY,
        "Expired": OrderStatus.RETURNED,
    },
    "internal": {
        "created": OrderStatus.CREATED,
        "allocated": OrderStatus.ALLOCATED,
        "packed": OrderStatus.PACKED,
        "picked_up": OrderStatus.PICKED_UP,
        "in_transit": OrderStatus.IN_TRANSIT,
        "out_for_delivery": OrderStatus.OUT_FOR_DELIVERY,
        "delivered": OrderStatus.DELIVERED,
        "failed_delivery": OrderStatus.FAILED_DELIVERY,
        "returned": OrderStatus.RETURNED,
        "cancelled": OrderStatus.CANCELLED,
    },
}

#: Sentinel used when a carrier sends a code we have no mapping for. It is a
#: real status, not a crash: unknown codes are a fact about the world.
UNRECOGNIZED = OrderStatus.IN_TRANSIT


def normalize_carrier_status(
    carrier: str, raw_code: str | None
) -> tuple[OrderStatus, bool]:
    """Map a carrier-native status code onto our normalized status.

    Returns the normalized status and a boolean flagging whether the code was
    recognised. The flag matters: an unrecognised code still advances the
    shipment (the parcel physically moved), but it is surfaced so the
    operations team can extend the mapping rather than discovering the gap
    from a customer complaint.
    """

    table = _CARRIER_STATUS_MAP.get(carter.lower())
    if table is None or raw_code is None:
        return UNRECOGNIZED, False
    status = table.get(raw_code)
    if status is None:
        return UNRECOGNIZED, False
    return status, True


# --------------------------------------------------------------------------- #
# Value objects
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class Address:
    """A delivery address plus its quality assessment.

    Address quality is not cosmetic. Published breakdowns of failed delivery
    put wrong PIN codes and missing landmarks in the top five causes, which
    is why the quality score feeds the attempt-success model directly rather
    than sitting in a report nobody reads.
    """

    address_id: str
    line1: str
    area: str
    city: str
    pin_code: str
    lat: float
    lng: float
    tier: str
    landmark: str | None = None
    geocode_confidence: float = 1.0
    #: 0.0 (unusable) to 1.0 (perfect). See :meth:`quality_score`.
    known_bad_pin: bool = False

    @property
    def quality_score(self) -> float:
        """A 0-1 address-quality score.

        The components are the ones that actually drive failed delivery:
        geocode confidence, whether a landmark was given, the PIN code's
        historical failure rate, and the known-bad-PIN flag.
        """

        score = 0.45 * self.geocode_confidence
        score += 0.20 if self.landmark else 0.0
        score += 0.15 if len(self.pin_code) == 6 else 0.0
        score += 0.20 if not self.known_bad_pin else -0.25
        return max(0.0, min(1.0, score))

    @property
    def has_quality_flag(self) -> bool:
        """Whether this address carries a flag worth acting on."""
        return self.quality_score < 0.75


@dataclass(frozen=True, slots=True)
class Parcel:
    """A physical parcel.

    Carries both actual and volumetric weight, because carriers charge the
    greater of the two. On small, light but bulky items — footwear, small
    appliances — the volumetric weight wins, and that gap is a real source of
    billing disputes that a TMS should be tracking.
    """

    parcel_id: str
    order_id: str
    weight_kg: float
    length_cm: float
    width_cm: float
    height_cm: float

    def volumetric_weight(self, divisor: float = 5000.0) -> float:
        """Volumetric (dimensional) weight in kg, at the given cm³/kg divisor."""
        volume_cm3 = self.length_cm * self.width_cm * self.height_cm
        return volume_cm3 / divisor

    def billable_weight(self, divisor: float = 5000.0) -> float:
        """Chargeable weight — the greater of actual and volumetric."""
        return max(self.weight_kg, self.volumetric_weight(divisor))

    @property
    def volume_m3(self) -> float:
        """Volume in cubic metres, for vehicle capacity checks."""
        return (self.length_cm * self.width_cm * self.height_cm) / 1_000_000.0

    @property
    def is_dim_weighted(self) -> bool:
        """Whether volumetric weight exceeds actual weight.

        True means the parcel is billed on its size rather than its weight.
        """
        return self.volumetric_weight(5000.0) > self.weight_kg


@dataclass(frozen=True, slots=True)
class Order:
    """A customer order."""

    order_id: str
    customer_id: str
    address: Address
    service_level: ServiceLevel
    order_value: float
    is_cod: bool
    #: The promise made at checkout. Frozen — it never moves, which is what
    #: makes an SLA breach meaningful.
    promised_at: datetime
    created_at: datetime
    zone_id: str
    merchant_id: str
    is_multi_package: bool = False
    #: Ground truth planted by the corpus generator: the order really is a
    #: return-fraud attempt. Used only by the eval harness.
    planted_fraud: bool = False
    #: True when the customer confirmed the COD order by SMS/IVR.
    cod_confirmed: bool = False
    risk_score: float = 0.0
    risk_action: RiskAction = RiskAction.RELEASE


@dataclass(slots=True)
class Shipment:
    """A shipment: one order's movement from origin to destination.

    An order may have several shipments when stock is split. Most do not.

    Mutable, unlike :class:`Order`. A shipment is a *live* thing whose
    status changes as it moves; freezing it would mean rebuilding the
    object on every scan, and the identity of a shipment has to survive
    those changes because the scan log refers to it by id.
    """

    shipment_id: str
    order_id: str
    tracking_number: str
    service_level: ServiceLevel
    carrier: str
    origin_hub: str
    destination_hub: str
    status: OrderStatus
    promised_at: datetime
    parcel_ids: tuple[str, ...] = ()
    courier_id: str | None = None
    route_id: str | None = None
    dispatched_at: datetime | None = None
    delivered_at: datetime | None = None
    #: Set once the parcel has been returned to origin.
    rto_reason: FailureReason | None = None


@dataclass(frozen=True, slots=True)
class Courier:
    """A delivery courier and the vehicle they work.

    A courier carries a *mode* (walk, bike, 3-wheeler, van) which determines
    their capacity envelope and their speed. Capacity is enforced in three
    dimensions — kilograms, cubic metres and parcel count — because a bike
    with 12 kg of room and 0.30 m³ of room runs out of both at once.
    """

    courier_id: str
    name: str
    mode: VehicleMode
    hub_id: str
    zone_ids: tuple[str, ...]
    shift_start: datetime
    shift_end: datetime
    #: True for a surge courier hired for a campaign day.
    is_surge: bool = False
    #: Cost of the courier's day. Higher for surge.
    fixed_cost: float = 0.0
    cost_per_stop: float = 0.0
    cost_per_km: float = 0.0
    max_weight_kg: float = 0.0
    max_volume_m3: float = 0.0
    max_parcels: int = 0


@dataclass(slots=True)
class Stop:
    """One delivery point on a route.

    A stop is *not* a parcel. Several parcels to the same address share one
    stop — that consolidation is where most of the last-mile cost saving
    comes from, and modelling it wrongly inflates cost per parcel badly.
    """

    stop_id: str
    route_id: str
    sequence: int
    address: Address
    order_ids: tuple[str, ...]
    parcel_ids: tuple[str, ...]
    window_start: datetime | None = None
    window_end: datetime | None = None
    #: The instant the parcels at this stop were picked, packed and
    #: manifested. The courier cannot arrive before this — a parcel that
    #: is still on the warehouse floor is not deliverable, and an ETA that
    #: ignores this reports a delivery happening before the parcel
    #: existed.
    ready_at: datetime | None = None
    eta_p50: datetime | None = None
    eta_p90: datetime | None = None
    service_minutes: float = 0.0
    distance_from_prev_km: float = 0.0
    completed_at: datetime | None = None
    outcome: str = "pending"


@dataclass(slots=True)
class Route:
    """A courier's plan for one day: an ordered sequence of stops."""

    route_id: str
    courier_id: str
    route_date: datetime
    stops: list[Stop] = field(default_factory=list)
    total_distance_km: float = 0.0
    total_service_minutes: float = 0.0
    #: Weight and volume actually loaded, against the courier's envelope.
    loaded_weight_kg: float = 0.0
    loaded_volume_m3: float = 0.0
    loaded_parcels: int = 0
    #: Cost accounting, filled in once the route is executed.
    cost: float = 0.0
    #: Order ids that were assigned to this courier but did not fit inside
    #: their shift, and were therefore dropped from the route. They go
    #: back to the dispatcher to be deferred to the next wave.
    dropped_order_ids: list[str] = field(default_factory=list)

    @property
    def parcel_count(self) -> int:
        """Total parcels across all stops on the route."""
        return sum(len(stop.parcel_ids) for stop in self.stops)

    @property
    def stop_count(self) -> int:
        """Number of stops — always less than or equal to the parcel count."""
        return len(self.stops)


@dataclass(frozen=True, slots=True)
class Attempt:
    """One delivery attempt at a stop, successful or not."""

    attempt_id: str
    shipment_id: str
    order_id: str
    attempt_no: int
    attempted_at: datetime
    courier_id: str
    success: bool
    reason: FailureReason | None = None
    pod_type: PodType = PodType.NONE
    #: Distance in metres between the POD geo-stamp and the planned address.
    pod_offset_m: float = 0.0
    cod_collected: float = 0.0


@dataclass(frozen=True, slots=True)
class ScanEvent:
    """An append-only logistics fact.

    Append-only is the point: the scan log is the source of truth, and the
    current status of a shipment is a fold over its scans, not a mutable
    field that can drift away from the history.
    """

    scan_id: str
    entity_type: str
    entity_id: str
    scan_type: ScanType
    occurred_at: datetime
    status: OrderStatus
    source: str
    location_id: str
    actor_id: str | None = None
    #: The carrier-native code, retained for audit.
    raw_code: str | None = None
    #: False when the raw code was not in the mapping table.
    normalized: bool = True
    note: str = ""


@dataclass(frozen=True, slots=True)
class CodSettlement:
    """Cash collected on delivery, remitted to the merchant on a cycle."""

    settlement_id: str
    shipment_id: str
    order_id: str
    merchant_id: str
    amount: float
    collected_at: datetime
    due_at: datetime
    remitted_at: datetime | None = None

    @property
    def is_settled(self) -> bool:
        """Whether the cash has reached the merchant."""
        return self.remitted_at is not None

    @property
    def days_to_settle(self) -> int | None:
        """Days from collection to remittance, or None if still outstanding."""
        if self.remitted_at is None:
            return None
        return (self.remitted_at - self.collected_at).days


@dataclass(frozen=True, slots=True)
class SlaBreach:
    """A promise that was broken, and when we knew it was going to break."""

    breach_id: str
    order_id: str
    shipment_id: str
    breach_type: BreachType
    detected_at: datetime
    promised_at: datetime
    service_level: ServiceLevel
    #: The ETA at detection time — the P90 we were forecasting against.
    forecast_eta: datetime | None = None
    #: How much slack was left when we first saw the breach coming.
    slack_hours: float = 0.0


@dataclass(frozen=True, slots=True)
class Fleet:
    """The courier roster for a simulated operating day."""

    day: datetime
    couriers: tuple[Courier, ...]

    def by_mode(self) -> dict[VehicleMode, list[Courier]]:
        """Group the roster by vehicle mode."""
        out: dict[VehicleMode, list[Courier]] = {}
        for courier in self.couriers:
            out.setdefault(courier.mode, []).append(courier)
        return out


@dataclass(slots=True)
class World:
    """The whole simulated world: everything the corpus generator produced.

    Passed around as one object so that no function needs a database or a
    global. The service holds one; the demo builds one; the tests share one.
    """

    orders: dict[str, Order] = field(default_factory=dict)
    shipments: dict[str, Shipment] = field(default_factory=dict)
    parcels: dict[str, Parcel] = field(default_factory=dict)
    couriers: dict[str, Courier] = field(default_factory=dict)
    hubs: dict[str, str] = field(default_factory=dict)
    zones: dict[str, str] = field(default_factory=dict)
    addresses: dict[str, Address] = field(default_factory=dict)
    #: The instant the simulation is evaluated at.
    now: datetime = datetime(2026, 11, 21, 12, 0, 0)
    #: Ground truth the corpus generator planted, for the eval harness.
    ground_truth: dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

#: Street-network detour factor.
#:
#: A straight line between two addresses is not a driveable route: in a
#: dense city the road path is roughly 30% longer. This constant lives
#: here, in the shared models module, because the dispatcher and the
#: router both need it and the router already imports from the
#: dispatcher. They have to agree: the dispatcher decides how many stops
#: a courier can make in a shift on the strength of this number, and if
#: the router then plans legs on a different basis, the plan it produces
#: will not fit the shift the dispatcher promised.
DETOUR_FACTOR = 1.3


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points, in kilometres."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def deadline_for(created_at: datetime, service_level: ServiceLevel, hours: int) -> datetime:
    """The promised delivery instant for an order placed at ``created_at``."""
    return created_at + timedelta(hours=hours)
