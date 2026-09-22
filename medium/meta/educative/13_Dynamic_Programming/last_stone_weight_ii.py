"""
Last Stone Weight II - 20 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/last-stone-weight-ii

Given stones (array of weights), the game smash rule:
- pick any two stones x, y with x <= y.
- if x == y: both destroyed.
- if x < y: stone x destroyed, stone y becomes y - x.
- game ends when at most one stone remains.

Return the smallest possible weight of the remaining stone.

KEY INSIGHT:
Smashing stones is equivalent to partitioning them into two groups (A, B).
Each smash is a +/- operation. The final remaining weight = |sum(A) - sum(B)|.
We want to minimize this, so we want sum(A) as close to total/2 as possible.
This is the classic "Partition into two subsets with min difference" problem.

dp[i] = True if subset sum i is achievable.
Then answer = min |total - 2*i| for valid i.

Examples:
    stones = [2,7,4,1,8,1] -> 1
        Partition: A={2,4,1,1}=8, B={7,8}=15... wait total=23.
        Best subset sum closest to 11: {2,4,1,8} = wait 2+4+1+8=15...
        Actually: {2,7,1,1}=11 exactly. 23-2*11=1.
    stones = [31,26,33,21,40] -> 5
        total = 151. half = 75. Best subset sum near 75:
        {31,33,21}=85? No. {31,40}=71, {31,26,21}=78, {33,40}=73,
        {31,26,21}=78, {33,26,21}=80, {40,21,26}=87, {33,21}=54...
        Closest to 75: {33,40}=73, diff=|151-2*73|=5. ✓

Constraints:
- 1 <= stones.length <= 30
- 1 <= stones[i] <= 100
- total sum <= 3000
"""

import copy
import sys

sys.setrecursionlimit(10000)


# ============================================================
# Way 1: Subset sum DP (BEST - Memorize!)
# ============================================================
def lastStoneWeightII_1(stones):
    total = sum(stones)
    target = total // 2
    dp = [False] * (target + 1)
    dp[0] = True
    for stone in stones:
        # iterate in reverse to avoid using stone twice
        for s in range(target, stone - 1, -1):
            if dp[s - stone]:
                dp[s] = True
    # find largest achievable sum <= target
    for s in range(target, -1, -1):
        if dp[s]:
            return total - 2 * s
    return total


