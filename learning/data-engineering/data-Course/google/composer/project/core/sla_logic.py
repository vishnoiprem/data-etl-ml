from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pipeline_logic import logical_date_window

def sla_deadline(logical_date: str, sla: timedelta) -> datetime:
    _, end = logical_date_window(logical_date)
    interval_end = datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return interval_end + sla

def sla_met(logical_date: str, sla: timedelta, finished_at: datetime) -> bool:
    if finished_at.tzinfo is None:
        finished_at = finished_at.replace(tzinfo=timezone.utc)
    return finished_at <= sla_deadline(logical_date, sla)
