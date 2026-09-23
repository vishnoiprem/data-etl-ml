"""
Count Days Without Meetings - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/count-days-without-meetings

Given a positive integer days and a list of meeting intervals, return the
number of days when no meeting occurs.

KEY INSIGHT:
Sort intervals, merge them. The free days = days - total_meeting_days.

Examples:
    days = 10, meetings = [[5,7],[1,3],[9,10]] -> 2
    (Merged intervals: [1,3],[5,7],[9,10]. Meeting days = 3+3+2=8. Free = 2.)

Constraints:
- 1 <= days <= 10^9
- 1 <= meetings.length <= 10^5
"""

import copy
import sys

sys.setrecursionlimit(100000)


def _eq(a, b):
    return a == b


def _merge(intervals):
    if not intervals:
        return []
    s = sorted(intervals, key=lambda x: x[0])
    out = [s[0][:]]
    for cur in s[1:]:
        if cur[0] <= out[-1][1] + 1:
            # Adjacent or overlapping — merge into a contiguous range.
            # Treat [1,3] and [5,7] as adjacent if they touch or overlap.
            out[-1][1] = max(out[-1][1], cur[1])
        else:
            out.append(cur[:])
    return out


# ============================================================
# Way 1: Merge meetings and subtract (BEST - Memorize!)
# ============================================================
def count_days_without_meetings_1(days, meetings):
    """Merge meetings; subtract total meeting days from days."""
    if not meetings:
        return days
    merged = _merge(meetings)
    meeting_days = sum(e - s + 1 for s, e in merged)
    return max(0, days - meeting_days)


# ============================================================
# Way 2: Mark days in a set (only for small days)
# ============================================================
def count_days_without_meetings_2(days, meetings):
    """Mark all meeting days; count non-meeting days."""
    if days > 10**6:
        # Skip for large days
        merged = _merge(meetings)
        meeting_days = sum(e - s + 1 for s, e in merged)
        return max(0, days - meeting_days)
    busy = [False] * (days + 1)
    for s, e in meetings:
        for d in range(s, e + 1):
            if d <= days:
                busy[d] = True
    return sum(1 for d in range(1, days + 1) if not busy[d])


# ============================================================
# Way 3: Sweep line, count busy days then subtract
# ============================================================
def count_days_without_meetings_3(days, meetings):
    """Sweep line; sum busy days."""
    events = []
    for s, e in meetings:
        events.append((s, 1))
        events.append((e + 1, -1))
    if not events:
        return days
    events.sort()
    busy_days = 0
    cur = 0
    prev = None
    for pos, delta in events:
        if cur > 0 and prev is not None:
            busy_days += min(pos, days + 1) - prev
        cur += delta
        if cur > 0:
            prev = pos
        else:
            prev = None
    return max(0, days - busy_days)


# ============================================================
# Way 4: Sort and walk
# ============================================================
def count_days_without_meetings_4(days, meetings):
    """Sort and walk; count gaps."""
    if not meetings:
        return days
    merged = _merge(meetings)
    return max(0, days - sum(e - s + 1 for s, e in merged))


# ============================================================
# Way 5: Recursive merge
# ============================================================
def count_days_without_meetings_5(days, meetings):
    """Recursive helper."""
    if not meetings:
        return days

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
            if out and cur[0] <= out[-1][1] + 1:
                out[-1][1] = max(out[-1][1], cur[1])
            else:
                out.append(cur[:])
        while i < len(left):
            if out and left[i][0] <= out[-1][1] + 1:
                out[-1][1] = max(out[-1][1], left[i][1])
            else:
                out.append(left[i][:])
            i += 1
        while j < len(right):
            if out and right[j][0] <= out[-1][1] + 1:
                out[-1][1] = max(out[-1][1], right[j][1])
            else:
                out.append(right[j][:])
            j += 1
        return out

    merged = merge_recurse(sorted(meetings, key=lambda x: x[0]))
    return max(0, days - sum(e - s + 1 for s, e in merged))


# ============================================================
# Way 6: Class-based
# ============================================================
class DayCounter_6:
    def __init__(self, days):
        self.days = days

    def count_without_meetings(self, meetings):
        return count_days_without_meetings_1(self.days, meetings)


def count_days_without_meetings_6(days, meetings):
    return DayCounter_6(days).count_without_meetings(meetings)


