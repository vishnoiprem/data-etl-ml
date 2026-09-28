"""Test runner — invoke pytest, capture results, parse failures."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass

from .schemas import RunTestsArgs


@dataclass
class TestResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_s: float
    failures: list[dict]  # [{"file": ..., "line": ..., "test": ..., "msg": ...}]

    @property
    def passed(self) -> bool:
        return self.exit_code == 0

    def summary(self) -> str:
        return (
            f"exit={self.exit_code}  duration={self.duration_s:.1f}s  "
            f"failures={len(self.failures)}"
        )


def run_tests(root: Path, args: RunTestsArgs) -> TestResult:  # type: ignore[name-defined]
    """Run pytest in the given repo root. Capture output and parse failures."""
    import time
    # Always pass the root explicitly via a cd target. Pytest treats positional
    # args as paths to test files/roots.
    cmd = ["pytest"]
    if args.target:
        cmd.append(args.target)
    else:
        cmd.append(str(root))
    cmd += ["-x", "--tb=short", "--no-header", "-q"]

    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=args.timeout_s,
        )
    except subprocess.TimeoutExpired as e:
        return TestResult(
            exit_code=124,
            stdout=e.stdout or "",
            stderr=f"TimeoutExpired after {args.timeout_s}s",
            duration_s=args.timeout_s,
            failures=[{"msg": "test run timed out"}],
        )

    duration = time.perf_counter() - t0
    failures = _parse_failures(proc.stdout + "\n" + proc.stderr)
    return TestResult(
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        duration_s=duration,
        failures=failures,
    )


# ── parsing ─────────────────────────────────────────────────────────────
FAILURE_RE = re.compile(
    r"FAILED (?P<file>[^\s:]+)::(?P<test>[^\s]+)\s*(?:-\s*(?P<msg>.+))?",
)
SHORT_TRACE_RE = re.compile(
    r"^> +(?P<msg>.+?)(?=\n\n|\Z)", re.MULTILINE | re.DOTALL,
)


def _parse_failures(output: str) -> list[dict]:
    failures = []
    for m in FAILURE_RE.finditer(output):
        msg_match = SHORT_TRACE_RE.search(output[m.end():])
        msg = msg_match.group("msg").strip() if msg_match else m.group("msg")
        failures.append({
            "file": m.group("file"),
            "test": m.group("test"),
            "msg": (msg or "")[:1500],
        })
    return failures[:10]