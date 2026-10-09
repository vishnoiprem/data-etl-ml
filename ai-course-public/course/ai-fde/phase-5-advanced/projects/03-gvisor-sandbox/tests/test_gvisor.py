"""
projects/03-gvisor-sandbox/tests/test_gvisor.py — 2 tests for the gVisor runner.

1. test_safe_code_runs       — a "hello world" returns ok=True
2. test_timeout_kills        — infinite loop is killed at the timeout
"""
from __future__ import annotations

import sys
from pathlib import Path

SVC = Path(__file__).parent.parent / "service"
sys.path.insert(0, str(SVC))

from gvisor_runner import run_code  # noqa: E402


def test_safe_code_runs():
    r = run_code('print("hello")', timeout_s=2.0)
    assert r.ok, f"safe code should run, got ok={r.ok} error={r.error}"
    assert "hello" in r.stdout
    print(f"  PASS: safe code ran on backend={r.backend}, stdout={r.stdout.strip()!r}")


def test_timeout_kills():
    r = run_code("while True: pass", timeout_s=1.0)
    assert not r.ok
    assert r.timed_out, f"infinite loop should be killed by timeout, got {r}"
    print(f"  PASS: timeout killed on backend={r.backend} after {r.elapsed_ms}ms")


def _run_all():
    print("=" * 60)
    print("gVisor tests — Phase 5 Project 3")
    print("=" * 60)
    for fn in [test_safe_code_runs, test_timeout_kills]:
        print(f"\n[{fn.__name__}]")
        fn()
    print("\n" + "=" * 60)
    print("ALL 2 GVISOR TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    _run_all()
