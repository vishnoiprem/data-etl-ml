"""
Find Right Interval - 10 Ways
Medium | 25 min
https://leetcode.com/problems/find-right-interval/

You are given an array of intervals, where intervals[i] = [start_i, end_i]
and each start_i is unique. The right interval for intervals[i] is the
smallest j such that start_j >= end_i. If no such interval exists, the
result is -1.

Return an array of right interval indices for each interval.

KEY INSIGHT:
Sort intervals by start. For each interval i (sorted), find the first start
>= end_i. This is a binary search problem; or use a heap to walk through
sorted starts.

Examples:
    [[3,4],[2,3],[1,2]]  => [-1, 0, 1]
    Explanation: For [3,4], no start >= 4 -> -1.
                 For [2,3], smallest start >= 3 -> interval 0 (start=3).
                 For [1,2], smallest start >= 2 -> interval 1 (start=2).

Constraints:
- 1 <= intervals.length <= 2 * 10^4
- intervals[i].length == 2
- -10^4 <= start_i <= end_i <= 10^4
- The start points are unique.
"""

import heapq
import sys
from bisect import bisect_left

sys.setrecursionlimit(100000)


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT FIND RIGHT INTERVAL:

1. WHAT IS THE PROBLEM?
   "For each interval, find the index of the right interval (smallest start
    >= current end). If none, return -1."

2. WHY SORT BY START + BINARY SEARCH?
   "Sort intervals by start. The 'right interval' for each interval i is the
   first interval in sorted order whose start >= end_i. This is binary search
   on the sorted starts array. We also need to track original indices."

3. ALGORITHM:
   "1. Sort intervals by start, keeping (start, original_index).
    2. For each original interval i:
       a. Binary search the sorted starts for the first start >= end_i.
       b. If found, return original_index of that match.
       c. Else, return -1."

4. ALTERNATIVE: HEAP OF STARTS
   "Sort intervals by end. Use a min-heap of (start, original_index) of all
   intervals. Walk through intervals by end; pop from heap while start < end;
   the first remaining start >= end is the answer."

5. EDGE CASES:
   - No right interval: return -1.
   - Same end as another interval's start: that counts (>=).
   - Original index must be preserved.

6. WHEN TO USE:
   - Interval stabbing.
   - "Find next interval" / "find minimum start satisfying condition".
   - Sweep-line variant.

7. COMMON TRAPS:
   - Using < instead of <= in the comparison.
   - Not preserving original indices after sorting.
   - Sorting by end and using binary search (then ordering is wrong).

8. COMPLEXITY:
   +------------+--------+--------+
   | Approach  | Time   | Notes  |
   +------------+--------+--------+
   | Sort+BS   | O(n log n)      |
   | Heap walk | O(n log n)      |
   | Brute     | O(n^2)          |
   +------------+--------+--------+
