"""Step-level checkpoints - the difference between retry and resume.

* **Retry** re-runs the step that just failed. Correct for transient errors
  (timeout, 503) and only safe when the step is idempotent.
* **Resume** re-runs nothing that already succeeded. It replays completed steps
  from their checkpoint and continues from the first unfinished one, so
  completed side effects never happen twice.

This implementation is a dict. That is the point: the interface is what matters,
so swapping in Redis or Postgres is a one-class change. In-memory means
checkpoints die with the process and are not shared between workers - fine for a
demo, wrong for production.
"""

from typing import Any


class CheckpointStore:
    def __init__(self) -> None:
        self._runs: dict[str, dict[str, Any]] = {}

    def get(self, run_id: str, step: str) -> tuple[bool, Any]:
        """Return ``(found, value)``. A flag rather than ``None``, because a step
        is allowed to legitimately produce ``None`` or an empty list."""
        run = self._runs.get(run_id, {})
        if step in run:
            return True, run[step]
        return False, None

    def put(self, run_id: str, step: str, value: Any) -> None:
        self._runs.setdefault(run_id, {})[step] = value

    def completed_steps(self, run_id: str) -> list[str]:
        return list(self._runs.get(run_id, {}))

    def clear(self, run_id: str) -> None:
        self._runs.pop(run_id, None)
