"""
Target Sum
Medium | 30 min

Given an integer array nums and an integer target, assign either + or -
to each element. Return the count of assignments where signed sum equals target.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/target-sum

Examples:
    nums=[1,1,1,1,1], target=3 -> 5
    nums=[1], target=1 -> 1
    nums=[1,0], target=1 -> 2  (assign + to both, or + to 1 and - to 0)
                              # Actually: +1+0=1, +1-0=1, -1+0=-1, -1-0=-1. Two ways.

Constraints:
- 1 <= nums.length <= 20
- 0 <= nums[i] <= 1000
- 0 <= sum(nums) <= 1000
- -1000 <= target <= 1000

KEY INSIGHT:
Let P = set of positively-signed indices, N = negatively-signed indices.
sum(P) - sum(N) = target
sum(P) + sum(N) = total
=> 2*sum(P) = target + total
=> sum(P) = (target + total) / 2

So we count subsets of nums that sum to (target + total) / 2.
This is the classic "count subsets with target sum" problem.
If (target + total) is odd or negative, return 0.
"""


# =============================================================================
# WAY 1: Subset-sum DP (BEST - Memorize!)
# =============================================================================
def target_sum_1(nums, target):
    """Count subsets with sum = (target + total) / 2."""
    total = sum(nums)
    if (target + total) % 2 != 0 or target + total < 0:
        return 0
    s = (target + total) // 2
    # dp[j] = # of subsets with sum j using elements considered so far
    dp = [0] * (s + 1)
    dp[0] = 1
    for x in nums:
        for j in range(s, x - 1, -1):
            dp[j] += dp[j - x]
    return dp[s]


