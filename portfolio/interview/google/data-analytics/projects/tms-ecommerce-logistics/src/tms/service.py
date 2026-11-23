"""The composition root: the one place the whole system is wired together.

**Every other module in this project is a pure function over data.** None of
them holds state, none of them reads a file, none of them reaches the
network. That is what makes the system testable and what makes it
reproducible — and it means there has to be exactly one place where the
pipeline is actually run in order.

The pipeline, in order:

    corpus -> risk scoring -> daily dispatch -> routing -> ETA
           -> delivery simulation -> SLA scan -> metrics -> ledger

**Why the order matters.** Risk scoring runs before dispatch, so a blocked
order never takes up a courier's capacity. Dispatch runs before routing,
because the router can only sequence stops that a courier has been given.
Routing runs before ETA, because the ETA is a function of the sequence.
Delivery runs before the SLA scan, because a breach can only be confirmed
after the parcel has actually moved.

Sub-parts
---------
- :class:`TmsService` — the built system.
- :class:`TmsService.create` — the one-call constructor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .audit import AuditLedger
from .config import DEFAULT_VALUES, Settings, ValueConfig, assumptions_snapshot
from .corpus import build_world, corpus_summary
from .delivery import DeliveryOutcome, cod_ledger, simulate_delivery
from .dispatch import DispatchPlan, dispatch_day, plan_summary
from .eta import promise_drift, route_promise_drift
from .fraud import (
    RiskAssessment,
    apply_risk_decisions,
    fraud_summary,
    scan_courier_fraud,
)
from .lifecycle import ScanLog, advance_shipment
from .metrics import cost_model, delivery_kpis, gmv_summary, scorecard
from .models import (
    Address,
    Order,
    OrderStatus,
    Route,
    ScanType,
    ServiceLevel,
    Shipment,
    World,
)
from .routing import (
    dropped_order_ids,
    plan_routes,
    route_cost_breakdown,
    utilisation_report,
)
from .sla import breach_detail, scan_for_breaches, scan_for_risk, sla_summary


@dataclass(slots=True)
class TmsService:
    """A built, runnable transport management system.

    Holds the world, the plans, the routes, the delivery outcomes and the
    ledger. The API layer and the demo script both go through this object,
    so they cannot drift apart.
    """

    settings: Settings
    values: ValueConfig
    world: World
    scan_log: ScanLog = field(default_factory=ScanLog)
    ledger: AuditLedger = field(default_factory=AuditLedger)
    plans: dict[str, DispatchPlan] = field(default_factory=dict)
    routes: list[Route] = field(default_factory=list)
    outcomes: dict[str, DeliveryOutcome] = field(default_factory=dict)
    assessments: list[RiskAssessment] = field(default_factory=list)
    #: shipment id -> P90 forecast, used for early-warning SLA detection.
    forecasts: dict[str, datetime] = field(default_factory=dict)
    #: Rejected state transitions. Should always be empty; if it is not, the
    #: state machine caught something the pipeline tried to do.
    _transition_failures: list[str] = field(default_factory=list)
    _hub_addresses: dict[str, Address] = field(default_factory=dict)

    # -- Construction ------------------------------------------------------- #

    @classmethod
    def create(
        cls,
        settings: Settings | None = None,
        values: ValueConfig | None = None,
    ) -> TmsService:
        """Build and run the whole simulation.

        One call, one fully populated system. The pipeline runs here so that
        every consumer — the API, the demo, the tests, the eval harness —
        sees the same world.
        """

        cfg = settings or Settings.from_env()
        vals = values or DEFAULT_VALUES

        world = build_world(cfg, vals)
        service = cls(settings=cfg, values=vals, world=world)
        service.run()
        return service

    # -- The pipeline ------------------------------------------------------- #

    def run(self) -> None:
        """Run the whole simulation pipeline.

        Safe to call twice — the second call rebuilds from scratch, which
        keeps the service idempotent for tests.
        """

        self.scan_log = ScanLog()
        self.ledger = AuditLedger()
        self.plans = {}
        self.routes = []
        self.outcomes = {}
        self.forecasts = {}
        self._transition_failures = []

        self._build_hub_addresses()
        self._score_risk()
        self._dispatch_all_days()
        self._plan_routes()
        self._simulate_delivery()
        self._record_ledger()

    def _build_hub_addresses(self) -> None:
        """Give every hub a physical location to plan routes from."""
        from .corpus import _HUBS

        for hub_id, _name, lat, lng in _HUBS:
            self._hub_addresses[hub_id] = Address(
                address_id=f"hub-addr-{hub_id}",
                line1="Fulfillment Center",
                area="Industrial Estate",
                city="Metro City",
                pin_code="000001",
                lat=lat,
                lng=lng,
                tier="tier1",
                landmark="Loading Bay",
            )

    # -- Risk --------------------------------------------------------------- #

    def _score_risk(self) -> None:
        """Score every order for COD return-fraud risk."""
        self.assessments = apply_risk_decisions(self.world, self.values)

        for assessment in self.assessments:
            order = self.world.orders.get(assessment.order_id)
            if order is None:
                continue
            if assessment.action.value in ("block", "prepay_only", "partial_prepay"):
                self.ledger.record(
                    kind="risk_decision",
                    subject_id=assessment.order_id,
                    outcome=assessment.action.value,
                    rationale=(
                        f"risk score {assessment.score:.2f} "
                        f"({len(assessment.signals)} signals)"
                    ),
                    decided_at=order.created_at,
                    detail=assessment.as_dict(),
                )

    # -- Dispatch ----------------------------------------------------------- #

    def _dispatch_all_days(self) -> None:
        """Run dispatch and routing for every simulated operating day.

        Orders that miss one day's wave are carried into the next day's
        wave rather than being dropped. An order placed at 11pm cannot
        be delivered that night — the warehouse is closed and the couriers
        have gone home — but it can go out on the next morning's first
        wave, and holding it until the following day instead would break
        the promise for no reason other than the accounting boundary.

        Routing is interleaved with the dispatch because the two can
        disagree. The dispatcher assigns stops to couriers; the router
        re-sequences them into a path, and the path can turn out not to
        fit inside the shift the dispatcher thought it would. The stops
        that fall off the end are handed back and carried into the next
        day, the same way a stop the dispatcher could not place is.
        """
        days = sorted(
            {o.created_at.date() for o in self.world.orders.values()}
        )
        carry_in: list[str] = []
        for day in days:
            day_start = datetime(
                day.year, day.month, day.day, tzinfo=self.world.now.tzinfo
            )
            plan = dispatch_day(self.world, day_start, self.values, carry_in=carry_in)

            # -- Route this day's plan ------------------------------------ #
            # Anything the router could not fit into a shift is nobody's
            # job until the dispatcher puts it on tomorrow's wave.
            routes = plan_routes(plan.allocations, self._hub_addresses, self.values)
            self.routes.extend(routes)
            overflow = dropped_order_ids(routes)
            if overflow:
                plan.deferred_orders.extend(overflow)
                plan.projected_breaches.extend(overflow)

            self.plans[day_start.date().isoformat()] = plan

            for order_id in plan.deferred_orders:
                self.ledger.record(
                    kind="deferral",
                    subject_id=order_id,
                    outcome="deferred_to_next_wave",
                    rationale=(
                        "no courier capacity after surge hiring, or the "
                        "planned route did not fit inside the shift; "
                        "deferred to the next wave rather than left unassigned"
                    ),
                    decided_at=day_start,
                )

            carry_in = list(plan.deferred_orders)

    # -- Routing ------------------------------------------------------------ #

    def _plan_routes(self) -> None:
        """Plan a route for every courier who was given stops.

        Kept for the case where a caller has built plans by hand and
        wants the routes without the interleaved dispatch. The normal
        path plans each day's routes as it dispatches it.
        """

        if self.routes:
            return
        for plan in self.plans.values():
            self.routes.extend(
                plan_routes(plan.allocations, self._hub_addresses, self.values)
            )

    # -- Delivery ----------------------------------------------------------- #

    def _simulate_delivery(self) -> None:
        """Run the delivery chain for every shipment that was routed."""
        # Index the routes by the orders they carry, and the shipments by
        # their order. Both lookups happen once per shipment, so a linear
        # scan over the shipment table would make this O(n^2).
        order_to_route: dict[str, Route] = {}
        for route in self.routes:
            for stop in route.stops:
                for order_id in stop.order_ids:
                    order_to_route[order_id] = route

        shipments_by_order = {
            shipment.order_id: shipment for shipment in self.world.shipments.values()
        }

        for shipment in self.world.shipments.values():
            route = order_to_route.get(shipment.order_id)
            if route is None:
                continue

            order = self.world.orders.get(shipment.order_id)
            if order is None:
                continue

            courier_id = route.courier_id
            courier = self.world.couriers.get(courier_id)
            if courier is None:
                continue

            # -- Move the shipment through its states to out-for-delivery #
            # The transitions must follow the legal path in the state
            # machine: created -> allocated -> packed -> picked_up ->
            # in_transit. Skipping a step is rejected by the machine, and a
            # rejected transition is *not* silently ignored — it is counted.
            for target, scan_type, hours in (
                (OrderStatus.ALLOCATED, ScanType.ALLOCATED, 2),
                (OrderStatus.PACKED, ScanType.PACKED, 4),
                (OrderStatus.PICKED_UP, ScanType.PICKED_UP, 7),
                (OrderStatus.IN_TRANSIT, ScanType.LINE_HAUL_DEPARTED, 9),
                (OrderStatus.OUT_FOR_DELIVERY, ScanType.OUT_FOR_DELIVERY, 11),
            ):
                result = advance_shipment(
                    shipment,
                    target,
                    occurred_at=order.created_at + timedelta(hours=hours),
                    scan_type=scan_type,
                    log=self.scan_log,
                    location_id=shipment.origin_hub,
                    actor_id=courier_id,
                )
                if not result.ok:
                    self._transition_failures.append(result.error)

            # -- Find the planned attempt time ---------------------------- #
            attempt_at = order.created_at + timedelta(hours=12)
            for stop in route.stops:
                if order.order_id in stop.order_ids:
                    if stop.eta_p50 is not None:
                        attempt_at = stop.eta_p50
                    break

            outcome = simulate_delivery(
                shipment,
                order,
                courier_id,
                attempt_at,
                self.values,
                self.settings,
                carrier=shipment.carrier,
            )
            self.outcomes[shipment.shipment_id] = outcome

            # -- Record the delivery in the scan log --------------------- #
            if outcome.final_status == OrderStatus.DELIVERED:
                delivered = advance_shipment(
                    shipment,
                    OrderStatus.DELIVERED,
                    occurred_at=outcome.delivered_at or attempt_at,
                    scan_type=ScanType.DELIVERED,
                    log=self.scan_log,
                    location_id=shipment.destination_hub,
                    actor_id=courier_id,
                    note=f"POD: {outcome.attempts[-1].pod_type.value}",
                )
                if not delivered.ok:
                    self._transition_failures.append(delivered.error)
                shipment.delivered_at = outcome.delivered_at
                if outcome.cod_collected > 0:
                    self.scan_log.append(
                        entity_type="shipment",
                        entity_id=shipment.shipment_id,
                        scan_type=ScanType.COD_COLLECTED,
                        occurred_at=outcome.delivered_at or attempt_at,
                        status=OrderStatus.DELIVERED,
                        source="tms",
                        location_id=shipment.destination_hub,
                        actor_id=courier_id,
                        note=f"{outcome.cod_collected:.2f} collected",
                    )
            else:
                ndr = advance_shipment(
                    shipment,
                    OrderStatus.FAILED_DELIVERY,
                    occurred_at=attempt_at,
                    scan_type=ScanType.NDR_RAISED,
                    log=self.scan_log,
                    location_id=shipment.destination_hub,
                    actor_id=courier_id,
                    note=outcome.rto_reason.value if outcome.rto_reason else "",
                )
                if not ndr.ok:
                    self._transition_failures.append(ndr.error)

                rto = advance_shipment(
                    shipment,
                    OrderStatus.RETURNED,
                    occurred_at=attempt_at + timedelta(days=2),
                    scan_type=ScanType.RETURNED,
                    log=self.scan_log,
                    location_id=shipment.origin_hub,
                    note="returned to origin",
                )
                if not rto.ok:
                    self._transition_failures.append(rto.error)

                shipment.rto_reason = outcome.rto_reason

            # -- Record the P90 forecast for early warning --------------- #
            if outcome.final_status != OrderStatus.DELIVERED:
                for stop in route.stops:
                    if order.order_id in stop.order_ids and stop.eta_p90 is not None:
                        self.forecasts[shipment.shipment_id] = stop.eta_p90
                        break

    # -- Ledger ------------------------------------------------------------- #

    def _record_ledger(self) -> None:
        """Record the notable decisions in the audit ledger."""
        for shipment in self.world.shipments.values():
            order = self.world.orders.get(shipment.order_id)
            if order is None:
                continue
            if shipment.status == OrderStatus.RETURNED:
                self.ledger.record(
                    kind="rto",
                    subject_id=shipment.order_id,
                    outcome="returned_to_origin",
                    rationale=(
                        f"delivery failed after "
                        f"{self.outcomes[shipment.shipment_id].attempt_count} attempts"
                        if shipment.shipment_id in self.outcomes
                        else "delivery failed"
                    ),
                    decided_at=order.promised_at,
                    detail={
                        "service_level": order.service_level.value,
                        "is_cod": order.is_cod,
                        "order_value": order.order_value,
                    },
                )

    # -- Views -------------------------------------------------------------- #

    def health(self) -> dict[str, Any]:
        """What is loaded and what is live."""
        return {
            "ok": True,
            "service": "tms-ecommerce-logistics",
            "corpus": corpus_summary(self.world),
            "routes_planned": len(self.routes),
            "shipments_simulated": len(self.outcomes),
            "decisions_recorded": len(self.ledger.decisions),
            "scan_events": len(self.scan_log.events),
            "now": self.world.now.isoformat(),
            "seed": self.settings.seed,
            "deterministic": True,
            "transition_failures": len(self._transition_failures),
        }

    def metrics(self) -> dict[str, Any]:
        """The full KPI, cost and commercial scorecard."""
        outcomes = list(self.outcomes.values())
        kpis = delivery_kpis(self.world, outcomes, self.world.now)
        cost = cost_model(self.routes, self.world, outcomes, self.values)
        settlements = cod_ledger(self.world)
        gmv = gmv_summary(self.world, settlements)
        return scorecard(kpis, cost, gmv, self.values)

    def dispatch_view(self, day: str | None = None) -> dict[str, Any]:
        """The dispatch plan for one day, or all days."""
        if day is None:
            return {
                "days": {
                    key: plan_summary(plan) for key, plan in sorted(self.plans.items())
                }
            }
        plan = self.plans.get(day)
        if plan is None:
            return {"ok": False, "error": f"no dispatch plan for {day}"}
        return {"ok": True, **plan_summary(plan)}

    def routes_view(self) -> dict[str, Any]:
        """Every planned route, with its cost breakdown."""
        rows: list[dict[str, Any]] = []
        for route in self.routes:
            courier = self.world.couriers.get(route.courier_id)
            if courier is None:
                continue
            row = route_cost_breakdown(route, courier)
            row["date"] = route.route_date.date().isoformat()
            row["is_surge"] = courier.is_surge
            rows.append(row)
        rows.sort(key=lambda r: r["cost_per_parcel"])
        return {
            "routes": rows,
            "count": len(rows),
            "utilisation": utilisation_report(self.routes, self.world.couriers),
        }

    def tracking_view(self, shipment_id: str) -> dict[str, Any]:
        """The tracking timeline for one shipment."""
        shipment = self.world.shipments.get(shipment_id)
        if shipment is None:
            return {"ok": False, "error": f"no shipment {shipment_id}"}
        order = self.world.orders.get(shipment.order_id)
        attempts = self.outcomes.get(shipment_id)

        return {
            "ok": True,
            "shipment": {
                "shipment_id": shipment.shipment_id,
                "order_id": shipment.order_id,
                "tracking_number": shipment.tracking_number,
                "carrier": shipment.carrier,
                "status": shipment.status.value,
                "service_level": shipment.service_level.value,
                "promised_at": shipment.promised_at.isoformat(),
            },
            "customer": {
                "name": order.customer_id if order else None,
                "zone": order.zone_id if order else None,
                "tier": order.address.tier if order else None,
                "is_cod": order.is_cod if order else None,
                "order_value": order.order_value if order else None,
            },
            "timeline": self.scan_log.timeline(shipment_id),
            "attempts": [
                {
                    "attempt_no": a.attempt_no,
                    "attempted_at": a.attempted_at.isoformat(),
                    "success": a.success,
                    "reason": a.reason.value if a.reason else None,
                    "pod_type": a.pod_type.value,
                    "cod_collected": a.cod_collected,
                }
                for a in (attempts.attempts if attempts else [])
            ],
        }

    def sla_view(self) -> dict[str, Any]:
        """Confirmed breaches and at-risk shipments."""
        breaches = scan_for_breaches(self.world, self.world.now)
        attempts_by_shipment = {
            sid: outcome.attempt_count for sid, outcome in self.outcomes.items()
        }
        risks = scan_for_risk(
            self.world, self.forecasts, attempts_by_shipment, self.world.now
        )
        return {
            "summary": sla_summary(self.world, breaches, self.world.now),
            "breaches": [breach_detail(b) for b in breaches],
            "at_risk": [r.as_dict() for r in risks],
            "at_risk_count": len(risks),
        }

    def fraud_view(self) -> dict[str, Any]:
        """The risk decisions and the courier-side findings."""
        attempts = [a for o in self.outcomes.values() for a in o.attempts]
        courier_findings = scan_courier_fraud(attempts, self.world, self.values)
        summary = fraud_summary(self.assessments, courier_findings)

        # Does the model actually catch the planted fraud?
        planted = set(self.world.ground_truth.get("fraud_order_ids", []))
        caught = {
            a.order_id
            for a in self.assessments
            if a.order_id in planted and a.action.value != "release"
        }
        flagged = {a.order_id for a in self.assessments if a.action.value != "release"}

        return {
            "summary": summary,
            "courier_findings": [f.as_dict() for f in courier_findings],
            "planted_fraud_orders": len(planted),
            "planted_fraud_caught": len(caught),
            "planted_fraud_recall": round(len(caught) / len(planted), 4)
            if planted
            else 0.0,
            "false_positives": len(flagged - planted),
        }

    def cod_view(self) -> dict[str, Any]:
        """The COD money: collected, outstanding, and how long it took."""
        settlements = cod_ledger(self.world)
        from .delivery import settle_due_cash

        settled = settle_due_cash(settlements, self.world.now)
        outstanding = [
            s.as_dict() if hasattr(s, "as_dict") else _settlement_dict(s)
            for s in settlements
            if not s.is_settled
        ]
        return {
            "summary": settled,
            "outstanding": outstanding[:50],
            "outstanding_total": len(outstanding),
        }

    def assumptions(self) -> dict[str, Any]:
        """Every business assumption, with its provenance tag."""
        return {
            "assumptions": [
                {
                    "key": a.key,
                    "value": a.value,
                    "provenance": a.provenance,
                    "note": a.note,
                }
                for a in assumptions_snapshot(self.values)
            ]
        }


def _settlement_dict(settlement: Any) -> dict[str, Any]:
    """A JSON-friendly view of a settlement record."""
    return {
        "settlement_id": settlement.settlement_id,
        "order_id": settlement.order_id,
        "merchant_id": settlement.merchant_id,
        "amount": settlement.amount,
        "collected_at": settlement.collected_at.isoformat(),
        "due_at": settlement.due_at.isoformat(),
    }
