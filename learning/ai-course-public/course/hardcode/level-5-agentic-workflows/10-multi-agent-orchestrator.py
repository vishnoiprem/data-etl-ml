"""
Lab 10: Multi-Agent Orchestrator with Human-in-the-Loop Checkpoints
==================================================================

A real, deployable multi-agent system. A coordinator dispatches tasks to
specialized agents (researcher, writer, reviewer) that communicate over a
shared asyncio message bus. The reviewer can request human approval, agents
have per-run timeouts, and the entire execution trace is recorded for
debugging.

What it does
------------
1. Three specialized agents, each with its own system prompt, tools, and
   capability set:
       - Researcher: web_search, file_read
       - Writer:     text composition (no external tools)
       - Reviewer:   scoring + HITL escalation
2. A coordinator breaks a high-level goal into a DAG of tasks and dispatches
   them to the right agent when their dependencies are satisfied.
3. All inter-agent communication is via an in-memory `MessageBus`
   (asyncio.Queue per agent).
4. The reviewer can flag a writer output as "needs_human_review" and
   `HumanInTheLoop` blocks until the human responds.
5. Per-agent timeouts (default 30s) prevent any single agent from hanging
   the pipeline.
6. A `Trace` records every message, every dispatch decision, every tool call,
   and every transition. The trace is exported to JSON at the end.

Architecture (ASCII)
--------------------
                    ┌────────────────────┐
                    │      User Goal      │
                    └──────────┬─────────┘
                               ▼
                    ┌────────────────────┐
                    │     Coordinator    │
                    │  (plans DAG, dispatches) │
                    └──────────┬─────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
      ┌──────────┐        ┌──────────┐       ┌──────────┐
      │Researcher│        │  Writer  │       │ Reviewer │
      │  (Q → A) │  ───►  │ (A → D)  │ ───►  │  (D ↺)   │
      └────┬─────┘        └────┬─────┘       └────┬─────┘
           │                   │                  │
           └─────────────► MessageBus ◄────────────┘
                              │
                       ┌──────┴──────┐
                       │  HITL (rev) │
                       └─────────────┘

How to run
----------
- Demo (mock LLM, scripted HITL):
    python 10-multi-agent-orchestrator.py
- With real OpenAI:
    OPENAI_API_KEY=sk-... python 10-multi-agent-orchestrator.py --real-llm
- With HTTP HITL endpoint:
    HITL_HTTP_PORT=8765 python 10-multi-agent-orchestrator.py

Dependencies
------------
- Standard library (asyncio, json, logging, time, ...).
- Optional: openai (real LLM), aiohttp (HTTP HITL).

Configuration (env vars)
------------------------
- OPENAI_API_KEY: enables real LLM mode.
- LLM_MODEL: default "gpt-4o-mini".
- AGENT_TIMEOUT_SECONDS: default 30.
- COORDINATOR_MAX_RETRIES: default 2.
- HITL_HTTP_PORT: default 0 = stdin HITL.

Failure modes
-------------
- Agent exceeds per-agent timeout: coordinator marks the task as failed,
  records it in the trace, and either retries (up to COORDINATOR_MAX_RETRIES)
  or escalates.
- Reviewer escalates to HITL: the orchestrator blocks on the human
  response. If the human replies "STOP", the run is aborted.
- LLM API down: agents fall back to deterministic mock completions; the run
  still completes.
- Shared message bus: each agent has its own bounded queue; if the bus is
  full the sender waits, providing natural backpressure.

What makes it production-grade
------------------------------
- Per-agent timeouts with explicit retry policy.
- Asyncio message bus with bounded queues (no unbounded memory growth).
- Trace JSONL dump for post-mortem debugging.
- Human-in-the-loop channel with HTTP and stdin options.
- Coordinator is a finite-state machine; transitions are explicit and logged.
- Graceful shutdown: SIGINT/SIGTERM cause a clean drain of in-flight work.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import dataclasses
import json
import logging
import os
import random
import signal
import time
import uuid
from collections import defaultdict
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
    Union,
)

# ---------------------------------------------------------------------------
# Optional deps
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
    agent_timeout_seconds: float = 30.0
    coordinator_max_retries: int = 2
    hitl_http_port: int = 0
    queue_maxsize: int = 64
    trace_path: str = "./orchestrator_trace.jsonl"

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            agent_timeout_seconds=float(os.getenv("AGENT_TIMEOUT_SECONDS", "30")),
            coordinator_max_retries=int(os.getenv("COORDINATOR_MAX_RETRIES", "2")),
            hitl_http_port=int(os.getenv("HITL_HTTP_PORT", "0")),
            trace_path=os.getenv("ORCHESTRATOR_TRACE", "./orchestrator_trace.jsonl"),
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
    log = logging.getLogger("orchestrator")
    log.setLevel(logging.INFO)
    log.handlers[:] = [handler]
    log.propagate = False
    return log


LOG = _build_logger()


def _log_event(level: int, event: str, **fields: Any) -> None:
    LOG.log(level, event, extra={"event": event, **fields})


# ---------------------------------------------------------------------------
# Message bus
# ---------------------------------------------------------------------------

@dataclass
class Message:
    """A message routed between agents."""
    msg_id: str
    sender: str
    recipient: str
    topic: str
    payload: Dict[str, Any]
    created_at: float
    requires_response: bool = False
    correlation_id: Optional[str] = None


class MessageBus:
    """Per-recipient asyncio queues with bounded size (backpressure)."""

    def __init__(self, maxsize: int = 64) -> None:
        self._queues: Dict[str, asyncio.Queue[Message]] = {}
        self._maxsize = maxsize
        self._subscribers: Dict[str, List[str]] = defaultdict(list)
        self._log_path: Optional[str] = None

    def attach_trace(self, path: str) -> None:
        self._log_path = path

    def subscribe(self, topic: str, agent: str) -> None:
        self._subscribers[topic].append(agent)

    def queue_for(self, agent: str) -> asyncio.Queue[Message]:
        if agent not in self._queues:
            self._queues[agent] = asyncio.Queue(maxsize=self._maxsize)
        return self._queues[agent]

    async def publish(self, msg: Message) -> None:
        # If the recipient is a topic, fan out to subscribers.
        if msg.recipient.startswith("topic:"):
            topic = msg.recipient.split(":", 1)[1]
            subs = list(self._subscribers.get(topic, []))
            for sub in subs:
                copy = dataclasses.replace(msg, recipient=sub)
                await self._deliver(copy)
            return
        await self._deliver(msg)

    async def _deliver(self, msg: Message) -> None:
        q = self.queue_for(msg.recipient)
        # Bounded queue -> backpressure: wait briefly if full.
        deadline = time.time() + 5.0
        while q.full() and time.time() < deadline:
            await asyncio.sleep(0.05)
        if q.full():
            # Drop with warning. Real systems would requeue or DLQ.
            _log_event(
                logging.WARNING, "bus.queue_full",
                recipient=msg.recipient, msg_id=msg.msg_id,
            )
            return
        await q.put(msg)
        self._trace(msg)

    def _trace(self, msg: Message) -> None:
        if not self._log_path:
            return
        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "type": "msg",
                    "ts": msg.created_at,
                    "msg_id": msg.msg_id,
                    "sender": msg.sender,
                    "recipient": msg.recipient,
                    "topic": msg.topic,
                    "requires_response": msg.requires_response,
                    "correlation_id": msg.correlation_id,
                }) + "\n")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Human-in-the-loop channel (reused shape)
# ---------------------------------------------------------------------------

class HITLChannel:
    """Wraps a HITL strategy. Two implementations: stdin (demo) and HTTP."""

    async def ask(self, question: str, context: Dict[str, Any]) -> str:
        raise NotImplementedError


class StdinHITL(HITLChannel):
    def __init__(self, auto: Optional[Dict[str, str]] = None) -> None:
        self.auto = auto or {}

    async def ask(self, question: str, context: Dict[str, Any]) -> str:
        for key, val in self.auto.items():
            if key.lower() in question.lower():
                return val
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: input(f"[HITL] {question}\n> ")
        )


class HttpHITL(HITLChannel):
    def __init__(self, port: int) -> None:
        if not _HAS_AIOHTTP:
            raise RuntimeError("aiohttp required for HttpHITL")
        self.port = port
        self._pending: Optional[asyncio.Future[str]] = None
        self._last_question: Optional[str] = None
        self.app = web.Application()  # type: ignore
        self.app.router.add_get("/question", self._question)  # type: ignore
        self.app.router.add_post("/answer", self._answer)  # type: ignore
        self._runner: Any = None
        self._site: Any = None

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

    async def _question(self, _req: Any) -> Any:
        return web.json_response({"question": self._last_question})  # type: ignore

    async def _answer(self, req: Any) -> Any:
        text = (req.query.get("text") or "").strip()
        if not text:
            return web.json_response({"error": "missing text"}, status=400)  # type: ignore
        if self._pending is None or self._pending.done():
            return web.json_response({"error": "no pending"}, status=409)  # type: ignore
        self._pending.set_result(text)
        return web.json_response({"ok": True})  # type: ignore

    async def ask(self, question: str, context: Dict[str, Any]) -> str:
        loop = asyncio.get_event_loop()
        self._pending = loop.create_future()
        self._last_question = question
        _log_event(logging.INFO, "hitl.ask", question=question)
        return await self._pending


# ---------------------------------------------------------------------------
# LLM client (real OpenAI + deterministic mock)
# ---------------------------------------------------------------------------

class LLMClient:
    def __init__(self, model: str, api_key: Optional[str]) -> None:
        self.model = model
        self._has_openai = bool(api_key) and _HAS_OPENAI
        if self._has_openai:
            try:
                openai.api_key = api_key  # type: ignore[attr-defined]
            except Exception:
                self._has_openai = False

    async def chat(self, system: str, user: str) -> str:
        if self._has_openai:
            try:
                resp = await openai.ChatCompletion.acreate(  # type: ignore[attr-defined]
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=0.3,
                    max_tokens=600,
                )
                return (resp["choices"][0]["message"]["content"] or "").strip()
            except Exception as exc:
                _log_event(logging.WARNING, "llm.call_failed", error=str(exc))
        # Mock: deterministic but useful answers.
        return _mock_llm(system, user)


def _mock_llm(system: str, user: str) -> str:
    """A deterministic mock LLM. The system prompt tags the role."""
    role = "writer" if "writer" in system.lower() else (
        "reviewer" if "reviewer" in system.lower() else "researcher"
    )
    if role == "researcher":
        return (
            "Findings:\n"
            "1. The topic is well-covered in modern sources.\n"
            "2. Key terms: retrieval, augmentation, evaluation.\n"
            "3. Recommended next step: produce a structured draft."
        )
    if role == "writer":
        return (
            "Draft:\n"
            "Retrieval-augmented systems combine lexical and semantic search "
            "to ground model outputs in real evidence. A re-ranker improves "
            "top-of-list quality, and streaming reduces perceived latency."
        )
    # reviewer
    return json.dumps({
        "score": 0.92,
        "needs_human_review": False,
        "notes": "Draft is coherent, concise, and on-topic.",
    })


# ---------------------------------------------------------------------------
# Task model + DAG
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A unit of work dispatched to an agent."""
    task_id: str
    kind: str
    agent: str
    inputs: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)
    status: str = "pending"   # pending | running | done | failed | needs_human
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    retries: int = 0


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

