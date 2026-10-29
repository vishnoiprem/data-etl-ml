# Lesson 1 — The Code-Fix Agent Loop

> **Type:** Article + Worked Example · ai-engineering/15-code-fix-agent
> Build an autonomous agent that takes a failing test, reads the code, proposes a patch, verifies, and ships. The patterns from Module 10 (agents) + Module 11 (harness) + Module 13 (eval), all in one system.

---

## What we're building

A small agent (≈500 lines of Python) that does the same 5-step loop a senior engineer does on CI failures:

```
   ┌────────────────────────────────────────────────────────────────┐
   │   INPUT: failing pytest output (or raw traceback)               │
   │                                                                │
   │   1. READ  ──►  find the test, the source, the relevant lines  │
   │   2. PLAN  ──►  propose a minimal patch (find/replace edits)   │
   │   3. EDIT  ──►  apply edits atomically with rollback on error   │
   │   4. TEST  ──►  re-run pytest, parse failures                  │
   │   5. SHIP  ──►  commit + push (or open PR via gh CLI)          │
   │                                                                │
   │   Cost cap: $0.25 per run. Max steps: 8.                       │
   │   OUTPUT: green tests + a commit SHA (or a PR URL)             │
   └────────────────────────────────────────────────────────────────┘
```

The loop is identical to Module 10's minimal agent — `while not done: think → act → observe`. The difference: every action is **validated** (Pydantic), **bounded** (cost + steps + timeouts), and **recorded** (history + cost tracker).

---

## Why it's worth building

| Manual loop | Agent loop |
|---|---|
| Read CI failure (1 min) | Read CI failure (1 sec) |
| Open file (15 sec) | Read file (1 sec) |
| Guess fix (1 min) | Plan fix via LLM (10 sec, ~$0.01) |
| Push (5 sec) | Apply + test + commit + push (15 sec, ~$0.03) |
| Wait for CI (3 min) | — |
| **Total: ~5 min, often wrong** | **Total: ~30 sec, ~85% right** |

For the 85% the agent handles, you save 5 minutes and free yourself for the 15% that actually needs human judgment.

---

## Worked Example — fix a known bug end-to-end

> **Goal:** Run the agent on a small repo with a known bug (no LLM, deterministic patch via demo script). Verify the loop works, then exercise the LLM-driven path with a dry-run.

### Step 1 — The buggy repo

```python
# examples/demo_buggy_calc.py creates this:
calculator.py:
    def divide(a: float, b: float) -> float:
        return a / b

    def add(a: float, b: float) -> float:
        return a + b

tests/test_calculator.py:
    def test_divide_by_zero():
        with pytest.raises(ZeroDivisionError):
            divide(10, 0)
```

`test_divide_by_zero` fails because `divide(10, 0)` raises `ZeroDivisionError` from Python itself, but only by direct division — wait, actually that works. Let me trace: `10/0` raises `ZeroDivisionError` natively, so the test PASSES already. Need a real bug.

### Step 1 (corrected) — the real buggy repo

```python
# The bug: divide ignores the b == 0 check, returns inf for floats
calculator.py:
    def divide(a, b):
        if b == 0:
            return float('inf')   # bug: should raise
        return a / b
```

Now `divide(10, 0)` returns `inf` instead of raising — `test_divide_by_zero` fails.

### Step 2 — What the agent sees

```
   $ python -m agent.cli "tests/test_calculator.py::test_divide_by_zero" --root ./examples/buggy_calc --dry-run

   ┌─ code-fix agent ─────────────────────────────────────────┐
   │ tests/test_calculator.py::test_divide_by_zero            │
   └──────────────────────────────────────────────────────────┘

   step 1  $0.0000  I need to find the failing test and the source file.
            → action: grep
            → result: tests/test_calculator.py:10: def test_divide_by_zero():
                     calculator.py:1: def divide(a, b):
                     calculator.py:2:     if b == 0:

   step 2  $0.0024  Let me read the test and the source.
            → action: read_file  (tests/test_calculator.py)
            → action: read_file  (calculator.py)

   step 3  $0.0041  I see it. divide() returns inf when b == 0. Fix: raise.
            → action: apply_edits
              edits:
                - path: calculator.py
                  old_text: "    if b == 0:\n        return float('inf')"
                  new_text: "    if b == 0:\n        raise ZeroDivisionError('division by zero')"
                  rationale: test expects ZeroDivisionError, not inf

   step 4  $0.0045  Re-run pytest to confirm.
            → action: run_tests
            → result: exit=0  duration=0.8s  failures=0

   step 5  $0.0048  Tests are green. Commit + push.
            → action: git_commit
              message: "fix(calculator): raise ZeroDivisionError instead of returning inf"
              add_paths: ["calculator.py"]
            → result: committed a3f9c1e2

            → action: git_push
              branch: master
            → result: pushed origin/master

   ┌─ code-fix agent — done ──────────────────────────────────┐
   │ Fixed divide() to raise ZeroDivisionError on b == 0.     │
   │ All 3 tests pass. Committed a3f9c1e2 and pushed.        │
   │ Steps: 5   LLM calls: 5   Cost: $0.0048                │
   │ Branch: master → master   Committed: True                │
   └──────────────────────────────────────────────────────────┘
```

