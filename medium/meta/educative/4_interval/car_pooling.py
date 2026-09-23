"""
Car Pooling - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/car-pooling

Given a list of trips [passengers, start, end] and a car capacity, return
True if it's possible to fulfill all trips without exceeding capacity.

KEY INSIGHT:
Sweep line: at each start, +passengers; at each end, -passengers. Walk
through sorted events; track current passengers; if it ever exceeds
capacity, return False.

Examples:
    trips = [[2,1,5],[3,3,7]], capacity = 4 -> False (peak=5 at stop 3)
    trips = [[2,1,5],[3,3,7]], capacity = 5 -> True
    trips = [[2,1,5],[3,5,7]], capacity = 3 -> True (3 never overlap)

Constraints:
- 1 <= trips.length <= 1000
- 1 <= capacity <= 10^5
"""

import copy
import sys

sys.setrecursionlimit(100000)


def _eq(a, b):
    return a == b


# ============================================================
# Way 1: Sweep line (BEST - Memorize!)
# ============================================================
def car_pooling_1(trips, capacity):
    """Sweep line: at start add passengers, at end remove."""
    events = []
    for p, s, e in trips:
        events.append((s, p))
        events.append((e, -p))
    events.sort()
    cur = 0
    for _, delta in events:
        cur += delta
        if cur > capacity:
            return False
    return True


# ============================================================
# Way 2: Sort by start, accumulate, check at each step
# ============================================================
def car_pooling_2(trips, capacity):
    """Sort trips by start; track passengers on board."""
    trips.sort(key=lambda x: x[1])
    on_board = []  # list of [end, count]
    for p, s, e in trips:
        # Remove passengers whose trips ended before s
        on_board = [trip for trip in on_board if trip[0] > s]
        cur = sum(trip[1] for trip in on_board) + p
        if cur > capacity:
            return False
        on_board.append([e, p])
    return True


# ============================================================
# Way 3: Diff array (only for small max position)
# ============================================================
def car_pooling_3(trips, capacity):
    """Use diff array over position."""
    if not trips:
        return True
    max_pos = max(e for _, _, e in trips)
    diff = [0] * (max_pos + 2)
    for p, s, e in trips:
        diff[s] += p
        diff[e] -= p
    cur = 0
    for d in diff:
        cur += d
        if cur > capacity:
            return False
    return True


# ============================================================
# Way 4: Sort events by (pos, type) where drop happens before pickup at same pos
# ============================================================
def car_pooling_4(trips, capacity):
    """Drops before pickups at same position."""
    events = []
    for p, s, e in trips:
        events.append((s, 1, p))   # pickup
        events.append((e, -1, p))  # drop
    # Sort by position; at same position, drops first.
    events.sort(key=lambda x: (x[0], x[1]))
    cur = 0
    for _, sign, p in events:
        cur += sign * p
        if cur > capacity:
            return False
    return True


# ============================================================
# Way 5: Sort by end, sweep with running count
# ============================================================
def car_pooling_5(trips, capacity):
    """Sort trips by end; check max overlap."""
    # Actually need to think: not strictly sorted by end alone.
    # Use start-based sweep but sort trips by start.
    events = sorted([(s, p) for p, s, _ in trips] + [(e, -p) for p, _, e in trips])
    cur = 0
    for _, d in events:
        cur += d
        if cur > capacity:
            return False
    return True


# ============================================================
# Way 6: Heap-based
# ============================================================
def car_pooling_6(trips, capacity):
    """Use min-heap of end times."""
    import heapq
    trips = sorted(trips, key=lambda x: x[1])
    heap = []  # (end, passengers)
    cur = 0
    for p, s, e in trips:
        while heap and heap[0][0] <= s:
            _, p_drop = heapq.heappop(heap)
            cur -= p_drop
        cur += p
        if cur > capacity:
            return False
        heapq.heappush(heap, (e, p))
    return True


# ============================================================
# Way 7: Recursive
# ============================================================
def car_pooling_7(trips, capacity):
    """Recursive helper."""
    if not trips:
        return True

    def helper(idx, on_board):
        if idx >= len(trips):
            return True
        p, s, e = trips[idx]
        # Drop off passengers whose trips ended before s
        new_board = [(end, pn) for end, pn in on_board if end > s]
        if sum(pn for _, pn in new_board) + p > capacity:
            return False
        new_board.append((e, p))
        return helper(idx + 1, new_board)

    trips.sort(key=lambda x: x[1])
    return helper(0, [])


