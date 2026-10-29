"""
SUBSETS (educative canonical version)
LeetCode 78. Subsets

This file is the canonical backtracking reference. Same algorithm as
01, but written as a single clean function suitable for memorising.
"""

from typing import List


def subsets(nums: List[int]) -> List[List[int]]:
    r"""
    Recursion tree for nums = [1,2,3]:

                         []
                /        |        \
              [1]       [2]       [3]      <- "include" branch
             /   \       |
          [1,2] [1,3]  [2,3]
           /
        [1,2,3]

    Each level corresponds to an index i. We either take nums[i] or not,
    then recurse on i+1. Every leaf is one subset.
    """
    res, path = [], []

    def backtrack(i: int):
        # Record the current subset at EVERY node (not just leaves),
        # because any prefix is a valid subset.
        res.append(path.copy())
        for j in range(i, len(nums)):
            path.append(nums[j])
            backtrack(j + 1)
            path.pop()

    backtrack(0)
    return res


if __name__ == "__main__":
    print(subsets([1, 2, 3]))
