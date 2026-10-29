"""
projects/04-multi-region-dr/tests/test_multi_region.py — 1 integration test for DR.

1. test_failover_timing — 3 consecutive failures on primary flips active to replica
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

SVC = Path(__file__).parent.parent / "service"
sys.path.insert(0, str(SVC))

from health import MultiRegionRouter  # noqa: E402


def test_failover_timing():
    """3 consecutive primary failures should flip active to replica."""
    r = MultiRegionRouter(primary="ap-southeast-1", replica="ap-northeast-1")
    assert r.active == "ap-southeast-1", "should start on primary"
    # 1st failure: no failover yet
    r.check("ap-southeast-1", ok=False)
    assert r.active == "ap-southeast-1"
    # 2nd failure: still no failover
    r.check("ap-southeast-1", ok=False)
    assert r.active == "ap-southeast-1"
    # 3rd failure: failover!
    t0 = time.monotonic()
    r.check("ap-southeast-1", ok=False)
    elapsed = time.monotonic() - t0
    assert r.active == "ap-northeast-1", "should have flipped to replica"
    assert elapsed < 0.5, f"failover should be < 500ms, took {elapsed*1000:.1f}ms"
    print(f"  PASS: failed over to replica in {elapsed*1000:.1f}ms")
    # Recovery: primary returns
    r.check("ap-southeast-1", ok=True)
    r.check("ap-southeast-1", ok=True)
    # We don't auto-failback in this minimal router (production would, with hysteresis)
    assert r.checks["ap-southeast-1"].consecutive_failures == 0
    print("  PASS: primary recovered, consecutive_failures reset to 0")


def _run_all():
    print("=" * 60)
    print("Multi-region DR tests — Phase 5 Project 4")
    print("=" * 60)
    for fn in [test_failover_timing]:
        print(f"\n[{fn.__name__}]")
        fn()
    print("\n" + "=" * 60)
    print("ALL 1 MULTI-REGION DR TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    _run_all()
