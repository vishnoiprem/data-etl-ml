"""Claude Code (agentic coding tool) — core service.

A small, runnable agentic coding service. The user describes a task
in natural language; the (mock) agent loop:

    1. Read the user's request.
    2. Decide which tool to call (read_file / write_file / run_command
       / list_dir).
    3. Execute the tool against a sandboxed workspace.
    4. Append the observation.
    5. Loop up to MAX_ITERATIONS times, or until the agent emits a
       final text reply.

The agent's tool-use policy is a deterministic mock. Real Claude Code
calls the Anthropic API with tool definitions and a sandboxed
execution environment. We do the same shape, locally.

State machine per session:

    idle ──(message)──► thinking ──(tool_call)──► tool_running
                                              │
                                              └─(done)──► thinking
                                                                │
                                                                └─(final)──► idle
"""

from __future__ import annotations

import os
import re
import subprocess
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from common.storage import KeyValueStore


# ---------------------------------------------------------------------------
# Defaults & limits
# ---------------------------------------------------------------------------


MAX_ITERATIONS = 5
MAX_TOOL_OUTPUT = 4_000
MAX_FILENAME = 128
ALLOWED_COMMAND_CHARS = re.compile(r"^[A-Za-z0-9_./\- \t=:&|()<>{}'\"`!]+$")
DANGEROUS_COMMAND_TOKENS = (
    "rm -rf /", "rm -rf /*", ":(){ :|:& };:",
    "mkfs", "dd if=", "shutdown", "reboot", "halt",
)
DEFAULT_WORKSPACE = "var/workspace"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ToolCall:
    name: str
    args: dict
    call_id: str
    started_at: float = field(default_factory=lambda: time.time())
    finished_at: Optional[float] = None
    output: str = ""
    error: Optional[str] = None
    status: str = "pending"  # "pending" | "ok" | "error"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AgentTurn:
    role: str  # "user" | "assistant" | "tool"
    content: str
    tool_call: Optional[ToolCall] = None
    created_at: float = field(default_factory=lambda: time.time())

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "tool_call": self.tool_call.to_dict() if self.tool_call else None,
            "created_at": self.created_at,
        }


@dataclass
class Session:
    session_id: int
    user_id: str
    workspace: str
    created_at: float = field(default_factory=lambda: time.time())
    turns: list[AgentTurn] = field(default_factory=list)
    iteration_count: int = 0
    last_status: str = "idle"  # "idle" | "thinking" | "tool_running" | "done" | "error"

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "workspace": self.workspace,
            "created_at": self.created_at,
            "iteration_count": self.iteration_count,
            "last_status": self.last_status,
            "turns": [t.to_dict() for t in self.turns],
        }


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def _safe_join(workspace: Path, rel: str) -> Path:
    """Resolve a relative path under the workspace, blocking traversal."""
    rel = rel.lstrip("/").lstrip("\\")
    candidate = (workspace / rel).resolve()
    workspace = workspace.resolve()
    try:
        candidate.relative_to(workspace)
    except ValueError as e:
        raise ValueError(f"path '{rel}' escapes the workspace") from e
    return candidate


def tool_read_file(workspace: Path, args: dict) -> ToolCall:
    call = ToolCall(name="read_file", args=args, call_id=str(int(time.time() * 1e6)))
    path = args.get("path", "")
    if not path:
        call.status = "error"
        call.error = "missing 'path' arg"
        call.finished_at = time.time()
        return call
    try:
        p = _safe_join(workspace, path)
        if not p.exists():
            call.status = "error"
            call.error = f"no such file: {path}"
        else:
            data = p.read_text(errors="replace")
            if len(data) > MAX_TOOL_OUTPUT:
                data = data[:MAX_TOOL_OUTPUT] + "\n…(truncated)"
            call.output = data
            call.status = "ok"
    except Exception as e:
        call.status = "error"
        call.error = str(e)
    call.finished_at = time.time()
    return call