# =============================================================================
# WAY 2: Subset-sum with 2D DP
# =============================================================================
def target_sum_2(nums, target):
    total = sum(nums)
    if (target + total) % 2 != 0 or target + total < 0:
        return 0
    s = (target + total) // 2
    n = len(nums)
    dp = [[0] * (s + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = 1
    for i in range(1, n + 1):
        for j in range(s + 1):
            dp[i][j] = dp[i - 1][j]
            if j >= nums[i - 1]:
                dp[i][j] += dp[i - 1][j - nums[i - 1]]
    return dp[n][s]


# =============================================================================
# WAY 3: DFS with memoization
# =============================================================================
def target_sum_3(nums, target):
    from functools import lru_cache
    n = len(nums)

    @lru_cache(maxsize=None)
    def dfs(i, cur):
        if i == n:
            return 1 if cur == target else 0
        return dfs(i + 1, cur + nums[i]) + dfs(i + 1, cur - nums[i])

    return dfs(0, 0)


# =============================================================================
# WAY 4: Brute force 2^n
# =============================================================================
def target_sum_4(nums, target):
    n = len(nums)
    count = 0
    for mask in range(1 << n):
        s = 0
        for i in range(n):
            if mask & (1 << i):
                s += nums[i]
            else:
                s -= nums[i]
        if s == target:
            count += 1
    return count


# =============================================================================
# WAY 5: Subset-sum with Counter (handle zero elements)
# =============================================================================
def target_sum_5(nums, target):
    total = sum(nums)
    if (target + total) % 2 != 0 or target + total < 0:
        return 0
    s = (target + total) // 2
    dp = {0: 1}
    for x in nums:
        new_dp = dict(dp)
        for j, c in dp.items():
            new_dp[j + x] = new_dp.get(j + x, 0) + c
        dp = new_dp
    return dp.get(s, 0)


# =============================================================================
# WAY 6: DFS iterative with stack
# =============================================================================
def target_sum_6(nums, target):
    n = len(nums)
    stack = [(0, 0)]
    count = 0
    while stack:
        i, cur = stack.pop()
        if i == n:
            if cur == target:
                count += 1
            continue
        stack.append((i + 1, cur + nums[i]))
        stack.append((i + 1, cur - nums[i]))
    return count


# =============================================================================
# WAY 7: Subset-sum DP compact
# =============================================================================
def target_sum_7(nums, target):
    total = sum(nums)
    if (target + total) % 2 != 0 or target + total < 0:
        return 0
    s = (target + total) // 2
    dp = [1] + [0] * s
    for x in nums:
        for j in range(s, x - 1, -1):
            dp[j] += dp[j - x]
    return dp[s]


# =============================================================================
# WAY 8: Meet-in-the-middle
# =============================================================================
def target_sum_8(nums, target):
    """Split into two halves. For each half, enumerate all signed sums."""
    from collections import Counter
    n = len(nums)
    mid = n // 2
    left = nums[:mid]
    right = nums[mid:]

    def signed_sums(arr):
        from itertools import product
        sums = Counter()
        for signs in product([1, -1], repeat=len(arr)):
            s = sum(x * sign for x, sign in zip(arr, signs))
            sums[s] += 1
        return sums

    sums_left = signed_sums(left)
    sums_right = signed_sums(right)
    count = 0
    for sl, cl in sums_left.items():
        count += cl * sums_right.get(target - sl, 0)
    return count


# =============================================================================
# WAY 9: Class OOP
# =============================================================================
class TargetSumCounter:
    def __init__(self, nums, target):
        self.nums = nums
        self.target = target

    def count(self):
        total = sum(self.nums)
        if (self.target + total) % 2 != 0 or self.target + total < 0:
            return 0
        s = (self.target + total) // 2
        dp = [1] + [0] * s
        for x in self.nums:
            for j in range(s, x - 1, -1):
                dp[j] += dp[j - x]
        return dp[s]


def target_sum_9(nums, target):
    return TargetSumCounter(nums, target).count()


# =============================================================================
# WAY 10: Recursive without memo
# =============================================================================
def target_sum_10(nums, target):
    def dfs(i, cur):
        if i == len(nums):
            return 1 if cur == target else 0
        return dfs(i + 1, cur + nums[i]) + dfs(i + 1, cur - nums[i])
    return dfs(0, 0)


# =============================================================================
# WAY 11: Numpy DP
# =============================================================================
def target_sum_11(nums, target):
    import numpy as np
    total = sum(nums)
    if (target + total) % 2 != 0 or target + total < 0:
        return 0
    s = (target + total) // 2
    dp = np.zeros(s + 1, dtype=np.int64)
    dp[0] = 1
    for x in nums:
        # Shift dp to the right by x positions
        shifted = np.zeros(s + 1, dtype=np.int64)
        if x <= s:
            shifted[x:] = dp[:s + 1 - x]
        dp = dp + shifted
    return int(dp[s])


# =============================================================================
# WAY 12: Subset-sum DP with explicit if (instead of check)
# =============================================================================
def target_sum_12(nums, target):
    total = sum(nums)
    if (target + total) % 2 != 0 or target + total < 0:
        return 0
    s = (target + total) // 2
    dp = [0] * (s + 1)
    dp[0] = 1
    for x in nums:
        for j in range(s, x - 1, -1):
            dp[j] = dp[j] + dp[j - x]
    return dp[s]


# =============================================================================
# WAY 13: Top-down memo on (i, cur) with dict
# =============================================================================
def target_sum_13(nums, target):
    memo = {}

    def dfs(i, cur):
        if (i, cur) in memo:
            return memo[(i, cur)]
        if i == len(nums):
            memo[(i, cur)] = 1 if cur == target else 0
            return memo[(i, cur)]
        memo[(i, cur)] = dfs(i + 1, cur + nums[i]) + dfs(i + 1, cur - nums[i])
        return memo[(i, cur)]

    return dfs(0, 0)


# =============================================================================
# WAY 14: Subset-sum using defaultdict
# =============================================================================
def target_sum_14(nums, target):
    from collections import defaultdict
    total = sum(nums)
    if (target + total) % 2 != 0 or target + total < 0:
        return 0
    s = (target + total) // 2
    dp = defaultdict(int)
    dp[0] = 1
    for x in nums:
        new_dp = defaultdict(int)
        for j, c in dp.items():
            new_dp[j] += c
            new_dp[j + x] += c
        dp = new_dp
    return dp.get(s, 0)


# =============================================================================
# WAY 15: 2D DP with tuple keys
# =============================================================================
def target_sum_15(nums, target):
    n = len(nums)
    dp = {(0, 0): 1}
    for i in range(n):
        new_dp = {}
        for (j, cur), c in dp.items():
            new_dp[(j + 1, cur + nums[i])] = new_dp.get((j + 1, cur + nums[i]), 0) + c
            new_dp[(j + 1, cur - nums[i])] = new_dp.get((j + 1, cur - nums[i]), 0) + c
        dp = new_dp
    return sum(c for (j, cur), c in dp.items() if j == n and cur == target)


# =============================================================================
# WAY 16: BFS over (i, cur) states
# =============================================================================
def target_sum_16(nums, target):
    """BFS: count number of paths to (n, target)."""
    from collections import defaultdict
    cur_counts = defaultdict(int)
    cur_counts[0] = 1
    for x in nums:
        new_counts = defaultdict(int)
        for cur, c in cur_counts.items():
            new_counts[cur + x] += c
            new_counts[cur - x] += c
        cur_counts = new_counts
    return cur_counts.get(target, 0)


# =============================================================================
# WAY 17: Subset-sum with roll/shift
# =============================================================================
def target_sum_17(nums, target):
    total = sum(nums)
    if (target + total) % 2 != 0 or target + total < 0:
        return 0
    s = (target + total) // 2
    # dp[j] = # of subsets summing to j
    dp = [0] * (s + 1)
    dp[0] = 1
    for x in nums:
        # Iterate in reverse to avoid double-counting
        for j in range(s, x - 1, -1):
            dp[j] += dp[j - x]
    return dp[s]


# =============================================================================
# WAY 18: Brute force with itertools
# =============================================================================
def target_sum_18(nums, target):
    from itertools import product
    count = 0
    for signs in product([1, -1], repeat=len(nums)):
        s = sum(x * sign for x, sign in zip(nums, signs))
        if s == target:
            count += 1
    return count


# =============================================================================
# WAY 19: Recursive with explicit memo via closure
# =============================================================================
def target_sum_19(nums, target):
    memo = {}

    def helper(i, cur):
        if i == len(nums):
            return 1 if cur == target else 0
        key = (i, cur)
        if key in memo:
            return memo[key]
        memo[key] = helper(i + 1, cur + nums[i]) + helper(i + 1, cur - nums[i])
        return memo[key]

    return helper(0, 0)


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def target_sum_20(nums, target):
    """
    THE ONE TO MEMORIZE.

    Reduce to subset-sum:
      sum(P) - sum(N) = target
      sum(P) + sum(N) = total
      => sum(P) = (target + total) / 2

    Count subsets of nums with sum = (target + total) / 2.

    Time:  O(n * S) where S = (target + total) / 2.
    Space: O(S).
    """
    total = sum(nums)
    if (target + total) % 2 != 0 or target + total < 0:
        return 0
    s = (target + total) // 2
    dp = [1] + [0] * s
    for x in nums:
        for j in range(s, x - 1, -1):
            dp[j] += dp[j - x]
    return dp[s]


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to count + / - assignments to nums that sum to target."

Key Insight:
"Reduction to subset sum. Let P = positive-signed indices, N = negative.
  sum(P) - sum(N) = target
  sum(P) + sum(N) = total
=> sum(P) = (target + total) / 2

So I count subsets of nums that sum to (target + total) / 2."

Algorithm:
1. Compute total = sum(nums).
2. If (target + total) is odd or negative, return 0.
3. s = (target + total) / 2.
4. Subset-sum DP: dp[j] = # of subsets with sum j.
   Iterate x in nums:
     for j from s down to x: dp[j] += dp[j - x]
5. Return dp[s].

Edge Cases:
- target > total or target < -total: 0.
- nums has zeros: each zero doubles the count.
- Empty nums: target == 0 -> 1, else 0.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| Subset DP| O(nS)  | O(S)   |
| Brute    | O(2^n) | O(n)   |
| Meet-mid | O(2^(n/2)) | O(2^(n/2)) |
+----------+--------+--------+
S = (target + total) / 2.

KEY TRICK:
Algebraic reduction: 2 equations, 2 unknowns (sum(P), sum(N)). Solves
the problem analytically before counting.

RELATED PROBLEMS:
- Partition Equal Subset Sum (LC 416).
- Subset Sum (gfg).
- Last Stone Weight II (LC 1049).
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Subset-sum DP (BEST)", target_sum_1),
        ("Way 2: 2D DP", target_sum_2),
        ("Way 3: DFS memo", target_sum_3),
        ("Way 4: Brute 2^n", target_sum_4),
        ("Way 5: Subset Counter", target_sum_5),
        ("Way 6: DFS iterative", target_sum_6),
        ("Way 7: Subset compact", target_sum_7),
        ("Way 8: Meet-in-middle", target_sum_8),
        ("Way 9: Class OOP", target_sum_9),
        ("Way 10: Recursive no memo", target_sum_10),
        ("Way 11: Numpy DP", target_sum_11),
        ("Way 12: Subset explicit", target_sum_12),
        ("Way 13: Top-down dict memo", target_sum_13),
        ("Way 14: Subset defaultdict", target_sum_14),
        ("Way 15: 2D tuple keys", target_sum_15),
        ("Way 16: BFS states", target_sum_16),
        ("Way 17: Subset roll", target_sum_17),
        ("Way 18: Brute itertools", target_sum_18),
        ("Way 19: Memo closure", target_sum_19),
        ("Way 20: Final cleanest", target_sum_20),
    ]

    test_cases = [
        # (nums, target, expected)
        ([1, 1, 1, 1, 1], 3, 5),
        ([1], 1, 1),
        ([1, 0], 1, 2),
        ([1], -1, 1),
        ([0, 0, 0, 0, 0], 0, 32),  # 2^5 = 32 ways
        ([1, 2, 3], 0, 2),  # 1+2-3=0, -1-2+3=0
        ([1, 2, 3], 6, 1),  # all positive
        ([1, 2, 3], -6, 1),  # all negative
        ([1, 2, 3], 4, 1),  # 1+3=4
        ([100], -100, 1),
        ([1, 2, 7, 9, 9, 9], 3, 3),  # 3 ways: {7,9}*3
        ([2, 7, 4, 3, 1], 5, 2),  # {7,4} or {7,3,1}
        ([1, 1, 2, 2], 0, 4),
        ([], 0, 1),
        ([], 1, 0),
        ([5, 2, 1, 3], 4, 0),  # odd sum → 0
    ]

    print("=" * 70)
    print("TARGET SUM - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/target-sum")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for nums, target, expected in test_cases:
            try:
                result = func(nums[:], target)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: nums={nums}, target={target}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: nums={nums}, target={target}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)