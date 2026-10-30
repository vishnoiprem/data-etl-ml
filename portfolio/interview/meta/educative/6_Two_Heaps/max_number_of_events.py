"""
Maximum Number of Events - 10 Ways
Medium | 30 min
https://leetcode.com/problems/maximum-number-of-events-that-can-be-attended/

You are given an array of events where events[i] = [startDay_i, endDay_i].
Every event i starts at startDay_i and ends at endDay_i. You can attend any
event on any day d where startDay_i <= d <= endDay_i. You can only attend
ONE event at any given day d.

Return the maximum number of events you can attend.

KEY INSIGHT:
Sort events by start. Walk day by day; at each day, add events whose start
day == today to a min-heap of end days. Pop events that have already ended.
Attend the event with the earliest end day (greedy). This guarantees max
attendance because attending the earliest-ending event leaves flexibility.

Examples:
    [[1,2],[2,3],[3,4]] -> 3
    [[1,2],[2,3],[3,4],[1,2]] -> 4

Constraints:
- 1 <= events.length <= 10^5
- events[i].length == 2
- 1 <= startDay_i <= endDay_i <= 10^5
"""

import heapq
import sys

sys.setrecursionlimit(100000)


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT MAXIMUM NUMBER OF EVENTS:

1. WHAT IS THE PROBLEM?
   "Attend max number of events; one event per day; each event can be
    attended any day in [start, end] inclusive."

2. WHY GREEDY + MIN-HEAP?
   "At each day, consider all events whose start <= today. To maximize the
    total attended, attend the event with the EARLIEST ENDING (it would die
    soonest otherwise)."

3. ALGORITHM:
   "1. Sort events by start day.
    2. min-heap of end days.
    3. For day = 1 to max_day:
       a. Add all events whose start == day to heap (push end).
       b. Pop events whose end < day (already expired).
       c. If heap non-empty: pop top, attend this event, count++.
    4. Return count."

4. EARLY EXIT OPTIMIZATION:
   "If heap is empty and no more events to add (i >= n), break early."

5. EDGE CASES:
   - Events with start == end.
   - Many events same day.
   - Events spanning many days.

6. WHEN TO USE:
   - Interval scheduling with flexible assignment.
   - Greedy by earliest deadline.

7. COMMON TRAPS:
   - Removing expired events BEFORE adding new ones for the day.
   - Confusing < vs <= for end < day.
   - Walking days beyond max end unnecessarily.

8. COMPLEXITY:
   +------------+--------+--------+
   | Operation  | Time   | Notes  |
   +------------+--------+--------+
   | Sort       | O(n log n)      |
   | Heap ops   | O(n log n)      |
   | Day walk   | O(max_day)      |
   | Total      | O(n log n + D)  | D = max day |
   +------------+--------+--------+
