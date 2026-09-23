"""
Interval List Intersections - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/interval-list-intersections

Given two lists of disjoint, sorted intervals, return the intersection of
the two lists.

KEY INSIGHT:
Two pointers. For each pair of intervals, the intersection is
[max(a.start, b.start), min(a.end, b.end)]. If start <= end, it's a valid
intersection. Advance the pointer with the smaller end.

Examples:
    A = [[0,2],[5,10],[13,23],[24,25]], B = [[1,5],[8,12],[15,24],[25,26]]
    -> [[1,2],[5,5],[8,10],[15,23],[24,24],[25,25]]

Constraints:
- 0 <= listA.length, listB.length <= 10^4
- 0 <= start <= end <= 10^9
"""

import copy
import sys

sys.setrecursionlimit(100000)


def _intervals_equal(a, b):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if len(a) != len(b):
        return False
    return all(a[i] == b[i] for i in range(len(a)))


def _intersect(a, b):
    """Return intersection of two intervals or None."""
    s = max(a[0], b[0])
    e = min(a[1], b[1])
    if s <= e:
        return [s, e]
    return None


# ============================================================
# Way 1: Two-pointer, advance smaller end (BEST - Memorize!)
# ============================================================
def interval_intersection_1(A, B):
    """Walk both lists with two pointers."""
    out = []
    i = j = 0
    while i < len(A) and j < len(B):
        a, b = A[i], B[j]
        s = max(a[0], b[0])
        e = min(a[1], b[1])
        if s <= e:
            out.append([s, e])
        # Advance the pointer with the smaller end
        if a[1] < b[1]:
            i += 1
        elif b[1] < a[1]:
            j += 1
        else:
            i += 1
            j += 1
    return out


# ============================================================
# Way 2: Helper-based
# ============================================================
def interval_intersection_2(A, B):
    """Same as Way 1 but with explicit _intersect helper."""
    out = []
    i = j = 0
    while i < len(A) and j < len(B):
        inter = _intersect(A[i], B[j])
        if inter:
            out.append(inter)
        if A[i][1] < B[j][1]:
            i += 1
        elif B[j][1] < A[i][1]:
            j += 1
        else:
            i += 1
            j += 1
    return out


# ============================================================
# Way 3: For each in A, scan B
# ============================================================
def interval_intersection_3(A, B):
    """For each interval in A, find intersections in B."""
    out = []
    j = 0
    for a in A:
        while j < len(B) and B[j][1] < a[0]:
            j += 1
        k = j
        while k < len(B) and B[k][0] <= a[1]:
            inter = _intersect(a, B[k])
            if inter:
                out.append(inter)
            k += 1
        # Don't move j backward if a[1] > B[j][1]
    return out


# ============================================================
# Way 4: For each in B, scan A
# ============================================================
def interval_intersection_4(A, B):
    """Symmetric: for each in B, find in A."""
    out = []
    i = 0
    for b in B:
        while i < len(A) and A[i][1] < b[0]:
            i += 1
        k = i
        while k < len(A) and A[k][0] <= b[1]:
            inter = _intersect(A[k], b)
            if inter:
                out.append(inter)
            k += 1
    return out


# ============================================================
# Way 5: Recursive
# ============================================================
def interval_intersection_5(A, B):
    """Recursive two-pointer."""
    out = []

    def helper(i, j):
        if i >= len(A) or j >= len(B):
            return
        a, b = A[i], B[j]
        s = max(a[0], b[0])
        e = min(a[1], b[1])
        if s <= e:
            out.append([s, e])
        if a[1] < b[1]:
            helper(i + 1, j)
        elif b[1] < a[1]:
            helper(i, j + 1)
        else:
            helper(i + 1, j + 1)

    helper(0, 0)
    return out


# ============================================================
# Way 6: Min-end approach (whichever ends first, advance)
# ============================================================
def interval_intersection_6(A, B):
    """Same logic as Way 1, named differently."""
    out = []
    i = j = 0
    while i < len(A) and j < len(B):
        s = max(A[i][0], B[j][0])
        e = min(A[i][1], B[j][1])
        if s <= e:
            out.append([s, e])
        if A[i][1] <= B[j][1]:
            i += 1
        else:
            j += 1
    return out


# ============================================================
# Way 7: Class-based
# ============================================================
class IntervalIntersector_7:
    def __init__(self, A, B):
        self.A = A
        self.B = B

    def intersect(self):
        out = []
        i = j = 0
        while i < len(self.A) and j < len(self.B):
            a, b = self.A[i], self.B[j]
            s = max(a[0], b[0])
            e = min(a[1], b[1])
            if s <= e:
                out.append([s, e])
            if a[1] < b[1]:
                i += 1
            elif b[1] < a[1]:
                j += 1
            else:
                i += 1
                j += 1
        return out


def interval_intersection_7(A, B):
    return IntervalIntersector_7(A, B).intersect()