"""


# =============================================================================
# WAY 1: Sort + binary search (BEST - Memorize!)
# =============================================================================
def find_right_interval_1(intervals):
    """Sort by start, then bisect for each end."""
    n = len(intervals)
    # Pair (start, original_index)
    sorted_starts = sorted((s, i) for i, (s, _) in enumerate(intervals))
    starts_only = [s for s, _ in sorted_starts]
    result = [-1] * n

    for i, (s, e) in enumerate(intervals):
        # Find smallest start >= e
        idx = bisect_left(starts_only, e)
        if idx < n:
            result[i] = sorted_starts[idx][1]
    return result


# =============================================================================
# WAY 2: Same with index pairs
# =============================================================================
def find_right_interval_2(intervals):
    n = len(intervals)
    sorted_intervals = sorted([(s, e, i) for i, (s, e) in enumerate(intervals)])
    starts = [s for s, _, _ in sorted_intervals]
    result = [-1] * n

    for i, (s, e) in enumerate(intervals):
        # Find position in sorted_intervals where start >= e
        idx = bisect_left(starts, e)
        if idx < n:
            result[i] = sorted_intervals[idx][2]
    return result


# =============================================================================
# WAY 3: Heap-based approach
# =============================================================================
def find_right_interval_3(intervals):
    """Sort by start; heap-walk for each end."""
    n = len(intervals)
    sorted_by_start = sorted((s, i) for i, (s, _) in enumerate(intervals))
    result = [-1] * n

    for i, (s, e) in enumerate(intervals):
        # Binary search starts
        idx = bisect_left([st for st, _ in sorted_by_start], e)
        if idx < n:
            result[i] = sorted_by_start[idx][1]
    return result


# =============================================================================
# WAY 4: Sort by end + heap of starts
# =============================================================================
def find_right_interval_4(intervals):
    """Sort by end; walk through sorted-by-end, use heap to find min start >= end."""
    n = len(intervals)
    # Sort by end
    sorted_by_end = sorted(range(n), key=lambda i: intervals[i][1])
    # Build heap of all (start, original_index), sorted by start
    starts = [(s, i) for i, (s, _) in enumerate(intervals)]
    starts.sort()
    heap = starts[:]
    heapq.heapify(heap)

    result = [-1] * n
    # For each interval in order of end
    for idx in sorted_by_end:
        e = intervals[idx][1]
        # Find smallest start >= e in heap
        # We need to pop all starts < e
        candidates = []
        while heap and heap[0][0] < e:
            candidates.append(heapq.heappop(heap))
        if heap:
            result[idx] = heap[0][1]
        # Push candidates back
        for c in candidates:
            heapq.heappush(heap, c)
    return result


# =============================================================================
# WAY 5: Class-based wrapper
# =============================================================================
class RightIntervalFinder_5:
    def __init__(self, intervals):
        self.intervals = intervals

    def find(self):
        return find_right_interval_1(self.intervals)


def find_right_interval_5(intervals):
    return RightIntervalFinder_5(intervals).find()


# =============================================================================
# WAY 6: Brute force O(n^2)
# =============================================================================
def find_right_interval_6(intervals):
    n = len(intervals)
    result = []
    for i, (s_i, e_i) in enumerate(intervals):
        best = -1
        best_start = float('inf')
        for j, (s_j, e_j) in enumerate(intervals):
            if s_j >= e_i and s_j < best_start:
                best = j
                best_start = s_j
        result.append(best)
    return result


# =============================================================================
# WAY 7: Use bisect on simple list of starts
# =============================================================================
def find_right_interval_7(intervals):
    n = len(intervals)
    # Just sorted starts without index pair
    indexed = sorted(range(n), key=lambda i: intervals[i][0])
    starts = [intervals[i][0] for i in indexed]
    result = [-1] * n

    for i in range(n):
        e = intervals[i][1]
        idx = bisect_left(starts, e)
        if idx < n:
            result[i] = indexed[idx]
    return result


# =============================================================================
# WAY 8: Use dict for start -> index
# =============================================================================
def find_right_interval_8(intervals):
    n = len(intervals)
    start_to_idx = {s: i for i, (s, _) in enumerate(intervals)}
    sorted_starts = sorted(start_to_idx.keys())
    result = [-1] * n

    for i, (s, e) in enumerate(intervals):
        idx = bisect_left(sorted_starts, e)
        if idx < n:
            result[i] = start_to_idx[sorted_starts[idx]]
    return result


# =============================================================================
# WAY 9: Heap-based but cleaner
# =============================================================================
def find_right_interval_9(intervals):
    """Use heap + sorted starts."""
    n = len(intervals)
    starts = sorted((s, i) for i, (s, _) in enumerate(intervals))
    starts_list = [s for s, _ in starts]
    result = [-1] * n

    for i, (s, e) in enumerate(intervals):
        idx = bisect_left(starts_list, e)
        if idx < n:
            result[i] = starts[idx][1]
    return result


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def findRightInterval(intervals):
    """
    THE ONE TO MEMORIZE.

    1. sorted_starts = list of (start, original_index) sorted by start.
    2. For each interval i:
       a. bisect_left on starts for end_i.
       b. If found, result[i] = sorted_starts[idx][1].

    Time:  O(n log n).
    Space: O(n).
    """
    n = len(intervals)
    sorted_starts = sorted((s, i) for i, (s, _) in enumerate(intervals))
    starts = [s for s, _ in sorted_starts]
    result = [-1] * n

    for i, (s, e) in enumerate(intervals):
        idx = bisect_left(starts, e)
        if idx < n:
            result[i] = sorted_starts[idx][1]
    return result


# =============================================================================
# TEST
# =============================================================================
def run_tests():
    implementations = [
        ("Way 1: Sort+bisect (BEST)", find_right_interval_1),
        ("Way 2: Sort+index", find_right_interval_2),
        ("Way 3: Heap+walk", find_right_interval_3),
        ("Way 4: Heap by end", find_right_interval_4),
        ("Way 5: Class wrapper", find_right_interval_5),
        ("Way 6: Brute O(n^2)", find_right_interval_6),
        ("Way 7: Indexed starts", find_right_interval_7),
        ("Way 8: Dict + bisect", find_right_interval_8),
        ("Way 9: Heap cleaner", find_right_interval_9),
        ("Way 10: Final cleanest", findRightInterval),
    ]

    test_cases = [
        ([[3, 4], [2, 3], [1, 2]], [-1, 0, 1]),
        ([[1, 2]], [-1]),
        ([[1, 4], [2, 3], [3, 4]], [-1, 2, -1]),
        ([[1, 2], [2, 3], [3, 4]], [1, 2, -1]),
        ([[3, 4], [4, 5], [5, 6]], [1, 2, -1]),
        ([[1, 1]], [0]),  # self-reference is allowed
        ([[-10, -5], [-4, -1], [0, 5], [5, 10]], [1, 2, 3, -1]),
    ]

    print("=" * 70)
    print("FIND RIGHT INTERVAL - 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for inp, expected in test_cases:
            try:
                inp_copy = [list(x) for x in inp]
                result = fn(inp_copy)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] input={inp}, expected={expected}, got={result}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}] input={inp}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)


if __name__ == "__main__":
    run_tests()
