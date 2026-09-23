"""
Magnetic Force Between Two Balls
Medium | 30 min

You have baskets at given positions (sorted integer array). Place m balls
in the baskets (one ball per basket) to maximize the minimum distance
between any two balls. Return that maximum minimum distance.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/magnetic-force-between-two-balls

Constraints:
- 2 <= position.length <= 10^5
- 2 <= m <= position.length
- 0 <= position[i] <= 10^9
- position are distinct.

Examples:
    position=[1,2,3,4,7], m=3 -> 3
    (Place at 1, 4, 7. Min distance = 3.)
    position=[5,4,3,2,1,1000000000], m=2 -> 999999999
    (Place at 1 and 1000000000. Distance = 999999999.)

Key Insight:
Binary search on the answer.
For each candidate distance d, check if we can place m balls such that
all pairwise distances are >= d.

Greedy feasibility check:
- Place first ball at position[0].
- Each next ball at smallest position >= last_ball + d.
- If we can place m balls, d is feasible.

Time:  O(n log(max_position)) - binary search + O(n) per check.
Space: O(1) extra.
"""


# =============================================================================
# WAY 1: Binary search on answer (BEST - Memorize!)
# =============================================================================
def max_distance_1(position, m):
    """
    Sort positions. Binary search on distance d.
    For each d, greedy check if m balls fit with min distance d.
    """
    position.sort()
    n = len(position)
    lo, hi = 1, position[-1] - position[0]
    # Ensure at least m-1 balls can fit (m <= n per constraints)

    def feasible(d):
        """Check if we can place m balls with min distance d."""
        count = 1
        last = position[0]
        for i in range(1, n):
            if position[i] - last >= d:
                count += 1
                last = position[i]
                if count >= m:
                    return True
        return False

    while lo < hi:
        mid = (lo + hi + 1) // 2  # Upper mid to avoid infinite loop
        if feasible(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 2: Verbose version
# =============================================================================
def max_distance_2(position, m):
    """Verbose with comments."""
    position.sort()
    n = len(position)

    def can_place(d):
        count = 1
        last_pos = position[0]
        for i in range(1, n):
            if position[i] - last_pos >= d:
                count += 1
                last_pos = position[i]
                if count >= m:
                    return True
        return False

    left, right = 1, position[-1] - position[0]
    while left < right:
        mid = (left + right + 1) // 2
        if can_place(mid):
            left = mid
        else:
            right = mid - 1
    return left


# =============================================================================
# WAY 3: Different binary search variant
# =============================================================================
def max_distance_3(position, m):
    """Alternative binary search (lo + hi + 1) // 2 style."""
    position.sort()
    n = len(position)

    def feasible(d):
        count = 1
        last = position[0]
        for p in position[1:]:
            if p - last >= d:
                count += 1
                last = p
        return count >= m

    lo, hi = 1, position[-1] - position[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if feasible(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 4: With helper functions
# =============================================================================
def max_distance_4(position, m):
    """Extract helpers."""

    def sorted_positions(pos):
        return sorted(pos)

    def can_fit(positions, m_balls, min_dist):
        count = 1
        last = positions[0]
        for p in positions[1:]:
            if p - last >= min_dist:
                count += 1
                last = p
        return count >= m_balls

    positions = sorted_positions(position)
    lo, hi = 1, positions[-1] - positions[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if can_fit(positions, m, mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 5: Recursive binary search
# =============================================================================
def max_distance_5(position, m):
    """Recursive binary search."""

    def search(lo, hi):
        if lo >= hi:
            return lo
        mid = (lo + hi + 1) // 2
        if feasible(mid):
            return search(mid, hi)
        else:
            return search(lo, mid - 1)

    def feasible(d):
        count = 1
        last = position[0]
        for p in position[1:]:
            if p - last >= d:
                count += 1
                last = p
                if count >= m:
                    return True
        return False

    position.sort()
    return search(1, position[-1] - position[0])


# =============================================================================
# WAY 6: Class-based
# =============================================================================
class MagneticForce:
    def __init__(self, positions, m):
        self.positions = sorted(positions)
        self.m = m

    def feasible(self, d):
        count = 1
        last = self.positions[0]
        for p in self.positions[1:]:
            if p - last >= d:
                count += 1
                last = p
                if count >= self.m:
                    return True
        return False

    def max_distance(self):
        lo, hi = 1, self.positions[-1] - self.positions[0]
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.feasible(mid):
                lo = mid
            else:
                hi = mid - 1
        return lo


def max_distance_6(position, m):
    """Class-based."""
    return MagneticForce(position, m).max_distance()


# =============================================================================
# WAY 7: Use bisect for placement
# =============================================================================
def max_distance_7(position, m):
    """Use bisect to find next ball position."""
    position.sort()
    import bisect

    def feasible(d):
        count = 1
        last = position[0]
        for i in range(1, len(position)):
            # Find next position >= last + d
            target = last + d
            idx = bisect.bisect_left(position, target, i)
            if idx < len(position):
                count += 1
                last = position[idx]
                if count >= m:
                    return True
        return False

    lo, hi = 1, position[-1] - position[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if feasible(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 8: Iterate with enumerate
# =============================================================================
def max_distance_8(position, m):
    """Enumerate for iteration."""
    position.sort()
    n = len(position)

    def feasible(d):
        count = 1
        last = position[0]
        for i, p in enumerate(position[1:], start=1):
            if p - last >= d:
                count += 1
                last = p
                if count >= m:
                    return True
        return False

    lo, hi = 1, position[-1] - position[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if feasible(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 9: With itertools.islice
# =============================================================================
def max_distance_9(position, m):
    """Use islice for cleaner iteration."""
    from itertools import islice
    position.sort()
    n = len(position)

    def feasible(d):
        count = 1
        last = position[0]
        for p in islice(position, 1, None):
            if p - last >= d:
                count += 1
                last = p
                if count >= m:
                    return True
        return False

    lo, hi = 1, position[-1] - position[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if feasible(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 10: Lambda feasibility
# =============================================================================
def max_distance_10(position, m):
    """Use lambda for feasibility."""
    position.sort()

    def feasible(d):
        return sum(
            1 for i, p in enumerate(position[1:], 1)
            if p - position[i - 1] >= d  # Wait, this is wrong. Need last ball.
        ) + 1 >= m
    # Actually we need greedy: count balls, not pairs.
    # Let me fix this.

    def feasible2(d):
        count = 1
        last = position[0]
        for p in position[1:]:
            if p - last >= d:
                count += 1
                last = p
        return count >= m

    lo, hi = 1, position[-1] - position[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if feasible2(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 11: With reduce
# =============================================================================
def max_distance_11(position, m):
    """Use reduce for feasibility check."""
    from functools import reduce
    position.sort()

    def feasible(d):
        count, last = reduce(
            lambda acc, p: (acc[0] + 1, p) if p - acc[1] >= d else acc,
            position[1:],
            (1, position[0])
        )
        return count >= m

    lo, hi = 1, position[-1] - position[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if feasible(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 12: One-liner style (still clear)
# =============================================================================
def max_distance_12(position, m):
    """Cleaner one-liner feasibility."""
    position = sorted(position)  # Don't mutate input

    def feasible(d):
        cnt = 1
        last = position[0]
        for p in position[1:]:
            if p - last >= d:
                cnt += 1
                last = p
                if cnt >= m:
                    return True
        return False

    lo, hi = 1, position[-1] - position[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if feasible(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 13: While True binary search
# =============================================================================
def max_distance_13(position, m):
    """While True loop variant."""
    position.sort()

    def feasible(d):
        count = 1
        last = position[0]
        for p in position[1:]:
            if p - last >= d:
                count += 1
                last = p
        return count >= m

    lo, hi = 1, position[-1] - position[0]
    while True:
        if lo >= hi:
            return lo
        mid = (lo + hi + 1) // 2
        if feasible(mid):
            lo = mid
        else:
            hi = mid - 1


# =============================================================================
# WAY 14: Two-pointer for feasibility
# =============================================================================
def max_distance_14(position, m):
    """Two-pointer approach for feasibility."""

    def feasible(d):
        i = 0
        count = 1
        last = position[0]
        for j in range(1, len(position)):
            if position[j] - last >= d:
                count += 1
                last = position[j]
                if count >= m:
                    return True
        return False

    position.sort()
    lo, hi = 1, position[-1] - position[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if feasible(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 15: Memoize feasibility
# =============================================================================
def max_distance_15(position, m):
    """Memoize feasibility check."""
    from functools import lru_cache
    position.sort()

    @lru_cache(maxsize=None)
    def feasible(d):
        count = 1
        last = position[0]
        for p in position[1:]:
            if p - last >= d:
                count += 1
                last = p
        return count >= m

    lo, hi = 1, position[-1] - position[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if feasible(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 16: Iterative placement
# =============================================================================
def max_distance_16(position, m):
    """Iterative placement with explicit next_ball function."""
    position.sort()

    def count_balls(d):
        """Count how many balls can fit with min distance d."""
        count = 1
        last = position[0]
        for p in position[1:]:
            if p - last >= d:
                count += 1
                last = p
        return count

    lo, hi = 1, position[-1] - position[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if count_balls(mid) >= m:
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 17: Lower bound binary search
# =============================================================================
def max_distance_17(position, m):
    """Find largest feasible distance using lower_bound."""
    position.sort()

    def feasible(d):
        count = 1
        last = position[0]
        for p in position[1:]:
            if p - last >= d:
                count += 1
                last = p
        return count >= m

    # Binary search: find smallest d that is NOT feasible, then answer is d-1
    lo, hi = 1, position[-1] - position[0] + 1
    while lo < hi:
        mid = (lo + hi) // 2
        if feasible(mid):
            lo = mid + 1
        else:
            hi = mid
    return lo - 1


# =============================================================================
# WAY 18: Generator-based
# =============================================================================
def max_distance_18(position, m):
    """Use generator for feasibility."""

    def feasible(d):
        positions_gen = iter(position[1:])
        last = position[0]
        count = 1
        for p in positions_gen:
            if p - last >= d:
                count += 1
                last = p
                if count >= m:
                    return True
        return False

    position.sort()
    lo, hi = 1, position[-1] - position[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if feasible(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 19: Just for variety — same as Way 1 (binary search)
# =============================================================================
def max_distance_19(position, m):
    """Same as Way 1 (binary search)."""
    position.sort()
    n = len(position)

    def feasible(d):
        count = 1
        last = position[0]
        for p in position[1:]:
            if p - last >= d:
                count += 1
                last = p
        return count >= m

    lo, hi = 1, position[-1] - position[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if feasible(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def max_distance_20(position, m):
    """
    Final clean version.

    Algorithm:
    1. Sort positions.
    2. Binary search on distance d in [1, max-min].
    3. For each d, greedy check if m balls can fit with min distance d.
    4. Return largest feasible d.

    Why this works:
    - If distance d is feasible, all d' <= d are also feasible (monotone).
    - Binary search exploits this monotonicity.
    - Greedy placement: place balls at earliest positions. If m balls fit
      greedily, they can fit any way (greedy uses minimum positions).

    Why greedy works for feasibility:
    - Greedy uses the earliest possible positions, leaving more room for
      subsequent balls.
    - If greedy fails to fit m balls, no other placement can either
      (since greedy is optimal in this sense).

    Time:  O(n log(max_position)).
    Space: O(1) extra.
    """
    position.sort()
    n = len(position)

    def feasible(d):
        count = 1
        last = position[0]
        for i in range(1, n):
            if position[i] - last >= d:
                count += 1
                last = position[i]
                if count >= m:
                    return True
        return False

    lo, hi = 1, position[-1] - position[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if feasible(mid):
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
"I need to place m balls in baskets to maximize the minimum distance
between any two balls."

Key Insight:
"Binary search on the answer. For each candidate distance d, check if
m balls can fit with all pairwise distances >= d (greedy check). The
feasibility function is monotone: if d works, smaller d also works."

Algorithm:
"1. Sort positions.
2. Binary search on d in [1, max-min].
3. Feasibility check: greedy placement.
   - Place first ball at position[0].
   - Each next ball at smallest position >= last + d.
   - Count balls. If >= m, d is feasible.
4. Return largest feasible d."

Why this works:
"If d is feasible, all smaller d are also feasible (more room).
Greedy placement uses minimum positions, so if greedy fails, no
placement works."

Edge cases:
- m == n: each basket gets a ball. Min distance = sorted diff min.
- m == 2: distance = max - min.
- All positions close: distance is small.

Complexity:
- Time:  O(n log(max_position)) — binary search * O(n) per check.
- Space: O(1) extra.

KEY TRICK:
Binary search on the answer. Feasibility is monotone. Greedy placement.

ALTERNATIVE: Brute force
Try all placements. Exponential. Not feasible.

ALTERNATIVE: DP
For each position, place a ball or skip. State: (position, balls placed).
O(n*m) states. Possible but more complex.

ALTERNATIVE: Sort + DP
Track minimum max-min for each (position, balls placed). Similar complexity.

RELATIONSHIP TO OTHER PROBLEMS:
- Aggressive Cows (same problem, different name): LC 1552.
- Koko Eating Bananas (LC 875): Binary search on answer.
- Minimize Max Distance to Gas Station (LC 774): Binary search.

INTERVIEW TIPS:
1. Recognize this as binary search on answer.
2. Note the greedy feasibility check.
3. Discuss why greedy works.
4. Handle the upper bound calculation.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Binary search (BEST)", max_distance_1),
        ("Way 2: Verbose", max_distance_2),
        ("Way 3: Different binary search", max_distance_3),
        ("Way 4: Helper functions", max_distance_4),
        ("Way 5: Recursive", max_distance_5),
        ("Way 6: Class-based", max_distance_6),
        ("Way 7: bisect for placement", max_distance_7),
        ("Way 8: enumerate", max_distance_8),
        ("Way 9: itertools.islice", max_distance_9),
        ("Way 10: Lambda", max_distance_10),
        ("Way 11: functools.reduce", max_distance_11),
        ("Way 12: Cleaner one-liner", max_distance_12),
        ("Way 13: While True", max_distance_13),
        ("Way 14: Two-pointer", max_distance_14),
        ("Way 15: Memoize", max_distance_15),
        ("Way 16: Iterative placement", max_distance_16),
        ("Way 17: Lower bound", max_distance_17),
        ("Way 18: Generator", max_distance_18),
        ("Way 19: Linear scan", max_distance_19),
        ("Way 20: Final cleanest", max_distance_20),
    ]

    test_cases = [
        # Educative examples
        # position=[1,2,3,4,7], m=3 -> 3 (place at 1, 4, 7)
        ([1, 2, 3, 4, 7], 3, 3),

        # position=[5,4,3,2,1,1000000000], m=2 -> 999999999
        ([5, 4, 3, 2, 1, 1000000000], 2, 999999999),

        # m == n (each basket gets a ball)
        # position=[1,2,3], m=3 -> min distance = 1
        ([1, 2, 3], 3, 1),

        # m == 2
        # position=[1,5], m=2 -> distance = 4
        ([1, 5], 2, 4),

        # Standard case
        # position=[1,2,3,4,5], m=3
        # Place at 1, 3, 5. Min = 2.
        ([1, 2, 3, 4, 5], 3, 2),

        # Larger gap
        # position=[1,2,3,10,11,12], m=2
        # Place at 1 and 12. Distance = 11.
        ([1, 2, 3, 10, 11, 12], 2, 11),

        # Three balls in larger array
        # position=[1,5,9,10,15,20], m=3
        # Place at 1, 10, 20. Min = 9.
        # Or 1, 9, 20. Min = 8.
        # Or 5, 10, 20. Min = 5.
        # Best: 1, 10, 20 -> 9.
        ([1, 5, 9, 10, 15, 20], 3, 9),

        # Unsorted input
        # position=[7,4,3,2,1], m=3 -> 3 (sorted: 1,2,3,4,7, place at 1,4,7)
        ([7, 4, 3, 2, 1], 3, 3),
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
                import copy
                result = func(copy.deepcopy(position), m)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: pos={position}, m={m} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on pos={position}, m={m} - {e}")
        if all_test_pass:
            print(f"  OK {name}: PASS")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)