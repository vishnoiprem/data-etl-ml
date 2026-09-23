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

# sortedcontainers is an optional dep; import lazily inside L2.
try:
    from sortedcontainers import SortedList  # type: ignore
    _HAS_SORTED_LIST = True
except ImportError:  # pragma: no cover
    SortedList = None  # type: ignore
    _HAS_SORTED_LIST = False


@dataclass
class Meeting:
    start: int
    end: int
    people: int


# ----------------------------------------------------------------------
# L0 — Easy / brute force: scan every integer instant between the
# earliest start and the latest end.
# How to think: "For every instant t, sum people whose start <= t < end.
# O(n · range). Only viable for tiny ranges; never ship this."
# ----------------------------------------------------------------------
def max_attendees_l0(meetings: list[Meeting]) -> int:
    if not meetings:
        return 0
    lo = min(m.start for m in meetings)
    hi = max(m.end for m in meetings)
    best = 0
    for t in range(lo, hi):
        s = sum(m.people for m in meetings if m.start <= t < m.end)
        if s > best:
            best = s
    return best


# ----------------------------------------------------------------------
# L1 — Medium / interview-canonical: sweep line.
# How to think: "Two events per meeting, sort, sweep. End events first
# on tie — that's the classic bug to call out loud."
# ----------------------------------------------------------------------
def max_attendees(meetings: list[Meeting]) -> int:
    """Return the max total attendees at any instant across all meetings."""
    if not meetings:
        return 0
    # Event = (time, delta). End events use a smaller delta so they
    # sort BEFORE start events at the same time (no double-counting).
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


# ----------------------------------------------------------------------
# L2 — Hard / streaming: SortedList keyed by end time. Add on start,
# remove on end, peak over the running sum.
# How to think: "If meetings arrive as a stream and you can't fit all
# events in memory at once, you need a structure that supports
# add/remove-by-key in O(log n). SortedList does that. Mention this
# only if the interviewer asks about streaming or memory."
# ----------------------------------------------------------------------
def max_attendees_l2(meetings: list[Meeting]) -> int:
    if not meetings:
        return 0
    if not _HAS_SORTED_LIST:
        # Fall back to the L1 sweep-line implementation if the optional
        # dependency isn't installed. Same answer, different shape.
        return max_attendees(meetings)
    active = SortedList()                    # entries: (end, people)
    peak = 0
    for m in sorted(meetings, key=lambda m: m.start):
        # Remove meetings that ended at or before this start
        while active and active[0][0] <= m.start:
            active.pop(0)
        active.add((m.end, m.people))
        current = sum(p for _, p in active)
        if current > peak:
            peak = current
    return peak


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
    samples = [
        ([Meeting(0, 10, 3), Meeting(5, 15, 4), Meeting(10, 20, 2)], 7),
        ([Meeting(0, 10, 1), Meeting(0, 10, 1), Meeting(0, 10, 1)], 3),
        ([Meeting(0, 5, 1), Meeting(5, 10, 1)], 1),
        ([Meeting(0, 5, 42)], 42),
        ([], 0),
    ]
    for ms, expected in samples:
        assert max_attendees_l0(ms) == expected, ms
        assert max_attendees(ms) == expected, ms
        assert max_attendees_l2(ms) == expected, ms
    print("All tests passed for max_attendees (L0 + L1 + L2).")
