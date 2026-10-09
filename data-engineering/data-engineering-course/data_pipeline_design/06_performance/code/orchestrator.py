"""Tiny DAG orchestrator.

A 100-line implementation of the Airflow / Dagster / Prefect
DAG pattern. Tasks are registered with ``add_task(name, fn,
depends_on=[...])``; ``run()`` topologically sorts and
executes them.

The orchestrator tracks per-task state (pending / running /
done / failed). If a task raises, the DAG run is marked
failed and the exception is re-raised so the caller can
decide whether to retry.

The implementation is intentionally simple — no parallel
execution, no retries, no SLA tracking. Those are added
in production orchestrators and in the rest of this module.

Author: Prem Vishnoi <prem.vishnoi.example.com>
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


class Dag:
    """A tiny DAG runner.

    Usage::

        dag = Dag("daily_orders")
        dag.add_task("extract", extract_fn)
        dag.add_task("transform", transform_fn, depends_on=["extract"])
        dag.add_task("load", load_fn, depends_on=["transform"])
        results = dag.run()
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._tasks: Dict[str, Callable] = {}
        self._deps: Dict[str, List[str]] = defaultdict(list)
        self._state: Dict[str, TaskState] = {}
        self._results: Dict[str, Any] = {}
        self._durations: Dict[str, float] = {}
        self._execution_order: List[str] = []

    # ---- public API ---------------------------------------------------

    def add_task(
        self, name: str, fn: Callable, depends_on: Optional[List[str]] = None
    ) -> None:
        if name in self._tasks:
            raise ValueError(f"task {name!r} already exists")
        for dep in depends_on or []:
            if dep not in self._tasks:
                raise ValueError(
                    f"task {name!r} depends on unknown task {dep!r}"
                )
        self._tasks[name] = fn
        self._deps[name] = list(depends_on or [])
        self._state[name] = TaskState.PENDING

    @property
    def execution_order(self) -> List[str]:
        return list(self._execution_order)

    @property
    def state(self) -> Dict[str, TaskState]:
        return dict(self._state)

    def results(self) -> Dict[str, Any]:
        return dict(self._results)

    # ---- core --------------------------------------------------------

    def _topological_order(self) -> List[str]:
        """Return tasks in topological order.

        Uses Kahn's algorithm. Raises ``ValueError`` on a cycle.
        """
        in_degree: Dict[str, int] = {name: 0 for name in self._tasks}
        for name, deps in self._deps.items():
            in_degree[name] = len(deps)
        # Build reverse adjacency for the traversal.
        dependents: Dict[str, List[str]] = defaultdict(list)
        for name, deps in self._deps.items():
            for dep in deps:
                dependents[dep].append(name)
        # Start with tasks that have no dependencies.
        queue: deque = deque(
            name for name, deg in in_degree.items() if deg == 0
        )
        order: List[str] = []
        while queue:
            n = queue.popleft()
            order.append(n)
            for m in dependents[n]:
                in_degree[m] -= 1
                if in_degree[m] == 0:
                    queue.append(m)
        if len(order) != len(self._tasks):
            raise ValueError(f"cycle detected in DAG {self.name!r}")
        return order

    def run(self) -> Dict[str, Any]:
        """Execute the DAG in topological order. Return per-task results."""
        order = self._topological_order()
        failed = False
        first_exc: Optional[BaseException] = None
        for name in order:
            # Verify all deps are done (in case of partial prior state).
            if failed or any(
                self._state[dep] != TaskState.DONE for dep in self._deps[name]
            ):
                self._state[name] = TaskState.SKIPPED
                self._execution_order.append(name)
                continue
            self._state[name] = TaskState.RUNNING
            start = time.time()
            try:
                self._results[name] = self._tasks[name]()
            except Exception as exc:  # noqa: BLE001
                self._state[name] = TaskState.FAILED
                self._durations[name] = time.time() - start
                self._execution_order.append(name)
                if first_exc is None:
                    first_exc = exc
                failed = True
                continue
            self._durations[name] = time.time() - start
            self._state[name] = TaskState.DONE
            self._execution_order.append(name)
        if first_exc is not None:
            raise first_exc
        return self._results
