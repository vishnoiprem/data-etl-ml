# Project 4 — AI Data Analyst (sandboxed code execution)

> **Phase 4, Project 4.** A fresh-engagement AI Data Analyst. The
> customer asks "what were last quarter's signups by region?"; the LLM
> writes pandas code; a sandboxed subprocess runs it; the answer is
> returned. The security boundary is a hard blocklist (28 regex
> patterns) + a subprocess sandbox (timeout + memory cap + no-network env).

## What's in this directory

```
04-ai-data-analyst/
├── ARCHITECTURE.md             # 7-section design doc
├── README.md                   # ← you are here
└── service/
    ├── security.py             # The hard blocklist (28 patterns)
    ├── sandbox.py              # The subprocess runner
    └── tests/
        ├── conftest.py
        └── test_sandbox.py     # 3 tests (blocklist, timeout, memory cap)
```

## What this project proves

Phases 1-3 are all about the PacificFreight drafter. Project 4 proves
the FDE pattern **transfers to a different customer, a different domain,
a different security model.** The sandbox is a fresh failure mode
(code execution) that the PF drafter doesn't have.

The customer here is "Acme Analytics" — a placeholder for a 20-person
SaaS company. The learner substitutes their own. The pattern transfers;
the domain doesn't.

## The 2 security layers

| Layer | File | What it catches |
|---|---|---|
| **Blocklist** (regex, 28 patterns) | `security.py` | Dangerous patterns: `os.system`, `subprocess`, `__import__`, `eval`, `exec`, `open(...)`, `os.remove`, `requests`, `urllib`, `socket`, `pickle.loads`, `__builtins__`, `globals()`, `locals()`, ... |
| **Sandbox** (subprocess) | `sandbox.py` | Dangerous behavior: infinite loops (5s timeout), memory blowups (256 MB rlimit), network calls (no API keys in env), file system writes (fresh temp dir) |

**The two layers compose.** The blocklist catches patterns; the sandbox
catches behavior. Either alone is insufficient:
- Blocklist alone misses: `"".__class__.__mro__[1].__subclasses__()` (a
  clever way to reach `os.system` without spelling it out)
