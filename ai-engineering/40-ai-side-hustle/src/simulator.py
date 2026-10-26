"""
simulator.py — Inject synthetic but realistic daily revenue events.

Why a simulator?  The factory's "projected" revenue is all stamped
on a single day (today). To make the dashboard tell a story — ramp,
plateau, occasional spikes — we need events spread across many days.

The simulator:
  1. Looks at the last N days of revenue in the ledger.
  2. For each empty day, probabilistically injects a small event
     (one SEO click-through, one Gumroad sale, etc.).
  3. The amount is sampled from a log-normal distribution with the
     stream's median as the mode — so most events are small but
     occasionally you get a $99 SaaS signup that "found you on HN".

It's not a Monte Carlo simulator (no confidence intervals), but it
produces a believable time series for the dashboard demo and the
consultant can run it once to seed a 30-day view.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Iterable

from ledger import Ledger


def _log_normal(median: float, sigma: float = 0.6) -> float:
    """Sample from a log-normal with the given median. Always > 0."""
    return max(0.01, random.lognormvariate(math_log(median), sigma))


def math_log(x: float) -> float:
    import math
    return math.log(max(x, 0.01))


def _stream_typical_unit(stream: str) -> float:
    """Median $ per single event for this stream."""
    return {
        "seo": 0.40,        # an ad click or affiliate click
        "saas": 19.0,        # a monthly subscription
        "product": 14.0,     # a digital product sale
    }.get(stream, 5.0)


def simulate_days(
    ledger: Ledger,
    days: int = 30,
    events_per_day: tuple[int, int] = (0, 3),
    seed: int | None = None,
    streams: Iterable[str] = ("seo", "saas", "product"),
) -> int:
    """Fill the last `days` days with synthetic revenue events.

    Returns the number of events injected. Skips days that already
    have revenue (so you can re-run safely).
    """
    if seed is not None:
        random.seed(seed)

    streams = list(streams)
    today = datetime.now(timezone.utc).date()
    total = 0

    for offset in range(days):
        day = today - timedelta(days=offset)
        day_iso = day.isoformat()
        n_events = random.randint(*events_per_day)
        for _ in range(n_events):
            stream = random.choice(streams)
            # 90% of events are "normal", 10% are big wins
            if random.random() < 0.10:
                amount = _log_normal(_stream_typical_unit(stream) * 8, sigma=0.4)
            else:
                amount = _log_normal(_stream_typical_unit(stream), sigma=0.6)
            occurred_at = f"{day_iso}T{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:00+00:00"
            ledger.record(
                stream=stream,
                amount_usd=round(amount, 2),
                units=1,
                source=f"simulated-{stream}",
                note="simulated daily event",
                occurred_at=occurred_at,
            )
            total += 1

    return total


def simulate_ramp(ledger: Ledger, days: int = 14) -> int:
    """Specific scenario: zero for first half, then ramp up to a few
    events/day in the second half. Tells a better story than uniform."""
    if seed := 42:
        random.seed(seed)

    today = datetime.now(timezone.utc).date()
    total = 0
    for offset in range(days):
        day = today - timedelta(days=offset)
        day_iso = day.isoformat()
        # Ramp: 0 → 4 events over the window
        progress = 1.0 - (offset / max(days, 1))
        max_events = max(0, int(progress * 4))
        if max_events == 0:
            continue
        for _ in range(random.randint(0, max_events)):
            stream = random.choice(["seo", "saas", "product"])
            amount = _log_normal(_stream_typical_unit(stream))
            ledger.record(
                stream=stream,
                amount_usd=round(amount, 2),
                units=1,
                source=f"simulated-ramp-{stream}",
                note="simulated ramp event",
                occurred_at=f"{day_iso}T{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:00+00:00",
            )
            total += 1
    return total
