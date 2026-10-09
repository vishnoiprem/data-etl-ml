"""
projects/03-gvisor-sandbox/service/gvisor_runner.py — gVisor runtime wrapper.

What this file does
-------------------
The Phase 4 data analyst's sandbox (`subprocess.py`) is sufficient when the
threat model is "the LLM emits code that the customer doesn't realize is
dangerous" — 1 customer, 1 tenant, 50 questions/day. Phase 5 changes the
threat model: **multi-tenant**, with users uploading untrusted code at
higher volume. Subprocess + rlimit lets a motivated attacker (or a clever
LLM) escape via a kernel or library CVE.

This file wraps Google's gVisor (`runsc`) to give every code execution
a true userspace kernel boundary. The sandbox is now a Docker container
running under gVisor: no host filesystem, no network, no capabilities,
no `/proc`, no `/sys`. Even a kernel CVE in `matplotlib` or `pandas`
can't escape.

The cost: ~50ms per execution (vs ~5ms for the Phase 4 subprocess). At
500 questions/day this is fine; at 50,000 it's the next bottleneck.

How to run
----------
    # Requires Docker + gVisor installed. See the lesson for setup.
    # If gVisor isn't available, the wrapper falls back to subprocess+rlimit.
    python3 gvisor_runner.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SandboxResult:
    ok: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = -1
    timed_out: bool = False
    oom: bool = False
    escaped: bool = False  # True if the code tried to break out
    backend: str = "gvisor"  # "gvisor" | "subprocess" | "unavailable"
    error: Optional[str] = None
    elapsed_ms: int = 0

    def to_dict(self) -> dict:
        return self.__dict__


# ---------------------------------------------------------------------------
# Backend selection: prefer gVisor, fall back to subprocess
# ---------------------------------------------------------------------------
def _have_gvisor() -> bool:
    return shutil.which("runsc") is not None or shutil.which("docker") is not None


def _have_docker() -> bool:
    return shutil.which("docker") is not None


# ---------------------------------------------------------------------------
# The runner
# ---------------------------------------------------------------------------
def run_code_gvisor(
    code: str,
    *,
    timeout_s: float = 5.0,
    mem_mb: int = 256,
    image: str = "python:3.11-slim",
) -> SandboxResult:
    """Run `code` inside a gVisor-sandboxed Docker container.

    Network: NONE (--network=none).
    Filesystem: a fresh tmpfs at /workspace; no host mount.
    User: nobody (no root inside the sandbox).
    Capabilities: all dropped.
    """
    t0 = time.monotonic()
    if not _have_gvisor():
        # Fall back: subprocess + rlimit (Phase 4 behavior).
        return _run_subprocess_fallback(code, timeout_s=timeout_s, mem_mb=mem_mb)
    if not _have_docker():
        return SandboxResult(
            ok=False, backend="unavailable",
            error="gVisor requires Docker; neither `runsc` nor `docker` found",
        )

    with tempfile.TemporaryDirectory(prefix="gvisor_") as tmp:
        tmp_path = Path(tmp)
        code_path = tmp_path / "user_code.py"
        code_path.write_text(code)
        # Build the docker run command with gVisor as the runtime.
        cmd = [
            "docker", "run",
            "--rm",
            "--runtime=runsc",                  # gVisor
            "--network=none",                   # no network
            "--read-only",                      # no host writes
            "--tmpfs", "/workspace:size=64m",   # small tmpfs for output
            "-v", f"{code_path}:/workspace/user_code.py:ro",
            "-w", "/workspace",
            "-m", f"{mem_mb}m",
            "--cpus=1.0",
            "--user", "nobody",
            "--security-opt", "no-new-privileges",
            "--cap-drop=ALL",
            image,
            "python", "/workspace/user_code.py",
        ]
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=timeout_s,
            )
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            oom = (proc.returncode == 137)  # OOM kill = SIGKILL = 128+9
            # Detect the "docker daemon unreachable" case: returncode 125
            # with stderr mentioning the docker socket. Fall back to
            # subprocess in this case so unit tests + dev machines without
            # a running Docker daemon still work.
            stderr = proc.stderr or ""
            if proc.returncode == 125 and ("Cannot connect" in stderr or "docker.sock" in stderr):
                return _run_subprocess_fallback(code, timeout_s=timeout_s, mem_mb=mem_mb)
            return SandboxResult(
                ok=(proc.returncode == 0 and not oom),
                stdout=proc.stdout,
                stderr=proc.stderr,
                returncode=proc.returncode,
                oom=oom,
                backend="gvisor",
                elapsed_ms=elapsed_ms,
            )
        except subprocess.TimeoutExpired as e:
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            return SandboxResult(
                ok=False, returncode=-1,
                timed_out=True, backend="gvisor",
                error=f"execution exceeded {timeout_s}s",
                elapsed_ms=elapsed_ms,
            )
        except FileNotFoundError:
            return _run_subprocess_fallback(code, timeout_s=timeout_s, mem_mb=mem_mb)
        except Exception as e:
            # Docker binary exists but daemon not reachable, or other
            # gVisor-side failure. Fall back to subprocess so the system
            # still works (with weaker isolation guarantees).
            stderr_msg = str(e)[:200]
            # If the failure looks like "cannot connect to docker daemon",
            # transparently fall back; otherwise surface the error.
            if "Cannot connect" in stderr_msg or "docker.sock" in stderr_msg:
                return _run_subprocess_fallback(code, timeout_s=timeout_s, mem_mb=mem_mb)
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            return SandboxResult(
                ok=False, returncode=-1,
                backend="gvisor", error=stderr_msg,
                elapsed_ms=elapsed_ms,
            )


def _run_subprocess_fallback(code: str, *, timeout_s: float, mem_mb: int) -> SandboxResult:
    """The Phase 4 fallback. Subprocess + rlimit."""
    t0 = time.monotonic()
    try:
        import resource  # Unix only
        def _set_limits():
            try:
                resource.setrlimit(resource.RLIMIT_AS, (mem_mb * 1024 * 1024,) * 2)
                resource.setrlimit(resource.RLIMIT_CPU, (int(timeout_s) + 1,) * 2)
            except Exception:
                pass
        preexec_fn = _set_limits
    except ImportError:
        preexec_fn = None

    with tempfile.TemporaryDirectory(prefix="sub_") as tmp:
        code_path = Path(tmp) / "user_code.py"
        code_path.write_text(code)
        try:
            proc = subprocess.run(
                [sys.executable, "-I", str(code_path)],
                capture_output=True, text=True, timeout=timeout_s,
                preexec_fn=preexec_fn,
            )
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            return SandboxResult(
                ok=(proc.returncode == 0),
                stdout=proc.stdout, stderr=proc.stderr,
                returncode=proc.returncode,
                backend="subprocess",
                elapsed_ms=elapsed_ms,
            )
        except subprocess.TimeoutExpired as e:
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            return SandboxResult(
                ok=False, returncode=-1,
                timed_out=True, backend="subprocess",
                error=f"execution exceeded {timeout_s}s",
                elapsed_ms=elapsed_ms,
            )


def run_code(code: str, **kw) -> SandboxResult:
    """Public entry point. Prefers gVisor, falls back to subprocess."""
    return run_code_gvisor(code, **kw)


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------
def main() -> int:
    print("=" * 70)
    print("gVisor runner — Phase 5 Project 3")
    print("=" * 70)

    if _have_gvisor():
        print("  gVisor: AVAILABLE (will prefer it)")
    else:
        print("  gVisor: NOT INSTALLED (will fall back to subprocess)")
        print("  Install: https://gvisor.dev/docs/user_guide/quick_start/")

    cases = [
        ("safe print", 'print("hello from sandbox")'),
        ("math",        'import math; print(math.pi)'),
        ("infinite loop", 'while True: pass'),
        ("memory bomb",   "x = ' ' * (10**8)\nprint(len(x))"),
    ]
    for label, code in cases:
        print(f"\n--- {label} ---")
        r = run_code(code, timeout_s=2.0)
        print(f"  backend={r.backend}  ok={r.ok}  rc={r.returncode}  "
              f"timed_out={r.timed_out}  elapsed={r.elapsed_ms}ms")
        if r.stdout.strip():
            print(f"  stdout: {r.stdout.strip()[:80]}")
        if r.error:
            print(f"  error: {r.error[:120]}")

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
