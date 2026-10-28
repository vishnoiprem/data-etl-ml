from pathlib import Path
import sys

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent.parent
sys.path.insert(0, str(COURSE_ROOT / "project" / "core"))
sys.path.insert(0, str(COURSE_ROOT / "project"))

print("COURSE_ROOT =", COURSE_ROOT)
print("project/ present:", (COURSE_ROOT / "project").exists())
print("core/ present:", (COURSE_ROOT / "project" / "core").exists())

import local_runner
print("local_runner loaded from:", local_runner.__file__)

from pipeline_logic import (
    transform_orders,
    summarise_by_region,
    render_summary_csv,
    render_rejects_csv,
    reject_counts,
    logical_date_window,
    partition_for_date,
)

import datetime as dt


def parse_schedule(schedule: str) -> dt.timedelta:
    """Convert a schedule string into an interval length."""
    presets = {
        "@hourly": dt.timedelta(hours=1),
        "@daily": dt.timedelta(days=1),
        "@weekly": dt.timedelta(days=7),
        "@monthly": dt.timedelta(days=30),
    }
    if schedule in presets:
        return presets[schedule]
    if schedule.startswith("@"):
        raise ValueError(f"unsupported preset: {schedule}")
    # Treat a 5-field cron as daily for the purposes of this simulator.
    parts = schedule.split()
    if len(parts) == 5:
        if parts[0] == "*" and parts[1] == "*" and parts[2] == "*" and parts[3] == "*":
            return dt.timedelta(days=1)
        raise ValueError(f"unsupported cron: {schedule} (hourly crons not modelled)")
    raise ValueError(f"unsupported schedule: {schedule}")


def simulate_schedule(
    start_date: str,
    schedule: str,
    now: str,
    catchup: bool,
) -> list[str]:
    """Simulate which logical dates the Airflow scheduler would create."""
    interval = parse_schedule(schedule)
    start = dt.datetime.strptime(start_date, "%Y-%m-%d")
    now_dt = dt.datetime.strptime(now, "%Y-%m-%d %H:%M")

    logical_dates: list[str] = []
    current = start
    while current < now_dt:
        logical_dates.append(current.date().isoformat())
        current += interval

    if not catchup:
        # Without catchup, only the most recent interval is created.
        logical_dates = logical_dates[-1:] if logical_dates else []

    return logical_dates


print("Simulator built.\n")
print("--- catchup=False, DAG deployed late ---")
print(simulate_schedule("2026-01-01", "@daily", "2026-03-01 12:00", catchup=False))
print()
print("--- catchup=True, same situation ---")
print(simulate_schedule("2026-01-01", "@daily", "2026-03-01 12:00", catchup=True))