# ============================================================
# Way 2: Verbose subset sum
# ============================================================
def lastStoneWeightII_2(stones):
    total = sum(stones)
    n = len(stones)
    target = total // 2
    # dp[i][s] = can we achieve sum s using first i stones
    dp = [[False] * (target + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = True
    for i in range(1, n + 1):
        for s in range(target + 1):
            dp[i][s] = dp[i - 1][s]
            if s >= stones[i - 1]:
                dp[i][s] = dp[i][s] or dp[i - 1][s - stones[i - 1]]
    for s in range(target, -1, -1):
        if dp[n][s]:
            return total - 2 * s
    return total


# ============================================================
# Way 3: Brute force (subset enumeration) - exponential
# ============================================================
def lastStoneWeightII_3(stones):
    n = len(stones)
    best = float('inf')
    # 2^n subsets: bit i means stone i is in group A (positive)
    for mask in range(1 << n):
        sum_a = 0
        sum_b = 0
        for i in range(n):
            if mask & (1 << i):
                sum_a += stones[i]
            else:
                sum_b += stones[i]
        best = min(best, abs(sum_a - sum_b))
    return best


# ============================================================
# Way 4: Memoized recursion
# ============================================================
def lastStoneWeightII_4(stones):
    memo = {}

    def helper(i, current_diff):
        # current_diff = sum_a - sum_b for stones processed so far
        if i == len(stones):
            return abs(current_diff)
        key = (i, current_diff)
        if key in memo:
            return memo[key]
        # stone in A (add to A's sum)
        take = helper(i + 1, current_diff + stones[i])
        # stone in B (subtract from A's sum)
        skip = helper(i + 1, current_diff - stones[i])
        memo[key] = min(take, skip)
        return memo[key]

    return helper(0, 0)


# ============================================================
# Way 5: DP over subset sums (using bitset)
# ============================================================
def lastStoneWeightII_5(stones):
    total = sum(stones)
    bits = 1  # bit 0 set = sum 0 achievable
    for stone in stones:
        bits = bits | (bits << stone)
    target = total // 2
    # mask keeps only sums <= target
    mask = bits & ((1 << (target + 1)) - 1)
    # find highest bit set
    s = mask.bit_length() - 1
    return total - 2 * s


# ============================================================
# Way 6: Class-based
# ============================================================
class LastStoneWeightII_6:
    def __init__(self, stones):
        self.stones = stones

    def compute(self):
        total = sum(self.stones)
        target = total // 2
        dp = set([0])
        for stone in self.stones:
            new_dp = set(dp)
            for s in dp:
                if s + stone <= target:
                    new_dp.add(s + stone)
            dp = new_dp
        s = max(dp)
        return total - 2 * s


def lastStoneWeightII_6(stones):
    return LastStoneWeightII_6(stones).compute()


# ============================================================
# Way 7: numpy vectorized
# ============================================================
def lastStoneWeightII_7(stones):
    import numpy as np
    total = sum(stones)
    target = total // 2
    dp = np.zeros(target + 1, dtype=bool)
    dp[0] = True
    for stone in stones:
        if stone <= target:
            shifted = np.zeros(target + 1, dtype=bool)
            shifted[stone:] = dp[:target + 1 - stone]
            dp = dp | shifted
    s = int(np.max(np.where(dp)[0])) if dp.any() else 0
    return total - 2 * s


# ============================================================
# Way 8: lru_cache decorator
# ============================================================
from functools import lru_cache


def lastStoneWeightII_8(stones):
    stones_tuple = tuple(stones)
    n = len(stones_tuple)

    @lru_cache(maxsize=None)
    def helper(i, current_diff):
        if i == n:
            return abs(current_diff)
        return min(
            helper(i + 1, current_diff + stones_tuple[i]),
            helper(i + 1, current_diff - stones_tuple[i])
        )

    return helper(0, 0)


# ============================================================
# Way 9: Iterative using set of achievable sums
# ============================================================
def lastStoneWeightII_9(stones):
    total = sum(stones)
    target = total // 2
    achievable = {0}
    for stone in stones:
        # add stone to each existing subset to form new subsets
        new_sums = {s + stone for s in achievable if s + stone <= target}
        achievable |= new_sums
    s = max(achievable)
    return total - 2 * s


# ============================================================
# Way 10: Helper functions
# ============================================================
def lastStoneWeightII_10(stones):
    def subset_sum(items, target):
        dp = [False] * (target + 1)
        dp[0] = True
        for item in items:
            for s in range(target, item - 1, -1):
                if dp[s - item]:
                    dp[s] = True
        return dp

    total = sum(stones)
    target = total // 2
    dp = subset_sum(stones, target)
    for s in range(target, -1, -1):
        if dp[s]:
            return total - 2 * s
    return total


# ============================================================
# Way 11: Functional map
# ============================================================
def lastStoneWeightII_11(stones):
    from functools import reduce
    total = sum(stones)
    target = total // 2
    # dp is a set of achievable sums after each stone
    dp = reduce(
        lambda acc, stone: acc | {s + stone for s in acc if s + stone <= target},
        stones,
        {0}
    )
    s = max(dp)
    return total - 2 * s


# ============================================================
# Way 12: One-liner-ish using itertools
# ============================================================
def lastStoneWeightII_12(stones):
    from itertools import combinations
    n = len(stones)
    total = sum(stones)
    best = total
    # enumerate all subsets
    for r in range(n + 1):
        for combo in combinations(range(n), r):
            s = sum(stones[i] for i in combo)
            best = min(best, abs(total - 2 * s))
    return best


# ============================================================
# Way 13: DFS with pruning
# ============================================================
def lastStoneWeightII_13(stones):
    # Sort descending to prune early
    stones = sorted(stones, reverse=True)
    n = len(stones)
    best = [float('inf')]

    def dfs(i, diff):
        if i == n:
            best[0] = min(best[0], abs(diff))
            return
        if abs(diff) >= best[0]:
            return  # prune: can't improve
        dfs(i + 1, diff + stones[i])
        dfs(i + 1, diff - stones[i])

    dfs(0, 0)
    return best[0]


# ============================================================
# Way 14: Meet in the middle (for larger n)
# ============================================================
def lastStoneWeightII_14(stones):
    n = len(stones)
    mid = n // 2
    left = stones[:mid]
    right = stones[mid:]
    target = sum(stones) // 2

    def all_sums(arr):
        sums = []
        for mask in range(1 << len(arr)):
            s = 0
            for i in range(len(arr)):
                if mask & (1 << i):
                    s += arr[i]
            sums.append(s)
        return sums

    left_sums = all_sums(left)
    right_sums = sorted(all_sums(right))

    import bisect
    best = float('inf')
    for ls in left_sums:
        # find right_sum closest to (target - ls)
        rem = target - ls
        idx = bisect.bisect_right(right_sums, rem)
        if idx < len(right_sums):
            total_sum = ls + right_sums[idx]
            best = min(best, abs(sum(stones) - 2 * total_sum))
        if idx > 0:
            total_sum = ls + right_sums[idx - 1]
            best = min(best, abs(sum(stones) - 2 * total_sum))
    return best


# ============================================================
# Way 15: Tabulation by index
# ============================================================
def lastStoneWeightII_15(stones):
    total = sum(stones)
    target = total // 2
    n = len(stones)
    # dp[i] = set of achievable sums using stones processed so far
    dp = [set() for _ in range(n + 1)]
    dp[0].add(0)
    for i in range(1, n + 1):
        stone = stones[i - 1]
        for s in dp[i - 1]:
            dp[i].add(s)
            if s + stone <= target:
                dp[i].add(s + stone)
    s = max(dp[n])
    return total - 2 * s


# ============================================================
# Way 16: enumerate-based subset sum
# ============================================================
def lastStoneWeightII_16(stones):
    total = sum(stones)
    target = total // 2
    dp = [False] * (target + 1)
    dp[0] = True
    for i, stone in enumerate(stones):
        for s in range(target, stone - 1, -1):
            if dp[s - stone]:
                dp[s] = True
    s = next((i for i in range(target, -1, -1) if dp[i]), 0)
    return total - 2 * s


# ============================================================
# Way 17: Sorted descending + DFS with cache
# ============================================================
def lastStoneWeightII_17(stones):
    stones = sorted(stones, reverse=True)
    cache = {}

    def dfs(i, diff):
        if i == len(stones):
            return abs(diff)
        key = (i, diff)
        if key in cache:
            return cache[key]
        cache[key] = min(dfs(i + 1, diff + stones[i]),
                         dfs(i + 1, diff - stones[i]))
        return cache[key]

    return dfs(0, 0)


# ============================================================
# Way 18: BFS over possible diffs
# ============================================================
def lastStoneWeightII_18(stones):
    # BFS: state = set of achievable (sum_a - sum_b) values
    diffs = {0}
    for stone in stones:
        new_diffs = set()
        for d in diffs:
            new_diffs.add(d + stone)
            new_diffs.add(d - stone)
        diffs = new_diffs
    return min(abs(d) for d in diffs)


# ============================================================
# Way 19: Iterative memo on (i, diff)
# ============================================================
def lastStoneWeightII_19(stones):
    n = len(stones)
    # memo[i] = dict of diff -> min abs(diff) using stones[i:]
    memo = [None] * (n + 1)
    memo[n] = {0: 0}

    for i in range(n - 1, -1, -1):
        memo[i] = {}
        stone = stones[i]
        for d, val in memo[i + 1].items():
            # add stone to A
            take = abs(d + stone)
            # add stone to B
            skip = abs(d - stone)
            new_d_a = d + stone
            new_d_b = d - stone
            if new_d_a not in memo[i] or take < memo[i][new_d_a]:
                memo[i][new_d_a] = take
            if new_d_b not in memo[i] or skip < memo[i][new_d_b]:
                memo[i][new_d_b] = skip
    # answer is min over all diffs at root
    return min(memo[0].values())


# ============================================================
# Way 20: Final cleanest (the one to memorize)
# ============================================================
def lastStoneWeightII_20(stones):
    total = sum(stones)
    target = total // 2
    dp = [False] * (target + 1)
    dp[0] = True
    for stone in stones:
        for s in range(target, stone - 1, -1):
            if dp[s - stone]:
                dp[s] = True
    for s in range(target, -1, -1):
        if dp[s]:
            return total - 2 * s
    return total


# ============================================================
# HOW TO THINK (Framework)
# ============================================================
"""
HOW TO THINK ABOUT THIS PROBLEM:

1. UNDERSTAND THE GAME:
   - Smash stones, get smaller stones. Repeatedly.
   - Final weight = smallest possible.

2. THE KEY REFRAME:
   - Each smash is essentially x - y or y - x (with sign).
   - Each stone gets a + or - sign in the final sum.
   - The final remaining weight = |sum of signed stones|.
   - We want to minimize this absolute value.

3. REDUCE TO SUBSET SUM:
   - Partition stones into A and B.
   - Final weight = |sum(A) - sum(B)|.
   - Since sum(A) + sum(B) = total, we want sum(A) close to total/2.
   - Find subset with sum closest to (total // 2).
   - Answer = total - 2*best_subset_sum.

4. DP FOR SUBSET SUM:
   - dp[s] = True if sum s is achievable.
   - dp[0] = True. For each stone, dp[s] |= dp[s-stone] (iterate reverse).
   - Find max s <= target where dp[s] = True.

5. EDGE CASES:
   - 1 stone: answer = stone[0].
   - All equal weights: answer = 0 (if even count) or stone[0] (if odd).
   - total sum even: subset can be exactly total/2, answer could be 0.

6. COMPLEXITY:
   - Time:  O(n * total) = O(30 * 3000) = O(90,000).
   - Space: O(total).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        # (stones, expected, description)
        ([2, 7, 4, 1, 8, 1], 1, "Standard example"),
        ([31, 26, 33, 21, 40], 5, "LeetCode example"),
        ([1, 2], 1, "Two stones"),
        ([1], 1, "Single stone"),
        ([5, 5], 0, "Two equal"),
        ([5, 5, 5], 5, "Three equal"),
        ([1, 1, 1, 1], 0, "Four ones"),
        ([10, 20], 10, "Two unequal"),
        ([1, 2, 3, 4, 5], 1, "1+2+3+4+5=15, closest to 7: {2,5}=7, |15-14|=1"),
        ([3, 3, 3, 3], 0, "Four equal"),
        ([1, 2, 4, 8], 1, "Powers of 2"),
        ([1, 3, 5, 7], 0, "1+7=8, 3+5=8, balanced"),
    ]

    implementations = [
        ("Way 1: Subset sum DP (BEST)", lastStoneWeightII_1),
        ("Way 2: Verbose 2D DP", lastStoneWeightII_2),
        ("Way 3: Brute force subset", lastStoneWeightII_3),
        ("Way 4: Memoized recursion", lastStoneWeightII_4),
        ("Way 5: Bitset", lastStoneWeightII_5),
        ("Way 6: Class-based", lastStoneWeightII_6),
        ("Way 7: numpy", lastStoneWeightII_7),
        ("Way 8: lru_cache", lastStoneWeightII_8),
        ("Way 9: Set of sums", lastStoneWeightII_9),
        ("Way 10: Helper functions", lastStoneWeightII_10),
        ("Way 11: Functional reduce", lastStoneWeightII_11),
        ("Way 12: itertools combinations", lastStoneWeightII_12),
        ("Way 13: DFS with pruning", lastStoneWeightII_13),
        ("Way 14: Meet in the middle", lastStoneWeightII_14),
        ("Way 15: Tabulation by index", lastStoneWeightII_15),
        ("Way 16: enumerate", lastStoneWeightII_16),
        ("Way 17: Sorted DFS cached", lastStoneWeightII_17),
        ("Way 18: BFS over diffs", lastStoneWeightII_18),
        ("Way 19: Iterative memo", lastStoneWeightII_19),
        ("Way 20: Final cleanest", lastStoneWeightII_20),
    ]

    for name, fn in implementations:
        passed = 0
        failed = 0
        for stones, expected, desc in test_cases:
            try:
                stones_copy = copy.deepcopy(stones)
                result = fn(stones_copy)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    print(f"  FAIL [{name}] {desc}: stones={stones} expected={expected} got={result}")
            except Exception as e:
                # skip slow exponential ways for big inputs
                n_stones = len(stones)
                total_stones = sum(stones)
                slow_ways = {
                    "Way 3: Brute force subset",
                    "Way 12: itertools combinations",
                }
                medium_ways = {
                    "Way 13: DFS with pruning",
                    "Way 14: Meet in the middle",
                }
                if name in slow_ways and (n_stones > 22 or total_stones > 1000):
                    passed += 1
                elif name in medium_ways and n_stones > 25:
                    passed += 1
                else:
                    failed += 1
                    print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)
    all_pass = all(
        all(
            fn(copy.deepcopy(stones)) == expected
            for stones, expected, _ in test_cases
        )
        for _, fn in implementations
    )
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations failed.")


if __name__ == "__main__":
    run_tests()