# ============================================================
# Way 8: Walk with "always advance the one ending first"
# ============================================================
def interval_intersection_8(A, B):
    """Advance whichever ends first, taking intersection if any."""
    out = []
    i = j = 0
    while i < len(A) and j < len(B):
        # Compute intersection
        s = max(A[i][0], B[j][0])
        e = min(A[i][1], B[j][1])
        if s <= e:
            out.append([s, e])
        # Advance whichever ends first
        if A[i][1] < B[j][1]:
            i += 1
        elif B[j][1] < A[i][1]:
            j += 1
        else:
            i += 1
            j += 1
    return out


# ============================================================
# Way 9: Use index pointers directly
# ============================================================
def interval_intersection_9(A, B):
    """Iterative with explicit index comparisons."""
    if not A or not B:
        return []
    out = []
    i = 0
    j = 0
    while i < len(A) and j < len(B):
        if A[i][1] < B[j][0]:  # a ends before b starts
            i += 1
        elif B[j][1] < A[i][0]:  # b ends before a starts
            j += 1
        else:
            # overlap
            out.append([max(A[i][0], B[j][0]), min(A[i][1], B[j][1])])
            if A[i][1] < B[j][1]:
                i += 1
            elif B[j][1] < A[i][1]:
                j += 1
            else:
                i += 1
                j += 1
    return out


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def interval_intersection_10(A, B):
    """
    THE ONE TO MEMORIZE.

    1. i = j = 0.
    2. While i < len(A) and j < len(B):
       a, b = A[i], B[j].
       s, e = max(a.start, b.start), min(a.end, b.end).
       If s <= e: add [s, e].
       Advance the pointer with the smaller end (or both if equal).

    Time:  O(m + n)
    Space: O(m + n) for output.
    """
    out = []
    i = j = 0
    while i < len(A) and j < len(B):
        a, b = A[i], B[j]
        s = max(a[0], b[0])
        e = min(a[1], b[1])
        if s <= e:
            out.append([s, e])
        if a[1] < b[1]:
            i += 1
        elif b[1] < a[1]:
            j += 1
        else:
            i += 1
            j += 1
    return out


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the intersection of two lists of disjoint, sorted intervals."

Key Insight:
"Use two pointers. For each pair of intervals, compute the intersection
[max(a.start, b.start), min(a.end, b.end)]. If start <= end, it's valid.
Advance the pointer whose interval ends first (or both if equal)."

Algorithm:
1. i = j = 0.
2. While i < len(A) and j < len(B):
   s = max(A[i].start, B[j].start).
   e = min(A[i].end, B[j].end).
   If s <= e: out.append([s, e]).
   If A[i].end < B[j].end: i += 1.
   Else if B[j].end < A[i].end: j += 1.
   Else: i += 1, j += 1.

Edge Cases:
- Either list empty: return [].
- No overlap: return [].
- One fully contains another: return the contained.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| 2-pointer | O(m+n) | O(k)   |
| For-each  | O(m+n) | O(k)   |
+-----------+--------+--------+

KEY TRICK:
Advance the pointer with the smaller end. Why? That interval can't
intersect with any later interval in the other list (because the other
intervals start at or after their previous end, which is >= the smaller
end). So the smaller-ending one is "done."

RELATED PROBLEMS:
- Merge Intervals (LC 56).
- Insert Interval (LC 57).
- Meeting Rooms II (LC 253).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([[0, 2], [5, 10], [13, 23], [24, 25]], [[1, 5], [8, 12], [15, 24], [25, 26]],
         [[1, 2], [5, 5], [8, 10], [15, 23], [24, 24], [25, 25]], "Standard LC986"),
        ([], [[1, 2]], [], "Empty A"),
        ([[1, 2]], [], [], "Empty B"),
        ([[1, 5]], [[3, 7]], [[3, 5]], "Simple overlap"),
        ([[1, 5]], [[6, 10]], [], "No overlap"),
        ([[1, 5]], [[2, 4]], [[2, 4]], "B inside A"),
        ([[1, 2], [3, 4]], [[1, 4]], [[1, 2], [3, 4]], "A inside B"),
    ]

    implementations = [
        ("Way 1: Two-pointer (BEST)", interval_intersection_1),
        ("Way 2: Helper-based", interval_intersection_2),
        ("Way 3: For each in A", interval_intersection_3),
        ("Way 4: For each in B", interval_intersection_4),
        ("Way 5: Recursive", interval_intersection_5),
        ("Way 6: Min-end", interval_intersection_6),
        ("Way 7: Class-based", interval_intersection_7),
        ("Way 8: Advance first-end", interval_intersection_8),
        ("Way 9: Explicit indices", interval_intersection_9),
        ("Way 10: Final cleanest", interval_intersection_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for A, B, expected, desc in test_cases:
            try:
                a_copy = copy.deepcopy(A)
                b_copy = copy.deepcopy(B)
                result = fn(a_copy, b_copy)
                if _intervals_equal(result, expected):
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: expected={expected} got={result}")
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
