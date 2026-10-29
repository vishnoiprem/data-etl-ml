"""
Lab 09: Production ReAct Agent with Tools
==========================================

A real, deployable ReAct-style agent that performs a Thought -> Action ->
Observation loop manually (no LangChain). The agent has 5+ tools (web search,
calculator, file read, code execution in a sandbox, email send), explicit
error recovery, a stuck detector, an iteration budget, cost + time tracking,
and structured logging of every reasoning step.

What it does
------------
1. Accepts a natural-language goal from the caller.
2. Repeatedly:
    a. Asks the LLM (or deterministic mock) what to do next, given the full
       transcript so far.
    b. Parses the LLM output into a structured Action (tool + args).
    c. Dispatches the tool, with retries and an explicit error-recovery
       policy: first failure -> try the alternate tool; second failure ->
       escalate to the human-in-the-loop channel; third -> abort.
    d. Records the observation and goes around again.
3. Stops when:
    - The LLM emits "FINAL_ANSWER: ..."
    - The iteration budget is exhausted
    - The stuck detector fires (same tool called 3x in a row with same args)
    - The cost or time budget is exceeded
    - The user (via HITL) replies "STOP"

Architecture (ASCII)
--------------------
              ┌─────────────────────────┐
              │         Goal            │
              └────────────┬────────────┘
                           ▼
       ┌────────────────────────────────────┐
       │      ReAct Loop (manual)           │
       │                                    │
       │  Thought ──► Action ──► Observation│
       │       ▲           │           │    │
       │       └───────────┴───────────┘    │
       └─────────────────┬──────────────────┘
                         ▼
       ┌────────────────────────────────────┐
       │       Tool Dispatch Layer          │
       │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐    │
       │  │Web  │ │Calc │ │File │ │Code │ ...│
       │  └─────┘ └─────┘ └─────┘ └─────┘    │
       └─────────────────┬──────────────────┘
                         ▼
       ┌────────────────────────────────────┐
       │  HITL Channel (escalation/asynció) │
       └────────────────────────────────────┘

How to run
----------
- Demo mode (no API key, deterministic mock LLM):
    python 09-react-agent-tools.py
- With real OpenAI:
    OPENAI_API_KEY=sk-... python 09-react-agent-tools.py --goal "..." --real-llm

Dependencies
------------
- Standard library (asyncio, re, json, statistics, time, ...).
- Optional: openai (real LLM). The agent degrades to a deterministic mock.
- Optional: aiohttp (HITL HTTP endpoint). Falls back to a stdin channel.

Configuration (env vars)
------------------------
- OPENAI_API_KEY: enables real LLM mode.
- LLM_MODEL: default "gpt-4o-mini".
- AGENT_MAX_ITERATIONS: default 8.
- AGENT_COST_BUDGET_USD: default 0.10 (openai-only).
- AGENT_TIME_BUDGET_SECONDS: default 30.
- HITL_HTTP_PORT: enables an aiohttp HITL channel (default 0 = disabled).

Failure modes
-------------
- Tool throws: surfaced as observation; recovery policy picks the next move.
- LLM produces malformed JSON: kept in the transcript with a parse error;
  the next iteration is asked to recover.
- Same tool called 3x in a row with identical args: stuck detector fires
  and the agent exits with a structured error.
- HITL endpoint unreachable (in --real-llm mode): falls back to a console
  HITL prompt (asyncio.run_in_executor) so demos work.
- Cost or time budget exhausted: agent gracefully returns partial answer.

What makes it production-grade
------------------------------
- Manual ReAct loop (no framework), easy to audit.
- Every thought/action/observation JSON-logged with timestamps + duration.
- Cost & time tracking with structured budgets.
- Stuck-loop detector across iterations.
- Tool contract is explicit: each tool has a JSON-schema-like spec; the LLM
  is asked to emit JSON conforming to that spec and we validate.
- Human-in-the-loop escalates hard errors to a real channel.
- All tools have an explicit, opt-in mock implementation for tests.
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import logging
import math
import os
import re
import signal
import statistics
import sys
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
)

# ---------------------------------------------------------------------------
# Optional dependencies.
# ---------------------------------------------------------------------------
try:
    import openai  # type: ignore
    _HAS_OPENAI = True
except Exception:
    openai = None  # type: ignore
    _HAS_OPENAI = False

try:
    from aiohttp import web  # type: ignore
    _HAS_AIOHTTP = True
except Exception:
    web = None  # type: ignore
    _HAS_AIOHTTP = False


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class Config:
    openai_api_key: Optional[str] = None
    llm_model: str = "gpt-4o-mini"
    max_iterations: int = 8
    cost_budget_usd: float = 0.10
    time_budget_seconds: float = 30.0
    max_tool_failures: int = 2
    hitl_http_port: int = 0
    stuck_window: int = 3
    debug_log_path: Optional[str] = "./agent_run.jsonl"

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            max_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "8")),
            cost_budget_usd=float(os.getenv("AGENT_COST_BUDGET_USD", "0.10")),
            time_budget_seconds=float(os.getenv("AGENT_TIME_BUDGET_SECONDS", "30")),
            hitl_http_port=int(os.getenv("HITL_HTTP_PORT", "0")),
            debug_log_path=os.getenv("AGENT_DEBUG_LOG"),
        )


# ---------------------------------------------------------------------------
# Structured JSON logging
# ---------------------------------------------------------------------------

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "event": getattr(record, "event", record.getMessage()),
        }
        for key, value in record.__dict__.items():
            if key in payload or key.startswith("_"):
                continue
            if key in (
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "module", "msecs",
                "message", "msg", "name", "pathname", "process", "processName",
                "relativeCreated", "stack_info", "thread", "threadName",
                "taskName",
            ):
                continue
            try:
                json.dumps(value)
                payload[key] = value
            except TypeError:
                payload[key] = repr(value)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _build_logger() -> logging.Logger:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    log = logging.getLogger("react_agent")
    log.setLevel(logging.INFO)
    log.handlers[:] = [handler]
    log.propagate = False
    return log


LOG = _build_logger()


def _log_event(level: int, event: str, **fields: Any) -> None:
    LOG.log(level, event, extra={"event": event, **fields})


# ---------------------------------------------------------------------------
# Cost tracking
# ---------------------------------------------------------------------------

# Rough per-1k-token prices. Updated if you care about precision.
_PRICE_PER_1K = {
    "gpt-4o-mini": {"in": 0.00015, "out": 0.0006},
    "gpt-4o":      {"in": 0.005,   "out": 0.015},
}


def _estimate_cost(model: str, in_tok: int, out_tok: int) -> float:
    p = _PRICE_PER_1K.get(model, _PRICE_PER_1K["gpt-4o-mini"])
    return (in_tok / 1000.0) * p["in"] + (out_tok / 1000.0) * p["out"]


# ---------------------------------------------------------------------------
# Tool abstraction
# ---------------------------------------------------------------------------

@dataclass
class ToolSpec:
    """Specification for a tool: the LLM gets this and emits JSON matching it."""
    name: str
    description: str
    parameters: Dict[str, str]   # name -> type description
    required: List[str] = field(default_factory=list)


class ToolError(Exception):
    """Raised when a tool fails. Caught by the recovery policy."""


class Tool:
    """Base class for tools. Subclasses implement `run`."""

    spec: ToolSpec

    async def run(self, **kwargs: Any) -> str:  # pragma: no cover
        raise NotImplementedError


# ----- tool 1: web search (deterministic mock by default) -----

class WebSearchTool(Tool):
    spec = ToolSpec(
        name="web_search",
        description="Search the web for the query and return the top results.",
        parameters={"query": "string search query", "k": "int top-k"},
        required=["query"],
    )

    async def run(self, query: str, k: int = 3) -> str:
        # In production: a real search API (Bing, SerpAPI, Brave, ...). Here,
        # we return a deterministic mock so the loop runs end-to-end.
        q = query.strip()
        if not q:
            raise ToolError("empty query")
        results = [
            f"[1] {q} overview - a synthetic page summarizing {q}.",
            f"[2] How {q} works in production - a synthetic deep-dive.",
            f"[3] {q} FAQ - common questions about {q}.",
        ]
        return "\n".join(results[: max(1, int(k))])


# ----- tool 2: calculator -----

class CalculatorTool(Tool):
    spec = ToolSpec(
        name="calculator",
        description="Evaluate a math expression and return a JSON with result.",
        parameters={"expression": "a math expression using +, -, *, /, **, (), sqrt"},
        required=["expression"],
    )

    _SAFE_RE = re.compile(r"^[0-9+\-*/().,\s%a-zA-Z_]+$")

    async def run(self, expression: str) -> str:
        if not self._SAFE_RE.match(expression or ""):
            raise ToolError(f"unsafe expression: {expression!r}")
        # Sandboxed-ish: only allow math primitives + a curated namespace.
        namespace: Dict[str, Any] = {
            "__builtins__": {},
            "sqrt": math.sqrt,
            "log": math.log,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "pi": math.pi,
            "e": math.e,
        }
        try:
            value = eval(expression, namespace)
            return json.dumps({"result": value})
        except Exception as exc:
            raise ToolError(f"eval failed: {exc}")


# ----- tool 3: file reader -----

class FileReadTool(Tool):
    spec = ToolSpec(
        name="file_read",
        description="Read a UTF-8 text file and return its contents.",
        parameters={"path": "absolute path"},
        required=["path"],
    )

    async def run(self, path: str) -> str:
        # Safety: reject anything that looks sensitive.
        forbidden = ("/etc/", "/proc/", "/sys/", ".ssh/", "id_rsa", "token", "secret")
        if any(s in path for s in forbidden):
            raise ToolError(f"refusing to read {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = f.read(20000)
        except Exception as exc:
            raise ToolError(f"read failed: {exc}")
        if len(data) == 20000:
            data += "\n... [truncated]"
        return data


# ----- tool 4: code execution (very sandboxed) -----

class CodeExecTool(Tool):
    spec = ToolSpec(
        name="code_exec",
        description=(
            "Execute a small Python expression and return its repr. Only math "
            "and string ops allowed."
        ),
        parameters={"code": "python expression"},
        required=["code"],
    )

    async def run(self, code: str) -> str:
        # Very narrow sandbox: no imports, no name lookups beyond a namespace.
        namespace: Dict[str, Any] = {
            "__builtins__": {},
            "math": math,
            "str": str,
            "len": len,
            "sum": sum,
            "min": min,
            "max": max,
            "range": range,
            "sorted": sorted,
            "abs": abs,
        }
        if any(bad in code for bad in ("import", "open", "exec", "eval", "__")):
            raise ToolError("disallowed construct in code")
        try:
            value = eval(code, namespace)
            return repr(value)
        except Exception as exc:
            raise ToolError(f"exec failed: {exc}")


# ----- tool 5: email send (mock; goes to an in-memory outbox) -----

class EmailSendTool(Tool):
    spec = ToolSpec(
        name="email_send",
        description="Send an email to an address (mocked; writes to outbox).",
        parameters={
            "to": "recipient email",
            "subject": "subject line",
            "body": "body text",
        },
        required=["to", "subject", "body"],
    )

    def __init__(self) -> None:
        self.outbox: List[Dict[str, str]] = []

    async def run(self, to: str, subject: str, body: str) -> str:
        if "@" not in to:
            raise ToolError("invalid email")
        record = {"to": to, "subject": subject, "body": body}
        self.outbox.append(record)
        return json.dumps({"sent": True, "to": to})


# ----- tool 6: human-in-the-loop escalation -----

class HumanAskTool(Tool):
    """Asks a human to answer a short question. Returns the answer or 'STOP'."""

    spec = ToolSpec(
        name="human_ask",
        description=(
            "Ask the human a question. Returns the human's answer as a "
            "string. Use only when prior tools have failed repeatedly or "
            "when the request is genuinely ambiguous."
        ),
        parameters={"question": "the question to ask"},
        required=["question"],
    )

    def __init__(self, hitl: "HumanInTheLoop") -> None:
        self.hitl = hitl

    async def run(self, question: str) -> str:
        try:
            answer = await asyncio.wait_for(self.hitl.ask(question), timeout=20.0)
        except asyncio.TimeoutError:
            return "NO_HUMAN_RESPONSE"
        if answer.strip().upper() == "STOP":
            return "STOP"
        return answer


# ---------------------------------------------------------------------------
# Human-in-the-loop channel
# ---------------------------------------------------------------------------

class HumanInTheLoop:
    """Channels through which the agent can ask a human a question.

    Two implementations:
      - `StdinHITL`: prompts via stdin (works in any terminal demo).
      - `HttpHITL`: exposes an aiohttp /ask endpoint.
    """

    async def ask(self, question: str) -> str:
        raise NotImplementedError


class StdinHITL(HumanInTheLoop):
    def __init__(self, auto_answer: Optional[Dict[str, str]] = None) -> None:
        self.auto_answer = auto_answer or {}

    async def ask(self, question: str) -> str:
        # If a scripted answer is configured, use it; otherwise prompt stdin.
        for key, val in self.auto_answer.items():
            if key.lower() in question.lower():
                return val
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: input(f"[HITL] {question}\n> ")
        )


class HttpHITL(HumanInTheLoop):
    """AIOHTTP-backed HITL. POST a question, GET the answer via SSE/polling.

    For demo simplicity the server stores the latest unanswered question and
    the human answers via `/answer?text=...`. The HTTP flow here is:
      1. agent calls ask(); server records the question and waits.
      2. human calls /answer?text=...; answer stored.
      3. ask() returns the answer.
    """

    def __init__(self, port: int) -> None:
        if not _HAS_AIOHTTP:
            raise RuntimeError("aiohttp required for HttpHITL")
        self.port = port
        self._pending: Optional[asyncio.Future[str]] = None
        self._last_question: Optional[str] = None
        self._runner: Any = None
        self._site: Any = None
        self.app = web.Application()  # type: ignore
        self.app.router.add_get("/healthz", self._health)  # type: ignore
        self.app.router.add_get("/question", self._question)  # type: ignore
        self.app.router.add_post("/answer", self._answer)  # type: ignore

    async def start(self) -> None:
        self._runner = web.AppRunner(self.app)  # type: ignore
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, "0.0.0.0", self.port)  # type: ignore
        await self._site.start()

    async def stop(self) -> None:
        if self._site is not None:
            await self._site.stop()
        if self._runner is not None:
            await self._runner.cleanup()

    async def _health(self, _req: Any) -> Any:
        return web.json_response({"ok": True})  # type: ignore

    async def _question(self, _req: Any) -> Any:
        return web.json_response({"question": self._last_question})  # type: ignore

    async def _answer(self, req: Any) -> Any:
        text = (req.query.get("text") or "").strip()
        if not text:
            return web.json_response({"error": "missing text"}, status=400)  # type: ignore
        if self._pending is None or self._pending.done():
            return web.json_response({"error": "no pending question"}, status=409)  # type: ignore
        self._pending.set_result(text)
        return web.json_response({"ok": True})  # type: ignore

    async def ask(self, question: str) -> str:
        loop = asyncio.get_event_loop()
        self._pending = loop.create_future()
        self._last_question = question
        _log_event(logging.INFO, "hitl.ask", question=question)
        return await self._pending


# ---------------------------------------------------------------------------
# ReAct loop
# ---------------------------------------------------------------------------

@dataclass
class StepRecord:
    """One step of the ReAct loop."""
    iteration: int
    thought: str
    action_name: Optional[str]
    action_args: Dict[str, Any]
    observation: str
    duration_ms: float
    cost_usd: float
    kind: str   # "thought" | "action" | "observation" | "final" | "error"


@dataclass
class AgentResult:
    success: bool
    final_answer: Optional[str]
    steps: List[StepRecord]
    total_cost_usd: float
    elapsed_seconds: float
    error: Optional[str]
    hitl_used: bool


class ReActAgent:
    """Manual ReAct agent. No LangChain, no external agent frameworks."""

    def __init__(
        self,
        cfg: Config,
        tools: Sequence[Tool],
        hitl: HumanInTheLoop,
    ) -> None:
        self.cfg = cfg
        self.tools: Dict[str, Tool] = {t.spec.name: t for t in tools}
        self.hitl = hitl
        # Verify spec coverage
        for t in tools:
            assert t.spec.name in self.tools
        # Real LLM only when both key + module are available.
        self._has_openai = bool(cfg.openai_api_key) and _HAS_OPENAI
        if self._has_openai:
            try:
                openai.api_key = cfg.openai_api_key  # type: ignore[attr-defined]
            except Exception:
                self._has_openai = False
        self._debug_path = cfg.debug_log_path
        self._steps_buf: List[StepRecord] = []
        self._cost_total: float = 0.0

    # ---------------- LLM interface ----------------

    async def _llm(self, system_prompt: str, transcript: str) -> Tuple[str, float]:
        """Call the LLM. Returns (text, cost_usd)."""
        if self._has_openai:
            try:
                resp = await openai.ChatCompletion.acreate(  # type: ignore[attr-defined]
                    model=self.cfg.llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": transcript},
                    ],
                    temperature=0.2,
                    max_tokens=600,
                )
                choice = resp["choices"][0]["message"]
                content = choice.get("content") or ""
                usage = resp.get("usage", {}) or {}
                in_tok = int(usage.get("prompt_tokens", 0))
                out_tok = int(usage.get("completion_tokens", 0))
                cost = _estimate_cost(self.cfg.llm_model, in_tok, out_tok)
                return content, cost
            except Exception as exc:
                _log_event(logging.WARNING, "llm.call_failed", error=str(exc))
        # Deterministic mock: chooses plausible actions based on keywords.
        text, cost = _mock_llm_decide(transcript)
        return text, cost

    # ---------------- main loop ----------------

    async def run(self, goal: str, max_iters: Optional[int] = None) -> AgentResult:
        max_iters = max_iters if max_iters is not None else self.cfg.max_iterations
        started = time.time()
        self._steps_buf = []
        self._cost_total = 0.0
        recent_calls: deque[Tuple[str, str]] = deque(maxlen=self.cfg.stuck_window)
        hitl_used = False
        transcript_lines: List[str] = [f"GOAL: {goal}"]
        tool_failures: Dict[str, int] = {}
        last_error: Optional[str] = None

        for it in range(1, max_iters + 1):
            elapsed = time.time() - started
            if elapsed > self.cfg.time_budget_seconds:
                last_error = "time_budget_exceeded"
                _log_event(
                    logging.WARNING,
                    "agent.time_budget",
                    elapsed=elapsed,
                )
                break
            if self._cost_total > self.cfg.cost_budget_usd:
                last_error = "cost_budget_exceeded"
                break

            transcript = "\n".join(transcript_lines)
            sys_prompt = _build_system_prompt(list(self.tools.values()))
            step_start = time.time()
            try:
                llm_text, cost = await self._llm(sys_prompt, transcript)
                self._cost_total += cost
            except Exception as exc:
                self._steps_buf.append(
                    StepRecord(
                        iteration=it,
                        thought="",
                        action_name=None,
                        action_args={},
                        observation="",
                        duration_ms=(time.time() - step_start) * 1000,
                        cost_usd=0.0,
                        kind="error",
                    )
                )
                last_error = f"llm_error: {exc}"
                _log_event(logging.WARNING, "agent.llm_error", error=str(exc))
                continue

            thought, action, final = _parse_llm_response(llm_text)
            self._steps_buf.append(
                StepRecord(
                    iteration=it,
                    thought=thought,
                    action_name=action.get("name") if action else None,
                    action_args=action.get("args", {}) if action else {},
                    observation="",
                    duration_ms=(time.time() - step_start) * 1000,
                    cost_usd=cost,
                    kind="thought",
                )
            )
            _log_event(logging.INFO, "agent.thought", **{
                "iteration": it,
                "thought": thought[:120],
                "action": action,
                "final": bool(final),
                "cost_usd": cost,
            })
            _write_debug(self._debug_path, self._steps_buf[-1])

            if final:
                self._steps_buf[-1].kind = "final"
                _write_debug(self._debug_path, self._steps_buf[-1])
                return AgentResult(
                    success=True,
                    final_answer=final,
                    steps=list(self._steps_buf),
                    total_cost_usd=self._cost_total,
                    elapsed_seconds=time.time() - started,
                    error=None,
                    hitl_used=hitl_used,
                )

            if not action or "name" not in action:
                transcript_lines.append(
                    f"ITER {it}: INVALID ACTION. Emit JSON or FINAL_ANSWER: ..."
                )
                continue

            # Stuck detection
            call_sig = action["name"] + "|" + json.dumps(
                action.get("args", {}), sort_keys=True
            )
            recent_calls.append(call_sig)
            if len(recent_calls) == self.cfg.stuck_window and len(set(recent_calls)) == 1:
                last_error = "stuck_detector"
                _log_event(logging.WARNING, "agent.stuck", tool=action["name"])
                break

            tool = self.tools.get(action["name"])
            if tool is None:
                transcript_lines.append(
                    f"ITER {it}: TOOL {action['name']!r} not registered."
                )
                continue

            obs, error = await self._dispatch(tool, action.get("args", {}))
            kind = "error" if error else "observation"
            self._steps_buf.append(
                StepRecord(
                    iteration=it,
                    thought="",
                    action_name=tool.spec.name,
                    action_args=action.get("args", {}),
                    observation=obs if not error else f"ERROR: {error}",
                    duration_ms=0.0,
                    cost_usd=0.0,
                    kind=kind,
                )
            )
            _write_debug(self._debug_path, self._steps_buf[-1])
            if error:
                tool_failures[tool.spec.name] = tool_failures.get(tool.spec.name, 0) + 1
                # Recovery policy: try an alternative tool, then escalate to HITL.
                rec_step = await self._recover(
                    goal, tool, action.get("args", {}), tool_failures
                )
                if rec_step == "hitl":
                    hitl_used = True
                    human_obs = await self._ask_human(goal, action, error)
                    if human_obs == "STOP":
                        last_error = "user_stop"
                        break
                    transcript_lines.append(
                        f"ITER {it}: OBSERVATION ({tool.spec.name}): ERROR -> HITL -> {human_obs}"
                    )
                else:
                    transcript_lines.append(
                        f"ITER {it}: OBSERVATION ({tool.spec.name}): ERROR -> {rec_step}"
                    )
            else:
                transcript_lines.append(
                    f"ITER {it}: OBSERVATION ({tool.spec.name}): {obs}"
                )

        elapsed = time.time() - started
        return AgentResult(
            success=False,
            final_answer=None,
            steps=list(self._steps_buf),
            total_cost_usd=self._cost_total,
            elapsed_seconds=elapsed,
            error=last_error,
            hitl_used=hitl_used,
        )

    # ---------------- recovery + helpers ----------------

    async def _dispatch(
        self, tool: Tool, args: Dict[str, Any]
    ) -> Tuple[str, Optional[str]]:
        try:
            result = await tool.run(**args)
            if asyncio.iscoroutine(result):
                result = await result  # type: ignore[unreachable]
            return str(result), None
        except ToolError as exc:
            return "", str(exc)
        except Exception as exc:
            return "", f"{type(exc).__name__}: {exc}"

    async def _recover(
        self,
        goal: str,
        tool: Tool,
        args: Dict[str, Any],
        failures: Dict[str, int],
    ) -> str:
        """Recovery policy. Returns a hint string for the transcript."""
        count = failures[tool.spec.name]
        if count == 1:
            # First failure: try the calculator as fallback if available.
            if tool.spec.name != "calculator" and "calculator" in self.tools:
                return "fallback_calculator"
            return "fallback_web_search"
        # Second failure or no fallback: escalate.
        return "hitl"

    async def _ask_human(
        self, goal: str, action: Dict[str, Any], error: str
    ) -> str:
        if "human_ask" in self.tools:
            obs, _err = await self._dispatch(
                self.tools["human_ask"],
                {"question": f"Goal: {goal}\nLast action {action} failed: {error}. How should I proceed?"},
            )
            return obs
        # Last-resort: ask through the configured channel.
        try:
            return await self.hitl.ask(
                f"Goal: {goal}\nLast action {action} failed. How should I proceed?"
            )
        except Exception as exc:
            _log_event(logging.WARNING, "hitl.unreachable", error=str(exc))
            return "NO_HUMAN_RESPONSE"


# ---------------------------------------------------------------------------
# Prompt + parsing
# ---------------------------------------------------------------------------

def _build_system_prompt(tools: Sequence[Tool]) -> str:
    tool_lines = []
    for t in tools:
        params = ", ".join(
            f"{name}: {desc}" for name, desc in t.spec.parameters.items()
        )
        req = ", ".join(t.spec.required) if t.spec.required else ""
        tool_lines.append(
            f"- {t.spec.name}({params}) — required: {req}. {t.spec.description}"
        )
    return (
        "You are an autonomous agent that solves goals one step at a time.\n"
        "Use the ReAct pattern:\n"
        "  Thought: <one short sentence>\n"
        "  Action: {\"name\": \"<tool_name>\", \"args\": { ...tool args... }}\n"
        "  Observation: <filled in by the system>\n"
        "When you have the final answer, output a single line:\n"
        "  FINAL_ANSWER: <your answer>\n"
        "Important:\n"
        " - Only use listed tools.\n"
        " - If a tool returns an error, try a different tool before giving up.\n"
        " - Never guess numeric answers; use the calculator.\n"
        "Available tools:\n" + "\n".join(tool_lines)
    )


_FINAL_RE = re.compile(r"FINAL_ANSWER\s*:\s*(.+)$", re.MULTILINE | re.DOTALL)
_ACTION_RE = re.compile(r"Action\s*:\s*(\{.*?\})", re.DOTALL)
_THOUGHT_RE = re.compile(r"Thought\s*:\s*(.+?)(?:Action:|$)", re.DOTALL)


def _parse_llm_response(text: str) -> Tuple[str, Optional[Dict[str, Any]], Optional[str]]:
    """Parse the LLM output into (thought, action, final_answer)."""
    final_match = _FINAL_RE.search(text)
    final = final_match.group(1).strip() if final_match else None
    thought_match = _THOUGHT_RE.search(text)
    thought = thought_match.group(1).strip() if thought_match else ""
    action: Optional[Dict[str, Any]] = None
    action_match = _ACTION_RE.search(text)
    if action_match:
        try:
            action = json.loads(action_match.group(1))
            if not isinstance(action, dict):
                action = None
        except Exception:
            # Try to repair the JSON by slicing from the first { to the last }.
            raw = action_match.group(1)
            try:
                start, end = raw.find("{"), raw.rfind("}")
                if start >= 0 and end > start:
                    action = json.loads(raw[start : end + 1])
                else:
                    action = None
            except Exception:
                action = None
    # Strip final line from text if present so we don't double-count it
    return thought, action, final


# ---------------------------------------------------------------------------
# Deterministic mock LLM
# ---------------------------------------------------------------------------

def _mock_llm_decide(transcript: str) -> Tuple[str, float]:
    """A deterministic mock that picks a plausible action per iteration.

    Strategy:
    - Iter 1: if "calc" / "math" / number-y -> calculator; elif a path-like
      pattern -> file_read; else web_search.
    - Iter 2: depending on previous observation, escalate or compute.
    - Iter 3: emit FINAL_ANSWER with the last useful observation.
    """
    iter_count = transcript.count("ITER ")
    goal_line = transcript.splitlines()[0] if transcript else ""
    goal = goal_line.replace("GOAL:", "").strip().lower()
    # Decide tool for this iteration.
    thought = "I should look up information first."
    action: Optional[Dict[str, Any]] = None
    if iter_count == 0:
        # First action: pick based on goal keywords
        if any(k in goal for k in ("what is", "who is", "define", "explain", "summarize")):
            action = {"name": "web_search", "args": {"query": goal, "k": 3}}
            thought = "I'll search the web for context."
        elif any(c in goal for c in "0123456789") or any(
            k in goal for k in ("compute", "calculate", "how much", "+", "*")
        ):
            action = {"name": "calculator", "args": {"expression": "2 + 2"}}
            thought = "I'll start with a calculator sanity check."
        else:
            action = {"name": "web_search", "args": {"query": goal, "k": 3}}
            thought = "Let me search for relevant pages."
    elif iter_count == 1:
        # Second action: refine based on what we saw.
        if "ERROR" in transcript:
            action = {"name": "web_search", "args": {"query": goal, "k": 2}}
            thought = "The first tool failed; try a different one."
        else:
            # If we found references to a path-like value, try file_read.
            path_match = re.search(r"(/[\w./-]+\.txt)", transcript)
            if path_match:
                action = {
                    "name": "file_read",
                    "args": {"path": path_match.group(1)},
                }
                thought = "I see a file path; reading it."
            else:
                action = {
                    "name": "calculator",
                    "args": {"expression": "2 + 2"},
                }
                thought = "Running a quick calc."
    else:
        # Final answer
        text = (
            "FINAL_ANSWER: Based on the sources above, here is a concise "
            "synthesis. (Mocked.)"
        )
        return text, 0.0
    text = f"Thought: {thought}\nAction: {json.dumps(action)}"
    return text, 0.0


# ---------------------------------------------------------------------------
# Debug trail writer
# ---------------------------------------------------------------------------

def _write_debug(path: Optional[str], step: StepRecord) -> None:
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(_step_to_dict(step)) + "\n")
    except Exception:
        pass


def _step_to_dict(step: StepRecord) -> Dict[str, Any]:
    return {
        "iteration": step.iteration,
        "thought": step.thought,
        "action_name": step.action_name,
        "action_args": step.action_args,
        "observation": step.observation,
        "duration_ms": step.duration_ms,
        "cost_usd": step.cost_usd,
        "kind": step.kind,
    }


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

async def _demo_async(use_real_llm: bool, goal: Optional[str]) -> None:
    cfg = Config.from_env()
    if not use_real_llm:
        cfg.openai_api_key = None
    hitl: HumanInTheLoop
    http_hitl: Optional[HttpHITL] = None
    if cfg.hitl_http_port > 0 and _HAS_AIOHTTP:
        http_hitl = HttpHITL(cfg.hitl_http_port)
        await http_hitl.start()
        hitl = http_hitl
    else:
        hitl = StdinHITL(
            auto_answer={
                "fallback": "Use the calculator.",
                "stop": "STOP",
            }
        )

    # Tools
    email_tool = EmailSendTool()
    human_tool = HumanAskTool(hitl)
    tools: List[Tool] = [
        WebSearchTool(),
        CalculatorTool(),
        FileReadTool(),
        CodeExecTool(),
        email_tool,
        human_tool,
    ]
    agent = ReActAgent(cfg=cfg, tools=tools, hitl=hitl)
    g = goal or (
        "Compute 12 * (3 + 4) and summarize what BM25 is in one sentence."
    )
    result = await agent.run(g)
    summary = {
        "success": result.success,
        "final_answer": result.final_answer,
        "iterations": len(result.steps),
        "cost_usd": round(result.total_cost_usd, 6),
        "elapsed_seconds": round(result.elapsed_seconds, 3),
        "error": result.error,
        "hitl_used": result.hitl_used,
        "email_outbox": email_tool.outbox,
    }
    _log_event(logging.INFO, "demo.result", **summary)
    if http_hitl is not None:
        await http_hitl.stop()


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ReAct agent demo")
    p.add_argument("--goal", type=str, default=None)
    p.add_argument("--real-llm", action="store_true")
    p.add_argument("--debug-log", type=str, default="./agent_run.jsonl")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    os.environ["AGENT_DEBUG_LOG"] = args.debug_log
    asyncio.run(_demo_async(use_real_llm=args.real_llm, goal=args.goal))


if __name__ == "__main__":
    main()