def tool_write_file(workspace: Path, args: dict) -> ToolCall:
    call = ToolCall(name="write_file", args={"path": args.get("path", "")}, call_id=str(int(time.time() * 1e6)))
    path = args.get("path", "")
    content = args.get("content", "")
    if not path:
        call.status = "error"
        call.error = "missing 'path' arg"
        call.finished_at = time.time()
        return call
    try:
        p = _safe_join(workspace, path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        call.output = f"wrote {len(content)} bytes to {path}"
        call.status = "ok"
    except Exception as e:
        call.status = "error"
        call.error = str(e)
    call.finished_at = time.time()
    return call


def tool_list_dir(workspace: Path, args: dict) -> ToolCall:
    call = ToolCall(name="list_dir", args={"path": args.get("path", ".")}, call_id=str(int(time.time() * 1e6)))
    rel = args.get("path", ".")
    try:
        p = _safe_join(workspace, rel)
        if not p.exists():
            call.status = "error"
            call.error = f"no such directory: {rel}"
        elif not p.is_dir():
            call.status = "error"
            call.error = f"not a directory: {rel}"
        else:
            entries = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name))
            call.output = "\n".join(
                f"{'d' if e.is_dir() else 'f'} {e.relative_to(p)}" for e in entries
            )
            if not call.output:
                call.output = "(empty directory)"
            call.status = "ok"
    except Exception as e:
        call.status = "error"
        call.error = str(e)
    call.finished_at = time.time()
    return call


def tool_run_command(workspace: Path, args: dict) -> ToolCall:
    call = ToolCall(name="run_command", args={"command": args.get("command", "")}, call_id=str(int(time.time() * 1e6)))
    cmd = args.get("command", "")
    if not cmd:
        call.status = "error"
        call.error = "missing 'command' arg"
        call.finished_at = time.time()
        return call
    # Sandbox: only allow characters in a small whitelist.
    if not ALLOWED_COMMAND_CHARS.match(cmd):
        call.status = "error"
        call.error = "command contains disallowed characters"
        call.finished_at = time.time()
        return call
    if any(tok in cmd for tok in DANGEROUS_COMMAND_TOKENS):
        call.status = "error"
        call.error = "command blocked by safety policy"
        call.finished_at = time.time()
        return call
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=5,
        )
        out = (result.stdout or "") + (result.stderr or "")
        if len(out) > MAX_TOOL_OUTPUT:
            out = out[:MAX_TOOL_OUTPUT] + "\n…(truncated)"
        call.output = out or f"(no output, exit={result.returncode})"
        call.status = "ok" if result.returncode == 0 else "error"
        if result.returncode != 0:
            call.error = f"exit code {result.returncode}"
    except subprocess.TimeoutExpired:
        call.status = "error"
        call.error = "command timed out after 5s"
    except Exception as e:
        call.status = "error"
        call.error = str(e)
    call.finished_at = time.time()
    return call


TOOL_DISPATCH = {
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "list_dir": tool_list_dir,
    "run_command": tool_run_command,
}


# ---------------------------------------------------------------------------
# Deterministic agent policy
# ---------------------------------------------------------------------------


