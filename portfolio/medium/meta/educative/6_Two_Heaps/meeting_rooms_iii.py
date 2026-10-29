"""
Meeting Rooms III - 10 Ways
Hard | 35 min
https://leetcode.com/problems/meeting-rooms-iii/

You have n meeting rooms numbered 0 to n-1. You are given a 2D integer
array meetings where meetings[i] = [start_i, end_i] meaning a meeting will
be held during the half-closed time interval [start_i, end_i).

Allocate meetings to rooms following these rules:
1. Each meeting will be held in the smallest indexed room that is free and
   can host it (i.e., the room has no overlapping meeting).
2. If no room is free, the meeting is delayed until the earliest occupied
   room becomes free. The delayed meeting still uses the smallest indexed
   room among all currently free rooms.

Return the index of the room that hosted the most meetings. If there are
multiple rooms with the same maximum count, return the smallest indexed one.

KEY INSIGHT:
Maintain two heaps:
- available: min-heap of free room indices (always pop smallest first).
- busy: min-heap of (end_time, room_index) for rooms currently in use.

For each meeting [start, end]:
1. Free up rooms whose end_time <= start.
2. If available is non-empty: pop smallest room, schedule meeting there.
3. Else: pop earliest-busy (end_time, room). Delay start to end_time,
   set new end = end_time + (end - start). Reuse that room.
Track meeting count per room; return index with max count (tie -> smallest).

Examples:
    n=2, meetings=[[0,10],[1,5],[2,7],[3,4]]
    Output: 0
    Explanation:
      - Meeting 0 [0,10] -> room 0
      - Meeting 1 [1,5]  -> room 1
      - Meeting 2 [2,7]   -> no room; wait for room 0 at 10; [10,15] in room 0
      - Meeting 3 [3,4]   -> no room; wait for room 1 at 5; [5,6] in room 1
      Room 0 has 2 meetings, room 1 has 2 meetings; return 0.

Constraints:
- 1 <= n <= 100
- 1 <= meetings.length <= 10^5
- 0 <= start_i < end_i <= 10^6
"""

import heapq
import sys
from collections import Counter

sys.setrecursionlimit(100000)


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT MEETING ROOMS III:

1. WHAT IS THE PROBLEM?
   "Schedule meetings into n rooms. If all rooms busy, defer the meeting
    until the earliest room frees. Return the room with most meetings."

2. WHY TWO HEAPS?
   "We need:
    - The smallest-indexed FREE room (pop min from available heap).
    - The EARLIEST-FREEING busy room (pop min end_time from busy heap).
   Two min-heaps solve both in O(log n) per meeting."

3. ALGORITHM:
   "available = min-heap of all room indices [0, 1, ..., n-1].
    busy = min-heap of (end_time, room_index).
    count = array of size n, all zeros.

    For each (start, end) in meetings:
      a. While busy not empty AND busy[0].end <= start:
           pop (end, room); push room to available.
      b. If available not empty:
           room = heappop(available)
      c. Else:
           (end_time, room) = heappop(busy)
           start = end_time  # meeting delayed
           end = end_time + (original duration)
      d. count[room] += 1
      e. heappush(busy, (end, room))

    Return index with max count; tie -> smaller index."

4. EDGE CASES:
   - Meeting starts at 0: all rooms available.
   - Meetings ordered by start (input is sorted by start per LC guarantee).
   - Long delays: meeting can be delayed arbitrarily long.
   - Ties in count: choose smaller index.

5. WHEN TO USE:
   - Resource allocation with priority by index.
   - Job queue with priority rooms.
   - Defer and reassign tasks.

6. COMMON TRAPS:
   - Not freeing rooms whose end <= current start BEFORE checking available.
   - Not updating the duration when deferring a meeting.
   - Tie-breaking by smallest index needs careful final scan.

