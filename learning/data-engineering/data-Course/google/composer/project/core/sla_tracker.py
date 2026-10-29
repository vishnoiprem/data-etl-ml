"""Track SLA outcomes across runs, so compliance can be computed later."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sla_logic import sla_deadline, sla_met


class SlaTracker:
    """Record SLA outcomes for a DAG and compute a compliance rate.

    This is the shape of the thing you build *outside* Airflow: Airflow
    gives you the events, and you aggregate them over a period to check
    the contractual number.

    Attributes:
        sla: The SLA duration being tracked.
        outcomes: A mapping of logical_date -> True/False.
    """

    def __init__(self, sla: timedelta) -> None:
        """Create a tracker.

        Args:
            sla: The SLA duration.
        """
        self.sla = sla
        self.outcomes: dict[str, bool] = {}

    def record(self, logical_date: str, finished_at: datetime) -> bool:
        """Record one run's outcome.

        Args:
            logical_date: The run's logical date.
            finished_at: When the run finished.

        Returns:
            True when the SLA was met.
        """
        met = sla_met(logical_date, self.sla, finished_at)
        self.outcomes[logical_date] = met
        return met

    def compliance(self) -> float:
        """Return the fraction of runs that met their SLA.

        Returns:
            A number between 0.0 and 1.0, or 1.0 when nothing is recorded.
        """
        if not self.outcomes:
            return 1.0
        met = sum(1 for ok in self.outcomes.values() if ok)
        return met / len(self.outcomes)

    def report(self) -> str:
        """Return a human-readable compliance report.

        Returns:
            A multi-line report.
        """
        lines = [
            f"SLA: {self.sla} (deadline = interval end + SLA)",
            f"runs recorded : {len(self.outcomes)}",
            f"on time       : {sum(1 for ok in self.outcomes.values() if ok)}",
            f"missed        : {sum(1 for ok in self.outcomes.values() if not ok)}",
            f"compliance    : {self.compliance():.4%}",
        ]
        return "\n".join(lines)
