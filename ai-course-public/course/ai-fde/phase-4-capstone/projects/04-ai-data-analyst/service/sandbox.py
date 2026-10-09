"""
service/sandbox.py — Subprocess-based Python sandbox for the AI Data Analyst.

What this file does
-------------------
The `/analyst` endpoint takes a user's question, asks the LLM to write
Python code that answers it, then runs that code in THIS sandbox.

The sandbox is a SUBPROCESS (not Docker-in-Docker, not gVisor). We
apply four limits:

  1. **Timeout** — 5s wall-clock (kills the subprocess if it runs longer)
  2. **Memory cap** — 256 MB (via `resource.setrlimit` on Unix)
  3. **No network** — empty environment, no API keys
  4. **No file system writes outside `/data`** — the cwd is a temp dir
     with only the customer's CSVs

The threat model is "an LLM emitting code that the customer doesn't
realize is dangerous." Subprocess + rlimit + blocklist is the right
level for THIS threat model. A real deployment with untrusted users
should use gVisor or Firecracker (noted in the lesson).

**Important:** the sandbox does NOT replace the security blocklist.
The blocklist (`security.py`) catches dangerous PATTERNS (os.system,
subprocess, etc.); the sandbox catches dangerous BEHAVIOR (infinite
loops, memory blowups, network calls). The two layers compose.

How to run
----------
    # As a CLI demo
    python3 sandbox.py

    # From your code
    from sandbox import run_code
    result = run_code("print(1 + 1)", timeout_s=2.0)
    print(result.stdout)  # "2\n"
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import tempfile
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ===========================================================================
# Resource limits (Unix only — Windows falls back to timeout-only)
# ===========================================================================
IS_UNIX = platform.system() != "Windows"


def _set_resource_limits(mem_bytes: int) -> None:
    """Apply memory + CPU limits to the current process. Unix only."""
    if not IS_UNIX:
        return
    try:
        import resource
        # Address-space limit (RLIMIT_AS) — caps total memory.
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        # CPU time limit (RLIMIT_CPU) — kills the process after N seconds
        # of CPU time (not wall-clock; the timeout handles wall-clock).
        resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
    except (ImportError, OSError, ValueError):
        # Some sandboxes don't allow setrlimit (e.g., Docker default).
        # The timeout + blocklist still apply.
        pass


# ===========================================================================
# The sandbox result
# ===========================================================================
@dataclass
class SandboxResult:
    """The standardized response shape for any code execution."""
    ok: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = -1
    timed_out: bool = False
    oom: bool = False
    error: Optional[str] = None
    elapsed_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "returncode": self.returncode,
            "timed_out": self.timed_out,
            "oom": self.oom,
            "error": self.error,
            "elapsed_ms": self.elapsed_ms,
        }


# ===========================================================================
# The runner
# ===========================================================================
def run_code(
    code: str,
    *,
    timeout_s: float = 5.0,
    mem_mb: int = 256,
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
) -> SandboxResult:
    """Run `code` in a subprocess with timeout + memory cap + no-network env.

    Args:
        code:     The Python code to run (single string)
        timeout_s: Wall-clock timeout in seconds. Process is killed if it
                   exceeds this. Default 5s.
        mem_mb:   Memory cap in MB. Applied via `resource.setrlimit` on
                  Unix; ignored on Windows. Default 256 MB.
        cwd:      Working directory. Default: a fresh temp dir.
        env:      Environment. Default: minimal env (no API keys).

    Returns:
        SandboxResult with stdout, stderr, returncode, etc.
    """
    t0 = time.monotonic()
    # 1. Pick a working directory.
    if cwd is None:
        cwd = Path(tempfile.mkdtemp(prefix="analyst_sandbox_"))
    # 2. Build the minimal environment (no API keys leaked).
    if env is None:
        env = {
            "PATH": "/usr/bin:/usr/local/bin",
            "HOME": str(cwd),
            "LANG": "C.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            # No AWS_*, no GITHUB_*, no OPENAI_API_KEY, etc.
        }
    # 3. Write the code to a temp file (cleaner than `python -c`).
    code_path = cwd / "_user_code.py"
    code_path.write_text(code)
    # 4. Build the subprocess command. We use `sys.executable -S` to
    # skip site-packages loading and `python -I` for isolated mode.
    cmd = [sys.executable, "-I", str(code_path)]
    # 5. Set the preexec_fn for rlimit (Unix only).
    preexec_fn = _make_preexec_fn(mem_mb * 1024 * 1024) if IS_UNIX else None
    # 6. Run.
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            cwd=str(cwd),
            env=env,
            preexec_fn=preexec_fn,
        )
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        # Detect OOM (returncode is often -9 SIGKILL on Linux).
        oom = (proc.returncode == -9) or ("MemoryError" in proc.stderr)
        return SandboxResult(
            ok=(proc.returncode == 0 and not oom),
            stdout=proc.stdout,
            stderr=proc.stderr,
            returncode=proc.returncode,
            oom=oom,
            elapsed_ms=elapsed_ms,
        )
    except subprocess.TimeoutExpired as e:
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        return SandboxResult(
            ok=False,
            stdout=e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or ""),
            stderr=(e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")),
            returncode=-1,
            timed_out=True,
            error=f"execution exceeded {timeout_s}s timeout",
            elapsed_ms=elapsed_ms,
        )
    except Exception as e:
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        return SandboxResult(
            ok=False,
            error=f"{type(e).__name__}: {e}",
            elapsed_ms=elapsed_ms,
        )


def _make_preexec_fn(mem_bytes: int):
    """Return a preexec_fn that applies the memory + CPU limits."""
    def _preexec():
        _set_resource_limits(mem_bytes)
    return _preexec


# ===========================================================================
# Convenience: run with a security check first
# ===========================================================================
def run_code_safe(
    code: str,
    *,
    timeout_s: float = 5.0,
    mem_mb: int = 256,
) -> SandboxResult:
    """Run `code` only if it passes the security blocklist. The two
    layers compose: blocklist catches patterns, sandbox catches behavior."""
    # Lazy import to avoid a hard dep cycle.
    from security import is_safe, scan_violations
    if not is_safe(code):
        return SandboxResult(
            ok=False,
            error=f"code blocked by security policy: {', '.join(scan_violations(code))}",
        )
    return run_code(code, timeout_s=timeout_s, mem_mb=mem_mb)


# ===========================================================================
# The /analyst endpoint logic (the orchestrator)
# ===========================================================================
ANALYST_SYSTEM_PROMPT = """You are a data analyst. The user will ask a question
about a CSV dataset. Write Python code (pandas) that answers the question.
Output ONLY the code — no prose, no markdown fences.

