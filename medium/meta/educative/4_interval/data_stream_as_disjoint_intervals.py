"""
Data Stream as Disjoint Intervals - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/data-stream-as-disjoint-intervals

Implement a SummaryRanges class that supports adding numbers from a data
stream and returning a summary of disjoint intervals of the numbers seen.

KEY INSIGHT:
Maintain a sorted list of disjoint intervals. To add a number:
  1. Find the interval where it would go.
  2. If it extends an existing interval (number is just before/inside), merge.
  3. Otherwise, insert a new [val, val] interval.

Examples:
    add(1) -> [[1,1]]
    add(3) -> [[1,1],[3,3]]
    add(7) -> [[1,1],[3,3],[7,7]]
    add(2) -> [[1,3],[7,7]] (merges 1,1 and 3,3 with 2)

Constraints:
- 0 <= val <= 10^4
- At most 3 * 10^4 calls in total
"""

import copy
import sys
from bisect import bisect_left, bisect_right, insort

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
# Way 1: Sorted intervals list with bisect (BEST - Memorize!)
# ============================================================
class SummaryRanges_1:
    """Maintain sorted intervals using bisect."""

    def __init__(self):
        self.intervals = []  # list of [start, end], sorted by start

    def addNum(self, val):
        # Find the first interval with start > val
        idx = bisect_right(self.intervals, [val, float('inf')])
        # Check if val is already in an interval (the one before idx)
        if idx > 0 and self.intervals[idx - 1][1] >= val:
            return  # already inside
        # Check if we can merge with the next interval
        merge_next = idx < len(self.intervals) and self.intervals[idx][0] == val + 1
        # Check if we can merge with the previous interval
        merge_prev = idx > 0 and self.intervals[idx - 1][1] + 1 == val
        if merge_prev and merge_next:
            new_end = self.intervals[idx][1]
            del self.intervals[idx]
            self.intervals[idx - 1][1] = new_end
        elif merge_prev:
            self.intervals[idx - 1][1] = val
        elif merge_next:
            new_end = self.intervals[idx][1]
            self.intervals[idx][0] = val
        else:
            insort(self.intervals, [val, val])

    def getIntervals(self):
        return [iv[:] for iv in self.intervals]


# ============================================================
# Way 2: Set + on-demand interval construction
# ============================================================
class SummaryRanges_2:
    def __init__(self):
        self.nums = set()

    def addNum(self, val):
        self.nums.add(val)

    def getIntervals(self):
        if not self.nums:
            return []
        sorted_nums = sorted(self.nums)
        intervals = []
        s = sorted_nums[0]
        e = s
        for v in sorted_nums[1:]:
            if v == e + 1:
                e = v
            else:
                intervals.append([s, e])
                s = v
                e = v
        intervals.append([s, e])
        return intervals


# ============================================================
# Way 3: Union-Find style
# ============================================================
class SummaryRanges_3:
    def __init__(self):
        self.parent = {}
        self.intervals = []  # sorted list

    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx != ry:
            self.parent[rx] = ry

    def addNum(self, val):
        self.parent[val] = val
        # Union with val-1 and val+1 if they exist
        if val - 1 in self.parent:
            self.union(val, val - 1)
        if val + 1 in self.parent:
            self.union(val, val + 1)

    def getIntervals(self):
        if not self.parent:
            return []
        roots = {}
        for v in self.parent:
            r = self.find(v)
            if r not in roots:
                roots[r] = [v, v]
            else:
                roots[r][0] = min(roots[r][0], v)
                roots[r][1] = max(roots[r][1], v)
        return sorted(roots.values())


# ============================================================
# Way 4: Mark + iterate
# ============================================================
class SummaryRanges_4:
    def __init__(self):
        self.nums = set()

    def addNum(self, val):
        self.nums.add(val)

    def getIntervals(self):
        if not self.nums:
            return []
        intervals = []
        cur_start = None
        cur_end = None
        for v in sorted(self.nums):
            if cur_start is None:
                cur_start = cur_end = v
            elif v == cur_end + 1:
                cur_end = v
            else:
                intervals.append([cur_start, cur_end])
                cur_start = cur_end = v
        intervals.append([cur_start, cur_end])
        return intervals


