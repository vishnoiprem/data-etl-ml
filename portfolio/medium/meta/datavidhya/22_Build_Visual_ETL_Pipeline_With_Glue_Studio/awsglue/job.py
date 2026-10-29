"""``Job`` -- Glue's ``awsglue.job.Job`` shim.

Production ``Job`` records the run in the Glue Data Catalog's job-bookmark
table and surfaces metrics to CloudWatch. Offline we treat ``init`` /
``commit`` as no-ops -- they exist purely so the generated script's
``job.init(...)`` / ``job.commit()`` lines don't blow up.
"""
from __future__ import annotations

from typing import Any


class Job:
    def __init__(self, glue_context: Any) -> None:
        self._ctx = glue_context
        self._initialised = False

    def init(self, name: str, args: Any = None) -> None:
        self._initialised = True

    def commit(self) -> None:
        if not self._initialised:
            raise RuntimeError("Job.commit() called before Job.init()")