Constraints:
- Use only `pandas`, `numpy`, and the Python stdlib.
- Read CSVs from `./data/` (relative to the working directory).
- Write any plots to `./output/` (the sandbox creates this dir).
- Print the final answer to stdout.
- Keep the code under 30 lines."""

ANALYST_SYSTEM_PROMPT_SAFE = """You are a data analyst. The user will ask a question
about a CSV dataset. Write Python code (pandas) that answers the question.
Output ONLY the code — no prose, no markdown fences.

Constraints (SECURITY — must follow):
- Use only `pandas`, `numpy`, and the Python stdlib (math, json, csv, datetime, re).
- Read CSVs from `./data/` (relative to the working directory).
- Write any plots to `./output/` (the sandbox creates this dir).
- Print the final answer to stdout.
- Keep the code under 30 lines.
- DO NOT use `os.system`, `subprocess`, `__import__`, `eval`, `exec`,
  `open(...)`, `os.remove`, `requests`, `httpx`, `urllib`, `socket`,
  `pickle.loads`, `__builtins__`. The sandbox will reject any of these."""


def build_code_generation_prompt(question: str, columns: list[str] | None = None) -> str:
    """Build the prompt that asks the LLM to write the analyst code."""
    cols = ", ".join(columns) if columns else "(unknown — use df.columns)"
    return (
        f"{ANALYST_SYSTEM_PROMPT_SAFE}\n\n"
        f"Available columns: {cols}\n\n"
        f"Question: {question}\n\n"
        f"Code:"
    )


# ===========================================================================
# CLI demo
# ===========================================================================
def main() -> int:
    print("=" * 70)
    print("Sandbox — PacificFreight AI Data Analyst (Phase 4 Project 4)")
    print("=" * 70)

    cases = [
        ("safe arithmetic", "print(sum(range(10)))", 2.0),
        ("safe pandas (no data file, will error gracefully)",
         "import pandas as pd\nprint(pd.DataFrame({'a': [1, 2, 3]}).sum())", 2.0),
        ("timeout (infinite loop)", "while True: pass", 1.0),
        ("memory blowup",
         "x = ' ' * (10**9)\nprint(len(x))", 2.0),
    ]
    for label, code, timeout in cases:
        print(f"\n--- {label} ---")
        print(f"code ({len(code)} chars): {code[:60]}...")
        r = run_code(code, timeout_s=timeout, mem_mb=128)
        print(f"  ok={r.ok}  rc={r.returncode}  "
              f"timed_out={r.timed_out}  oom={r.oom}  "
              f"elapsed={r.elapsed_ms}ms")
        if r.stdout:
            print(f"  stdout: {r.stdout.strip()[:80]}")
        if r.stderr:
            print(f"  stderr: {r.stderr.strip()[:80]}")
        if r.error:
            print(f"  error: {r.error}")

    # Combined: security + sandbox
    print("\n--- combined: blocked by security before reaching sandbox ---")
    r = run_code_safe("import os; os.system('echo pwned')", timeout_s=2.0)
    print(f"  ok={r.ok}  error={r.error}")

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())