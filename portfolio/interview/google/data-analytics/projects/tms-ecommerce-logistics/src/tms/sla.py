"""SLA monitoring: detecting broken promises, and detecting them early.

**The interesting engineering is not detecting the breach — it is knowing
about it before it happens.** Every TMS can tell you after the fact that a
parcel was late. The useful version says "this parcel will be late unless
something changes, and here is what is causing it".

So this module produces two kinds of finding:

- **Confirmed breaches** — the parcel arrived, and it arrived late.
- **At-risk shipments** — the P90 forecast has already crossed the promise
  line, so the breach is *knowable* even though the parcel is still moving.

The at-risk list is the one worth putting on a dashboard, because it is
actionable: a parcel at risk can be re-sequenced, escalated, or given a
proactive customer call. A confirmed breach can only be apologised for.

Sub-parts
---------
- :func:`detect_breach` — classify a single shipment against its promise.
- :func:`scan_for_breaches` — sweep the world for confirmed breaches.
- :func:`scan_for_risk` — sweep for shipments that are heading for a breach.
- :func:`sla_summary` — the aggregate view.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .models import (
    BreachType,
    Order,
    OrderStatus,
    ServiceLevel,
    Shipment,
    SlaBreach,
    World,
)


@dataclass(frozen=True, slots=True)
class RiskFinding:
    """A shipment that is heading for a breach but has not breached yet."""

    shipment_id: str
    order_id: str
    promised_at: datetime
    forecast_eta: datetime
    slack_hours: float
    cause: str
    severity: str

    def as_dict(self) -> dict[str, Any]:
        """A JSON-friendly view."""
        return {
            "shipment_id": self.shipment_id,
            "order_id": self.order_id,
            "promised_at": self.promised_at.isoformat(),
            "forecast_eta": self.forecast_eta.isoformat(),
            "slack_hours": round(self.slack_hours, 2),
            "cause": self.cause,
            "severity": self.severity,
        }


# --------------------------------------------------------------------------- #
# Breach detection
# --------------------------------------------------------------------------- #


def detect_breach(
    shipment: Shipment,
    order: Order,
    now: datetime,
) -> SlaBreach | None:
    """Classify one shipment against its promise.

    Returns ``None`` when the shipment is within SLA.

    Three distinct failure modes, which matter because they have different
    fixes:

    - ``LATE_DELIVERY`` — delivered, but after the promise. The network
      worked but was too slow.
    - ``NOT_DELIVERED`` — failed and returned, or failed and still open
      past the promise. The network did not work.
    - ``DISPATCH_SLA_BREACH`` — the parcel never even left in time to make
      the promise. This one is a dispatch decision, not a delivery failure,
      and it is preventable.
    """

    promised = order.promised_at

    if shipment.status == OrderStatus.DELIVERED and shipment.delivered_at is not None:
        if shipment.delivered_at > promised:
            slack = (promised - shipment.delivered_at).total_seconds() / 3600.0
            return SlaBreach(
                breach_id=f"brk-{shipment.shipment_id}",
                order_id=order.order_id,
                shipment_id=shipment.shipment_id,
                breach_type=BreachType.LATE_DELIVERY,
                detected_at=shipment.delivered_at,
                promised_at=promised,
                service_level=order.service_level,
                forecast_eta=shipment.delivered_at,
                slack_hours=round(slack, 2),
            )
        return None

    if shipment.status == OrderStatus.RETURNED:
        return SlaBreach(
            breach_id=f"brk-{shipment.shipment_id}",
            order_id=order.order_id,
            shipment_id=shipment.shipment_id,
            breach_type=BreachType.NOT_DELIVERED,
            detected_at=now,
            promised_at=promised,
            service_level=order.service_level,
            slack_hours=round((promised - now).total_seconds() / 3600.0, 2),
        )

    # Still moving, but the promise has already passed.
    if now > promised and shipment.status not in (
        OrderStatus.DELIVERED,
        OrderStatus.RETURNED,
        OrderStatus.CANCELLED,
    ):
        return SlaBreach(
            breach_id=f"brk-{shipment.shipment_id}",
            order_id=order.order_id,
            shipment_id=shipment.shipment_id,
            breach_type=BreachType.NOT_DELIVERED,
            detected_at=promised,
            promised_at=promised,
            service_level=order.service_level,
            slack_hours=0.0,
        )

    return None


def scan_for_breaches(world: World, now: datetime | None = None) -> list[SlaBreach]:
    """Sweep every shipment for confirmed SLA breaches."""
    at = now or world.now
    breaches: list[SlaBreach] = []
    for shipment in world.shipments.values():
        order = world.orders.get(shipment.order_id)
        if order is None:
            continue
        breach = detect_breach(shipment, order, at)
        if breach is not None:
            breaches.append(breach)
    breaches.sort(key=lambda b: b.promised_at)
    return breaches


# --------------------------------------------------------------------------- #
# Early warning
# --------------------------------------------------------------------------- #


def _cause_for_risk(
    order: Order, shipment: Shipment, attempts_made: int, slack_hours: float
) -> str:
    """Work out *why* a shipment is at risk.

    A risk finding without a cause is an alert nobody acts on. The causes
    are distinguished because they have different responses:

    - A promise that was already impossible at allocation is a *planning*
      problem — the order was accepted with a window the network could not
      meet.
    - Many attempts means a *customer contact* problem — the parcel is
      fine, the customer is not reachable.
    - A COD order in a high-risk PIN code is a *fraud* problem.
    """

    if attempts_made >= 2:
        return "REPEATED_FAILED_ATTEMPTS"
    if order.is_cod and order.address.known_bad_pin:
        return "COD_IN_HIGH_RISK_AREA"
    if order.address.quality_score < 0.6:
        return "POOR_ADDRESS_QUALITY"
    if order.service_level == ServiceLevel.SAME_DAY and slack_hours < 4:
        return "TIGHT_SAME_DAY_WINDOW"
    if shipment.dispatched_at is not None and shipment.dispatched_at > order.promised_at:
        return "DISPATCHED_AFTER_PROMISE"
    return "CAPACITY_SHORTFALL"


def _severity_for(slack_hours: float) -> str:
    """Grade the severity of a risk finding."""
    if slack_hours <= -6:
        return "critical"
    if slack_hours <= 0:
        return "high"
    if slack_hours <= 6:
        return "medium"
    return "low"


def scan_for_risk(
    world: World,
    forecasts: dict[str, datetime],
    attempts_by_shipment: dict[str, int] | None = None,
    now: datetime | None = None,
) -> list[RiskFinding]:
    """Find shipments whose forecast ETA has already passed their promise.

    ``forecasts`` maps shipment id to the P90 forecast. Only shipments that
    are still moving are considered — a delivered parcel cannot be at risk.

    The finding is *early* by construction: the P90 is used, not the P50,
    so a shipment is flagged while there is still time to act.
    """

    at = now or world.now
    attempts_by_shipment = attempts_by_shipment or {}

    findings: list[RiskFinding] = []
    for shipment in world.shipments.values():
        if shipment.status in (
            OrderStatus.DELIVERED,
            OrderStatus.RETURNED,
            OrderStatus.CANCELLED,
        ):
            continue

        order = world.orders.get(shipment.order_id)
        if order is None:
            continue

        forecast = forecasts.get(shipment.shipment_id)
        if forecast is None:
            continue

        if forecast <= order.promised_at:
            continue

        slack = (order.promised_at - forecast).total_seconds() / 3600.0
        findings.append(
            RiskFinding(
                shipment_id=shipment.shipment_id,
                order_id=order.order_id,
                promised_at=order.promised_at,
                forecast_eta=forecast,
                slack_hours=round(slack, 2),
                cause=_cause_for_risk(
                    order, shipment, attempts_by_shipment.get(shipment.shipment_id, 0), slack
                ),
                severity=_severity_for(slack),
            )
        )

    findings.sort(key=lambda f: f.slack_hours)
    return findings


# --------------------------------------------------------------------------- #
# Summary
# --------------------------------------------------------------------------- #


def sla_summary(
    world: World, breaches: list[SlaBreach], at: datetime | None = None
) -> dict[str, Any]:
    """The aggregate SLA view: how well the network is keeping promises."""

    now = at or world.now
    by_type: dict[str, int] = {}
    by_level: dict[str, int] = {}
    for breach in breaches:
        by_type[breach.breach_type.value] = by_type.get(breach.breach_type.value, 0) + 1
        by_level[breach.service_level.value] = by_level.get(breach.service_level.value, 0) + 1

    # Denominator: shipments that were actually due by now.
    due = [
        s
        for s in world.shipments.values()
        if world.orders.get(s.order_id) is not None
        and world.orders[s.order_id].promised_at <= now
    ]
    delivered_on_time = sum(
        1
        for s in due
        if s.status == OrderStatus.DELIVERED
        and s.delivered_at is not None
        and s.delivered_at <= world.orders[s.order_id].promised_at
    )

    otd = delivered_on_time / len(due) if due else 0.0

    return {
        "as_of": now.isoformat(),
        "shipments_due": len(due),
        "delivered_on_time": delivered_on_time,
        "on_time_delivery_rate": round(otd, 4),
        "breaches_total": len(breaches),
        "breaches_by_type": by_type,
        "breaches_by_service_level": by_level,
    }


def breach_detail(breach: SlaBreach) -> dict[str, Any]:
    """A JSON-friendly breach record."""
    return {
        "breach_id": breach.breach_id,
        "order_id": breach.order_id,
        "shipment_id": breach.shipment_id,
        "breach_type": breach.breach_type.value,
        "detected_at": breach.detected_at.isoformat(),
        "promised_at": breach.promised_at.isoformat(),
        "service_level": breach.service_level.value,
        "forecast_eta": breach.forecast_eta.isoformat() if breach.forecast_eta else None,
        "slack_hours": breach.slack_hours,
    }
