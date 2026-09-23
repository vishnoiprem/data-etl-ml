"""
Remove Covered Intervals - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/remove-covered-intervals

Given a list of intervals, return the count of intervals that are NOT
covered by another interval. An interval [a, b] is covered by [c, d] if
c <= a and b <= d.

KEY INSIGHT:
Sort by start ascending, end descending. Then walk: if current interval's
end <= max_end_so_far, it's covered; otherwise update max_end.

Examples:
    [[1,4],[3,6],[2,8]] -> 2 (3,6 covered by 1,4? no; 2,8 covers both)
    [[1,4],[2,3]] -> 1 (2,3 covered by 1,4)
    [[0,10],[5,12]] -> 2 (neither covers the other)

Constraints:
- 1 <= intervals.length <= 1000
- 0 <= starti <= endi <= 10^5
"""

import copy
import sys

sys.setrecursionlimit(100000)


def _eq(a, b):
    return a == b


# ============================================================
# Way 1: Sort + walk + max_end (BEST - Memorize!)
# ============================================================
def remove_covered_intervals_1(intervals):
    """Sort by start asc, end desc. Track max_end."""
    if not intervals:
        return 0
    intervals = sorted(intervals, key=lambda x: (x[0], -x[1]))
    max_end = intervals[0][1]
    count = 1  # First interval is always kept.
    for i in range(1, len(intervals)):
        s, e = intervals[i]
        if e > max_end:
            count += 1
            max_end = e
        # Else: covered (e <= max_end and start is <= max_end's start
        # because of the sort, so the interval is covered).
    return count


# ============================================================
# Way 2: Sort + walk, count always (different way)
# ============================================================
def remove_covered_intervals_2(intervals):
    """Sort by start asc, end desc. Walk; if covered by earlier, skip."""
    if not intervals:
        return 0
    intervals = sorted(intervals, key=lambda x: (x[0], -x[1]))
    count = 0
    for i in range(len(intervals)):
        s, e = intervals[i]
        covered = False
        for k in range(i):
            if intervals[k][0] <= s and intervals[k][1] >= e:
                covered = True
                break
        if not covered:
            count += 1
    return count


# ============================================================
# Way 3: Sort + O(n) walk using monotonic max_end
# ============================================================
def remove_covered_intervals_3(intervals):
    """Sort by start asc; walk; max_end tracks widest seen ending at <= s."""
    if not intervals:
        return 0
    intervals = sorted(intervals, key=lambda x: (x[0], -x[1]))
    max_end = intervals[0][1]
    count = 1
    for i in range(1, len(intervals)):
        s, e = intervals[i]
        if e > max_end:
            count += 1
            max_end = e
    return count


# ============================================================
# Way 4: Brute force O(n^2)
# ============================================================
def remove_covered_intervals_4(intervals):
    """For each interval, check if any other covers it."""
    n = len(intervals)
    covered = [False] * n
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if intervals[j][0] <= intervals[i][0] and intervals[i][1] <= intervals[j][1]:
                covered[i] = True
                break
    return sum(1 for c in covered if not c)


# ============================================================
# Way 5: Sort, then count with explicit "is covered" check
# ============================================================
def remove_covered_intervals_5(intervals):
    """Sort and walk, checking for coverage from any prior interval."""
    if not intervals:
        return 0
    intervals = sorted(intervals, key=lambda x: (x[0], -x[1]))
    max_end = intervals[0][1]
    count = 1
    for i in range(1, len(intervals)):
        s, e = intervals[i]
        if e > max_end:
            count += 1
            max_end = e
    return count


# ============================================================
# Way 6: Sort + scan, count intervals that "win"
# ============================================================
def remove_covered_intervals_6(intervals):
    """Sort by start asc, end desc. Count intervals whose end >= all previous ends."""
    if not intervals:
        return 0
    intervals = sorted(intervals, key=lambda x: (x[0], -x[1]))
    count = 0
    max_end = -1
    for s, e in intervals:
        if e > max_end:
            count += 1
            max_end = e
    return count


# ============================================================
# Way 7: Recursive
# ============================================================
def remove_covered_intervals_7(intervals):
    """Recursive helper."""
    if not intervals:
        return 0
    intervals = sorted(intervals, key=lambda x: (x[0], -x[1]))

    def helper(idx, max_end):
        if idx >= len(intervals):
            return 0
        s, e = intervals[idx]
        if e > max_end:
            return 1 + helper(idx + 1, e)
        return helper(idx + 1, max_end)

    # First interval is always counted; set initial max_end to its end.
    # But the helper correctly handles idx=0 with max_end=first.end (it's
    # always > itself, so it counts).
    return helper(0, intervals[0][1] - 1)


