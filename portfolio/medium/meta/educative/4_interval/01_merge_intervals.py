"""
Merge Intervals - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/merge-intervals

Given a list of intervals, merge all overlapping intervals and return a list
of non-overlapping intervals that cover all the input.

KEY INSIGHT:
Sort by start. Walk through; if current overlaps previous, extend previous.
"Overlap" means current.start <= prev.end (closed intervals).

Examples:
    [[1,3],[2,6],[8,10],[15,18]] -> [[1,6],[8,10],[15,18]]

Constraints:
- 1 <= intervals.length <= 10^4
- intervals[i].length == 2
- 0 <= start <= end <= 10^4
"""

import copy
import sys

sys.setrecursionlimit(100000)


def _intervals_equal(a, b):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if len(a) != len(b):
        return False
    return all(a[i] == b[i] for i in range(len(a)))


def _overlaps(a, b):
    """Two intervals overlap if a.start <= b.end and b.start <= a.end."""
    return a[0] <= b[1] and b[0] <= a[1]


def _merge_two(a, b):
    return [min(a[0], b[0]), max(a[1], b[1])]


# ============================================================
# Way 1: Sort by start, walk and extend (BEST - Memorize!)
# ============================================================
def merge_intervals_1(intervals):
    """Sort by start. Walk. If current overlaps prev, extend prev."""
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: x[0])
    merged = [intervals[0][:]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


# ============================================================
# Way 2: Sort + iterative merge into new list
# ============================================================
def merge_intervals_2(intervals):
    """Sort and merge into a fresh list."""
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: x[0])
    out = []
    for cur in intervals:
        if out and cur[0] <= out[-1][1]:
            out[-1][1] = max(out[-1][1], cur[1])
        else:
            out.append(cur[:])
    return out


# ============================================================
# Way 3: In-place merge (after sort)
# ============================================================
def merge_intervals_3(intervals):
    """Sort in place; merge in place by tracking write index."""
    if not intervals:
        return []
    intervals.sort(key=lambda x: x[0])
    write = 0
    for read in range(1, len(intervals)):
        if intervals[read][0] <= intervals[write][1]:
            intervals[write][1] = max(intervals[write][1], intervals[read][1])
        else:
            write += 1
            intervals[write] = intervals[read][:]
    return intervals[:write + 1]


# ============================================================
# Way 4: Sort by start, end, then merge
# ============================================================
def merge_intervals_4(intervals):
    """Sort by start, then end. Merge."""
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: (x[0], x[1]))
    out = [intervals[0][:]]
    for cur in intervals[1:]:
        if cur[0] <= out[-1][1]:
            out[-1][1] = max(out[-1][1], cur[1])
        else:
            out.append(cur[:])
    return out


# ============================================================
# Way 5: Recursive
# ============================================================
def merge_intervals_5(intervals):
    """Sort, then recursively merge from the end."""
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: x[0])

    def helper(idx, acc):
        if idx >= len(intervals):
            return acc
        if acc and intervals[idx][0] <= acc[-1][1]:
            acc[-1][1] = max(acc[-1][1], intervals[idx][1])
        else:
            acc.append(intervals[idx][:])
        return helper(idx + 1, acc)

    return helper(0, [intervals[0][:]])


# ============================================================
# Way 6: Two-pointer approach
# ============================================================
def merge_intervals_6(intervals):
    """Two-pointer approach on sorted intervals."""
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: x[0])
    out = [intervals[0][:]]
    i, j = 0, 1
    while j < len(intervals):
        if intervals[j][0] <= out[i][1]:
            out[i][1] = max(out[i][1], intervals[j][1])
        else:
            out.append(intervals[j][:])
            i += 1
        j += 1
    return out


# ============================================================
# Way 7: Class-based
# ============================================================
class IntervalMerger_7:
    def __init__(self, intervals):
        self.intervals = intervals

    def merge(self):
        if not self.intervals:
            return []
        sorted_iv = sorted(self.intervals, key=lambda x: x[0])
        out = [sorted_iv[0][:]]
        for cur in sorted_iv[1:]:
            if cur[0] <= out[-1][1]:
                out[-1][1] = max(out[-1][1], cur[1])
            else:
                out.append(cur[:])
        return out


