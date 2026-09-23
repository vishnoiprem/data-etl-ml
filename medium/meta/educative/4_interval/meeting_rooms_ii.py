"""
Meeting Rooms II - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/meeting-rooms-ii

Given an array of meeting time intervals, find the minimum number of
conference rooms required.

KEY INSIGHT:
Sweep line or min-heap. Sort starts, sort ends. Two pointers: walk
through starts; for each start, if it overlaps an end, need new room;
else reuse.

Examples:
    [[0,30],[5,10],[15,20]] -> 2
    [[7,10],[2,4]] -> 1

Constraints:
- 1 <= intervals.length <= 10^4
"""

import copy
import sys
import heapq

sys.setrecursionlimit(100000)


def _eq(a, b):
    return a == b


# ============================================================
# Way 1: Chronological ordering / two-pointer sweep (BEST - Memorize!)
# ============================================================
def min_meeting_rooms_1(intervals):
    """Sort starts and ends. Use two pointers."""
    if not intervals:
        return 0
    starts = sorted([iv[0] for iv in intervals])
    ends = sorted([iv[1] for iv in intervals])
    rooms = 0
    end_ptr = 0
    for start in starts:
        if start >= ends[end_ptr]:
            # This meeting's start is at/after when another meeting ended
            # -> reuse that room.
            end_ptr += 1
        else:
            rooms += 1
    return rooms


# ============================================================
# Way 2: Min-heap
# ============================================================
def min_meeting_rooms_2(intervals):
    """Sort by start. Push end times to min-heap. Pop if meeting ends before next starts."""
    if not intervals:
        return 0
    intervals = sorted(intervals, key=lambda x: x[0])
    heap = []  # min-heap of end times
    for s, e in intervals:
        if heap and heap[0] <= s:
            heapq.heappop(heap)
        heapq.heappush(heap, e)
    return len(heap)


# ============================================================
# Way 3: Sweep line (events)
# ============================================================
def min_meeting_rooms_3(intervals):
    """Sweep line: +1 on start, -1 on end. Max prefix sum = rooms."""
    if not intervals:
        return 0
    events = []
    for s, e in intervals:
        events.append((s, 1))    # meeting starts: need a room
        events.append((e, -1))   # meeting ends: free a room
    # Sort: ends (-1) before starts (+1) at same time so touching intervals
    # can share a room.
    events.sort(key=lambda x: (x[0], x[1]))
    rooms = 0
    best = 0
    for _, delta in events:
        rooms += delta
        best = max(best, rooms)
    return best


# ============================================================
# Way 4: Group by conflict (start/end list walk)
# ============================================================
def min_meeting_rooms_4(intervals):
    """Walk starts list with end pointer."""
    if not intervals:
        return 0
    starts = sorted([iv[0] for iv in intervals])
    ends = sorted([iv[1] for iv in intervals])
    used = 0
    best = 0
    i = j = 0
    while i < len(starts):
        if starts[i] < ends[j]:
            used += 1
            best = max(best, used)
            i += 1
        else:
            used -= 1
            j += 1
    return best


# ============================================================
# Way 5: Sort, then walk and count max overlap at any time
# ============================================================
def min_meeting_rooms_5(intervals):
    """Sort intervals; use min-heap of end times."""
    if not intervals:
        return 0
    intervals = sorted(intervals, key=lambda x: x[0])
    ends = []
    for s, e in intervals:
        if ends and ends[0] <= s:
            ends.pop(0)
        ends.append(e)
        ends.sort()
    return len(ends)


# ============================================================
# Way 6: Recursive
# ============================================================
def min_meeting_rooms_6(intervals):
    """Recursive divide-and-conquer approach."""
    if not intervals:
        return 0

    def helper(ivs):
        if len(ivs) <= 1:
            return ivs, max(1, len(ivs))
        mid = len(ivs) // 2
        left_ivs, left_max = helper(ivs[:mid])
        right_ivs, right_max = helper(ivs[mid:])
        all_ivs = left_ivs + right_ivs
        events = []
        for s, e in all_ivs:
            events.append((s, 1))
            events.append((e, -1))
        events.sort(key=lambda x: (x[0], x[1]))
        cur = 0
        best = 0
        for _, d in events:
            cur += d
            best = max(best, cur)
        return all_ivs, max(left_max, right_max, best)

    _, max_rooms = helper(intervals)
    return max_rooms


# ============================================================
# Way 7: Class-based (heap)
# ============================================================
class MeetingRoomCalculator_7:
    def __init__(self, intervals):
        self.intervals = intervals

    def min_rooms(self):
        if not self.intervals:
            return 0
        sorted_iv = sorted(self.intervals, key=lambda x: x[0])
        heap = []
        for s, e in sorted_iv:
            if heap and heap[0] <= s:
                heapq.heappop(heap)
            heapq.heappush(heap, e)
        return len(heap)


