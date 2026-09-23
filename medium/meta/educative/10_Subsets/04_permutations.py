"""
PERMUTATIONS — LeetCode 46
Given an array `nums` of DISTINCT integers, return ALL possible
permututations (orderings).

Example
-------
nums = [1, 2, 3]
Answer:
  [1,2,3] [1,3,2] [2,1,3] [2,3,1] [3,1,2] [3,2,1]   (6 total = 3!)

Subset vs Permutation: the ONE-LINE difference
----------------------------------------------
- Subsets:    next pick must be RIGHT of the previous pick (start = i+1).
              That's why we never see [2,1] — order is irrelevant.
- Permutations: next pick can be ANY unused element (start = 0),
                but we skip indices already in the path.

That single change of `start = i+1` → "any remaining index" turns
subset generation into permutation generation.
"""

from typing import List


def permute(nums: List[int]) -> List[List[int]]:
    res, path, used = [], [], [False] * len(nums)

    def backtrack():
        if len(path) == len(nums):
            res.append(path.copy())
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            used[i] = True
            path.append(nums[i])
            backtrack()
            path.pop()
            used[i] = False

    backtrack()
    return res


# ---- Alternative: swap-based in-place permutation ----
# Classic "no extra array" approach. Mutates nums as it goes.
def permute_swap(nums: List[int]) -> List[List[int]]:
    res = []

    def backtrack(start: int):
        if start == len(nums):
            res.append(nums.copy())
            return
        for i in range(start, len(nums)):
            nums[start], nums[i] = nums[i], nums[start]
            backtrack(start + 1)
            nums[start], nums[i] = nums[i], nums[start]

    backtrack(0)
    return res


if __name__ == "__main__":
    print(permute([1, 2, 3]))
    print(permute_swap([1, 2, 3]))
