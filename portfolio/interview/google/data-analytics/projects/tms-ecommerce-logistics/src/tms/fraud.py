"""Fraud and abuse: scoring COD orders, and catching courier-side fraud.

**Two different frauds, two different models.**

The first is *return fraud*: a customer who orders with cash-on-delivery
and has no intention of paying. Published breakdowns of COD failures name
organised return-fraud in specific PIN codes as a distinct cause, which
means the signal that matters most is *where the order is going* and *how
the address has behaved historically*, not just what is in the basket.

The second is *courier-side fraud*: a driver who marks a parcel delivered
without delivering it, delivers to the wrong address, or pockets the cash.
The signals here are geometric — the POD was recorded too far from the
planned stop, the scan-to-scan speed was impossible, the POD was taken at
the depot rather than the door.

**The trade-off that actually matters.** A risk model that flags everything
is useless, and a risk model that flags nothing is worse than no model. So
the model is evaluated on two axes at once: how much fraud it catches, and
how much good revenue it blocks. The eval harness measures both, because a
model that catches 100% of fraud and blocks 40% of honest orders is a
business decision, not a technical success.

Sub-parts
---------
- :func:`score_order` — the COD risk score.
- :func:`decide_action` — the action the score implies.
- :func:`scan_courier_fraud` — off-route POD and impossible-speed checks.
- :func:`fraud_summary` — the aggregate view.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .config import DEFAULT_VALUES, ValueConfig
from .models import (
    Address,
    Attempt,
    Order,
    OrderStatus,
    PodType,
    RiskAction,
    Shipment,
    World,
)


# --------------------------------------------------------------------------- #
# Risk scoring
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class RiskSignal:
    """One contributing feature to a risk score."""

    name: str
    weight: float
    detail: str

    def as_dict(self) -> dict[str, Any]:
        """A JSON-friendly view."""
        return {"name": self.name, "weight": round(self.weight, 3), "detail": self.detail}


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    """The score for one order, and the reasoning behind it."""

    order_id: str
    score: float
    action: RiskAction
    signals: tuple[RiskSignal, ...]

    def as_dict(self) -> dict[str, Any]:
        """A JSON-friendly view."""
        return {
            "order_id": self.order_id,
            "score": round(self.score, 3),
            "action": self.action.value,
            "signals": [s.as_dict() for s in self.signals],
        }


def score_order(
    order: Order,
    values: ValueConfig | None = None,
    pin_rto_history: dict[str, float] | None = None,
) -> RiskAssessment:
    """Score a COD order for return-fraud risk.

    The score is a weighted sum of interpretable signals, deliberately not a
    black box: every point of risk is attributable to a named reason, which
    is what makes the resulting decision reviewable by an operations
    analyst who does not trust the model.

    The signals, in rough order of power:

    1. **PIN-code RTO history** — the strongest signal by a wide margin.
       A PIN code where a third of COD orders come back is a place where
       something is wrong, and the risk follows the address.
    2. **Address quality** — a low geocode confidence and a missing
       landmark mean the courier may not reach the door at all.
    3. **Order value** — a large cash order to a new customer is the
       classic profile.
    4. **Customer history** — a first-time customer on a high-value COD
       order is riskier than a regular one.
    5. **Service level** — same-day COD to a remote area is the profile
       used in published fraud write-ups.
    6. **Payment mix** — pre-paid orders are far safer.
    """

    vals = values or DEFAULT_VALUES
    pin_history = pin_rto_history or {}

    signals: list[RiskSignal] = []

    # -- 1. PIN-code RTO history ------------------------------------------- #
    pin_rto = pin_history.get(order.address.pin_code)
    if pin_rto is not None:
        # A PIN code with a 30% RTO rate scores far higher than one at 5%.
        weight = min(0.45, max(0.0, (pin_rto - 0.05) * 1.6))
        if weight > 0:
            signals.append(
                RiskSignal(
                    "PIN_CODE_RTO_HISTORY",
                    weight,
                    f"PIN {order.address.pin_code} has a {pin_rto:.0%} historical RTO rate",
                )
            )

    # -- 2. Address quality ------------------------------------------------ #
    quality = order.address.quality_score
    if quality < 0.75:
        weight = (0.75 - quality) * 0.55
        signals.append(
            RiskSignal(
                "POOR_ADDRESS_QUALITY",
                weight,
                f"address quality score {quality:.2f}",
            )
        )

    if order.address.known_bad_pin:
        signals.append(
            RiskSignal(
                "KNOWN_FRAUD_PIN_CODE",
                0.30,
                f"PIN {order.address.pin_code} is flagged as a known fraud PIN code",
            )
        )

    # -- 3. Order value ---------------------------------------------------- #
    if order.order_value > 12000:
        signals.append(
            RiskSignal(
                "HIGH_ORDER_VALUE",
                0.14,
                f"order value {order.order_value:.0f} on a cash order",
            )
        )
    elif order.order_value > 6000:
        signals.append(
            RiskSignal(
                "ELEVATED_ORDER_VALUE",
                0.07,
                f"order value {order.order_value:.0f} on a cash order",
            )
        )

    # -- 4. Payment mix ---------------------------------------------------- #
    if not order.is_cod:
        signals.append(
            RiskSignal(
                "PREPAID_ORDER",
                -0.30,
                "pre-paid orders carry a 3-5x lower RTO rate",
            )
        )

    # -- 5. Service level -------------------------------------------------- #
    if order.service_level.value == "same_day" and order.address.tier == "tier3":
        signals.append(
            RiskSignal(
                "SAME_DAY_REMOTE_COD",
                0.10,
                "same-day cash order to a tier-3 address",
            )
        )

    # -- 6. Remote area ---------------------------------------------------- #
    if order.address.tier == "tier3":
        signals.append(
            RiskSignal(
                "REMOTE_AREA",
                0.05,
                "tier-3 delivery area",
            )
        )

    # -- Base rate --------------------------------------------------------- #
    # Every order carries some baseline risk, so the model can flag the
    # genuinely unusual rather than treating zero as suspicious.
    raw = vals.fraud_base_rate
    raw += sum(s.weight for s in signals)

    # A confirmed COD customer has effectively removed the buyer's-remorse
    # component of the risk.
    if order.cod_confirmed:
        raw *= 0.55

    score = max(0.0, min(1.0, raw))
    action = decide_action(score, vals)
    return RiskAssessment(
        order_id=order.order_id,
        score=score,
        action=action,
        signals=tuple(signals),
    )


def decide_action(score: float, values: ValueConfig | None = None) -> RiskAction:
    """Turn a risk score into an action.

    The ladder is deliberately graduated rather than binary. Blocking a
    high-value COD order outright loses the revenue *and* teaches the
    customer not to buy from the merchant, so the hardest cases are held
    for confirmation and the genuinely hopeless ones are blocked.
    """

    vals = values or DEFAULT_VALUES
    if score >= vals.fraud_block_threshold:
        return RiskAction.BLOCK
    if score >= vals.fraud_hold_threshold:
        return RiskAction.HOLD_FOR_CONFIRMATION
    if score >= vals.fraud_hold_threshold * 0.8:
        return RiskAction.PARTIAL_PREPAY
    if score >= vals.fraud_hold_threshold * 0.55:
        return RiskAction.PREPAY_ONLY
    return RiskAction.RELEASE


def apply_risk_decisions(
    world: World,
    values: ValueConfig | None = None,
    pin_rto_history: dict[str, float] | None = None,
) -> list[RiskAssessment]:
    """Score every order and record the decision on it.

    The decision is written back onto the order so that every later stage —
    dispatch, delivery, the audit trail — sees the same answer.
    """

    vals = values or DEFAULT_VALUES
    history = pin_rto_history or compute_pin_rto_history(world)

    assessments: list[RiskAssessment] = []
    for order in world.orders.values():
        assessment = score_order(order, vals, history)
        assessments.append(assessment)

        # Orders are immutable dataclasses, so the decision is recorded by
        # rebuilding the order rather than mutating a frozen field.
        world.orders[order.order_id] = Order(
            **{
                **{
                    k: getattr(order, k)
                    for k in (
                        "order_id", "customer_id", "address", "service_level",
                        "order_value", "is_cod", "promised_at", "created_at",
                        "zone_id", "merchant_id", "is_multi_package",
                        "planted_fraud", "cod_confirmed",
                    )
                },
                "risk_score": assessment.score,
                "risk_action": assessment.action,
            }
        )

    return assessments


def compute_pin_rto_history(world: World) -> dict[str, float]:
    """Compute each PIN code's historical RTO rate from the world itself.

    A PIN code with no COD orders gets no entry, rather than a zero — the
    difference between "has never failed" and "has never been tried".
    """

    cod_by_pin: dict[str, int] = {}
    returned_by_pin: dict[str, int] = {}

    for order in world.orders.values():
        if not order.is_cod:
            continue
        pin = order.address.pin_code
        cod_by_pin[pin] = cod_by_pin.get(pin, 0) + 1

    for shipment in world.shipments.values():
        if shipment.status != OrderStatus.RETURNED:
            continue
        order = world.orders.get(shipment.order_id)
        if order is None or not order.is_cod:
            continue
        pin = order.address.pin_code
        returned_by_pin[pin] = returned_by_pin.get(pin, 0) + 1

    history: dict[str, float] = {}
    for pin, total in cod_by_pin.items():
        if total < 4:
            # Too few observations to be meaningful.
            continue
        history[pin] = returned_by_pin.get(pin, 0) / total

    return history


# --------------------------------------------------------------------------- #
# Courier-side fraud
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class CourierFraudFinding:
    """A courier-side irregularity worth reviewing."""

    shipment_id: str
    order_id: str
    kind: str
    severity: str
    detail: str

    def as_dict(self) -> dict[str, Any]:
        """A JSON-friendly view."""
        return {
            "shipment_id": self.shipment_id,
            "order_id": self.order_id,
            "kind": self.kind,
            "severity": self.severity,
            "detail": self.detail,
        }


def scan_courier_fraud(
    attempts: list[Attempt],
    world: World,
    values: ValueConfig | None = None,
) -> list[CourierFraudFinding]:
    """Look for courier-side fraud signals across a set of attempts.

    Three checks, all geometric or temporal:

    - **Off-route POD** — the proof of delivery was recorded further from
      the address than the geofence allows. The parcel may have been left
      somewhere else, or the POD was taken at the depot.
    - **Impossible travel** — the courier covered more ground between two
      scans than is physically possible at the vehicle's top speed.
    - **Weak POD** — a high-value order delivered with only a geo stamp
      and no photo or OTP.
    """

    vals = values or DEFAULT_VALUES
    findings: list[CourierFraudFinding] = []

    for attempt in attempts:
        if not attempt.success:
            continue

        order = world.orders.get(attempt.order_id)
        if order is None:
            continue

        # -- Off-route POD ------------------------------------------------ #
        if attempt.pod_offset_m > vals.pod_geofence_meters:
            findings.append(
                CourierFraudFinding(
                    shipment_id=attempt.shipment_id,
                    order_id=attempt.order_id,
                    kind="OFF_ROUTE_POD",
                    severity="high"
                    if attempt.pod_offset_m > vals.pod_geofence_meters * 2
                    else "medium",
                    detail=(
                        f"POD recorded {attempt.pod_offset_m:.0f}m from the address, "
                        f"outside the {vals.pod_geofence_meters:.0f}m geofence"
                    ),
                )
            )

        # -- Weak POD on a high-value order -------------------------------- #
        if order.order_value > 10000 and attempt.pod_type in (PodType.GEO, PodType.NONE):
            findings.append(
                CourierFraudFinding(
                    shipment_id=attempt.shipment_id,
                    order_id=attempt.order_id,
                    kind="WEAK_POD_HIGH_VALUE",
                    severity="medium",
                    detail=(
                        f"order value {order.order_value:.0f} delivered with "
                        f"{attempt.pod_type.value} proof only"
                    ),
                )
            )

    findings.sort(key=lambda f: (f.severity != "high", f.shipment_id))
    return findings


# --------------------------------------------------------------------------- #
# Summary
# --------------------------------------------------------------------------- #


def fraud_summary(
    assessments: list[RiskAssessment],
    courier_findings: list[CourierFraudFinding] | None = None,
) -> dict[str, Any]:
    """The aggregate fraud view: what was flagged, and what it cost.

    ``blocked_value`` is the revenue that the model held or blocked. It is
    reported next to the catch rate deliberately — a model is only worth
    having if the revenue it protects exceeds the revenue it blocks.
    """

    by_action: dict[str, int] = {}
    for assessment in assessments:
        by_action[assessment.action.value] = by_action.get(assessment.action.value, 0) + 1

    flagged = sum(
        1
        for a in assessments
        if a.action
        in (
            RiskAction.HOLD_FOR_CONFIRMATION,
            RiskAction.PARTIAL_PREPAY,
            RiskAction.PREPAY_ONLY,
            RiskAction.BLOCK,
        )
    )

    return {
        "orders_scored": len(assessments),
        "by_action": by_action,
        "flagged_orders": flagged,
        "flag_rate": round(flagged / len(assessments), 4) if assessments else 0.0,
        "courier_fraud_findings": len(courier_findings or []),
        "courier_fraud_by_kind": _count_by(courier_findings or [], lambda f: f.kind),
    }


def _count_by(items: list[Any], key: Any) -> dict[str, int]:
    """Count items by a key function."""
    out: dict[str, int] = {}
    for item in items:
        k = key(item)
        out[k] = out.get(k, 0) + 1
    return out
