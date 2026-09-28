# Code-Fix Agent

> A small autonomous agent that takes a failing test (or any error), proposes a fix, applies it, runs the tests, and either commits + pushes or opens a PR.
>
> Built on the patterns from Module 11 (Harness Engineering) and Module 10 (AI Agents) of the AI Engineering Course.

---

## What it does

```
   INPUT                          AGENT LOOP                         OUTPUT
   ─────                          ──────────                         ──────
   - Failing pytest output        1. Read failing test + traceback    - Patched files
   - Or a stack trace              2. Read the source under test      - Tests passing
   - Or a "fix this bug" prompt    3. Plan a minimal change           - Git commit
                                   4. Apply the edit                  - (optional) PR
                                   5. Re-run tests
                                   6. If green: commit + push
                                      If red: iterate (max 5 tries)
                                   7. Report back
```

---

## Why it's worth having

Most CI failures get stuck in a 30-minute cycle of:
1. Read the error
2. Open the file
3. Guess a fix
4. Push
5. Wait for CI
6. Repeat

A code-fix agent closes the loop in seconds and only surfaces the case it can't handle. That's the same insight as the harness from Module 11 — automation for the 80% case, escalation for the 20%.

---

## Quick start

```bash
cd ai-engineering/15-code-fix-agent
python -m pip install -r requirements.txt
export OPENAI_API_KEY=sk-...

# Fix a failing test
python -m agent.cli "tests/test_calculator.py::test_add" --root ../..

# Fix from a raw traceback
python -m agent.cli --traceback "ZeroDivisionError at line 42 of foo.py"

# Run in dry-run mode (don't commit/push)
python -m agent.cli "tests/test_x.py" --dry-run
```

---

## Architecture

```
   ┌────────────────────────────────────────────────────────┐
   │   CLI  ─►  Planner  ─►  Editor  ─►  Runner  ─►  Reporter │
   │              │            │            │             │
   │              ▼            ▼            ▼             │
   │           read files    edit files   pytest          │
   │           grep, find    (PATCH)      capture exit    │
   │           git log       reject bad   parse failures  │
   │                         diffs                        │
   └────────────────────────────────────────────────────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │  git commit +   │
                     │  push (or PR)   │
                     └─────────────────┘
```

Same harness pattern from Module 11:
- Pydantic schemas for tool args
- Retry + timeout on every tool call
- Cost tracker
- Eval hook
- Hard cap on iteration count

---

## Files

- `agent/planner.py` — decides what to read and what to edit
- `agent/editor.py` — applies file edits safely (Pydantic-validated)
- `agent/runner.py` — runs pytest, parses results
- `agent/git_tools.py` — commit + push (or open PR) helpers
- `agent/cli.py` — entry point
- `tests/` — the agent's own test suite
- `examples/` — sample run traces

See `01-the-agent-loop.md` for the full worked example walkthrough.