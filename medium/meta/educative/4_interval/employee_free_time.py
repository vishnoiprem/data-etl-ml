"""
Employee Free Time - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/employee-free-time

Given a list of employees' schedules (each a list of disjoint, sorted
intervals), return a list of intervals representing the common free time
for ALL employees.

KEY INSIGHT:
Merge all intervals into one sorted list. Free time gaps between consecutive
merged intervals are common free time.

Examples:
    schedule = [[[1,3],[5,6]], [[2,3],[6,8]]] -> [[3,5]]
    (Employees are free during 3-5 when neither has a meeting.)

Constraints:
- 1 <= schedule.length, schedule[i].length <= 50
- 0 <= intervals.start < intervals.end <= 10^8
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


def _merge(intervals):
    if not intervals:
        return []
    s = sorted(intervals, key=lambda x: x[0])
    out = [s[0][:]]
    for cur in s[1:]:
        if cur[0] <= out[-1][1]:
            out[-1][1] = max(out[-1][1], cur[1])
        else:
            out.append(cur[:])
    return out


# ============================================================
# Way 1: Flatten, merge, find gaps (BEST - Memorize!)
# ============================================================
def employee_free_time_1(schedule):
    """Flatten all intervals, merge, then find gaps."""
    all_intervals = []
    for emp in schedule:
        all_intervals.extend(emp)
    merged = _merge(all_intervals)
    free = []
    for i in range(1, len(merged)):
        if merged[i][0] > merged[i - 1][1]:
            free.append([merged[i - 1][1], merged[i][0]])
    return free


# ============================================================
# Way 2: Sweep line
# ============================================================
def employee_free_time_2(schedule):
    """Sweep line: collect events, walk and track busy state."""
    events = []
    for emp in schedule:
        for s, e in emp:
            events.append((s, 1))   # start
            events.append((e, -1))  # end
    if not events:
        return []
    events.sort(key=lambda x: (x[0], x[1]))  # ends first at same time
    busy = 0
    free = []
    last_busy_end = None
    for pos, delta in events:
        if delta == 1:  # start
            if busy == 0 and last_busy_end is not None and pos > last_busy_end:
                free.append([last_busy_end, pos])
            busy += 1
        else:  # end
            busy -= 1
            if busy == 0:
                last_busy_end = pos
    return free


# ============================================================
# Way 3: K-way merge using heap
# ============================================================
def employee_free_time_3(schedule):
    """Use min-heap to merge intervals k-way."""
    import heapq
    heap = []  # (start, end, emp_idx, interval_idx)
    for i, emp in enumerate(schedule):
        if emp:
            heapq.heappush(heap, (emp[0][0], emp[0][1], i, 0))
    merged = []
    while heap:
        s, e, ei, ii = heapq.heappop(heap)
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
        if ii + 1 < len(schedule[ei]):
            nxt = schedule[ei][ii + 1]
            heapq.heappush(heap, (nxt[0], nxt[1], ei, ii + 1))
    free = []
    for i in range(1, len(merged)):
        if merged[i][0] > merged[i - 1][1]:
            free.append([merged[i - 1][1], merged[i][0]])
    return free


# ============================================================
# Way 4: Sort by start, walk and find gaps
# ============================================================
def employee_free_time_4(schedule):
    """Sort all intervals by start, walk and merge, then find gaps."""
    all_intervals = [iv for emp in schedule for iv in emp]
    if not all_intervals:
        return []
    all_intervals.sort(key=lambda x: x[0])
    merged = [all_intervals[0][:]]
    for cur in all_intervals[1:]:
        if cur[0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], cur[1])
        else:
            merged.append(cur[:])
    free = []
    for i in range(1, len(merged)):
        if merged[i][0] > merged[i - 1][1]:
            free.append([merged[i - 1][1], merged[i][0]])
    return free


def _intersect_intervals(A, B):
    """Intersect two sorted, disjoint interval lists."""
    out = []
    i = j = 0
    while i < len(A) and j < len(B):
        s = max(A[i][0], B[j][0])
        e = min(A[i][1], B[j][1])
        if s < e:
            out.append([s, e])
        if A[i][1] < B[j][1]:
            i += 1
        else:
            j += 1
    return out


# ============================================================
# Way 5: Recursive
# ============================================================
def employee_free_time_5(schedule):
    """Recursive flatten + merge."""
    all_intervals = []
    for emp in schedule:
        all_intervals.extend(emp)

    def merge_recurse(ivs):
        if len(ivs) <= 1:
            return ivs
        mid = len(ivs) // 2
        left = merge_recurse(ivs[:mid])
        right = merge_recurse(ivs[mid:])
        out = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i][0] <= right[j][0]:
                cur = left[i]
                i += 1
            else:
                cur = right[j]
                j += 1
            if out and cur[0] <= out[-1][1]:
                out[-1][1] = max(out[-1][1], cur[1])
            else:
                out.append(cur[:])
        while i < len(left):
            if out and left[i][0] <= out[-1][1]:
                out[-1][1] = max(out[-1][1], left[i][1])
            else:
                out.append(left[i][:])
            i += 1
        while j < len(right):
            if out and right[j][0] <= out[-1][1]:
                out[-1][1] = max(out[-1][1], right[j][1])
            else:
                out.append(right[j][:])
            j += 1
        return out

    merged = merge_recurse(sorted(all_intervals, key=lambda x: x[0]))
    free = []
    for i in range(1, len(merged)):
        if merged[i][0] > merged[i - 1][1]:
            free.append([merged[i - 1][1], merged[i][0]])
    return free


# ============================================================
# Way 6: Class-based
# ============================================================
class EmployeeFreeTimeFinder_6:
    def __init__(self, schedule):
        self.schedule = schedule

    def find(self):
        return employee_free_time_1(self.schedule)


def employee_free_time_6(schedule):
    return EmployeeFreeTimeFinder_6(schedule).find()


# ============================================================
# Way 7: Flatten with list comprehension
# ============================================================
def employee_free_time_7(schedule):
    """Flatten via list comprehension; merge; find gaps."""
    all_intervals = [iv for emp in schedule for iv in emp]
    merged = _merge(all_intervals)
    return [[merged[i - 1][1], merged[i][0]] for i in range(1, len(merged))
            if merged[i][0] > merged[i - 1][1]]


# ============================================================
# Way 8: Two-pointer style per employee
# ============================================================
def employee_free_time_8(schedule):
    """Walk all employees with k pointers, find gaps."""
    if not schedule or not any(schedule):
        return []
    pointers = [0] * len(schedule)
    merged = []
    while True:
        # Find earliest-ending current interval across employees
        best = None
        for i, emp in enumerate(schedule):
            if pointers[i] < len(emp):
                if best is None or emp[pointers[i]][1] < best[1][1]:
                    best = (i, emp[pointers[i]])
        if best is None:
            break
        i, cur = best
        if merged and cur[0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], cur[1])
        else:
            merged.append(cur[:])
        pointers[i] += 1
    free = []
    for i in range(1, len(merged)):
        if merged[i][0] > merged[i - 1][1]:
            free.append([merged[i - 1][1], merged[i][0]])
    return free


# ============================================================
# Way 9: Iterative, build busy ranges then subtract
# ============================================================
def employee_free_time_9(schedule):
    """Build a sorted list of busy ranges; emit gaps."""
    all_ivs = sorted([iv for emp in schedule for iv in emp], key=lambda x: x[0])
    merged = []
    for cur in all_ivs:
        if merged and cur[0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], cur[1])
        else:
            merged.append(cur[:])
    free = []
    for i in range(1, len(merged)):
        if merged[i][0] > merged[i - 1][1]:
            free.append([merged[i - 1][1], merged[i][0]])
    return free


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def employee_free_time_10(schedule):
    """
    THE ONE TO MEMORIZE.

    1. Flatten all intervals across employees.
    2. Sort by start and merge overlapping.
    3. Gaps between consecutive merged intervals are common free time.

    Time:  O(N log N) where N = total intervals.
    Space: O(N).
    """
    all_intervals = [iv for emp in schedule for iv in emp]
    if not all_intervals:
        return []
    merged = _merge(all_intervals)
    return [[merged[i - 1][1], merged[i][0]] for i in range(1, len(merged))
            if merged[i][0] > merged[i - 1][1]]


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the common free time across all employees' schedules."

Key Insight:
"If I merge all employees' busy intervals into one sorted, merged list,
then the gaps between consecutive merged intervals are the times when NO
employee is busy — i.e., common free time."

Algorithm:
1. Flatten all intervals across all employees.
2. Sort by start, merge overlapping intervals.
3. For each pair of consecutive merged intervals, the gap is free time.

Edge Cases:
- Empty schedule: return [].
- All employees busy the whole time: return [].
- Single employee: free time = gaps in their schedule.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Flat+merge| O(NlogN)| O(N)  |
| Sweep     | O(NlogN)| O(N)  |
+-----------+--------+--------+

KEY TRICK:
The "merged intervals" view shows when at least one employee is busy.
The gaps are when no one is busy — that's the common free time.

RELATED PROBLEMS:
- Merge Intervals (LC 56).
- Interval List Intersections (LC 986).
- Meeting Rooms II (LC 253).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([[[1, 3], [5, 6]], [[2, 3], [6, 8]]], [[3, 5]], "Standard LC759"),
        ([[[1, 3], [5, 7]], [[2, 4]], [[6, 8]]], [[4, 5]], "Three employees"),
        ([[[1, 5]], [[2, 3]]], [], "Always busy"),
        ([[[1, 2], [5, 6]]], [[2, 5]], "Single employee, gap"),
        ([[]], [], "Empty schedule"),
        ([[[1, 2]], [[3, 4]]], [[2, 3]], "Two disjoint employees"),
    ]

    implementations = [
        ("Way 1: Flatten + merge (BEST)", employee_free_time_1),
        ("Way 2: Sweep line", employee_free_time_2),
        ("Way 3: K-way heap", employee_free_time_3),
        ("Way 4: Gap intersection", employee_free_time_4),
        ("Way 5: Recursive merge", employee_free_time_5),
        ("Way 6: Class-based", employee_free_time_6),
        ("Way 7: List comp flatten", employee_free_time_7),
        ("Way 8: K-pointer walk", employee_free_time_8),
        ("Way 9: Iterative busy ranges", employee_free_time_9),
        ("Way 10: Final cleanest", employee_free_time_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for inp, expected, desc in test_cases:
            try:
                result = fn(copy.deepcopy(inp))
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
