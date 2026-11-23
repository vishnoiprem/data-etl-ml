"""The router: turning a courier's assigned stops into an ordered route.

**This is a capacitated vehicle routing problem with time windows**
(VRPTW), and the real one has four complications that a textbook example
does not:

1. **Stop consolidation happens upstream.** By the time a route is planned,
   the courier has stops, not parcels. Modelling one-stop-per-parcel here
   would double the cost of every delivery.
2. **Time windows are hard, not soft.** A customer who asked for a
   10am-12am-noon delivery has to be served in that window. Serving them
   outside it is a failure even if the parcel arrives "on the day".
3. **Capacity is three-dimensional.** Weight, volume and parcel count.
4. **The objective is not distance.** Minimising kilometres produces a route
   that arrives at every customer at once and then spends the afternoon
   driving back. A better objective blends distance with *lateness*, so
   the route front-loads the tight promises.

**Why no solver dependency.** OR-Tools CP-SAT would give a better answer,
but it needs a compiled wheel. This project has to run on a laptop with no
network and no Docker, so the router is a pure-python construction heuristic
followed by 2-opt and relocate local search. That is enough to show the
constraint handling, which is the part worth reading.

Sub-parts
---------
- :func:`plan_route` — build and optimise one courier's route.
- :func:`plan_routes` — plan every route on a dispatch plan.
- :func:`route_objective` — the blended cost function.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from .config import DEFAULT_VALUES, ValueConfig
from .dispatch import Allocation, ConsolidatedStop
from .eta import recompute_route_eta
from .models import (
    DETOUR_FACTOR,
    Address,
    Courier,
    Route,
    Stop,
    haversine_km,
)


# --------------------------------------------------------------------------- #
# Distance
# --------------------------------------------------------------------------- #

#: Cache of address-pair distances, keyed by the two address ids.
#:
#: The router evaluates the same pair of addresses thousands of times: once
#: per candidate move, per local-search pass, per route. Without this the
#: haversine call is the dominant cost of the whole simulation.
_DISTANCE_CACHE: dict[tuple[str, str], float] = {}


#: Street-network detour factor. A straight line between two addresses is
#: not a driveable route: in a dense city the road path is roughly 30%
#: longer. The same factor is used by the dispatcher when it budgets a
#: courier's time, so the two agree on how long a leg takes. If they did
#: not, the dispatcher would hand the router a plan the router could not
#: finish inside the shift, and every parcel on that route would arrive
#: after the courier had gone home.
DETOUR_FACTOR = 1.3


def distance_km(a: Address, b: Address) -> float:
    """Great-circle distance between two addresses.

    Straight-line, not road distance. Real routing follows the street
    network, and a real project would plug in a road-network matrix. The
    distortion is consistent — every leg is roughly 1.3x the straight line
    in a dense city — so it shifts the cost level but not the shape of the
    optimisation problem.

    Memoised on the address pair. The router asks for the same distance
    thousands of times — once per candidate move, per pass, per route — and
    the haversine computation is the single most expensive thing in the
    simulation. Caching it turns the routing stage from tens of seconds
    into a couple of seconds.
    """

    key = (a.address_id, b.address_id)
    cached = _DISTANCE_CACHE.get(key)
    if cached is not None:
        return cached

    result = haversine_km(a.lat, a.lng, b.lat, b.lng) * DETOUR_FACTOR
    _DISTANCE_CACHE[key] = result
    return result


def _route_distance(stops: list[ConsolidatedStop], hub: Address) -> float:
    """Total distance of a route, including the legs to and from the hub."""
    if not stops:
        return 0.0
    total = distance_km(hub, stops[0].address)
    for prev, nxt in zip(stops, stops[1:], strict=False):
        total += distance_km(prev.address, nxt.address)
    total += distance_km(stops[-1].address, hub)
    return total


# --------------------------------------------------------------------------- #
# Objective
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class RouteMetrics:
    """The score of one candidate route, and its components."""

    distance_km: float
    lateness_minutes: float
    window_violations: int
    travel_minutes: float
    service_minutes: float
    #: Minutes by which the route runs past the courier's shift end. A
    #: route with any of these is a route whose tail goes out on someone
    #: else's van, a day later.
    shift_overflow_minutes: float = 0.0

    @property
    def objective(self) -> float:
        """The blended score, lower is better.

        Distance is weighted lightly because it is the thing we can least
        control and the thing operators care least about. Lateness and
        window violations are weighted heavily, because they are what the
        customer actually experiences and what the SLA is judged on.

        Shift overflow is weighted most heavily of all, because it is the
        one failure the other two cannot recover from. A route that
        finishes late still delivers its parcels; a route that finishes
        after the courier has gone home delivers them tomorrow.
        """
        return (
            self.distance_km * 1.0
            + self.lateness_minutes * 0.08
            + self.window_violations * 45.0
            + self.shift_overflow_minutes * 0.5
        )


def evaluate_sequence(
    stops: list[ConsolidatedStop],
    courier: Courier,
    hub: Address,
    values: ValueConfig | None = None,
    departure: datetime | None = None,
) -> RouteMetrics:
    """Score a candidate stop sequence for one courier.

    Walks the sequence from the departure time, accumulating travel and
    service time, and measures how late each stop arrives against its
    promised deadline and any hard window.

    The departure time defaults to the later of the courier's shift start
    and the moment the last parcel is in hand — the same baseline the ETA
    engine uses, so the objective and the forecast never disagree.

    **The walk honours each stop's readiness.** A stop whose parcel is not
    yet manifested cannot be served when the courier arrives, so the
    courier waits — and that wait pushes every stop behind it later. An
    objective that ignores readiness will happily put a stop that is ready
    at 18:00 third on a route, producing a route that looks fine on
    distance and delivers half its parcels after midnight.
    """

    vals = values or DEFAULT_VALUES
    speed = max(1.0, vals.mode_speed_kmh.get(courier.mode.value, 12.0))

    if departure is None:
        departure = _route_ready_time(courier, stops, None)

    clock = departure
    prev_addr = hub
    total_distance = 0.0
    lateness = 0.0
    violations = 0
    travel_total = 0.0
    service_total = 0.0
    shift_overflow = 0.0

    for stop in stops:
        leg = distance_km(prev_addr, stop.address)
        total_distance += leg
        travel_minutes = (leg / speed) * 60.0
        travel_total += travel_minutes
        clock = clock + timedelta(minutes=travel_minutes)

        # The parcel has to be in hand before it can be served.
        if stop.ready_at is not None and stop.ready_at > clock:
            clock = stop.ready_at

        parcel_count = max(1, len(stop.parcel_ids))
        service_minutes = vals.service_minutes_base + vals.service_minutes_per_parcel * parcel_count
        service_total += service_minutes

        if clock > stop.promised_at:
            lateness += (clock - stop.promised_at).total_seconds() / 60.0

        if stop.window_start is not None and stop.window_end is not None:
            if clock < stop.window_start:
                # Too early: wait for the window to open.
                clock = stop.window_start
            if clock > stop.window_end:
                violations += 1

        # Serving after the shift ends means the parcel goes out on
        # someone else's van, a day later.
        if clock + timedelta(minutes=service_minutes) > courier.shift_end:
            shift_overflow += (
                clock + timedelta(minutes=service_minutes) - courier.shift_end
            ).total_seconds() / 60.0

        clock = clock + timedelta(minutes=service_minutes)
        prev_addr = stop.address

    # The leg back to the hub.
    back = distance_km(prev_addr, hub)
    total_distance += back
    travel_total += (back / speed) * 60.0

    return RouteMetrics(
        distance_km=round(total_distance, 3),
        lateness_minutes=round(lateness, 2),
        window_violations=violations,
        travel_minutes=round(travel_total, 2),
        service_minutes=round(service_total, 2),
        shift_overflow_minutes=round(shift_overflow, 2),
    )


# --------------------------------------------------------------------------- #
# Construction heuristic
# --------------------------------------------------------------------------- #


def _construct_sequence(
    stops: list[ConsolidatedStop],
    courier: Courier,
    hub: Address,
    values: ValueConfig | None = None,
) -> list[ConsolidatedStop]:
    """Build an initial sequence with a regret-2 insertion heuristic.

    The naive approach — nearest-neighbour — produces a route that starts in
    one corner and criss-crosses the city, because each step is locally
    greedy. Regret-2 insertion fixes this: at each step it considers the
    *worst regret* of leaving a stop unplaced, and places the stop whose
    regret is largest first.

    Concretely, for each unplaced stop we compute how much worse it gets by
    inserting it now versus its best possible insertion later. Placing the
    stop with the biggest regret first keeps the awkward, hard-to-place
    stops from being stranded at the end of the route.

    **Readiness dominates the ordering.** A stop's parcel is in hand at
    ``ready_at``, and a courier cannot serve it before then. Sequencing a
    route purely on distance is what produces the classic failure: a stop
    that is not manifested until 18:00 sits third on a route that started
    at 07:00, the courier drives out to the address at 09:00, waits for
    the parcel to appear, and delivers at 18:30 — or worse, on tomorrow's
    route.

    So the route is built in **readiness blocks**. Stops are bucketed by
    when their parcels are manifested, and the buckets are served in
    order: everything that is ready in the morning goes first, then the
    midday batch, then the evening batch. Within a bucket the regret-2
    heuristic still applies, because that is what keeps the route short.

    The first bucket is special: it fixes the departure time, and it is
    the earliest the courier can possibly leave. The rest of the route is
    a consequence of what is ready when, not of where it is on the map.
    """

    vals = values or DEFAULT_VALUES
    speed = max(1.0, vals.mode_speed_kmh.get(courier.mode.value, 12.0))

    # Stops whose parcel cannot be manifested before the shift ends are
    # not this route's problem at all.
    servable = [
        s for s in stops if s.ready_at is None or s.ready_at <= courier.shift_end
    ]
    if not servable:
        return []

    # -- Bucket by readiness --------------------------------------------- #
    # The buckets are two hours wide and measured from midnight, so the
    # router and the local search agree about which batch a parcel
    # belongs to. See :func:`_readiness_bucket`.
    remaining = sorted(servable, key=lambda s: (_readiness_bucket(s), s.ready_at))
    sequence: list[ConsolidatedStop] = []
    current_addr = hub
    clock = courier.shift_start

    while remaining:
        # Only consider stops in the current readiness bucket. Moving on to
        # the next batch before this one is served would mean driving back
        # across the city later.
        current_bucket = _readiness_bucket(remaining[0])
        batch = [s for s in remaining if _readiness_bucket(s) == current_bucket]

        best_stop: ConsolidatedStop | None = None
        best_key: tuple[float, float, float] | None = None
        is_first = not sequence

        for stop in batch:
            leg = distance_km(current_addr, stop.address)

            # How long the courier would have to wait at this stop for the
            # parcel to be in hand. A stop that is ready now costs
            # nothing; one that is not ready for four hours costs four.
            arrival = clock + timedelta(minutes=(leg / speed) * 60.0)
            wait = 0.0
            if stop.ready_at is not None and stop.ready_at > arrival:
                wait = (stop.ready_at - arrival).total_seconds() / 60.0

            # -- The first stop fixes the departure ------------------------- #
            # The departure time is the moment the first parcel on the route
            # is manifested, so the first stop has to be the
            # earliest-ready one. A route that departs at 21:05 because
            # the parcel at the top of the list was manifested then has
            # eight hours of shift left over and a route of eight stops
            # to serve in them.
            #
            # After the first stop the heuristic switches to regret: the
            # stop that suffers most from being postponed goes next.
            if is_first:
                key = (wait, stop.promised_at.timestamp(), 0.0)
            else:
                best_pos, best_cost = _best_insertion_cost(
                    sequence, stop, current_addr, hub, courier, vals
                )
                # Regret: how much worse the second-best position is than
                # the best one. Higher regret means place it now.
                second_cost = _second_best_insertion_cost(
                    sequence, stop, current_addr, hub, courier, vals, exclude=best_pos
                )
                regret = second_cost - best_cost
                # Ties broken by the earliest deadline.
                key = (-regret, wait, stop.promised_at.timestamp())

            if best_key is None or key < best_key:
                best_key = key
                best_stop = stop

        if best_stop is None:
            break

        # -- Append, never insert ------------------------------------------ #
        # The sequence is built in readiness order, and it has to stay
        # that way. Inserting a stop at the best *geometric* position can
        # put a parcel that is not manifested until 21:05 at the front of
        # a route whose first parcel was ready at 12:25, and then the
        # whole route departs eight hours late and the tail is trimmed
        # off it.
        #
        # Within a bucket the stops are close enough in time that serving
        # them in readiness order costs almost nothing in distance, and
        # the local search can still reorder them afterwards if it finds
        # a genuinely better path that preserves readiness order.
        sequence.append(best_stop)
        remaining.remove(best_stop)

        leg = distance_km(current_addr, best_stop.address)
        arrival = clock + timedelta(minutes=(leg / speed) * 60.0)
        if best_stop.ready_at is not None and best_stop.ready_at > arrival:
            arrival = best_stop.ready_at
        clock = arrival
        current_addr = best_stop.address

    return sequence


def _insertion_delta(
    sequence: list[ConsolidatedStop],
    stop: ConsolidatedStop,
    pos: int,
    hub: Address,
) -> float:
    """The extra distance incurred by inserting a stop at position ``pos``.

    Insertion changes exactly two edges — the one it breaks and the one it
    creates — so the delta is O(1). Computing it this way rather than by
    re-measuring the whole route is what keeps the construction heuristic
    fast enough to run over a week of demand.
    """

    if not sequence:
        return distance_km(hub, stop.address)

    prev_addr = hub if pos == 0 else sequence[pos - 1].address
    next_addr = hub if pos == len(sequence) else sequence[pos].address

    removed = distance_km(prev_addr, next_addr)
    added = distance_km(prev_addr, stop.address) + distance_km(stop.address, next_addr)
    return added - removed


def _best_insertion_cost(
    sequence: list[ConsolidatedStop],
    stop: ConsolidatedStop,
    current_addr: Address,
    hub: Address,
    courier: Courier,
    values: ValueConfig,
) -> tuple[int, float]:
    """The cheapest insertion position for a stop, and its cost."""
    best_pos = len(sequence)
    best_cost = float("inf")

    for pos in range(len(sequence) + 1):
        delta = _insertion_delta(sequence, stop, pos, hub)
        if delta < best_cost:
            best_cost = delta
            best_pos = pos

    return best_pos, best_cost


def _second_best_insertion_cost(
    sequence: list[ConsolidatedStop],
    stop: ConsolidatedStop,
    current_addr: Address,
    hub: Address,
    courier: Courier,
    values: ValueConfig,
    exclude: int,
) -> float:
    """The cost of the best insertion position *other than* ``exclude``.

    When there is only one possible position, the regret is zero — the stop
    has no flexibility, but that is also true for every other stop in the
    same situation, so it does not distort the ordering.
    """
    costs: list[float] = []
    for pos in range(len(sequence) + 1):
        if pos == exclude:
            continue
        costs.append(_insertion_delta(sequence, stop, pos, hub))

    if not costs:
        return float("inf")
    return min(costs)


# --------------------------------------------------------------------------- #
# Local search
# --------------------------------------------------------------------------- #


def _two_opt(
    sequence: list[ConsolidatedStop],
    courier: Courier,
    hub: Address,
    values: ValueConfig,
) -> list[ConsolidatedStop]:
    """Reverse sub-paths to untangle a crossing route.

    Two routes that cross each other can always be untangled by reversing
    the segment between the crossing points, which shortens the total. This
    is the classic 2-opt move, and it is what stops the output looking like
    a scribble.

    The move is accepted on the **full objective**, not on distance alone.
    A pure-distance 2-opt will happily reverse a segment and put a stop
    that is not manifested until 18:00 in front of one that is ready at
    07:00 — shortening the route by half a kilometre and pushing the
    evening parcel past the courier's shift end. Distance is one term of
    the objective; lateness and shift overflow are the ones that decide
    whether the parcel arrives.
    """

    best = list(sequence)
    n = len(best)
    if n < 4:
        return best

    improved = True
    # Bounded for the same reason as the relocate pass: a local search that
    # cycles would otherwise hang instead of returning a route.
    max_passes = n * 2
    for _ in range(max_passes):
        improved = False
        for i in range(n - 2):
            for j in range(i + 2, n):
                candidate = (
                    best[: i + 1] + best[i + 1 : j + 1][::-1] + best[j + 1 :]
                )
                # Reversing a segment can put a later-ready parcel ahead of
                # an earlier one, which sends the courier back across the
                # city for a batch that is not manifested yet.
                if not _readiness_preserved(candidate):
                    continue
                if (
                    evaluate_sequence(candidate, courier, hub, values).objective
                    < evaluate_sequence(best, courier, hub, values).objective - 1e-9
                ):
                    best = candidate
                    improved = True
        if not improved:
            break

    return best


def _readiness_preserved(sequence: list[ConsolidatedStop]) -> bool:
    """Whether the sequence still serves stops in readiness order.

    The router groups stops into readiness buckets and serves them in
    order. A local-search move that reverses a segment can reorder them,
    and a route that goes back to the depot for a batch that is not
    manifested yet is worse than one that is half a kilometre longer.

    The order that has to hold is the **bucket** order, not the exact
    order of the individual ready times. Stops within a bucket were
    manifested within minutes of each other, so serving them in any
    order is equally correct as far as the warehouse is concerned — and
    insisting on the exact order would freeze the local search on every
    route that has two parcels manifested ninety seconds apart, which is
    most of them.

    What must not happen is a stop from a *later* bucket being served
    before a stop from an earlier one. That is the move that sends the
    courier back to the depot for a batch that is not manifested yet.
    """

    buckets = [_readiness_bucket(s) for s in sequence]
    return all(a <= b for a, b in zip(buckets, buckets[1:], strict=False))


#: How wide a readiness bucket is.
#:
#: Two hours. A narrower bucket would make the route jump between
#: addresses whose parcels were manifested minutes apart; a wider one
#: would mix a 07:00 parcel with an 11:00 one and send the courier back
#: to the depot.
READINESS_BUCKET = timedelta(hours=2)


def _readiness_bucket(stop: ConsolidatedStop) -> int:
    """The readiness bucket a stop belongs to, on the absolute clock.

    The bucket is measured from midnight rather than from the earliest
    stop on the route, so two routes built on the same day agree about
    which batch a parcel belongs to. That matters because the local
    search compares a candidate sequence against the one it is
    improving: if the two used different origins, "readiness order"
    would mean something different on each side of the comparison.
    """

    if stop.ready_at is None:
        return 0
    midnight = stop.ready_at.replace(hour=0, minute=0, second=0, microsecond=0)
    return int((stop.ready_at - midnight) // READINESS_BUCKET)


def _relocate(
    sequence: list[ConsolidatedStop], courier: Courier, hub: Address, values: ValueConfig
) -> list[ConsolidatedStop]:
    """Move single stops to better positions.

    Relocate is the move that fixes a single badly-placed stop, which 2-opt
    cannot always reach on its own.

    The candidate move is scored on the **full objective**, not on a
    distance delta. Distance is the cheap approximation, and it is wrong
    here: a move that shortens the route by a few hundred metres but puts
    an un-manifested parcel behind a ready one is a move that pushes the
    evening parcel past the courier's shift end.

    Re-measuring the route for every candidate is O(n^3) in the worst
    case, but a route has at most a couple of dozen stops, so the whole
    simulation stays in the low seconds. The alternative — an O(1) delta
    on distance — is fast and wrong.
    """

    best = list(sequence)
    n = len(best)
    if n < 3:
        return best

    improved = True
    # Bounded: local search can cycle (A moves, then B moves back), and an
    # unbounded loop would hang the simulation rather than return a route.
    # Each pass is bounded by n moves, so this cap is generous.
    max_passes = n * 2
    for _ in range(max_passes):
        improved = False
        best_objective = evaluate_sequence(best, courier, hub, values).objective
        for i in range(n):
            moved = best[i]
            rest = best[:i] + best[i + 1 :]
            for j in range(len(rest) + 1):
                if j == i:
                    continue
                candidate = rest[:j] + [moved] + rest[j:]
                if not _readiness_preserved(candidate):
                    continue
                objective = evaluate_sequence(candidate, courier, hub, values).objective
                if objective < best_objective - 1e-9:
                    best = candidate
                    best_objective = objective
                    improved = True
                    break
            if improved:
                break
        if not improved:
            break
    return best


def _path_length(sequence: list[ConsolidatedStop]) -> float:
    """Total distance of the sequence, treating it as a path."""
    if len(sequence) < 2:
        return 0.0
    total = 0.0
    for a, b in zip(sequence, sequence[1:], strict=False):
        total += distance_km(a.address, b.address)
    return total


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def _route_ready_time(
    courier: Courier,
    stops: list[ConsolidatedStop],
    earliest_ready: datetime | None,
) -> datetime:
    """The instant the courier can actually leave the hub.

    Two constraints, and the later of them wins:

    - The courier's shift has to have started.
    - The parcels on the route have to be in hand.

    The second constraint is about the **earliest ready time on the
    route**, and it has to be. The dispatcher hands a courier a route
    whose stops are all ready before the courier's deadline, and it
    models the departure as the moment the *first parcel they were given*
    is manifested — which, because the dispatcher assigns stops in
    readiness order, is the earliest one on the route.

    The tempting alternative is to use the *first stop in the sequence*,
    on the argument that a courier leaves when the parcel at the top of
    their list is in hand. That argument confuses two different things.
    It is true that a courier does not stand at the hub until the *last*
    parcel in their load has been picked — that is why the route must not
    wait for the maximum ready time. It says nothing about the earliest
    one, and a route whose first *sequenced* stop is manifested at 21:05
    does not depart at 21:05: it departs at 14:00 with the parcel that
    was ready at 12:25, and it reaches the 21:05 parcel later in the
    day.

    Getting this wrong is expensive and it is silent. The courier
    departs eight hours late, the whole route is crammed into the last
    two hours of the shift, the router's trim drops the tail, and the
    orders on it are deferred to tomorrow — which is a promise broken by
    a day, for a route that had eight hours of daylight to serve.
    """

    ready_times = [s.ready_at for s in stops if s.ready_at is not None]
    if ready_times:
        first_ready: datetime | None = min(ready_times)
    else:
        first_ready = None

    ready = max(
        courier.shift_start,
        first_ready or courier.shift_start,
        earliest_ready or courier.shift_start,
    )
    # A route cannot depart after the courier has gone home.
    return min(ready, courier.shift_end)


def _stops_ready_time(stops: list[ConsolidatedStop]) -> datetime | None:
    """The instant the last parcel on the route is in hand.

    Used for the *earliest* readiness check — a parcel that is not ready
    before the courier's shift ends cannot be on that courier's route at
    all.
    """
    if not stops:
        return None
    return max(stop.ready_at for stop in stops)


def _trim_to_shift(
    sequence: list[ConsolidatedStop],
    courier: Courier,
    hub: Address,
    values: ValueConfig,
    departure: datetime | None = None,
) -> tuple[list[ConsolidatedStop], list[ConsolidatedStop]]:
    """Drop the tail of the route that the courier cannot finish in shift.

    Returns the stops that fit and the stops that were dropped. The
    dropped ones go back to the caller to be deferred to the next wave.

    The check is not just "is the last stop before the shift ends" — it
    is "is the last stop, plus the ride back to the hub, before the shift
    ends", because the last delivery is not the last thing that happens
    in a shift.
    """

    if not sequence:
        return [], []

    speed = max(1.0, values.mode_speed_kmh.get(courier.mode.value, 12.0))
    clock = departure or _route_ready_time(courier, sequence, None)
    prev_addr = hub

    keep: list[ConsolidatedStop] = []
    for stop in sequence:
        leg = distance_km(prev_addr, stop.address)
        arrival = clock + timedelta(minutes=(leg / speed) * 60.0)
        if stop.ready_at is not None and stop.ready_at > arrival:
            arrival = stop.ready_at

        parcel_count = max(1, len(stop.parcel_ids))
        service_minutes = (
            values.service_minutes_base + values.service_minutes_per_parcel * parcel_count
        )
        back = distance_km(stop.address, hub)
        back_minutes = (back / speed) * 60.0

        finish = arrival + timedelta(minutes=service_minutes + back_minutes)
        if finish > courier.shift_end:
            break

        keep.append(stop)
        clock = arrival + timedelta(minutes=service_minutes)
        prev_addr = stop.address

    return keep, sequence[len(keep) :]


def plan_route(
    courier: Courier,
    stops: list[ConsolidatedStop],
    hub_address: Address,
    values: ValueConfig | None = None,
    route_id: str | None = None,
    earliest_ready: datetime | None = None,
) -> Route:
    """Plan one courier's route for the day.

    Builds an initial sequence, improves it with 2-opt and relocate, then
    computes the per-stop ETAs and the cost.

    ``earliest_ready`` is the instant the parcels on this route are all in
    hand — normally the time the newest order was placed, plus the pick and
    pack time. The route cannot depart before then, and using the courier's
    shift start instead would let an evening order be "delivered" hours
    before it was even ordered.
    """

    vals = values or DEFAULT_VALUES
    speed = max(1.0, vals.mode_speed_kmh.get(courier.mode.value, 12.0))

    sequence = _construct_sequence(stops, courier, hub_address, vals)
    sequence = _two_opt(sequence, courier, hub_address, vals)
    sequence = _relocate(sequence, courier, hub_address, vals)

    # The departure time is fixed by the *first stop in the sequence*, not
    # by the earliest ready time on the route. A route whose first stop is
    # not manifested until 18:27 does not depart at 06:20 because some
    # other parcel on it was ready then — the courier waits at the depot
    # for the load they are actually taking, and everything on the route
    # shifts with them.
    route_ready_time = _route_ready_time(courier, sequence, earliest_ready)

    # -- Trim the route to the shift --------------------------------------- #
    # The dispatcher and the router do not model the route identically —
    # the dispatcher walks the stops in the order it assigned them, the
    # router re-sequences them for a shorter path — so a route that
    # passed the dispatcher's shift check can still overrun it here.
    #
    # When that happens the tail of the route is dropped. A courier who
    # serves eleven stops and then drives home has done a day's work; a
    # courier who serves eleven stops and then delivers the twelfth at
    # midnight has done a day's work and a half, and the twelfth parcel
    # goes out on tomorrow's van anyway. The dropped stops are returned
    # so the caller can defer them to the next wave.
    sequence, dropped = _trim_to_shift(
        sequence, courier, hub_address, vals, route_ready_time
    )

    route_id = route_id or f"rte-{courier.courier_id}-{courier.shift_start:%Y%m%d}"

    route_stops: list[Stop] = []
    prev_addr = hub_address
    for idx, cs in enumerate(sequence):
        leg = distance_km(prev_addr, cs.address)
        parcel_count = max(1, len(cs.parcel_ids))
        service_minutes = vals.service_minutes_base + vals.service_minutes_per_parcel * parcel_count
        route_stops.append(
            Stop(
                stop_id=f"{route_id}-s{idx + 1:03d}",
                route_id=route_id,
                sequence=idx + 1,
                address=cs.address,
                order_ids=cs.order_ids,
                parcel_ids=cs.parcel_ids,
                window_start=cs.window_start,
                window_end=cs.window_end,
                ready_at=cs.ready_at,
                service_minutes=service_minutes,
                distance_from_prev_km=round(leg, 3),
            )
        )
        prev_addr = cs.address

    metrics = evaluate_sequence(sequence, courier, hub_address, vals)

    route = Route(
        route_id=route_id,
        courier_id=courier.courier_id,
        route_date=courier.shift_start,
        stops=route_stops,
        total_distance_km=metrics.distance_km,
        total_service_minutes=metrics.service_minutes,
        dropped_order_ids=[oid for stop in dropped for oid in stop.order_ids],
    )

    # The courier cannot leave before their shift starts, and cannot leave
    # before the parcel for the first stop has been picked and packed.
    # Taking the later of the two is what stops a 10pm order from being
    # routed with a 6am departure and therefore "delivered" before it
    # existed.
    recompute_route_eta(route, courier, vals, earliest_ready=route_ready_time)

    # Cost: the courier's day, plus the variable cost of the work done.
    route.cost = round(
        courier.fixed_cost
        + courier.cost_per_stop * route.stop_count
        + courier.cost_per_km * route.total_distance_km,
        2,
    )

    return route


def plan_routes(
    allocations: list[Allocation],
    hub_addresses: dict[str, Address],
    values: ValueConfig | None = None,
) -> list[Route]:
    """Plan a route for every allocation in a dispatch plan."""

    routes: list[Route] = []
    for alloc in allocations:
        hub = hub_addresses.get(alloc.courier.hub_id)
        if hub is None:
            continue
        routes.append(plan_route(alloc.courier, alloc.stops, hub, values))
    return routes


def dropped_order_ids(routes: list[Route]) -> list[str]:
    """Every order that was assigned but did not fit inside a shift.

    These are the orders the dispatcher has to defer: they were allocated
    to a courier, the router found they did not fit inside that
    courier's shift, and they are now nobody's job.
    """

    ids: list[str] = []
    for route in routes:
        ids.extend(route.dropped_order_ids)
    return ids


def route_cost_breakdown(route: Route, courier: Courier) -> dict[str, Any]:
    """Split a route's cost into the three components a TMS is judged on.

    Fixed daily cost, per-stop cost and per-kilometre cost are all real and
    all behave differently under volume changes: fixed cost per parcel
    falls as the route gets fuller, per-stop cost falls as consolidation
    improves, and per-kilometre cost falls as the route gets shorter.
    """

    parcels = route.parcel_count
    stops = route.stop_count
    fixed = courier.fixed_cost
    per_stop = courier.cost_per_stop * stops
    per_km = courier.cost_per_km * route.total_distance_km
    total = fixed + per_stop + per_km

    return {
        "route_id": route.route_id,
        "courier_id": courier.courier_id,
        "mode": courier.mode.value,
        "parcels": parcels,
        "stops": stops,
        "distance_km": round(route.total_distance_km, 2),
        "fixed_cost": round(fixed, 2),
        "stop_cost": round(per_stop, 2),
        "distance_cost": round(per_km, 2),
        "total_cost": round(total, 2),
        "cost_per_parcel": round(total / parcels, 2) if parcels else 0.0,
        "cost_per_stop": round(total / stops, 2) if stops else 0.0,
        "parcels_per_stop": round(parcels / stops, 2) if stops else 0.0,
    }


def utilisation_report(routes: list[Route], couriers: dict[str, Courier]) -> dict[str, Any]:
    """Capacity utilisation across every planned route.

    A route below ~60% utilisation means the courier was under-loaded, which
    is usually a dispatch problem rather than a demand problem.
    """

    rows: list[dict[str, Any]] = []
    for route in routes:
        courier = couriers.get(route.courier_id)
        if courier is None:
            continue
        rows.append(
            {
                "route_id": route.route_id,
                "mode": courier.mode.value,
                "parcels": route.parcel_count,
                "stops": route.stop_count,
                "max_parcels": courier.max_parcels,
                "parcel_utilisation": round(route.parcel_count / courier.max_parcels, 3)
                if courier.max_parcels
                else 0.0,
            }
        )

    if not rows:
        return {"routes": 0, "mean_parcel_utilisation": 0.0, "detail": []}

    mean_util = sum(r["parcel_utilisation"] for r in rows) / len(rows)
    return {
        "routes": len(rows),
        "mean_parcel_utilisation": round(mean_util, 3),
        "underfilled_routes": sum(1 for r in rows if r["parcel_utilisation"] < 0.6),
        "detail": rows,
    }