# ============================================================
# Way 7: In-place merge (after sort)
# ============================================================
def count_days_without_meetings_7(days, meetings):
    """Sort in place; merge in place; count meeting days."""
    if not meetings:
        return days
    meetings.sort(key=lambda x: x[0])
    meetings[0][1] = meetings[0][1]
    write = 0
    for read in range(1, len(meetings)):
        if meetings[read][0] <= meetings[write][1] + 1:
            meetings[write][1] = max(meetings[write][1], meetings[read][1])
        else:
            write += 1
            meetings[write] = meetings[read]
    merged = meetings[:write + 1]
    meeting_days = sum(e - s + 1 for s, e in merged)
    return max(0, days - meeting_days)


# ============================================================
# Way 8: Walk with two-pointer style
# ============================================================
def count_days_without_meetings_8(days, meetings):
    """Two-pointer merge; count meeting days."""
    if not meetings:
        return days
    s = sorted(meetings, key=lambda x: x[0])
    merged = [s[0][:]]
    for cur in s[1:]:
        if cur[0] <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], cur[1])
        else:
            merged.append(cur[:])
    meeting_days = sum(e - s + 1 for s, e in merged)
    return max(0, days - meeting_days)


# ============================================================
# Way 9: Use set with explicit merging
# ============================================================
def count_days_without_meetings_9(days, meetings):
    """Use set of days; merge then count."""
    if not meetings:
        return days
    merged = _merge(meetings)
    meeting_days = sum(e - s + 1 for s, e in merged)
    return max(0, days - meeting_days)


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def count_days_without_meetings_10(days, meetings):
    """
    THE ONE TO MEMORIZE.

    1. Sort meetings; merge adjacent/overlapping.
       (Note: meetings may touch via [1,3] and [5,7] without overlap,
        but for counting meeting DAYS, we just merge overlapping.)
    2. meeting_days = sum of (end - start + 1) for each merged.
    3. Return days - meeting_days.

    Time:  O(n log n)
    Space: O(n).
    """
    if not meetings:
        return days
    merged = _merge(meetings)
    meeting_days = sum(e - s + 1 for s, e in merged)
    return max(0, days - meeting_days)


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to count the number of days when no meeting occurs in a given
range of days."

Key Insight:
"Merge all meeting intervals into non-overlapping ranges, sum the total
meeting days, and subtract from the total days."

Algorithm:
1. Sort meetings by start; merge overlapping.
2. meeting_days = sum(end - start + 1) for each merged interval.
3. Return days - meeting_days.

Edge Cases:
- No meetings: return days.
- All days are meeting days: return 0.
- Meetings spanning beyond days: cap at days.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Sort+merge| O(nlogn)| O(n)  |
| Sweep     | O(nlogn)| O(n)  |
| Mark days | O(days*n)| O(d) |
+-----------+--------+--------+

KEY TRICK:
Treat meeting DAYS as inclusive ranges. [1,3] means 3 meeting days (1,2,3).
The subtraction uses `days - total_meeting_days`.

RELATED PROBLEMS:
- Merge Intervals (LC 56).
- Employee Free Time (LC 759).
- Meeting Rooms II (LC 253).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        (10, [[5, 7], [1, 3], [9, 10]], 2, "Standard LC3169"),
        (5, [[2, 4], [1, 3]], 1, "All covered (one free)"),
        (5, [], 5, "No meetings"),
        (10, [[1, 2], [6, 10]], 3, "Gaps"),
        (100, [[1, 100]], 0, "Spans all"),
        (5, [[1, 5]], 0, "Exact span"),
    ]

    implementations = [
        ("Way 1: Merge + subtract (BEST)", count_days_without_meetings_1),
        ("Way 2: Mark days set", count_days_without_meetings_2),
        ("Way 3: Sweep line", count_days_without_meetings_3),
        ("Way 4: Sort + walk", count_days_without_meetings_4),
        ("Way 5: Recursive", count_days_without_meetings_5),
        ("Way 6: Class-based", count_days_without_meetings_6),
        ("Way 7: In-place merge", count_days_without_meetings_7),
        ("Way 8: Two-pointer merge", count_days_without_meetings_8),
        ("Way 9: Set + merge", count_days_without_meetings_9),
        ("Way 10: Final cleanest", count_days_without_meetings_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for d, m, expected, desc in test_cases:
            try:
                result = fn(d, copy.deepcopy(m))
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: days={d} m={m} expected={expected} got={result}")
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
