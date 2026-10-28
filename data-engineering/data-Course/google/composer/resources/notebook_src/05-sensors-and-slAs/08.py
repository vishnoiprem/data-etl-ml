from datetime import datetime, timedelta, timezone

from sla_logic import sla_deadline, sla_met

SLA = timedelta(hours=2)
LOGICAL_DATE = "2026-01-15"

deadline = sla_deadline(LOGICAL_DATE, SLA)
print(f"logical date      : {LOGICAL_DATE}")
print(f"data interval end : 2026-01-16 00:00:00 UTC")
print(f"SLA duration      : {SLA}")
print(f"deadline          : {deadline}")
print()

candidates = [
    ("on time, finished 01:30", datetime(2026, 1, 16, 1, 30, tzinfo=timezone.utc)),
    ("exactly at deadline", datetime(2026, 1, 16, 2, 0, 0, tzinfo=timezone.utc)),
    ("one minute late", datetime(2026, 1, 16, 2, 1, 0, tzinfo=timezone.utc)),
    ("three hours late", datetime(2026, 1, 16, 3, 0, 0, tzinfo=timezone.utc)),
]

for label, finished_at in candidates:
    met = sla_met(LOGICAL_DATE, SLA, finished_at)
    margin = deadline - finished_at
    print(f"  {label:<28} met={str(met):<5} margin={margin}")
