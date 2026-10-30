"""
INTRODUCTION TO SUBSETS — Educative
LeetCode equivalent: 78. Subsets

Problem
-------
Given a set of distinct integers `nums`, return ALL possible subsets
(the power set). The solution set must not contain duplicate subsets.
Return the answer in any order.

Example
-------
nums = [1, 2, 3]
Answer:
  [], [1], [2], [1,2], [3], [1,3], [2,3], [1,2,3]

Key Insight
-----------
For an array of length n there are exactly 2^n subsets (including the
empty set). This is because each element is INDEPENDENTLY "in" or
"out" of any subset. That bit-flipping intuition is the foundation
of every problem in this folder.
"""

from typing import List


# ---------- Solution 1: BFS-style build (EASIEST to teach) ----------
# Idea: start with [[]]. For each number, take every existing subset
# and make a copy with the new number appended. This is iterative
# and feels like "level-order expansion".
def subsets_bfs(nums: List[int]) -> List[List[int]]:
    result = [[]]                       # the empty set is always valid
    for num in nums:
        # snapshot the current size so we don't double-include this num
        result += [subset + [num] for subset in result]
    return result


# ---------- Solution 2: Backtracking (the one interviewers expect) ----------
# We make a decision for every index: include it, or skip it.
# Each leaf of the recursion tree is one subset.
def subsets_backtrack(nums: List[int]) -> List[List[int]]:
    result, path = [], []

    def dfs(i: int):
        # Base case: we've decided on every element → one complete subset
        if i == len(nums):
            result.append(path.copy())   # MUST copy, list is mutated later
            return
        # Branch 1: skip nums[i]
        dfs(i + 1)

        # Branch 2: include nums[i]
        path.append(nums[i])
        dfs(i + 1)
        path.pop()                      # undo so siblings see a clean path

    dfs(0)
    return result


# ---------- Solution 3: Bit-mask (elegant, great for follow-ups) ----------
# Treat subset as an n-bit number. Bit j == 1 means "include nums[j]".
def subsets_bitmask(nums: List[int]) -> List[List[int]]:
    n = len(nums)
    result = []
    for mask in range(1 << n):          # 0 ... 2^n - 1
        subset = [nums[j] for j in range(n) if (mask >> j) & 1]
        result.append(subset)
    return result


if __name__ == "__main__":
    nums = [1, 2, 3]
    print("BFS       :", subsets_bfs(nums))
    print("Backtrack :", subsets_backtrack(nums))
    print("Bitmask   :", subsets_bitmask(nums))