# ============================================================
# Way 8: Class-based
# ============================================================
class CoveredIntervalRemover_8:
    def __init__(self, intervals):
        self.intervals = intervals

    def remove(self):
        if not self.intervals:
            return 0
        sorted_iv = sorted(self.intervals, key=lambda x: (x[0], -x[1]))
        max_end = sorted_iv[0][1]
        count = 1
        for s, e in sorted_iv[1:]:
            if e > max_end:
                count += 1
                max_end = e
        return count


def remove_covered_intervals_8(intervals):
    return CoveredIntervalRemover_8(intervals).remove()


# ============================================================
# Way 9: Group by start, count max ends at unique starts
# ============================================================
def remove_covered_intervals_9(intervals):
    """Group by start; for each start, count intervals with end > max_end_so_far."""
    if not intervals:
        return 0
    from collections import defaultdict
    by_start = defaultdict(list)
    for s, e in intervals:
        by_start[s].append(e)
    max_end = -1
    count = 0
    for s in sorted(by_start.keys()):
        # Within the same start, the largest end survives; smaller are covered.
        ends = sorted(by_start[s], reverse=True)
        for e in ends:
            if e > max_end:
                count += 1
                max_end = e
    return count


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def remove_covered_intervals_10(intervals):
    """
    THE ONE TO MEMORIZE.

    1. Sort by start ascending, end descending.
    2. max_end = first end. count = 1.
    3. For each interval:
       if end > max_end: count += 1, max_end = end.

    Time:  O(n log n)
    Space: O(n) for sort.
    """
    if not intervals:
        return 0
    intervals = sorted(intervals, key=lambda x: (x[0], -x[1]))
    max_end = intervals[0][1]
    count = 1
    for s, e in intervals[1:]:
        if e > max_end:
            count += 1
            max_end = e
    return count


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to count intervals that are not covered by any other interval."

Key Insight:
"Sort by start ascending, end descending. This means for intervals with the
same start, the wider one comes first. As we walk, we maintain max_end:
the widest end seen so far. If the current interval's end <= max_end, it's
covered (its start is <= the interval that gave us max_end, since that
interval came earlier in sort order). Otherwise, it survives."

Algorithm:
1. Sort by (start asc, end desc).
2. max_end = first.end, count = 1.
3. For each interval: if end > max_end: count++, max_end = end.

Edge Cases:
- Empty: 0.
- Single: 1.
- All same: 1 (only widest survives, all others covered).
- Disjoint: all kept.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Sort+walk | O(nlogn)| O(n)  |
| Brute     | O(n^2) | O(1)  |
+-----------+--------+--------+

KEY TRICK:
The sort key `(start asc, end desc)` is critical. Without sorting end
descending, two intervals with same start and different ends would be
ambiguous. Sorting end desc ensures the widest comes first, so subsequent
narrower ones at the same start are correctly classified as covered.

RELATED PROBLEMS:
- Merge Intervals (LC 56).
- Non-overlapping Intervals (LC 435).
- Interval List Intersections (LC 986).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([[1, 4], [3, 6], [2, 8]], 2, "Standard LC1288"),
        ([[1, 4], [2, 3]], 1, "Inner covered"),
        ([[0, 10], [5, 12]], 2, "Not covered"),
        ([[1, 4], [1, 3]], 1, "Same start"),
        ([[1, 2], [1, 4], [0, 3]], 2, "Multiple overlap"),
        ([], 0, "Empty"),
        ([[1, 4]], 1, "Single"),
    ]

    implementations = [
        ("Way 1: Sort + max_end (BEST)", remove_covered_intervals_1),
        ("Way 2: Sort + walk back", remove_covered_intervals_2),
        ("Way 3: Sort + monotonic", remove_covered_intervals_3),
        ("Way 4: Brute O(n^2)", remove_covered_intervals_4),
        ("Way 5: Sort + merge", remove_covered_intervals_5),
        ("Way 6: Sort + scan", remove_covered_intervals_6),
        ("Way 7: Recursive", remove_covered_intervals_7),
        ("Way 8: Class-based", remove_covered_intervals_8),
        ("Way 9: Group by start", remove_covered_intervals_9),
        ("Way 10: Final cleanest", remove_covered_intervals_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for inp, expected, desc in test_cases:
            try:
                result = fn(copy.deepcopy(inp))
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: input={inp} expected={expected} got={result}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 60)
    print(HOW_TO_THINK)


if __name__ == "__main__":
    run_tests()
