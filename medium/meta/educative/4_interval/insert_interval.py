"""
Insert Interval - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/insert-interval

Given a list of non-overlapping intervals sorted by start and a new interval,
insert the new interval and merge if necessary.

KEY INSIGHT:
Three phases: (1) intervals ending before new interval, (2) intervals
overlapping new interval (merged), (3) intervals starting after new interval.
Since input is sorted, each phase is contiguous.

Examples:
    intervals = [[1,3],[6,9]], new = [2,5] -> [[1,5],[6,9]]
    intervals = [[1,2],[3,5],[6,7],[8,10],[12,16]], new = [4,8] -> [[1,2],[3,10],[12,16]]

Constraints:
- 0 <= intervals.length <= 10^4
- new interval: [start, end]
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


# ============================================================
# Way 1: Three-phase scan (BEST - Memorize!)
# ============================================================
def insert_interval_1(intervals, new):
    """Three-phase: before, merge, after."""
    out = []
    i = 0
    n = len(intervals)
    # Phase 1: intervals ending before new starts
    while i < n and intervals[i][1] < new[0]:
        out.append(intervals[i][:])
        i += 1
    # Phase 2: merge overlapping intervals
    merged_start, merged_end = new[0], new[1]
    while i < n and intervals[i][0] <= new[1]:
        merged_start = min(merged_start, intervals[i][0])
        merged_end = max(merged_end, intervals[i][1])
        i += 1
    out.append([merged_start, merged_end])
    # Phase 3: intervals starting after merged ends
    while i < n:
        out.append(intervals[i][:])
        i += 1
    return out


# ============================================================
# Way 2: Append new, sort, then merge
# ============================================================
def insert_interval_2(intervals, new):
    """Add new, sort, then merge all."""
    if not intervals:
        return [new[:]]
    all_iv = intervals + [new]
    all_iv.sort(key=lambda x: x[0])
    out = [all_iv[0][:]]
    for cur in all_iv[1:]:
        if cur[0] <= out[-1][1]:
            out[-1][1] = max(out[-1][1], cur[1])
        else:
            out.append(cur[:])
    return out


# ============================================================
# Way 3: Binary search for insertion point
# ============================================================
def insert_interval_3(intervals, new):
    """Use bisect to find insertion point, then merge."""
    if not intervals:
        return [new[:]]
    # Binary search: find first index where intervals[i].end >= new.start.
    lo, hi = 0, len(intervals)
    while lo < hi:
        mid = (lo + hi) // 2
        if intervals[mid][1] >= new[0]:
            hi = mid
        else:
            lo = mid + 1
    # Find end of merge region: first index with start > new.end
    end_idx = lo
    while end_idx < len(intervals) and intervals[end_idx][0] <= new[1]:
        end_idx += 1
    # Backtrack start_idx to include any intervals that overlap from before.
    start_idx = lo
    while start_idx > 0 and intervals[start_idx - 1][1] >= new[0]:
        start_idx -= 1
    if start_idx < end_idx:
        merged_start = min(new[0], intervals[start_idx][0])
        merged_end = max(new[1], intervals[end_idx - 1][1])
    else:
        merged_start, merged_end = new[0], new[1]
    return intervals[:start_idx] + [[merged_start, merged_end]] + intervals[end_idx:]


# ============================================================
# Way 4: Walk with explicit merged tracking
# ============================================================
def insert_interval_4(intervals, new):
    """Walk and merge into a single accumulator."""
    out = []
    merged = new[:]
    merged_done = False
    for cur in intervals:
        if cur[1] < merged[0]:
            # cur ends before merged starts
            out.append(cur[:])
        elif cur[0] > merged[1]:
            # cur starts after merged ends
            if not merged_done:
                out.append(merged[:])
                merged_done = True
            out.append(cur[:])
        else:
            # overlap; merge
            merged[0] = min(merged[0], cur[0])
            merged[1] = max(merged[1], cur[1])
    if not merged_done:
        out.append(merged[:])
    return out


# ============================================================
# Way 5: Recursive
# ============================================================
def insert_interval_5(intervals, new):
    """Recursive helper."""
    if not intervals:
        return [new[:]]

    def helper(idx, acc, merged):
        if idx >= len(intervals):
            acc.append(merged[:])
            return acc
        cur = intervals[idx]
        if cur[1] < merged[0]:
            acc.append(cur[:])
            return helper(idx + 1, acc, merged)
        if cur[0] > merged[1]:
            acc.append(merged[:])
            acc.extend([iv[:] for iv in intervals[idx:]])
            return acc
        merged[0] = min(merged[0], cur[0])
        merged[1] = max(merged[1], cur[1])
        return helper(idx + 1, acc, merged)

    return helper(0, [], new[:])


# ============================================================
# Way 6: In-place modification
# ============================================================
def insert_interval_6(intervals, new):
    """Mutate the intervals list in place."""
    if not intervals:
        intervals.append(new[:])
        return intervals
    # Find where new ends vs each existing interval
    new_start, new_end = new[0], new[1]
    out = []
    i = 0
    while i < len(intervals) and intervals[i][1] < new_start:
        out.append(intervals[i])
        i += 1
    merged_start, merged_end = new_start, new_end
    while i < len(intervals) and intervals[i][0] <= new_end:
        merged_start = min(merged_start, intervals[i][0])
        merged_end = max(merged_end, intervals[i][1])
        i += 1
    out.append([merged_start, merged_end])
    while i < len(intervals):
        out.append(intervals[i])
        i += 1
    intervals[:] = out
    return intervals


# ============================================================
# Way 7: Class-based
# ============================================================
class IntervalInserter_7:
    def __init__(self, intervals):
        self.intervals = intervals

    def insert(self, new):
        return insert_interval_1(self.intervals, new)


def insert_interval_7(intervals, new):
    return IntervalInserter_7(intervals).insert(new)


# ============================================================
# Way 8: Two-pointer scan
# ============================================================
def insert_interval_8(intervals, new):
    """Two-pointer style with merge."""
    if not intervals:
        return [new[:]]
    out = []
    i = 0
    n = len(intervals)
    ms, me = new[0], new[1]
    placed = False
    while i < n:
        if intervals[i][1] < ms:
            out.append(intervals[i][:])
            i += 1
        elif intervals[i][0] > me:
            if not placed:
                out.append([ms, me])
                placed = True
            out.append(intervals[i][:])
            i += 1
        else:
            ms = min(ms, intervals[i][0])
            me = max(me, intervals[i][1])
            i += 1
    if not placed:
        out.append([ms, me])
    return out


# ============================================================
# Way 9: Sweep-line events
# ============================================================
def insert_interval_9(intervals, new):
    """Sweep-line: collect events, sort, walk and merge."""
    if not intervals:
        return [new[:]]
    events = []
    for iv in intervals:
        events.append((iv[0], 0))  # start
        events.append((iv[1], 1))  # end
    events.append((new[0], 0))
    events.append((new[1], 1))
    events.sort()
    out = []
    depth = 0
    cur_start = None
    for pos, typ in events:
        if typ == 0:  # start
            if depth == 0:
                cur_start = pos
            depth += 1
        else:  # end
            depth -= 1
            if depth == 0:
                out.append([cur_start, pos])
    return out


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def insert_interval_10(intervals, new):
    """
    THE ONE TO MEMORIZE.

    Phase 1: add intervals ending before new.
    Phase 2: merge intervals overlapping new.
    Phase 3: add intervals starting after merged.

    Time:  O(n)
    Space: O(n).
    """
    out = []
    i = 0
    n = len(intervals)
    while i < n and intervals[i][1] < new[0]:
        out.append(intervals[i][:])
        i += 1
    ms, me = new[0], new[1]
    while i < n and intervals[i][0] <= new[1]:
        ms = min(ms, intervals[i][0])
        me = max(me, intervals[i][1])
        i += 1
    out.append([ms, me])
    while i < n:
        out.append(intervals[i][:])
        i += 1
    return out


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to insert a new interval into a sorted list of non-overlapping
intervals and merge if necessary."

Key Insight:
"Since input is sorted by start, I can do this in three phases in O(n):
  1. Add intervals that end before the new interval starts.
  2. Merge all intervals that overlap with the new interval.
  3. Add the rest."

Algorithm:
1. Walk intervals ending before new (interval.end < new.start): add as-is.
2. Walk intervals overlapping new (interval.start <= new.end): merge into
   the new interval.
3. Append the merged interval.
4. Add remaining intervals as-is.

Edge Cases:
- Empty input: return [new].
- new at the start: prepend after merge.
- new at the end: append after merge.
- new fully contained in existing: merge absorbs it.
- new fully covers existing: replaces several.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| 3-phase   | O(n)   | O(n)   |
| Add+merge | O(nlogn)| O(n)  |
+-----------+--------+--------+

KEY TRICK:
The condition "interval.end < new.start" (strict) for phase 1, then
"interval.start <= new.end" for phase 2. The strict-less in phase 1
prevents duplicate processing of touching intervals.

RELATED PROBLEMS:
- Merge Intervals (LC 56).
- Interval List Intersections (LC 986).
- Non-overlapping Intervals (LC 435).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([[1, 3], [6, 9]], [2, 5], [[1, 5], [6, 9]], "Insert middle"),
        ([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8], [[1, 2], [3, 10], [12, 16]], "Standard LC57"),
        ([], [5, 7], [[5, 7]], "Empty intervals"),
        ([[1, 5]], [2, 3], [[1, 5]], "Inside existing"),
        ([[1, 5]], [6, 8], [[1, 5], [6, 8]], "After existing"),
        ([[3, 5], [12, 15]], [6, 6], [[3, 5], [6, 6], [12, 15]], "Single point between"),
        ([[1, 5]], [0, 0], [[0, 0], [1, 5]], "Before existing"),
        ([[1, 5]], [2, 7], [[1, 7]], "Extending right"),
    ]

    implementations = [
        ("Way 1: 3-phase (BEST)", insert_interval_1),
        ("Way 2: Add+sort+merge", insert_interval_2),
        ("Way 3: Binary search", insert_interval_3),
        ("Way 4: Explicit merged", insert_interval_4),
        ("Way 5: Recursive", insert_interval_5),
        ("Way 6: In-place", insert_interval_6),
        ("Way 7: Class-based", insert_interval_7),
        ("Way 8: Two-pointer", insert_interval_8),
        ("Way 9: Sweep-line", insert_interval_9),
        ("Way 10: Final cleanest", insert_interval_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for inp_iv, new_iv, expected, desc in test_cases:
            try:
                if "in-place" in name.lower():
                    arr = copy.deepcopy(inp_iv)
                    result = fn(arr, new_iv)
                elif "class-based" in name.lower():
                    arr = copy.deepcopy(inp_iv)
                    result = fn(arr, new_iv)
                else:
                    result = fn(copy.deepcopy(inp_iv), new_iv)
                if _intervals_equal(result, expected):
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: input={inp_iv} new={new_iv} expected={expected} got={result}")
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