def min_meeting_rooms_7(intervals):
    return MeetingRoomCalculator_7(intervals).min_rooms()


# ============================================================
# Way 8: Sort both lists, then merge-walk
# ============================================================
def min_meeting_rooms_8(intervals):
    """Sort starts; walk with end pointer."""
    if not intervals:
        return 0
    starts = sorted([iv[0] for iv in intervals])
    ends = sorted([iv[1] for iv in intervals])
    i = j = 0
    rooms = 0
    used = 0
    while i < len(starts):
        if j < len(ends) and ends[j] <= starts[i]:
            used -= 1
            j += 1
        else:
            used += 1
            i += 1
            rooms = max(rooms, used)
    return rooms


# ============================================================
# Way 9: Track currently active meetings
# ============================================================
def min_meeting_rooms_9(intervals):
    """Use a set to track active meetings (less efficient)."""
    if not intervals:
        return 0
    intervals = sorted(intervals, key=lambda x: x[0])
    active = []
    max_rooms = 0
    for s, e in intervals:
        # Remove ended meetings
        active = [a for a in active if a > s]
        # Add current
        active.append(e)
        active.sort()
        max_rooms = max(max_rooms, len(active))
    return max_rooms


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def min_meeting_rooms_10(intervals):
    """
    THE ONE TO MEMORIZE.

    1. Sort starts and ends separately.
    2. Walk starts with end_ptr.
    3. If current start >= ends[end_ptr]: reuse room, end_ptr++.
    4. Else: need new room.

    Time:  O(n log n)
    Space: O(n).
    """
    if not intervals:
        return 0
    starts = sorted([iv[0] for iv in intervals])
    ends = sorted([iv[1] for iv in intervals])
    end_ptr = 0
    rooms = 0
    for start in starts:
        if start >= ends[end_ptr]:
            end_ptr += 1
        else:
            rooms += 1
    return rooms


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the minimum number of meeting rooms required to host all
meetings without conflict."

Key Insight:
"Two-pointer sweep: sort meeting starts and ends separately. Walk through
starts; for each start, if it's after the earliest end, the room is freed
(reuse). Otherwise, we need a new room."

Algorithm:
1. Sort starts, sort ends.
2. end_ptr = 0, rooms = 0.
3. For each start:
   if start >= ends[end_ptr]: end_ptr += 1
   else: rooms += 1
4. Return rooms.

Alternative (Min-heap):
1. Sort intervals by start.
2. Push end times onto a min-heap.
3. For each meeting, if heap[0] <= start, pop.
4. Push current end.
5. Heap size = max rooms.

Edge Cases:
- Empty: 0.
- Single meeting: 1.
- Nested: depth = max rooms.
- Back-to-back (touching): same room.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| 2-pointer | O(nlogn)| O(n)  |
| Min-heap  | O(nlogn)| O(n)  |
| Sweep     | O(nlogn)| O(n)  |
+-----------+--------+--------+

KEY TRICK:
Back-to-back meetings ([1,4],[4,5]) can share a room because end=4 < start=4.
Use <= for "ends before next starts" instead of <.

RELATED PROBLEMS:
- Meeting Rooms (LC 252): just detect conflict.
- Interval List Intersections (LC 986).
- Car Pooling (LC 1094).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([[0, 30], [5, 10], [15, 20]], 2, "Standard"),
        ([[7, 10], [2, 4]], 1, "Two non-overlapping"),
        ([[1, 5], [2, 6], [4, 8]], 3, "All overlap"),
        ([[1, 4], [4, 5]], 1, "Touching"),
        ([[1, 5]], 1, "Single"),
        ([], 0, "Empty"),
        ([[1, 10], [2, 3], [4, 5], [6, 7]], 2, "Stacked inside one"),
    ]

    implementations = [
        ("Way 1: Chronological 2-ptr (BEST)", min_meeting_rooms_1),
        ("Way 2: Min-heap", min_meeting_rooms_2),
        ("Way 3: Sweep line", min_meeting_rooms_3),
        ("Way 4: Group conflict", min_meeting_rooms_4),
        ("Way 5: Sort + list", min_meeting_rooms_5),
        ("Way 6: Recursive", min_meeting_rooms_6),
        ("Way 7: Class-based", min_meeting_rooms_7),
        ("Way 8: Two-pointer merge-walk", min_meeting_rooms_8),
        ("Way 9: Active set", min_meeting_rooms_9),
        ("Way 10: Final cleanest", min_meeting_rooms_10),
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
