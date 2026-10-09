"""Job scheduler core service.

Three kinds of jobs:

  - ``once``  – run at a specific ``run_at`` time.
  - ``cron``  – run every ``interval_seconds``.
  - ``dag``   – a container of child jobs (each may have
                ``depends_on`` referencing sibling names). The DAG
                runs each child in topological order.

The service persists job and run state to a KeyValueStore and uses
an in-memory sorted-list due queue to dispatch work to a worker
thread. The wall clock is injected (``time_fn``) so tests can
advance time deterministically without sleeping.

This module has no HTTP layer; ``app.py`` is the Flask wrapper.
"""

from __future__ import annotations

import heapq
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from common.cache import TTLCache
from common.ids import Snowflake
from common.storage import KeyValueStore


# ----------------------------- defaults -----------------------------------

DEFAULT_POLL_INTERVAL = 0.1
DEFAULT_MAX_RETRIES = 3
DEFAULT_RUN_HISTORY_CAP = 200


# ----------------------------- exceptions ---------------------------------


class SchedulerError(Exception):
    pass


class JobNotFoundError(SchedulerError):
    pass


class InvalidJobError(SchedulerError):
    pass


class DAGCycleError(SchedulerError):
    pass


# ----------------------------- dataclasses --------------------------------


@dataclass
class Job:
    job_id: int
    name: str
    kind: str           # once | cron | dag
    status: str = "active"  # active | disabled
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    # once
    run_at: Optional[float] = None
    # cron
    interval_seconds: Optional[float] = None
    next_run_at: Optional[float] = None
    # dag
    children: List[int] = field(default_factory=list)
    # shared
    payload: Dict[str, Any] = field(default_factory=dict)
    max_retries: int = DEFAULT_MAX_RETRIES
    last_error: Optional[str] = None
    run_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Run:
    run_id: int
    job_id: int
    started_at: float
    finished_at: Optional[float] = None
    status: str = "running"  # running | success | failed
    trigger: str = "scheduled"  # scheduled | manual
    result: Any = None
    error: Optional[str] = None
    attempt: int = 1

    def to_dict(self) -> dict:
        return asdict(self)


# ----------------------------- runner -------------------------------------


class JobRunner:
    """Runs a job. Returns ``(ok, result_or_error)``."""

    def run(self, job: Job, payload: Dict[str, Any]) -> Tuple[bool, Any]:
        raise NotImplementedError


class FunctionJobRunner(JobRunner):
    """Runs a job whose ``payload['fn']`` is a registered callable name."""

    def __init__(self, registry: Dict[str, Callable[..., Any]]):
        self.registry = registry

    def run(self, job: Job, payload: Dict[str, Any]) -> Tuple[bool, Any]:
        fn_name = payload.get("fn")
        if fn_name is None:
            return False, "payload.fn missing"
        fn = self.registry.get(fn_name)
        if fn is None:
            return False, f"unknown fn '{fn_name}'"
        try:
            result = fn(payload)
            return True, result
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"


# ----------------------------- helpers ------------------------------------


def topo_sort_children(children: List[Job]) -> List[int]:
    """Return job ids of `children` in topological order by name.

    Each child's ``payload['depends_on']`` lists sibling names.
    """
    by_name = {c.name: c for c in children}
    order: List[str] = []
    seen: set = set()
    temp: set = set()

    def visit(name: str) -> None:
        if name in seen:
            return
        if name in temp:
            raise DAGCycleError(f"cycle at '{name}'")
        temp.add(name)
        node = by_name[name]
        for dep in node.payload.get("depends_on", []) or []:
            if dep not in by_name:
                # External dep — treat as already satisfied.
                continue
            visit(dep)
        temp.discard(name)
        seen.add(name)
        order.append(name)

    for c in children:
        visit(c.name)

    return [by_name[n].job_id for n in order]