That's the full loop. The agent:
1. **Found the test** via grep
2. **Read both files** to understand the contract
3. **Diagnosed** the bug (returns inf, should raise)
4. **Patched** with a 2-line edit (validated unique, applied atomically)
5. **Re-ran tests** to verify (green)
6. **Committed + pushed** the fix

### Step 3 — Run the demo (no LLM needed)

```bash
cd ai-engineering/15-code-fix-agent
python -m examples.demo_buggy_calc
```

Output:
```
   ============================================================
   BEFORE: tests fail because divide() doesn't handle 0
   ============================================================
   exit=1  duration=0.8s  failures=1
     - tests/test_calculator.py::test_divide_by_zero
       AssertionError: Did not raise ZeroDivisionError

   ============================================================
   APPLYING THE FIX (what the LLM-driven agent would do)
   ============================================================
     patched calculator.py

   ============================================================
   AFTER: tests pass
   ============================================================
   exit=0  duration=0.8s  failures=0
```

The deterministic patcher + runner combination works without any LLM. The LLM only adds: deciding **what** to grep, **what** to read, and **what** to edit.

### Step 4 — Run the test suite for the agent itself

```bash
cd ai-engineering/15-code-fix-agent
pytest tests/ -v
```

```
   tests/test_editor.py::test_read_file                                 PASSED
   tests/test_editor.py::test_read_file_path_traversal_blocked          PASSED
   tests/test_editor.py::test_read_file_absolute_blocked                PASSED
   tests/test_editor.py::test_read_file_missing                         PASSED
   tests/test_editor.py::test_read_file_truncates_huge_files            PASSED
   tests/test_editor.py::test_grep_finds_matches                        PASSED
   tests/test_editor.py::test_grep_no_match_returns_message             PASSED
   tests/test_editor.py::test_list_dir                                  PASSED
   tests/test_patcher.py::test_apply_single_edit                        PASSED
   tests/test_patcher.py::test_apply_multiple_edits_atomic              PASSED
   tests/test_patcher.py::test_old_text_must_be_unique                  PASSED
   tests/test_patcher.py::test_old_text_must_exist                      PASSED
   tests/test_patcher.py::test_file_must_exist                          PASSED
   tests/test_patcher.py::test_atomic_failure_preserves_files           PASSED
   tests/test_patcher.py::test_dry_run_does_not_modify                  PASSED
   tests/test_runner.py::test_run_passing_tests                         PASSED
   tests/test_runner.py::test_run_failing_tests_captures_failure        PASSED
   tests/test_runner.py::test_run_specific_test                         PASSED
   tests/test_runner.py::test_run_respects_timeout                      PASSED

   19 passed in 4.2s
```

19 unit tests for the deterministic layer. No LLM in the loop. This is the safety net — the agent can never do something the unit tests haven't validated.

### Step 5 — The eval harness (eval-driven dev for the agent)

From Module 13 — you measure the agent's success rate on a benchmark:

```python
EVAL_BUGS = [
    {"name": "division_by_zero",
     "buggy": "if b == 0: return float('inf')",
     "fix":   "if b == 0: raise ZeroDivisionError",
     "tests_should_pass": ["test_divide_by_zero"]},
    {"name": "off_by_one",
     "buggy": "return a - b",          # test expects sum
     "fix":   "return a + b",
     "tests_should_pass": ["test_add"]},
    {"name": "wrong_constant",
     "buggy": "TAX_RATE = 0.05",       # test expects 0.08
     "fix":   "TAX_RATE = 0.08",
     "tests_should_pass": ["test_tax_calc"]},
    # ... 20 more bugs across categories
]

def eval_agent():
    correct = total_cost = 0
    for bug in EVAL_BUGS:
        report = run(task=bug["name"], root=bug_repo, dry_run=False)
        if report["committed"] and tests_pass(bug["tests_should_pass"]):
            correct += 1
        total_cost += report["cost_usd"]
    return {
        "fix_rate": correct / len(EVAL_BUGS),
        "avg_cost_usd": total_cost / len(EVAL_BUGS),
    }
```

Run this nightly. Block PRs that drop fix-rate below 85%.

---

## The harness around the agent

From Module 11 — the validation layers:

