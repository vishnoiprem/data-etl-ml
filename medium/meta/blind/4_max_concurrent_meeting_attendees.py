"""
Problem 4 (Medium) — Max number of people in meetings at any instant

You have a list of data classes representing meetings, each with a
start, end, and people count. Meetings can overlap. Return the maximum
TOTAL number of people that were in a meeting at any single instant.

Examples
--------
>>> m1 = Meeting(0, 10, 3)
>>> m2 = Meeting(5, 15, 4)
>>> m3 = Meeting(10, 20, 2)
>>> max_attendees([m1, m2, m3])
7

How to think (interview script)
------------------------------
"The LeetCode hint in the Blind post says 'meeting rooms I and II'. This
is the 'Meeting Rooms II' question with attendees instead of rooms.

Sweep-line: convert each meeting to a (+people) event at start and a
(-people) event at end. Sort events by time. Ties: end events BEFORE
start events, so a meeting ending at t=10 doesn't overlap with one
starting at t=10.

Running total: best = max(running). This is O(n log n).

The reason end events come first on ties is a CLASSIC bug — mention
this in the interview to show you know it."

Complexity: O(n log n) time, O(n) extra space for events.

Follow-ups
----------
- "What if meetings are inclusive on both ends?"
  Same logic; off-by-one is a unit-test problem.
- "How would you do it in SQL?"
  Build an event table, then a running sum via window function.
- "How would you do it streaming?"
  Use a sorted container (TreeMap) keyed by end time; add attendees at
  start, remove at end.
"""

from dataclasses import dataclass


@dataclass
class Meeting:
    start: int
    end: int
    people: int


def max_attendees(meetings: list[Meeting]) -> int:
    """Return the max total attendees at any instant across all meetings."""
    if not meetings:
        return 0
    # Event = (time, delta). End events use -inf-priority so they sort
    # BEFORE start events at the same time (no double-counting).
    events: list[tuple[int, int]] = []
    for m in meetings:
        if m.end < m.start:
            continue  # invalid; skip
        events.append((m.start, +m.people))
        events.append((m.end,   -m.people))
    # Sort: by time; on tie, end (-delta) before start (+delta)
    events.sort(key=lambda e: (e[0], e[1]))

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
    # All-overlap sanity
    assert max_attendees([Meeting(0, 10, 1), Meeting(0, 10, 1), Meeting(0, 10, 1)]) == 3
    # No overlap
    assert max_attendees([Meeting(0, 5, 1), Meeting(5, 10, 1)]) == 1
    # Single meeting
    assert max_attendees([Meeting(0, 5, 42)]) == 42
    # Empty
    assert max_attendees([]) == 0
    print("All tests passed for max_attendees.")
