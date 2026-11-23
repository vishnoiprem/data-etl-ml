"""Measurement harness: the KPI set, printed in one block.

This exists so that a change can be evaluated against the same numbers
every time, rather than against a number remembered from an earlier run.
"""

from __future__ import annotations

import collections

from tms.models import OrderStatus
from tms.service import TmsService


def main() -> None:
    s = TmsService.create()
    w = s.world
    now = w.now

    due = [
        sh
        for sh in w.shipments.values()
        if w.orders[sh.order_id].promised_at <= now
    ]
    delivered = [sh for sh in due if sh.status == OrderStatus.DELIVERED]
    on_time = [
        sh
        for sh in delivered
        if sh.delivered_at is not None
        and sh.delivered_at <= w.orders[sh.order_id].promised_at
    ]
    late = [
        sh
        for sh in delivered
        if sh.delivered_at is not None
        and sh.delivered_at > w.orders[sh.order_id].promised_at
    ]
    returned = [sh for sh in due if sh.status == OrderStatus.RETURNED]
    unrouted = [sh for sh in due if sh.status == OrderStatus.CREATED]

    lateness = [
        (sh.delivered_at - w.orders[sh.order_id].promised_at).total_seconds() / 3600
        for sh in late
    ]
    outcomes = list(s.outcomes.values())
    delivered_outcomes = [o for o in outcomes if o.final_status == OrderStatus.DELIVERED]
    fad = sum(1 for o in outcomes if o.first_attempt_success) / max(
        1, len(delivered_outcomes)
    )

    print(
        f"OTD={len(on_time) / len(due):.4f} "
        f"(delivered-only={len(on_time) / max(1, len(delivered)):.4f}) "
        f"due={len(due)} del={len(delivered)} late={len(late)} "
        f"ret={len(returned)} unrouted={len(unrouted)}"
    )
    print(
        f"FAD={fad:.4f} "
        f"RTO={len(returned) / max(1, len(delivered) + len(returned)):.4f} "
        f"meanlate={sum(lateness) / max(1, len(lateness)):.2f}h"
    )

    deferrals = {k: len(v.deferred_orders) for k, v in sorted(s.plans.items())}
    print(f"deferrals: {deferrals} total={sum(deferrals.values())}")

    past = 0
    for r in s.routes:
        courier = w.couriers.get(r.courier_id)
        if courier is None:
            continue
        if r.stops and r.stops[-1].eta_p90 and r.stops[-1].eta_p90 > courier.shift_end:
            past += 1
    print(f"routes with last stop past shift end: {past} / {len(s.routes)}")

    print(
        "late by service:",
        dict(collections.Counter(w.orders[sh.order_id].service_level.value for sh in late)),
    )
    print(
        "late by promise hour:",
        collections.Counter(
            w.orders[sh.order_id].promised_at.strftime("%H") for sh in late
        ).most_common(8),
    )
    print(
        "late by delivered hour:",
        collections.Counter(sh.delivered_at.strftime("%H") for sh in late).most_common(8),
    )


if __name__ == "__main__":
    main()
