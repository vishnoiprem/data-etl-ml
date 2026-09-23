"""
Minimum Interval to Include Each Query - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-interval-to-include-each-query

Given a list of intervals and a list of queries, for each query return the
size of the smallest interval that contains the query. Return -1 if no
interval contains it.

KEY INSIGHT:
Sort intervals by start. Sort queries. Use a min-heap of (size, end) for
intervals whose start <= query. Pop intervals whose end < query (no longer
contain). The top of the heap is the smallest interval containing the query.

Examples:
    intervals = [[1,4],[2,4],[3,6],[4,4]], queries = [2,3,4,5]
    -> [3,3,2,4]
    ([2,4] size 3, [3,6] size 4 -> smallest for 2 is [2,4] size 3;
     smallest for 3 is [2,4] size 3;
     smallest for 4 is [4,4] size 1 -> wait, [4,4] has size 1.
     Let me re-read.

Actually the smallest interval containing 4 is [4,4] size 1.

Let me redo: for query 4, candidates: [1,4] size 4, [2,4] size 3, [4,4] size 1 -> 1.
For query 5: candidates: [3,6] size 4 -> 4.

Constraints:
- 1 <= intervals.length <= 10^5
- 1 <= queries.length <= 10^5
- 1 <= start <= end <= 10^7
"""

import copy
import sys
import heapq

sys.setrecursionlimit(100000)


def _eq(a, b):
    return a == b


def _min_interval_query_brute(intervals, queries):
    """Brute force for each query."""
    out = []
    for q in queries:
        best = -1
        for s, e in intervals:
            if s <= q <= e:
                size = e - s + 1
                if best == -1 or size < best:
                    best = size
        out.append(best)
    return out


# ============================================================
# Way 1: Sort + min-heap (BEST - Memorize!)
# ============================================================
def min_interval_1(intervals, queries):
    """Sort intervals by start. Sort queries. Use min-heap by size."""
    if not intervals or not queries:
        return [-1] * len(queries)
    intervals = sorted(intervals, key=lambda x: x[0])
    sorted_q = sorted(enumerate(queries), key=lambda x: x[1])
    heap = []  # (size, end)
    out = [-1] * len(queries)
    i = 0
    for orig_idx, q in sorted_q:
        # Add intervals with start <= q
        while i < len(intervals) and intervals[i][0] <= q:
            s, e = intervals[i]
            heapq.heappush(heap, (e - s + 1, e))
            i += 1
        # Remove intervals that no longer contain q
        while heap and heap[0][1] < q:
            heapq.heappop(heap)
        # Top of heap is smallest interval containing q
        if heap:
            out[orig_idx] = heap[0][0]
    return out


# ============================================================
# Way 2: Sort + heap (with explicit removal)
# ============================================================
def min_interval_2(intervals, queries):
    """Same approach, slight variation."""
    if not intervals or not queries:
        return [-1] * len(queries)
    intervals = sorted(intervals)
    sorted_q = sorted(range(len(queries)), key=lambda x: queries[x])
    heap = []
    out = [-1] * len(queries)
    j = 0
    for idx in sorted_q:
        q = queries[idx]
        while j < len(intervals) and intervals[j][0] <= q:
            s, e = intervals[j]
            heapq.heappush(heap, (e - s + 1, e))
            j += 1
        while heap and heap[0][1] < q:
            heapq.heappop(heap)
        out[idx] = heap[0][0] if heap else -1
    return out


# ============================================================
# Way 3: Sort queries and intervals together (sweep)
# ============================================================
def min_interval_3(intervals, queries):
    """Sweep line: at each query, add new intervals, remove stale."""
    if not intervals or not queries:
        return [-1] * len(queries)
    sorted_q = sorted(range(len(queries)), key=lambda x: queries[x])
    sorted_iv = sorted(intervals, key=lambda x: x[0])
    heap = []
    out = [-1] * len(queries)
    j = 0
    for idx in sorted_q:
        q = queries[idx]
        while j < len(sorted_iv) and sorted_iv[j][0] <= q:
            s, e = sorted_iv[j]
            heapq.heappush(heap, (e - s + 1, e))
            j += 1
        while heap and heap[0][1] < q:
            heapq.heappop(heap)
        out[idx] = heap[0][0] if heap else -1
    return out