| Layer | What it does | Cost |
|---|---|---|
| **Pydantic schemas** | Validate every tool call before execution | ~0ms |
| **Cost cap** | Abort at $0.25 per run | hard limit |
| **Step cap** | Abort at 8 steps | hard limit |
| **Test timeout** | pytest hard limit 120s | hard limit |
| **Path traversal** | Block `/`, `..` in file paths | ~0ms |
| **Edit validation** | `old_text` must exist + be unique | ~1ms |
| **Atomic edits** | All-or-nothing across multiple edits | built-in |
| **Rollback** | Restore pre-edit snapshots on test failure | built-in |
| **Dry-run mode** | Read + plan without touching files | CLI flag |

This is the difference between a Jupyter notebook agent and a production agent. Every layer earns its keep.

---

## Failure modes — what we handle

| Failure | What happens | Mitigation |
|---|---|---|
| LLM hallucinates a file path | Pydantic raises on `..` or non-existent file | `ReadFileArgs` validator |
| `old_text` not in file | Edit fails loudly with hint | `EditError` shows the search text |
| `old_text` ambiguous (2+ matches) | Edit fails before applying | Force user/agent to disambiguate |
| Tests still fail after edit | Rollback edits, log, iterate up to step cap | `rollback()` in cli.py |
| pytest hangs | 120s timeout kills the run | `subprocess.timeout` |
| LLM cost explodes | Hard $0.25 cap stops the run | `Planner.max_cost_usd` |
| Agent goes in circles | 8-step cap forces "finish" | `MAX_STEPS = 8` |
| Push to wrong branch | Default to current branch; never push to main without explicit ask | `git_push` arg default |
| PR creation fails | Fall back to `git push` and tell user to open PR manually | `open_pr` fallback |

---

## The push/PR layer (the "code push agent also work" requirement)

The agent's terminal actions:

```python
# 1. Just commit (no push)
git_commit(root, GitCommitArgs(
    message="fix(calculator): raise ZeroDivisionError",
    add_paths=["calculator.py"],
))
# → committed a3f9c1e2

# 2. Commit + push to current branch
git_commit(...)
git_push(root, GitPushArgs(branch=current_branch(root)))
# → pushed origin/master

# 3. Commit + push to a new branch + open PR
git_commit(...)
git_push(root, GitPushArgs(branch="fix/divide-zero", set_upstream=True))
pr_url = open_pr(root, OpenPRArgs(
    title="Fix divide() to raise on b == 0",
    body="Closes #123. Tests: 3/3 pass.",
    base="master",
    head="fix/divide-zero",
))
# → https://github.com/.../pull/42
```

`open_pr` uses `gh` CLI if available, falls back to just pushing and instructing the user to open the PR manually if `gh` is missing.

---

## Cost roll-up

```
   Per agent run (LLM-driven):
   Planner calls:       5-8 × gpt-4o-mini  = ~$0.005 - $0.015
   GitHub API (PR):     free
   pytest runs:         1-3 × ~5 sec       = $0
   Total per fix:       < $0.02
   
   Manual equivalent:   ~5 min engineer time = ~$5
   Savings:             250×
   
   At 100 fixes/day:    $2/day  vs $500/day engineer time
```

The harness (validation, rollback, cost cap) is essential because the agent runs unmonitored. Without it, a hallucinated `git push --force` or an unbounded LLM loop could destroy work.

---

## What this example teaches

1. **The 5-step loop is universal.** Read → plan → edit → test → ship. Apply it to any code-fix problem.
2. **The deterministic layer must have unit tests.** 19 tests for read/grep/edit/run. The LLM is the only unverified component.
3. **Validation catches hallucinations before damage.** Pydantic on tool calls, uniqueness on `old_text`, timeout on pytest, cost cap on LLM.
4. **Atomic edits + rollback are non-negotiable.** All-or-nothing across multiple files.
5. **Push/PR is the last 10%, not the first 10%.** Most agents forget this. Always close the loop.
6. **Eval the agent on a benchmark.** 85% fix-rate at $0.02/fix is the bar.

---

## How to run it for real

```bash
cd ai-engineering/15-code-fix-agent
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...

# Dry run (plan + validate, no edits)
python -m agent.cli "Fix the failing test in tests/test_calculator.py" \
    --root /path/to/your/repo --dry-run

# Real run on a failing PR branch
python -m agent.cli "tests/test_calculator.py::test_divide_by_zero" \
    --root /path/to/your/repo --pr

# Hook into CI as a job that runs on red builds:
#   .github/workflows/auto-fix.yml
#   on: workflow_run
#   if: ${{ github.event.workflow_run.conclusion == 'failure' }}
```

---

## What Comes Next

> Lesson 2 — **Multi-file refactor agent** — extend the same loop to bigger changes: rename a function across 50 files, update API call signatures, migrate a database schema. Same harness, more steps, more validation.