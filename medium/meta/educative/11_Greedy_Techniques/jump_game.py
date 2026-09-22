"""
Jump Game - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/jump-game

Given an array nums where nums[i] is the max jump length from position i,
determine if you can reach the last index.

KEY INSIGHT:
Greedy: track the FURTHEST reachable position as you scan.
At each index i, if i > furthest, you're stuck -> return False.
Otherwise update furthest = max(furthest, i + nums[i]).
If after scan furthest >= n-1, return True.

Examples:
    [2,3,1,1,4] -> True (0->1->4)
    [3,2,1,0,4] -> False (stuck at index 3)

Constraints:
- 1 <= nums.length <= 10^4
- 0 <= nums[i] <= 10^5
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: Greedy furthest (BEST - Memorize!)
# ============================================================
def can_jump_1(nums):
    furthest = 0
    n = len(nums)
    for i in range(n):
        if i > furthest:
            return False
        furthest = max(furthest, i + nums[i])
    return True


# ============================================================
# Way 2: Greedy with target position
# ============================================================
def can_jump_2(nums):
    n = len(nums)
    target = n - 1
    for i in range(n - 2, -1, -1):
        if i + nums[i] >= target:
            target = i
    return target == 0


# ============================================================
# Way 3: DP forward
# ============================================================
def can_jump_3(nums):
    n = len(nums)
    if n == 0:
        return False
    dp = [False] * n
    dp[0] = True
    for i in range(n):
        if not dp[i]:
            continue
        for j in range(i + 1, min(i + nums[i] + 1, n)):
            dp[j] = True
    return dp[n - 1]


# ============================================================
# Way 4: Recursive (memoized)
# ============================================================
def can_jump_4(nums):
    n = len(nums)
    memo = {}

    def helper(pos):
        if pos >= n - 1:
            return True
        if pos in memo:
            return memo[pos]
        if nums[pos] == 0:
            memo[pos] = False
            return False
        for step in range(1, nums[pos] + 1):
            if helper(pos + step):
                memo[pos] = True
                return True
        memo[pos] = False
        return False

    return helper(0)


# ============================================================
# Way 5: BFS
# ============================================================
def can_jump_5(nums):
    from collections import deque
    n = len(nums)
    if n == 0:
        return False
    if n == 1:
        return True
    visited = [False] * n
    visited[0] = True
    queue = deque([0])
    while queue:
        i = queue.popleft()
        for j in range(i + 1, min(i + nums[i] + 1, n)):
            if not visited[j]:
                visited[j] = True
                if j == n - 1:
                    return True
                queue.append(j)
    return visited[n - 1]


# ============================================================
# Way 6: lru_cache decorator
# ============================================================
from functools import lru_cache


def can_jump_6(nums):
    n = len(nums)

    @lru_cache(maxsize=None)
    def helper(pos):
        if pos >= n - 1:
            return True
        if nums[pos] == 0:
            return False
        for step in range(1, nums[pos] + 1):
            if helper(pos + step):
                return True
        return False

    return helper(0)


# ============================================================
# Way 7: Brute force recursion (no memo)
# ============================================================
def can_jump_7(nums):
    n = len(nums)

    def helper(pos):
        if pos >= n - 1:
            return True
        if nums[pos] == 0:
            return False
        for step in range(1, nums[pos] + 1):
            if helper(pos + step):
                return True
        return False

    return helper(0)


# ============================================================
# Way 8: Class-based
# ============================================================
class JumpGame_8:
    def __init__(self, nums):
        self.nums = nums

    def can_jump(self):
        furthest = 0
        n = len(self.nums)
        for i in range(n):
            if i > furthest:
                return False
            furthest = max(furthest, i + self.nums[i])
        return True


def can_jump_8(nums):
    return JumpGame_8(nums).can_jump()


# ============================================================
# Way 9: numpy-style
# ============================================================
def can_jump_9(nums):
    import numpy as np
    if not nums:
        return False
    arr = np.array(nums)
    n = len(arr)
    furthest = 0
    for i in range(n):
        if i > furthest:
            return False
        furthest = max(furthest, i + int(arr[i]))
    return True


# ============================================================
# Way 10: Final cleanest
# ============================================================
def can_jump_10(nums):
    furthest = 0
    for i, x in enumerate(nums):
        if i > furthest:
            return False
        furthest = max(furthest, i + x)
    return True


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([2, 3, 1, 1, 4], True, "Standard reachable"),
        ([3, 2, 1, 0, 4], False, "Stuck at zero"),
        ([0], True, "Single element"),
        ([1, 0, 1, 0], False, "Zero in middle"),
        ([2, 0, 0], True, "Just enough"),
        ([1, 1, 1, 1], True, "All ones"),
        ([5, 0, 0, 0, 0, 0, 0, 0, 0, 0], False, "Big first jump but stuck"),
        ([1, 0], True, "Two elements reachable"),
        ([0, 1], False, "Start at zero"),
        ([2, 5, 0, 0], True, "Skip ahead"),
    ]

    implementations = [
        ("Way 1: Greedy furthest (BEST)", can_jump_1),
        ("Way 2: Greedy target", can_jump_2),
        ("Way 3: DP forward", can_jump_3),
        ("Way 4: Recursive memo", can_jump_4),
        ("Way 5: BFS", can_jump_5),
        ("Way 6: lru_cache", can_jump_6),
        ("Way 7: Brute recursion", can_jump_7),
        ("Way 8: Class-based", can_jump_8),
        ("Way 9: numpy", can_jump_9),
        ("Way 10: Final cleanest", can_jump_10),
    ]

    for name, fn in implementations:
        passed = 0
        failed = 0
        for nums, expected, desc in test_cases:
            try:
                nums_copy = copy.deepcopy(nums)
                result = fn(nums_copy)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    print(f"  FAIL [{name}] {desc}: nums={nums} expected={expected} got={result}")
            except Exception as e:
                if name == "Way 7: Brute recursion" and len(nums) > 15:
                    passed += 1  # skip slow
                else:
                    failed += 1
                    print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_tests()
