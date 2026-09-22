"""
Delete and Earn
Medium | 30 min

Given an integer array nums, you can perform the following operation any
number of times:
- Pick an element nums[i] and earn nums[i] points.
- Then delete ALL elements with value nums[i] - 1 or nums[i] + 1 (these
  earn no points).

Return the maximum number of points you can earn.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/delete-and-earn

Examples:
    nums=[3,4,2] -> 6 (delete 4 to earn 4, then 2 gives 2, total 6? Or
                     delete 3+2=5? Let's think: pick 3 -> delete 2 and 4,
                     earn 3. Then no more. Total 3. Pick 4 -> delete 3,
                     earn 4. Then 2 gives 2. Total 6. Pick 2 -> delete 3,
                     earn 2. Then 4 gives 4. Total 6. So 6.)
    nums=[2,2,3,3,3] -> 6 (delete all 3's, earn 9? but 2 is +/-1 of 3 so
                          also deleted, no 2's earned. Hmm let me re-read.
                          Actually deleting 3 also deletes 2's. So:
                          Pick 3 -> delete 2, 4. Earn 3. Repeat for other 3's:
                          3+3+3 = 9. But all 2's are gone. Total 9.
                          Pick 2 -> delete 1, 3. Earn 2 + 2 = 4. But all 3's
                          gone. Total 4.
                          So 9 is better.)
                          Expected = 9.
    nums=[1,1,1,2,2,3,3,3,3,4] -> ?
                          Pick 3 -> earn 3*4 = 12, deletes 2, 4.
                          Remaining: 1, 1, 1. Pick 1 -> earn 3, deletes 0, 2.
                          Total = 12 + 3 = 15.

Constraints:
- 1 <= nums.length <= 2 * 10^4
- 1 <= nums[i] <= 10^4

KEY INSIGHT:
This is the HOUSE ROBBER problem in disguise!
- Count total points for each value v: points[v] = v * count(nums, v).
- We can't pick adjacent values (picking v deletes v-1 and v+1).
- So maximize sum of points[v] such that no two chosen v are adjacent.
- That's House Robber on the array points[0..max(nums)].
"""


# =============================================================================
# WAY 1: Points array + House Robber DP (BEST - Memorize!)
# =============================================================================
def delete_and_earn_1(nums):
    """Reduce to House Robber."""
    if not nums:
        return 0
    max_n = max(nums)
    points = [0] * (max_n + 1)
    for x in nums:
        points[x] += x
    # House Robber: rob[i] = max(rob[i-1], rob[i-2] + points[i])
    rob_prev_2 = 0
    rob_prev_1 = 0
    for i in range(max_n + 1):
        cur = max(rob_prev_1, rob_prev_2 + points[i])
        rob_prev_2 = rob_prev_1
        rob_prev_1 = cur
    return rob_prev_1


# =============================================================================
# WAY 2: House Robber DP with full array
# =============================================================================
def delete_and_earn_2(nums):
    if not nums:
        return 0
    max_n = max(nums)
    points = [0] * (max_n + 1)
    for x in nums:
        points[x] += x
    rob = [0] * (max_n + 1)
    rob[0] = points[0]
    for i in range(1, max_n + 1):
        rob[i] = max(rob[i - 1], rob[i - 2] + points[i])
    return rob[max_n]


# =============================================================================
# WAY 3: Compact DP with prev values
# =============================================================================
def delete_and_earn_3(nums):
    if not nums:
        return 0
    max_n = max(nums)
    points = [0] * (max_n + 1)
    for x in nums:
        points[x] += x
    prev2, prev1 = 0, 0
    for p in points:
        prev2, prev1 = prev1, max(prev1, prev2 + p)
    return prev1


# =============================================================================
# WAY 4: Use Counter for points
# =============================================================================
def delete_and_earn_4(nums):
    from collections import Counter
    if not nums:
        return 0
    cnt = Counter(nums)
    max_n = max(nums)
    points = [0] * (max_n + 1)
    for k, v in cnt.items():
        points[k] = k * v
    prev2, prev1 = 0, 0
    for p in points:
        prev2, prev1 = prev1, max(prev1, prev2 + p)
    return prev1


# =============================================================================
# WAY 5: Sort + DP with dict
# =============================================================================
def delete_and_earn_5(nums):
    if not nums:
        return 0
    points = {}
    for x in nums:
        points[x] = points.get(x, 0) + x
    keys = sorted(points.keys())
    prev2, prev1 = 0, 0
    prev_key = None
    for k in keys:
        if prev_key is None or k > prev_key + 1:
            cur = prev1 + points[k]
        else:
            cur = max(prev1, prev2 + points[k])
        prev2 = prev1
        prev1 = cur
        prev_key = k
    return prev1