# ============================================================
# Way 5: Binary search + manual insert
# ============================================================
class SummaryRanges_5:
    def __init__(self):
        self.intervals = []  # sorted by start

    def addNum(self, val):
        # Binary search for position
        lo, hi = 0, len(self.intervals)
        while lo < hi:
            mid = (lo + hi) // 2
            if self.intervals[mid][0] < val:
                lo = mid + 1
            else:
                hi = mid
        idx = lo
        # Already inside?
        if idx > 0 and self.intervals[idx - 1][1] >= val:
            return
        merge_prev = idx > 0 and self.intervals[idx - 1][1] + 1 == val
        merge_next = idx < len(self.intervals) and self.intervals[idx][0] == val + 1
        if merge_prev and merge_next:
            new_end = self.intervals[idx][1]
            del self.intervals[idx]
            self.intervals[idx - 1][1] = new_end
        elif merge_prev:
            self.intervals[idx - 1][1] = val
        elif merge_next:
            self.intervals[idx][0] = val
        else:
            self.intervals.insert(idx, [val, val])

    def getIntervals(self):
        return [iv[:] for iv in self.intervals]


# ============================================================
# Way 6: Linear scan on add
# ============================================================
class SummaryRanges_6:
    def __init__(self):
        self.intervals = []

    def addNum(self, val):
        # Find the first interval with start > val
        idx = 0
        while idx < len(self.intervals) and self.intervals[idx][0] <= val:
            if self.intervals[idx][1] >= val:
                return  # inside
            idx += 1
        merge_prev = idx > 0 and self.intervals[idx - 1][1] + 1 == val
        merge_next = idx < len(self.intervals) and self.intervals[idx][0] == val + 1
        if merge_prev and merge_next:
            new_end = self.intervals[idx][1]
            del self.intervals[idx]
            self.intervals[idx - 1][1] = new_end
        elif merge_prev:
            self.intervals[idx - 1][1] = val
        elif merge_next:
            self.intervals[idx][0] = val
        else:
            self.intervals.insert(idx, [val, val])

    def getIntervals(self):
        return [iv[:] for iv in self.intervals]


# ============================================================
# Way 7: Class with explicit state
# ============================================================
class SummaryRanges_7:
    def __init__(self):
        self.intervals = []

    def addNum(self, val):
        # Walk to find position
        for i, (s, e) in enumerate(self.intervals):
            if s > val:
                # insert before this
                if (i == 0 or self.intervals[i - 1][1] < val - 1) and e > val + 1:
                    self.intervals.insert(i, [val, val])
                elif i == 0 or self.intervals[i - 1][1] < val - 1:
                    self.intervals[i][0] = val
                elif e > val + 1:
                    self.intervals[i - 1][1] = val
                else:
                    # Merge prev and next (and current)
                    new_end = e
                    del self.intervals[i]
                    self.intervals[i - 1][1] = new_end
                return
            if e >= val:
                return  # inside
        # Insert at end
        if self.intervals and self.intervals[-1][1] + 1 == val:
            self.intervals[-1][1] = val
        else:
            self.intervals.append([val, val])

    def getIntervals(self):
        return [iv[:] for iv in self.intervals]


# ============================================================
# Way 8: Class-based with sorted list of intervals
# ============================================================
class SummaryRanges_8:
    def __init__(self):
        self.intervals = []

    def addNum(self, val):
        # Use bisect for position
        idx = bisect_left([iv[0] for iv in self.intervals], val + 1)
        # Check inside
        for j in range(max(0, idx - 1), min(len(self.intervals), idx + 1)):
            if self.intervals[j][0] <= val <= self.intervals[j][1]:
                return
        # Check merge with prev
        merge_prev = idx > 0 and self.intervals[idx - 1][1] + 1 == val
        merge_next = idx < len(self.intervals) and self.intervals[idx][0] == val + 1
        if merge_prev and merge_next:
            new_end = self.intervals[idx][1]
            del self.intervals[idx]
            self.intervals[idx - 1][1] = new_end
        elif merge_prev:
            self.intervals[idx - 1][1] = val
        elif merge_next:
            self.intervals[idx][0] = val
        else:
            self.intervals.insert(idx, [val, val])

    def getIntervals(self):
        return [iv[:] for iv in self.intervals]


