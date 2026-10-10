# 03 — The 5 Python Screen Problems (Worked Solutions)

> **Author:** Prem Vishnoi &lt;prem.vishnoi@example.com&gt;
>
> **Companion:** [medium.com/@premvishnoi](https://medium.com/@premvishnoi)

The 5 Python screen problems below match the 2026 Meta DE
CoderPad format. **Not DSA.** Pandas / dict / string handling
on million-row data. The solutions in `code/meta_screen_python.py`
are vectorized. The first problem shows the wrong (iterative)
approach and the right (vectorized) approach side-by-side.

The full problem set in the 2026 Meta Python screen per
[Interview101 2026](https://www.interview101.com/interviews/meta/data-engineer):

1. Top 5 pages by statistically-significant upward 30-day
   impression trend
2. Second-highest salary per department
3. Read CSV, handle exception, summarize by category
4. Find users with 3+ calls in the last week from a stream
5. Compute 15-min tumbling-window counts from a ride-request stream

---

## Problem 1 — Top 5 pages by upward impression trend

> *"Given 30 days of page-level impression data, return the top
> 5 pages by statistically-significant upward trend. Use a
> simple trend test (e.g., 30-day slope > 0 with at least 5
> data points)."*

### Solution

```python
import pandas as pd
import numpy as np


def top_5_pages_by_upward_trend(impressions_df):
    """Return the top-5 page_ids by upward 30-day impression trend.

    The trend is the OLS slope of impressions vs. day. A page
    qualifies if the slope > 0 and there are >= 5 data points.

    Vectorized: groupby + apply, no Python loops over rows.

    Time:  O(n) over the DataFrame; the per-group slope is
           O(7) for a 7-day window, so total work is O(n).
    Space: O(p) for p pages.
    """
    # Group by page and day, sum impressions.
    daily = (impressions_df
             .groupby(['page_id', 'day'], as_index=False)['impressions']
             .sum())
    # Compute the slope per page. groupby + apply is the
    # idiomatic way; an explicit Python loop over page_ids
    # is the *rejected* approach.
    def slope(group):
        if len(group) < 5:
            return np.nan
        x = np.arange(len(group))
        y = group['impressions'].values
        # Vectorized OLS slope: cov(x,y) / var(x).
        return np.polyfit(x, y, 1)[0]
    slopes = (daily
              .groupby('page_id')
              .apply(slope)
              .rename('slope')
              .reset_index())
    qualified = slopes[slopes['slope'] > 0].sort_values(
        'slope', ascending=False).head(5)
    return qualified['page_id'].tolist()
```

### What the interviewer is testing

- **Vectorization.** A loop over rows is *rejected*. The
  right answer uses `groupby` + `apply` (or `transform`).
- **Edge cases.** A page with fewer than 5 data points
  should not appear. The `len(group) < 5` check is named
  explicitly.
- **Naming the slope choice.** "I used `np.polyfit` for
  the OLS slope" is more credible than "I computed the
  slope." The named-tool signal is the senior move.

---

## Problem 2 — Second-highest salary per department

> *"Given a list of employees (department, salary), return
> the second-highest salary per department. If a department
> has fewer than 2 employees, return None for that
> department."*

### Solution

```python
from collections import defaultdict


def second_highest_per_department(employees):
    """Return {department: second_highest_salary_or_None}."""
    by_dept = defaultdict(list)
    for name, dept, salary in employees:
        by_dept[dept].append(salary)
    out = {}
    for dept, salaries in by_dept.items():
        if len(salaries) < 2:
            out[dept] = None
            continue
        # Use a set to dedupe; the second element of a sorted
        # set is the second-highest *distinct* salary.
        distinct = sorted(set(salaries), reverse=True)
        out[dept] = distinct[1] if len(distinct) >= 2 else None
    return out
```

### What the interviewer is testing

- **Distinct vs. raw second.** "Second-highest salary" is
  ambiguous. The senior answer is "the second-highest
  *distinct* salary," and the code shows it (`sorted(set(...))`).
- **Edge case named.** Departments with 1 employee get
  `None`. Naming the edge case in narration is the
  senior move.
- **No pandas.** This problem tests *raw Python* —
  `defaultdict`, set, sorted. Some Meta DE Python screens
  don't allow pandas at all.

---

## Problem 3 — CSV read + exception handling

> *"Write a function that reads a CSV with columns (date,
> page_id, impressions), and returns a dict: {page_id:
> total_impressions}. Handle a missing file with a printed
> message and an empty dict. Handle a malformed row by
> skipping it and continuing."*

### Solution

```python
import csv


def summarize_by_page(path):
    """Return {page_id: total_impressions}, skipping malformed rows."""
    totals = {}
    try:
        with open(path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    page_id = row['page_id']
                    imp = int(row['impressions'])
                except (KeyError, ValueError):
                    # Malformed row: skip and continue.
                    continue
                totals[page_id] = totals.get(page_id, 0) + imp
    except FileNotFoundError:
        print(f"file not found: {path}")
        return {}
    return totals
```

### What the interviewer is testing

- **`with` for the file handle.** Closes the file even
  on exception.
- **Per-row try/except.** A single bad row should not
  kill the whole summary.
- **The print-and-return-empty pattern.** The question
  said "print a message." The senior answer prints *and*
  returns `{}` so the caller can branch on the empty
  result.

---

## Problem 4 — Users with 3+ calls in the last week (stream)

> *"Given a stream of call events (timestamp, caller_id,
> receiver_id), return the set of users who have made 3 or
> more calls in the last 7 days, where 'made a call' means
> either caller or receiver."*