# =============================================================================
# WAY 6: Sort + DP using tuple
# =============================================================================
def delete_and_earn_6(nums):
    if not nums:
        return 0
    points = {}
    for x in nums:
        points[x] = points.get(x, 0) + x
    sorted_keys = sorted(points.items())  # list of (k, v)
    n = len(sorted_keys)
    if n == 0:
        return 0
    rob = [0] * (n + 1)
    rob[0] = 0
    # i indexes sorted_keys[i-1] (use 1-indexed rob for clarity)
    for i in range(1, n + 1):
        k, v = sorted_keys[i - 1]
        # Skip key i: rob[i-1]
        skip = rob[i - 1]
        # Take key i (value v): combine with rob[i-2] only if prev key was k-1 (adjacent).
        # If not adjacent (or i==1), can always take with rob[i-1] skip state.
        if i >= 2 and sorted_keys[i - 2][0] == k - 1:
            take = rob[i - 2] + v
        else:
            take = rob[i - 1] + v
        rob[i] = max(skip, take)
    return rob[n]


# =============================================================================
# WAY 7: Brute force (try all subsets)
# =============================================================================
def delete_and_earn_7(nums):
    """Try all subsets - exponential."""
    from itertools import combinations
    n = len(nums)
    best = 0
    # For each subset, check validity and compute score
    for r in range(n + 1):
        for subset in combinations(nums, r):
            subset_set = set(subset)
            valid = True
            for x in subset:
                if (x - 1) in subset_set or (x + 1) in subset_set:
                    valid = False
                    break
            if valid:
                best = max(best, sum(subset))
    return best


# =============================================================================
# WAY 8: Recursive memoization
# =============================================================================
def delete_and_earn_8(nums):
    if not nums:
        return 0
    from functools import lru_cache
    max_n = max(nums)
    points = [0] * (max_n + 1)
    for x in nums:
        points[x] += x

    @lru_cache(maxsize=None)
    def rob(i):
        if i < 0:
            return 0
        return max(rob(i - 1), rob(i - 2) + points[i])

    return rob(max_n)


# =============================================================================
# WAY 9: Class OOP
# =============================================================================
class DeleteAndEarn:
    def __init__(self, nums):
        self.nums = nums

    def solve(self):
        if not self.nums:
            return 0
        max_n = max(self.nums)
        points = [0] * (max_n + 1)
        for x in self.nums:
            points[x] += x
        prev2, prev1 = 0, 0
        for p in points:
            prev2, prev1 = prev1, max(prev1, prev2 + p)
        return prev1


def delete_and_earn_9(nums):
    return DeleteAndEarn(nums).solve()


# =============================================================================
# WAY 10: O(max_n) DP using skip/take state per index
# =============================================================================
def delete_and_earn_10(nums):
    """For each i: rob[i] = max(rob[i-1], rob[i-2] + points[i])."""
    if not nums:
        return 0
    max_n = max(nums)
    points = [0] * (max_n + 1)
    for x in nums:
        points[x] += x
    # Use skip[i], take[i] states
    skip = 0
    take = 0
    for i in range(max_n + 1):
        new_skip = max(skip, take)
        new_take = skip + points[i]
        skip, take = new_skip, new_take
    return max(skip, take)


# =============================================================================
# WAY 11: Using defaultdict
# =============================================================================
def delete_and_earn_11(nums):
    from collections import defaultdict
    if not nums:
        return 0
    points = defaultdict(int)
    for x in nums:
        points[x] += x
    keys = sorted(points.keys())
    prev2, prev1 = 0, 0
    prev_key = None
    for k in keys:
        if prev_key is None or k != prev_key + 1:
            cur = prev1 + points[k]
        else:
            cur = max(prev1, prev2 + points[k])
        prev2, prev1 = prev1, cur
        prev_key = k
    return prev1


# =============================================================================
# WAY 12: Numpy House Robber
# =============================================================================
def delete_and_earn_12(nums):
    import numpy as np
    if not nums:
        return 0
    max_n = max(nums)
    points = np.zeros(max_n + 1, dtype=np.int64)
    for x in nums:
        points[x] += x
    rob = np.zeros(max_n + 1, dtype=np.int64)
    rob[0] = points[0]
    for i in range(1, max_n + 1):
        rob[i] = max(rob[i - 1], (rob[i - 2] if i >= 2 else 0) + points[i])
    return int(rob[max_n])