"""


# =============================================================================
# WAY 1: Sort by start + min-heap of end days (BEST - Memorize!)
# =============================================================================
def max_events_1(events):
    """Sort by start; min-heap of end days."""
    events.sort()  # by start day
    n = len(events)
    heap = []  # min-heap of end days
    count = 0
    i = 0
    max_day = max(e[1] for e in events)

    for day in range(1, max_day + 2):  # +1 because days are 1-indexed; +1 for inclusive end
        # Add events starting today
        while i < n and events[i][0] <= day:
            heapq.heappush(heap, events[i][1])
            i += 1
        # Remove expired events
        while heap and heap[0] < day:
            heapq.heappop(heap)
        # Attend earliest-ending
        if heap:
            heapq.heappop(heap)
            count += 1

    return count


# =============================================================================
# WAY 2: Sort by start + remove expired before adding
# =============================================================================
def max_events_2(events):
    events.sort()
    n = len(events)
    heap = []
    count = 0
    i = 0
    max_day = max(e[1] for e in events)

    for day in range(1, max_day + 2):
        # First, remove expired
        while heap and heap[0] < day:
            heapq.heappop(heap)
        # Add new
        while i < n and events[i][0] <= day:
            heapq.heappush(heap, events[i][1])
            i += 1
        # Attend
        if heap:
            heapq.heappop(heap)
            count += 1
    return count


# =============================================================================
# WAY 3: Walk only days needed (early exit)
# =============================================================================
def max_events_3(events):
    events.sort()
    n = len(events)
    heap = []
    count = 0
    i = 0

    for day in range(1, 10**6 + 2):
        # Add events starting today
        while i < n and events[i][0] <= day:
            heapq.heappush(heap, events[i][1])
            i += 1
        # Remove expired
        while heap and heap[0] < day:
            heapq.heappop(heap)
        # Early exit if no more events to add and heap empty
        if i >= n and not heap:
            break
        if heap:
            heapq.heappop(heap)
            count += 1
    return count


# =============================================================================
# WAY 4: Sort by end day, use DSU
# =============================================================================
def max_events_4(events):
    """DSU-based: sort by end (then by start desc), find latest available day."""
    if not events:
        return 0
    # Sort by end asc, then start desc (events with less flexibility first)
    events.sort(key=lambda x: (x[1], -x[0]))
    parent = {}

    def find(x):
        if x not in parent:
            return x
        parent[x] = find(parent[x])
        return parent[x]

    count = 0
    for start, end in events:
        day = find(end)
        if day >= start:
            count += 1
            parent[day] = day - 1
    return count


# =============================================================================
# WAY 5: Class-based wrapper
# =============================================================================
class EventAttender_5:
    def __init__(self, events):
        self.events = events

    def max_attended(self):
        return max_events_1(self.events)


def max_events_5(events):
    return EventAttender_5(events).max_attended()


# =============================================================================
# WAY 6: Sort by start, no early exit (naive)
# =============================================================================
def max_events_6(events):
    events.sort()
    n = len(events)
    heap = []
    count = 0
    i = 0
    if not events:
        return 0
    max_day = max(e[1] for e in events)

    for day in range(1, max_day + 1):
        while i < n and events[i][0] <= day:
            heapq.heappush(heap, events[i][1])
            i += 1
        while heap and heap[0] < day:
            heapq.heappop(heap)
        if heap:
            heapq.heappop(heap)
            count += 1
    return count


# =============================================================================
# WAY 7: Sort by end, use union-find to pick latest day
# =============================================================================
def max_events_7(events):
    """Sort by end (then by start desc); for each event pick latest available day."""
    if not events:
        return 0
    events.sort(key=lambda x: (x[1], -x[0]))
    parent = {}

    def find(x):
        if x not in parent:
            return x
        parent[x] = find(parent[x])
        return parent[x]

    count = 0
    for s, e in events:
        day = find(e)
        if day >= s:
            count += 1
            parent[day] = day - 1
    return count


# =============================================================================
# WAY 8: Sort + heap with explicit day counter
# =============================================================================
def max_events_8(events):
    events.sort()
    n = len(events)
    heap = []
    count = 0
    i = 0

    day = 1
    while i < n or heap:
        # Add events starting today
        while i < n and events[i][0] <= day:
            heapq.heappush(heap, events[i][1])
            i += 1
        # Remove expired
        while heap and heap[0] < day:
            heapq.heappop(heap)
        if heap:
            heapq.heappop(heap)
            count += 1
            day += 1
        elif i < n:
            # Skip to next event's start day
            day = events[i][0]
        else:
            break
    return count


# =============================================================================
# WAY 9: Brute force day-by-day attendance
# =============================================================================
def max_events_9(events):
    """Use set of available events per day."""
    events.sort()
    if not events:
        return 0
    max_day = max(e[1] for e in events)
    n = len(events)
    i = 0
    available = []  # events available today (with end day)
    count = 0

    for day in range(1, max_day + 1):
        while i < n and events[i][0] <= day:
            available.append(events[i][1])
            i += 1
        # Remove expired
        available = [e for e in available if e >= day]
        if available:
            # Attend earliest-ending
            available.sort()
            available.pop(0)
            count += 1
    return count


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def maxEvents(events):
    """
    THE ONE TO MEMORIZE.

    1. Sort events by start day.
    2. min-heap of end days.
    3. For day = 1 to max_end + 1:
       a. Push end day for events starting <= today.
       b. Pop expired (end < day).
       c. Pop one (attend earliest-ending); count++.

    Time:  O(n log n + max_day).
    Space: O(n).
    """
    events.sort()
    n = len(events)
    if n == 0:
        return 0
    heap = []
    count = 0
    i = 0
    max_day = max(e[1] for e in events)

    for day in range(1, max_day + 2):
        while i < n and events[i][0] <= day:
            heapq.heappush(heap, events[i][1])
            i += 1
        while heap and heap[0] < day:
            heapq.heappop(heap)
        if heap:
            heapq.heappop(heap)
            count += 1
    return count


# =============================================================================
# TEST
# =============================================================================
def run_tests():
    implementations = [
        ("Way 1: Sort + heap (BEST)", max_events_1),
        ("Way 2: Remove expired first", max_events_2),
        ("Way 3: Early exit", max_events_3),
        ("Way 4: DSU", max_events_4),
        ("Way 5: Class wrapper", max_events_5),
        ("Way 6: Sort + heap naive", max_events_6),
        ("Way 7: Sort by end", max_events_7),
        ("Way 8: Day counter", max_events_8),
        ("Way 9: Brute day-by-day", max_events_9),
        ("Way 10: Final cleanest", maxEvents),
    ]

    test_cases = [
        ([[1, 2], [2, 3], [3, 4]], 3),
        ([[1, 2], [2, 3], [3, 4], [1, 2]], 4),
        ([[1, 4], [4, 4], [2, 2], [3, 4]], 4),  # all 4 events attendable
        ([[1, 100000]], 1),
        ([[1, 1], [2, 2], [3, 3]], 3),
        ([[1, 5], [1, 5], [1, 5]], 3),  # 3 events, attend all on different days
        ([[1, 2], [1, 2]], 2),
        ([[1, 10], [2, 3], [4, 5], [6, 7], [8, 9]], 5),
    ]

    print("=" * 70)
    print("MAXIMUM NUMBER OF EVENTS - 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for inp, expected in test_cases:
            try:
                inp_copy = [list(e) for e in inp]
                result = fn(inp_copy)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] events={inp}, expected={expected}, got={result}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}] events={inp}: {e}")
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
