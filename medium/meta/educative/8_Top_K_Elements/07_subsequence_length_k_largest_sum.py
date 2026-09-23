"""
FIND SUBSEQUENCE OF LENGTH K WITH THE LARGEST SUM — LeetCode 2099
=================================================================
Given nums and k, return any subsequence of length k whose sum is
MAXIMUM. Crucially: the subsequence must PRESERVE the relative order
of the original array.

When the problem also wants the indices in the original order, the
cleanest pattern is:
    1. Pair each value with its index.
    2. Sort by value DESCENDING (with index as tie-break).
    3. Take the top k.
    4. Re-sort those k by index ASCENDING (restore original order).
    5. Return only the values.
"""

from typing import List


def max_subsequence(nums: List[int], k: int) -> List[int]:
    # (value, index); we want highest values first, ties broken by smaller index
    paired = sorted(((v, i) for i, v in enumerate(nums)), reverse=True)
    top_k = sorted(paired[:k], key=lambda p: p[1])          # restore original order
    return [v for v, _ in top_k]


if __name__ == "__main__":
    print(max_subsequence([2, 1, 3, 3], 2))   # [3, 3]
    print(max_subsequence([-1, -2, 3, 4], 3)) # [-1, 3, 4]  (any order-preserving)
