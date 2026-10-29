"""
SUBSETS II — LeetCode 90
Given an integer array `nums` that may contain DUPLICATES, return all
possible subsets without duplicates.

Example
-------
nums = [1, 2, 2]
Answer: [[],[1],[1,2],[1,2,2],[2],[2,2]]

Pattern: SAME algorithm as Subsets, plus ONE pruning rule
---------------------------------------------------------
Pre-sort nums so duplicates sit next to each other. At each level of
the recursion, when we are about to pick nums[i]:
  • If i > start AND nums[i] == nums[i-1], SKIP nums[i].
Why? Within this level of "starting at `start`", we'd otherwise
produce identical subsets that only differ by *which* duplicate we
picked first — but the subset contents are the same.

This "sort + skip-if-equal-to-previous" trick is the canonical way
to dedupe in any subset / combination / permutation problem.
"""

from typing import List


def subsets_with_dup(nums: List[int]) -> List[List[int]]:
    nums.sort()
    res, path = [], []

    def backtrack(start: int):
        res.append(path.copy())
        for i in range(start, len(nums)):
            # Skip duplicates at the same recursion depth.
            if i > start and nums[i] == nums[i - 1]:
                continue
            path.append(nums[i])
            backtrack(i + 1)
            path.pop()

    backtrack(0)
    return res


if __name__ == "__main__":
    print(subsets_with_dup([1, 2, 2]))