- Sandbox alone misses: code that exfiltrates data via DNS or timing
  channels (the rlimit doesn't help)

A real deployment with untrusted users should use **gVisor** or
**Firecracker** instead of plain subprocesses (the lesson notes this).
For the AI-emitted-code threat model, the blocklist + sandbox is the
right level.

## How to run

### 1. Test the security blocklist alone

```bash
cd course/ai-fde/phase-4-capstone/projects/04-ai-data-analyst
python3 service/security.py
```

Expected output (8 cases):
```
  safe: groupby                    ✓
  safe: filter                     ✓
  unsafe: os.system                ✗ blocked (os.system)
  unsafe: open write               ✗ blocked (open()
  unsafe: subprocess               ✗ blocked (subprocess)
  unsafe: __import__               ✗ blocked (__import__)
  unsafe: requests                 ✗ blocked (requests.
  unsafe: pickle                   ✗ blocked (pickle.loads)
```

### 2. Test the sandbox alone

```bash
cd course/ai-fde/phase-4-capstone/projects/04-ai-data-analyst
python3 service/sandbox.py
```

Runs 4 cases (safe arithmetic, safe pandas, infinite loop, memory blowup)
and reports which were killed by the timeout / memory cap.

### 3. Run the 3 tests

```bash
cd course/ai-fde/phase-4-capstone/projects/04-ai-data-analyst
python3 -m pytest service/tests/test_sandbox.py -v
```

Expected: **3 passed in 2.0s**

The tests cover:
1. `test_os_system_is_blocked` — the blocklist catches 8 dangerous patterns (`os.system`, `subprocess`, `__import__`, `eval`, `exec`, `open(`, `requests.`, `pickle.loads`)
2. `test_timeout_works` — an infinite loop is killed at the 1-second timeout
3. `test_memory_cap_works` — the rlimit is applied (the test passes on both Linux, where the cap is enforced, and macOS, where `RLIMIT_AS` is not enforced but the mechanism is in place)

### 4. Call the security check from your code

```python
import sys
sys.path.insert(0, "course/ai-fde/phase-4-capstone/projects/04-ai-data-analyst/service")
import security

r = security.check("import os; os.system('rm -rf /')")
print(r)
# → {"ok": False, "violations": ["os.system"], "code_lines": 2, "code_chars": 30}

r = security.check("print(1 + 1)")
print(r)
# → {"ok": True, "violations": [], "code_lines": 1, "code_chars": 10}
```

### 5. Run code in the sandbox

```python
import sandbox

# Safe code: returns immediately
r = sandbox.run_code("print(sum(range(10)))", timeout_s=2.0)
print(r.stdout)  # "45\n"

# Bad code: blocklist catches it BEFORE we even run it
r = sandbox.run_code_safe("import os; os.system('whoami')", timeout_s=2.0)
print(r.error)  # "code blocked by security policy: os.system"

# Bad code: timeout catches it
r = sandbox.run_code("while True: pass", timeout_s=1.0)
print(r.timed_out)  # True
```

## How to extend

### Add a new dangerous pattern to the blocklist

Edit `service/security.py`:

```python
BLOCKED_PATTERNS = [
    # ... existing patterns ...
    ("new_pattern", r"\bnew_pattern\s*\("),  # add this line
]
```

That's it. The next call to `security.check()` will reject the pattern.
No code change anywhere else.

### Add a new allowed import

Edit `service/security.py`:

```python
ALLOWED_IMPORTS = {
    # ... existing imports ...
    "scipy.stats",  # add this line
}
```

The LLM prompt (`sandbox.py::ANALYST_SYSTEM_PROMPT_SAFE`) is hand-edited
to mention the new import. A more sophisticated system would inject
`ALLOWED_IMPORTS` into the prompt automatically (left as a Phase 5 lift).

### Add a `/analyst` HTTP endpoint

The sandbox + blocklist are exposed as Python functions. To expose them
over HTTP, add a FastAPI handler in `service/app.py` (a new file in
this project, not Phase 3's `app.py`):

```python
# In service/app.py (this project's, not Phase 3's)
from security import check
from sandbox import run_code_safe, build_code_generation_prompt

@app.post("/analyst")
def analyst(req: AnalystRequest) -> AnalystResponse:
    # 1. Ask the LLM for code
    prompt = build_code_generation_prompt(req.question, req.columns)
    code = call_llm(prompt)  # you implement this; reuse Phase 1's complete()
    # 2. Blocklist check
    sec = check(code)
    if not sec["ok"]:
        return AnalystResponse(ok=False, error="blocked", violations=sec["violations"])
    # 3. Run in sandbox
    result = run_code_safe(code, timeout_s=5.0, mem_mb=256)
    return AnalystResponse(ok=result.ok, answer=result.stdout, code=code)
```

This is the integration pattern. The LLM call uses Phase 1's
`complete()` (the same function the drafter uses). The blocklist and
sandbox are unchanged.

## Dependencies

- **Python 3.10+** — for the match/case syntax in the dispatch
- **subprocess, resource** — stdlib only (no Docker, no gVisor)
- **No LLM dependency** — the security + sandbox are standalone;
  the LLM call is in the integration layer (your `app.py`)

## Where this fits in the bigger picture

```
PacificFreight              Acme Analytics
─────────────               ───────────────
drafter (1 email            analyst (1 question →
  → 1 draft)                  1 code →
                              1 answer)

Tool layer:                 Tool layer:
  MCP server (RBAC)           Subprocess (rlimit)
  + 4 tools                   + 28-pattern blocklist

Why different:              Why different:
  emails need structured      questions need arbitrary
  replies with limited        code (pandas, groupby,
  variability                 filter, plot)
  → 4 tools cover it          → sandbox needed for
                                "execute arbitrary
                                Python"
```

**The drafter pattern transfers; the security model doesn't.** Phase 3
protects the customer from runaway LLM costs and bad output; Project 4
protects the customer from arbitrary code execution. The 5-question
"FDE has left" test is the rubric for handoff: the customer knows the
blocklist patterns, the sandbox limits, and how to add a new one.

## Related

- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — the design doc
- [`service/security.py`](./service/security.py) — the blocklist
- [`service/sandbox.py`](./service/sandbox.py) — the subprocess runner
- [`service/tests/test_sandbox.py`](./service/tests/test_sandbox.py) — the 3 tests
- [`../../phase-2-core-build/service/retrieval_v2.py`](../../../phase-2-core-build/service/retrieval_v2.py) — Phase 3's retriever (you'd reuse this for RAG over the customer's docs)
- [`../../phase-2-core-build/service/circuit.py`](../../../phase-2-core-build/service/circuit.py) — Phase 3's circuit breaker (you'd reuse this for the LLM call inside `/analyst`)
- [`../01-mcp-drafter/`](../01-mcp-drafter/) — the MCP server (the same `tracker.lookup` tool could be exposed to the analyst for "join against the shipments table")
- [`../02-multi-agent-dispatcher/`](../02-multi-agent-dispatcher/) — the multi-agent orchestrator (the analyst could be a 4th agent in a future customer)
- [`../03-distilled-slm/`](../03-distilled-slm/) — the SLM (the code-generation prompt is small enough to be served by a 1.5B model, but Phase 5)
