"""
Schedule Tasks on Minimum Machines - 10 Ways
Medium | 20 min
Given a list of tasks where each task is (start, end), find the minimum
number of machines required to run all tasks (where one machine can only
run one task at a time).

This is equivalent to LC 253: Meeting Rooms II - given meeting intervals,
find min number of meeting rooms required.

KEY INSIGHT:
Sort intervals by start. Use a min-heap of end times. For each interval:
- If the earliest-ending meeting has ended before this interval starts,
  reuse that machine (pop from heap).
- Otherwise, need a new machine (push new end time).
The heap size is the answer.

Examples:
    [[0,30],[5,10],[15,20]]  =>  2
    [[7,10],[2,4]]  =>  1

Constraints:
- 1 <= intervals.length <= 10^4
- 0 <= starti < endi <= 10^6
"""

import heapq
import sys

sys.setrecursionlimit(100000)


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT MIN MACHINES / MEETING ROOMS:

1. WHAT IS THE PROBLEM?
   "Given intervals [start, end), find the max number of overlapping
   intervals (= min machines needed at peak)."

2. WHY MIN-HEAP OF END TIMES?
   "Sort intervals by start. For each interval, the smallest end time in
    the heap represents the meeting that ends soonest. If that end time
    is <= this interval's start, we can reuse that room (pop).
    Otherwise, we need a new room (push)."

3. ALGORITHM:
   "1. Sort intervals by start.
    2. min_heap = [].
    3. For each (start, end) in sorted intervals:
       a. While min_heap and min_heap[0] <= start: pop (room freed).
       b. Push end to min_heap.
    4. Return len(min_heap)."

4. ALTERNATIVE: SWEEP LINE
   "Create events (time, delta): +1 at start, -1 at end. Sort by time.
    Walking through events, the running sum is the # of active meetings.
    Max running sum = min rooms."

5. WHEN TO USE:
   - Min machines / meeting rooms.
   - Max concurrent users / connections.
   - Resource allocation with time-bound tasks.

6. COMMON TRAPS:
   - Inclusive vs exclusive intervals (use <= for start vs end).
   - Not sorting by start first.
   - Using max-heap instead of min-heap for end times.

7. COMPLEXITY:
   +-------------+--------+--------+
   | Operation   | Time   | Notes  |
   +-------------+--------+--------+
   | Sort        | O(n log n)      |
   | Heap ops    | O(n log n)      |
   | Total       | O(n log n)      |
   | Space       | O(n)            |
   +-------------+--------+--------+
