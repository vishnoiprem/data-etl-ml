# 37 — Design Claude Code (Agentic Coding Tool)

> **Module 5 of 6 — Agentic AI Systems**

A complete, runnable design + implementation of an agentic coding tool
like Claude Code. The user describes a task; the agent autonomously
calls tools (`read_file`, `write_file`, `list_dir`, `run_command`)
against a sandboxed workspace, observes results, and loops until it
produces a final reply.

The agent loop is the heart of every agentic system:

```
                  ┌──────────────────────────────────┐
                  │                                  │
                  ▼                                  │
   user msg ─► LLM ─► tool_call? ─yes─► execute tool │
                  │                     │            │
                  │                     ▼            │
                  │                  observation    │
                  │                                  │
                  │◄─────────────────────────────────┘
                  │
                  ▼
             final reply
```

---

## 1. Requirements

### Functional
- Create a session with a sandboxed workspace.
- Run the agent loop: model decides → tool executes → observation → loop.
- Cap loop iterations (`MAX_ITERATIONS`).
- Persist the entire turn history (user, assistant, tool).
- List / read files in the workspace.

### Non-functional
- **Sandboxed**: all file paths must resolve under the session's
  workspace; no path traversal.
- **Tool safety**: command allow-list + blocked tokens; 5-second
  timeout per command.
- **Bounded output**: tool output is truncated to `MAX_TOOL_OUTPUT`.
- **Stateful across turns**: files written in one turn persist into
  the next.

### Out of scope
- Real LLM (we use a deterministic policy).
- Multi-session parallelism.
- Diff/undo of file changes.

---

## 2. Capacity estimation

| Metric | Value |
|---|---|
| Iterations per turn | ≤ 5 (cap) |
| Tool calls per turn | ≤ 5 |
| Tool output | ≤ 4 KB each (truncated) |
| Workspace size | 100s of files; MBs |
| Session state | ~10 KB / session (turn log) |

The bottleneck is the **agent loop latency**: each iteration is a
synchronous LLM call. Production systems fan out tool calls in
parallel and stream tool observations.

---

## 3. High-level design

```
       client ──► POST /api/sessions ──► {session_id, workspace}
              ──► POST /api/sessions/<id>/messages {content}
                          │
                          ▼
                  ┌──────────────────┐
                  │   agent loop     │  (deterministic policy mock)
                  └────────┬─────────┘
                           │ tool_call
                           ▼
                  ┌──────────────────┐
                  │   tool runner    │  read_file / write_file /
                  │   (sandboxed)    │  list_dir / run_command
                  └────────┬─────────┘
                           │ observation
                           ▼
                  ┌──────────────────┐
                  │   turn store     │  session:<id>
                  └──────────────────┘
```

State machine:

```
                ┌─────────┐
                │  idle   │──run_turn──►┌─────────┐
                └─────────┘             │thinking │
                                        └────┬────┘
                                             │ tool_call
                                             ▼
                                       ┌────────────┐
                                       │tool_running│
                                       └────┬───────┘
                                            │ result
                                            ▼
                                       ┌─────────┐
                                       │thinking │ (loop)
                                       └────┬────┘
                                            │ no tool_call
                                            ▼
                                       ┌─────────┐
                                       │  done   │
                                       └─────────┘
```

---

