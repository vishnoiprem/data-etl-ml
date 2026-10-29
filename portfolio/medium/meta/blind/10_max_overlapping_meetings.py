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

import heapq
import itertools
from collections import Counter
from typing import List, Tuple

# sortedcontainers is an optional dep; import lazily inside L8 only.
try:
    from sortedcontainers import SortedList  # type: ignore
    _HAS_SORTED_LIST = True
except ImportError:  # pragma: no cover
    SortedList = None  # type: ignore
    _HAS_SORTED_LIST = False


# ----------------------------------------------------------------------
# L0 — Easy / brute force: per-instant scan.
# How to think: "For every integer instant t in [lo, hi), count how
# many meetings have start <= t < end. The max of those counts is the
# answer. O(n · range). Start here to show the answer, then improve."
# ----------------------------------------------------------------------
def max_overlapping_l0(meetings: List[Tuple[int, int]]) -> int:
    if not meetings:
        return 0
    best = 0
    # True brute force: every (meeting, instant) pair.
    lo = min(s for s, _ in meetings)
    hi = max(e for _, e in meetings)
    for t in range(lo, hi):
        c = sum(1 for s, e in meetings if s <= t < e)
        if c > best:
            best = c
    return best


# ----------------------------------------------------------------------
# L1 — Medium / interview-canonical: sweep line.
# How to think: "Two events per meeting, sweep. The 'end before start
# on tie' rule is the bug to call out loud."
# ----------------------------------------------------------------------
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


# ----------------------------------------------------------------------
# L2 — Hard / min-heap (LeetCode-canonical).
# How to think: "Sort by start; keep a heap of active end times; pop
# expired meetings; push current end. Heap size = rooms needed.
# Same complexity, more explicit 'active meetings' set — easier to
# extend for follow-ups (which meeting overlaps which)."
# ----------------------------------------------------------------------
def max_overlapping_l2(meetings: List[Tuple[int, int]]) -> int:
    if not meetings:
        return 0
    ends: list[int] = []
    best = 0
    # Zero-length / invalid meetings occupy no time — skip (matches L1).
    for s, e in sorted(m for m in meetings if m[1] > m[0]):
        # Release meetings that ended at or before this start
        while ends and ends[0] <= s:
            heapq.heappop(ends)
        heapq.heappush(ends, e)
        if len(ends) > best:
            best = len(ends)
    return best


# ----------------------------------------------------------------------
# L3 — Two pointers on sorted starts and ends.
# How to think: "Split meetings into two sorted lists: all start
# times and all end times. Walk both lists with pointers. When the
# next start is strictly less than the next end, a new meeting opens
# before the earliest one closes — count++. Otherwise a room frees up
# — count--. The peak of count is the answer. Strict-less is what
# enforces 'end before start on tie'."
# ----------------------------------------------------------------------
def max_overlapping_l3(meetings: List[Tuple[int, int]]) -> int:
    """Two-pointer variant on sorted starts and sorted ends."""
    if not meetings:
        return 0
    # Zero-length / invalid meetings would push the end pointer past the
    # list (IndexError) — drop them first, matching L1's answer.
    valid = [(s, e) for s, e in meetings if e > s]
    starts = sorted(s for s, _ in valid)
    ends = sorted(e for _, e in valid)
    s = e = 0
    count = best = 0
    while s < len(starts):
        if starts[s] < ends[e]:
            count += 1
            if count > best:
                best = count
            s += 1
        else:
            count -= 1
            e += 1
    return best


# ----------------------------------------------------------------------
# L4 — Sweep line with numeric tie encoding.
# How to think: "Same as L1, but instead of sorting events by
# (time, delta) and relying on -1 < +1, encode ends as (time, 0) and
# starts as (time, 1). Then a single sort by (time, type) puts ends
# first. Same O(n log n), different way to express the same rule."
# ----------------------------------------------------------------------
def max_overlapping_l4(meetings: List[Tuple[int, int]]) -> int:
    """Sweep line with ends encoded as 0 and starts as 1."""
    if not meetings:
        return 0
    events: list[tuple[int, int]] = []
    for s, e in meetings:
        if e < s:
            continue
        events.append((e, 0))  # end first
        events.append((s, 1))  # start second
    events.sort()
    running = best = 0
    for _, kind in events:
        running += 1 if kind == 1 else -1
        if running > best:
            best = running
    return best