def validate_job_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Light validation. Returns a normalised spec dict or raises."""
    if not isinstance(spec, dict):
        raise InvalidJobError("job must be an object")
    name = spec.get("name")
    kind = spec.get("kind")
    if not name or not isinstance(name, str):
        raise InvalidJobError("job.name is required (str)")
    if kind not in ("once", "cron", "dag"):
        raise InvalidJobError(f"job.kind must be once|cron|dag, got {kind!r}")
    payload = spec.get("payload") or {}
    out: Dict[str, Any] = {
        "name": name,
        "kind": kind,
        "payload": payload,
        "max_retries": int(spec.get("max_retries", DEFAULT_MAX_RETRIES)),
    }
    if kind == "once":
        if "run_at" not in spec:
            raise InvalidJobError("once jobs need 'run_at'")
        try:
            out["run_at"] = float(spec["run_at"])
        except (TypeError, ValueError):
            raise InvalidJobError("run_at must be a number")
    elif kind == "cron":
        try:
            out["interval_seconds"] = float(spec["interval_seconds"])
        except (TypeError, ValueError, KeyError):
            raise InvalidJobError("cron jobs need numeric interval_seconds")
        if out["interval_seconds"] <= 0:
            raise InvalidJobError("interval_seconds must be > 0")
        # Next run defaults to "now" unless overridden.
        try:
            out["next_run_at"] = float(spec.get("next_run_at", time.time()))
        except (TypeError, ValueError):
            raise InvalidJobError("next_run_at must be a number")
    elif kind == "dag":
        kids = spec.get("children")
        if not isinstance(kids, list) or not kids:
            raise InvalidJobError("dag jobs need a non-empty 'children' list")
        # Defer validation of children to insertion time.
        out["child_specs"] = kids
    return out


# ----------------------------- the service --------------------------------


class JobScheduler:
    """A small cron + DAG scheduler with a worker thread.

    >>> s = JobScheduler(start_worker=False)
    >>> job = s.create_job({"name": "tick", "kind": "cron", "interval_seconds": 60})
    >>> job["status"]
    'active'
    """

    def __init__(
        self,
        store: Optional[KeyValueStore] = None,
        idgen: Optional[Snowflake] = None,
        runner: Optional[JobRunner] = None,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        time_fn: Callable[[], float] = time.time,
        start_worker: bool = True,
    ):
        self.store = store or KeyValueStore("job_scheduler")
        self.idgen = idgen or Snowflake(machine_id=11)
        self.runner = runner or FunctionJobRunner(registry={})
        self.poll_interval = poll_interval
        self.time_fn = time_fn
        self.run_history_cap = DEFAULT_RUN_HISTORY_CAP

        # min-heap of (next_run_at, job_id)
        self._due: List[Tuple[float, int]] = []
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._worker: Optional[threading.Thread] = None
        self._lock = threading.RLock()

        # Recover: mark any 'running' runs as failed.
        self._recover_in_flight_runs()

        if start_worker:
            self.start_worker()

    # ---- lifecycle ------------------------------------------------------

    def start_worker(self) -> None:
        with self._lock:
            if self._worker and self._worker.is_alive():
                return
            self._stop.clear()
            # Seed the due heap with existing cron/once jobs.
            self._rebuild_due_heap()
            self._worker = threading.Thread(
                target=self._worker_loop,
                name="job-scheduler-worker",
                daemon=True,
            )
            self._worker.start()

    def stop_worker(self, timeout: float = 1.0) -> None:
        with self._lock:
            self._stop.set()
            self._wake.set()
        if self._worker:
            self._worker.join(timeout=timeout)

    def _worker_loop(self) -> None:
        while not self._stop.is_set():
            progressed = self.run_once()
            if not progressed:
                # Sleep until either something is due or shutdown.
                sleep_for = self._sleep_until_due()
                self._wake.wait(timeout=sleep_for)
                self._wake.clear()

    def _sleep_until_due(self) -> float:
        with self._lock:
            if not self._due:
                return self.poll_interval
            next_at = self._due[0][0]
            wait = max(0.0, next_at - self.time_fn())
            return min(wait, self.poll_interval) if wait <= 0 else wait

    def _recover_in_flight_runs(self) -> None:
        for _k, run in list(self.store.scan("run:")):
            if run.get("status") == "running":
                run["status"] = "failed"
                run["error"] = "recovered: process restarted mid-run"
                run["finished_at"] = self.time_fn()
                self.store.set(_k, run)

    def _rebuild_due_heap(self) -> None:
        self._due = []
        for _k, job in self.store.scan("job:"):
            if job.get("kind") in ("once", "cron"):
                nra = job.get("next_run_at")
                if nra is not None:
                    self._due.append((float(nra), int(job["job_id"])))
        heapq.heapify(self._due)

    # ---- job CRUD -------------------------------------------------------

    def create_job(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        norm = validate_job_spec(spec)
        now = self.time_fn()
        job = Job(
            job_id=self.idgen.next_id(),
            name=norm["name"],
            kind=norm["kind"],
            created_at=now,
            updated_at=now,
            payload=norm["payload"],
            max_retries=norm["max_retries"],
        )
        if norm["kind"] == "once":
            job.run_at = norm["run_at"]
            job.next_run_at = norm["run_at"]
        elif norm["kind"] == "cron":
            job.interval_seconds = norm["interval_seconds"]
            job.next_run_at = norm.get("next_run_at", now)
        elif norm["kind"] == "dag":
            # Persist children.
            kids = self._create_children(job, norm["child_specs"])
            job.children = kids

        self._persist_job(job)
        with self._lock:
            if job.next_run_at is not None and job.kind in ("once", "cron"):
                heapq.heappush(self._due, (job.next_run_at, job.job_id))
        self._wake.set()
        return job.to_dict()

    def _create_children(
        self, parent: Job, child_specs: List[Dict[str, Any]]
    ) -> List[int]:
        child_jobs: List[Job] = []
        now = self.time_fn()
        for cs in child_specs:
            if not isinstance(cs, dict):
                raise InvalidJobError("each child must be an object")
            if cs.get("kind") not in ("once", "cron"):
                raise InvalidJobError("child kind must be once|cron")
            if cs.get("kind") == "cron":
                if not isinstance(cs.get("interval_seconds"), (int, float)) or cs["interval_seconds"] <= 0:
                    raise InvalidJobError("cron child needs positive interval_seconds")
            kid = Job(
                job_id=self.idgen.next_id(),
                name=cs.get("name") or f"{parent.name}.{len(child_jobs)}",
                kind=cs["kind"],
                created_at=now,
                updated_at=now,
                payload=cs.get("payload") or {},
                max_retries=int(cs.get("max_retries", DEFAULT_MAX_RETRIES)),
            )
            if kid.kind == "once":
                kid.run_at = float(cs.get("run_at", now))
                kid.next_run_at = kid.run_at
            else:
                kid.interval_seconds = float(cs["interval_seconds"])
                kid.next_run_at = float(cs.get("next_run_at", now))
            child_jobs.append(kid)
        # Validate DAG has no cycles (topo_sort_children will raise).
        topo_sort_children(child_jobs)
        for k in child_jobs:
            self._persist_job(k)
            if k.next_run_at is not None and k.kind in ("once", "cron"):
                with self._lock:
                    heapq.heappush(self._due, (k.next_run_at, k.job_id))
        return [k.job_id for k in child_jobs]

    def _persist_job(self, job: Job) -> None:
        self.store.set(f"job:{job.job_id}", job.to_dict())
        idx = self.store.get("jobindex:all", [])
        if job.job_id not in idx:
            idx.append(job.job_id)
            self.store.set("jobindex:all", idx)

    def list_jobs(self) -> List[Dict[str, Any]]:
        return [
            self.store.get(f"job:{jid}")
            for jid in self.store.get("jobindex:all", [])
            if self.store.get(f"job:{jid}")
        ]

    def get_job(self, job_id: int) -> Dict[str, Any]:
        data = self.store.get(f"job:{job_id}")
        if not data:
            raise JobNotFoundError(str(job_id))
        return data

    def disable_job(self, job_id: int) -> Dict[str, Any]:
        data = self.get_job(job_id)
        data["status"] = "disabled"
        data["updated_at"] = self.time_fn()
        self.store.set(f"job:{job_id}", data)
        return data

    # ---- runs -----------------------------------------------------------

    def list_runs(self, job_id: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        if job_id is not None:
            ids = self.store.get(f"runindex:job:{job_id}", [])
        else:
            ids = list(self.store.keys_with_prefix("runindex:job:"))
            ids = []  # we'll scan below
        if job_id is None:
            # Scan all runs.
            out = [v for _k, v in self.store.scan("run:")]
        else:
            out = []
            for rid in ids:
                r = self.store.get(f"run:{rid}")
                if r:
                    out.append(r)
        out.sort(key=lambda r: r.get("started_at", 0), reverse=True)
        return out[: max(1, limit)]

    def get_run(self, run_id: int) -> Dict[str, Any]:
        data = self.store.get(f"run:{run_id}")
        if not data:
            raise JobNotFoundError(f"run {run_id} not found")
        return data

    def trigger_now(self, job_id: int) -> Dict[str, Any]:
        """Run a job synchronously and return the resulting Run."""
        job_data = self.get_job(job_id)
        # Build a transient Job dataclass for the runner.
        job = Job(
            job_id=job_data["job_id"],
            name=job_data["name"],
            kind=job_data["kind"],
            payload=job_data.get("payload", {}),
            max_retries=job_data.get("max_retries", DEFAULT_MAX_RETRIES),
        )
        run = self._execute(job, trigger="manual")
        return run.to_dict()

    # ---- worker tick ----------------------------------------------------

    def run_once(self) -> bool:
        """Pop the next due job, execute it, and reschedule cron jobs.

        Returns True if we did meaningful work, False otherwise. Tests
        drive this directly.
        """
        now = self.time_fn()
        with self._lock:
            while self._due and self._due[0][0] <= now:
                _at, job_id = heapq.heappop(self._due)
                job_data = self.store.get(f"job:{job_id}")
                if not job_data:
                    continue
                if job_data.get("status") != "active":
                    continue
                job = Job(
                    job_id=job_data["job_id"],
                    name=job_data["name"],
                    kind=job_data["kind"],
                    payload=job_data.get("payload", {}),
                    max_retries=job_data.get("max_retries", DEFAULT_MAX_RETRIES),
                )
                # Re-arm cron BEFORE running so we don't lose ticks if
                # the job takes a long time.
                if job.kind == "cron":
                    interval = float(job_data["interval_seconds"])
                    next_at = now + interval
                    job_data["next_run_at"] = next_at
                    self.store.set(f"job:{job.job_id}", job_data)
                    heapq.heappush(self._due, (next_at, job.job_id))
                break
            else:
                return False

        # Outside the lock.
        self._execute(job, trigger="scheduled")
        return True

    def _execute(self, job: Job, trigger: str) -> Run:
        run = Run(
            run_id=self.idgen.next_id(),
            job_id=job.job_id,
            started_at=self.time_fn(),
            trigger=trigger,
            attempt=1,
        )
        self._persist_run(run)

        if job.kind == "dag":
            ok, detail = self._run_dag(job)
            run.finished_at = self.time_fn()
            run.status = "success" if ok else "failed"
            run.result = detail if ok else None
            run.error = None if ok else str(detail)
        else:
            ok, detail = self.runner.run(job, job.payload)
            run.finished_at = self.time_fn()
            run.status = "success" if ok else "failed"
            run.result = detail if ok else None
            run.error = None if ok else str(detail)

        self._persist_run(run)

        # Update job-level counters / last_error.
        data = self.store.get(f"job:{job.job_id}") or {}
        data["run_count"] = int(data.get("run_count", 0)) + 1
        if run.status == "failed":
            data["last_error"] = run.error
        else:
            data["last_error"] = None
        data["updated_at"] = self.time_fn()
        self.store.set(f"job:{job.job_id}", data)

        return run

    def _run_dag(self, parent: Job) -> Tuple[bool, Any]:
        children = [
            Job(**self.store.get(f"job:{cid}"))
            for cid in parent.children
            if self.store.get(f"job:{cid}")
        ]
        # Topological order.
        order_ids = topo_sort_children(children)
        results: Dict[str, Any] = {}
        ok = True
        for cid in order_ids:
            cjob = next(c for c in children if c.job_id == cid)
            # Resolve depends_on and gate.
            deps = cjob.payload.get("depends_on") or []
            if any(d not in results or results.get(f"_status:{d}") != "success"
                   for d in deps if d in [c.name for c in children]):
                # Skip with status=failed.
                cjob_run = Run(
                    run_id=self.idgen.next_id(),
                    job_id=cjob.job_id,
                    started_at=self.time_fn(),
                    finished_at=self.time_fn(),
                    status="failed",
                    trigger="scheduled",
                    error="dependency failed",
                )
                self._persist_run(cjob_run)
                results[cjob.name] = None
                results[f"_status:{cjob.name}"] = "failed"
                ok = False
                continue
            crow = self.runner.run(cjob, cjob.payload)
            crow_status = "success" if crow[0] else "failed"
            crow_run = Run(
                run_id=self.idgen.next_id(),
                job_id=cjob.job_id,
                started_at=self.time_fn(),
                finished_at=self.time_fn(),
                status=crow_status,
                trigger="scheduled",
                result=crow[1] if crow[0] else None,
                error=None if crow[0] else str(crow[1]),
            )
            self._persist_run(crow_run)
            results[cjob.name] = crow[1] if crow[0] else None
            results[f"_status:{cjob.name}"] = crow_status
            if not crow[0]:
                ok = False
        return ok, results

    def _persist_run(self, run: Run) -> None:
        self.store.set(f"run:{run.run_id}", run.to_dict())
        idx_key = f"runindex:job:{run.job_id}"
        ids = self.store.get(idx_key, [])
        ids.append(run.run_id)
        # Cap per-job history.
        if len(ids) > self.run_history_cap:
            for old in ids[: -self.run_history_cap]:
                # Best-effort delete; the run may already be gone.
                self.store.delete(f"run:{old}")
            ids = ids[-self.run_history_cap:]
            self.store.set(idx_key, ids)
        if run.run_id not in (ids[-self.run_history_cap:]):
            self.store.set(idx_key, ids)

    # ---- helpers --------------------------------------------------------

    def cache_stats(self) -> dict:
        # Scheduler doesn't own a cache; we expose a no-op for parity.
        return {"size": 0, "hits": 0, "misses": 0, "evictions": 0}

    def status(self) -> dict:
        with self._lock:
            return {
                "due": len(self._due),
                "due_head": self._due[0] if self._due else None,
                "jobs": len(self.store.get("jobindex:all", [])),
                "runs": sum(1 for _ in self.store.scan("run:")),
            }