def merge_intervals_7(intervals):
    return IntervalMerger_7(intervals).merge()


# ============================================================
# Way 8: Reduce / functools approach
# ============================================================
def merge_intervals_8(intervals):
    """Use functools.reduce to merge."""
    from functools import reduce
    if not intervals:
        return []
    s = sorted(intervals, key=lambda x: x[0])

    def reducer(acc, cur):
        if acc and cur[0] <= acc[-1][1]:
            acc[-1][1] = max(acc[-1][1], cur[1])
        else:
            acc.append(cur[:])
        return acc

    return reduce(reducer, s, [])


# ============================================================
# Way 9: Sort, then explicit two-pointer with extension
# ============================================================
def merge_intervals_9(intervals):
    """Sort and use two-pointer explicit extension."""
    if not intervals:
        return []
    s = sorted(intervals, key=lambda x: x[0])
    out = []
    i = 0
    while i < len(s):
        cur_start = s[i][0]
        cur_end = s[i][1]
        j = i + 1
        while j < len(s) and s[j][0] <= cur_end:
            cur_end = max(cur_end, s[j][1])
            j += 1
        out.append([cur_start, cur_end])
        i = j
    return out


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def merge_intervals_10(intervals):
    """
    THE ONE TO MEMORIZE.

    1. Sort by start.
    2. Initialize merged = [first].
    3. For each next interval:
       if next.start <= merged[-1].end:
         merged[-1].end = max(merged[-1].end, next.end)
       else:
         merged.append(next)

    Time:  O(n log n)
    Space: O(n) for output.
    """
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda x: x[0])
    merged = [intervals[0][:]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to merge overlapping intervals into a minimal set of non-overlapping
intervals that cover the same range."

Key Insight:
"Sort intervals by their start. Then walk through; if the current interval
overlaps the previous one (current.start <= prev.end), extend the previous
one. Otherwise, start a new interval."

Algorithm:
1. Sort by start.
2. merged = [first interval].
3. For each next interval:
   if next.start <= merged[-1].end:
     merged[-1].end = max(merged[-1].end, next.end)
   else:
     merged.append(next).

Edge Cases:
- Empty input: return [].
- Single interval: return [it].
- Already non-overlapping: pass through.
- Fully nested: keep outermost.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Sort+walk | O(nlogn)| O(n)  |
| Sweep line| O(nlogn)| O(n)  |
+-----------+--------+--------+

KEY TRICK:
Compare with <= (not <) for closed intervals. If intervals are open on the
right, use <. The key check is: does the new one start before/at the end
of the current merged interval?

RELATED PROBLEMS:
- Insert Interval (LC 57).
- Interval List Intersections (LC 986).
- Non-overlapping Intervals (LC 435).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([[1, 3], [2, 6], [8, 10], [15, 18]], [[1, 6], [8, 10], [15, 18]], "Standard"),
        ([[1, 4], [4, 5]], [[1, 5]], "Touching"),
        ([[1, 4], [0, 4]], [[0, 4]], "Same end"),
        ([[1, 4], [2, 3]], [[1, 4]], "Nested"),
        ([], [], "Empty"),
        ([[1, 4]], [[1, 4]], "Single"),
        ([[1, 4], [0, 0]], [[0, 0], [1, 4]], "Disjoint"),
        ([[1, 4], [0, 2], [3, 5]], [[0, 5]], "All merge"),
    ]

    implementations = [
        ("Way 1: Sort + walk (BEST)", merge_intervals_1),
        ("Way 2: Sort + new list", merge_intervals_2),
        ("Way 3: Sort + in-place", merge_intervals_3),
        ("Way 4: Sort by (start,end)", merge_intervals_4),
        ("Way 5: Recursive", merge_intervals_5),
        ("Way 6: Two-pointer", merge_intervals_6),
        ("Way 7: Class-based", merge_intervals_7),
        ("Way 8: functools.reduce", merge_intervals_8),
        ("Way 9: Sort + extension", merge_intervals_9),
        ("Way 10: Final cleanest", merge_intervals_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for inp, expected, desc in test_cases:
            try:
                ic = copy.deepcopy(inp)
                result = fn(ic)
                if _intervals_equal(result, expected):
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