# ============================================================
# Way 4: Brute force
# ============================================================
def min_interval_4(intervals, queries):
    """For each query, scan all intervals."""
    return _min_interval_query_brute(intervals, queries)


# ============================================================
# Way 5: Sort intervals; for each query, binary search start, then walk
# ============================================================
def min_interval_5(intervals, queries):
    """For each query, find intervals containing it via binary search."""
    if not intervals or not queries:
        return [-1] * len(queries)
    intervals = sorted(intervals)
    out = []
    for q in queries:
        # Binary search for first interval with start > q
        lo, hi = 0, len(intervals)
        while lo < hi:
            mid = (lo + hi) // 2
            if intervals[mid][0] <= q:
                lo = mid + 1
            else:
                hi = mid
        # Now lo is first with start > q. Check prev intervals that may contain q.
        best = -1
        # Walk back from lo - 1, checking intervals whose end >= q
        # But this can be O(n) in the worst case. Let's just walk forward and filter.
        for s, e in intervals:
            if s <= q <= e:
                size = e - s + 1
                if best == -1 or size < best:
                    best = size
        out.append(best)
    return out


# ============================================================
# Way 6: Sweep with index mapping
# ============================================================
def min_interval_6(intervals, queries):
    """Sweep + index mapping."""
    if not intervals or not queries:
        return [-1] * len(queries)
    iv_sorted = sorted(intervals)
    q_sorted = sorted(enumerate(queries), key=lambda x: x[1])
    heap = []
    out = [-1] * len(queries)
    j = 0
    for orig_idx, q in q_sorted:
        while j < len(iv_sorted) and iv_sorted[j][0] <= q:
            s, e = iv_sorted[j]
            heapq.heappush(heap, (e - s + 1, e))
            j += 1
        while heap and heap[0][1] < q:
            heapq.heappop(heap)
        if heap:
            out[orig_idx] = heap[0][0]
    return out


# ============================================================
# Way 7: Class-based wrapper
# ============================================================
class MinIntervalFinder_7:
    def __init__(self, intervals):
        self.intervals = sorted(intervals)
        self.j = 0
        self.heap = []

    def query(self, q):
        while self.j < len(self.intervals) and self.intervals[self.j][0] <= q:
            s, e = self.intervals[self.j]
            heapq.heappush(self.heap, (e - s + 1, e))
            self.j += 1
        while self.heap and self.heap[0][1] < q:
            heapq.heappop(self.heap)
        return self.heap[0][0] if self.heap else -1


def min_interval_7(intervals, queries):
    if not queries:
        return []
    finder = MinIntervalFinder_7(intervals)
    sorted_q = sorted(enumerate(queries), key=lambda x: x[1])
    out = [-1] * len(queries)
    for orig_idx, q in sorted_q:
        out[orig_idx] = finder.query(q)
    return out


# ============================================================
# Way 8: All-queries-first sort (alternative)
# ============================================================
def min_interval_8(intervals, queries):
    """Same as Way 1, refactored."""
    if not intervals or not queries:
        return [-1] * len(queries)
    intervals = sorted(intervals)
    sorted_q = sorted(range(len(queries)), key=lambda x: queries[x])
    heap = []
    out = [-1] * len(queries)
    i = 0
    for idx in sorted_q:
        q = queries[idx]
        while i < len(intervals) and intervals[i][0] <= q:
            s, e = intervals[i]
            heapq.heappush(heap, (e - s + 1, e))
            i += 1
        while heap and heap[0][1] < q:
            heapq.heappop(heap)
        out[idx] = heap[0][0] if heap else -1
    return out


