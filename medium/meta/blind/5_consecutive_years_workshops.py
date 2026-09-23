"""
Problem 5 (Medium) — Largest sum of classes across consecutive years

Given a list of workshops (year, num_classes), return the largest total
number of classes hosted in any CONSECUTIVE run of years that had at
least one workshop each.

"2 consecutive years that had at least one workshop each" — so we need
a run like 2020, 2021 (gap=1) or 2020, 2021, 2022 (gaps=1,1).

Examples
--------
>>> workshops = [
...     (2018, 10),
...     (2019, 5),
...     (2020, 12),
...     (2022, 7),
...     (2023, 3),
... ]
>>> max_classes_consecutive_years(workshops)
27
>>> max_classes_consecutive_years([(2020, 1), (2022, 1)])
1
>>> max_classes_consecutive_years([])
0

How to think (interview script)
------------------------------
"Two interpretations:
  A) 'Consecutive years' = adjacent integers with no gap.
  B) 'Consecutive in the input list'.

The Blind post phrasing suggests (A). With (B), the answer is trivial
because all inputs are consecutive in the list.

Algorithm:
  1) Aggregate classes by year (dict: year -> total).
  2) Sort by year.
  3) Walk the sorted years; whenever the gap between consecutive years
     is > 1, close the current run and start a new one.
  4) Track max run sum."

Complexity: O(n log n) time, O(n) extra space.

Follow-ups
----------
- "What if multiple workshops occur in the same year?"
  My aggregation handles that. Mention this is why I aggregate first.
- "What if 'consecutive' means 'at least one per year for N years'?"
  Same algorithm; we'd return the count of years in the run, not the sum.
- "What about an unsorted input?"
  Sort first; the dict-aggregation step implicitly sorts.
"""

from typing import List, Tuple


# ----------------------------------------------------------------------
# L0 — Easy / brute force: nested loops over the input.
# How to think: "For each starting workshop, sum classes until the
# next year's gap exceeds 1. O(n²). Correct but slow."
# ----------------------------------------------------------------------
def max_classes_consecutive_years_l0(workshops: List[Tuple[int, int]]) -> int:
    if not workshops:
        return 0
    best = 0
    # Aggregate first so duplicate years collapse (matches L1's semantics)
    by_year: dict[int, int] = {}
    for y, n in workshops:
        by_year[y] = by_year.get(y, 0) + n
    years = sorted(by_year)
    for i in range(len(years)):
        run = 0
        prev_year = None
        for y in years[i:]:
            if prev_year is not None and y - prev_year > 1:
                break
            run += by_year[y]
            prev_year = y
        if run > best:
            best = run
    return best


# ----------------------------------------------------------------------
# L1 — Medium / interview-canonical: aggregate + single pass.
# How to think: "Aggregate first (handles duplicate years), sort, walk.
# O(n log n)."
# ----------------------------------------------------------------------
def max_classes_consecutive_years(workshops: List[Tuple[int, int]]) -> int:
    """Largest total classes across any run of consecutive years with >= 1 workshop each."""
    if not workshops:
        return 0
    by_year: dict[int, int] = {}
    for year, n in workshops:
        by_year[year] = by_year.get(year, 0) + n
    years_sorted = sorted(by_year)
    best = 0
    run_sum = 0
    prev_year = None
    for y in years_sorted:
        if prev_year is None or y - prev_year > 1:
            run_sum = by_year[y]
        else:
            run_sum += by_year[y]
        if run_sum > best:
            best = run_sum
        prev_year = y
    return best


# ----------------------------------------------------------------------
# L2 — Hard / production-grade: difference array on a bounded year-axis.
# How to think: "When year values are bounded (say 1900..2100), a
# difference array gives O(Y) sweep with no comparisons inside the
# loop. Reset `run` when a year has zero workshops."
# ----------------------------------------------------------------------
def max_classes_consecutive_years_l2(workshops: List[Tuple[int, int]]) -> int:
    if not workshops:
        return 0
    lo = min(y for y, _ in workshops)
    hi = max(y for y, _ in workshops)
    arr = [0] * (hi - lo + 1)
    for y, n in workshops:
        arr[y - lo] += n
    best = run = 0
    for v in arr:
        run = v if v else 0
        if run > best:
            best = run
    return best


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
    samples = [
        ([(2018, 10), (2019, 5), (2020, 12), (2022, 7), (2023, 3)], 27),
        ([(2020, 1), (2022, 1)], 1),
        ([], 0),
        ([(2020, 5)], 5),
        ([(2020, 1), (2022, 1), (2024, 1)], 1),
        ([(2020, 1), (2021, 2), (2022, 3)], 6),
        ([(2020, 1), (2020, 1), (2021, 5)], 7),
    ]
    for ws, expected in samples:
        assert max_classes_consecutive_years_l0(ws) == expected, ws
        assert max_classes_consecutive_years(ws) == expected, ws
        assert max_classes_consecutive_years_l2(ws) == expected, ws
    print("All tests passed for max_classes_consecutive_years (L0 + L1 + L2).")
