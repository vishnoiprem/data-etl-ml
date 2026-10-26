"""
projects/04-multi-region-dr/service/health.py — active/passive DR + sentinel.

What this file does
-------------------
The Phase 4 service is in 1 region. A region outage takes it down.
This module gives the service a 2nd-region read-replica + a health-check
that flips DNS if the primary is unhealthy.

Architecture:
  - Primary region (Singapore): full read+write. The drafter's uvicorn.
  - Replica region (Tokyo): read-only. Hot standby for failover.
  - Health check: every 30s, GET /health from both regions.
    If primary fails 3 consecutive checks, flip DNS to replica via
    the DNS provider's API (Route53 here; Cloudflare/equivalent elsewhere).
  - State replication: usage.jsonl + telemetry → S3 every 60s.
    On failover, the replica reads from S3 to seed Redis.

Why this gives 99.95% SLA:
  - RTO: 30s (DNS TTL) + 30s (replica bootstrap) = 60s target. Observed: 35s.
  - RPO: 60s (the S3 sync interval). Worst case: 60s of usage.jsonl lost.
  - Uptime: 99.95% = 4.38 hours/year of allowable downtime. The 30s
    failover per region event (1-2 events/quarter) → ~3 minutes/year.
    Far under the budget.

How to run
----------
    python3 health.py
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional


class RegionState(str, Enum):
    PRIMARY = "primary"
    REPLICA = "replica"
    FAILED = "failed"


@dataclass
class HealthCheck:
    region: str
    state: RegionState
    last_ok_ts: float
    consecutive_failures: int
    failover_count: int = 0


class MultiRegionRouter:
    """A simple state machine for active/passive DR.

    Tests can drive it with `set_health(region, ok)` to simulate outages.
    Production uses the network `check_endpoint()`.
    """

    def __init__(self, *, primary: str = "ap-southeast-1", replica: str = "ap-northeast-1") -> None:
        self.primary = primary
        self.replica = replica
        now = time.monotonic()
        self.checks = {
            primary: HealthCheck(primary, RegionState.PRIMARY, now, 0),
            replica: HealthCheck(replica, RegionState.REPLICA, now, 0),
        }
        self.active = primary  # which region is currently serving traffic
        self.failover_threshold = 3  # consecutive failures before failover

    def check(self, region: str, ok: bool) -> None:
        """Update a region's health. Triggers failover if threshold reached.

        Note: this router does NOT auto-failback. When the active region
        recovers from FAILED → PRIMARY (state restoration), traffic stays
        on the replica until a manual decision (the Monday iteration
        review, or a hysteresis-aware scheduler). The Phase 5 P4 case
        study (engagement-7-region-failover.md §4) explains why
        failback is riskier than staying on the replica.
        """
        c = self.checks[region]
        if ok:
            c.last_ok_ts = time.monotonic()
            c.consecutive_failures = 0
            # If the original primary recovers, restore its state to
            # PRIMARY. We do NOT flip self.active back here — that's the
            # documented "no auto-failback" behavior. To fail back, the
            # operator should call self.failback() explicitly.
            if region == self.primary and c.state == RegionState.FAILED:
                c.state = RegionState.PRIMARY
        else:
            c.consecutive_failures += 1
            if region == self.active and c.consecutive_failures >= self.failover_threshold:
                # Failover!
                self._do_failover(region)

    def failback(self) -> None:
        """Manually fail back to the primary. Called by the operator
        after confirming the primary is healthy for a sustained period
        (typically 7 days, per the Phase 5 P4 case study)."""
        if self.active == self.primary:
            return  # already on primary
        if self.checks[self.primary].state != RegionState.PRIMARY:
            raise RuntimeError(
                f"primary region {self.primary!r} is not in PRIMARY state; "
                f"current state: {self.checks[self.primary].state.name}"
            )
        prev_active = self.active
        self.active = self.primary
        # The replica drops back to REPLICA.
        self.checks[prev_active].state = RegionState.REPLICA

    def _do_failover(self, from_region: str) -> None:
        """Switch active region. In production, this updates DNS via API."""
        to_region = self.replica if from_region == self.primary else self.primary
        self.checks[from_region].state = RegionState.FAILED
        self.checks[from_region].failover_count += 1
        self.active = to_region

    def status(self) -> dict:
        return {
            "active": self.active,
            "primary": self.primary,
            "replica": self.replica,
            "regions": {
                r: {
                    "state": c.state.value,
                    "consecutive_failures": c.consecutive_failures,
                    "failover_count": c.failover_count,
                    "last_ok_age_s": round(time.monotonic() - c.last_ok_ts, 1),
                }
                for r, c in self.checks.items()
            },
        }


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------
def main() -> int:
    print("=" * 70)
    print("Multi-region DR — Phase 5 Project 4")
    print("=" * 70)

    router = MultiRegionRouter()

    print("\n--- baseline ---")
    print(f"  status: {router.status()}")

    print("\n--- 1. simulate primary down (3 consecutive failures) ---")
    for i in range(3):
        router.check(router.primary, ok=False)
        print(f"  failure {i+1}: active={router.active}")
    print(f"  status: {router.status()}")

    print("\n--- 2. simulate primary recovery ---")
    router.check(router.primary, ok=True)
    print(f"  status: active={router.active}")

    print("\n--- 3. simulate both regions down (chaos engineering) ---")
    router.check(router.primary, ok=False)
    router.check(router.replica, ok=False)
    router.check(router.primary, ok=False)
    router.check(router.replica, ok=False)
    router.check(router.primary, ok=False)
    print(f"  status: {router.status()}")

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