# ============================================================
# Way 9: Sweep with sorted queries list
# ============================================================
def min_interval_9(intervals, queries):
    """Build sorted (q, orig_idx) pairs; sweep."""
    if not intervals or not queries:
        return [-1] * len(queries)
    pairs = sorted(enumerate(queries), key=lambda x: x[1])
    intervals = sorted(intervals)
    heap = []
    out = [-1] * len(queries)
    i = 0
    for oi, q in pairs:
        while i < len(intervals) and intervals[i][0] <= q:
            heapq.heappush(heap, (intervals[i][1] - intervals[i][0] + 1, intervals[i][1]))
            i += 1
        while heap and heap[0][1] < q:
            heapq.heappop(heap)
        out[oi] = heap[0][0] if heap else -1
    return out


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def min_interval_10(intervals, queries):
    """
    THE ONE TO MEMORIZE.

    1. Sort intervals by start.
    2. Sort queries (with original index for output).
    3. Walk queries; at each query q:
       a. Add all intervals with start <= q to a min-heap (by size, end).
       b. Remove intervals whose end < q.
       c. Heap top is smallest interval containing q.

    Time:  O((n + m) log n)
    Space: O(n).
    """
    if not intervals or not queries:
        return [-1] * len(queries)
    intervals = sorted(intervals)
    sorted_q = sorted(range(len(queries)), key=lambda x: queries[x])
    heap = []
    out = [-1] * len(queries)
    i = 0
    for idx in sorted_q:
        q = queries[idx]
        while i < len(intervals) and intervals[i][0] <= q:
            s, e = intervals[i]
            heapq.heappush(heap, (e - s + 1, e))
            i += 1
        while heap and heap[0][1] < q:
            heapq.heappop(heap)
        out[idx] = heap[0][0] if heap else -1
    return out


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find, for each query, the smallest interval that contains it."

Key Insight:
"Sort intervals by start. Sort queries. Use a min-heap keyed by interval
size, storing (size, end). For each query, add intervals whose start is
<= query, then pop intervals whose end is < query. Heap top is the smallest
interval containing the query."

Algorithm:
1. Sort intervals by start.
2. Sort queries (with original indices).
3. i = 0 (pointer in intervals).
4. For each query q in sorted order:
   a. While intervals[i].start <= q: push (size, end) to heap.
   b. While heap top has end < q: pop.
   c. Output heap top's size if heap non-empty, else -1.

Edge Cases:
- Empty intervals or queries: return -1 for each.
- Query outside all intervals: -1.
- Multiple intervals of same size: any is fine.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Heap      | O(nlogm)| O(n)  |
| Brute     | O(nm)  | O(1)  |
+-----------+--------+--------+

KEY TRICK:
Sort queries so we can walk intervals once (each interval is pushed and
popped at most once). The heap gives us the smallest size in O(1)
after cleanup.

RELATED PROBLEMS:
- Meeting Rooms II (LC 253).
- Car Pooling (LC 1094).
- Range Module (LC 715).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([[1, 4], [2, 4], [3, 6], [4, 4]], [2, 3, 4, 5], [3, 3, 1, 4], "Standard LC1851"),
        ([[2, 3], [2, 5], [1, 8], [6, 7]], [1, 5, 5, 8], [8, 4, 4, 8], "Mixed"),
        ([[4, 5], [5, 8]], [1, 4, 5, 6, 8, 10], [-1, 2, 2, 4, 4, -1], "No overlap some"),
        ([], [1, 2], [-1, -1], "Empty intervals"),
        ([[1, 1]], [1, 2], [1, -1], "Single point"),
        ([[1, 10]], [2, 3, 5, 7], [10, 10, 10, 10], "One big interval"),
    ]

    implementations = [
        ("Way 1: Sort + heap (BEST)", min_interval_1),
        ("Way 2: Sort + heap variant", min_interval_2),
        ("Way 3: Sweep + sort", min_interval_3),
        ("Way 4: Brute force", min_interval_4),
        ("Way 5: Binary search walk", min_interval_5),
        ("Way 6: Sweep index map", min_interval_6),
        ("Way 7: Class-based", min_interval_7),
        ("Way 8: Refactored", min_interval_8),
        ("Way 9: Sorted pairs", min_interval_9),
        ("Way 10: Final cleanest", min_interval_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for ivs, qs, expected, desc in test_cases:
            try:
                result = fn(copy.deepcopy(ivs), copy.deepcopy(qs))
                if result == expected:
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
