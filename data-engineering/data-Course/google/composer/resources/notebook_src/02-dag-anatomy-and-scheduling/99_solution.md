```python
# Exercise 1
def parse_schedule(schedule):
    presets = {
        "@hourly": dt.timedelta(hours=1),
        "@daily": dt.timedelta(days=1),
        "@weekly": dt.timedelta(days=7),
    }
    if schedule in presets:
        return presets[schedule]
    parts = schedule.split()
    if len(parts) == 5:
        if parts[2] == "*" and parts[3] == "*" and parts[4] == "*":
            return dt.timedelta(hours=1) if parts[1] == "*" else None
        return dt.timedelta(days=1)
    raise ValueError(schedule)
```

```python
# Exercise 2
dates = simulate_schedule("2026-01-01", "@daily", "2026-01-08 12:00", catchup=True)
print(dates)   # ['2026-01-01' ... '2026-01-07'] - 7 runs
```

With `WRITE_TRUNCATE`, each run replaces the whole table with that single
day's data, so the table ends up containing only the last run's rows
(2026-01-07) — the other six days are destroyed. With `WRITE_APPEND`, each
run adds its day without removing anything, so the table ends up containing
the union of all seven days — which happens to be correct *here*, but only
because no day overlaps. The dangerous combination is `WRITE_APPEND` with a
schedule that overlaps (e.g. a 6-hourly schedule appending to a daily
partition), which quadruples every row.

```python
# Exercise 3
from pipeline_logic import partition_for_date

def partitions_for_backfill(start, end):
    partitions = []
    current = dt.date.fromisoformat(start)
    last = dt.date.fromisoformat(end)
    while current < last:                 # half-open: end is exclusive
        partitions.append(partition_for_date(current.isoformat()))
        current += dt.timedelta(days=1)
    return partitions

print(partitions_for_backfill("2026-01-13", "2026-01-16"))
# ['20260113', '20260114', '20260115']
```

The end is exclusive because the window convention is uniform: every window
in the system is `[start, end)`. Using an inclusive end here would make the
backfill overlap the next scheduled run, and the last partition would be
written twice.