## 4. API

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/api/sessions` | `{user_id, workspace?}` | `Session` |
| `GET`  | `/api/sessions` | — | `Session[]` |
| `GET`  | `/api/sessions/<id>` | — | `Session` |
| `POST` | `/api/sessions/<id>/messages` | `{content}` | `{new_turns: [...]}` |
| `GET`  | `/api/sessions/<id>/files` | — | `[{path, size, modified_at}]` |
| `GET`  | `/api/sessions/<id>/files/<path>` | — | file contents (text) |
| `GET`  | `/metrics`, `/health` | — | metrics / health |

---

## 5. Data model

### Session

```json
{
  "session_id": 7,
  "user_id": "u-123",
  "workspace": "ws",
  "created_at": 1700000000.0,
  "iteration_count": 4,
  "last_status": "done",
  "turns": [
    {"role": "user",      "content": "list the files", "tool_call": null},
    {"role": "assistant", "content": "Listing...",    "tool_call": {...}},
    {"role": "tool",      "content": "f README.md\nd src", "tool_call": {...}}
  ]
}
```

### ToolCall

```json
{
  "name": "read_file",
  "args": {"path": "README.md"},
  "call_id": "c0",
  "started_at": 1700000000.0,
  "finished_at": 1700000000.01,
  "output": "# Session 7\n...",
  "error": null,
  "status": "ok"
}
```

### Workspace on disk

```
var/workspace/<workspace_id>/
  README.md
  src/...
  ...
```

---

## 6. Read path deep dive: run_turn

`run_turn(session_id, content)`:

1. Append the user message to the turn log.
2. Set `last_status = "thinking"`.
3. For each iteration (max `MAX_ITERATIONS`):
   - Call `_agent_policy(turns, iteration)` → `(text, tool_call, status)`.
   - Append the assistant turn (with the planned tool call).
   - If `tool_call is None`, set `last_status = "done"`, break.
   - Else, dispatch the tool, capture the result, append a "tool" turn.
4. Persist the session.

The deterministic policy routes requests like this:

- "list" / "show files" → `list_dir`
- "create"/"write" → `write_file` (with a default body)
- "run" / "execute" / "test" → `run_command("ls -la")`
- "read" → `read_file(<first filename mentioned>)`
- otherwise → start with `list_dir`, then summarize

The **safety rails** in `run_command`:
- Allow-list regex on characters.
- Blocklist of dangerous tokens (`rm -rf /`, `mkfs`, `shutdown`, ...).
- 5-second timeout.
- Truncate output to `MAX_TOOL_OUTPUT`.

---

## 7. Write path deep dive: tools

- `read_file(workspace, {path})` — resolves path under workspace, reads
  text, truncates.
- `write_file(workspace, {path, content})` — creates parent dirs, writes.
- `list_dir(workspace, {path})` — sorted `f`/`d` listing.
- `run_command(workspace, {command})` — `subprocess.run` with cwd=workspace.

All paths go through `_safe_join(workspace, rel)` which rejects any
relative path that escapes the workspace. This is the same defense
Snyk / CodeQL expect.

---

## 8. Failure modes

| Failure | Mitigation |
|---|---|
| Tool crashes | Status="error", turn recorded; agent can try again next iteration. |
| LLM produces no tool call | Loop terminates with a final assistant turn. |
| Infinite loop | `MAX_ITERATIONS` hard cap. |
| Path traversal | `_safe_join` rejects any path resolving outside workspace. |
| Dangerous command | Allow-list + blocklist + timeout. |
| Runaway tool output | `MAX_TOOL_OUTPUT` truncate. |
| Workspace disk full | `write_file` raises; agent turn logs the error. |

---

## 9. Tradeoffs

- **Deterministic policy vs real LLM**: the policy is regex-driven so
  tests are deterministic. A real Claude Code calls the Anthropic API
  with tool definitions; the loop is identical.
- **Sequential vs parallel tool calls**: we run tools one at a time.
  Real Claude Code can dispatch several tools in one assistant turn and
  join the results.
- **Sandboxing**: we use a process cwd + allow-list. A real product
  uses a container / firecracker VM / bubblewrap.
- **File persistence**: the workspace is a real directory. A real
  product snapshots it for "undo" / "diff".
- **Token cost of tool observations**: large tool outputs are truncated
  to keep the prompt small. The actual LLM prompt would include only
  the truncated text.

---

## 10. Code map

| File | Role |
|---|---|
| `code/service.py` | `AgentService` — sessions, agent loop, tools, deterministic policy. |
| `code/app.py` | Flask HTTP service. |
| `tests/test_service.py` | Service-level tests (session, loop, files, command safety). |
| `tests/test_app.py` | HTTP-level tests for the agentic flow. |
