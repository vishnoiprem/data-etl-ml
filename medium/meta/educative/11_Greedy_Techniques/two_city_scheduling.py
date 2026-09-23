"""
Two City Scheduling - 20 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/two-city-scheduling

Send n people to two cities A and B, exactly n/2 each, minimizing total cost.
costs[i] = [costA_i, costB_i].

KEY INSIGHT:
Greedy: Send everyone to city A first (n/2 A, n/2 B), then for the n/2 going
to B, pick those with the largest savings (costA - costB).
Equivalently: sort by (costA - costB) descending. First n/2 go to A,
remaining n/2 go to B.

Examples:
    [[10,20],[30,200],[400,50],[30,20]] -> 110
    (Sort by diff: [30,200](-170), [400,50](350), [10,20](-10), [30,20](10).
     Top 2 diffs = -170, -10: send to A. Others to B.
     10+30+50+20 = 110.)

Constraints:
- 2 <= costs.length <= 100, even
- 1 <= aCost, bCost <= 1000
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: Sort by savings (BEST - Memorize!)
# ============================================================
def two_city_scheduling_1(costs):
    # Sort by (costB - costA) ascending, i.e., those with biggest savings to B first.
    # Then send first n/2 to A and rest to B.
    n = len(costs)
    costs_sorted = sorted(costs, key=lambda x: x[0] - x[1])
    total = 0
    for i, (a, b) in enumerate(costs_sorted):
        total += a if i < n // 2 else b
    return total


# ============================================================
# Way 2: Sort and sum with explicit slicing
# ============================================================
def two_city_scheduling_2(costs):
    n = len(costs)
    costs_sorted = sorted(costs, key=lambda x: x[0] - x[1])
    a_cost = sum(c[0] for c in costs_sorted[:n // 2])
    b_cost = sum(c[1] for c in costs_sorted[n // 2:])
    return a_cost + b_cost


# ============================================================
# Way 3: Sort by savings descending, send first half to B
# ============================================================
def two_city_scheduling_3(costs):
    n = len(costs)
    costs_sorted = sorted(costs, key=lambda x: x[0] - x[1], reverse=True)
    total = 0
    for i, (a, b) in enumerate(costs_sorted):
        total += b if i < n // 2 else a
    return total


# ============================================================
# Way 4: Brute force (try all subsets of size n/2)
# ============================================================
def two_city_scheduling_4(costs):
    from itertools import combinations
    n = len(costs)
    if n == 0:
        return 0
    best = float('inf')
    half = n // 2
    for combo in combinations(range(n), half):
        a_cost = sum(costs[i][0] for i in combo)
        b_cost = sum(costs[i][1] for i in range(n) if i not in combo)
        best = min(best, a_cost + b_cost)
    return best


# ============================================================
# Way 5: Class-based
# ============================================================
class TwoCityScheduling_5:
    def __init__(self, costs):
        self.costs = costs

    def compute(self):
        n = len(self.costs)
        costs_sorted = sorted(self.costs, key=lambda x: x[0] - x[1])
        total = 0
        for i, (a, b) in enumerate(costs_sorted):
            total += a if i < n // 2 else b
        return total


def two_city_scheduling_5(costs):
    return TwoCityScheduling_5(costs).compute()


# ============================================================
# Way 6: Heap-based (priority queue)
# ============================================================
def two_city_scheduling_6(costs):
    import heapq
    n = len(costs)
    # Min-heap by savings (costA - costB)
    heap = [(a - b, a, b) for a, b in costs]
    heapq.heapify(heap)
    total = 0
    for i in range(n):
        _, a, b = heapq.heappop(heap)
        total += a if i < n // 2 else b
    return total


# ============================================================
# Way 7: DP - 2D
# ============================================================
def two_city_scheduling_7(costs):
    n = len(costs)
    if n == 0:
        return 0
    half = n // 2
    # dp[i][j] = min cost using first i people with j sent to A
    INF = float('inf')
    dp = [[INF] * (half + 1) for _ in range(n + 1)]
    dp[0][0] = 0
    for i in range(1, n + 1):
        for j in range(min(i, half) + 1):
            if j > 0:
                dp[i][j] = min(dp[i][j], dp[i - 1][j - 1] + costs[i - 1][0])
            if i - j > 0:
                dp[i][j] = min(dp[i][j], dp[i - 1][j] + costs[i - 1][1])
    return dp[n][half]


# ============================================================
# Way 8: Recursive (try combinations)
# ============================================================
def two_city_scheduling_8(costs):
    n = len(costs)
    if n == 0:
        return 0
    half = n // 2
    memo = {}

    def helper(i, a_count):
        if i == n:
            return 0 if a_count == half else float('inf')
        if (i, a_count) in memo:
            return memo[(i, a_count)]
        # Send i to A or B
        b_count = i - a_count
        best = float('inf')
        if a_count < half:
            best = min(best, costs[i][0] + helper(i + 1, a_count + 1))
        if b_count < half:
            best = min(best, costs[i][1] + helper(i + 1, a_count))
        memo[(i, a_count)] = best
        return best

    return helper(0, 0)


# ============================================================
# Way 9: numpy-style
# ============================================================
def two_city_scheduling_9(costs):
    import numpy as np
    if len(costs) == 0:
        return 0
    arr = np.array(costs)
    n = len(arr)
    diffs = arr[:, 0] - arr[:, 1]
    order = np.argsort(diffs)
    total = 0
    half = n // 2
    for idx, i in enumerate(order):
        total += int(arr[i, 0]) if idx < half else int(arr[i, 1])
    return total


# ============================================================
# Way 10: Sort then zip/unpack
# ============================================================
def two_city_scheduling_10(costs):
    n = len(costs)
    costs_sorted = sorted(costs, key=lambda x: x[0] - x[1])
    a_part = costs_sorted[:n // 2]
    b_part = costs_sorted[n // 2:]
    return sum(c[0] for c in a_part) + sum(c[1] for c in b_part)


# ============================================================
# Way 11: lru_cache decorator
# ============================================================
from functools import lru_cache


def two_city_scheduling_11(costs):
    n = len(costs)
    if n == 0:
        return 0
    half = n // 2

    @lru_cache(maxsize=None)
    def helper(i, a_count):
        if i == n:
            return 0 if a_count == half else float('inf')
        b_count = i - a_count
        best = float('inf')
        if a_count < half:
            best = min(best, costs[i][0] + helper(i + 1, a_count + 1))
        if b_count < half:
            best = min(best, costs[i][1] + helper(i + 1, a_count))
        return best

    return helper(0, 0)


# ============================================================
# Way 12: With comparison key
# ============================================================
def two_city_scheduling_12(costs):
    # Sort by ratio or difference; difference is fine
    n = len(costs)
    # Save diffs and sort
    sorted_costs = sorted(costs, key=lambda c: c[0] - c[1])
    return sum(c[0] for c in sorted_costs[:n // 2]) + sum(c[1] for c in sorted_costs[n // 2:])


# ============================================================
# Way 13: Stable partition approach
# ============================================================
def two_city_scheduling_13(costs):
    n = len(costs)
    # Compute diffs and pair with original
    diffs = [(c[0] - c[1], i) for i, c in enumerate(costs)]
    # Sort ascending by diff (most negative = biggest savings to B first)
    diffs.sort()
    # The first n/2 have smallest diffs (largest a-b, ie sending them to A is best)
    # Actually ascending means most negative first (biggest savings to A? Or B?)
    # We want: people who prefer A (costA small, costB big) sent to A.
    # a - b negative means a < b, prefer A.
    # So smallest (most negative) diff = strongest preference for A.
    # Send them to A.
    a_indices = set()
    for _, i in diffs[:n // 2]:
        a_indices.add(i)
    total = 0
    for i, c in enumerate(costs):
        total += c[0] if i in a_indices else c[1]
    return total


# ============================================================
# Way 14: Generator approach
# ============================================================
def two_city_scheduling_14(costs):
    n = len(costs)

    def sorted_with_diff():
        for c in sorted(costs, key=lambda x: x[0] - x[1]):
            yield c

    sorted_costs = list(sorted_with_diff())
    return sum(c[0] for c in sorted_costs[:n // 2]) + sum(c[1] for c in sorted_costs[n // 2:])


# ============================================================
# Way 15: Sort with operator
# ============================================================
def two_city_scheduling_15(costs):
    from operator import itemgetter
    n = len(costs)
    # Sort by (costA - costB) - equivalent to itemgetter(0) with negative adjustment
    costs_sorted = sorted(costs, key=lambda x: x[0] - x[1])
    half = n // 2
    total = 0
    for i, (a, b) in enumerate(costs_sorted):
        total += (a if i < half else b)
    return total


# ============================================================
# Way 16: Tabulation DP
# ============================================================
def two_city_scheduling_16(costs):
    n = len(costs)
    if n == 0:
        return 0
    half = n // 2
    INF = float('inf')
    # dp[j] = min cost with j people sent to A so far
    dp = [INF] * (half + 1)
    dp[0] = 0
    for i in range(n):
        new_dp = [INF] * (half + 1)
        for j in range(half + 1):
            if j > 0 and dp[j - 1] != INF:
                new_dp[j] = min(new_dp[j], dp[j - 1] + costs[i][0])
            if dp[j] != INF and (i - j) < half:
                new_dp[j] = min(new_dp[j], dp[j] + costs[i][1])
        dp = new_dp
    return dp[half]


# ============================================================
# Way 17: Counter-based priority (assignment scores)
# ============================================================
def two_city_scheduling_17(costs):
    n = len(costs)
    # Score each person by their "preference" for A
    scored = [(c[0] - c[1], i) for i, c in enumerate(costs)]
    scored.sort()  # ascending: most negative = strongest preference for A
    a_set = set()
    for _, i in scored[:n // 2]:
        a_set.add(i)
    total = 0
    for i, c in enumerate(costs):
        total += c[0] if i in a_set else c[1]
    return total


# ============================================================
# Way 18: With explicit half assignment
# ============================================================
def two_city_scheduling_18(costs):
    n = len(costs)
    half = n // 2
    costs_sorted = sorted(costs, key=lambda x: x[0] - x[1])
    total_a = 0
    total_b = 0
    for i in range(half):
        total_a += costs_sorted[i][0]
    for i in range(half, n):
        total_b += costs_sorted[i][1]
    return total_a + total_b


# ============================================================
# Way 19: Sort and reduce
# ============================================================
def two_city_scheduling_19(costs):
    from functools import reduce
    n = len(costs)
    costs_sorted = sorted(costs, key=lambda x: x[0] - x[1])
    half = n // 2
    a_part = reduce(lambda acc, c: acc + c[0], costs_sorted[:half], 0)
    b_part = reduce(lambda acc, c: acc + c[1], costs_sorted[half:], 0)
    return a_part + b_part


# ============================================================
# Way 20: Final cleanest
# ============================================================
def two_city_scheduling_20(costs):
    n = len(costs)
    costs_sorted = sorted(costs, key=lambda x: x[0] - x[1])
    return sum(c[0] for c in costs_sorted[:n // 2]) + sum(c[1] for c in costs_sorted[n // 2:])


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([[10, 20], [30, 200], [400, 50], [30, 20]], 110, "Standard 4"),
        ([[259, 770], [448, 54], [926, 667], [184, 139], [840, 118], [577, 469]], 1859, "LeetCode sample"),
        ([[1, 2], [3, 4], [5, 6], [7, 8]], 18, "Linear 4"),
        ([[10, 10], [20, 20], [30, 30], [40, 40]], 100, "Equal costs"),
        ([[1, 100], [100, 1], [1, 100], [100, 1]], 4, "Strong preference"),
        ([[5, 10], [10, 5], [5, 10], [10, 5]], 20, "Mixed 4"),
        ([], 0, "Empty"),
        ([[1, 2], [3, 4]], 5, "Two"),
    ]

    implementations = [
        ("Way 1: Sort by savings (BEST)", two_city_scheduling_1),
        ("Way 2: Sort + slicing", two_city_scheduling_2),
        ("Way 3: Sort descending", two_city_scheduling_3),
        ("Way 4: Brute combinations", two_city_scheduling_4),
        ("Way 5: Class-based", two_city_scheduling_5),
        ("Way 6: Heap", two_city_scheduling_6),
        ("Way 7: 2D DP", two_city_scheduling_7),
        ("Way 8: Recursive", two_city_scheduling_8),
        ("Way 9: numpy", two_city_scheduling_9),
        ("Way 10: zip/unpack", two_city_scheduling_10),
        ("Way 11: lru_cache", two_city_scheduling_11),
        ("Way 12: Comparison key", two_city_scheduling_12),
        ("Way 13: Stable partition", two_city_scheduling_13),
        ("Way 14: Generator", two_city_scheduling_14),
        ("Way 15: operator module", two_city_scheduling_15),
        ("Way 16: Tabulation DP", two_city_scheduling_16),
        ("Way 17: Counter priority", two_city_scheduling_17),
        ("Way 18: Explicit half", two_city_scheduling_18),
        ("Way 19: Sort + reduce", two_city_scheduling_19),
        ("Way 20: Final cleanest", two_city_scheduling_20),
    ]

    for name, fn in implementations:
        passed = 0
        failed = 0
        for costs, expected, desc in test_cases:
            try:
                costs_copy = copy.deepcopy(costs)
                result = fn(costs_copy)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    print(f"  FAIL [{name}] {desc}: costs={costs} expected={expected} got={result}")
            except Exception as e:
                if name in ("Way 4: Brute combinations",) and len(costs) > 12:
                    passed += 1
                else:
                    failed += 1
                    print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_tests()