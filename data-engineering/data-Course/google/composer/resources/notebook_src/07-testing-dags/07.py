"""A minimal Airflow stand-in, enough to assert on DAG structure.

Mirrors the shape of airflow.models.DAG / airflow.models.BaseOperator for
the attributes a structure test cares about.
"""
from __future__ import annotations


class BaseOperator:
    """A stand-in for an Airflow operator."""

    def __init__(self, task_id, *, upstream_task_ids=None, trigger_rule="all_success",
                 retries=0, timeout=None, **kwargs):
        self.task_id = task_id
        self.upstream_task_ids = set(upstream_task_ids or ())
        self.trigger_rule = trigger_rule
        self.retries = retries
        self.timeout = timeout
        self.kwargs = kwargs

    def __repr__(self):
        return f"<Task {self.task_id}>"


class DAG:
    """A stand-in for an Airflow DAG."""

    def __init__(self, dag_id, tasks, *, schedule=None, start_date=None,
                 catchup=False, max_active_runs=1, default_args=None, **kwargs):
        self.dag_id = dag_id
        self.schedule = schedule
        self.start_date = start_date
        self.catchup = catchup
        self.max_active_runs = max_active_runs
        self.default_args = default_args or {}
        self._tasks = {task.task_id: task for task in tasks}

    def get_task(self, task_id):
        """Return a task by id.

        Args:
            task_id: The task's identifier.

        Returns:
            The task.

        Raises:
            KeyError: When no such task exists.
        """
        return self._tasks[task_id]

    @property
    def tasks(self):
        """Return all tasks."""
        return list(self._tasks.values())

    @property
    def task_ids(self):
        """Return all task ids."""
        return list(self._tasks)