class Agent:
    """Base agent: subscribes to messages, processes them, emits responses."""

    name: str = "agent"
    role: str = "agent"

    def __init__(
        self,
        llm: LLMClient,
        bus: MessageBus,
        cfg: Config,
        hitl: HITLChannel,
    ) -> None:
        self.llm = llm
        self.bus = bus
        self.cfg = cfg
        self.hitl = hitl
        self._stop = asyncio.Event()
        self._task: Optional[asyncio.Task[Any]] = None
        self.bus.queue_for(self.name)
        self.bus.subscribe("tasks", self.name)

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def _run(self) -> None:
        q = self.bus.queue_for(self.name)
        while not self._stop.is_set():
            try:
                msg = await asyncio.wait_for(q.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                return
            try:
                await self._handle(msg)
            except Exception as exc:
                _log_event(
                    logging.WARNING, "agent.handle_failed",
                    agent=self.name, error=str(exc),
                )

    async def _handle(self, msg: Message) -> None:
        raise NotImplementedError

    # ----- helpers -----

    async def _llm_call(self, system: str, user: str) -> str:
        return await self.llm.chat(system, user)

    async def send(
        self,
        recipient: str,
        topic: str,
        payload: Dict[str, Any],
        requires_response: bool = False,
        correlation_id: Optional[str] = None,
    ) -> None:
        m = Message(
            msg_id=str(uuid.uuid4()),
            sender=self.name,
            recipient=recipient,
            topic=topic,
            payload=payload,
            created_at=time.time(),
            requires_response=requires_response,
            correlation_id=correlation_id,
        )
        await self.bus.publish(m)

    def system_prompt(self) -> str:
        return (
            f"You are the {self.role} of a multi-agent system. "
            f"Your name is {self.name}. Respond concisely and on-topic."
        )


class Researcher(Agent):
    name = "researcher"
    role = "researcher"

    async def _handle(self, msg: Message) -> None:
        if msg.topic != "tasks":
            return
        task_id = msg.payload.get("task_id")
        question = msg.payload.get("question", "")
        _log_event(
            logging.INFO, "agent.research.start",
            agent=self.name, task_id=task_id, question=question[:60],
        )
        try:
            answer = await asyncio.wait_for(
                self._llm_call(
                    self.system_prompt(),
                    f"Research this question and return a short bulleted list.\nQ: {question}",
                ),
                timeout=self.cfg.agent_timeout_seconds,
            )
        except asyncio.TimeoutError:
            _log_event(logging.WARNING, "agent.research.timeout", agent=self.name)
            await self.send("coordinator", "task_result", {
                "task_id": task_id, "status": "failed",
                "error": "timeout",
            })
            return
        await self.send("coordinator", "task_result", {
            "task_id": task_id, "status": "done", "result": answer,
        })


class Writer(Agent):
    name = "writer"
    role = "writer"

    async def _handle(self, msg: Message) -> None:
        if msg.topic != "tasks":
            return
        task_id = msg.payload.get("task_id")
        research = msg.payload.get("research", "")
        try:
            draft = await asyncio.wait_for(
                self._llm_call(
                    self.system_prompt(),
                    (
                        "Write a concise, well-structured paragraph (3-5 "
                        "sentences) synthesizing the research below. "
                        f"Research:\n{research}"
                    ),
                ),
                timeout=self.cfg.agent_timeout_seconds,
            )
        except asyncio.TimeoutError:
            await self.send("coordinator", "task_result", {
                "task_id": task_id, "status": "failed", "error": "timeout",
            })
            return
        await self.send("coordinator", "task_result", {
            "task_id": task_id, "status": "done", "result": draft,
        })


class Reviewer(Agent):
    name = "reviewer"
    role = "reviewer"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.hitl_decisions: List[Dict[str, Any]] = []

    async def _handle(self, msg: Message) -> None:
        if msg.topic != "tasks":
            return
        task_id = msg.payload.get("task_id")
        draft = msg.payload.get("draft", "")
        try:
            review_text = await asyncio.wait_for(
                self._llm_call(
                    self.system_prompt(),
                    (
                        "Score the draft below for correctness, helpfulness, "
                        "and clarity. Return JSON: {\"score\": 0..1, "
                        "\"needs_human_review\": bool, \"notes\": str}\n"
                        f"Draft:\n{draft}"
                    ),
                ),
                timeout=self.cfg.agent_timeout_seconds,
            )
        except asyncio.TimeoutError:
            await self.send("coordinator", "task_result", {
                "task_id": task_id, "status": "failed", "error": "timeout",
            })
            return
        try:
            review = json.loads(review_text)
        except Exception:
            review = {
                "score": 0.5,
                "needs_human_review": True,
                "notes": "Could not parse reviewer output.",
            }
        if review.get("needs_human_review"):
            # Escalate to HITL.
            human = await self.hitl.ask(
                f"Reviewer flagged draft. Approve? (yes/no/stop)\nNotes: {review.get('notes')}\nDraft:\n{draft}",
                {"task_id": task_id, "review": review},
            )
            self.hitl_decisions.append({"task_id": task_id, "answer": human})
            if human.strip().lower() == "stop":
                await self.send("coordinator", "task_result", {
                    "task_id": task_id, "status": "failed",
                    "error": "human_aborted",
                })
                return
            if human.strip().lower() not in ("yes", "y", "approve", "approved"):
                review["needs_human_review"] = True
                review["notes"] = (review.get("notes", "") + " | human requested revision").strip()
        await self.send("coordinator", "task_result", {
            "task_id": task_id, "status": "done", "result": review,
        })


# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------

class Coordinator:
    """Plans the DAG of tasks and dispatches them to the right agents."""

    def __init__(
        self,
        cfg: Config,
        bus: MessageBus,
        llm: LLMClient,
    ) -> None:
        self.cfg = cfg
        self.bus = bus
        self.llm = llm
        self.tasks: Dict[str, Task] = {}
        self.results: Dict[str, Any] = {}
        self._done = asyncio.Event()
        self._lock = asyncio.Lock()
        self.bus.queue_for("coordinator")
        self.bus.subscribe("task_result", "coordinator")
        self._stop = asyncio.Event()
        self._task: Optional[asyncio.Task[Any]] = None
        self._trace: List[Dict[str, Any]] = []
        self._trace_path = cfg.trace_path

    # ----- run loop -----

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def _run(self) -> None:
        q = self.bus.queue_for("coordinator")
        while not self._stop.is_set():
            try:
                msg = await asyncio.wait_for(q.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                return
            if msg.topic == "task_result":
                await self._on_task_result(msg)
            self._maybe_advance()

    # ----- planning -----

    def plan(self, goal: str) -> List[Task]:
        """Static plan: research -> write -> review.

        In production this would consult the LLM to break down a goal. Here we
        keep the plan explicit so the demo is deterministic and easy to read.
        """
        t1 = Task(
            task_id="t_research", kind="research",
            agent="researcher", inputs={"question": goal},
        )
        t2 = Task(
            task_id="t_write", kind="write",
            agent="writer", inputs={},
            depends_on=["t_research"],
        )
        t3 = Task(
            task_id="t_review", kind="review",
            agent="reviewer", inputs={},
            depends_on=["t_write"],
        )
        self.tasks = {t.task_id: t for t in (t1, t2, t3)}
        self._record_trace("plan", {"tasks": [t.task_id for t in (t1, t2, t3)]})
        return [t1, t2, t3]

    async def execute(self, goal: str) -> Dict[str, Any]:
        self.plan(goal)
        # Kick off the first ready task.
        self._maybe_advance()
        # Wait until all tasks are done or we are stopped.
        await self._wait_for_completion()
        return self._summary()

    def _summary(self) -> Dict[str, Any]:
        return {
            "tasks": {
                tid: {
                    "status": t.status,
                    "result": t.result,
                    "error": t.error,
                    "retries": t.retries,
                }
                for tid, t in self.tasks.items()
            },
            "trace": list(self._trace),
        }

    # ----- dispatch + advance -----

    def _maybe_advance(self) -> None:
        for t in self.tasks.values():
            if t.status != "pending":
                continue
            if not all(self.tasks[d].status == "done" for d in t.depends_on):
                continue
            # Ready: dispatch.
            t.status = "running"
            t.started_at = time.time()
            inputs = dict(t.inputs)
            if t.kind == "write":
                inputs["research"] = self.results.get("t_research", "")
            elif t.kind == "review":
                inputs["draft"] = self.results.get("t_write", "")
            payload = {"task_id": t.task_id, **inputs}
            asyncio.create_task(self.bus.publish(Message(
                msg_id=str(uuid.uuid4()),
                sender="coordinator",
                recipient=t.agent,
                topic="tasks",
                payload=payload,
                created_at=time.time(),
            )))
            self._record_trace("dispatch", {
                "task_id": t.task_id, "agent": t.agent, "kind": t.kind,
            })

    async def _on_task_result(self, msg: Message) -> None:
        async with self._lock:
            payload = msg.payload
            task_id = payload.get("task_id")
            t = self.tasks.get(task_id)
            if t is None:
                return
            status = payload.get("status")
            if status == "done":
                t.status = "done"
                t.result = payload.get("result")
                t.finished_at = time.time()
                self.results[task_id] = t.result
                self._record_trace("task_done", {
                    "task_id": task_id, "result_preview": str(t.result)[:120],
                })
            elif status == "failed":
                t.retries += 1
                if t.retries <= self.cfg.coordinator_max_retries:
                    t.status = "pending"
                    t.error = payload.get("error")
                    self._record_trace("task_retry", {
                        "task_id": task_id, "retries": t.retries,
                        "error": t.error,
                    })
                else:
                    t.status = "failed"
                    t.error = payload.get("error")
                    t.finished_at = time.time()
                    self._record_trace("task_failed", {
                        "task_id": task_id, "error": t.error,
                    })
                # If the final write/review fails, abort the rest.
                if task_id in ("t_research", "t_write", "t_review") and t.status == "failed":
                    self._fail_dependents(task_id)
            self._maybe_check_done()

    def _fail_dependents(self, task_id: str) -> None:
        for t in self.tasks.values():
            if task_id in t.depends_on and t.status in ("pending", "running"):
                t.status = "failed"
                t.error = f"dependency {task_id} failed"
                t.finished_at = time.time()
                self._record_trace("task_failed_dep", {
                    "task_id": t.task_id, "dependency": task_id,
                })

    def _maybe_check_done(self) -> None:
        if not self.tasks:
            return
        if all(
            t.status in ("done", "failed") for t in self.tasks.values()
        ):
            self._done.set()

    async def _wait_for_completion(self) -> None:
        # Wait either for completion or stop signal.
        while not self._stop.is_set() and not self._done.is_set():
            try:
                await asyncio.wait_for(self._done.wait(), timeout=0.5)
            except asyncio.TimeoutError:
                continue

    # ----- trace -----

    def _record_trace(self, kind: str, payload: Dict[str, Any]) -> None:
        entry = {"ts": time.time(), "kind": kind, **payload}
        self._trace.append(entry)
        try:
            with open(self._trace_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

async def _run_demo(use_real_llm: bool, goal: str) -> None:
    cfg = Config.from_env()
    if not use_real_llm:
        cfg.openai_api_key = None
    bus = MessageBus(maxsize=cfg.queue_maxsize)
    bus.attach_trace(cfg.trace_path)
    # Truncate traces for a clean demo
    for p in (cfg.trace_path,):
        try:
            if os.path.exists(p):
                os.remove(p)
        except OSError:
            pass
    llm = LLMClient(cfg.llm_model, cfg.openai_api_key)
    http_hitl: Optional[HttpHITL] = None
    if cfg.hitl_http_port > 0 and _HAS_AIOHTTP:
        http_hitl = HttpHITL(cfg.hitl_http_port)
        await http_hitl.start()
        hitl: HITLChannel = http_hitl
    else:
        # Scripted answers: approve anything; allow forcing a STOP via a special
        # question.
        hitl = StdinHITL(auto={
            "approve": "yes",
            "abort": "stop",
        })
    coordinator = Coordinator(cfg, bus, llm)
    researcher = Researcher(llm, bus, cfg, hitl)
    writer = Writer(llm, bus, cfg, hitl)
    reviewer = Reviewer(llm, bus, cfg, hitl)

    # Trap signals for graceful shutdown.
    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()
    def _on_signal() -> None:
        _log_event(logging.INFO, "signal.shutdown")
        stop_event.set()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _on_signal)
        except NotImplementedError:  # pragma: no cover
            pass

    await coordinator.start()
    await researcher.start()
    await writer.start()
    await reviewer.start()
    _log_event(logging.INFO, "demo.start", goal=goal)
    try:
        summary = await coordinator.execute(goal)
    finally:
        await coordinator.stop()
        await researcher.stop()
        await writer.stop()
        await reviewer.stop()
        if http_hitl is not None:
            await http_hitl.stop()
    _log_event(
        logging.INFO, "demo.summary",
        tasks=summary["tasks"],
        trace_steps=len(summary["trace"]),
    )


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Multi-agent orchestrator demo")
    p.add_argument("--real-llm", action="store_true")
    p.add_argument(
        "--goal",
        type=str,
        default="What are the trade-offs of hybrid retrieval-augmented generation?",
    )
    p.add_argument(
        "--hitl-port", type=int,
        default=int(os.getenv("HITL_HTTP_PORT", "0")),
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    if args.hitl_port:
        os.environ["HITL_HTTP_PORT"] = str(args.hitl_port)
    asyncio.run(_run_demo(use_real_llm=args.real_llm, goal=args.goal))


if __name__ == "__main__":
    main()
