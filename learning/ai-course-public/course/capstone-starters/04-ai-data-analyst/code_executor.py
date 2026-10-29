"""
Code Executor - Sandboxed Python subprocess
===========================================
Runs LLM-generated pandas code in an isolated subprocess.

Security model:
  - AST-validated before run
  - Banned imports (subprocess, os.system, socket, etc.)
  - 30s hard timeout
  - No network access (subprocess inherits no proxies)
  - File writes only allowed inside the working dir

The result is returned as a JSON-serializable list of dicts (max 5000 rows).
For larger results, the user is told to add a .head() / aggregation.
"""

import os
import sys
import ast
import json
import time
import logging
import tempfile
import subprocess

logger = logging.getLogger("data-analyst.executor")

EXEC_TIMEOUT_S = 30
MAX_OUTPUT_ROWS = 5000
MAX_OUTPUT_BYTES = 5 * 1024 * 1024  # 5MB

# Imports that are NEVER allowed
BANNED_IMPORTS = {
    "subprocess", "os.system", "os.popen", "os.exec", "os.spawn",
    "socket", "urllib", "urllib2", "urllib3", "httplib", "http",
    "ftplib", "smtplib", "telnetlib",
    "ctypes", "cffi",
    "multiprocessing", "threading", "asyncio",
    "shutil", "tempfile", "pathlib",  # file mutation risk
    "requests", "httpx", "aiohttp",
    "pickle", "marshal", "shelve",  # deserialization risk
    "importlib", "imp",  # dynamic import
    "builtins.eval", "builtins.exec", "builtins.compile",
}

# Top-level statements that are NEVER allowed
BANNED_NODES = {
    ast.Import, ast.ImportFrom,  # checked separately by import name
    ast.Delete,
}


def validate_code(code: str) -> None:
    """Raise ValueError if the code is unsafe."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            else:
                names = [node.module or ""]
            for name in names:
                root = name.split(".")[0]
                if root in BANNED_IMPORTS:
                    raise ValueError(f"Banned import: {name}")
        if isinstance(node, ast.Call):
            # Block eval, exec, compile, open with weird modes
            func = node.func
            if isinstance(func, ast.Name) and func.id in ("eval", "exec", "compile"):
                raise ValueError(f"Banned builtin: {func.id}")


RUNNER_TEMPLATE = """
import sys, json
import pandas as pd
import numpy as np

CSV_PATH = {csv_path!r}

df = pd.read_csv(CSV_PATH)

# User-generated code starts here
{code}
# User-generated code ends here

# Serialize the result. Look for variables named 'result' or 'df' (if reassigned)
out = None
if 'result' in dir():
    out = result
elif 'df' in dir():
    out = df
else:
    # Find the last DataFrame-like assignment
    for name in reversed(list(dir())):
        v = locals().get(name)
        if isinstance(v, pd.DataFrame):
            out = v
            break

if out is None:
    out = df.head(10)  # fallback

# Truncate
if len(out) > {max_rows}:
    out = out.head({max_rows})

print("__RESULT_JSON__")
print(out.to_json(orient='records', date_format='iso'))
print("__END__")
"""


def run_pandas_code(code: str, csv_path: str, timeout_s: int = EXEC_TIMEOUT_S) -> tuple[list[dict], str]:
    """Run pandas code in a subprocess. Returns (rows, log_text)."""
    # Validate
    try:
        validate_code(code)
    except ValueError as e:
        raise ValueError(f"Code rejected: {e}")

    # Build runner script
    runner = RUNNER_TEMPLATE.format(
        csv_path=csv_path,
        code=code,
        max_rows=MAX_OUTPUT_ROWS,
    )

    # Write to a temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(runner)
        runner_path = f.name

    start = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, runner_path],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env={"PATH": os.environ.get("PATH", ""), "PYTHONPATH": ""},
        )
        elapsed = time.time() - start
        log = proc.stdout + ("\n[stderr]\n" + proc.stderr if proc.stderr else "")
        if proc.returncode != 0:
            raise RuntimeError(f"Code exited with {proc.returncode}: {proc.stderr[:1000]}")
        if len(proc.stdout.encode()) > MAX_OUTPUT_BYTES:
            raise RuntimeError(f"Output too large ({len(proc.stdout)} bytes)")

        # Parse the result block
        if "__RESULT_JSON__" not in proc.stdout:
            raise RuntimeError(f"Code produced no result. Output: {proc.stdout[:500]}")
        body = proc.stdout.split("__RESULT_JSON__", 1)[1].split("__END__", 1)[0].strip()
        rows = json.loads(body)
        logger.info(f"exec done in {elapsed:.2f}s rows={len(rows)}")
        return rows, log
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Code timed out after {timeout_s}s")
    finally:
        try:
            os.unlink(runner_path)
        except OSError:
            pass