# ============================================================
# Way 9: Dict of intervals, sorted on query
# ============================================================
class SummaryRanges_9:
    def __init__(self):
        self.intervals = {}  # start -> end

    def addNum(self, val):
        # Check if any interval contains val
        for s, e in list(self.intervals.items()):
            if s <= val <= e:
                return
        # Find adjacent intervals
        prev_s = None
        next_s = None
        for s in self.intervals:
            if s == val + 1:
                next_s = s
            if self.intervals[s] == val - 1:
                prev_s = s
        if prev_s is not None and next_s is not None:
            new_end = self.intervals[next_s]
            del self.intervals[next_s]
            self.intervals[prev_s] = new_end
        elif prev_s is not None:
            self.intervals[prev_s] = val
        elif next_s is not None:
            new_end = self.intervals[next_s]
            del self.intervals[next_s]
            self.intervals[val] = new_end
        else:
            self.intervals[val] = val

    def getIntervals(self):
        return [[s, self.intervals[s]] for s in sorted(self.intervals.keys())]


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
class SummaryRanges_10:
    """
    THE ONE TO MEMORIZE.

    Maintain a sorted list of disjoint intervals.
    On addNum(val):
      1. Find the position where val would go (binary search).
      2. If inside an existing interval, do nothing.
      3. If adjacent to prev or next, merge accordingly.
      4. Otherwise, insert a new [val, val].
    """

    def __init__(self):
        self.intervals = []

    def addNum(self, val):
        idx = bisect_right(self.intervals, [val, float('inf')])
        if idx > 0 and self.intervals[idx - 1][1] >= val:
            return
        merge_next = idx < len(self.intervals) and self.intervals[idx][0] == val + 1
        merge_prev = idx > 0 and self.intervals[idx - 1][1] + 1 == val
        if merge_prev and merge_next:
            new_end = self.intervals[idx][1]
            del self.intervals[idx]
            self.intervals[idx - 1][1] = new_end
        elif merge_prev:
            self.intervals[idx - 1][1] = val
        elif merge_next:
            self.intervals[idx][0] = val
        else:
            insort(self.intervals, [val, val])

    def getIntervals(self):
        return [iv[:] for iv in self.intervals]


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to implement a data structure that supports adding numbers from
a stream and returning the disjoint intervals they form."

Key Insight:
"Maintain a sorted list of disjoint intervals. When adding a number:
  - Find its position via binary search.
  - If it's inside an existing interval, do nothing.
  - If it's adjacent to prev or next (val-1 == prev.end or val+1 == next.start),
    merge.
  - Otherwise, insert [val, val]."

Algorithm:
1. bisect_right(intervals, [val, +inf]) to find position.
2. Check if inside any interval; if so, return.
3. Determine merge_prev, merge_next.
4. Insert or merge as appropriate.

Edge Cases:
- Empty stream: [].
- Single number: [[n, n]].
- Consecutive: merge to [n, n+k].
- Repeated add: no-op.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Sorted+BS | O(log n)| O(n)  |
| Set+sort  | O(nlogn)| O(n)  |
| Union-find| O(α(n))| O(n)  |
+-----------+--------+--------+

KEY TRICK:
The four cases for adding: (1) inside, (2) merge prev only, (3) merge next
only, (4) merge both prev and next. Be careful with the indices after
deleting one before merging.

RELATED PROBLEMS:
- Merge Intervals (LC 56).
- Insert Interval (LC 57).
- Summary Ranges (LC 228).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        # (operations, expected_intervals, description)
        ([("addNum", 1), ("getIntervals", None)], [[1, 1]], "Add single"),
        ([("addNum", 1), ("addNum", 3), ("getIntervals", None)], [[1, 1], [3, 3]], "Add disjoint"),
        ([("addNum", 1), ("addNum", 2), ("getIntervals", None)], [[1, 2]], "Consecutive merge"),
        ([("addNum", 1), ("addNum", 3), ("addNum", 2), ("getIntervals", None)], [[1, 3]], "Bridge merge"),
        ([("addNum", 1), ("addNum", 5), ("addNum", 3), ("getIntervals", None)], [[1, 1], [3, 3], [5, 5]], "Out of order adds"),
        ([("addNum", 1), ("addNum", 2), ("addNum", 4), ("addNum", 5), ("getIntervals", None)], [[1, 2], [4, 5]], "Two ranges"),
    ]

    implementations = [
        ("Way 1: Bisect (BEST)", SummaryRanges_1),
        ("Way 2: Set + sort", SummaryRanges_2),
        ("Way 3: Union-find", SummaryRanges_3),
        ("Way 4: Mark + iterate", SummaryRanges_4),
        ("Way 5: Binary search", SummaryRanges_5),
        ("Way 6: Linear scan", SummaryRanges_6),
        ("Way 7: Explicit state", SummaryRanges_7),
        ("Way 8: Class-based", SummaryRanges_8),
        ("Way 9: Dict of intervals", SummaryRanges_9),
        ("Way 10: Final cleanest", SummaryRanges_10),
    ]

    all_pass = True
    for name, cls in implementations:
        passed = 0
        failed = 0
        for ops, expected, desc in test_cases:
            try:
                sr = cls()
                for op, val in ops:
                    if op == "addNum":
                        sr.addNum(val)
                    elif op == "getIntervals":
                        result = sr.getIntervals()
                if _intervals_equal(result, expected):
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: expected={expected} got={result}")
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
