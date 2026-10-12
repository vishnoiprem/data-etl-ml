# 9. Claude Code-style terminal agent

A REPL that lives in your shell: read the file, edit the file, run the command, read the output, fix the bug, run again. The agent doesn't just call tools — it streams diffs to your TTY and asks before destructive actions.

## The shape

```
   ┌────────────────────────────────────────┐
   │   TUI (Textual)                        │
   │   - user prompt at the bottom          │
   │   - streaming diffs in the middle      │
   │   - tool call log at the top           │
   └──────────────┬─────────────────────────┘
                  │
                  ▼
   ┌────────────────────────────────────────┐
   │   Agent loop (LangGraph)               │
   │   - planner -> tool call -> verify     │
   │   - bounded retries                    │
   │   - approval gate for destructive ops  │
   └──────────────┬─────────────────────────┘
                  │
                  ▼
   ┌────────────────────────────────────────┐
   │   Tools                                │
   │   - read / edit (file)                 │
   │   - run (PTY, with timeout)            │
   │   - grep (ripgrep)                     │
   └────────────────────────────────────────┘
```

## What I built

- `tui/app.py` — Textual TUI with prompt input, streaming output, tool log.
- `agent/loop.py` — the agent loop with approval gate.
- `tools/file.py` — read, edit, create, with backup on edit.
- `tools/pty.py` — runs commands in a PTY so the agent sees real terminal output.
- `tools/grep.py` — ripgrep wrapper.
- `examples/run_demo.py` — opens the TUI and starts the agent.

## The approval gate

The agent asks before any destructive action: delete file, drop table, kill process, force-push. The gate is implemented as an `ApprovalRequest` that pauses the loop and waits for the user. This is the part that turns "scary agent" into "useful agent."

```python
DESTRUCTIVE_TOOLS = {"delete", "drop", "kill", "force_push", "rm -rf", "truncate"}

async def maybe_approve(tool_call):
    if tool_call.tool in DESTRUCTIVE_TOOLS:
        return await ask_user(f"Allow {tool_call.tool}({tool_call.args})? [y/N]")
    return True
```

## Real-world test (in my own shell)

- 80% of my own refactoring chores: handled without intervention.
- 15% of cases: needed me to approve a destructive action.
- 5% of cases: agent got stuck in a loop and I had to kill it.

The 5% is the part to fix. The pattern: detect "I've been doing the same thing for 3 steps with no progress" and stop.

## Run

```bash
pip install -r requirements.txt
make demo
```
---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  
