"""The lifecycle: order state machine and the append-only scan ledger.

**The scan log is the truth; the status field is a fold over it.** Every
state change in this system appends a :class:`ScanEvent` and the current
status of a shipment is derived. A mutable status field that can drift away
from the event history is how a TMS ends up claiming a parcel was delivered
when the log says the driver never arrived.

The transition table is explicit and total. Every state has a defined set of
legal successors, and an illegal transition is rejected loudly rather than
being coerced — because a silent coercion in a state machine is how a
shipment ends up jumping from ``PACKED`` straight to ``DELIVERED`` and
nobody notices until a customer does.

Sub-parts
---------
- :data:`TRANSITIONS` — the legal-successor table.
- :class:`ScanLog` — append-only event store.
- :func:`advance_shipment` — validated state transition.
- :func:`shipment_history` — the fold that reconstructs current status.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable

from .models import (
    ATTEMPTABLE_STATUSES,
    TERMINAL_STATUSES,
    OrderStatus,
    ScanEvent,
    ScanType,
    Shipment,
    normalize_carrier_status,
)

# --------------------------------------------------------------------------- #
# Transition table
# --------------------------------------------------------------------------- #

#: Legal successors for each order status.
#:
#: Note that ``FAILED_DELIVERY`` can go back to ``OUT_FOR_DELIVERY`` — that
#: is the retry path, and it is a *forward* transition in the sense that
#: matters (a new attempt happens), not a rollback.
TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.CREATED: frozenset(
        {OrderStatus.ALLOCATED, OrderStatus.CANCELLED}
    ),
    OrderStatus.ALLOCATED: frozenset(
        {OrderStatus.PACKED, OrderStatus.CANCELLED, OrderStatus.RETURNED}
    ),
    OrderStatus.PACKED: frozenset(
        {OrderStatus.PICKED_UP, OrderStatus.CANCELLED, OrderStatus.RETURNED}
    ),
    OrderStatus.PICKED_UP: frozenset(
        {OrderStatus.IN_TRANSIT, OrderStatus.RETURNED}
    ),
    OrderStatus.IN_TRANSIT: frozenset(
        {
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.FAILED_DELIVERY,
            OrderStatus.RETURNED,
        }
    ),
    OrderStatus.OUT_FOR_DELIVERY: frozenset(
        {
            OrderStatus.DELIVERED,
            OrderStatus.FAILED_DELIVERY,
            OrderStatus.IN_TRANSIT,
            OrderStatus.RETURNED,
        }
    ),
    OrderStatus.FAILED_DELIVERY: frozenset(
        {
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.RETURNED,
            OrderStatus.DELIVERED,
        }
    ),
    OrderStatus.DELIVERED: frozenset(),
    OrderStatus.RETURNED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
}


class IllegalTransitionError(RuntimeError):
    """Raised when a caller asks for a state change the machine forbids."""


def can_transition(current: OrderStatus, target: OrderStatus) -> bool:
    """Whether ``current -> target`` is a legal transition."""
    return target in TRANSITIONS.get(current, frozenset())


# --------------------------------------------------------------------------- #
# Scan log
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class ScanLog:
    """An append-only store of logistics events.

    Deliberately has no update or delete. Events are identified by a
    monotonically increasing counter so the order of the log is the order of
    the world, even when two events share a timestamp.
    """

    events: list[ScanEvent] = field(default_factory=list)
    _ids: itertools.count = field(default_factory=lambda: itertools.count(1))

    def append(
        self,
        entity_type: str,
        entity_id: str,
        scan_type: ScanType,
        occurred_at: datetime,
        status: OrderStatus,
        source: str = "tms",
        location_id: str = "",
        actor_id: str | None = None,
        raw_code: str | None = None,
        normalized: bool = True,
        note: str = "",
    ) -> ScanEvent:
        """Append one event and return it."""
        event = ScanEvent(
            scan_id=f"scan-{next(self._ids):08d}",
            entity_type=entity_type,
            entity_id=entity_id,
            scan_type=scan_type,
            occurred_at=occurred_at,
            status=status,
            source=source,
            location_id=location_id,
            actor_id=actor_id,
            raw_code=raw_code,
            normalized=normalized,
            note=note,
        )
        self.events.append(event)
        return event

    def for_entity(self, entity_id: str) -> list[ScanEvent]:
        """All events for one entity, in the order they were recorded."""
        return [e for e in self.events if e.entity_id == entity_id]

    def by_type(self, scan_type: ScanType) -> list[ScanEvent]:
        """All events of one type."""
        return [e for e in self.events if e.scan_type == scan_type]

    def unrecognized(self) -> list[ScanEvent]:
        """Events whose carrier code was not in the mapping table.

        These are not errors — a carrier introducing a new status is a fact
        about the world — but they are the signal that the mapping table
        needs extending, so they are worth surfacing rather than hiding.
        """
        return [e for e in self.events if not e.normalized]

    def timeline(self, entity_id: str) -> list[dict[str, Any]]:
        """A JSON-friendly timeline for one entity."""
        return [
            {
                "scan_id": e.scan_id,
                "scan_type": e.scan_type.value,
                "occurred_at": e.occurred_at.isoformat(),
                "status": e.status.value,
                "source": e.source,
                "location_id": e.location_id,
                "actor_id": e.actor_id,
                "raw_code": e.raw_code,
                "normalized": e.normalized,
                "note": e.note,
            }
            for e in self.for_entity(entity_id)
        ]


# --------------------------------------------------------------------------- #
# Transitions
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class AdvanceResult:
    """The outcome of a state change."""

    ok: bool
    shipment_id: str
    previous: OrderStatus
    current: OrderStatus
    scan: ScanEvent | None = None
    error: str = ""


def advance_shipment(
    shipment: Shipment,
    target: OrderStatus,
    *,
    occurred_at: datetime,
    scan_type: ScanType,
    log: ScanLog,
    source: str = "tms",
    location_id: str = "",
    actor_id: str | None = None,
    raw_code: str | None = None,
    normalized: bool = True,
    note: str = "",
) -> AdvanceResult:
    """Move a shipment to a new status, recording the transition.

    The shipment is updated in place only if the transition is legal. An
    illegal transition returns a failed result rather than raising, because
    the caller is usually a batch job that should skip the bad shipment and
    keep going — but it is returned as a failure, never silently swallowed.
    """

    previous = shipment.status
    if not can_transition(previous, target):
        return AdvanceResult(
            ok=False,
            shipment_id=shipment.shipment_id,
            previous=previous,
            current=previous,
            error=(
                f"{shipment.shipment_id}: {previous.value} -> {target.value} "
                f"is not a legal transition"
            ),
        )

    shipment.status = target
    scan = log.append(
        entity_type="shipment",
        entity_id=shipment.shipment_id,
        scan_type=scan_type,
        occurred_at=occurred_at,
        status=target,
        source=source,
        location_id=location_id,
        actor_id=actor_id,
        raw_code=raw_code,
        normalized=normalized,
        note=note,
    )
    return AdvanceResult(
        ok=True,
        shipment_id=shipment.shipment_id,
        previous=previous,
        current=target,
        scan=scan,
    )


def apply_carrier_update(
    shipment: Shipment,
    raw_code: str,
    *,
    occurred_at: datetime,
    log: ScanLog,
    source: str | None = None,
    location_id: str = "",
) -> AdvanceResult:
    """Apply an inbound carrier status update.

    The carrier code is normalised, and the raw code is retained either way.
    An unrecognised code still moves the shipment — the parcel physically
    moved — but the event is flagged so the mapping gap is visible.
    """

    carrier = shipment.carrier
    status, recognized = normalize_carrier_status(carrier, raw_code)

    if not recognized:
        # Unknown code: keep the shipment where it is rather than guessing a
        # transition, but record the event so the gap is auditable.
        scan = log.append(
            entity_type="shipment",
            entity_id=shipment.shipment_id,
            scan_type=ScanType.IN_TRANSIT,
            occurred_at=occurred_at,
            status=shipment.status,
            source=source or carrier,
            location_id=location_id,
            raw_code=raw_code,
            normalized=False,
            note=f"unrecognized carrier code {raw_code!r} from {carrier}",
        )
        return AdvanceResult(
            ok=False,
            shipment_id=shipment.shipment_id,
            previous=shipment.status,
            current=shipment.status,
            scan=scan,
            error=f"unrecognized carrier status {raw_code!r} for {carrier}",
        )

    scan_type = _SCAN_TYPE_FOR_STATUS.get(status, ScanType.IN_TRANSIT)
    return advance_shipment(
        shipment,
        status,
        occurred_at=occurred_at,
        scan_type=scan_type,
        log=log,
        source=source or carrier,
        location_id=location_id,
        raw_code=raw_code,
        normalized=True,
    )


#: Which scan type accompanies a normalized status.
_SCAN_TYPE_FOR_STATUS: dict[OrderStatus, ScanType] = {
    OrderStatus.CREATED: ScanType.ORDER_CONFIRMED,
    OrderStatus.ALLOCATED: ScanType.ALLOCATED,
    OrderStatus.PACKED: ScanType.PACKED,
    OrderStatus.PICKED_UP: ScanType.PICKED_UP,
    OrderStatus.IN_TRANSIT: ScanType.LINE_HAUL_DEPARTED,
    OrderStatus.OUT_FOR_DELIVERY: ScanType.OUT_FOR_DELIVERY,
    OrderStatus.DELIVERED: ScanType.DELIVERED,
    OrderStatus.FAILED_DELIVERY: ScanType.NDR_RAISED,
    OrderStatus.RETURNED: ScanType.RETURNED,
    OrderStatus.CANCELLED: ScanType.CANCELLED,
}


def shipment_history(log: ScanLog, shipment_id: str) -> list[ScanEvent]:
    """The event history for a shipment."""
    return log.for_entity(shipment_id)


def reconstruct_status(log: ScanLog, shipment_id: str) -> OrderStatus | None:
    """Fold the scan log back into the current status of a shipment.

    This is the check that the append-only log and the mutable status field
    agree. If they ever disagree, the log wins — the status field is a
    cache of the log, not the other way round.
    """

    events = log.for_entity(shipment_id)
    if not events:
        return None
    return events[-1].status


def assert_log_consistent(shipments: Iterable[Shipment], log: ScanLog) -> list[str]:
    """Return a list of shipments whose status disagrees with their log.

    An empty list means the invariant holds.
    """

    problems: list[str] = []
    for shipment in shipments:
        derived = reconstruct_status(log, shipment.shipment_id)
        if derived is not None and derived != shipment.status:
            problems.append(
                f"{shipment.shipment_id}: status={shipment.status.value} "
                f"but log says {derived.value}"
            )
    return problems


def is_attemptable(status: OrderStatus) -> bool:
    """Whether a delivery attempt may be made from this status."""
    return status in ATTEMPTABLE_STATUSES


def is_terminal(status: OrderStatus) -> bool:
    """Whether the order has reached a final state."""
    return status in TERMINAL_STATUSES
