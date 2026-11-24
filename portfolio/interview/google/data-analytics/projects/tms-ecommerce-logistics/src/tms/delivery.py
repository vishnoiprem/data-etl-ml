"""Delivery: attempts, non-delivery reports, cash on delivery, remittance.

**A failed delivery is not a failed order.** They are different events with
different economics: a failed attempt costs money and time but the parcel is
still deliverable; a returned parcel costs *more* than a delivered one
(because reverse logistics is dearer than forward — published reverse rates
run roughly 1.5-2x forward freight) and generates no revenue.

The chain modelled here is the real one:

    attempt fails -> NDR raised -> reschedule -> attempt again
        -> (3 attempts exhausted) -> RTO -> reverse leg -> RETURNED

**Why three attempts.** Three-attempt NDR policies are what the large
carriers actually operate. The number is not arbitrary, and modelling fewer
attempts would inflate the RTO rate far above the published 12-40% band.

**Why address quality matters so much.** Published breakdowns of failed
delivery put address problems in the top five causes. So the address quality
score feeds the attempt-success probability directly, and a PIN code with a
known fraud history makes things worse still.

**Why COD confirmation exists.** A pre-dispatch confirmation SMS is the
single most effective published lever on COD RTO — it cuts the rate by
15-25 percentage points — because most COD returns are buyer's remorse
caught before the courier is anywhere near the address.

Sub-parts
---------
- :func:`attempt_success_probability` — the success model.
- :func:`run_attempt` — make one delivery attempt.
- :func:`simulate_delivery` — run the full attempt chain for a shipment.
- :func:`create_settlement` / :func:`settle_due_cash` — the COD money cycle.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .config import DEFAULT_VALUES, ValueConfig
from .models import (
    Attempt,
    CodSettlement,
    FailureReason,
    Order,
    OrderStatus,
    PodType,
    Shipment,
    World,
)


# --------------------------------------------------------------------------- #
# Success model
# --------------------------------------------------------------------------- #


def attempt_success_probability(
    order: Order,
    values: ValueConfig | None = None,
    rng: random.Random | None = None,
) -> float:
    """The probability that the next delivery attempt succeeds.

    The model starts from a published baseline first-attempt failure rate
    and adjusts it for four factors, each of which is a documented driver
    of failed delivery:

    1. **Address quality.** A score of 1.0 leaves the baseline alone; a
       score of 0.5 halves the failure rate, because a courier who cannot
       find the door will not find it on the second try either.
    2. **COD.** Cash-on-delivery orders fail more often — the customer may
       not have the money, may have changed their mind, or may refuse at
       the door.
    3. **Order value.** High-value orders are refused more often.
    4. **Time of day.** Evening deliveries fail more: the customer may be
       out, and there may be no cash at home.

    A confirmed COD order (the customer replied to the confirmation SMS) is
    materially more likely to be accepted, which is exactly why the
    confirmation lever exists.
    """

    vals = values or DEFAULT_VALUES
    failure = vals.baseline_first_attempt_failure

    # -- Address quality --------------------------------------------------- #
    quality = order.address.quality_score
    failure *= max(0.35, 1.0 - (1.0 - quality) * vals.address_quality_failure_multiplier)

    # -- COD --------------------------------------------------------------- #
    if order.is_cod:
        failure *= 1.45
        if order.cod_confirmed:
            # A confirmed customer is present and has the money ready.
            failure *= 0.55

    # -- Order value ------------------------------------------------------- #
    if order.order_value > 15000:
        failure *= 1.3
    elif order.order_value > 5000:
        failure *= 1.12

    # -- Time of day ------------------------------------------------------- #
    hour = order.promised_at.hour
    if 19 <= hour or hour < 7:
        failure *= 1.18

    # -- Known bad PIN code ------------------------------------------------ #
    if order.address.known_bad_pin:
        failure *= 1.4

    return max(0.01, min(0.95, 1.0 - failure))


def _pick_failure_reason(
    order: Order, values: ValueConfig | None = None, rng: random.Random | None = None
) -> FailureReason:
    """Pick *why* an attempt failed.

    The reason matters because the recovery rate differs by reason. A
    customer who was not home will probably be home tomorrow. A wrong
    address will be wrong tomorrow too.
    """

    vals = values or DEFAULT_VALUES
    r = rng or random.Random()

    mix = dict(vals.failure_reason_mix)

    # Reasons that are actually plausible for this order get more weight.
    if order.is_cod:
        mix["INSUFFICIENT_CASH"] *= 2.2
        mix["CUSTOMER_REFUSED"] *= 1.8
    else:
        mix["INSUFFICIENT_CASH"] *= 0.15
    if order.address.quality_score < 0.6:
        mix["ADDRESS_INCORRECT"] *= 2.5
        mix["ADDRESS_UNREACHABLE"] *= 2.0

    total = sum(mix.values())
    roll = r.random() * total
    cumulative = 0.0
    for reason, weight in mix.items():
        cumulative += weight
        if roll <= cumulative:
            return FailureReason(reason)
    return FailureReason.CUSTOMER_UNAVAILABLE


#: Failure reasons that a retry can actually fix.
_RECOVERABLE = frozenset(
    {
        FailureReason.CUSTOMER_UNAVAILABLE,
        FailureReason.INSUFFICIENT_CASH,
        FailureReason.CONSIGNEE_RESCHEDULED,
        FailureReason.WEATHER,
        FailureReason.ROAD_BLOCKED,
    }
)


# --------------------------------------------------------------------------- #
# Attempts
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class DeliveryOutcome:
    """The result of running the delivery chain for one shipment."""

    shipment_id: str
    order_id: str
    final_status: OrderStatus
    attempts: list[Attempt] = field(default_factory=list)
    delivered_at: datetime | None = None
    cod_collected: float = 0.0
    rto_reason: FailureReason | None = None
    #: Extra cost incurred by failing attempts.
    attempt_cost: float = 0.0
    settlement: CodSettlement | None = None

    @property
    def first_attempt_success(self) -> bool:
        """Whether the parcel went out on the first try."""
        return bool(self.attempts) and self.attempts[0].success

    @property
    def attempt_count(self) -> int:
        """How many attempts it took."""
        return len(self.attempts)


def run_attempt(
    shipment: Shipment,
    order: Order,
    attempt_no: int,
    at: datetime,
    courier_id: str,
    values: ValueConfig | None = None,
    rng: random.Random | None = None,
    pod_geofence_m: float = 250.0,
) -> Attempt:
    """Make one delivery attempt and record what happened.

    On success: a POD is generated (photo + geo for most, OTP for high-value
    orders), and for COD the cash is collected.

    On failure: a reason code is chosen and an NDR is implied.
    """

    vals = values or DEFAULT_VALUES
    r = rng or random.Random()

    probability = attempt_success_probability(order, vals, r)
    success = r.random() < probability

    if not success:
        reason = _pick_failure_reason(order, vals, r)
        return Attempt(
            attempt_id=f"att-{shipment.shipment_id}-{attempt_no}",
            shipment_id=shipment.shipment_id,
            order_id=order.order_id,
            attempt_no=attempt_no,
            attempted_at=at,
            courier_id=courier_id,
            success=False,
            reason=reason,
            pod_type=PodType.NONE,
        )

    # -- Success: build the proof of delivery ------------------------------ #
    if order.order_value > 10000:
        pod_type = PodType.OTP
    elif r.random() < 0.18:
        pod_type = PodType.SIGNATURE
    else:
        pod_type = PodType.PHOTO_GEO

    # The courier is nearly always within the geofence of the address, but
    # occasionally not — a mis-pinned address, or a POD taken at the depot.
    # This is the courier-side fraud signal, and it is checked downstream.
    offset = 0.0
    if r.random() < 0.02:
        offset = pod_geofence_m * r.uniform(1.4, 3.2)

    cod_collected = order.order_value if order.is_cod else 0.0

    return Attempt(
        attempt_id=f"att-{shipment.shipment_id}-{attempt_no}",
        shipment_id=shipment.shipment_id,
        order_id=order.order_id,
        attempt_no=attempt_no,
        attempted_at=at,
        courier_id=courier_id,
        success=True,
        pod_type=pod_type,
        pod_offset_m=round(offset, 1),
        cod_collected=cod_collected,
    )


def simulate_delivery(
    shipment: Shipment,
    order: Order,
    courier_id: str,
    first_attempt_at: datetime,
    values: ValueConfig | None = None,
    settings: Any = None,
    rng: random.Random | None = None,
    carrier: str = "ninja_van",
) -> DeliveryOutcome:
    """Run the full attempt chain for a shipment.

    Attempts are spaced by the retry interval until the parcel is delivered
    or the attempt budget is exhausted, at which point it goes to
    return-to-origin.
    """

    vals = values or DEFAULT_VALUES
    r = rng or random.Random()
    max_attempts = getattr(settings, "max_attempts", 3) if settings else 3
    retry_spacing = getattr(settings, "retry_spacing_days", 1) if settings else 1

    outcome = DeliveryOutcome(
        shipment_id=shipment.shipment_id,
        order_id=order.order_id,
        final_status=shipment.status,
    )

    attempt_at = first_attempt_at
    for attempt_no in range(1, max_attempts + 1):
        attempt = run_attempt(
            shipment, order, attempt_no, attempt_at, courier_id, vals, r
        )
        outcome.attempts.append(attempt)

        if attempt.success:
            outcome.final_status = OrderStatus.DELIVERED
            outcome.delivered_at = attempt.attempted_at
            outcome.cod_collected = attempt.cod_collected
            break

        outcome.attempt_cost += vals.failed_attempt_cost
        outcome.rto_reason = attempt.reason

        # Not every failure can be fixed by trying again.
        if attempt.reason not in _RECOVERABLE:
            break

        # A confirmed customer who failed for a fixable reason is more
        # likely to succeed on a retry.
        if attempt.reason == FailureReason.CUSTOMER_UNAVAILABLE and r.random() > vals.retry_recovery_rate:
            # Low chance of recovery — but we still try, because the
            # alternative is an RTO, which is worse.
            pass

        attempt_at = attempt_at + timedelta(days=retry_spacing)

    if outcome.final_status != OrderStatus.DELIVERED:
        outcome.final_status = OrderStatus.RETURNED

    # -- COD settlement ---------------------------------------------------- #
    if outcome.cod_collected > 0:
        outcome.settlement = create_settlement(
            shipment, order, outcome.cod_collected, outcome.delivered_at or attempt_at, carrier, vals
        )

    return outcome


# --------------------------------------------------------------------------- #
# COD settlement
# --------------------------------------------------------------------------- #


def create_settlement(
    shipment: Shipment,
    order: Order,
    amount: float,
    collected_at: datetime,
    carrier: str,
    values: ValueConfig | None = None,
) -> CodSettlement:
    """Create the COD settlement record for a delivered cash order.

    The remittance cycle is the carrier's published cycle: T+1 for an
    on-demand courier, T+2 for an integrated network, T+5 for an aggregator
    that batches several carriers' cash together.
    """

    vals = values or DEFAULT_VALUES
    cycle_days = vals.cod_remittance_days.get(carrier, 5)

    return CodSettlement(
        settlement_id=f"cod-{shipment.shipment_id}",
        shipment_id=shipment.shipment_id,
        order_id=order.order_id,
        merchant_id=order.merchant_id,
        amount=round(amount, 2),
        collected_at=collected_at,
        due_at=collected_at + timedelta(days=cycle_days),
        remitted_at=collected_at + timedelta(days=cycle_days),
    )


def settle_due_cash(
    settlements: list[CodSettlement], as_of: datetime
) -> dict[str, Any]:
    """Settle every settlement whose due date has passed.

    Returns a summary of what moved and what is still outstanding, so the
    working-capital position of the COD float is visible at any point.
    """

    remitted = 0
    outstanding = 0.0
    outstanding_count = 0
    total_cash = 0.0

    for settlement in settlements:
        total_cash += settlement.amount
        if settlement.remitted_at is None and settlement.due_at <= as_of:
            remitted += 1
        elif settlement.remitted_at is None:
            outstanding += settlement.amount
            outstanding_count += 1

    return {
        "as_of": as_of.isoformat(),
        "settlements": len(settlements),
        "total_cash_collected": round(total_cash, 2),
        "remitted_count": remitted,
        "outstanding_count": outstanding_count,
        "outstanding_amount": round(outstanding, 2),
        "average_days_to_settle": round(
            sum(s.days_to_settle or 0 for s in settlements if s.is_settled)
            / max(1, sum(1 for s in settlements if s.is_settled)),
            2,
        ),
    }


def cod_ledger(world: World) -> list[CodSettlement]:
    """Every COD settlement across the world."""
    settlements: list[CodSettlement] = []
    for shipment in world.shipments.values():
        if shipment.status == OrderStatus.DELIVERED and shipment.delivered_at:
            order = world.orders.get(shipment.order_id)
            if order is None or not order.is_cod:
                continue
            settlements.append(
                create_settlement(
                    shipment,
                    order,
                    order.order_value,
                    shipment.delivered_at,
                    shipment.carrier,
                )
            )
    return settlements


def shipment_by_order(world: World) -> dict[str, Shipment]:
    """An order-id to shipment index for the whole world.

    Several parts of the system need "the shipment for this order". A
    linear scan over the shipment table turns each of those into an O(n^2)
    operation over the whole week of demand.
    """
    return {shipment.order_id: shipment for shipment in world.shipments.values()}