"""


# =============================================================================
# WAY 1: Sort + min-heap of end times (BEST - Memorize!)
# =============================================================================
def min_machines_1(intervals):
    """Sort by start; use min-heap of end times."""
    if not intervals:
        return 0
    intervals.sort(key=lambda x: x[0])
    heap = []  # min-heap of end times
    for start, end in intervals:
        # Free rooms whose meetings ended before/at this start
        while heap and heap[0] <= start:
            heapq.heappop(heap)
        heapq.heappush(heap, end)
    return len(heap)


# =============================================================================
# WAY 2: Sort + heap (single assignment per interval)
# =============================================================================
def min_machines_2(intervals):
    if not intervals:
        return 0
    intervals.sort()
    heap = []
    for start, end in intervals:
        if heap and heap[0] <= start:
            heapq.heapreplace(heap, end)
        else:
            heapq.heappush(heap, end)
    return len(heap)


# =============================================================================
# WAY 3: Sweep line
# =============================================================================
def min_machines_3(intervals):
    """Sweep line: events [time, delta]; running sum = concurrent."""
    if not intervals:
        return 0
    events = []
    for s, e in intervals:
        events.append((s, 1))
        events.append((e, -1))
    events.sort()
    cur = 0
    best = 0
    for _, delta in events:
        cur += delta
        best = max(best, cur)
    return best


# =============================================================================
# WAY 4: Sweep line with explicit loop
# =============================================================================
def min_machines_4(intervals):
    if not intervals:
        return 0
    events = []
    for s, e in intervals:
        events.append((s, 1))  # meeting starts
        events.append((e, -1))  # meeting ends
    events.sort()
    cur = 0
    best = 0
    for time, delta in events:
        cur += delta
        if cur > best:
            best = cur
    return best


# =============================================================================
# WAY 5: Class-based wrapper
# =============================================================================
class TaskScheduler_5:
    def __init__(self, intervals):
        self.intervals = intervals

    def min_machines(self):
        return min_machines_1(self.intervals)


def min_machines_5(intervals):
    return TaskScheduler_5(intervals).min_machines()


# =============================================================================
# WAY 6: Brute force - sweep line as brute force
# =============================================================================
def min_machines_6(intervals):
    """Brute force sweep line: count active intervals at each unique time."""
    if not intervals:
        return 0
    n = len(intervals)
    max_active = 0
    # Check every unique start time
    for s, _ in intervals:
        # Count intervals active at this start time (inclusive start, exclusive end)
        active = sum(1 for s2, e2 in intervals if s2 <= s < e2)
        max_active = max(max_active, active)
    return max_active


# =============================================================================
# WAY 7: Sort + count overlap with two-pointer
# =============================================================================
def min_machines_7(intervals):
    """Two pointers over sorted starts and ends."""
    if not intervals:
        return 0
    starts = sorted(s for s, _ in intervals)
    ends = sorted(e for _, e in intervals)
    i = j = 0
    cur = 0
    best = 0
    while i < len(starts):
        if starts[i] < ends[j]:
            cur += 1
            best = max(best, cur)
            i += 1
        else:
            cur -= 1
            j += 1
    return best


# =============================================================================
# WAY 8: Sort + heap with custom comparator
# =============================================================================
def min_machines_8(intervals):
    """Use heapq but with explicit sorted start."""
    if not intervals:
        return 0
    sorted_intervals = sorted(intervals)
    heap = []
    for s, e in sorted_intervals:
        if heap and heap[0] <= s:
            heapq.heappop(heap)
        heapq.heappush(heap, e)
    return len(heap)


# =============================================================================
# WAY 9: Group by start, then sweep
# =============================================================================
def min_machines_9(intervals):
    """Group intervals; sweep through sorted unique times."""
    if not intervals:
        return 0
    events = []
    for s, e in intervals:
        events.append((s, 1))
        events.append((e, -1))
    events.sort()  # ends (-1) come before starts (+1) at same time (lexicographic)
    cur = 0
    best = 0
    for _, delta in events:
        cur += delta
        best = max(best, cur)
    return best


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def minMachines(intervals):
    """
    THE ONE TO MEMORIZE.

    1. Sort intervals by start.
    2. min_heap = []  (stores end times).
    3. For each (start, end):
       a. Pop all ends <= start (rooms freed).
       b. Push end (this meeting now occupies a room).
    4. Return len(min_heap).

    Time:  O(n log n).
    Space: O(n).
    """
    if not intervals:
        return 0
    intervals.sort(key=lambda x: x[0])
    heap = []
    for start, end in intervals:
        while heap and heap[0] <= start:
            heapq.heappop(heap)
        heapq.heappush(heap, end)
    return len(heap)


# =============================================================================
# TEST
# =============================================================================
def run_tests():
    implementations = [
        ("Way 1: Sort + heap (BEST)", min_machines_1),
        ("Way 2: heapreplace", min_machines_2),
        ("Way 3: Sweep line", min_machines_3),
        ("Way 4: Sweep line 2", min_machines_4),
        ("Way 5: Class wrapper", min_machines_5),
        ("Way 6: Brute O(n^2)", min_machines_6),
        ("Way 7: Two pointers", min_machines_7),
        ("Way 8: Sort + heap alt", min_machines_8),
        ("Way 9: Sweep w/ order", min_machines_9),
        ("Way 10: Final cleanest", minMachines),
    ]

    test_cases = [
        ([], 0, "Empty"),
        ([[0, 30]], 1, "Single"),
        ([[0, 30], [5, 10], [15, 20]], 2, "Standard LC253"),
        ([[7, 10], [2, 4]], 1, "Non-overlapping"),
        ([[0, 5], [0, 5], [0, 5]], 3, "All overlap"),
        ([[1, 2], [2, 3], [3, 4]], 1, "Sequential"),
        ([[1, 4], [2, 5], [3, 6], [4, 7]], 3, "Staircase"),
        ([[1, 10], [2, 7], [3, 19], [8, 12], [10, 20]], 3, "Complex"),
    ]

    print("=" * 70)
    print("SCHEDULE TASKS ON MINIMUM MACHINES - 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for inp, expected, desc in test_cases:
            try:
                # Deep copy to avoid mutation issues
                inp_copy = [list(x) for x in inp]
                result = fn(inp_copy)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: input={inp}, expected={expected}, got={result}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}] {desc}: {e}")
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