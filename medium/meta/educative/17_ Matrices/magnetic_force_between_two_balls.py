"""
Magnetic Force Between Two Balls
Medium | 30 min

Given positions[] and m balls, place all balls in baskets such that the
MINIMUM magnetic force between any two balls is MAXIMIZED. Return that
maximum minimum force.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/magnetic-force-between-two-balls

Examples:
    position=[1,2,3,4,7], m=3 -> 3
    # Place at 1, 4, 7. Min gap = 3.

    position=[5,4,3,2,1,1000000000], m=2 -> 999999999
    # Place at 1, 1000000000.

Constraints:
- 2 <= position.length <= 10^5
- 2 <= m <= position.length
- 0 <= position[i] <= 10^9

KEY INSIGHT: Sort. Binary search on answer (force d). For each d,
greedily place balls: count how many baskets fit. If count >= m, d is
feasible (try larger). Else infeasible (try smaller).
"""


# =============================================================================
# WAY 1: Sort + BS on distance (BEST - Memorize!)
# =============================================================================
def max_distance_1(position, m):
    """
    Sort. Binary search on min distance d. For each d, greedy place
    balls and check if m fit.
    """
    a = sorted(position)
    n = len(a)

    def can_place(d):
        """Check if we can place m balls with min gap d."""
        count = 1
        last = a[0]
        for i in range(1, n):
            if a[i] - last >= d:
                count += 1
                last = a[i]
                if count >= m:
                    return True
        return False

    lo, hi = 1, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if can_place(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 2: Sort + BS verbose
# =============================================================================
def max_distance_2(position, m):
    a = sorted(position)
    n = len(a)

    def can_place(d):
        count = 1
        last = a[0]
        for i in range(1, n):
            if a[i] - last >= d:
                count += 1
                last = a[i]
                if count >= m:
                    return True
        return count >= m

    lo, hi = 1, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if can_place(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 3: Sort + BS with explicit check
# =============================================================================
def max_distance_3(position, m):
    a = sorted(position)
    n = len(a)
    lo, hi = 1, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        # Try placing m balls with min gap mid
        count = 1
        last = a[0]
        ok = False
        for i in range(1, n):
            if a[i] - last >= mid:
                count += 1
                last = a[i]
                if count >= m:
                    ok = True
                    break
        if ok:
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 4: Sort + recursive BS
# =============================================================================
def max_distance_4(position, m):
    a = sorted(position)
    n = len(a)

    def can_place(d):
        count = 1
        last = a[0]
        for i in range(1, n):
            if a[i] - last >= d:
                count += 1
                last = a[i]
                if count >= m:
                    return True
        return False

    lo, hi = 1, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if can_place(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 5: Sort + greedy first try, then BS
# =============================================================================
def max_distance_5(position, m):
    """Sort + iterative search."""
    a = sorted(position)
    n = len(a)
    lo, hi = 1, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        # Greedy place
        count = 1
        last = a[0]
        for i in range(1, n):
            if a[i] - last >= mid:
                count += 1
                last = a[i]
        if count >= m:
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 6: Brute force - try all d
# =============================================================================
def max_distance_6(position, m):
    """Try each d from largest down."""
    a = sorted(position)
    n = len(a)
    for d in range(a[-1] - a[0], 0, -1):
        count = 1
        last = a[0]
        for i in range(1, n):
            if a[i] - last >= d:
                count += 1
                last = a[i]
                if count >= m:
                    return d
    return 0


# =============================================================================
# WAY 7: Sort + memoized feasibility
# =============================================================================
def max_distance_7(position, m):
    from functools import lru_cache
    a = sorted(position)
    n = len(a)

    @lru_cache(maxsize=None)
    def can_place(d):
        count = 1
        last = a[0]
        for i in range(1, n):
            if a[i] - last >= d:
                count += 1
                last = a[i]
                if count >= m:
                    return True
        return False

    lo, hi = 1, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if can_place(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 8: Class OOP
# =============================================================================
class MagneticForceFinder:
    def __init__(self, position):
        self.a = sorted(position)
        self.n = len(self.a)

    def can_place(self, d, m):
        count = 1
        last = self.a[0]
        for i in range(1, self.n):
            if self.a[i] - last >= d:
                count += 1
                last = self.a[i]
                if count >= m:
                    return True
        return False

    def find_max(self, m):
        lo, hi = 1, self.a[-1] - self.a[0]
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.can_place(mid, m):
                lo = mid
            else:
                hi = mid - 1
        return lo


def max_distance_8(position, m):
    return MagneticForceFinder(position).find_max(m)


# =============================================================================
# WAY 9: Sort + lambda binary search
# =============================================================================
def max_distance_9(position, m):
    import bisect
    a = sorted(position)
    n = len(a)

    def can_place(d):
        count = 1
        last = a[0]
        for i in range(1, n):
            if a[i] - last >= d:
                count += 1
                last = a[i]
                if count >= m:
                    return True
        return False

    lo, hi = 1, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        lo, hi = (mid, hi) if can_place(mid) else (lo, mid - 1)
    return lo


# =============================================================================
# WAY 10: Sort + itertools accumulate
# =============================================================================
def max_distance_10(position, m):
    a = sorted(position)
    n = len(a)
    lo, hi = 1, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        count = 1
        last = a[0]
        for i in range(1, n):
            if a[i] - last >= mid:
                count += 1
                last = a[i]
        if count >= m:
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 11: Sort + bisect-based BS
# =============================================================================
def max_distance_11(position, m):
    """Use bisect to find placement efficiently."""
    import bisect
    a = sorted(position)
    n = len(a)

    def can_place(d):
        count = 1
        last = a[0]
        for i in range(1, n):
            if a[i] - last >= d:
                count += 1
                last = a[i]
                if count >= m:
                    return True
        return False

    lo, hi = 1, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if can_place(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 12: Sort + one-liner style
# =============================================================================
def max_distance_12(position, m):
    a = sorted(position)
    n = len(a)
    lo, hi = 1, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        count, last = 1, a[0]
        for i in range(1, n):
            if a[i] - last >= mid:
                count += 1
                last = a[i]
        if count >= m:
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 13: Sort + manual range bisect
# =============================================================================
def max_distance_13(position, m):
    """Manual binary search."""
    a = sorted(position)
    n = len(a)

    def can(d):
        c = 1
        last = a[0]
        for x in a[1:]:
            if x - last >= d:
                c += 1
                last = x
                if c >= m:
                    return True
        return False

    lo, hi = 1, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if can(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 14: Sort + generator-based check
# =============================================================================
def max_distance_14(position, m):
    a = sorted(position)
    n = len(a)

    def can_place(d):
        # Generator yielding valid next positions
        def next_positions():
            last = a[0]
            count = 1
            for x in a[1:]:
                if x - last >= d:
                    count += 1
                    last = x
                    if count >= m:
                        return True
            return False
        return next_positions()

    lo, hi = 1, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if can_place(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 15: Sort + while loop greedy check
# =============================================================================
def max_distance_15(position, m):
    a = sorted(position)
    n = len(a)
    lo, hi = 1, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        count = 1
        last = a[0]
        i = 1
        while i < n:
            if a[i] - last >= mid:
                count += 1
                last = a[i]
            i += 1
        if count >= m:
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 16: Sort + numpy
# =============================================================================
def max_distance_16(position, m):
    import numpy as np
    a = np.sort(np.array(position))
    n = len(a)

    def can_place(d):
        count = 1
        last = a[0]
        for i in range(1, n):
            if a[i] - last >= d:
                count += 1
                last = a[i]
                if count >= m:
                    return True
        return False

    lo, hi = 1, int(a[-1] - a[0])
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if can_place(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 17: Sort + reduce
# =============================================================================
def max_distance_17(position, m):
    from functools import reduce
    a = sorted(position)
    n = len(a)

    def can_place(d):
        count = 1
        last = a[0]
        for x in a[1:]:
            if x - last >= d:
                count += 1
                last = x
                if count >= m:
                    return True
        return False

    lo, hi = 1, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        lo, hi = (mid, hi) if can_place(mid) else (lo, mid - 1)
    return lo


# =============================================================================
# WAY 18: Sort + early termination
# =============================================================================
def max_distance_18(position, m):
    """Optimized: break early when count reaches m."""
    a = sorted(position)
    n = len(a)

    def can_place(d):
        count = 1
        last = a[0]
        for i in range(1, n):
            if a[i] - last >= d:
                count += 1
                if count >= m:
                    return True
                last = a[i]
        return False

    lo, hi = 1, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if can_place(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 19: Sort + recursive placement
# =============================================================================
def max_distance_19(position, m):
    """Recursive feasibility check."""
    a = sorted(position)
    n = len(a)

    def can_place(d):
        def helper(idx, count, last):
            if count >= m:
                return True
            if idx >= n:
                return False
            if a[idx] - last >= d:
                if helper(idx + 1, count + 1, a[idx]):
                    return True
            return helper(idx + 1, count, last)
        return helper(1, 1, a[0])

    lo, hi = 1, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if can_place(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def max_distance_20(position, m):
    """
    THE ONE TO MEMORIZE.

    1. Sort positions.
    2. Binary search on min distance d in [1, max_diff].
    3. For each d, greedy place: count balls with min gap d.
       If count >= m, d is feasible (try larger).
       Else infeasible (try smaller).
    4. Return max feasible d.

    Time:  O(n log(max_diff))
    Space: O(n) for sort
    """
    a = sorted(position)
    n = len(a)

    def can_place(d):
        count = 1
        last = a[0]
        for i in range(1, n):
            if a[i] - last >= d:
                count += 1
                if count >= m:
                    return True
                last = a[i]
        return False

    lo, hi = 1, a[-1] - a[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if can_place(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to place m balls in baskets such that the MINIMUM distance
between any two balls is MAXIMIZED. Return that maximum minimum."

Key Insight:
"Binary search on the ANSWER (distance d).
- Sort positions first.
- For each candidate d, check feasibility: can we place m balls with
  min gap d? Use greedy: place ball at first position, then next ball
  at first position >= last + d.
- If feasible: try larger d.
- If infeasible: try smaller d.
- The predicate is MONOTONIC: if d works, d-1 works too."

Algorithm:
1. Sort positions.
2. lo = 1, hi = max - min.
3. While lo < hi:
   - mid = (lo + hi + 1) // 2 (upper mid).
   - Greedy: count = 1, last = a[0]. For x in a[1:]: if x - last >= mid:
     count += 1, last = x. If count >= m: feasible.
   - If feasible: lo = mid. Else: hi = mid - 1.
4. Return lo.

Edge Cases:
- m = 2: just need max - min.
- All same position: 0.
- Two positions only: max - min.

Complexity:
+----------+----------+--------+
| Approach | Time     | Space  |
+----------+----------+--------+
| BS+greedy| O(nlog(M)| O(n)   |
|          | )        |        |
| Brute    | O(n^2*M) | O(n)   |
|          | or O(n*M)|        |
+----------+----------+--------+
Where M = max position value.

KEY TRICK:
Monotonic feasibility predicate. Greedy placement is optimal for
fixed distance: always pick earliest possible next ball.

RELATED PROBLEMS:
- Aggressive Cows (same problem on different name).
- K-th Smallest Pair Distance (LC 719).
- Capacity to Ship Packages (LC 1011).
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Sort+BS (BEST)", max_distance_1),
        ("Way 2: Sort+BS verbose", max_distance_2),
        ("Way 3: Sort+BS explicit", max_distance_3),
        ("Way 4: Sort+recursive BS", max_distance_4),
        ("Way 5: Sort+iterative", max_distance_5),
        ("Way 6: Brute force", max_distance_6),
        ("Way 7: Sort+memoized", max_distance_7),
        ("Way 8: Class OOP", max_distance_8),
        ("Way 9: Sort+lambda BS", max_distance_9),
        ("Way 10: Sort+accumulate", max_distance_10),
        ("Way 11: Sort+bisect", max_distance_11),
        ("Way 12: Sort+one-liner", max_distance_12),
        ("Way 13: Sort+manual range", max_distance_13),
        ("Way 14: Sort+generator", max_distance_14),
        ("Way 15: Sort+while greedy", max_distance_15),
        ("Way 16: Sort+numpy", max_distance_16),
        ("Way 17: Sort+reduce", max_distance_17),
        ("Way 18: Sort+early term", max_distance_18),
        ("Way 19: Sort+recursive", max_distance_19),
        ("Way 20: Final cleanest", max_distance_20),
    ]

    test_cases = [
        # (position, m, expected)
        ([1, 2, 3, 4, 7], 3, 3),  # 1,4,7
        ([5, 4, 3, 2, 1, 1000000000], 2, 999999999),  # 1 and 1e9
        ([1, 2, 3, 4, 5], 2, 4),  # 1 and 5
        ([1, 2, 3, 4, 5], 3, 2),  # 1,3,5
        ([1, 2, 3, 4, 5], 5, 1),  # all
        # Constraint says m >= 2 and position.length >= 2.
        # Remove the n=1 / m=n tests since those don't fit LC constraints.
        ([1, 2], 2, 1),
        ([1, 100], 2, 99),
        ([1, 2, 3], 2, 2),  # 1, 3
        ([10, 20, 30, 40, 50], 3, 20),  # 10, 30, 50
        # sorted [22,57,74,79]. d=5: 22,57,74,79 works. d=6 fails.
        ([79, 74, 57, 22], 4, 5),
        ([1, 5, 9, 10], 2, 9),  # 1 and 10
        ([0, 10, 20], 2, 20),
        ([0, 1], 2, 1),
        ([1, 2, 3, 4], 2, 3),  # 1 and 4
    ]

    print("=" * 70)
    print("MAGNETIC FORCE BETWEEN TWO BALLS - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/magnetic-force-between-two-balls")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for position, m, expected in test_cases:
            try:
                result = func(position[:], m)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: position={position}, m={m}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