# =============================================================================
# WAY 13: Sort + iterate merging
# =============================================================================
def delete_and_earn_13(nums):
    """Sort and group by value, then DP."""
    if not nums:
        return 0
    sorted_nums = sorted(nums)
    # Group by value
    groups = []
    i = 0
    while i < len(sorted_nums):
        j = i
        while j < len(sorted_nums) and sorted_nums[j] == sorted_nums[i]:
            j += 1
        groups.append((sorted_nums[i], sorted_nums[i] * (j - i)))
        i = j
    # DP on groups
    prev2, prev1 = 0, 0
    prev_val = None
    for val, pts in groups:
        if prev_val is None or val > prev_val + 1:
            cur = prev1 + pts
        else:
            cur = max(prev1, prev2 + pts)
        prev2 = prev1
        prev1 = cur
        prev_val = val
    return prev1


# =============================================================================
# WAY 14: Iterative with state (not picking / picking)
# =============================================================================
def delete_and_earn_14(nums):
    if not nums:
        return 0
    max_n = max(nums)
    points = [0] * (max_n + 1)
    for x in nums:
        points[x] += x
    # skip[i] = max points in points[0..i] not including i
    # take[i] = max points in points[0..i] including i
    skip = 0
    take = points[0] if max_n >= 0 else 0
    for i in range(1, max_n + 1):
        new_skip = max(skip, take)
        new_take = skip + points[i]
        skip, take = new_skip, new_take
    return max(skip, take)


# =============================================================================
# WAY 15: With list of distinct values
# =============================================================================
def delete_and_earn_15(nums):
    if not nums:
        return 0
    points = {}
    for x in nums:
        points[x] = points.get(x, 0) + x
    sorted_keys = sorted(points.keys())
    # dp[i] = max earning considering first i keys
    dp = [0] * (len(sorted_keys) + 1)
    for i in range(1, len(sorted_keys) + 1):
        k = sorted_keys[i - 1]
        if i >= 2 and sorted_keys[i - 2] == k - 1:
            dp[i] = max(dp[i - 1], dp[i - 2] + points[k])
        else:
            dp[i] = dp[i - 1] + points[k]
    return dp[-1]


# =============================================================================
# WAY 16: Reduction to House Robber
# =============================================================================
def delete_and_earn_16(nums):
    """Explicit House Robber on sorted values."""
    if not nums:
        return 0
    points = {}
    for x in nums:
        points[x] = points.get(x, 0) + x
    keys = sorted(points.keys())
    # Map to house robber: each key is a house with value points[key].
    # Adjacent keys (k, k+1) are connected.
    n = len(keys)
    if n == 0:
        return 0
    if n == 1:
        return points[keys[0]]
    rob = [0] * n
    rob[0] = points[keys[0]]
    rob[1] = max(points[keys[0]], points[keys[1]]) if keys[1] == keys[0] + 1 else points[keys[0]] + points[keys[1]]
    for i in range(2, n):
        if keys[i] == keys[i - 1] + 1:
            rob[i] = max(rob[i - 1], rob[i - 2] + points[keys[i]])
        else:
            rob[i] = rob[i - 1] + points[keys[i]]
    return rob[n - 1]


# =============================================================================
# WAY 17: Memoization with explicit dict
# =============================================================================
def delete_and_earn_17(nums):
    if not nums:
        return 0
    points = {}
    for x in nums:
        points[x] = points.get(x, 0) + x
    keys = sorted(points.keys())
    memo = {-1: 0}

    def solve(i):
        if i in memo:
            return memo[i]
        skip = solve(i - 1)
        if i == 0 or keys[i] > keys[i - 1] + 1:
            take = solve(i - 1) + points[keys[i]]
        else:
            take = solve(i - 2) + points[keys[i]]
        memo[i] = max(skip, take)
        return memo[i]

    return solve(len(keys) - 1)


# =============================================================================
# WAY 18: Use heapq
# =============================================================================
def delete_and_earn_18(nums):
    if not nums:
        return 0
    points = {}
    for x in nums:
        points[x] = points.get(x, 0) + x
    keys = sorted(points.keys())
    # Standard DP
    prev2, prev1 = 0, 0
    for k in keys:
        v = points[k]
        # Check if k-1 is in our sorted list... but we iterate sorted, so
        # we need to know if previous key was k-1.
        # Since we iterate in order, the previous key is the previous element.
        # So we need to track prev_key.
        pass
    # Actually let me redo this with a cleaner approach:
    prev2, prev1 = 0, 0
    prev_key = -2  # so first iteration doesn't think prev_key + 1 == current
    for k in keys:
        v = points[k]
        if k == prev_key + 1:
            cur = max(prev1, prev2 + v)
        else:
            cur = prev1 + v
        prev2 = prev1
        prev1 = cur
        prev_key = k
    return prev1


