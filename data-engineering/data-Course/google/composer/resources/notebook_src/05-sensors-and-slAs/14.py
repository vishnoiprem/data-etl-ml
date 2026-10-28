from datetime import datetime, timedelta, timezone

from sla_tracker import SlaTracker

SLA = timedelta(hours=2)

tracker = SlaTracker(SLA)

# A week of runs. The first four finish on time, the last two do not.
finished_times = [
    datetime(2026, 1, 15, 23, 40, tzinfo=timezone.utc),   # on time
    datetime(2026, 1, 16, 23, 50, tzinfo=timezone.utc),   # on time
    datetime(2026, 1, 17, 23, 30, tzinfo=timezone.utc),   # on time
    datetime(2026, 1, 18, 23, 45, tzinfo=timezone.utc),   # on time
    datetime(2026, 1, 19, 23, 55, tzinfo=timezone.utc),   # on time
    datetime(2026, 1, 20, 5, 10, tzinfo=timezone.utc),    # LATE
    datetime(2026, 1, 21, 4, 0, tzinfo=timezone.utc),     # LATE
]

logical_dates = [
    "2026-01-15", "2026-01-16", "2026-01-17", "2026-01-18",
    "2026-01-19", "2026-01-20", "2026-01-21",
]

for logical_date, finished_at in zip(logical_dates, finished_times):
    met = tracker.record(logical_date, finished_at)
    print(f"{logical_date}  finished={finished_at.strftime('%H:%M')}  met={met}")

print()
print(tracker.report())
print()
print(f"Compliance target 99% met: {tracker.compliance() >= 0.99}")
