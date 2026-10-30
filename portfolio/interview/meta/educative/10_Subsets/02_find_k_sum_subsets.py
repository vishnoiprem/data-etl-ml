"""
FIND K-SUM SUBSETS — Educative
LeetCode equivalent: 78. Subsets  (filter by length AND sum)

Problem
-------
Given an integer array `nums` containing distinct integers and two
integers `k` and `sum`, return all subsets of `nums` of size exactly `k`
whose elements add up to `sum`. Return the answer in any order.

Example
-------
nums = [1, 2, 3, 4], k = 2, sum = 5
Answer: [[1, 4], [2, 3]]

Why this problem matters
------------------------
It is the bridge between "subsets" and "permutations". The remaining
size constraint (`k`) is what separates subset generation from subset
SELECTION. Once you can prune on remaining size, a dozen related
problems become trivial.
"""

from typing import List


def k_sum_subsets(nums: List[int], k: int, target: int) -> List[List[int]]:
    result, path = [], []
    n = len(nums)

    def dfs(start: int):
        # ---- Success: built k numbers that add to target ----
        if len(path) == k:
            if sum(path) == target:
                result.append(path.copy())
            return                       # can't extend further; backtrack

        # ---- Failure / prune paths that can never succeed ----
        # If not enough numbers remain, give up early.
        if n - start < k - len(path):
            return

        # ---- Recurse ----
        for i in range(start, n):
            path.append(nums[i])
            dfs(i + 1)                   # next pick must be RIGHT of i
            path.pop()

    dfs(0)
    return result


if __name__ == "__main__":
    print(k_sum_subsets([1, 2, 3, 4], 2, 5))   # [[1, 4], [2, 3]]
    print(k_sum_subsets([1, 2, 3, 4], 3, 7))   # [[1, 2, 4]]
    print(k_sum_subsets([5, -1, 2, 0], 2, 1))  # [[-1, 2], [1? no...]]
