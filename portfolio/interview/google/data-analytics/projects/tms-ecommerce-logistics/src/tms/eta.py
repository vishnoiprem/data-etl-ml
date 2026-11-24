"""The ETA engine: predicting when a parcel actually arrives.

**An ETA is a distribution, not a timestamp.** A courier service says "by
6pm" and means something between 3pm and 8pm. Publishing a single point
estimate — and then being wrong — is how a delivery promise becomes a
complaint. So every ETA in this project carries three numbers:

- ``p50`` — the median arrival, what the customer is told.
- ``p90`` — the pessimistic arrival, what the SLA is judged against.
- ``confidence`` — how much to trust the estimate, which degrades as the
  route gets longer and more variable.

Judging SLA against the P50 would be a mistake in the operator's favour:
every route would "pass" while a third of customers were late. Judging
against the P90 is the conservative choice, and it is the one that makes
early warning work — if the P90 has already slipped past the promise, the
breach is knowable hours before it happens.

The estimate itself is deliberately simple:

    remaining_time = remaining_distance / mode_speed + remaining_service_time

with speed taken from the *rush-hour* figure rather than free-flow, because
a route planned at free-flow speed is a route that is late at 5pm.

Sub-parts
---------
- :class:`Eta` — the three-number estimate.
- :func:`estimate_stop_eta` — forecast a single stop.
- :func:`recompute_route_eta` — refresh every ETA on a route.
- :func:`promise_drift` — how far the promise has moved against reality.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from .config import DEFAULT_VALUES, ValueConfig
from .models import Courier, Order, Route, Stop


@dataclass(frozen=True, slots=True)
class Eta:
    """A delivery time forecast with its uncertainty."""

    #: Median arrival — what the customer is told.
    p50: datetime
    #: Pessimistic arrival — what the SLA is judged against.
    p90: datetime
    #: 0-1. Degrades with route length and stop count.
    confidence: float

    def as_dict(self) -> dict[str, Any]:
        """A JSON-friendly view."""
        return {
            "p50": self.p50.isoformat(),
            "p90": self.p90.isoformat(),
            "confidence": round(self.confidence, 3),
            "spread_minutes": round(
                (self.p90 - self.p50).total_seconds() / 60.0, 1
            ),
        }


# --------------------------------------------------------------------------- #
# Confidence
# --------------------------------------------------------------------------- #


def eta_confidence(stops_remaining: int, distance_remaining_km: float) -> float:
    """How much to trust an ETA, as a 0-1 number.

    Confidence falls as the remaining route gets longer and busier. Twenty
    stops left in a dense zone is a very different proposition from two
    stops left, and treating them alike is how a P90 stops meaning anything.

    The curve is deliberately aggressive: it never drops below 0.35, because
    a low-confidence forecast that still produces a usable P90 is more
    valuable than a confident one that is wrong.
    """

    if stops_remaining <= 0:
        return 0.98
    stop_penalty = 1.0 - min(0.45, stops_remaining * 0.028)
    distance_penalty = 1.0 - min(0.25, distance_remaining_km * 0.006)
    return max(0.35, round(stop_penalty * distance_penalty, 3))


# --------------------------------------------------------------------------- #
# Estimation
# --------------------------------------------------------------------------- #


def estimate_stop_eta(
    *,
    departure: datetime,
    distance_km: float,
    stops_remaining: int,
    service_minutes: float,
    mode_speed_kmh: float,
    values: ValueConfig | None = None,
) -> Eta:
    """Forecast the arrival at one stop.

    ``stops_remaining`` includes the stop being estimated, because the
    courier still has to get there before serving it.

    The P50 is the moment the courier *arrives* at this stop. It is not
    the moment they finish the whole route: adding the service time of
    every downstream stop into this stop's ETA would push the first stop
    of a long route hours past its own promise, and the SLA verdict
    would then be a statement about the route's length rather than about
    this parcel's delivery. The downstream stops show up in the spread
    instead, which is where an unknown quantity belongs.
    """

    vals = values or DEFAULT_VALUES
    speed = max(1.0, mode_speed_kmh)

    travel_hours = distance_km / speed
    travel_minutes = travel_hours * 60.0

    p50 = departure + timedelta(minutes=travel_minutes)

    # The spread grows with the number of stops left: each stop is another
    # chance for a queue, a wrong address, a customer who is not ready.
    # It also covers the time the courier still owes the stops behind
    # this one, which is the real source of uncertainty about *when*
    # they will get here.
    base_spread = 18.0 + 3.2 * max(0, stops_remaining - 1)
    spread_minutes = min(210.0, base_spread)
    p90 = p50 + timedelta(minutes=spread_minutes)

    return Eta(
        p50=p50,
        p90=p90,
        confidence=eta_confidence(stops_remaining, distance_km),
    )


def recompute_route_eta(
    route: Route,
    courier: Courier,
    values: ValueConfig | None = None,
    earliest_ready: datetime | None = None,
) -> Route:
    """Refresh every ETA on a route, in sequence.

    Walks the stops in their planned order, accumulating distance and
    elapsed time, and writes the new ETA onto each stop. The route is
    mutated in place and returned for convenience.

    The speed used is the mode's rush-hour speed, and the departure time is
    the latest of the courier's shift start and ``earliest_ready`` — the
    instant the last parcel on the route was in hand. A courier cannot
    leave before their shift, and cannot deliver a parcel that has not been
    picked and packed yet.

    **Each stop's own ready time is honoured.** The courier arrives at the
    later of "when they could get here" and "when the parcel was in hand",
    and any wait is charged to the shift. Skipping that wait is how an ETA
    engine comes to report a delivery at 18:00 for a parcel the warehouse
    did not manifest until 21:00 — a forecast that is not merely optimistic
    but physically impossible, and therefore useless for early warning.
    """

    vals = values or DEFAULT_VALUES
    speed = vals.mode_speed_kmh.get(courier.mode.value, 12.0)

    # The route cannot start before the courier's shift, and cannot start
    # before the parcels are in hand. It also cannot start *after* the
    # shift ends — a route that departs after the courier has gone home is
    # not a route at all, and letting that through is how every parcel on
    # it ends up delivered a day late.
    departure = max(courier.shift_start, earliest_ready or courier.shift_start)
    departure = min(departure, courier.shift_end)
    if route.stops and route.stops[0].eta_p50 is not None:
        # Re-planning mid-route: depart from wherever we are now.
        departure = min(s.eta_p50 for s in route.stops if s.eta_p50 is not None)

    clock = departure
    remaining_distance = route.total_distance_km

    for idx, stop in enumerate(route.stops):
        leg_distance = stop.distance_from_prev_km
        remaining_distance = max(0.0, remaining_distance - leg_distance)

        travel_minutes = (leg_distance / max(1.0, speed)) * 60.0
        clock = clock + timedelta(minutes=travel_minutes)

        # Wait for the parcel, if it is not in hand yet.
        if stop.ready_at is not None and stop.ready_at > clock:
            clock = stop.ready_at

        stops_remaining = len(route.stops) - idx
        eta = estimate_stop_eta(
            departure=clock,
            distance_km=leg_distance,
            stops_remaining=stops_remaining,
            service_minutes=stop.service_minutes,
            mode_speed_kmh=speed,
            values=vals,
        )
        stop.eta_p50 = eta.p50
        stop.eta_p90 = eta.p90

        # Advance the clock past this stop's service time.
        clock = eta.p50 + timedelta(minutes=stop.service_minutes)

    return route


def route_fits_shift(route: Route, courier: Courier) -> bool:
    """Whether every stop on the route is served before the shift ends.

    A route whose last stop is served after the courier has gone home is
    not a route — the parcel goes out on someone else's van, a day
    later. The dispatcher is supposed to prevent this, but the dispatcher
    and the router make their own estimates, and this is the check that
    says whether the two actually agreed.
    """

    for stop in route.stops:
        if stop.eta_p50 is None:
            return False
        if stop.eta_p50 > courier.shift_end:
            return False
    return True


def promise_drift(
    promised_at: datetime, eta_p50: datetime, eta_p90: datetime
) -> dict[str, Any]:
    """How far the promise has moved against the forecast.

    ``promise_at`` is frozen at allocation and never moves — that is what
    makes it a promise. The drift therefore only ever widens in one
    direction, and this function reports how much slack is left.

    ``at_risk`` means the P90 has already crossed the promise line: the
    breach is knowable now, before it happens. That is the single most
    valuable output this module produces.
    """

    slack_p50 = (promised_at - eta_p50).total_seconds() / 3600.0
    slack_p90 = (promised_at - eta_p90).total_seconds() / 3600.0
    return {
        "promised_at": promised_at.isoformat(),
        "eta_p50": eta_p50.isoformat(),
        "eta_p90": eta_p90.isoformat(),
        "slack_hours_p50": round(slack_p50, 2),
        "slack_hours_p90": round(slack_p90, 2),
        "at_risk": slack_p90 < 0,
        "breached": slack_p50 < 0,
        "late_by_hours_p50": round(max(0.0, -slack_p50), 2),
    }


def route_promise_drift(
    route: Route, orders_by_id: dict[str, Order]
) -> list[dict[str, Any]]:
    """Drift for every order on a route, worst first.

    The ordering matters: an operations dashboard should show the parcels
    that are already doomed before the ones that are merely tight.
    """

    rows: list[dict[str, Any]] = []
    for stop in route.stops:
        for order_id in stop.order_ids:
            order = orders_by_id.get(order_id)
            if order is None or stop.eta_p50 is None or stop.eta_p90 is None:
                continue
            row = promise_drift(order.promised_at, stop.eta_p50, stop.eta_p90)
            row["order_id"] = order_id
            row["stop_id"] = stop.stop_id
            row["service_level"] = order.service_level.value
            rows.append(row)

    rows.sort(key=lambda r: (r["slack_hours_p90"], r["slack_hours_p50"]))
    return rows


def route_accuracy(route: Route, actual_delivery_times: dict[str, datetime]) -> dict[str, Any]:
    """Compare the forecast against what actually happened.

    Reported in two ways, because they answer different questions:

    - **P50 accuracy**: how close the median forecast was to reality. This is
      the customer experience.
    - **P90 coverage**: how often the P90 was late. A well-calibrated P90
      should be wrong about 10% of the time. If it is wrong 40% of the time,
      the forecast is overconfident and the SLA verdicts built on it are
      meaningless.
    """

    errors_minutes: list[float] = []
    p90_late = 0
    compared = 0

    for stop in route.stops:
        actual = actual_delivery_times.get(stop.stop_id)
        if actual is None or stop.eta_p50 is None or stop.eta_p90 is None:
            continue
        compared += 1
        errors_minutes.append(abs((actual - stop.eta_p50).total_seconds()) / 60.0)
        if actual > stop.eta_p90:
            p90_late += 1

    if not compared:
        return {
            "compared": 0,
            "median_abs_error_minutes": 0.0,
            "mean_abs_error_minutes": 0.0,
            "p90_coverage": 1.0,
            "note": "no completed stops to score",
        }

    errors_minutes.sort()
    mean_error = sum(errors_minutes) / len(errors_minutes)
    median_error = errors_minutes[len(errors_minutes) // 2]
    # Coverage is the share of deliveries that landed *within* the P90.
    coverage = 1.0 - (p90_late / compared)

    return {
        "compared": compared,
        "median_abs_error_minutes": round(median_error, 1),
        "mean_abs_error_minutes": round(mean_error, 1),
        "p90_coverage": round(coverage, 3),
        "p90_late_count": p90_late,
    }
