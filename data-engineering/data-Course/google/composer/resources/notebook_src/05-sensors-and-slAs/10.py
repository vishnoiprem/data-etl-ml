from datetime import datetime, timedelta, timezone

from sla_logic import sla_deadline, sla_met

SLA = timedelta(hours=2)
LOGICAL_DATE = "2026-01-15"
INTERVAL_END = datetime(2026, 1, 16, 0, 0, tzinfo=timezone.utc)

# A run for the 2026-01-15 interval that executes just after midnight.
finished_at = datetime(2026, 1, 16, 0, 30, tzinfo=timezone.utc)

interval_rule = sla_met(LOGICAL_DATE, SLA, finished_at)

# The wrong rule: "the deadline is two hours after the task started".
wrong_deadline = finished_at + SLA
wall_clock_rule = finished_at <= wrong_deadline

print(f"interval-end deadline : {sla_deadline(LOGICAL_DATE, SLA)}")
print(f"wall-clock deadline   : {wrong_deadline}  (measured from finish)")
print()
print(f"interval-end rule says on time : {interval_rule}")
print(f"wall-clock rule says on time   : {wall_clock_rule}")
print()
print("Same run, two rules, two answers - which is exactly why the")
print("SLA must be anchored to the data interval, not to the clock.")