def _agent_policy(turns: list[AgentTurn], iteration: int) -> tuple[str, Optional[ToolCall], str]:
    """Decide the next action for the agent.

    Returns (assistant_text, tool_call, status). When ``tool_call`` is
    None we return a final reply and the loop terminates.
    """
    last_user = next((t for t in reversed(turns) if t.role == "user"), None)
    if last_user is None:
        return "I need a request to work on.", None, "done"

    text = last_user.content.lower()
    if iteration >= MAX_ITERATIONS:
        return (
            f"Reached the max iteration cap ({MAX_ITERATIONS}). "
            f"Final summary based on what I found.",
            None,
            "done",
        )

    # Policy 1: list dir.
    if any(k in text for k in ("list", "show me the files", "what's in", "what is in")):
        return (
            "Let me look at the workspace first.",
            ToolCall(name="list_dir", args={"path": "."}, call_id=f"c{iteration}"),
            "tool_running",
        )

    # Policy 2: read a file.
    if "read" in text or "show" in text and "file" in text:
        m = re.search(r"([A-Za-z0-9_\-./]+\.[A-Za-z0-9]+)", last_user.content)
        path = m.group(1) if m else "README.md"
        return (
            f"Reading `{path}`.",
            ToolCall(name="read_file", args={"path": path}, call_id=f"c{iteration}"),
            "tool_running",
        )

    # Policy 3: write/create.
    if "create" in text or "write" in text or "add" in text or "make" in text:
        m = re.search(r"([A-Za-z0-9_\-./]+\.[A-Za-z0-9]+)", last_user.content)
        path = m.group(1) if m else "note.txt"
        body = "Hello! Generated by the agent.\n"
        return (
            f"Creating `{path}`.",
            ToolCall(
                name="write_file",
                args={"path": path, "content": body},
                call_id=f"c{iteration}",
            ),
            "tool_running",
        )

    # Policy 4: run a command.
    if "run" in text or "execute" in text or "test" in text:
        return (
            "Running `ls -la` to inspect the workspace.",
            ToolCall(
                name="run_command",
                args={"command": "ls -la"},
                call_id=f"c{iteration}",
            ),
            "tool_running",
        )

    # Default: ask the agent to list the directory first.
    if iteration == 0:
        return (
            "I'll start by listing the workspace.",
            ToolCall(name="list_dir", args={"path": "."}, call_id=f"c{iteration}"),
            "tool_running",
        )

    # After a few steps without a clear policy, summarize and stop.
    return (
        "I've explored the workspace. Let me know what specifically you'd like me to do next.",
        None,
        "done",
    )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class AgentService:
    """A working agentic coding service.

    >>> import tempfile
    >>> root = tempfile.mkdtemp()
    >>> svc = AgentService(workspace_root=root)
    >>> sid = svc.create_session("u1")
    >>> out = svc.run_turn(sid, "List the files")
    >>> "I'll start by listing" in out[-1].content or out[-2].content.startswith("Workspace")
    True
    """

    def __init__(
        self,
        store: Optional[KeyValueStore] = None,
        workspace_root: Optional[str | Path] = None,
        default_workspace: str = DEFAULT_WORKSPACE,
    ):
        self.store = store or KeyValueStore("claude_code")
        self.workspace_root = Path(workspace_root or "var")
        (self.workspace_root / default_workspace).mkdir(parents=True, exist_ok=True)
        self.default_workspace = default_workspace
        self._next_id = self._max_id() + 1

    def _max_id(self) -> int:
        best = 0
        for k, _ in self.store.scan("session:"):
            try:
                best = max(best, int(k.split(":")[1]))
            except (IndexError, ValueError):
                continue
        return best

    def _session_workspace(self, session: Session) -> Path:
        p = self.workspace_root / session.workspace
        p.mkdir(parents=True, exist_ok=True)
        return p

    # ---- sessions ------------------------------------------------------

    def create_session(self, user_id: str, workspace: Optional[str] = None) -> Session:
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id is required")
        ws = workspace or self.default_workspace
        sid = self._next_id
        self._next_id += 1
        s = Session(session_id=sid, user_id=user_id, workspace=ws)
        # Seed each session with a tiny README so the agent has something
        # to read.
        readme = self._session_workspace(s) / "README.md"
        if not readme.exists():
            readme.write_text(
                f"# Session {sid}\n\nWelcome! This is the agent's workspace.\n"
            )
        self._persist(s)
        return s

    def get_session(self, session_id: int) -> Optional[Session]:
        d = self.store.get(f"session:{session_id}")
        if not d:
            return None
        turns = []
        for t in d.get("turns", []):
            tc = None
            if t.get("tool_call"):
                tc = ToolCall(**t["tool_call"])
            turns.append(
                AgentTurn(
                    role=t["role"],
                    content=t["content"],
                    tool_call=tc,
                    created_at=t.get("created_at", 0.0),
                )
            )
        return Session(
            session_id=d["session_id"],
            user_id=d["user_id"],
            workspace=d["workspace"],
            created_at=d.get("created_at", 0.0),
            iteration_count=d.get("iteration_count", 0),
            last_status=d.get("last_status", "idle"),
            turns=turns,
        )

    def list_sessions(self) -> list[Session]:
        out: list[Session] = []
        for k, _ in self.store.scan("session:"):
            sid = int(k.split(":")[1])
            s = self.get_session(sid)
            if s:
                out.append(s)
        out.sort(key=lambda s: s.session_id)
        return out

    # ---- turns ---------------------------------------------------------

    def post_message(self, session_id: int, content: str) -> AgentTurn:
        s = self.get_session(session_id)
        if not s:
            raise ValueError("session not found")
        if not content or not isinstance(content, str):
            raise ValueError("content is required")
        t = AgentTurn(role="user", content=content)
        s.turns.append(t)
        self._persist(s)
        return t

    def run_turn(self, session_id: int, content: str) -> list[AgentTurn]:
        """Run the agent loop for one user message and return all new turns."""
        s = self.get_session(session_id)
        if not s:
            raise ValueError("session not found")
        if not content or not isinstance(content, str):
            raise ValueError("content is required")
        workspace = self._session_workspace(s)

        s.turns.append(AgentTurn(role="user", content=content))
        s.last_status = "thinking"
        self._persist(s)

        new_turns: list[AgentTurn] = []

        for iteration in range(MAX_ITERATIONS + 1):
            s.iteration_count += 1
            text, planned_call, status = _agent_policy(s.turns, iteration)
            assistant_turn = AgentTurn(
                role="assistant",
                content=text,
                tool_call=planned_call,
            )
            s.turns.append(assistant_turn)
            new_turns.append(assistant_turn)
            if planned_call is None:
                s.last_status = "done"
                self._persist(s)
                break
            # Execute the tool.
            fn = TOOL_DISPATCH.get(planned_call.name)
            if fn is None:
                planned_call.status = "error"
                planned_call.error = f"unknown tool: {planned_call.name}"
                planned_call.finished_at = time.time()
            else:
                result_call = fn(workspace, planned_call.args)
                # Carry the result back into the planned_call.
                planned_call.output = result_call.output
                planned_call.error = result_call.error
                planned_call.status = result_call.status
                planned_call.finished_at = result_call.finished_at
            # Record the tool observation as its own turn.
            obs = AgentTurn(
                role="tool",
                content=planned_call.output or planned_call.error or "",
                tool_call=planned_call,
            )
            s.turns.append(obs)
            new_turns.append(obs)
            s.last_status = "thinking"
            self._persist(s)

        if s.last_status != "done":
            s.last_status = "done"
            self._persist(s)
        return new_turns

    # ---- files ---------------------------------------------------------

    def list_files(self, session_id: int) -> list[dict]:
        s = self.get_session(session_id)
        if not s:
            raise ValueError("session not found")
        workspace = self._session_workspace(s)
        out: list[dict] = []
        for p in sorted(workspace.rglob("*")):
            if p.is_file():
                out.append({
                    "path": str(p.relative_to(workspace)),
                    "size": p.stat().st_size,
                    "modified_at": p.stat().st_mtime,
                })
        return out

    def read_file(self, session_id: int, path: str) -> str:
        s = self.get_session(session_id)
        if not s:
            raise ValueError("session not found")
        workspace = self._session_workspace(s)
        p = _safe_join(workspace, path)
        if not p.exists() or not p.is_file():
            raise ValueError(f"no such file: {path}")
        return p.read_text(errors="replace")

    # ---- stats ---------------------------------------------------------

    def stats(self) -> dict:
        n_sessions = sum(1 for _ in self.store.scan("session:"))
        n_turns = 0
        n_tool_calls = 0
        for k, _ in self.store.scan("session:"):
            s = self.get_session(int(k.split(":")[1]))
            if s:
                n_turns += len(s.turns)
                n_tool_calls += sum(1 for t in s.turns if t.tool_call is not None)
        return {
            "sessions": n_sessions,
            "turns": n_turns,
            "tool_calls": n_tool_calls,
        }

    # ---- internals -----------------------------------------------------

    def _persist(self, s: Session) -> None:
        self.store.set(f"session:{s.session_id}", s.to_dict())