7. COMPLEXITY:
   +-------------+--------+--------+
   | Operation   | Time   | Notes  |
   +-------------+--------+--------+
   | Per meeting | O(log n + #freeups) | amortized O(log n) |
   | Overall     | O(m log n) | m meetings |
   | Space       | O(n)     | heaps + counts |
   +-------------+--------+--------+
"""


# =============================================================================
# WAY 1: Two heaps (BEST - Memorize!)
# =============================================================================
def most_booked_1(n, meetings):
    """Min-heap of available rooms; min-heap of (end, room) for busy."""
    available = list(range(n))
    heapq.heapify(available)
    busy = []  # (end_time, room)
    count = [0] * n

    for start, end in meetings:
        duration = end - start
        # Free rooms whose meetings ended at or before this start
        while busy and busy[0][0] <= start:
            _, room = heapq.heappop(busy)
            heapq.heappush(available, room)
        if available:
            room = heapq.heappop(available)
            heapq.heappush(busy, (end, room))
        else:
            earliest_end, room = heapq.heappop(busy)
            new_end = earliest_end + duration
            heapq.heappush(busy, (new_end, room))
        count[room] += 1

    # Return room with max count, smallest index on ties
    best = 0
    for i in range(1, n):
        if count[i] > count[best]:
            best = i
    return best


# =============================================================================
# WAY 2: Same as 1 with explicit tie-break
# =============================================================================
def most_booked_2(n, meetings):
    available = list(range(n))
    heapq.heapify(available)
    busy = []
    count = [0] * n

    for start, end in meetings:
        duration = end - start
        while busy and busy[0][0] <= start:
            _, room = heapq.heappop(busy)
            heapq.heappush(available, room)
        if available:
            room = heapq.heappop(available)
            heapq.heappush(busy, (end, room))
            count[room] += 1
        else:
            earliest_end, room = heapq.heappop(busy)
            heapq.heappush(busy, (earliest_end + duration, room))
            count[room] += 1

    best = 0
    for i in range(1, n):
        if count[i] > count[best]:
            best = i
    return best


# =============================================================================
# WAY 3: Use Counter + argmax
# =============================================================================
def most_booked_3(n, meetings):
    available = list(range(n))
    heapq.heapify(available)
    busy = []
    count = Counter()

    for start, end in meetings:
        duration = end - start
        while busy and busy[0][0] <= start:
            _, room = heapq.heappop(busy)
            heapq.heappush(available, room)
        if available:
            room = heapq.heappop(available)
            heapq.heappush(busy, (end, room))
        else:
            earliest_end, room = heapq.heappop(busy)
            heapq.heappush(busy, (earliest_end + duration, room))
        count[room] += 1

    # Find max count; tie -> smallest index
    best_count = -1
    best_room = 0
    for room in range(n):
        if count[room] > best_count:
            best_count = count[room]
            best_room = room
    return best_room


# =============================================================================
# WAY 4: Event-driven without heap (slow)
# =============================================================================
def most_booked_4(n, meetings):
    """Brute: simulate room state array."""
    rooms_free_at = [0] * n
    count = [0] * n

    for start, end in meetings:
        duration = end - start
        # Find available room (free_at <= start). Choose smallest index.
        chosen = None
        for r in range(n):
            if rooms_free_at[r] <= start:
                chosen = r
                break
        if chosen is None:
            # Find earliest freeing room
            earliest_end = min(rooms_free_at)
            chosen = rooms_free_at.index(earliest_end)
            rooms_free_at[chosen] = earliest_end + duration
        else:
            rooms_free_at[chosen] = end
        count[chosen] += 1

    best = 0
    for i in range(1, n):
        if count[i] > count[best]:
            best = i
    return best


# =============================================================================
# WAY 5: Class-based wrapper
# =============================================================================
class MeetingScheduler_5:
    def __init__(self, n):
        self.n = n

    def most_booked(self, meetings):
        return most_booked_1(self.n, meetings)


def most_booked_5(n, meetings):
    return MeetingScheduler_5(n).most_booked(meetings)


# =============================================================================
# WAY 6: Two heaps with index-tracked counts (defensive variant)
# =============================================================================
def most_booked_6(n, meetings):
    """Same as Way 1; emphasize count tracking."""
    available = list(range(n))
    heapq.heapify(available)
    busy = []
    count = [0] * n

    for start, end in meetings:
        duration = end - start
        while busy and busy[0][0] <= start:
            _, room = heapq.heappop(busy)
            heapq.heappush(available, room)
        if available:
            room = heapq.heappop(available)
            heapq.heappush(busy, (end, room))
        else:
            earliest_end, room = heapq.heappop(busy)
            heapq.heappush(busy, (earliest_end + duration, room))
        count[room] += 1

    # Tie-break by smaller index (since we iterate i=1..n-1, replace if strictly greater)
    best = 0
    for i in range(1, n):
        if count[i] > count[best]:
            best = i
    return best


# =============================================================================
# WAY 7: Use tuple (end, room) for busy; pop with heappop+heappush
# =============================================================================
def most_booked_7(n, meetings):
    available = list(range(n))
    heapq.heapify(available)
    busy = []  # (end, room)
    count = [0] * n

    for start, end in meetings:
        duration = end - start
        while busy and busy[0][0] <= start:
            _, room = heapq.heappop(busy)
            heapq.heappush(available, room)
        if available:
            room = heapq.heappop(available)
            heapq.heappush(busy, (end, room))
        else:
            earliest_end, room = heapq.heappop(busy)
            heapq.heappush(busy, (earliest_end + duration, room))
        count[room] += 1

    best = 0
    for i in range(1, n):
        if count[i] > count[best]:
            best = i
    return best


# =============================================================================
# WAY 8: Use sorted list for available (alternative)
# =============================================================================
def most_booked_8(n, meetings):
    """Use sortedcontainers-style; here just a sorted list."""
    import bisect
    available = list(range(n))  # sorted
    busy = []  # min-heap of (end, room)
    count = [0] * n

    for start, end in meetings:
        duration = end - start
        while busy and busy[0][0] <= start:
            _, room = heapq.heappop(busy)
            bisect.insort(available, room)
        if available:
            room = available.pop(0)
            heapq.heappush(busy, (end, room))
        else:
            earliest_end, room = heapq.heappop(busy)
            heapq.heappush(busy, (earliest_end + duration, room))
        count[room] += 1

    best = 0
    for i in range(1, n):
        if count[i] > count[best]:
            best = i
    return best


# =============================================================================
# WAY 9: Track busy rooms explicitly with dict
# =============================================================================
def most_booked_9(n, meetings):
    available = list(range(n))
    heapq.heapify(available)
    busy = []
    count = [0] * n

    for start, end in meetings:
        duration = end - start
        # Free rooms
        new_busy = []
        for end_time, room in busy:
            if end_time <= start:
                heapq.heappush(available, room)
            else:
                new_busy.append((end_time, room))
        busy = new_busy
        heapq.heapify(busy)

        if available:
            room = heapq.heappop(available)
            heapq.heappush(busy, (end, room))
        else:
            earliest_end, room = heapq.heappop(busy)
            heapq.heappush(busy, (earliest_end + duration, room))
        count[room] += 1

    best = 0
    for i in range(1, n):
        if count[i] > count[best]:
            best = i
    return best


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def mostBooked(n, meetings):
    """
    THE ONE TO MEMORIZE.

    available = min-heap of room indices.
    busy = min-heap of (end_time, room).
    count = [0] * n.

    For each meeting [start, end]:
      1. Pop busy entries with end_time <= start, push room to available.
      2. If available: pop smallest room, push (end, room) to busy.
      3. Else: pop (end_time, room) from busy, push (end_time + dur, room).
      4. count[room] += 1.

    Return argmax(count); ties broken by smallest index.

    Time:  O(m log n) for m meetings.
    Space: O(n).
    """
    available = list(range(n))
    heapq.heapify(available)
    busy = []  # (end_time, room)
    count = [0] * n

    for start, end in meetings:
        duration = end - start
        while busy and busy[0][0] <= start:
            _, room = heapq.heappop(busy)
            heapq.heappush(available, room)
        if available:
            room = heapq.heappop(available)
            heapq.heappush(busy, (end, room))
        else:
            earliest_end, room = heapq.heappop(busy)
            heapq.heappush(busy, (earliest_end + duration, room))
        count[room] += 1

    best = 0
    for i in range(1, n):
        if count[i] > count[best]:
            best = i
    return best


# =============================================================================
# TEST
# =============================================================================
def run_tests():
    implementations = [
        ("Way 1: Two heaps (BEST)", most_booked_1),
        ("Way 2: Two heaps explicit", most_booked_2),
        ("Way 3: Counter + argmax", most_booked_3),
        ("Way 4: Brute state", most_booked_4),
        ("Way 5: Class wrapper", most_booked_5),
        ("Way 6: Sort meetings", most_booked_6),
        ("Way 7: heapreplace", most_booked_7),
        ("Way 8: Sorted list avail", most_booked_8),
        ("Way 9: Filter busy", most_booked_9),
        ("Way 10: Final cleanest", mostBooked),
    ]

    test_cases = [
        # (n, meetings, expected)
        (2, [[0, 10], [1, 5], [2, 7], [3, 4]], 0),
        (3, [[1, 20], [2, 10], [3, 5], [4, 9], [6, 8]], 1),
        (4, [[0, 5], [0, 5], [0, 5], [0, 5]], 0),  # all same time; room 0 always chosen
        (1, [[0, 1], [1, 2], [2, 3]], 0),
        (3, [[0, 10], [1, 5], [2, 7]], 0),  # only room 0 used
        (2, [[1, 4], [4, 5]], 0),
        (3, [[0, 1], [0, 1], [0, 1], [1, 2], [1, 2]], 0),
        (4, [[18, 19], [3, 12], [17, 19], [2, 13], [7, 10]], 1),  # LC example (process in given order)
    ]

    print("=" * 70)
    print("MEETING ROOMS III - 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for n, meetings, expected in test_cases:
            try:
                # Deep copy to avoid mutation
                meetings_copy = [list(m) for m in meetings]
                result = fn(n, meetings_copy)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] n={n}, meetings={meetings}, expected={expected}, got={result}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}] n={n}, meetings={meetings}: {e}")
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
