"""
Problem 10 (Medium) — How many meetings can occur at the same time?
https://algo.monster/liteproblems/253
https://neetcode.io/problems/meeting-schedule-ii/solution


A variant of Problem 4: given meetings with start and end times (no
attendees), return the maximum NUMBER of meetings that overlap at any
instant. This is LeetCode 253 (Meeting Rooms II).

Examples
--------
>>> max_overlapping([(0, 10), (5, 15), (10, 20)])
2
>>> max_overlapping([(0, 30), (5, 10), (15, 20)])
2
>>> max_overlapping([])
0
>>> max_overlapping([(0, 5)])
1

How to think (interview script)
------------------------------
"Classic 'Meeting Rooms II'. Two solutions:

  A) Sweep line (used in problem 4). Same code, but each meeting is
     +1 at start and -1 at end. Best = max running sum. O(n log n).

  B) Min-heap of end times. Sort meetings by start; for each meeting,
     pop meetings that have ended (end <= current_start), push the
     current end. Max heap size = answer. O(n log n).

For Python clarity I'll show sweep line. The MIN-HEAP solution is also
fine and is the canonical LeetCode answer; mention it as the
alternative."

Complexity: O(n log n) time, O(n) extra space.

Follow-ups
----------
- "How many ROOMS do we need?"
  Same answer — that's what Meeting Rooms II literally asks.
- "Can you do it in O(n) time?"
  Yes, if end times are bounded or we can bucket-sort.
- "How would you do it streaming?"
  Maintain a sorted container (TreeMap / SortedList) of end times;
  increment on start, decrement on end.
"""

from typing import List, Tuple


def max_overlapping(meetings: List[Tuple[int, int]]) -> int:
    """Return the maximum number of meetings overlapping at any instant."""
    if not meetings:
        return 0
    events: list[tuple[int, int]] = []
    for s, e in meetings:
        if e < s:
            continue
        events.append((s, +1))
        events.append((e, -1))
    # End events first on ties — otherwise a meeting ending at t=10
    # would briefly count alongside one starting at t=10.
    events.sort(key=lambda ev: (ev[0], ev[1]))
    running = 0
    best = 0
    for _, delta in events:
        running += delta
        if running > best:
            best = running
    return best


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
    # All overlap
    assert max_overlapping([(0, 10), (0, 10), (0, 10)]) == 3
    # Touching at boundary — t=10 is end of first, start of second
    assert max_overlapping([(0, 10), (10, 20)]) == 1
    # Triple overlap: [15,20] has all three meetings active
    assert max_overlapping([(0, 100), (10, 20), (15, 30)]) == 3
    # No triple overlap (each small meets only the long; never all 3)
    assert max_overlapping([(0, 100), (10, 20), (30, 40)]) == 2
    print("All tests passed for max_overlapping.")
