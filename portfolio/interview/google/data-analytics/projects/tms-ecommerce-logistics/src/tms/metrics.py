"""The KPI and cost model: what the network actually delivered, and at what cost.

**This is the module a data analyst actually spends their day in.** Every
other module in this project produces events; this one turns them into the
numbers a logistics scorecard is built from, and it is honest about the
denominators — because a percentage without a denominator is a number
anybody can make mean whatever they want.

The KPI set follows the published benchmark structure:

| KPI | Published benchmark |
|---|---|
| On-time delivery | 92-95%, stretch 97%+ |
| First-attempt delivery success | 78-88%, stretch 90%+ |
| RTO rate | 12-18%, stretch under 10% |
| Damage/loss | 0.3-1.0% |
| Attempts per delivery | 1.15-1.35 |
| Order density | 25-45 parcels per bike route |
| COD remittance | T+1 to T+7 |
| Cost per parcel | mode-dependent |

**The cost model separates the three cost drivers** — the courier's day, the
stops they made, and the distance they drove — because they behave
differently under volume changes, and a TMS that reports one blended number
cannot tell an operator which lever to pull.

Sub-parts
---------
- :func:`delivery_kpis` — the delivery-performance metrics.
- :func:`cost_model` — the cost breakdown.
- :func:`gmv_summary` — the commercial view.
- :func:`scorecard` — everything, with targets and verdicts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import DEFAULT_VALUES, ValueConfig
from .delivery import DeliveryOutcome
from .models import (
    CodSettlement,
    Order,
    OrderStatus,
    Route,
    Shipment,
    World,
)


# --------------------------------------------------------------------------- #
# Delivery KPIs
# --------------------------------------------------------------------------- #


def delivery_kpis(
    world: World,
    outcomes: list[DeliveryOutcome],
    at: Any = None,
) -> dict[str, Any]:
    """The delivery-performance KPI set.

    Denominators are explicit in the output, because every one of these
    percentages is only interpretable next to its base size.
    """

    now = at or world.now

    due = [
        s
        for s in world.shipments.values()
        if (o := world.orders.get(s.order_id)) is not None and o.promised_at <= now
    ]

    delivered = [s for s in due if s.status == OrderStatus.DELIVERED]
    returned = [s for s in due if s.status == OrderStatus.RETURNED]

    on_time = [
        s
        for s in delivered
        if s.delivered_at is not None
        and s.delivered_at <= world.orders[s.order_id].promised_at
    ]

    # -- First-attempt success --------------------------------------------- #
    first_attempt_successes = sum(1 for o in outcomes if o.first_attempt_success)
    delivered_outcomes = [o for o in outcomes if o.final_status == OrderStatus.DELIVERED]

    # -- Attempts per delivery --------------------------------------------- #
    total_attempts = sum(o.attempt_count for o in outcomes)
    attempts_per_delivery = (
        total_attempts / len(delivered_outcomes) if delivered_outcomes else 0.0
    )

    # -- RTO --------------------------------------------------------------- #
    rto_base = len(delivered) + len(returned)
    rto_rate = len(returned) / rto_base if rto_base else 0.0

    # -- COD --------------------------------------------------------------- #
    cod_due = [
        s
        for s in due
        if (o := world.orders.get(s.order_id)) is not None and o.is_cod
    ]
    cod_returned = [s for s in cod_due if s.status == OrderStatus.RETURNED]
    cod_rto = len(cod_returned) / len(cod_due) if cod_due else 0.0

    prepaid_due = [s for s in due if s not in cod_due]
    prepaid_returned = [s for s in prepaid_due if s.status == OrderStatus.RETURNED]
    prepaid_rto = (
        len(prepaid_returned) / len(prepaid_due) if prepaid_due else 0.0
    )

    # -- Delivery latency -------------------------------------------------- #
    lateness_hours = [
        (s.delivered_at - world.orders[s.order_id].promised_at).total_seconds() / 3600.0
        for s in delivered
        if s.delivered_at is not None
    ]
    mean_lateness = sum(lateness_hours) / len(lateness_hours) if lateness_hours else 0.0

    lead_hours = [
        (s.delivered_at - world.orders[s.order_id].created_at).total_seconds() / 3600.0
        for s in delivered
        if s.delivered_at is not None
    ]
    mean_lead_time = sum(lead_hours) / len(lead_hours) if lead_hours else 0.0

    return {
        "as_of": now.isoformat(),
        "shipments_due": len(due),
        "delivered": len(delivered),
        "returned": len(returned),
        "on_time_delivery_rate": round(len(on_time) / len(due), 4) if due else 0.0,
        "first_attempt_success_rate": round(
            first_attempt_successes / len(delivered_outcomes), 4
        )
        if delivered_outcomes
        else 0.0,
        "rto_rate": round(rto_rate, 4),
        "cod_rto_rate": round(cod_rto, 4),
        "prepaid_rto_rate": round(prepaid_rto, 4),
        "attempts_per_delivery": round(attempts_per_delivery, 3),
        "mean_lead_time_hours": round(mean_lead_time, 2),
        "mean_lateness_hours": round(mean_lateness, 2),
        "denominators": {
            "otd": len(due),
            "fad": len(delivered_outcomes),
            "rto": rto_base,
            "cod_rto": len(cod_due),
            "prepaid_rto": len(prepaid_due),
        },
    }


# --------------------------------------------------------------------------- #
# Cost model
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class CostBreakdown:
    """Where the money went."""

    fixed_cost: float = 0.0
    stop_cost: float = 0.0
    distance_cost: float = 0.0
    failed_attempt_cost: float = 0.0
    rto_cost: float = 0.0

    @property
    def total(self) -> float:
        """Total cost to serve."""
        return (
            self.fixed_cost
            + self.stop_cost
            + self.distance_cost
            + self.failed_attempt_cost
            + self.rto_cost
        )

    def as_dict(self) -> dict[str, Any]:
        """A JSON-friendly view."""
        return {
            "fixed_cost": round(self.fixed_cost, 2),
            "stop_cost": round(self.stop_cost, 2),
            "distance_cost": round(self.distance_cost, 2),
            "failed_attempt_cost": round(self.failed_attempt_cost, 2),
            "rto_cost": round(self.rto_cost, 2),
            "total": round(self.total, 2),
        }


def cost_model(
    routes: list[Route],
    world: World,
    outcomes: list[DeliveryOutcome],
    values: ValueConfig | None = None,
) -> dict[str, Any]:
    """Build the full cost model for the network.

    The three route cost components are separated because they respond to
    different levers:

    - **Fixed** falls per parcel as routes get fuller. Fix utilisation.
    - **Stop cost** falls when consolidation improves. Fix the dispatcher.
    - **Distance** falls when routes get shorter. Fix the router.

    Blending them into one number hides which of the three is actually the
    problem, which is exactly the mistake this project is trying not to
    make.
    """

    vals = values or DEFAULT_VALUES
    breakdown = CostBreakdown()

    for route in routes:
        courier = world.couriers.get(route.courier_id)
        if courier is None:
            continue
        breakdown.fixed_cost += courier.fixed_cost
        breakdown.stop_cost += courier.cost_per_stop * route.stop_count
        breakdown.distance_cost += courier.cost_per_km * route.total_distance_km

    for outcome in outcomes:
        breakdown.failed_attempt_cost += outcome.attempt_cost

    # Reverse logistics is dearer than forward: published reverse rates run
    # roughly 1.5-2x the forward rate.
    shipments_by_order = {s.order_id: s for s in world.shipments.values()}
    for shipment in world.shipments.values():
        if shipment.status != OrderStatus.RETURNED:
            continue
        order = world.orders.get(shipment.order_id)
        if order is None:
            continue
        forward = _forward_cost_for(order, shipments_by_order.get(order.order_id), world, vals)
        breakdown.rto_cost += forward * (vals.rto_cost_multiplier - 1.0)

    total = breakdown.total
    delivered = sum(1 for o in outcomes if o.final_status == OrderStatus.DELIVERED)
    stops = sum(r.stop_count for r in routes)
    parcels = sum(r.parcel_count for r in routes)

    gmv = sum(
        world.orders[s.order_id].order_value
        for s in world.shipments.values()
        if s.status == OrderStatus.DELIVERED and s.order_id in world.orders
    )

    return {
        "breakdown": breakdown.as_dict(),
        "routes": len(routes),
        "stops": stops,
        "parcels": parcels,
        "delivered_parcels": delivered,
        "cost_per_parcel": round(total / parcels, 2) if parcels else 0.0,
        "cost_per_stop": round(total / stops, 2) if stops else 0.0,
        "cost_per_delivery": round(total / delivered, 2) if delivered else 0.0,
        "gmv_delivered": round(gmv, 2),
        "cost_to_serve_pct_of_gmv": round(total / gmv * 100, 2) if gmv else 0.0,
        "orders_per_stop": round(parcels / stops, 2) if stops else 0.0,
    }


def _forward_cost_for(
    order: Order,
    shipment: Shipment | None,
    world: World,
    values: ValueConfig,
) -> float:
    """The forward freight cost of one order, for the RTO multiplier."""
    if shipment is None:
        return 60.0
    parcels = [world.parcels[p] for p in shipment.parcel_ids if p in world.parcels]
    if not parcels:
        return 60.0
    total_kg = sum(p.weight_kg for p in parcels)
    return max(35.0, total_kg * 12.0)


# --------------------------------------------------------------------------- #
# Commercial view
# --------------------------------------------------------------------------- #


def gmv_summary(world: World, settlements: list[CodSettlement]) -> dict[str, Any]:
    """The commercial view: what the network moved, and what it collected.

    COD cash is a real balance-sheet item. A merchant delivering a third of
    their orders on cash is financing the network's collection cycle, and
    the days-to-settle figure is the cost of that financing.
    """

    delivered = [s for s in world.shipments.values() if s.status == OrderStatus.DELIVERED]
    returned = [s for s in world.shipments.values() if s.status == OrderStatus.RETURNED]

    gmv_delivered = sum(
        world.orders[s.order_id].order_value for s in delivered if s.order_id in world.orders
    )
    gmv_returned = sum(
        world.orders[s.order_id].order_value for s in returned if s.order_id in world.orders
    )
    gmv_placed = gmv_delivered + gmv_returned

    cod_collected = sum(s.amount for s in settlements)
    settled_days = [s.days_to_settle for s in settlements if s.days_to_settle is not None]

    return {
        "gmv_placed": round(gmv_placed, 2),
        "gmv_delivered": round(gmv_delivered, 2),
        "gmv_returned": round(gmv_returned, 2),
        "delivery_rate": round(len(delivered) / len(world.shipments), 4)
        if world.shipments
        else 0.0,
        "cod_cash_collected": round(cod_collected, 2),
        "cod_settlements": len(settlements),
        "average_days_to_settle": round(sum(settled_days) / len(settled_days), 2)
        if settled_days
        else 0.0,
        "max_days_to_settle": max(settled_days) if settled_days else 0,
    }


# --------------------------------------------------------------------------- #
# Scorecard
# --------------------------------------------------------------------------- #


def scorecard(
    kpis: dict[str, Any],
    cost: dict[str, Any],
    gmv: dict[str, Any],
    values: ValueConfig | None = None,
) -> dict[str, Any]:
    """The headline scorecard, with each KPI judged against its target.

    Each entry carries the measured value, the published target and a
    verdict, so a reader does not have to look up what "good" means.
    """

    vals = values or DEFAULT_VALUES

    checks = [
        {
            "kpi": "on_time_delivery_rate",
            "measured": kpis.get("on_time_delivery_rate", 0.0),
            "target": vals.otd_target,
            "direction": "higher_is_better",
        },
        {
            "kpi": "first_attempt_success_rate",
            "measured": kpis.get("first_attempt_success_rate", 0.0),
            "target": vals.fad_target,
            "direction": "higher_is_better",
        },
        {
            "kpi": "rto_rate",
            "measured": kpis.get("rto_rate", 0.0),
            "target": vals.rto_target,
            "direction": "lower_is_better",
        },
        {
            "kpi": "attempts_per_delivery",
            "measured": kpis.get("attempts_per_delivery", 0.0),
            "target": 1.35,
            "direction": "lower_is_better",
        },
        {
            "kpi": "orders_per_stop",
            "measured": cost.get("orders_per_stop", 0.0),
            "target": 1.5,
            "direction": "higher_is_better",
        },
    ]

    for check in checks:
        measured = float(check["measured"])
        target = float(check["target"])
        if check["direction"] == "higher_is_better":
            check["verdict"] = "pass" if measured >= target else "miss"
        else:
            check["verdict"] = "pass" if measured <= target else "miss"
        check["gap"] = round(measured - target, 4)

    passed = sum(1 for c in checks if c["verdict"] == "pass")

    return {
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "pass_rate": round(passed / len(checks), 4) if checks else 0.0,
        "kpis": kpis,
        "cost": cost,
        "gmv": gmv,
    }