# ============================================================
# Way 8: Class-based
# ============================================================
class CarPooler_8:
    def __init__(self, capacity):
        self.capacity = capacity

    def can_fulfill(self, trips):
        return car_pooling_1(trips, self.capacity)


def car_pooling_8(trips, capacity):
    return CarPooler_8(capacity).can_fulfill(trips)


# ============================================================
# Way 9: Sort by (start asc, end asc) and simulate
# ============================================================
def car_pooling_9(trips, capacity):
    """Sort trips by start; use priority queue for end times."""
    import heapq
    trips = sorted(trips, key=lambda x: (x[1], x[2]))
    cur = 0
    end_heap = []
    for p, s, e in trips:
        # Drop off
        while end_heap and end_heap[0][0] <= s:
            _, pn = heapq.heappop(end_heap)
            cur -= pn
        cur += p
        if cur > capacity:
            return False
        heapq.heappush(end_heap, (e, p))
    return True


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def car_pooling_10(trips, capacity):
    """
    THE ONE TO MEMORIZE.

    1. For each trip, add event (start, +passengers) and (end, -passengers).
    2. Sort events by position.
    3. Walk; accumulate current passengers.
    4. If at any point passengers > capacity, return False.

    Time:  O(n log n)
    Space: O(n).
    """
    events = []
    for p, s, e in trips:
        events.append((s, p))
        events.append((e, -p))
    events.sort()
    cur = 0
    for _, delta in events:
        cur += delta
        if cur > capacity:
            return False
    return True


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to determine if all trips can be fulfilled without exceeding car
capacity. Each trip has passengers, start, and end."

Key Insight:
"Sweep line. At each pickup, add passengers. At each drop-off, remove.
Sort all events by position and walk; track current passengers on board.
If at any point it exceeds capacity, return False."

Algorithm:
1. Build events: (start, +passengers), (end, -passengers).
2. Sort by position.
3. cur = 0. For each event, update cur. If cur > capacity, return False.

Edge Cases:
- Empty trips: True.
- All trips fit: True.
- One trip exceeds capacity: False (but only if the entire capacity is hit).

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Sweep     | O(nlogn)| O(n)  |
| Diff array| O(M)   | O(M)   |
| Heap      | O(nlogn)| O(n)  |
+-----------+--------+--------+

KEY TRICK:
At position p with multiple events (e.g., one drop and one pickup), the
order matters. Standard convention: drops happen before pickups at the
same stop. With the simple `(s, +p), (e, -p)` approach, since drop happens
at `e` and pickup at next `s` (which is >= e), they're naturally ordered.

RELATED PROBLEMS:
- Meeting Rooms II (LC 253).
- Employee Free Time (LC 759).
- Task Scheduler (LC 621).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([[2, 1, 5], [3, 3, 7]], 4, False, "Standard LC1094 (False)"),
        ([[2, 1, 5], [3, 3, 7]], 5, True, "Same trips, more capacity"),
        ([[2, 1, 5], [3, 5, 7]], 3, True, "No overlap"),
        ([[3, 2, 8], [4, 4, 6]], 7, True, "Peak overlap (exactly 7)"),
        ([[3, 2, 8], [4, 4, 6]], 6, False, "Peak exceeds capacity"),
        ([], 1, True, "Empty"),
        ([[1, 1, 2], [2, 2, 3]], 3, True, "Sequential"),
        ([[10, 0, 10]], 5, False, "Single trip exceeds"),
    ]

    implementations = [
        ("Way 1: Sweep line (BEST)", car_pooling_1),
        ("Way 2: Sort + on_board list", car_pooling_2),
        ("Way 3: Diff array", car_pooling_3),
        ("Way 4: Drops first", car_pooling_4),
        ("Way 5: Sort + sweep", car_pooling_5),
        ("Way 6: Heap-based", car_pooling_6),
        ("Way 7: Recursive", car_pooling_7),
        ("Way 8: Class-based", car_pooling_8),
        ("Way 9: Sort + heap", car_pooling_9),
        ("Way 10: Final cleanest", car_pooling_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for inp, cap, expected, desc in test_cases:
            try:
                result = fn(copy.deepcopy(inp), cap)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: trips={inp} cap={cap} expected={expected} got={result}")
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
