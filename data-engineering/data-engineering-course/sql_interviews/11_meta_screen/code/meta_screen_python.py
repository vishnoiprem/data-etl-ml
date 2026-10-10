"""The 5 Python screen problems for the 2026 Meta DE CoderPad.

The 2026 format: pandas / dict / string handling. NOT DSA.

Tests: tests/test_meta_screen_python.py
"""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from typing import Dict, Iterable, List, Optional, Set, Tuple

import numpy as np


# ----------------------------------------------------------------------
# Problem 1: top-5 pages by upward 30-day impression trend.
# ----------------------------------------------------------------------

def top_5_pages_by_upward_trend(impressions_df) -> List[int]:
    """Return the top-5 page_ids by upward 30-day impression trend.

    Parameters
    ----------
    impressions_df : pandas.DataFrame
        Columns: page_id (int), day (int, 0-29), impressions (int).

    Returns
    -------
    list of int
        The 5 page_ids with the largest positive slope, ties broken
        by page_id ascending. Pages with fewer than 5 days of data
        are excluded.
    """
    # Daily sum (in case of multiple rows per page per day).
    daily = (impressions_df
             .groupby(['page_id', 'day'], as_index=False)['impressions']
             .sum())
    def slope(group, **kwargs):
        if len(group) < 5:
            return np.nan
        x = np.arange(len(group))
        y = group['impressions'].values
        return float(np.polyfit(x, y, 1)[0])
    slopes = (daily
              .groupby('page_id')
              .apply(slope, include_groups=False)
              .rename('slope')
              .reset_index())
    qualified = slopes[slopes['slope'] > 0]
    qualified = qualified.sort_values(
        ['slope', 'page_id'], ascending=[False, True])
    return qualified.head(5)['page_id'].tolist()


# ----------------------------------------------------------------------
# Problem 2: second-highest *distinct* salary per department.
# ----------------------------------------------------------------------

def second_highest_per_department(employees: Iterable[Tuple[str, str, int]]
                                  ) -> Dict[str, Optional[int]]:
    """Return {department: second_highest_distinct_salary_or_None}.

    Parameters
    ----------
    employees : iterable of (name, department, salary)
    """
    by_dept: Dict[str, List[int]] = defaultdict(list)
    for _name, dept, salary in employees:
        by_dept[dept].append(salary)
    out: Dict[str, Optional[int]] = {}
    for dept, salaries in by_dept.items():
        distinct = sorted(set(salaries), reverse=True)
        out[dept] = distinct[1] if len(distinct) >= 2 else None
    return out


# ----------------------------------------------------------------------
# Problem 3: read CSV, handle missing file + malformed rows.
# ----------------------------------------------------------------------

def summarize_by_page(path: str) -> Dict[str, int]:
    """Read a CSV (date, page_id, impressions), return {page_id: total}.

    Missing file: print a message and return {}.
    Malformed row: skip and continue.
    """
    import csv
    totals: Dict[str, int] = {}
    try:
        with open(path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    page_id = row['page_id']
                    imp = int(row['impressions'])
                except (KeyError, ValueError):
                    continue
                totals[page_id] = totals.get(page_id, 0) + imp
    except FileNotFoundError:
        print(f"file not found: {path}")
        return {}
    return totals


# ----------------------------------------------------------------------
# Problem 4: users with 3+ calls in the last week (stream).
# ----------------------------------------------------------------------

def users_with_3plus_calls(events: Iterable[Tuple[int, int, int]],
                           now: int,
                           window_seconds: int = 7 * 86400) -> Set[int]:
    """Return users with >= 3 calls in the last ``window_seconds``.

    A 'user' is any caller_id or receiver_id in any event.
    The events are processed in stream order; the result is computed
    using a per-user sliding-window deque.
    """
    recent: Dict[int, deque] = defaultdict(deque)
    for ts, caller, receiver in events:
        for u in (caller, receiver):
            q = recent[u]
            q.append(ts)
            while q and q[0] < ts - window_seconds:
                q.popleft()
    return {u for u, q in recent.items() if len(q) >= 3}


# ----------------------------------------------------------------------
# Problem 5: 15-min tumbling-window counts.
# ----------------------------------------------------------------------

def tumbling_window_counts(events: Iterable[Tuple[int, int]],
                           window_seconds: int = 15 * 60
                           ) -> List[Tuple[int, int]]:
    """Return [(window_start, count), ...] sorted by window_start.

    Tumbling = non-overlapping, fixed-size windows. Each event
    falls into exactly one window.
    """
    counts: Counter = Counter()
    for ts, _rider in events:
        bucket = (ts // window_seconds) * window_seconds
        counts[bucket] += 1
    return sorted(counts.items())


if __name__ == "__main__":
    # Smoke demo: 15-min tumbling window on 4 ride events.
    sample = [(0, 1), (300, 1), (1200, 1), (1700, 1)]
    print(tumbling_window_counts(sample, window_seconds=900))
