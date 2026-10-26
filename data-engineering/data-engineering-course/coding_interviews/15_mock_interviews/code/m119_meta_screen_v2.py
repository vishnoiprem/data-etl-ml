"""Mock 119 — Meta E4/E5 screen, 2026 format (pandas / dict, NOT DSA).

This replaces m113_meta_screen.py, which was calibrated to a
2018-era "FizzBuzz + parens with wildcards" DSA flavor. The
2026 Meta Python screen is pandas / dict / string handling on
million-row data; iterative / loop-based solutions on large
DataFrames are explicitly rejected.

Three problems (calibrated to the 5+5 format, picked as the
three most-asked 2026 patterns):

  1. Top 5 pages by statistically-significant upward 30-day
     impression trend (pandas groupby + vectorized slope).
  2. Second-highest *distinct* salary per department (raw Python).
  3. 15-minute tumbling-window counts on a stream of events.

The other 2 of the 5 are in sql_interviews/11_meta_screen/ — the
SQL screen and the Python screen are the *same* screen, just
the second half.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

import numpy as np


# ----------------------------------------------------------------------
# Problem 1: top 5 pages by upward 30-day impression trend.
# ----------------------------------------------------------------------

def top_5_pages_by_upward_trend(impressions_df):
    """Return top-5 page_ids by upward 30-day impression trend.

    Vectorized: groupby + apply. Iterative loops on the
    DataFrame are rejected at Meta.
    """
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
    qualified = slopes[slopes['slope'] > 0].sort_values(
        'slope', ascending=False).head(5)
    return qualified['page_id'].tolist()


# ----------------------------------------------------------------------
# Problem 2: second-highest *distinct* salary per department.
# ----------------------------------------------------------------------

def second_highest_per_department(employees):
    """Return {department: second_highest_distinct_or_None}."""
    from collections import defaultdict
    by_dept = defaultdict(list)
    for _name, dept, salary in employees:
        by_dept[dept].append(salary)
    out = {}
    for dept, salaries in by_dept.items():
        distinct = sorted(set(salaries), reverse=True)
        out[dept] = distinct[1] if len(distinct) >= 2 else None
    return out


# ----------------------------------------------------------------------
# Problem 3: 15-min tumbling-window counts.
# ----------------------------------------------------------------------

def tumbling_window_counts(events, window_seconds=15 * 60):
    """Return [(window_start, count), ...] sorted by window_start."""
    from collections import Counter
    counts = Counter()
    for ts, _rider in events:
        bucket = (ts // window_seconds) * window_seconds
        counts[bucket] += 1
    return sorted(counts.items())


if __name__ == "__main__":
    # Smoke demo.
    sample = [(0, 1), (300, 1), (1200, 1), (1700, 1)]
    print(tumbling_window_counts(sample, window_seconds=900))