# ----------------------------------------------------------------------
# L5 — Counter-based sweep on sparse times.
# How to think: "When the time axis is sparse, we can group events
# per-time in a Counter and sweep over sorted keys. Same algorithm as
# L1 but with O(U) extra space where U = unique times instead of
# O(2n)."
# ----------------------------------------------------------------------
def max_overlapping_l5(meetings: List[Tuple[int, int]]) -> int:
    """Counter-based sweep — sparse-time friendly."""
    if not meetings:
        return 0
    delta: Counter = Counter()
    for s, e in meetings:
        if e < s:
            continue
        delta[s] += 1
        delta[e] -= 1
    running = best = 0
    for _, d in sorted(delta.items()):
        running += d
        if running > best:
            best = running
    return best


# ----------------------------------------------------------------------
# L6 — itertools.accumulate over a sorted event list.
# How to think: "Build the (time, delta) list as in L1, sort it, and
# let itertools.accumulate do the running-sum bookkeeping. The max of
# the resulting iterator is the answer. Functional / one-liner flavor
# — show off Python fluency."
# ----------------------------------------------------------------------
def max_overlapping_l6(meetings: List[Tuple[int, int]]) -> int:
    """Functional style via itertools.accumulate."""
    if not meetings:
        return 0
    events: list[tuple[int, int]] = []
    for s, e in meetings:
        if e < s:
            continue
        events.append((s, 1))
        events.append((e, -1))
    events.sort(key=lambda ev: (ev[0], ev[1]))
    return max(itertools.accumulate(d for _, d in events), default=0)


# ----------------------------------------------------------------------
# L7 — Coordinate compression, then linear scan.
# How to think: "If times are bounded integers, compress all distinct
# times to [0..U), build a dense array of length U, do a linear pass
# applying +1/-1, and return the peak. The compression itself sorts,
# so it is still O(n log n); if times are small bounded integers you can
# skip compression and index directly for true O(n + T)."
# ----------------------------------------------------------------------
def max_overlapping_l7(meetings: List[Tuple[int, int]]) -> int:
    """Coordinate-compressed linear scan."""
    if not meetings:
        return 0
    times = sorted({t for s, e in meetings for t in (s, e) if e >= s})
    if not times:
        return 0
    idx = {t: i for i, t in enumerate(times)}
    arr = [0] * len(times)
    for s, e in meetings:
        if e < s:
            continue
        arr[idx[s]] += 1
        arr[idx[e]] -= 1
    running = best = 0
    for v in arr:
        running += v
        if running > best:
            best = running
    return best


# ----------------------------------------------------------------------
# L8 — SortedList (sortedcontainers) of active end times.
# How to think: "Sort meetings by start. For each meeting, drop every
# end time that is <= current start (those meetings have finished),
# then push the current end. The list size is the number of currently
# overlapping meetings. Same complexity as L2, but uses an ordered
# multiset (optional dep) instead of a heap."
# ----------------------------------------------------------------------
def max_overlapping_l8(meetings: List[Tuple[int, int]]) -> int:
    """Active-end-time multiset via SortedList (optional dep)."""
    if not meetings:
        return 0
    if not _HAS_SORTED_LIST:
        # Fall back to L2's heap when sortedcontainers is unavailable.
        return max_overlapping_l2(meetings)
    ends = SortedList()
    best = 0
    for s, e in sorted(m for m in meetings if m[1] > m[0]):
        # Drop end times that are <= s (those meetings have ended).
        while ends and ends[0] <= s:
            ends.pop(0)
        ends.add(e)
        if len(ends) > best:
            best = len(ends)
    return best