### Solution

```python
from collections import defaultdict, deque


def users_with_3plus_calls(events, now, window_seconds=7 * 86400):
    """Return set of users with >= 3 calls in the last window.

    A 'user' is any caller_id or receiver_id in any event.
    """
    recent = defaultdict(deque)
    for ts, caller, receiver in events:
        for u in (caller, receiver):
            q = recent[u]
            q.append(ts)
            while q and q[0] < ts - window_seconds:
                q.popleft()
    return {u for u, q in recent.items() if len(q) >= 3}
```

### What the interviewer is testing

- **Streaming, not batch.** The input is a *stream*. A
  naive `events[-1000:]` is wrong. The right answer
  keeps a sliding window per user.
- **Both caller and receiver count.** A user is "active"
  if they appear as either side of a call.
- **`deque` for the sliding window.** `list.pop(0)` is
  O(n). `deque.popleft()` is O(1).

---

## Problem 5 — 15-min tumbling window

> *"Given a stream of ride requests (timestamp, rider_id),
> compute the count of ride requests in each 15-minute
> tumbling window. Return a list of (window_start,
> count) sorted by window_start."*

### Solution

```python
from collections import Counter


def tumbling_window_counts(events, window_seconds=15 * 60):
    """Return [(window_start, count), ...] sorted by window_start.

    Tumbling = non-overlapping, fixed-size windows. Each event
    falls into exactly one window.
    """
    counts = Counter()
    for ts, _rider in events:
        bucket = (ts // window_seconds) * window_seconds
        counts[bucket] += 1
    return sorted(counts.items())
```

### What the interviewer is testing

- **Tumbling vs. sliding.** Tumbling = non-overlapping.
  Sliding = overlapping. The interview answer names
  which one and why.
- **Integer arithmetic for the bucket.** `ts // window * window`
  is the idiomatic way. A `pd.DataFrame.resample` is also
  fine but slower at the per-event level.
- **Late-arriving events.** The Meta onsite version of
  this question adds late events. The right answer is to
  *count* the event in the *bucket of the event_ts*, not
  the bucket of arrival time. Naming this in narration is
  the senior move.

---

*Author: Prem Vishnoi &lt;prem.vishnoi@example.com&gt;*