# =============================================================================
# WAY 19: Pick elements greedily by frequency
# =============================================================================
def delete_and_earn_19(nums):
    """Doesn't work correctly for all cases. Educational only."""
    from collections import Counter
    cnt = Counter(nums)
    keys = sorted(cnt.keys())
    prev2, prev1 = 0, 0
    prev_key = None
    for k in keys:
        v = k * cnt[k]
        if prev_key is None or k != prev_key + 1:
            cur = prev1 + v
        else:
            cur = max(prev1, prev2 + v)
        prev2 = prev1
        prev1 = cur
        prev_key = k
    return prev1


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def delete_and_earn_20(nums):
    """
    THE ONE TO MEMORIZE.

    Reduction to House Robber:
    1. Count total points per value: points[v] = v * count(v).
    2. The constraint "can't pick v-1 and v together" makes this House
       Robber on the points array.
    3. rob[i] = max(rob[i-1], rob[i-2] + points[i]).

    Time:  O(n + max(nums)).
    Space: O(max(nums)).
    """
    if not nums:
        return 0
    max_n = max(nums)
    points = [0] * (max_n + 1)
    for x in nums:
        points[x] += x
    prev2, prev1 = 0, 0
    for p in points:
        prev2, prev1 = prev1, max(prev1, prev2 + p)
    return prev1


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to maximize points by picking elements. Picking value v gives v
points but deletes all v-1 and v+1 (which give no points)."

Key Insight:
"This is the HOUSE ROBBER problem in disguise!
- Let points[v] = v * count(v in nums). Total points for value v.
- Picking v forbids picking v-1 and v+1.
- So I want max sum of points[v] such that no two chosen v are adjacent.
- This is exactly House Robber on the points array."

Algorithm:
1. Compute points[v] for each value v.
2. Apply House Robber DP: rob[i] = max(rob[i-1], rob[i-2] + points[i]).
3. Return rob(max_n).

Edge Cases:
- Empty nums: 0.
- All same value: sum of all elements.
- No adjacent values: sum of all elements.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| Best     | O(n+M) | O(M)   |
| Brute    | O(2^n) | O(n)   |
+----------+--------+--------+
M = max(nums). With M up to 10^4, this is efficient.

KEY TRICK:
Counting points per value transforms the problem into House Robber.
The House Robber DP is classic.

RELATED PROBLEMS:
- House Robber (LC 198).
- House Robber II (LC 213): circular.
- Maximum sum of non-adjacent elements.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Points array + DP (BEST)", delete_and_earn_1),
        ("Way 2: Full DP array", delete_and_earn_2),
        ("Way 3: Compact DP", delete_and_earn_3),
        ("Way 4: Counter", delete_and_earn_4),
        ("Way 5: Sort + dict DP", delete_and_earn_5),
        ("Way 6: Sort + tuple DP", delete_and_earn_6),
        ("Way 7: Brute force subsets", delete_and_earn_7),
        ("Way 8: Recursive memo", delete_and_earn_8),
        ("Way 9: Class OOP", delete_and_earn_9),
        ("Way 10: Bitmask DP", delete_and_earn_10),
        ("Way 11: defaultdict", delete_and_earn_11),
        ("Way 12: Numpy", delete_and_earn_12),
        ("Way 13: Sort + group", delete_and_earn_13),
        ("Way 14: Skip/take state", delete_and_earn_14),
        ("Way 15: Distinct values", delete_and_earn_15),
        ("Way 16: House Robber explicit", delete_and_earn_16),
        ("Way 17: Memo dict", delete_and_earn_17),
        ("Way 18: Sort + DP clean", delete_and_earn_18),
        ("Way 19: Counter greedy-like", delete_and_earn_19),
        ("Way 20: Final cleanest", delete_and_earn_20),
    ]

    test_cases = [
        # (nums, expected)
        ([3, 4, 2], 6),
        ([2, 2, 3, 3, 3], 9),
        ([1, 1, 1, 2, 2, 3, 3, 3, 3, 4], 15),
        ([1, 2, 3], 4),
        ([1, 2, 3, 3, 3], 10),  # 3*3 + 1 = 10
        ([1], 1),
        ([2, 2], 4),
        ([2, 3, 4], 6),
        ([1, 2, 3, 4, 5], 9),
        ([1, 5, 1, 5], 12),  # 2*1 + 2*5 = 12
        ([1, 2, 1, 2], 4),  # points[1]=2, points[2]=4, House Robber = 4
        ([2, 2, 2], 6),
        ([], 0),
        ([5, 5, 5, 5, 5], 25),
    ]

    print("=" * 70)
    print("DELETE AND EARN - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/delete-and-earn")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for nums, expected in test_cases:
            try:
                result = func(nums[:])
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: nums={nums}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: nums={nums}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)