# ----------------------------------------------------------------------
# L9 — Fenwick tree (binary indexed tree) on compressed times.
# How to think: "Coordinate-compress times to indices 0..U-1. For each
# meeting, fenwick.update(start_idx, +1) and fenwick.update(end_idx,
# -1). After all meetings, walk indices 0..U-1 taking a prefix sum
# and return the max. O(n log U). Same idea as L7 but using a
# Fenwick tree instead of a flat array — useful when U is huge and we
# only need a subset of indices touched."
# ----------------------------------------------------------------------
def max_overlapping_l9(meetings: List[Tuple[int, int]]) -> int:
    """Fenwick tree on coordinate-compressed times."""
    if not meetings:
        return 0
    pairs = [(s, e) for s, e in meetings if e >= s]
    if not pairs:
        return 0
    times = sorted({t for s, e in pairs for t in (s, e)})
    idx = {t: i + 1 for i, t in enumerate(times)}  # Fenwick is 1-indexed
    n = len(times) + 1
    bit = [0] * n

    def update(i: int, delta: int) -> None:
        while i < n:
            bit[i] += delta
            i += i & -i

    def query(i: int) -> int:
        s = 0
        while i > 0:
            s += bit[i]
            i -= i & -i
        return s

    for s, e in pairs:
        update(idx[s], 1)
        update(idx[e], -1)

    best = 0
    for i in range(1, n):
        v = query(i)
        if v > best:
            best = v
    return best


# ----------------------------------------------------------------------
# L10 — Segment tree with lazy range-add and point-query for max.
# How to think: "Coordinate-compress times, build a segment tree over
# indices 0..U-1. For each meeting, do range_add(start_idx, end_idx,
# +1). After all meetings, the maximum value stored in any node is the
# answer. This is the most 'textbook' formulation: a sweep without
# sorting, just range updates and a max tree."
# ----------------------------------------------------------------------
def max_overlapping_l10(meetings: List[Tuple[int, int]]) -> int:
    """Segment tree with range-add / max-query on compressed times."""
    if not meetings:
        return 0
    pairs = [(s, e) for s, e in meetings if e >= s]
    if not pairs:
        return 0
    times = sorted({t for s, e in pairs for t in (s, e)})
    if not times:
        return 0
    u = len(times)
    idx = {t: i for i, t in enumerate(times)}
    size = 4 * u
    tree = [0] * size
    lazy = [0] * size

    def _apply(node: int, value: int) -> None:
        tree[node] += value
        lazy[node] += value

    def _push(node: int) -> None:
        if lazy[node]:
            _apply(node * 2, lazy[node])
            _apply(node * 2 + 1, lazy[node])
            lazy[node] = 0

    def update(node: int, lo: int, hi: int, ql: int, qh: int, val: int) -> None:
        if ql >= hi or qh <= lo:
            return
        if ql <= lo and hi <= qh:
            _apply(node, val)
            return
        _push(node)
        mid = (lo + hi) // 2
        update(node * 2, lo, mid, ql, qh, val)
        update(node * 2 + 1, mid, hi, ql, qh, val)
        tree[node] = max(tree[node * 2], tree[node * 2 + 1])

    for s, e in pairs:
        update(1, 0, u, idx[s], idx[e], 1)

    # After all updates, the max anywhere in the tree is at node 1.
    return tree[1]


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
    samples = [
        ([(0, 10), (5, 15), (10, 20)], 2),
        ([(0, 30), (5, 10), (15, 20)], 2),
        ([], 0),
        ([(0, 5)], 1),
        ([(0, 10), (0, 10), (0, 10)], 3),
        ([(0, 10), (10, 20)], 1),
        ([(0, 100), (10, 20), (15, 30)], 3),
        ([(0, 100), (10, 20), (30, 40)], 2),
        # All four overlap during [4, 5) — stresses L3 (two-pointer)
        # and L9/L10 (Fenwick / segment tree) with many distinct times.
        ([(1, 5), (3, 7), (2, 6), (4, 8)], 4),
        # Extreme single meeting — stresses L0 (per-instant scan) and
        # L7 (coordinate-compressed array length).
        ([(0, 1_000_000)], 1),
        # Zero-length and invalid (end < start) meetings occupy no time.
        ([(5, 5)], 0),
        ([(5, 3)], 0),
        ([(0, 10), (5, 5), (5, 3)], 1),
    ]
    implementations = [
        max_overlapping_l0,
        max_overlapping,
        max_overlapping_l2,
        max_overlapping_l3,
        max_overlapping_l4,
        max_overlapping_l5,
        max_overlapping_l6,
        max_overlapping_l7,
        max_overlapping_l8,
        max_overlapping_l9,
        max_overlapping_l10,
    ]
    for ms, expected in samples:
        for impl in implementations:
            assert impl(ms) == expected, (impl.__name__, ms, expected)
    print(f"All tests passed for max_overlapping ({len(implementations)} implementations, L0..L10).")
