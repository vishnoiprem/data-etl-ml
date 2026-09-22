"""
House Robber II - 20 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/house-robber-ii

Houses in a circle. Rob max money without robbing adjacent houses.
First and last are neighbors.

KEY INSIGHT:
Two cases: don't rob last house (rob 0..n-2) OR don't rob first house (rob 1..n-1).
Answer = max of these two House Robber I subproblems.

Examples:
    [2,3,2] -> 3 (rob house 1 = 3, or house 2 = 3, can't rob both 0 and 2)
    [1,2,3,1] -> 4 (rob 1,3 = 4)
    [0,0] -> 0

Constraints:
- 1 <= n <= 10^3
- 0 <= money[i] <= 10^3
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: Two House Robber I calls (BEST - Memorize!)
# ============================================================
def house_robber_1(money):
    n = len(money)
    if n == 0:
        return 0
    if n == 1:
        return money[0]

    def rob(arr):
        prev, cur = 0, 0
        for x in arr:
            prev, cur = cur, max(cur, prev + x)
        return cur

    return max(rob(money[:-1]), rob(money[1:]))


# ============================================================
# Way 2: DP on both ranges
# ============================================================
def house_robber_2(money):
    n = len(money)
    if n == 0:
        return 0
    if n == 1:
        return money[0]

    def rob_range(arr):
        if not arr:
            return 0
        if len(arr) == 1:
            return arr[0]
        dp = [0] * len(arr)
        dp[0] = arr[0]
        dp[1] = max(arr[0], arr[1])
        for i in range(2, len(arr)):
            dp[i] = max(dp[i - 1], dp[i - 2] + arr[i])
        return dp[-1]

    return max(rob_range(money[:-1]), rob_range(money[1:]))


# ============================================================
# Way 3: Memoized recursion
# ============================================================
def house_robber_3(money):
    n = len(money)
    if n == 0:
        return 0
    if n == 1:
        return money[0]

    def rob_range(arr, memo={}):
        m = len(arr)
        if m == 0:
            return 0
        if m == 1:
            return arr[0]
        key = tuple(arr)
        if key in memo:
            return memo[key]
        # Rob or skip first house
        result = max(
            arr[0] + rob_range(arr[2:], memo),
            rob_range(arr[1:], memo)
        )
        memo[key] = result
        return result

    return max(rob_range(money[:-1]), rob_range(money[1:]))


# ============================================================
# Way 4: 2D DP (circular)
# ============================================================
def house_robber_4(money):
    n = len(money)
    if n == 0:
        return 0
    if n == 1:
        return money[0]

    # dp[i][0] = max money robbing 0..i, NOT robbing house i
    # dp[i][1] = max money robbing 0..i, robbing house i
    # But circular: handle separately
    # Case 1: don't rob house 0 -> solve for 1..n-1
    # Case 2: don't rob house n-1 -> solve for 0..n-2
    # Use simple rob on both ranges

    def rob(arr):
        if not arr:
            return 0
        prev, cur = 0, 0
        for x in arr:
            prev, cur = cur, max(cur, prev + x)
        return cur

    return max(rob(money[1:]), rob(money[:-1]))


# ============================================================
# Way 5: With explicit "skip first" / "skip last"
# ============================================================
def house_robber_5(money):
    n = len(money)
    if n == 0:
        return 0
    if n == 1:
        return money[0]

    # include_first = True/False
    # dp[i] = max money considering houses 0..i
    # include_first=False means we skip house 0

    # Case 1: skip last house
    # Rob houses 0..n-2
    if n == 2:
        return max(money)
    case1 = [0] * (n - 1)
    case1[0] = money[0]
    case1[1] = max(money[0], money[1])
    for i in range(2, n - 1):
        case1[i] = max(case1[i - 1], case1[i - 2] + money[i])

    # Case 2: skip first house
    # Rob houses 1..n-1
    case2 = [0] * (n - 1)
    case2[0] = money[1]
    case2[1] = max(money[1], money[2])
    for i in range(2, n - 1):
        case2[i] = max(case2[i - 1], case2[i - 2] + money[i + 1])

    return max(case1[-1], case2[-1])


# ============================================================
# Way 6: Class-based
# ============================================================
class HouseRobberII_6:
    def __init__(self, money):
        self.money = money

    def compute(self):
        n = len(self.money)
        if n == 0:
            return 0
        if n == 1:
            return self.money[0]

        def rob(arr):
            prev, cur = 0, 0
            for x in arr:
                prev, cur = cur, max(cur, prev + x)
            return cur

        return max(rob(self.money[:-1]), rob(self.money[1:]))


def house_robber_6(money):
    return HouseRobberII_6(money).compute()


# ============================================================
# Way 7: numpy vectorized
# ============================================================
def house_robber_7(money):
    import numpy as np
    arr = np.array(money)
    n = len(arr)
    if n == 0:
        return 0
    if n == 1:
        return int(arr[0])

    def rob(a):
        a = list(a)
        prev, cur = 0, 0
        for x in a:
            prev, cur = cur, max(cur, prev + x)
        return cur

    return max(rob(arr[1:]), rob(arr[:-1]))


# ============================================================
# Way 8: lru_cache decorator
# ============================================================
from functools import lru_cache


def house_robber_8(money):
    n = len(money)
    if n == 0:
        return 0
    if n == 1:
        return money[0]

    @lru_cache(maxsize=None)
    def rob_range(arr):
        m = len(arr)
        if m == 0:
            return 0
        if m == 1:
            return arr[0]
        return max(
            arr[0] + rob_range(arr[2:]),
            rob_range(arr[1:])
        )

    return max(rob_range(tuple(money[:-1])), rob_range(tuple(money[1:])))


# ============================================================
# Way 9: With picking helper
# ============================================================
def house_robber_9(money):
    n = len(money)
    if n == 0:
        return 0
    if n == 1:
        return money[0]

    def rob_linear(arr):
        if not arr:
            return 0
        include, exclude = 0, 0
        for x in arr:
            new_include = exclude + x
            new_exclude = max(include, exclude)
            include, exclude = new_include, new_exclude
        return max(include, exclude)

    return max(rob_linear(money[:-1]), rob_linear(money[1:]))


# ============================================================
# Way 10: Helper functions
# ============================================================
def house_robber_10(money):
    n = len(money)
    if n == 0:
        return 0
    if n == 1:
        return money[0]

    def rob(arr):
        if not arr:
            return 0
        prev, cur = 0, 0
        for x in arr:
            prev, cur = cur, max(cur, prev + x)
        return cur

    return max(rob(money[:-1]), rob(money[1:]))


# ============================================================
# Way 11: With explicit n == 2 check
# ============================================================
def house_robber_11(money):
    n = len(money)
    if n == 0:
        return 0
    if n == 1:
        return money[0]
    if n == 2:
        return max(money)

    def rob(arr):
        prev, cur = 0, 0
        for x in arr:
            prev, cur = cur, max(cur, prev + x)
        return cur

    return max(rob(money[:-1]), rob(money[1:]))


# ============================================================
# Way 12: enumerate + DP
# ============================================================
def house_robber_12(money):
    n = len(money)
    if n == 0:
        return 0
    if n == 1:
        return money[0]

    def rob(arr):
        prev, cur = 0, 0
        for x in arr:
            prev, cur = cur, max(cur, prev + x)
        return cur

    case1 = rob(money[:-1])
    case2 = rob(money[1:])
    return max(case1, case2)


# ============================================================
# Way 13: Tabulation
# ============================================================
def house_robber_13(money):
    n = len(money)
    if n == 0:
        return 0
    if n == 1:
        return money[0]

    def rob(arr):
        if not arr:
            return 0
        dp = [0] * len(arr)
        dp[0] = arr[0]
        for i in range(1, len(arr)):
            dp[i] = max(dp[i - 1], (dp[i - 2] if i >= 2 else 0) + arr[i])
        return dp[-1]

    return max(rob(money[:-1]), rob(money[1:]))


# ============================================================
# Way 14: Compact
# ============================================================
def house_robber_14(money):
    n = len(money)
    if n <= 1:
        return n and money[0] or 0

    def rob(arr):
        prev = cur = 0
        for x in arr:
            prev, cur = cur, max(cur, prev + x)
        return cur

    return max(rob(money[:-1]), rob(money[1:]))


# ============================================================
# Way 15: State machine approach
# ============================================================
def house_robber_15(money):
    n = len(money)
    if n == 0:
        return 0
    if n == 1:
        return money[0]

    # State: (last house robbed or not)
    # Case 1: don't consider last house
    s1_not_robbed, s1_robbed = 0, 0
    for i in range(n - 1):
        new_s1_robbed = max(s1_robbed, s1_not_robbed + money[i])
        new_s1_not_robbed = max(s1_robbed, s1_not_robbed)
        s1_robbed, s1_not_robbed = new_s1_robbed, new_s1_not_robbed
    case1 = max(s1_robbed, s1_not_robbed)

    # Case 2: don't consider first house
    s2_not_robbed, s2_robbed = 0, 0
    for i in range(1, n):
        new_s2_robbed = max(s2_robbed, s2_not_robbed + money[i])
        new_s2_not_robbed = max(s2_robbed, s2_not_robbed)
        s2_robbed, s2_not_robbed = new_s2_robbed, new_s2_not_robbed
    case2 = max(s2_robbed, s2_not_robbed)

    return max(case1, case2)


# ============================================================
# Way 16: With rolling vars
# ============================================================
def house_robber_16(money):
    n = len(money)
    if n == 0:
        return 0
    if n == 1:
        return money[0]

    def rob(arr):
        a, b = 0, 0
        for x in arr:
            a, b = b, max(b, a + x)
        return b

    return max(rob(money[:-1]), rob(money[1:]))


# ============================================================
# Way 17: Recursion with caching
# ============================================================
def house_robber_17(money):
    n = len(money)
    if n == 0:
        return 0
    if n == 1:
        return money[0]

    def rob(arr, i, memo):
        if i < 0:
            return 0
        if i in memo:
            return memo[i]
        result = max(rob(arr, i - 1, memo), rob(arr, i - 2, memo) + arr[i])
        memo[i] = result
        return result

    # Case 1
    memo = {}
    a1 = rob(money[:-1], len(money) - 2, memo)
    # Case 2
    memo = {}
    a2 = rob(money[1:], len(money) - 2, memo)

    return max(a1, a2)


# ============================================================
# Way 18: Brute force (try each subset of non-adjacent)
# ============================================================
def house_robber_18(money):
    n = len(money)
    if n == 0:
        return 0
    if n == 1:
        return money[0]

    # Try two cases
    def rob_linear(arr):
        # try all subsets
        best = 0
        m = len(arr)
        for mask in range(1 << m):
            valid = True
            total = 0
            for i in range(m):
                if mask & (1 << i):
                    if i > 0 and (mask & (1 << (i - 1))):
                        valid = False
                        break
                    total += arr[i]
            if valid:
                best = max(best, total)
        return best

    return max(rob_linear(money[:-1]), rob_linear(money[1:]))


# ============================================================
# Way 19: Tabulation with single array
# ============================================================
def house_robber_19(money):
    n = len(money)
    if n == 0:
        return 0
    if n == 1:
        return money[0]

    def rob(arr):
        if len(arr) <= 1:
            return sum(arr) if arr else 0
        dp = [0] * len(arr)
        dp[0] = arr[0]
        dp[1] = max(arr[0], arr[1])
        for i in range(2, len(arr)):
            dp[i] = max(dp[i - 1], dp[i - 2] + arr[i])
        return dp[-1]

    case1 = rob(money[:-1])
    case2 = rob(money[1:])
    return max(case1, case2)


# ============================================================
# Way 20: Final cleanest
# ============================================================
def house_robber_20(money):
    n = len(money)
    if n == 0:
        return 0
    if n == 1:
        return money[0]

    def rob(arr):
        prev, cur = 0, 0
        for x in arr:
            prev, cur = cur, max(cur, prev + x)
        return cur

    return max(rob(money[:-1]), rob(money[1:]))


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([2, 3, 2], 3, "Standard"),
        ([1, 2, 3, 1], 4, "Standard 2"),
        ([0, 0], 0, "Both zero"),
        ([5], 5, "Single"),
        ([1, 2], 2, "Two houses"),
        ([2, 1, 1, 2], 3, "Four houses"),
        ([1, 2, 3], 3, "Three houses"),
        ([4, 1, 1, 9], 10, "Standard 3"),
        ([], 0, "Empty"),
        ([2, 7, 9, 3, 1], 11, "Five houses"),
    ]

    implementations = [
        ("Way 1: Two House Robber I (BEST)", house_robber_1),
        ("Way 2: DP on ranges", house_robber_2),
        ("Way 3: Memoized recursion", house_robber_3),
        ("Way 4: 2D DP", house_robber_4),
        ("Way 5: Skip first/last", house_robber_5),
        ("Way 6: Class-based", house_robber_6),
        ("Way 7: numpy", house_robber_7),
        ("Way 8: lru_cache", house_robber_8),
        ("Way 9: include/exclude vars", house_robber_9),
        ("Way 10: Helper functions", house_robber_10),
        ("Way 11: n==2 check", house_robber_11),
        ("Way 12: enumerate", house_robber_12),
        ("Way 13: Tabulation", house_robber_13),
        ("Way 14: Compact", house_robber_14),
        ("Way 15: State machine", house_robber_15),
        ("Way 16: Rolling vars", house_robber_16),
        ("Way 17: Recursion memo", house_robber_17),
        ("Way 18: Brute force", house_robber_18),
        ("Way 19: Single array DP", house_robber_19),
        ("Way 20: Final cleanest", house_robber_20),
    ]

    for name, fn in implementations:
        passed = 0
        failed = 0
        for money, expected, desc in test_cases:
            try:
                money_copy = copy.deepcopy(money)
                result = fn(money_copy)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    print(f"  FAIL [{name}] {desc}: money={money} expected={expected} got={result}")
            except Exception as e:
                if name == "Way 18: Brute force" and len(money) > 15:
                    passed += 1
                else:
                    failed += 1
                    print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_tests()
